"""One-shot seed script: download resumes + job descriptions from HuggingFace
and populate the backend DB + Qdrant RAG store.

Running this single script will:
  1. Download N resumes from `Sachinkelenjaguri/Resume_dataset`
  2. Download M job descriptions from `jacob-hugging-face/job-descriptions`
  3. POST each one to the running backend (SQLite + Qdrant embeddings)

Usage:
    # wipe existing records, download both + populate
    python scripts/populate.py
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import requests
from datasets import load_dataset

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTDATA = REPO_ROOT / "testdata"

RESUME_DATASET = "Sachinkelenjaguri/Resume_dataset"
JOB_DATASET = "jacob-hugging-face/job-descriptions"

JOB_TITLE_COL = "position_title"
JOB_CONTENT_COL = "job_description"

RESUME_TEXT_CANDIDATES = ("Resume", "Resume_str", "resume_text", "resume", "text", "content")
RESUME_NAME_CANDIDATES = ("candidate_name", "name", "Name", "full_name")


def _clean(text) -> str:
    return str(text or "").strip()


def _pick_resume_columns(features) -> tuple[str, str | None]:
    """Return (text_column, name_column_or_None) for an arbitrary resume dataset."""
    cols = list(features.keys())
    text_col = next((c for c in RESUME_TEXT_CANDIDATES if c in cols), None)
    if text_col is None:
        string_cols = [c for c, f in features.items() if getattr(f, "dtype", "") == "string"]
        if not string_cols:
            raise SystemExit(f"Could not find a text column in {RESUME_DATASET}; columns={cols}")
        text_col = string_cols[0]
    name_col = next((c for c in RESUME_NAME_CANDIDATES if c in cols), None)
    return text_col, name_col


# --- download ------------------------------------------------------------


def download_resumes(n: int) -> list[dict]:
    print(f"Downloading {n} resumes from {RESUME_DATASET} ...")
    ds = load_dataset(RESUME_DATASET, split="train")
    text_col, name_col = _pick_resume_columns(ds.features)
    print(f"  using text column '{text_col}'" + (f", name column '{name_col}'" if name_col else ""))

    out = []
    seen: set[str] = set()
    for i, row in enumerate(ds):
        content = _clean(row.get(text_col))
        if not content or content in seen:
            continue
        seen.add(content)
        name = _clean(row.get(name_col)) if name_col else ""
        out.append({"candidate_name": name or f"Candidate {len(out) + 1:02d}", "content": content})
        if len(out) >= n:
            break
    return out


def download_jobs(n: int) -> list[dict]:
    print(f"Downloading {n} job descriptions from {JOB_DATASET} ...")
    ds = load_dataset(JOB_DATASET, split="train")
    out = []
    seen: set[str] = set()
    for row in ds:
        content = _clean(row.get(JOB_CONTENT_COL))
        if not content or content in seen:
            continue
        seen.add(content)
        title = _clean(row.get(JOB_TITLE_COL)) or f"Job {len(out) + 1:02d}"
        out.append({"title": re.sub(r"\s+", " ", title)[:80], "content": content})
        if len(out) >= n:
            break
    return out


def save_copies(resumes: list[dict], jobs: list[dict]) -> None:
    """Keep a local .txt copy of what was ingested, for inspection."""
    (TESTDATA / "resumes").mkdir(parents=True, exist_ok=True)
    (TESTDATA / "jobs").mkdir(parents=True, exist_ok=True)
    for i, r in enumerate(resumes, 1):
        (TESTDATA / "resumes" / f"resume_{i:02d}.txt").write_text(r["content"], encoding="utf-8")
    for i, j in enumerate(jobs, 1):
        (TESTDATA / "jobs" / f"job_{i:02d}.txt").write_text(
            f"# TITLE: {j['title']}\n{j['content']}", encoding="utf-8"
        )


# --- populate ------------------------------------------------------------


def reset(base_url: str) -> None:
    """Delete every existing resume + JD (and their Qdrant chunks) before ingesting."""
    resumes = requests.get(f"{base_url}/api/v1/resumes", timeout=60).json()["data"]["resumes"]
    jobs = requests.get(f"{base_url}/api/v1/job-descriptions", timeout=60).json()["data"][
        "job_descriptions"
    ]
    for r in resumes:
        requests.delete(f"{base_url}/api/v1/resumes/{r['id']}", timeout=60).raise_for_status()
    for j in jobs:
        requests.delete(
            f"{base_url}/api/v1/job-descriptions/{j['id']}", timeout=60
        ).raise_for_status()
    print(f"Reset: deleted {len(resumes)} resume(s) and {len(jobs)} job description(s).")


def ingest_resumes(base_url: str, resumes: list[dict]) -> None:
    for r in resumes:
        resp = requests.post(f"{base_url}/api/v1/resumes", json=r, timeout=120)
        resp.raise_for_status()
        d = resp.json()["data"]
        print(f"  resume  {r['candidate_name']:>14}  id={d['resume_id']}  chunks={d['chunk_count']}")


def ingest_jobs(base_url: str, jobs: list[dict]) -> None:
    for j in jobs:
        resp = requests.post(f"{base_url}/api/v1/job-descriptions", json=j, timeout=120)
        resp.raise_for_status()
        d = resp.json()["data"]
        print(f"  job     {j['title'][:40]:>40}  id={d['jd_id']}  chunks={d['chunk_count']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:5000", help="backend base URL")
    parser.add_argument("--resumes", type=int, default=5, help="number of resumes to ingest")
    parser.add_argument("--jobs", type=int, default=3, help="number of job descriptions to ingest")
    parser.add_argument(
        "--no-save", action="store_true", help="do not write local .txt copies under testdata/"
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="keep existing resumes + JDs instead of wiping them first",
    )
    args = parser.parse_args()

    resumes = download_resumes(args.resumes)
    jobs = download_jobs(args.jobs)
    if not args.no_save:
        save_copies(resumes, jobs)

    if not args.no_reset:
        print("\nResetting existing records...")
        reset(args.base_url)

    print("\nIngesting resumes...")
    ingest_resumes(args.base_url, resumes)
    print("Ingesting job descriptions...")
    ingest_jobs(args.base_url, jobs)


if __name__ == "__main__":
    main()
