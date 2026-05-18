import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import DATA_DIR
from app.main import create_app


@pytest.fixture
def test_db_dir() -> Generator[Path, None, None]:
    base_dir = DATA_DIR / "test_runs"
    base_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="pytest-", dir=base_dir))
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def build_client(test_db_dir: Path) -> TestClient:
    app = create_app(test_db_dir / "test.db")
    return TestClient(app)


def test_student_header_present_on_every_response(test_db_dir: Path) -> None:
    client = build_client(test_db_dir)

    response = client.get("/health")
    missing_document = client.get("/api/documents/999")

    assert response.status_code == 200
    assert response.headers["X-Student-ID"] == "BSCS23092"
    assert missing_document.status_code == 404
    assert missing_document.headers["X-Student-ID"] == "BSCS23092"


def test_naive_update_silently_loses_the_first_writer(test_db_dir: Path) -> None:
    client = build_client(test_db_dir)
    seeded = client.post("/api/admin/reset").json()["document"]
    document_id = seeded["id"]

    user_a_view = client.get(f"/api/documents/{document_id}").json()
    user_b_view = client.get(f"/api/documents/{document_id}").json()

    first_write = client.put(
        f"/api/documents/{document_id}/naive",
        json={
            "content": "Alice adds the distributed locking section.",
            "editor": "alice",
            "expected_version": user_a_view["version"],
        },
    )
    second_write = client.put(
        f"/api/documents/{document_id}/naive",
        json={
            "content": "Bob replaces the paragraph with his own version.",
            "editor": "bob",
            "expected_version": user_b_view["version"],
        },
    )
    final_state = client.get(f"/api/documents/{document_id}")

    assert first_write.status_code == 200
    assert second_write.status_code == 200
    assert final_state.json()["content"] == "Bob replaces the paragraph with his own version."
    assert final_state.json()["version"] == 3


def test_optimistic_lock_rejects_stale_second_write(test_db_dir: Path) -> None:
    client = build_client(test_db_dir)
    seeded = client.post("/api/admin/reset").json()["document"]
    document_id = seeded["id"]

    user_a_view = client.get(f"/api/documents/{document_id}").json()
    user_b_view = client.get(f"/api/documents/{document_id}").json()

    first_write = client.put(
        f"/api/documents/{document_id}/optimistic",
        json={
            "content": "Alice adds the conflict-resolution notes.",
            "editor": "alice",
            "expected_version": user_a_view["version"],
        },
    )
    second_write = client.put(
        f"/api/documents/{document_id}/optimistic",
        json={
            "content": "Bob submits his stale copy without refreshing.",
            "editor": "bob",
            "expected_version": user_b_view["version"],
        },
    )
    final_state = client.get(f"/api/documents/{document_id}")

    assert first_write.status_code == 200
    assert first_write.json()["version"] == 2
    assert second_write.status_code == 409
    conflict_body = second_write.json()["detail"]
    assert "Version conflict detected" in conflict_body["message"]
    assert conflict_body["current_document"]["version"] == 2
    assert final_state.json()["content"] == "Alice adds the conflict-resolution notes."
    assert final_state.json()["version"] == 2
