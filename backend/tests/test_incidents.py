import pytest


async def create_test_user(client, email="inc@test.com", team="Inc Team"):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Test User",
            "team_name": team,
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "password123",
        },
    )
    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_list_incidents_empty(client):
    token = await create_test_user(client, "list@test.com", "List Team")
    response = await client.get(
        "/api/v1/incidents", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_incident_state_machine_valid(client):
    token = await create_test_user(client, "sm@test.com", "SM Team")
    headers = {"Authorization": f"Bearer {token}"}

    # Ingest alert to create incident
    await client.post(
        "/api/v1/alerts/ingest",
        json={
            "source": "prometheus",
            "name": "TestAlert",
            "service_name": "test-service",
            "priority": "P2",
            "labels": {},
        },
        headers=headers,
    )

    # Acknowledge
    response = await client.patch(
        "/api/v1/incidents/1/status",
        json={"status": "acknowledged"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "acknowledged"


@pytest.mark.asyncio
async def test_incident_state_machine_invalid(client):
    token = await create_test_user(client, "inv@test.com", "Inv Team")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/alerts/ingest",
        json={
            "source": "prometheus",
            "name": "TestAlert",
            "service_name": "test-service",
            "priority": "P2",
            "labels": {},
        },
        headers=headers,
    )

    # Try invalid transition triggered → triggered
    response = await client.patch(
        "/api/v1/incidents/1/status",
        json={"status": "triggered"},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_audit_log_written(client):
    token = await create_test_user(client, "audit@test.com", "Audit Team")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/alerts/ingest",
        json={
            "source": "grafana",
            "name": "AuditAlert",
            "service_name": "audit-service",
            "priority": "P3",
            "labels": {},
        },
        headers=headers,
    )

    response = await client.get(
        "/api/v1/incidents/1/audit",
        headers=headers,
    )
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) >= 1
    assert logs[0]["action"] == "incident.created"
