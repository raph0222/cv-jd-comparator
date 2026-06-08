"""
SQLite persistence for the RAG ("Find Best Candidates") feature.

Stores the raw text of job descriptions and resumes plus the Qdrant chunk ids
generated for each document. The vector store (Qdrant) only holds embeddings and
small payloads; SQLite remains the source of truth for document content.

A single connection is shared process-wide (singleton, mirroring ``get_settings``)
with ``check_same_thread=False`` so Flask/Gunicorn worker threads can reuse it.
"""
import json
import logging
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, List, Optional

from backend.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

_write_lock = threading.Lock()


_SCHEMA = """
CREATE TABLE IF NOT EXISTS job_descriptions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP,
    chunk_ids TEXT
);

CREATE TABLE IF NOT EXISTS resumes (
    id TEXT PRIMARY KEY,
    candidate_name TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMP,
    chunk_ids TEXT
);
"""


class Database:
    """Thin wrapper around a shared sqlite3 connection."""

    def __init__(self, path: str) -> None:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        logger.info("SQLite initialized at %s", path)

    # --- resumes ---------------------------------------------------------

    def insert_resume(
        self, candidate_name: str, content: str, chunk_ids: List[str], resume_id: Optional[str] = None
    ) -> str:
        resume_id = resume_id or str(uuid.uuid4())
        with _write_lock:
            self._conn.execute(
                "INSERT INTO resumes (id, candidate_name, content, created_at, chunk_ids) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    resume_id,
                    candidate_name,
                    content,
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(chunk_ids),
                ),
            )
            self._conn.commit()
        return resume_id

    def list_resumes(self) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id, candidate_name, created_at FROM resumes ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]

    def get_resume(self, resume_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT id, candidate_name, content, created_at, chunk_ids FROM resumes WHERE id = ?",
            (resume_id,),
        ).fetchone()
        return self._row_with_chunks(row)

    def delete_resume(self, resume_id: str) -> bool:
        with _write_lock:
            cur = self._conn.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
            self._conn.commit()
            return cur.rowcount > 0

    # --- job descriptions ------------------------------------------------

    def insert_job_description(
        self, title: str, content: str, chunk_ids: List[str], jd_id: Optional[str] = None
    ) -> str:
        jd_id = jd_id or str(uuid.uuid4())
        with _write_lock:
            self._conn.execute(
                "INSERT INTO job_descriptions (id, title, content, created_at, chunk_ids) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    jd_id,
                    title,
                    content,
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(chunk_ids),
                ),
            )
            self._conn.commit()
        return jd_id

    def list_job_descriptions(self) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id, title, created_at FROM job_descriptions ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]

    def get_job_description(self, jd_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT id, title, content, created_at, chunk_ids "
            "FROM job_descriptions WHERE id = ?",
            (jd_id,),
        ).fetchone()
        return self._row_with_chunks(row)

    def delete_job_description(self, jd_id: str) -> bool:
        with _write_lock:
            cur = self._conn.execute("DELETE FROM job_descriptions WHERE id = ?", (jd_id,))
            self._conn.commit()
            return cur.rowcount > 0

    # --- helpers ---------------------------------------------------------

    @staticmethod
    def _row_with_chunks(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        record = dict(row)
        record["chunk_ids"] = json.loads(record.get("chunk_ids") or "[]")
        return record


@lru_cache(maxsize=1)
def get_db() -> Database:
    return Database(get_settings().sqlite_path)


def reset_db() -> None:
    """Clear cached DB handle. Intended for test teardown."""
    get_db.cache_clear()
