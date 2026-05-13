"""
Tests for POST /api/v1/employees/import

Covers: happy paths, validation errors, duplicate handling, and batch atomicity.
"""
import pytest

BASE = "/api/v1/employees"
IMPORT = f"{BASE}/import"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_employee(**kwargs):
    base = {"username": "jdoe", "name": "John Doe", "usercode": "EMP001"}
    return {**base, **kwargs}


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------

async def test_import_single_employee_returns_created_record(client):
    payload = [make_employee()]
    resp = await client.post(IMPORT, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["username"] == "jdoe"
    assert data[0]["name"] == "John Doe"
    assert data[0]["usercode"] == "EMP001"
    assert "created_at" in data[0]


async def test_import_multiple_employees(client):
    payload = [
        make_employee(username="alice", name="Alice", usercode="E001"),
        make_employee(username="bob",   name="Bob",   usercode="E002"),
        make_employee(username="carol", name="Carol", usercode="E003"),
    ]
    resp = await client.post(IMPORT, json=payload)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


async def test_import_optional_fields_absent(client):
    """Only required fields — department, ip, hostname default to null."""
    payload = [{"username": "min_user", "name": "Min User", "usercode": "E100"}]
    resp = await client.post(IMPORT, json=payload)
    assert resp.status_code == 200
    record = resp.json()[0]
    assert record["department"] is None
    assert record["ip"] is None
    assert record["hostname"] is None


async def test_import_all_fields(client):
    payload = [make_employee(
        username="full",
        name="Full Record",
        usercode="E200",
        department="Engineering",
        ip="192.168.1.10",
        hostname="pc-eng-01",
    )]
    resp = await client.post(IMPORT, json=payload)
    assert resp.status_code == 200
    record = resp.json()[0]
    assert record["department"] == "Engineering"
    assert record["ip"] == "192.168.1.10"
    assert record["hostname"] == "pc-eng-01"


async def test_import_empty_list_returns_empty_array(client):
    resp = await client.post(IMPORT, json=[])
    assert resp.status_code == 200
    assert resp.json() == []


async def test_imported_employees_appear_in_list(client):
    payload = [make_employee(username="visible", name="Visible User", usercode="E300")]
    await client.post(IMPORT, json=payload)

    resp = await client.get(BASE)
    assert resp.status_code == 200
    usernames = [e["username"] for e in resp.json()]
    assert "visible" in usernames


# ---------------------------------------------------------------------------
# Validation errors (422)
# ---------------------------------------------------------------------------

async def test_import_missing_username_returns_422(client):
    payload = [{"name": "No Username", "usercode": "E400"}]
    resp = await client.post(IMPORT, json=payload)
    assert resp.status_code == 422


async def test_import_missing_name_returns_422(client):
    payload = [{"username": "noname", "usercode": "E401"}]
    resp = await client.post(IMPORT, json=payload)
    assert resp.status_code == 422


async def test_import_missing_usercode_returns_422(client):
    payload = [{"username": "nocode", "name": "No Code"}]
    resp = await client.post(IMPORT, json=payload)
    assert resp.status_code == 422


async def test_import_wrong_body_type_returns_422(client):
    """Sending a single object instead of a list should fail."""
    resp = await client.post(IMPORT, json=make_employee())
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Duplicate handling (409)
# ---------------------------------------------------------------------------

async def test_import_duplicate_username_returns_409(client):
    payload = [make_employee()]
    await client.post(IMPORT, json=payload)

    resp = await client.post(IMPORT, json=payload)
    assert resp.status_code == 409
    assert "Duplicate username" in resp.json()["detail"]


async def test_duplicate_in_batch_rolls_back_entire_batch(client):
    """If one row in a batch conflicts, no rows from that batch should be saved."""
    # Seed one employee
    await client.post(IMPORT, json=[make_employee(username="existing", name="Existing", usercode="E500")])

    # Batch where second row duplicates the seeded employee
    batch = [
        make_employee(username="new_one", name="New One", usercode="E501"),
        make_employee(username="existing", name="Existing Again", usercode="E500"),
    ]
    resp = await client.post(IMPORT, json=batch)
    assert resp.status_code == 409

    # new_one must NOT have been persisted
    list_resp = await client.get(BASE)
    usernames = [e["username"] for e in list_resp.json()]
    assert "new_one" not in usernames


async def test_import_duplicate_within_same_batch_returns_409(client):
    """Two rows with the same username in one payload should also trigger 409."""
    payload = [
        make_employee(username="twin", name="Twin A", usercode="E601"),
        make_employee(username="twin", name="Twin B", usercode="E602"),
    ]
    resp = await client.post(IMPORT, json=payload)
    assert resp.status_code == 409
