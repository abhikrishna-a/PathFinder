import threading
import logging

from rest_framework import status
from rest_framework.decorators import api_view

from django.http import JsonResponse
from config.settings import DEBUG

logger = logging.getLogger(__name__)
_fetcher_running = False


def _run_fetcher_background():
    global _fetcher_running
    try:
        from apps.jobs.fetchers import fetch_all_jobs
        from apps.jobs.matcher import match_all_jobs
        from apps.jobs.applicant import apply_to_job
        from apps.jobs.services import (
            enrich_jobs_with_emails, is_company_email,
            save_job, save_application, save_web_apply,
            update_daily_stats, job_exists,
        )
        from apps.jobs.models import Application
        from config.settings import MATCH_THRESHOLD_APPLY

        _fetcher_running = True

        raw_jobs = fetch_all_jobs()
        matched_jobs = match_all_jobs(raw_jobs)

        already_applied_uids = set(
            Application.objects.select_related("job")
            .values_list("job__uid", flat=True)
        )

        apply_candidates = [
            j for j in matched_jobs
            if j["match_score"] >= MATCH_THRESHOLD_APPLY and j["uid"] not in already_applied_uids
        ]

        if apply_candidates:
            apply_candidates = enrich_jobs_with_emails(apply_candidates)

        applied = 0
        web_applied = 0
        failed_apply = 0

        for job_data in matched_jobs:
            if job_data["uid"] in already_applied_uids:
                continue

            save_job(job_data)

            email = job_data.get("apply_email", "")
            if email and not is_company_email(email, job_data.get("company", "")):
                job_data["apply_email"] = ""
                email = ""

            if email and job_data["match_score"] >= MATCH_THRESHOLD_APPLY:
                result = apply_to_job(job_data)
                job = save_job(job_data)
                job.status = "applied"
                job.save()
                save_application(job, result)
                if result["success"]:
                    applied += 1
                else:
                    failed_apply += 1
            elif not email and job_data.get("apply_url") and job_data["match_score"] >= MATCH_THRESHOLD_APPLY:
                result = apply_to_job(job_data)
                job = save_job(job_data)
                job.status = "web_apply"
                job.save()
                save_web_apply(job, result)
                web_applied += 1

        ignored_count = len(raw_jobs) - len(matched_jobs)
        update_daily_stats(
            fetched=len(raw_jobs),
            matched=len(matched_jobs),
            applied=applied,
            ignored=ignored_count,
            failed=failed_apply,
        )

        logger.info(
            "Fetcher complete: fetched=%d matched=%d applied=%d web_apply=%d failed=%d",
            len(raw_jobs), len(matched_jobs), applied, web_applied, failed_apply,
        )
    except Exception:
        logger.exception("Fetcher failed")
    finally:
        _fetcher_running = False


@api_view(["POST"])
def run_fetcher(request):
    if not DEBUG:
        return JsonResponse({"error": "Only available in debug mode"}, status=status.HTTP_403_FORBIDDEN)

    global _fetcher_running
    if _fetcher_running:
        return JsonResponse({"error": "Fetcher is already running"}, status=status.HTTP_409_CONFLICT)

    thread = threading.Thread(target=_run_fetcher_background, daemon=True)
    thread.start()
    return JsonResponse({"success": True, "message": "Fetcher started"})
