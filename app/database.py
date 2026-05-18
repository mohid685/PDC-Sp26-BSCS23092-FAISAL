from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class DocumentRecord:
    id: int
    title: str
    content: str
    version: int
    last_editor: str
    updated_at: str


class DocumentStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.create_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def create_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    last_editor TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def reset_with_seed(self) -> DocumentRecord:
        with self._connect() as connection:
            connection.execute("DROP TABLE IF EXISTS documents")
            connection.commit()
        self.create_schema()
        return self.create_document(
            title="Distributed Systems Notes",
            content="Initial shared draft",
            editor="system",
        )

    def create_document(self, title: str, content: str, editor: str) -> DocumentRecord:
        timestamp = _utc_now()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO documents (title, content, version, last_editor, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, content, 1, editor, timestamp),
            )
            connection.commit()
            document_id = int(cursor.lastrowid)
        return self.get_document(document_id)

    def get_document(self, document_id: int) -> DocumentRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, title, content, version, last_editor, updated_at
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            ).fetchone()
        if row is None:
            return None
        return _row_to_document(row)

    def naive_update(self, document_id: int, content: str, editor: str) -> DocumentRecord | None:
        timestamp = _utc_now()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE documents
                SET content = ?, version = version + 1, last_editor = ?, updated_at = ?
                WHERE id = ?
                """,
                (content, editor, timestamp, document_id),
            )
            connection.commit()
            if cursor.rowcount == 0:
                return None
        return self.get_document(document_id)

    def optimistic_update(
        self,
        document_id: int,
        expected_version: int,
        content: str,
        editor: str,
    ) -> tuple[DocumentRecord | None, DocumentRecord | None]:
        timestamp = _utc_now()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE documents
                SET content = ?, version = version + 1, last_editor = ?, updated_at = ?
                WHERE id = ? AND version = ?
                """,
                (content, editor, timestamp, document_id, expected_version),
            )
            connection.commit()
            if cursor.rowcount == 0:
                return None, self.get_document(document_id)
        return self.get_document(document_id), None

    def list_documents(self) -> list[DocumentRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, content, version, last_editor, updated_at
                FROM documents
                ORDER BY id
                """
            ).fetchall()
        return [_row_to_document(row) for row in rows]

    def diagnostic_state(self) -> dict[str, Any]:
        documents = self.list_documents()
        return {
            "document_count": len(documents),
            "documents": [document.__dict__ for document in documents],
        }


def _row_to_document(row: sqlite3.Row) -> DocumentRecord:
    return DocumentRecord(
        id=int(row["id"]),
        title=str(row["title"]),
        content=str(row["content"]),
        version=int(row["version"]),
        last_editor=str(row["last_editor"]),
        updated_at=str(row["updated_at"]),
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
