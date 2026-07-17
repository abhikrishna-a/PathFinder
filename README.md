# PathFinder

Automatic job portal that fetches Python developer jobs from RSS, Technopark, and Cutshort, matches them against your profile, auto-sends CV + cover letter via Gmail, and displays everything on a Django dashboard.

**Created by Dennis Joseph** — [GitHub](https://github.com/dennisjoseph2025) · [LinkedIn](https://www.linkedin.com/in/dennisjoseph2025)

## Features

- **Multi-source job fetching** — RSS (3000+ jobs), Technopark (130+ jobs), Cutshort (300+ jobs)
- **Smart matching** — weighted skill scoring (60%), experience (15%), project relevance (20%), title (5%)
- **Auto-apply** — generates JD-aware cover letter and sends via Gmail SMTP
- **Profile management** — editable from the dashboard, takes effect on next fetch cycle
- **Skill gap analysis** — filters out jobs requiring >40% unknown skills
- **Experience range filtering** — only matches jobs within your experience bracket
- **Location + salary filtering** — respects your preferences
- **Dashboard** — dark UI with stats, charts, job cards, application tracking

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip
- Gmail account with [App Password](https://myaccount.google.com/apppasswords) enabled

## Installation

```bash
# Clone the repo
git clone https://github.com/dennisjoseph2025/pathfinder.git
cd pathfinder

# Create virtual environment and install dependencies
uv sync
# or
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install django httpx[http2] beautifulsoup4 schedule jinja2 python-dotenv lxml
```

## Configuration

### 1. Create `.env`

```bash
copy .env.example .env
```

Edit `.env` with your values:

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Any random string (e.g. `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) |
| `EMAIL_USER` | Your Gmail address |
| `EMAIL_PASS` | Gmail App Password (16 chars, no spaces) |
| `RESUME_PATH` | Path to your resume PDF (e.g. `resume/Your_Resume.pdf`) |

### 2. Create your profile

```bash
copy config\profile.example.py config\profile.py
```

Edit `config/profile.py` with your real info:

- **name** — your full name
- **email** — your email
- **phone** — your phone number
- **experience_min / experience_max** — your experience range in years
- **skills** — categorize your skills under `backend`, `frontend`, `ai_llm`, `cloud`, `devops`, `tools`
- **projects** — name, description, and tech stack for each project
- **looking_for** — target job titles

You can also edit your profile from the dashboard at `http://localhost:8000/profile/` — changes take effect on the next fetch cycle without restarting.

### 3. Place your resume

Put your resume PDF in the `resume/` folder:

```
resume/
  Your_Resume.pdf
```

### 4. Run migrations

```bash
python manage.py migrate
```

## Usage

### Run everything (recommended)

```bash
python manage.py run_all
```

This starts the Django dashboard on `http://localhost:8000` and runs the fetch-match-apply cycle every 60 minutes.

### Or run components separately

```bash
# Fetch jobs once (no server)
python manage.py run_fetcher

# Run scheduler only (fetches every 60 min, no dashboard)
python manage.py run_scheduler

# Run dashboard only (no auto-fetching)
python manage.py runserver
```

## How It Works

```
fetch_all_jobs()
    ├── RSS (rssjobs.app) — 3000+ Python/React/Django jobs
    ├── Technopark (technopark.in) — 130+ Kerala tech jobs
    └── Cutshort (cutshort.io) — 300+ jobs via __NEXT_DATA__ JSON

match_all_jobs(raw_jobs)
    ├── Skill matching (60%) — weighted by SKILL_WEIGHTS
    ├── Project matching (20%) — tech stack overlap
    ├── Experience matching (15%) — within min/max range
    ├── Title matching (5%) — target role keywords
    └── Filters: location, salary, role rejection, skill gap

apply_to_job(matched_jobs)
    ├── Extract company email (Technopark detail pages, Google "company + careers")
    ├── Generate JD-aware cover letter
    └── Send via Gmail SMTP (or save as "web_apply" if no email found)
```

## Dashboard Pages

| Page | URL | Description |
|------|-----|-------------|
| Overview | `/` | Stats cards, jobs-over-time chart, top skills chart |
| Jobs | `/jobs/` | All matched jobs with search, filters, pagination |
| Job Detail | `/jobs/{uid}/` | Full breakdown: match score, skill weights, cover letter |
| Applications | `/applications/` | Sent applications with status tracking |
| Web Apply | `/web-apply/` | Jobs with apply links (no email found) |
| Missing Emails | `/missing-emails/` | Jobs needing manual application |
| Skill Stats | `/skills/` | Skill frequency across all jobs |
| Company Stats | `/companies/` | Company job counts |
| Location Stats | `/locations/` | Job distribution by location |
| Profile | `/profile/` | Edit your profile, skills, projects |

## Project Structure

```
pathfinder/
├── config/
│   ├── __init__.py           # Loads profile.json override, re-exports all
│   ├── settings.py           # Thresholds, paths, credentials
│   ├── profile.py            # Your personal profile (gitignored)
│   ├── profile.example.py    # Template for profile.py (committed)
│   ├── queries.py            # Search queries for each source
│   └── constants.py          # Role keywords, recruiter keywords, etc.
├── core/
│   ├── fetcher.py            # Combines all sources, deduplicates
│   ├── matcher.py            # Scoring + filtering engine
│   ├── applicant.py          # Cover letter gen + Gmail SMTP
│   ├── tracker.py            # Save jobs/applications to DB
│   ├── email_extractor.py    # Find company emails
│   ├── technopark_fetcher.py # Technopark API scraper
│   ├── cutshort_fetcher.py   # Cutshort JSON parser
│   ├── notifier.py           # Daily email summary
│   ├── profile_manager.py    # Load/save profile.json
│   └── utils.py              # Shared helpers
├── dashboard/
│   ├── models.py             # Job, Application, SkillLog, DailyStats
│   ├── views.py              # All dashboard views
│   ├── urls.py               # URL routing
│   └── templates/            # 10 HTML templates
├── job_portal/               # Django project settings
├── static/style.css          # Dark theme CSS
├── resume/                   # Your resume PDFs (gitignored)
├── .env                      # Secrets (gitignored)
├── pyproject.toml            # Dependencies
└── manage.py
```

## Customization

### Change match thresholds

Edit `config/settings.py`:

```python
MATCH_THRESHOLD_TRACK = 50    # Minimum % to track a job
MATCH_THRESHOLD_APPLY = 65    # Minimum % to auto-apply
MIN_SALARY = 18000            # Minimum salary filter
MAX_SKILL_GAP_PCT = 40        # Skip jobs needing >40% unknown skills
```

### Add search queries

Edit `config/queries.py`:

```python
SEARCH_QUERIES = [
    "python developer",
    "django developer",
    # add more...
]
```

### Change role rejection keywords

Edit `config/constants.py`:

```python
REJECT_ROLE_KEYWORDS = [
    "data engineer", "devops", "java", ".net",
    # add more...
]
```

## Security

- `.env` — never committed (gitignored)
- `config/profile.py` — never committed (gitignored)
- `profile.json` — never committed (gitignored)
- `resume/*.pdf` — never committed (gitignored)
- `db.sqlite3` — never committed (gitignored)
- Django CSRF, X-Frame-Options, Content-Type nosniff, HttpOnly cookies all enabled
- No raw SQL, no eval/exec — uses Django ORM throughout

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License — Copyright (c) 2025 Dennis Joseph

See [LICENSE](LICENSE) for full terms. A mention of the original author is required if you use this project.

## Author

**Dennis Joseph** — Python Full-Stack Developer
- GitHub: [@dennisjoseph2025](https://github.com/dennisjoseph2025)
- LinkedIn: [dennisjoseph2025](https://www.linkedin.com/in/dennisjoseph2025)
