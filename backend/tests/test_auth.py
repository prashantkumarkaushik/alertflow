import pytest


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@test.com",
            "password": "password123",
            "full_name": "Test User",
            "team_name": "Test Team",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@test.com"
    assert data["team_id"] == 1


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {
        "email": "dupe@test.com",
        "password": "password123",
        "full_name": "Test User",
        "team_name": "Test Team",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@test.com",
            "password": "password123",
            "full_name": "Test User",
            "team_name": "Login Team",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "login@test.com",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong@test.com",
            "password": "password123",
            "full_name": "Test User",
            "team_name": "Wrong Team",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "wrong@test.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@test.com",
            "password": "password123",
            "full_name": "Me User",
            "team_name": "Me Team",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "me@test.com",
            "password": "password123",
        },
    )
    token = login.json()["access_token"]
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@test.com"
