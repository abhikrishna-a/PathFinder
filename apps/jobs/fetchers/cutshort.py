import json
import logging
import re
import time

import httpx
from bs4 import BeautifulSoup

from config.queries import CUTSHORT_SEARCH_URLS
from common.utils import make_uid, clean_html

logger = logging.getLogger(__name__)


def _extract_next_data(html: str) -> dict | None:
    try:
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            return json.loads(script.string)
        match = re.search(r'__NEXT_DATA__.*?>(.*?)</script>', html)
        if match:
            return json.loads(match.group(1))
    except Exception as e:
        logger.debug(f"Failed to parse __NEXT_DATA__: {e}")
    return None


def _parse_job(job: dict) -> dict | None:
    title = job.get("headline", "").strip()
    company_data = job.get("companyDetails", {})
    company = company_data.get("name", "").strip()

    if not title or not company:
        return None

    uid = make_uid(title, company)

    location_list = job.get("locations", [])
    location = ", ".join(location_list) if location_list else "Not specified"

    salary_data = job.get("salaryRange", {})
    min_salary = salary_data.get("min", 0)
    max_salary = salary_data.get("max", 0)

    if min_salary and max_salary:
        salary_display = f"{min_salary // 100000}L-{max_salary // 100000}L PA" if min_salary >= 100000 else f"{min_salary // 1000}K-{max_salary // 1000}K"
    elif min_salary:
        salary_display = f"{min_salary // 100000}L PA" if min_salary >= 100000 else f"{min_salary // 1000}K"
    else:
        salary_display = ""

    exp_data = job.get("expRange", {})
    min_exp = exp_data.get("min", 0)
    max_exp = exp_data.get("max", 0)

    description_html = job.get("sanitizedComment", "")
    description = clean_html(description_html)

    skills = job.get("allSkills", [])

    apply_url = job.get("publicUrl", "")

    remote_type = job.get("remoteType", "")
    remote = remote_type == "remote_okay" or "remote" in location.lower()

    return {
        "uid": uid,
        "title": title,
        "company": company,
        "location": location,
        "description": description,
        "apply_url": apply_url,
        "apply_email": "",
        "salary": salary_data.get("max", 0) if salary_data else 0,
        "salary_display": salary_display,
        "experience": f"{min_exp}-{max_exp} years" if max_exp else "",
        "min_experience": min_exp,
        "max_experience": max_exp,
        "skills": skills,
        "posted_date": "",
        "source": "cutshort",
        "remote": remote,
        "full_text": f"{title} {description} {' '.join(skills)}",
    }


def fetch_cutshort_jobs() -> list[dict]:
    all_jobs = []
    seen_uids = set()

    client = httpx.Client(
        http2=True,
        timeout=20,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    )

    for url in CUTSHORT_SEARCH_URLS:
        try:
            logger.info(f"Fetching Cutshort: {url}")
            resp = client.get(url)

            if resp.status_code != 200:
                logger.warning(f"  HTTP {resp.status_code}")
                continue

            data = _extract_next_data(resp.text)
            if not data:
                logger.warning(f"  No __NEXT_DATA__ found")
                continue

            queries = (
                data.get("props", {})
                .get("pageProps", {})
                .get("dehydratedState", {})
                .get("queries", [])
            )

            jobs_list = []
            for query in queries:
                page_data = (
                    query.get("state", {})
                    .get("data", {})
                    .get("data", {})
                    .get("pageData", {})
                )
                jobs_list = page_data.get("jobs", [])

                for job in jobs_list:
                    parsed = _parse_job(job)
                    if parsed and parsed["uid"] not in seen_uids:
                        seen_uids.add(parsed["uid"])
                        all_jobs.append(parsed)

            logger.info(f"  Got {len(jobs_list)} jobs from this page")
            time.sleep(1)

        except Exception as e:
            logger.error(f"  Failed: {e}")

    client.close()
    logger.info(f"Cutshort total: {len(all_jobs)} unique jobs")
    return all_jobs
