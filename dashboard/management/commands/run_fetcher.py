import logging
import time

from django.core.management.base import BaseCommand

from core.fetcher import fetch_all_jobs
from core.matcher import match_all_jobs
from core.applicant import apply_to_job
from core.email_extractor import enrich_jobs_with_emails, is_company_email
from core.tracker import save_job, save_application, save_web_apply, update_daily_stats, job_exists
from core.utils import safe
from dashboard.models import Application


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
                safe_reason = reason.encode("ascii", errors="replace").decode("ascii")
                self.stdout.write(f"  Filtered: {safe_reason} ({count})")

        already_applied_uids = set(
            Application.objects.select_related("job")
            .values_list("job__uid", flat=True)
        )

        apply_candidates = [
            j for j in matched_jobs
            if j["match_score"] >= 65 and j["uid"] not in already_applied_uids
        ]
        self.stdout.write(self.style.NOTICE(
            f"  {len(apply_candidates)} NEW jobs above 65% (skipping {len(matched_jobs) - len(apply_candidates)} already matched/applied)"
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
                self.stdout.write(f"  Rejected {email} for {safe(job_data['company'])} (not company domain)")
                job_data["apply_email"] = ""
                email = ""

            if email and job_data["match_score"] >= 65:
                self.stdout.write(
                    f"  Applying to {safe(job_data['title'][:50])} at {safe(job_data['company'])}..."
                )
                result = apply_to_job(job_data)
                job = save_job(job_data)
                job.status = "applied"
                job.save()
                save_application(job, result)

                if result["success"]:
                    applied += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"    Sent to {email} [{safe(job_data['title'][:40])}]"
                    ))
                else:
                    failed_apply += 1
                    self.stdout.write(self.style.WARNING(
                        f"    Failed: {safe(result['message'])}"
                    ))
            elif not email and job_data.get("apply_url") and job_data["match_score"] >= 65:
                result = apply_to_job(job_data)
                job = save_job(job_data)
                job.status = "web_apply"
                job.save()
                save_web_apply(job, result)
                web_applied += 1
                self.stdout.write(self.style.NOTICE(
                    f"    Web apply saved: {safe(job_data['title'][:40])} at {safe(job_data['company'])}"
                ))
            elif job_data["match_score"] >= 40:
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
