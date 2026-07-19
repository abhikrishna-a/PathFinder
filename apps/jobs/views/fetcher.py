import threading
import logging
import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.decorators import api_view

from django.http import JsonResponse
from config.settings import DEBUG

logger = logging.getLogger(__name__)
_fetcher_running = False

_fetcher_progress = {
    "running": False,
    "step": "",
    "message": "",
    "percent": 0,
    "details": {},
    "started_at": None,
    "finished_at": None,
}


def _broadcast_progress():
    channel_layer = get_channel_layer()
    payload = {
        "running": _fetcher_progress["running"],
        "step": _fetcher_progress["step"],
        "message": _fetcher_progress["message"],
        "percent": _fetcher_progress["percent"],
        "details": _fetcher_progress["details"],
    }
    if _fetcher_progress.get("started_at"):
        now = time.time()
        payload["elapsed_seconds"] = round(
            (_fetcher_progress.get("finished_at") or now) - _fetcher_progress["started_at"], 1
        )
    async_to_sync(channel_layer.group_send)(
        "fetcher_progress",
        {"type": "fetcher.progress.update", "data": payload},
    )


def _update_progress(step: str, message: str, percent: int, details: dict = None):
    _fetcher_progress["step"] = step
    _fetcher_progress["message"] = message
    _fetcher_progress["percent"] = percent
    if details:
        _fetcher_progress["details"].update(details)
    logger.info(f"[{percent}%] {message}")
    try:
        _broadcast_progress()
    except Exception:
        logger.debug("WebSocket broadcast failed, channel layer may not be running")


