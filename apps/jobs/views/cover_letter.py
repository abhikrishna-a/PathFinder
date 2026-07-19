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


def _compute_skill_gap(job) -> tuple[str, str]:
    """Compare job requirements against candidate profile.
    Returns (candidate_has, candidate_missing) as comma-separated strings."""
    candidate_skills_lower = set()
    for cat_skills in PROFILE.get("skills", {}).values():
        for s in cat_skills:
            candidate_skills_lower.add(s.lower())

    has_set = set()
    for s in (job.matched_skills or []):
        has_set.add(s)

    missing_set = set()
    for s in (job.skill_gaps or []):
        missing_set.add(s)

    desc = (job.description or "").lower()
    extra_keywords = {
        "rust", "go", "golang", "java", "scala", "ruby", "php", "c++",
        "graphql", "grpc", "mongodb", "cassandra", "neo4j", "elasticsearch",
        "kubernetes", "k8s", "terraform", "gcp", "azure", "flutter",
        "swift", "kotlin", "selenium", "cypress", "playwright",
        "kafka", "rabbitmq", "airflow", "spark", "hadoop",
        "tableau", "power bi", "blockchain", "web3",
    }
    for kw in extra_keywords:
        if re.search(rf"\b{re.escape(kw)}\b", desc) and kw not in candidate_skills_lower:
            display = kw.upper() if kw in ("go", "golang", "c++") else kw.title()
            if kw == "k8s":
                display = "Kubernetes"
            missing_set.add(display)

    has_lower = {s.lower() for s in has_set}
    missing_set = {s for s in missing_set if s.lower() not in has_lower}

    has_list = sorted(has_set, key=str.lower)
    missing_list = sorted(missing_set, key=str.lower)

    has_text = ", ".join(has_list) if has_list else "None"
    missing_text = ", ".join(missing_list) if missing_list else "None -- candidate matches all listed requirements"

    return has_text, missing_text


def _build_system_prompt() -> str:
    name = PROFILE.get("name", "Developer")
    phone = PROFILE.get("phone", "")
    email = PROFILE.get("email", "")
    portfolio = PROFILE.get("portfolio", "")
    github = PROFILE.get("github", "")
    linkedin = PROFILE.get("linkedin", "")

    signature_lines = [name]
    if phone:
        signature_lines.append(phone)
    if email:
        signature_lines.append(email)
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
- The letter must always begin with the line "Dear Hiring Manager," -- never omit this, even when varying the rest of the opening.
- NEVER use "I am writing to express my interest" or "I am excited to apply".
- NEVER use emojis, markdown formatting, bold, bullet points, or dashes (--) around descriptions.
- Plain text only, ATS-friendly.

STRUCTURE (4-5 short paragraphs, under 180 words body):
1. SALUTATION (mandatory, always first): The very first line of the letter must be exactly "Dear Hiring Manager," on its own line, followed by a blank line. This line is never optional and is never varied, skipped, or merged into the next sentence. Only the sentence that comes AFTER the salutation should vary and reference a specific JD detail -- the salutation itself stays fixed every time.
2. Opening paragraph (comes after the salutation line): Reference something SPECIFIC from the job description -- a named technology they use, the domain they operate in, or a problem they describe. Do NOT open with "I am applying for the {{title}} position at {{company}}" every time. Vary your opening sentence.
3. Body: Connect your most relevant project(s) and skills to what this specific job needs. Choose which project(s) to highlight based on relevance to THIS job, not a fixed order.
4. If the JD mentions Docker, AWS, CI/CD, Kubernetes, or DevOps -- naturally weave in relevant DevOps experience. If it mentions AI/ML/LLM -- naturally weave in relevant AI experience. Only mention what is relevant.
5. Closing: A brief, confident close. Vary it between letters -- do NOT always use the same closing sentence.

BANNED:
- "I am genuinely interested in contributing to X and happy to discuss how I can add value from day one" -- never use this closer.
- "I am writing to express my interest in the X position" -- never use this opener.
- "Dear Hiring Manager at {{company}}" -- always use exactly "Dear Hiring Manager," and let the company name appear naturally within the first paragraph.
- Any sentence that could apply to literally any job without changes.
- Passive or indirect openers like "As I read about X, I am reminded of..." or "I was impressed by...". Open with a direct, confident statement connecting a specific JD detail to a specific thing you built or done -- active voice, no throat-clearing. Example: "Convosight's focus on [JD detail] is close to what I built with [project] -- [specific result]." Get to a concrete detail in the first sentence.
- Stacking more than one soft/eager phrase in the same letter. Phrases like "I believe my experience aligns with," "I am confident that," "I am excited to bring," and "I would be a strong fit" are each acceptable ONCE per letter, never twice, never back-to-back in adjacent sentences. Pick the single strongest one and cut the rest -- replace with a concrete statement (a result, a number, a specific technology used).
- Generic closing lines like "I look forward to discussing my qualifications further" or "I look forward to discussing how I can contribute." The closing sentence must reference one specific responsibility, technology, or goal from the JD that has NOT been mentioned earlier in the letter, framed as what you are looking forward to working on.

