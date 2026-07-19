import logging
import re

from django.shortcuts import get_object_or_404
from rest_framework import status

from apps.jobs.models import AIConfig, Job, Application
from apps.jobs.llm_client import generate_with_llm
from apps.jobs.views.base import BaseAPIView
from config.profile import PROFILE

logger = logging.getLogger(__name__)


def _clean_cover_letter(text: str) -> str:
    text = re.sub(r"\s*--\s*", ", ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _build_system_prompt() -> str:
    name = PROFILE.get("name", "Developer")
    phone = PROFILE.get("phone", "")
    email = PROFILE.get("email", "")
    portfolio = PROFILE.get("portfolio", "")
    github = PROFILE.get("github", "")
    linkedin = PROFILE.get("linkedin", "")

    phone_line = f" | {phone}" if phone else ""
    signature_lines = [f"{name}{phone_line} | {email}"]
    if portfolio:
        signature_lines.append(portfolio)
    if github:
        signature_lines.append(f"GitHub: {github}")
    if linkedin:
        signature_lines.append(f"LinkedIn: {linkedin}")
    signature = "\n".join(signature_lines)

    return f"""You are a professional cover letter writer for a software developer.

OUTPUT RULES:
- Output ONLY the cover letter. No labels, no analysis, no commentary.
- NEVER output <think> or <thinking> or <thought> tags. Just the letter itself.
- NEVER use "I am writing to express my interest" or "I am excited to apply".
- NEVER use emojis, markdown formatting, bold, bullet points, or dashes (--) around descriptions.
- Plain text only, ATS-friendly.

STRUCTURE (4-5 short paragraphs, under 180 words body):
1. Opening: Reference something SPECIFIC from the job description — a named technology they use, the domain they operate in, or a problem they describe. Do NOT open with "I am applying for the {{title}} position at {{company}}" every time. Vary your opening sentence.
2. Body: Connect your most relevant project(s) and skills to what this specific job needs. Choose which project(s) to highlight based on relevance to THIS job, not a fixed order.
3. If the JD mentions Docker, AWS, CI/CD, Kubernetes, or DevOps — naturally weave in relevant DevOps experience. If it mentions AI/ML/LLM — naturally weave in relevant AI experience. Only mention what is relevant.
4. Closing: A brief, confident close. Vary it between letters — do NOT always use the same closing sentence.

BANNED:
- "I am genuinely interested in contributing to X and happy to discuss how I can add value from day one" — never use this closer.
- "I am writing to express my interest in the X position" — never use this opener.
- "Dear Hiring Manager at {{company}}" — always use exactly "Dear Hiring Manager," and let the company name appear naturally within the first paragraph.
- Any sentence that could apply to literally any job without changes.

NO REPETITION:
- Do not repeat any phrase, sentence fragment, or distinctive wording from the job description more than once in the entire letter. If you reference a JD detail (a technology, a responsibility, a stated need) in one paragraph, do not paraphrase or restate that same detail again later — move on to a new point instead.
- Before finalizing, mentally check: does any sentence in paragraph 2 or later restate an idea already covered in paragraph 1? If so, cut it or replace it with a new point.
- The closing paragraph must reference something specific and different from what was already said — not a generic restatement like "I am looking forward to discussing how my expertise can benefit {{company}}." Tie it to a concrete next step or a specific value point not yet mentioned.

SIGNATURE (append exactly as-is at the end of the letter):
{signature}"""


def _build_user_prompt(job) -> str:
    name = PROFILE.get("name", "Developer")
    location = PROFILE.get("location", "India")
    role = PROFILE.get("role", "Full Stack Developer")
    experience_years = PROFILE.get("experience_years", 1)

    experience = PROFILE.get("experience", [])
    exp_text = ""
    if experience:
        e = experience[0]
        exp_text = f"{e.get('role', role)} at {e.get('company', 'Unknown')}, {e.get('location', location)}"

    all_skills = []
    for cat_skills in PROFILE.get("skills", {}).values():
        all_skills.extend(cat_skills)
    core_skills = ", ".join(all_skills[:10])

    desc = (job.description or "")[:3000]
    matched = ", ".join(job.matched_skills[:10]) if job.matched_skills else "Python, Django"

    projects_text = ""
    for p in PROFILE.get("projects", []):
        projects_text += (
            f"- {p['name']}: {p['description']} "
            f"(Tech: {', '.join(p['tech'][:8])})\n"
        )

    return f"""Write a cover letter for this specific job application.

JOB:
Company: {job.company}
Title: {job.title}
Location: {job.location or 'Not specified'}
Matched skills: {matched}

JOB DESCRIPTION:
{desc}

CANDIDATE:
Name: {name}
Role: {role}
Experience: {experience_years} year(s) — {exp_text}
Core skills: {core_skills}

PROJECTS:
{projects_text}
INSTRUCTIONS:
- Identify 1-2 specific details from the job description above and reference at least one directly in your opening.
- Choose which project(s) to lead with based on relevance to THIS job's matched skills, not a fixed order.
- Keep it under 180 words in the body (excluding signature).
- Use the signature block provided in the system prompt exactly as-is.
- Do NOT add any text before or after the cover letter."""


class GenerateCoverLetter(BaseAPIView):
    def post(self, request, job_id):
        ai = AIConfig.load()
        if not ai.has_ai_config:
            return self.error(
                "AI not configured. Set your API key in Profile > AI Settings.",
                status.HTTP_400_BAD_REQUEST,
            )

        job = get_object_or_404(Job.objects.select_related(), id=job_id)

        api_key = ai.get_api_key()
        if not api_key:
            return self.error(
                "Could not decrypt API key. Please re-save your AI Settings.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        system_prompt = _build_system_prompt()
        user_prompt = _build_user_prompt(job)

        cover_letter = generate_with_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            api_key=api_key,
            api_base_url=ai.api_base_url,
            model=ai.model_name,
            provider=ai.provider,
        )

        if not cover_letter:
            return self.error(
                "AI generation failed. Check your API key and model in AI Settings.",
                status.HTTP_502_BAD_GATEWAY,
            )

        cover_letter = _clean_cover_letter(cover_letter)

        app, _ = Application.objects.get_or_create(job=job)
        app.cover_letter_text = cover_letter
        app.save(update_fields=["cover_letter_text"])

        return self.success({"cover_letter": cover_letter})