def _run_fetcher_background():
    global _fetcher_running
    _fetcher_progress.update({
        "running": True, "step": "starting", "message": "Starting job fetch...",
        "percent": 0, "details": {}, "started_at": time.time(), "finished_at": None,
    })
    try:
        from apps.jobs.fetchers import fetch_all_jobs
        from apps.jobs.matcher import match_all_jobs
        from apps.jobs.applicant import apply_to_job
        from apps.jobs.services import (
            enrich_jobs_with_emails, enrich_jobs_with_salaries,
            is_company_email,
            save_job, save_application, save_web_apply,
            update_daily_stats, _extract_salary_from_text,
        )
        from apps.jobs.models import Application, RawJob, JobEvent, Job
        from config.settings import MATCH_THRESHOLD_APPLY

        _fetcher_running = True

        _update_progress("fetch", "Fetching jobs from all sources...", 5)

        existing_uids = set(Job.objects.values_list("uid", flat=True))

        raw_jobs = fetch_all_jobs()
        batch_id = RawJob.new_batch_id()

        _update_progress("filter", f"Filtering {len(raw_jobs)} jobs against existing database...", 40,
                         {"total_raw": len(raw_jobs), "existing": len(existing_uids)})

        new_jobs = []
        updated_salary = 0
        for r in raw_jobs:
            uid = r.get("uid", "")
            if uid in existing_uids:
                job = Job.objects.filter(uid=uid).first()
                if job and not job.salary:
                    text = f"{r.get('title', '')} {r.get('description', '')[:800]}"
                    salary, salary_display = _extract_salary_from_text(text)
                    if salary:
                        job.salary = salary
                        job.salary_display = salary_display
                        job.save(update_fields=["salary", "salary_display"])
                        updated_salary += 1
                continue

            RawJob.objects.create(
                uid=uid,
                title=r.get("title", ""),
                company=r.get("company", ""),
                location=r.get("location", ""),
                description=r.get("description", ""),
                source=r.get("source", ""),
                posted_date=r.get("posted_date", ""),
                apply_url=r.get("apply_url", ""),
                search_query=r.get("search_query", ""),
                salary=r.get("salary", 0),
                salary_display=r.get("salary_display", ""),
                full_text=r.get("full_text", ""),
                fetch_batch_id=batch_id,
                raw_payload=r,
            )
            new_jobs.append(r)

        _fetcher_progress["details"].update({
            "new": len(new_jobs),
            "skipped": len(raw_jobs) - len(new_jobs),
            "salary_backfilled": updated_salary,
        })

        if not new_jobs:
            _update_progress("done", f"No new jobs found. {updated_salary} salaries backfilled.", 100)
            update_daily_stats()
            return

        _update_progress("match", f"Analyzing {len(new_jobs)} new jobs for skill matches...", 50,
                         {"new_count": len(new_jobs)})

        all_jobs = match_all_jobs(new_jobs)

        matched = sum(1 for j in all_jobs if j["status"] != "ignored")
        ignored = len(all_jobs) - matched
        _fetcher_progress["details"].update({"matched": matched, "ignored": ignored})

        already_applied_uids = set(
            Application.objects.select_related("job")
            .values_list("job__uid", flat=True)
        )

        apply_candidates = [
            j for j in all_jobs
            if j["match_score"] >= MATCH_THRESHOLD_APPLY
            and j["status"] != "ignored"
            and j["uid"] not in already_applied_uids
        ]

        if apply_candidates:
            _update_progress("email", f"Looking up company emails for {len(apply_candidates)} candidates...", 65,
                             {"candidates": len(apply_candidates)})
            apply_candidates = enrich_jobs_with_emails(apply_candidates)

        salary_candidates = [
            j for j in all_jobs
            if j["status"] != "ignored"
            and not j.get("salary", 0)
            and j.get("apply_url")
        ]
        salary_candidates.sort(key=lambda j: j.get("match_score", 0), reverse=True)
        salary_candidates = salary_candidates[:30]

        if salary_candidates:
            _update_progress("salary", f"Checking {len(salary_candidates)} job pages for salary info...", 75,
                             {"salary_check": len(salary_candidates)})
            enrich_jobs_with_salaries(salary_candidates)

        _update_progress("save", "Saving jobs and creating applications...", 85)

        applied = 0
        web_applied = 0
        failed_apply = 0

        for i, job_data in enumerate(all_jobs):
            if (i + 1) % 50 == 0:
                _update_progress("save", f"Saving jobs... ({i + 1}/{len(all_jobs)})", 85,
                                 {"saved": i + 1, "total": len(all_jobs)})

            if job_data["status"] == "ignored":
                job = save_job(job_data)
                JobEvent.objects.create(
                    job=job, event_type="ignored",
                    old_status="", new_status="ignored",
                    match_score=job_data.get("match_score", 0),
                )
                continue

            if job_data["uid"] in already_applied_uids:
                save_job(job_data)
                continue

            job = save_job(job_data)
            JobEvent.objects.create(
                job=job, event_type="matched",
                old_status="", new_status=job.status,
                match_score=job_data.get("match_score", 0),
            )

            email = job_data.get("apply_email", "")
            if email and not is_company_email(email, job_data.get("company", "")):
                job_data["apply_email"] = ""
                email = ""

            if email and job_data["match_score"] >= MATCH_THRESHOLD_APPLY:
                result = apply_to_job(job_data)
                old_status = job.status
                job.status = "applied"
                job.save()
                JobEvent.objects.create(
                    job=job, event_type="applied",
                    old_status=old_status, new_status="applied",
                    match_score=job_data.get("match_score", 0),
                )
                save_application(job, result)
                if result["success"]:
                    applied += 1
                else:
                    failed_apply += 1
            elif not email and job_data.get("apply_url") and job_data["match_score"] >= MATCH_THRESHOLD_APPLY:
                result = apply_to_job(job_data)
                old_status = job.status
                job.status = "web_apply"
                job.save()
                JobEvent.objects.create(
                    job=job, event_type="web_apply",
                    old_status=old_status, new_status="web_apply",
                    match_score=job_data.get("match_score", 0),
                )
                save_web_apply(job, result)
                web_applied += 1

        _update_progress("stats", "Updating dashboard statistics...", 95)
        update_daily_stats()

        _fetcher_progress["details"].update({
            "applied": applied, "web_applied": web_applied, "failed": failed_apply,
        })
        _update_progress("done",
                         f"Done! {len(new_jobs)} new jobs, {matched} matched, {applied} applied, {web_applied} web applied.",
                         100)

    except Exception as e:
        logger.exception("Fetcher failed")
        _update_progress("error", f"Fetcher failed: {e}", 100)
    finally:
        _fetcher_running = False
        _fetcher_progress["running"] = False
        _fetcher_progress["finished_at"] = time.time()


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


@api_view(["GET"])
def fetcher_status(request):
    progress = dict(_fetcher_progress)
    if progress.get("started_at") and progress.get("finished_at"):
        progress["elapsed_seconds"] = round(progress["finished_at"] - progress["started_at"], 1)
    elif progress.get("started_at") and progress.get("running"):
        progress["elapsed_seconds"] = round(time.time() - progress["started_at"], 1)
    return JsonResponse(progress)