NO REPETITION:
- Do not repeat any phrase, sentence fragment, or distinctive wording from the job description more than once in the entire letter. If you reference a JD detail (a technology, a responsibility, a stated need) in one paragraph, do not paraphrase or restate that same detail again later -- move on to a new point instead.
- Before finalizing, mentally check: does any sentence in paragraph 2 or later restate an idea already covered in paragraph 1? If so, cut it or replace it with a new point.
- The closing paragraph must reference something specific and different from what was already said -- not a generic restatement like "I am looking forward to discussing how my expertise can benefit {{company}}." Tie it to a concrete next step or a specific value point not yet mentioned.

ACRONYM RULES:
- Never expand, define, or explain an acronym or technical term unless the exact expansion is explicitly given in the job description or candidate profile provided to you.
- If a term appears only as an acronym (e.g. RAG, LLM, CI/CD, DRF, RBAC), use it as-is without spelling out what it stands for.
- Do not guess expansions. Incorrect expansions (e.g. inventing a wrong full form for an acronym) are worse than using the acronym alone.
- This applies especially to RAG -- RAG must NEVER be expanded or defined in your output under any circumstances, even if you believe you know what it stands for. Write 'RAG' alone, exactly as given, with no parenthetical expansion, ever. Do NOT write "Retrieval-Augmented Generation", "Real-time Agents", "Rhetorical Argument Generation", or any other expansion. Just RAG.

SKILL GAP RULE -- MANDATORY, NON-NEGOTIABLE:
You are given two lists: SKILLS THE CANDIDATE HAS THAT MATCH THIS JOB, and SKILLS THIS JOB REQUIRES THAT THE CANDIDATE DOES NOT HAVE.
- You may ONLY write about skills from the first list as things the candidate has, uses, or has experience with.
- Every skill name in the second list is FORBIDDEN to appear anywhere in your output, in any form -- not as something the candidate has, not as something that 'aligns with' their experience, not quoted from the job description, not implied, not mentioned as a learning goal. Treat each name in that list as a word you are not allowed to write.
- Before you finalize your response, re-read it and check: does any sentence contain a word from the missing-skills list? If yes, rewrite that sentence to remove it entirely and replace it with a point about a skill from the has-list instead.
- Do not summarize or paraphrase the job's full requirement line (e.g. 'backend services in X, Y, and Z') if it contains any missing skill -- instead reference only the specific matching skills from that same line, worded as your own list, not the job's list.
- This rule overrides any instinct to sound comprehensive or to mirror the job description's phrasing. Precision about actual skills matters more than matching every word of the JD.

NUMERIC CLAIM RULE -- MANDATORY, NON-NEGOTIABLE:
- Every number, percentage, statistic, or measurable claim in your output (e.g. '40%', 'sub-100ms', '500K+ LOC', '99%+ completion', '35 percent') must appear VERBATIM in the PROJECTS or EXPERIENCE data given to you below, attached to the exact same achievement it describes there.
- You are FORBIDDEN from moving a number from one achievement to a different achievement, combining two numbers, rounding a number, or inventing a new number that doesn't appear in the source data at all.
- If you want to mention an achievement that has a number attached in the source data, you must keep the number attached to the SAME technology/action it was originally paired with. Do not detach '40 percent' from 'reduced initial page load' and reattach it to 'deployment time' or any other claim.
- If no specific number supports the point you want to make, make the point WITHOUT a number rather than inventing one. A qualitative claim with no number is always safer and more honest than a fabricated statistic.
- Before finalizing, check every number in your draft against the source data: can you point to the exact sentence in PROJECTS/EXPERIENCE it came from, attached to the same claim? If not, delete it or rewrite without it.

