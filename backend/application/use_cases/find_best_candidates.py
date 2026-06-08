import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from backend.api_exceptions import NotFound
from backend.application.use_cases.compare_cv import run_compare
from backend.infrastructure.config.settings import get_settings
from backend.infrastructure.database.db import get_db
from backend.infrastructure.observability.tracing import trace_span
from backend.infrastructure.rag.qdrant_service import get_qdrant_service

logger = logging.getLogger(__name__)

# Keys copied from each CompareResponse into a candidate entry.
_CANDIDATE_SCORE_KEYS = (
    "match_score",
    "qualification_scores",
    "matching_skills",
    "missing_skills",
    "strengths",
    "risks",
    "seniority_fit",
    "reasoning",
)


def find_best_candidates(jd_id: str, request_id: str = "") -> Dict[str, Any]:
    """Two-stage retrieval: RAG pre-filter (Qdrant) then LLM analysis (run_compare).

    1. Fetch the JD content from SQLite.
    2. Shortlist the closest resumes via cosine similarity in Qdrant.
    3. Run the existing compare pipeline on each shortlisted resume, concurrently
    4. Sort by match_score descending and return the top N.
    """
    settings = get_settings()
    with trace_span("find_best_candidates", request_id=request_id):
        jd = get_db().get_job_description(jd_id)
        if jd is None:
            raise NotFound(detail="Job description not found.")

        jd_content = jd["content"]
        shortlist = get_qdrant_service().find_similar_resumes(
            jd_content, top_k=settings.rag_top_k_prefilter
        )
        logger.info(
            "request_id=%s find_candidates jd_id=%s shortlisted=%d",
            request_id,
            jd_id,
            len(shortlist),
        )

        # Resolve the shortlisted resumes up front, on this thread: SQLite
        # connections are not safe to share across threads, whereas the compare
        # calls below touch only the (network-bound) LLM.
        resolved: List[Dict[str, Any]] = []
        for resume_id in shortlist:
            resume = get_db().get_resume(resume_id)
            if resume is None:
                # Vector store and SQLite drifted apart; skip the orphan chunk.
                logger.warning(
                    "request_id=%s shortlisted resume_id=%s missing in SQLite, skipping",
                    request_id,
                    resume_id,
                )
                continue
            resolved.append({"resume_id": resume_id, "resume": resume})

        def _compare(item: Dict[str, Any]) -> Dict[str, Any]:
            resume = item["resume"]
            compare_result = run_compare(
                {"job_description": jd_content, "resume": resume["content"]},
                request_id=request_id,
            )
            entry = {
                "resume_id": item["resume_id"],
                "candidate_name": resume.get("candidate_name") or "",
            }
            for key in _CANDIDATE_SCORE_KEYS:
                entry[key] = compare_result.get(key)
            return entry

        candidates: List[Dict[str, Any]] = []
        if resolved:
            with ThreadPoolExecutor(max_workers=len(resolved)) as executor:
                candidates = list(executor.map(_compare, resolved))

        candidates.sort(key=lambda c: c.get("match_score") or 0, reverse=True)
        top = candidates[: settings.rag_top_k_final]
        for rank, candidate in enumerate(top, start=1):
            candidate["rank"] = rank

        return {
            "jd_id": jd_id,
            "jd_title": jd.get("title") or "",
            "candidates": top,
        }
