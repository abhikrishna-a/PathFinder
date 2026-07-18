import logging

import httpx
from bs4 import BeautifulSoup

from config.settings import FEED_BASE_URL
from config.queries import SEARCH_QUERIES
from common.utils import make_uid
from apps.jobs.fetchers.technopark import fetch_technopark_jobs
from apps.jobs.fetchers.cutshort import fetch_cutshort_jobs

logger = logging.getLogger(__name__)


def _parse_rss_xml(xml_text: str, query: dict) -> list[dict]:
    soup = BeautifulSoup(xml_text, "xml")
    jobs = []

    for item in soup.find_all("item"):
        title_tag = item.find("title")
        link_tag = item.find("link")
        desc_tag = item.find("description")
        pub_tag = item.find("pubDate")

        if not title_tag:
            continue

        raw_title = title_tag.get_text(strip=True)

        if " at " in raw_title:
            parts = raw_title.rsplit(" at ", 1)
            title = parts[0].strip()
            company = parts[1].strip()
        else:
            title = raw_title
            company = ""

        location = ""
        description = ""
        source = ""
        posted = pub_tag.get_text(strip=True) if pub_tag else ""
        apply_url = link_tag.get_text(strip=True) if link_tag else ""

        if desc_tag:
            desc_html = desc_tag.decode_contents()
            desc_soup = BeautifulSoup(desc_html, "html.parser")
            desc_text = desc_soup.get_text(separator="\n", strip=True)
            description = desc_text

            for line in desc_text.split("\n"):
                line = line.strip()
                low = line.lower()
                if low.startswith("location:") or low.startswith("location :"):
                    location = line.split(":", 1)[1].strip() if ":" in line else ""
                elif low.startswith("source:") or low.startswith("source :"):
                    source = line.split(":", 1)[1].strip() if ":" in line else ""

            src_link = desc_soup.find("a")
            if src_link:
                source = src_link.get_text(strip=True)
                src_href = src_link.get("href", "")
                if src_href and not apply_url:
                    apply_url = src_href

        if not location:
            location = query.get("location", "")

        if not company:
            continue

        uid = make_uid(title, company)
        full_text = f"{title} {company} {description} {location} {source}"

        jobs.append({
            "uid": uid,
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "posted_date": posted,
            "source": source,
            "apply_email": "",
            "apply_url": apply_url,
            "search_query": f"{query['keywords']} in {query['location']}",
            "job_url": apply_url,
            "salary": 0,
            "salary_display": "",
            "full_text": full_text,
        })

    return jobs


def _ensure_feed_exists(client: httpx.Client, query: dict):
    keywords = query["keywords"]
    location = query["location"]

    try:
        client.post(
            FEED_BASE_URL,
            data={"keywords": keywords, "location": location},
            headers={
                "HX-Request": "true",
                "HX-Target": "content",
                "HX-Swap": "innerHTML",
            },
        )
    except Exception as e:
        logger.debug(f"POST feed creation skipped for {keywords} in {location}: {e}")


def fetch_rss_jobs() -> list[dict]:
    all_jobs = []
    seen_uids = set()

    client = httpx.Client(
        http2=True,
        timeout=30,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
        },
    )

    for query in SEARCH_QUERIES:
        keywords = query["keywords"]
        location = query["location"]
        logger.info(f"RSS: Fetching {keywords} in {location}")

        _ensure_feed_exists(client, query)

        try:
            resp = client.get(
                FEED_BASE_URL,
                params={"keywords": keywords, "location": location},
            )
            resp.raise_for_status()

            jobs = _parse_rss_xml(resp.text, query)

            new_count = 0
            for job in jobs:
                if job["uid"] not in seen_uids:
                    seen_uids.add(job["uid"])
                    all_jobs.append(job)
                    new_count += 1

            logger.info(f"  Found {len(jobs)} jobs ({new_count} new)")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"  Feed not found (creating): {keywords} in {location}")
                _ensure_feed_exists(client, query)
            else:
                logger.error(f"  HTTP {e.response.status_code} for {keywords} in {location}")
        except Exception as e:
            logger.error(f"  Failed: {e}")

    client.close()
    logger.info(f"RSS total: {len(all_jobs)} unique jobs")
    return all_jobs


def fetch_all_jobs() -> list[dict]:
    all_jobs = []
    seen_uids = set()

    rss_jobs = fetch_rss_jobs()
    for job in rss_jobs:
        if job["uid"] not in seen_uids:
            seen_uids.add(job["uid"])
            all_jobs.append(job)

    try:
        technopark_jobs = fetch_technopark_jobs()
        for job in technopark_jobs:
            if job["uid"] not in seen_uids:
                seen_uids.add(job["uid"])
                all_jobs.append(job)
    except Exception as e:
        logger.error(f"Technopark scraper failed: {e}")

    try:
        cutshort_jobs = fetch_cutshort_jobs()
        for job in cutshort_jobs:
            if job["uid"] not in seen_uids:
                seen_uids.add(job["uid"])
                all_jobs.append(job)
    except Exception as e:
        logger.error(f"Cutshort scraper failed: {e}")

    logger.info(f"Total unique jobs from all sources: {len(all_jobs)}")
    return all_jobs
