from app.models.models import RoleEnum

def test_register_candidate(client):
    response = client.post("/api/v1/auth/register", json={
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "Password123!",
        "role": RoleEnum.JOB_SEEKER.value
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "jane@example.com"
    assert data["user"]["role"] == RoleEnum.JOB_SEEKER.value

def test_register_duplicate_email(client, candidate_user):
    response = client.post("/api/v1/auth/register", json={
        "name": "Another Name",
        "email": candidate_user.email,
        "password": "Password123!",
        "role": RoleEnum.JOB_SEEKER.value
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_success(client, candidate_user):
    response = client.post("/api/v1/auth/login", json={
        "email": candidate_user.email,
        "password": "Secret123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == candidate_user.email

def test_login_invalid_password(client, candidate_user):
    response = client.post("/api/v1/auth/login", json={
        "email": candidate_user.email,
        "password": "WrongPassword!"
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

def test_get_current_user_me(client, candidate_token):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test_candidate@skillsphere.com"
