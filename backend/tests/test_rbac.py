def test_candidate_cannot_post_job(client, candidate_token):
    # Candidate role attempting to access recruiter job creation endpoint
    response = client.post(
        "/api/v1/jobs",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={
            "title": "Unauthorized Job",
            "description": "This should fail with 403 Forbidden.",
            "location": "Remote",
            "required_skills": ["Python"]
        }
    )
    assert response.status_code == 403
    assert "Insufficient privileges" in response.json()["detail"]

def test_unauthenticated_cannot_access_protected_endpoint(client):
    response = client.get("/api/v1/resume/profile")
    assert response.status_code == 401

def test_recruiter_cannot_access_admin_analytics(client, recruiter_token):
    response = client.get(
        "/api/v1/admin/analytics",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert response.status_code == 403
