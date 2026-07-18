import hashlib
import re

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

JUNK_DOMAINS = {
    "sentry.io", "wixpress.com", "example.com", "test.com",
    "squarespace.com", "wix.com", "godaddy.com", "googleapis.com",
    "cloudflare.com", "github.io", "herokuapp.com", "vercel.app",
    "netlify.app", "apple.com", "google.com", "microsoft.com",
    "amazonaws.com", "facebook.com", "meta.com", "samsung.com",
    "oracle.com", "ibm.com", "adobe.com", "salesforce.com",
    "vmware.com", "cognizant.com", "capgemini.com", "infosys.com",
    "wipro.com", "tcs.com", "techmahindra.com", "hcl.com",
    "accenture.com", "deloitte.com", "ey.com", "pwc.com",
    "kpmg.com", "mba.com", "no-reply", "donotreply",
    "mailer-daemon", "postmaster", "noreply",
}

SPAM_DOMAINS = [
    "linkedin.com", "indeed.com", "glassdoor.com", "naukri.com",
    "monster.com", "shine.com", "timesjobs.com", "foundit.in",
    "cutshort.io", "hirist.com", "instahyre.com", "cutshort.in",
    "wellfound.com", "angel.co", "ycombinator.com",
]


def is_company_email(email: str) -> tuple:
    """Validates whether an email is likely a real company email."""
    if not email or not isinstance(email, str):
        return False, "empty"

    email = email.strip().lower()

    if not EMAIL_REGEX.match(email):
        return False, "invalid format"

    domain = email.split("@")[-1]

    if domain in JUNK_DOMAINS:
        return False, f"junk domain: {domain}"

    if any(sd in domain for sd in SPAM_DOMAINS):
        return False, f"job board domain: {domain}"

    return True, "valid"


def make_uid(title: str, company: str, location: str = "") -> str:
    """Generate a unique ID for deduplication based on title + company + location."""
    raw = f"{title.lower().strip()}|{company.lower().strip()}|{location.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def clean_html(html_text: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    if not html_text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def html_to_markdown(html_text: str) -> str:
    """Convert HTML to markdown, preserving formatting."""
    if not html_text:
        return ""
    if "<" not in html_text:
        return html_text.strip()

    text = html_text

    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?p[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?div[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?li[^>]*>', '\n- ', text, flags=re.IGNORECASE)
    text = re.sub(r'</?[ou]l[^>]*>', '\n', text, flags=re.IGNORECASE)

    text = re.sub(r'<a\s+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE)
    text = re.sub(r'</?b[^>]*>', '**', text, flags=re.IGNORECASE)
    text = re.sub(r'</?strong[^>]*>', '**', text, flags=re.IGNORECASE)
    text = re.sub(r'</?i[^>]*>', '*', text, flags=re.IGNORECASE)
    text = re.sub(r'</?em[^>]*>', '*', text, flags=re.IGNORECASE)

    text = re.sub(r'<[^>]+>', '', text)

    import html as html_mod
    text = html_mod.unescape(text)

    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[^\S\n]+', ' ', text)
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    return text.strip()


def safe_console(text: str) -> str:
    """Make text safe for Windows console output."""
    try:
        return str(text).encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        return str(text)