TONE -- WRITE LIKE A HUMAN, NOT AN AI:
- Write the way a sharp engineer would actually write to a hiring manager they respect -- direct, specific, a little informal in rhythm, not corporate-polished.
- Vary sentence length deliberately. Follow a longer sentence with a short one. Avoid three sentences in a row with the same length and structure -- that rhythm is a known AI tell.
- Do not use inflated adjectives that add no information: 'passionate', 'thrilled', 'excited to leverage', 'robust', 'seamless', 'cutting-edge', 'dynamic', 'comprehensive'. If a sentence still makes sense with the adjective deleted, delete it.
- Do not use symmetric three-part lists for their own rhythm ('design, build, and ship' / 'fast, reliable, and scalable') unless all three words are doing distinct, necessary work -- these are a strong AI-writing tell when overused.
- Avoid corporate transition phrases: 'Furthermore', 'Moreover', 'In addition to this', 'It is worth noting that'. Just state the next point directly.
- Every sentence should contain either a specific technical detail, a real outcome, or a direct connection to something the job actually asks for. If a sentence could be deleted without losing any specific information, delete it.
- One instance of genuine personality or specific curiosity about the company/problem is good (e.g. naming a real detail from the JD that's interesting, not just matching keywords). Flattery without specifics ('I'm impressed by your innovative culture') is banned.

PROJECT ATTRIBUTION RULE:
- Each project can only be described using the technologies and responsibilities listed for that specific project in the PROJECTS section of the prompt.
- Do not attribute a skill, technology, or responsibility to a project unless it is explicitly listed under that project's own entry.
- If a skill is only mentioned in the candidate's general skills list or under a different project or experience, either mention it generally without tying it to the wrong project, or attribute it to the correct project or role it actually belongs to.
- Never write "in Project X, I used Skill Y" if Skill Y does not appear in Project X's Tech line.

LOCATION RULE:
- Only make a claim about relocation, remote availability, or being 'based in' a location if the candidate's actual location and relocation preference are given to you explicitly below.
- Never state a firm commitment like 'I am ready to relocate to X' unless explicitly told the candidate is open to relocation. If relocation openness is not specified, either use soft, non-committal phrasing (e.g. 'happy to discuss location/relocation details') or omit location commentary entirely -- do not invent a decision on the candidate's behalf.
- Never name a specific city as a place the candidate is 'ready to relocate to' unless that is the job's actual stated location, given to you below, AND the candidate's relocation preference explicitly allows it.

AVAILABILITY RULE:
- Only make a claim about notice period, start date, or ability to join immediately if the candidate's actual availability is given to you explicitly below.
- Never state 'I am comfortable joining immediately' or 'I can start right away' or any similar claim unless the candidate's provided availability explicitly supports it.
- If availability is unspecified or indicates a notice period, either omit availability commentary entirely, or phrase it accurately and non-committally (e.g. 'happy to discuss timeline and availability further'). Do not round a notice period down to 'immediate' or invent urgency the candidate hasn't stated.

SENIORITY AWARENESS RULE:
- If the job title includes a seniority marker (Senior, Staff, Lead, Principal, etc.) and the candidate's total experience (given below) is under 3 years, do not write the letter as if seniority is a non-issue.
- In this case, spend one sentence making an honest, specific case for depth over tenure -- e.g. citing the scope or complexity of a real project (architecture decisions, scale numbers, ownership of a full system) rather than years. Do not apologize for experience level or draw attention to it as a weakness. Do not ignore it either -- make the strongest honest case that complexity of work compensates for fewer years, using only real details from the candidate's projects/experience data.
- If the candidate's experience level roughly matches or exceeds what the title implies, this rule does not apply -- write normally.

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
        if e.get("duration"):
            exp_text += f" ({e['duration']})"

    desc = (job.description or "")[:3000]

    candidate_has, candidate_missing = _compute_skill_gap(job)

    projects_text = ""
    for p in PROFILE.get("projects", []):
        projects_text += (
            f"- {p['name']}: {p['description']} "
            f"(Tech: {', '.join(p['tech'][:8])})\n"
        )

    experience_text = ""
    for e in experience:
        experience_text += (
            f"- {e.get('role', role)} at {e.get('company', 'Unknown')}, "
            f"{e.get('location', location)}"
        )
        if e.get("duration"):
            experience_text += f" ({e['duration']})"
        experience_text += "\n"

    return f"""Write a cover letter for this specific job application.

JOB:
Company: {job.company}
Title: {job.title}
Location: {job.location or 'Not specified'}

JOB DESCRIPTION:
{desc}

CANDIDATE:
Name: {name}
Role: {role}
Experience: {experience_years} year(s) -- {exp_text}
CANDIDATE TOTAL EXPERIENCE: {experience_years} year(s)
CANDIDATE LOCATION: {PROFILE.get('location', 'Not specified')}
OPEN TO RELOCATION: {PROFILE.get('open_to_relocation', 'Not specified')}
CANDIDATE AVAILABILITY: {PROFILE.get('availability', 'Not specified')}

SKILLS THE CANDIDATE HAS THAT MATCH THIS JOB: {candidate_has}
SKILLS THIS JOB REQUIRES THAT THE CANDIDATE DOES NOT HAVE: {candidate_missing}

PROJECTS:
{projects_text}
EXPERIENCE:
{experience_text}
INSTRUCTIONS:
- You may ONLY write about skills from the has-list above. The missing-skills list is FORBIDDEN in your output.
- Identify 1-2 specific details from the job description above and reference at least one directly in your opening.
- Choose which project(s) to lead with based on relevance to THIS job's matched skills, not a fixed order.
- Keep it under 180 words in the body (excluding signature).
- Use the signature block provided in the system prompt exactly as-is.
- Do NOT add any text before or after the cover letter."""


