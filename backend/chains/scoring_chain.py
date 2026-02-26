import json
import logging
from typing import Any, Dict, List

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from backend.parsers.json_parser import parse_match_response

logger = logging.getLogger(__name__)

SCORING_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", "{system_prompt}"),
        ("human", "{payload}"),
    ]
)
OUTPUT_PARSER = StrOutputParser()

LINE_SCORING_SYSTEM_PROMPT = """You are an expert hiring assessor for skill fit.

You will receive:
1) Job description text
2) Resume/CV text

Your objective:
- Evaluate candidate fit based ONLY on job-relevant skills, tools, technologies, and directly related hands-on experience.
- Ignore non-skill noise unless the job explicitly requires it (for example: generic personality claims, formatting quality, writing style, personal interests, unrelated achievements, location, demographics, and other non-job-related details).
- Prefer evidence-based scoring. If a skill is not clearly supported by resume evidence, score conservatively.
- Treat compensation/perks/policy/culture statements as NON-requirements and do not count them as candidate qualifications.
- If inputs include placeholders like [REDACTED_EMAIL], [REDACTED_PHONE], [REDACTED_URL], [REDACTED_COMPANY], ignore placeholders and focus on skill evidence only.

Mandatory scoring rules:
- Score each qualification line from 0 to 100.
- Use strict evidence levels:
  - 0-25: no credible evidence in the resume for this requirement
  - 26-50: weak or indirect evidence only
  - 51-75: moderate evidence, partially aligned
  - 76-90: strong evidence, clearly aligned
  - 91-100: very strong, explicit, repeated evidence
- Do not inflate scores for generic claims.
- Do not assume experience that is not explicitly or strongly implied in the resume text.
- If a requirement is clearly mandatory and missing, use a low score.
- If a qualification line is not a true skill/tool/experience requirement (examples: paid leave, flexible schedule, benefits, office policy), IGNORE that line completely (do not return it in qualification_scores).
- Never award high scores for eligibility to benefits or policy statements.

Output format:
Return ONLY one strict JSON object with EXACTLY these top-level keys:
- match_score: integer 0..100
- qualification_scores: array of objects with (include only true skill/tool/experience requirements):
  - qualification: string (infer requirement lines from the JD)
  - match_score: integer 0..100
  - reasoning: short factual sentence citing resume evidence or missing evidence
- matching_skills: array of strings (skills/tools in both JD and resume)
- missing_skills: array of strings (required/important JD skills not evidenced in resume)
- strengths: array of short bullet strings (skill-related only)
- risks: array of short bullet strings (skill-gap related only)
- seniority_fit: short string
- reasoning: short overall paragraph focused on skills fit only
- job_description_struct: object with keys:
  - required_skills: array of strings
  - preferred_skills: array of strings
  - responsibilities: array of strings
  - seniority: one of ["Junior", "Mid", "Senior", "Lead", "Principal", "Unknown"]
  - required_years_experience: integer
  - domain: short string
- resume_struct: object with keys:
  - skills: array of strings
  - tools: array of strings
  - roles: array of strings
  - industries: array of strings
  - years_of_experience: integer
  - seniority: one of ["Junior", "Mid", "Senior", "Lead", "Principal", "Unknown"]
  - education: array of strings
  - key_projects: array of short strings

Important:
- Keep output JSON-valid and parseable.
- No markdown, no prose outside JSON.
- No additional keys.
- Do not include personal identifiers from resume input (emails, phone numbers, personal URLs, home address) in any output field."""


def run_line_by_line_match_reasoning(
    chat_model: BaseChatModel,
    job_description: str,
    resume: str,
) -> Dict[str, Any]:
    user_payload = {
        "job_description": job_description,
        "resume": resume,
    }
    chain = SCORING_PROMPT_TEMPLATE | chat_model | OUTPUT_PARSER
    content = chain.invoke(
        {
            "system_prompt": LINE_SCORING_SYSTEM_PROMPT,
            "payload": json.dumps(user_payload),
        }
    ) or "{}"
    logger.info("Final reasoning raw content (truncated): %s", (content[:800] + ("..." if len(content) > 800 else "")))
    try:
        return parse_match_response(content)
    except Exception:
        logger.exception("Failed to parse reasoning response; returning minimal fallback.")
        return {
            "match_score": 0,
            "qualification_scores": [],
            "matching_skills": [],
            "missing_skills": [],
            "strengths": [],
            "risks": [],
            "seniority_fit": "Unknown",
            "reasoning": "Failed to parse model response.",
            "job_description_struct": {},
            "resume_struct": {},
        }


def normalise_qualification_scores(raw_scores: Any) -> List[Dict[str, Any]]:
    """Validate, clamp, and deduplicate qualification scores from LLM output."""
    normalised: List[Dict[str, Any]] = []
    if not isinstance(raw_scores, list):
        return normalised

    seen: set = set()
    for item in raw_scores:
        if not isinstance(item, dict):
            continue
        qualification = str(item.get("qualification") or "").strip()
        if not qualification:
            continue
        key = qualification.lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            score = max(0, min(100, int(item.get("match_score", 0))))
        except (TypeError, ValueError):
            score = 0
        reasoning = str(item.get("reasoning") or "").strip() or "No rationale returned."
        normalised.append(
            {
                "qualification": qualification,
                "match_score": score,
                "reasoning": reasoning,
            }
        )
    return normalised
