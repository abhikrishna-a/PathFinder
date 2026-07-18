import logging
import time

from django.core.management.base import BaseCommand

from apps.jobs.fetchers import fetch_all_jobs
from apps.jobs.matcher import match_all_jobs
from apps.jobs.applicant import apply_to_job
from apps.jobs.services import (
    enrich_jobs_with_emails, is_company_email,
    save_job, save_application, save_web_apply, update_daily_stats, job_exists,
)
from common.utils import safe_console
from apps.jobs.models import Application
from config.settings import MATCH_THRESHOLD_APPLY, DASHBOARD_MIN_SCORE_TRACK


class Command(BaseCommand):
    help = "Run one fetch-match-apply cycle (skip already applied)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting fetch cycle..."))
        start = time.time()

        raw_jobs = fetch_all_jobs()
        self.stdout.write(self.style.SUCCESS(f"Fetched {len(raw_jobs)} raw jobs from all sources"))

        new_count = sum(1 for j in raw_jobs if not job_exists(j["uid"]))
        self.stdout.write(f"  {new_count} new jobs (not seen before)")

        matched_jobs = match_all_jobs(raw_jobs)
        self.stdout.write(self.style.SUCCESS(f"Matched {len(matched_jobs)} jobs"))

        filter_stats = {}
        for j in raw_jobs:
            reason = j.get("filter_reason", "")
            if reason:
                key = reason.split("(")[0].strip()
                filter_stats[key] = filter_stats.get(key, 0) + 1
        if filter_stats:
            for reason, count in filter_stats.items():
                safe_reason = safe_console(reason)
                self.stdout.write(f"  Filtered: {safe_reason} ({count})")

        already_applied_uids = set(
            Application.objects.select_related("job")
            .values_list("job__uid", flat=True)
        )

        apply_candidates = [
            j for j in matched_jobs
            if j["match_score"] >= MATCH_THRESHOLD_APPLY and j["uid"] not in already_applied_uids
        ]
        self.stdout.write(self.style.NOTICE(
            f"  {len(apply_candidates)} NEW jobs above {MATCH_THRESHOLD_APPLY}% "
            f"(skipping {len(matched_jobs) - len(apply_candidates)} already matched/applied)"
        ))

        if apply_candidates:
            apply_candidates = enrich_jobs_with_emails(apply_candidates)

            valid_emails = sum(
                1 for j in apply_candidates
                if j.get("apply_email") and is_company_email(j["apply_email"], j.get("company", ""))
            )
            self.stdout.write(self.style.SUCCESS(f"  Found {valid_emails} valid company emails"))

        applied = 0
        web_applied = 0
        failed_apply = 0
        skipped = 0
        no_email = 0
        for job_data in matched_jobs:
            if job_data["uid"] in already_applied_uids:
                skipped += 1
                continue

            save_job(job_data)

            email = job_data.get("apply_email", "")
            if email and not is_company_email(email, job_data.get("company", "")):
                self.stdout.write(
                    f"  Rejected {email} for {safe_console(job_data['company'])} (not company domain)"
                )
                job_data["apply_email"] = ""
                email = ""

            if email and job_data["match_score"] >= MATCH_THRESHOLD_APPLY:
                self.stdout.write(
                    f"  Applying to {safe_console(job_data['title'][:50])} "
                    f"at {safe_console(job_data['company'])}..."
                )
                result = apply_to_job(job_data)
                job = save_job(job_data)
                job.status = "applied"
                job.save()
                save_application(job, result)

                if result["success"]:
                    applied += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"    Sent to {email} [{safe_console(job_data['title'][:40])}]"
                    ))
                else:
                    failed_apply += 1
                    self.stdout.write(self.style.WARNING(
                        f"    Failed: {safe_console(result['message'])}"
                    ))
            elif not email and job_data.get("apply_url") and job_data["match_score"] >= MATCH_THRESHOLD_APPLY:
                result = apply_to_job(job_data)
                job = save_job(job_data)
                job.status = "web_apply"
                job.save()
                save_web_apply(job, result)
                web_applied += 1
                self.stdout.write(self.style.NOTICE(
                    f"    Web apply saved: {safe_console(job_data['title'][:40])} "
                    f"at {safe_console(job_data['company'])}"
                ))
            elif job_data["match_score"] >= DASHBOARD_MIN_SCORE_TRACK:
                no_email += 1

        ignored_count = len(raw_jobs) - len(matched_jobs)
        update_daily_stats(
            fetched=len(raw_jobs),
            matched=len(matched_jobs),
            applied=applied,
            ignored=ignored_count,
            failed=failed_apply,
        )

        elapsed = round(time.time() - start, 1)
        self.stdout.write(self.style.SUCCESS(
            f"\nCycle complete in {elapsed}s\n"
            f"  Fetched:     {len(raw_jobs)}\n"
            f"  Matched:     {len(matched_jobs)}\n"
            f"  Applied:     {applied} (email sent)\n"
            f"  Web apply:   {web_applied} (saved for manual apply)\n"
            f"  Skipped:     {skipped} (already applied)\n"
            f"  No email:    {no_email} (missing company email)\n"
            f"  Failed:      {failed_apply}\n"
            f"  Ignored:     {ignored_count}"
        ))