def _check_project_attribution(letter: str) -> list[str]:
    """Scan the letter for project-name mentions and flag if a skill appears in the
    same sentence/vicinity that isn't in that project's actual tech list per PROFILE.
    Returns a list of warning strings (does not modify the letter)."""
    warnings = []
    projects = PROFILE.get("projects", [])
    sentences = re.split(r'(?<=[.!?])\s+', letter)
    for p in projects:
        proj_name = p["name"]
        proj_tech_lower = {t.lower() for t in p.get("tech", [])}
        for sent in sentences:
            if proj_name.lower() in sent.lower():
                all_known_terms = set()
                for other_p in projects:
                    all_known_terms.update(t.lower() for t in other_p.get("tech", []))
                for cat_skills in PROFILE.get("skills", {}).values():
                    all_known_terms.update(s.lower() for s in cat_skills)
                for term in all_known_terms:
                    if term in sent.lower() and term not in proj_tech_lower:
                        warnings.append(
                            f"Possible misattribution: '{term}' mentioned near "
                            f"'{proj_name}' but not in {proj_name}'s tech list"
                        )
    return warnings


_COVERAGE_KEYWORDS = {
    "test": ["test", "testing", "unit test", "integration test", "end-to-end", "e2e"],
    "ci/cd": ["ci/cd", "ci cd", "continuous integration", "continuous deployment", "pipeline"],
    "security": ["security", "compliance", "owasp", "vulnerability", "authentication"],
    "accessibility": ["accessibility", "a11y", "wcag", "screen reader"],
    "monitoring": ["monitoring", "observability", "logging", "alerting", "apm"],
    "documentation": ["documentation", "docs", "technical writing"],
    "agile": ["agile", "scrum", "sprint", "kanban"],
}


def _check_requirement_coverage(job, letter: str) -> list[str]:
    """Check if core JD requirements are addressed in the letter.
    Returns a list of warning strings (does not modify the letter)."""
    warnings = []
    desc = (job.description or "").lower()
    letter_lower = letter.lower()

    for category, keywords in _COVERAGE_KEYWORDS.items():
        jd_requires = False
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", desc):
                jd_requires = True
                break

        if not jd_requires:
            continue

        letter_addresses = False
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", letter_lower):
                letter_addresses = True
                break

        if not letter_addresses:
            warnings.append(
                f"JD requires '{category}' but letter does not address it"
            )

    return warnings


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

        cover_letter, llm_error = generate_with_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            api_key=api_key,
            api_base_url=ai.api_base_url,
            model=ai.model_name,
            provider=ai.provider,
        )

        if not cover_letter:
            if llm_error and "413" in llm_error:
                msg = "Prompt too large for your model's token limit. Try a model with higher limits (e.g. Groq paid tier, DeepSeek, or OpenRouter) or switch to a model with a larger context window."
            elif llm_error and "429" in llm_error:
                msg = "Rate limited by your AI provider. Wait a moment and try again, or upgrade your plan."
            elif llm_error and "timeout" in llm_error.lower():
                msg = "AI request timed out. Try again."
            elif llm_error and "401" in llm_error:
                msg = "Invalid API key. Check your API key in Profile > AI Settings."
            else:
                msg = f"AI generation failed: {llm_error}" if llm_error else "AI generation failed. Check your API key and model in AI Settings."
            return self.error(msg, status.HTTP_502_BAD_GATEWAY)

        cover_letter = _clean_cover_letter(cover_letter)

        attr_warnings = _check_project_attribution(cover_letter)
        if attr_warnings:
            logger.warning(
                "Project attribution warnings for job %d (%s): %s",
                job.id, job.company, "; ".join(attr_warnings),
            )

        coverage_warnings = _check_requirement_coverage(job, cover_letter)
        if coverage_warnings:
            logger.warning(
                "Requirement coverage warnings for job %d (%s): %s",
                job.id, job.company, "; ".join(coverage_warnings),
            )

        app, _ = Application.objects.get_or_create(job=job)
        app.cover_letter_text = cover_letter
        app.save(update_fields=["cover_letter_text"])

        return self.success({"cover_letter": cover_letter})
