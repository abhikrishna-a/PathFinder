import logging

from django.shortcuts import get_object_or_404
from rest_framework import status

from apps.jobs.models import AIConfig, Job, Application
from apps.jobs.llm_client import generate_with_llm
from apps.jobs.views.base import BaseAPIView
from config.profile import PROFILE

logger = logging.getLogger(__name__)

COVER_LETTER_SYSTEM = """You are a professional cover letter writer for a software developer named Mohammed Swalih N K.

RULES:
- Write exactly 120-180 words. No more.
- Output ONLY the cover letter body text. No subject line, no markdown, no headers.
- Use a warm, confident, modern professional tone. Not stiff or old-fashioned.
- Never use "I am writing to express my interest" or "I am excited to apply" or similar generic openers.
- Never use emojis.
- Structure: Hook (1 sentence) -> Skills match + project proof (2-3 sentences) -> Call to action (1 sentence).
- Mention specific technologies from the job description.
- Mention relevant project experience naturally.
- End with name, email, phone, and GitHub on separate lines.

COVER LETTER FORMAT:
[Opening hook - reference the role and one strong matching skill]

[2-3 sentences: project experience with specific tech, matching JD requirements]

[1 sentence closing - confident, forward-looking]

Mohammed Swalih N K
swalink555@gmail.com | +91 8547368811
github.com/nkswalih"""


def _build_user_prompt(job) -> str:
    desc = (job.description or "")[:1500]
    matched = ", ".join(job.matched_skills[:8]) if job.matched_skills else "Python, Django"

    projects_text = ""
    for p in PROFILE.get("projects", []):
        projects_text += f"- {p['name']}: {p['description']} (Tech: {', '.join(p['tech'][:6])})\n"

    return f"""Write a cover letter for this job application:

Position: {job.title}
Company: {job.company}
Location: {job.location or 'Not specified'}
Required skills: {matched}

Job Description (excerpt):
{desc}

My profile:
- Full Stack Developer with 1 year experience at Bridgeon Solutions LLP, Kozhikode
- Top skills: Python, Django, DRF, React, PostgreSQL, Docker, AWS

My projects:
{projects_text}
Write the cover letter now. 120-180 words only."""


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

        user_prompt = _build_user_prompt(job)

        cover_letter = generate_with_llm(
            system_prompt=COVER_LETTER_SYSTEM,
            user_prompt=user_prompt,
            api_key=api_key,
            api_base_url=ai.api_base_url,
            model=ai.model_name,
        )

        if not cover_letter:
            return self.error(
                "AI generation failed. Check your API key and model in AI Settings.",
                status.HTTP_502_BAD_GATEWAY,
            )

        app, _ = Application.objects.get_or_create(job=job)
        app.cover_letter_text = cover_letter
        app.save(update_fields=["cover_letter_text"])

        return self.success({"cover_letter": cover_letter})
