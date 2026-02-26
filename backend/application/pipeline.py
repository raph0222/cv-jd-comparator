from typing import Dict, Any

from backend.chains.scoring_chain import normalise_qualification_scores, run_line_by_line_match_reasoning
from backend.llm.factory import get_chat_model


def run_match_pipeline(
    model: str,
    job_description: str,
    resume: str,
) -> Dict[str, Any]:
    reasoning_model = get_chat_model(model, temperature=0.2)

    final_result = run_line_by_line_match_reasoning(
        reasoning_model,
        job_description,
        resume,
    )

    jd_struct = final_result.get("job_description_struct") or {}
    resume_struct = final_result.get("resume_struct") or {}
    qualification_scores = normalise_qualification_scores(
        final_result.get("qualification_scores"),
    )

    try:
        match_score = max(0, min(100, int(final_result.get("match_score", 0))))
    except (TypeError, ValueError):
        match_score = 0

    return {
        "match_score": match_score,
        "qualification_scores": qualification_scores,
        "matching_skills": final_result.get("matching_skills", []),
        "missing_skills": final_result.get("missing_skills", []),
        "strengths": final_result.get("strengths", []),
        "risks": final_result.get("risks", []),
        "seniority_fit": final_result.get("seniority_fit", ""),
        "reasoning": final_result.get("reasoning", ""),
        "job_description_struct": jd_struct,
        "resume_struct": resume_struct,
    }
