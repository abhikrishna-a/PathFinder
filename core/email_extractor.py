import re
import logging
import time

import httpx

from config import RECRUITER_KEYWORDS
from core.utils import is_company_email as _validate_company_email, EMAIL_REGEX, JUNK_DOMAINS

logger = logging.getLogger(__name__)


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


def extract_email_from_linkedin(url: str, client: httpx.Client) -> list[str]:
    emails = []
    try:
        resp = client.get(url, follow_redirects=True, timeout=15)
        if resp.status_code == 200:
            emails = _extract_emails_from_text(resp.text)
    except Exception as e:
        logger.debug(f"LinkedIn scrape failed for {url}: {e}")
    return emails


def extract_email_from_glassdoor(url: str, client: httpx.Client) -> list[str]:
    emails = []
    try:
        resp = client.get(url, follow_redirects=True, timeout=15)
        if resp.status_code == 200:
            emails = _extract_emails_from_text(resp.text)
    except Exception as e:
        logger.debug(f"Glassdoor scrape failed for {url}: {e}")
    return emails


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

        if "linkedin.com" in url:
            emails = extract_email_from_linkedin(url, client)
        elif "glassdoor" in url:
            emails = extract_email_from_glassdoor(url, client)
        else:
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
