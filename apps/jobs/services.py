import json
import re
import logging
import time
from datetime import date

import httpx
from django.db.models import Count

from apps.jobs.models import Job, Application, SkillLog, DailyStats
from config.constants import RECRUITER_KEYWORDS
from config.settings import MIN_SALARY
from common.utils import is_company_email as _validate_company_email, EMAIL_REGEX, JUNK_DOMAINS

logger = logging.getLogger(__name__)

SALARY_PATTERNS = [
    r"[\u20b9\uffe0]?\s*(\d[\d,]*)\s*[-\u2013to]+\s*[\u20b9\uffe0]?\s*(\d[\d,]*)\s*(?:lpa|lakhs?|k|per month|pm|annually|yearly|p\.?a\.?)?",
    r"(\d[\d,]*)\s*[-\u2013to]+\s*(\d[\d,]*)\s*(?:k|,?000)\s*(?:per month|pm|monthly|/month)?",
    r"salary[:\s]*[\u20b9\uffe0]?\s*(\d[\d,]*)\s*(?:k|,?000)?",
    r"(\d[\d,]*)\s*(?:k|,?000)\s*(?:per month|pm|monthly|/month)",
    r"[\u20b9\uffe0]\s*(\d[\d,]*)\s*(?:lpa|lakhs?|k|per month|pm)",
]


def _format_salary(amount: int) -> str:
    if amount >= 100000:
        return f"\u20b9{amount // 100000}L PA"
    elif amount >= 1000:
        return f"\u20b9{amount // 1000}K"
    return f"\u20b9{amount:,}"


def _extract_salary_from_text(text: str) -> tuple[int, str]:
    text_lower = text.lower()

    if any(w in text_lower for w in [
        "competitive salary", "negotiable", "market rate", "based on experience"
    ]):
        return 0, ""

    for pat in SALARY_PATTERNS:
        matches = re.finditer(pat, text, re.IGNORECASE)
        for m in matches:
            groups = m.groups()
            numbers = []
            for g in groups:
                if g:
                    clean = g.replace(",", "").replace(" ", "")
                    try:
                        numbers.append(int(clean))
                    except ValueError:
                        pass

            if not numbers:
                continue

            salary = max(numbers)
            context = text_lower[max(0, m.start() - 20):m.end() + 20]

            if "lpa" in context or "lakhs" in context or "lakh" in context:
                salary = salary * 100000
            elif salary < 1000:
                if "k" in context:
                    salary = salary * 1000
                elif "per month" in context or "pm" in context or "monthly" in context:
                    salary = salary * 12
                else:
                    salary = salary * 1000

            if salary >= MIN_SALARY:
                return salary, _format_salary(salary)

    return 0, ""


def job_exists(uid: str) -> bool:
    return Job.objects.filter(uid=uid).exists()


def save_job(job_data: dict) -> Job:
    salary = job_data.get("salary", 0)
    salary_display = job_data.get("salary_display", "")

    if not salary:
        search_text = f"{job_data.get('full_text', '')} {job_data.get('description', '')}"
        salary, salary_display = _extract_salary_from_text(search_text)

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
            "salary": salary,
            "salary_display": salary_display,
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
            "error_message": "No company email \u2014 manual apply via: " + (job.apply_url or ""),
            "skills_highlighted": result.get("skills_highlighted", []),
            "skills_in_job_desc": result.get("skills_in_jd", []),
            "skill_match_pct": job.match_score,
            "criteria_data": criteria,
            "skill_gaps": job.skill_gaps,
            "match_explanation": job.match_explanation,
        },
    )
    return app


def update_daily_stats(
    fetched: int = 0, matched: int = 0, applied: int = 0,
    ignored: int = 0, failed: int = 0,
):
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


def is_company_email(email: str, company: str = "") -> bool:
    is_valid, reason = _validate_company_email(email)
    if not is_valid:
        return False

    email = email.lower().strip()
    domain = email.split("@")[1]

    if company:
        company_slug = re.sub(r"[^a-z0-9]", "", company.lower())
        if company_slug and len(company_slug) >= 3:
            if company_slug in domain:
                return True

    if any(kw in domain for kw in RECRUITER_KEYWORDS):
        return False

    if email.startswith("noreply@") or email.startswith("no-reply@"):
        return False

    if len(email) > 60:
        return False

    return True


def _extract_emails_from_text(text: str) -> list[str]:
    raw = EMAIL_REGEX.findall(text)
    return [e.lower() for e in raw if is_company_email(e)]


def find_job_email(job: dict, client: httpx.Client | None = None) -> str:
    if job.get("apply_email"):
        if is_company_email(job["apply_email"], job.get("company", "")):
            return job["apply_email"]
        else:
            logger.info(f"  Rejected email {job['apply_email']} (not company domain)")
            job["apply_email"] = ""

    close_client = False
    if client is None:
        client = httpx.Client(
            http2=True, timeout=15, follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        close_client = True

    try:
        url = job.get("apply_url", "")
        if not url:
            return ""

        try:
            resp = client.get(url, follow_redirects=True, timeout=15)
            if resp.status_code == 200:
                all_emails = _extract_emails_from_text(resp.text)
                company = job.get("company", "")
                emails = [e for e in all_emails if is_company_email(e, company)]
            else:
                emails = []
        except Exception:
            emails = []

        if emails:
            email = emails[0]
            logger.info(f"  Found company email: {email}")
            return email

        description = job.get("description", "") + " " + job.get("full_text", "")
        desc_emails = _extract_emails_from_text(description)
        company = job.get("company", "")
        desc_emails_valid = [e for e in desc_emails if is_company_email(e, company)]
        if desc_emails_valid:
            return desc_emails_valid[0]

    except Exception as e:
        logger.debug(f"Email extraction failed: {e}")

    finally:
        if close_client:
            client.close()

    return ""


def enrich_jobs_with_emails(jobs: list[dict], batch_size: int = 5) -> list[dict]:
    client = httpx.Client(
        http2=True, timeout=15, follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        },
    )

    enriched = 0
    for i, job in enumerate(jobs):
        if job.get("apply_email"):
            if not is_company_email(job["apply_email"], job.get("company", "")):
                logger.info(f"  Rejected {job['apply_email']} for {job['company']}")
                job["apply_email"] = ""
            else:
                continue

        url = job.get("apply_url", "")
        if not url:
            continue

        logger.info(f"  [{i+1}/{len(jobs)}] Extracting email for {job['company']}...")

        email = find_job_email(job, client)
        if email:
            job["apply_email"] = email
            enriched += 1

        if (i + 1) % batch_size == 0:
            time.sleep(1)

    client.close()
    logger.info(f"Enriched {enriched}/{len(jobs)} jobs with valid company emails")
    return jobs
