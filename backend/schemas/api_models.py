from dataclasses import dataclass
from typing import Any, Dict, List, Mapping

from backend.api_exceptions import BadRequest, JobDescriptionTooLong, ResumeTooLong


@dataclass(frozen=True)
class ModelSelection:
    provider: str
    model: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ModelSelection":
        return cls(
            provider=str(raw.get("provider", "")),
            model=str(raw.get("model", "")),
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "provider": self.provider,
            "model": self.model,
        }


@dataclass(frozen=True)
class CompareRequest:
    job_description: str
    resume: str

    @classmethod
    def from_payload(cls, payload: Any, *, max_input_length: int = 50_000) -> "CompareRequest":
        if payload is None:
            payload = {}
        if not isinstance(payload, Mapping):
            raise BadRequest(detail="Request body must be a JSON object.")

        job_description = str(payload.get("job_description") or "").strip()
        resume = str(payload.get("resume") or "").strip()
        if not job_description or not resume:
            raise BadRequest(detail="Both job_description and resume are required")
        if len(job_description) > max_input_length:
            raise JobDescriptionTooLong()
        if len(resume) > max_input_length:
            raise ResumeTooLong()

        return cls(job_description=job_description, resume=resume)


@dataclass(frozen=True)
class CompareResponse:
    match_score: int
    qualification_scores: List[Dict[str, Any]]
    matching_skills: List[str]
    missing_skills: List[str]
    strengths: List[str]
    risks: List[str]
    seniority_fit: str
    reasoning: str
    request_id: str
    models: ModelSelection

    @classmethod
    def from_pipeline_result(
        cls,
        result: Mapping[str, Any],
        models: ModelSelection,
    ) -> "CompareResponse":
        return cls(
            match_score=max(0, min(100, int(result.get("match_score") or 0))),
            qualification_scores=list(result.get("qualification_scores") or []),
            matching_skills=list(result.get("matching_skills") or []),
            missing_skills=list(result.get("missing_skills") or []),
            strengths=list(result.get("strengths") or []),
            risks=list(result.get("risks") or []),
            seniority_fit=str(result.get("seniority_fit") or ""),
            reasoning=str(result.get("reasoning") or ""),
            request_id=str(result.get("request_id") or ""),
            models=models,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_score": self.match_score,
            "qualification_scores": self.qualification_scores,
            "matching_skills": self.matching_skills,
            "missing_skills": self.missing_skills,
            "strengths": self.strengths,
            "risks": self.risks,
            "seniority_fit": self.seniority_fit,
            "reasoning": self.reasoning,
            "request_id": self.request_id,
            "models": self.models.to_dict(),
        }
