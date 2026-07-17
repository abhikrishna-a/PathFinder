import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_DIR = Path(__file__).resolve().parent.parent

RESUME_PATH = BASE_DIR / os.getenv("RESUME_PATH", "resume/Your_Resume.pdf")

MATCH_THRESHOLD_APPLY = 65
MATCH_THRESHOLD_TRACK = 50
MIN_SALARY = 18000
MIN_PROJECT_MATCH = 1

MAX_SKILL_GAP_PCT = 40

FEED_BASE_URL = "https://rssjobs.app/feeds"

EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
