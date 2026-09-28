"""SQLite persistence for job metadata only; document bytes and passwords are excluded."""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.backend.domain.models import ConversionJob


class HistoryService:
    def __init__(self, database_path: Path, *, limit: int = 100) -> None:
        self.database_path = Path(database_path)
        self.limit = max(1, limit)
        self._lock = threading.RLock()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def entries(self, limit: int = 50) -> list[dict[str, object]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT job_id, operation, status, created_at, sources, outputs, duration_ms, error_code "
                "FROM job_history ORDER BY created_at DESC LIMIT ?",
                (max(0, limit),),
            ).fetchall()
        return [
            {
                "job_id": row[0],
                "operation": row[1],
                "status": row[2],
                "created_at": row[3],
                "sources": json.loads(row[4]),
                "outputs": json.loads(row[5]),
                "duration_ms": row[6],
                "error_code": row[7],
            }
            for row in rows
        ]

    def add(self, job: ConversionJob, *, duration_ms: int = 0) -> None:
        values = (
            job.id,
            job.operation.value,
            job.status.value,
            job.created_at.isoformat(),
            json.dumps([str(path) for path in job.source_files], ensure_ascii=False),
            json.dumps([str(path) for path in job.output_files], ensure_ascii=False),
            max(0, duration_ms),
            job.error_code,
        )
        with self._lock, self._connection() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO job_history "
                "(job_id, operation, status, created_at, sources, outputs, duration_ms, error_code) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                values,
            )
            connection.execute(
                "DELETE FROM job_history WHERE job_id NOT IN "
                "(SELECT job_id FROM job_history ORDER BY created_at DESC LIMIT ?)",
                (self.limit,),
            )

    def clear(self) -> None:
        with self._lock, self._connection() as connection:
            connection.execute("DELETE FROM job_history")

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=10)
        try:
            connection.execute("PRAGMA busy_timeout=10000")
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._lock, self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS job_history ("
                "job_id TEXT PRIMARY KEY, operation TEXT NOT NULL, status TEXT NOT NULL, "
                "created_at TEXT NOT NULL, sources TEXT NOT NULL, outputs TEXT NOT NULL, "
                "duration_ms INTEGER NOT NULL DEFAULT 0, error_code TEXT)"
            )
