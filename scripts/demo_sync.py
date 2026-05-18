from fastapi.testclient import TestClient

from app.main import create_app


def main() -> None:
    client = TestClient(create_app())

    print("=== Reset demo state ===")
    seeded = client.post("/api/admin/reset").json()["document"]
    document_id = seeded["id"]
    print(f"Seeded document #{document_id} at version {seeded['version']}")

    print("\n=== Failure case: naive endpoint silently loses an update ===")
    user_a_view = client.get(f"/api/documents/{document_id}").json()
    user_b_view = client.get(f"/api/documents/{document_id}").json()
    print(f"User A sees version {user_a_view['version']}")
    print(f"User B sees version {user_b_view['version']}")

    first_write = client.put(
        f"/api/documents/{document_id}/naive",
        json={
            "content": "Alice writes a concurrency-safe summary.",
            "editor": "alice",
            "expected_version": user_a_view["version"],
        },
    ).json()
    second_write = client.put(
        f"/api/documents/{document_id}/naive",
        json={
            "content": "Bob overwrites the same paragraph with stale data.",
            "editor": "bob",
            "expected_version": user_b_view["version"],
        },
    ).json()
    final_naive = client.get(f"/api/documents/{document_id}").json()
    print(f"First write stored version {first_write['version']}")
    print(f"Second write stored version {second_write['version']}")
    print(f"Final naive content: {final_naive['content']}")

    print("\n=== Recovery case: optimistic locking rejects stale write ===")
    seeded = client.post("/api/admin/reset").json()["document"]
    document_id = seeded["id"]
    user_a_view = client.get(f"/api/documents/{document_id}").json()
    user_b_view = client.get(f"/api/documents/{document_id}").json()

    first_write = client.put(
        f"/api/documents/{document_id}/optimistic",
        json={
            "content": "Alice writes a concurrency-safe summary.",
            "editor": "alice",
            "expected_version": user_a_view["version"],
        },
    )
    second_write = client.put(
        f"/api/documents/{document_id}/optimistic",
        json={
            "content": "Bob tries to save his stale copy.",
            "editor": "bob",
            "expected_version": user_b_view["version"],
        },
    )
    final_fixed = client.get(f"/api/documents/{document_id}").json()

    print(f"First write status: {first_write.status_code}")
    print(f"Second write status: {second_write.status_code}")
    print(f"Conflict payload: {second_write.json()['detail']['message']}")
    print(f"Final protected content: {final_fixed['content']}")


if __name__ == "__main__":
    main()
