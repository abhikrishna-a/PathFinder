import json
import logging
from datetime import date

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "job_portal.settings")

import django
django.setup()

from django.db.models import Count
from dashboard.models import Job, Application, SkillLog, DailyStats

logger = logging.getLogger(__name__)


def job_exists(uid: str) -> bool:
    return Job.objects.filter(uid=uid).exists()


def save_job(job_data: dict) -> Job:
    job, created = Job.objects.update_or_create(
        uid=job_data["uid"],
        defaults={
            "title": job_data.get("title", ""),
            "company": job_data.get("company", ""),
            "location": job_data.get("location", ""),
            "description": job_data.get("description", ""),
            "source": job_data.get("source", ""),
            "posted_date": job_data.get("posted_date", ""),
            "match_score": job_data.get("match_score", 0),
            "status": job_data.get("status", "new"),
            "apply_email": job_data.get("apply_email", ""),
            "apply_url": job_data.get("apply_url", ""),
            "search_query": job_data.get("search_query", ""),
            "matched_skills": job_data.get("matched_skills", []),
            "skill_score_breakdown": job_data.get("skill_score_breakdown", {}),
            "skill_gaps": job_data.get("skill_gaps", []),
            "filter_reason": job_data.get("filter_reason", ""),
            "match_explanation": job_data.get("match_explanation", ""),
            "job_url": job_data.get("job_url", ""),
        },
    )
    return job


def save_application(job: Job, result: dict) -> Application:
    criteria = {
        "skills_in_jd": result.get("skills_in_jd", []),
        "skills_highlighted": result.get("skills_highlighted", []),
        "sections_included": result.get("sections_included", []),
        "project_mentioned": result.get("project_mentioned", ""),
        "role_level": result.get("role_level", ""),
        "min_years_required": result.get("min_years_required"),
        "email_used": job.apply_email,
        "email_domain_valid": bool(job.apply_email),
        "resume_attached": True,
        "match_score": job.match_score,
    }

    app, created = Application.objects.update_or_create(
        job=job,
        defaults={
            "email_subject": result.get("email_subject", ""),
            "cover_letter_text": result.get("cover_letter", ""),
            "status": "sent" if result.get("success") else "failed",
            "error_message": "" if result.get("success") else result.get("message", ""),
            "skills_highlighted": result.get("skills_highlighted", []),
            "skills_in_job_desc": result.get("skills_in_jd", []),
            "skill_match_pct": job.match_score,
            "criteria_data": criteria,
            "skill_gaps": job.skill_gaps,
            "match_explanation": job.match_explanation,
        },
    )

    if created:
        for skill in result.get("skills_highlighted", job.matched_skills):
            SkillLog.objects.create(
                application=app,
                job=job,
                skill_name=skill,
                found_in_job_desc=True,
                highlighted_in_cover_letter=True,
            )

    return app


def save_web_apply(job: Job, result: dict) -> Application:
    criteria = {
        "skills_in_jd": result.get("skills_in_jd", []),
        "skills_highlighted": result.get("skills_highlighted", []),
        "sections_included": result.get("sections_included", []),
        "project_mentioned": result.get("project_mentioned", ""),
        "role_level": result.get("role_level", ""),
        "min_years_required": result.get("min_years_required"),
        "email_used": "",
        "email_domain_valid": False,
        "resume_attached": False,
        "match_score": job.match_score,
        "apply_url": job.apply_url,
    }

    app, created = Application.objects.update_or_create(
        job=job,
        defaults={
            "email_subject": result.get("email_subject", ""),
            "cover_letter_text": result.get("cover_letter", ""),
            "status": "web_apply",
            "error_message": "No company email — manual apply via: " + (job.apply_url or ""),
            "skills_highlighted": result.get("skills_highlighted", []),
            "skills_in_job_desc": result.get("skills_in_jd", []),
            "skill_match_pct": job.match_score,
            "criteria_data": criteria,
            "skill_gaps": job.skill_gaps,
            "match_explanation": job.match_explanation,
        },
    )
    return app


def update_daily_stats(fetched: int = 0, matched: int = 0, applied: int = 0, ignored: int = 0, failed: int = 0):
    today = date.today()
    stats, _ = DailyStats.objects.get_or_create(date=today)
    stats.total_fetched += fetched
    stats.total_matched += matched
    stats.total_applied += applied
    stats.total_ignored += ignored
    stats.total_failed += failed

    top_skills = (
        SkillLog.objects
        .filter(created_at__date=today)
        .values("skill_name")
        .annotate(count=Count("skill_name"))
        .order_by("-count")[:20]
    )
    stats.top_keywords = [s["skill_name"] for s in top_skills]

    top_companies = (
        Application.objects
        .filter(sent_at__date=today)
        .values("job__company")
        .annotate(count=Count("job__company"))
        .order_by("-count")[:20]
    )
    stats.top_companies = [c["job__company"] for c in top_companies]
    stats.save()


def get_recent_jobs(limit=50):
    return Job.objects.all()[:limit]


def get_matched_jobs():
    return Job.objects.filter(status__in=["matched", "applied"]).order_by("-match_score")


def get_all_applications():
    return Application.objects.select_related("job").order_by("-sent_at")


def get_job_stats():
    return {
        "total_jobs": Job.objects.count(),
        "total_matched": Job.objects.filter(status="matched").count(),
        "total_applied": Application.objects.filter(status="sent").count(),
        "total_failed": Application.objects.filter(status="failed").count(),
        "total_ignored": Job.objects.filter(status="ignored").count(),
    }
