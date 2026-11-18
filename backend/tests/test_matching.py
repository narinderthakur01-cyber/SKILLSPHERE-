from app.services.matching_service import calculate_skill_match

def test_standard_skill_matching():
    candidate_skills = ["Python", "FastAPI", "React", "Docker", "Git"]
    job_skills = ["Python", "FastAPI", "React", "Kubernetes"]

    result = calculate_skill_match(candidate_skills, job_skills)
    assert result["match_score"] == 75.0  # 3 of 4 skills matched
    assert len(result["matched_skills"]) == 3
    assert "Kubernetes" in result["missing_skills"]
    assert "Moderate match" in result["recommendations"]

def test_perfect_skill_matching():
    candidate_skills = ["Python", "FastAPI", "Docker", "PostgreSQL", "React"]
    job_skills = ["Python", "FastAPI", "Docker"]

    result = calculate_skill_match(candidate_skills, job_skills)
    assert result["match_score"] == 100.0
    assert len(result["missing_skills"]) == 0
    assert "High match" in result["recommendations"]

def test_zero_match():
    candidate_skills = ["Ruby", "PHP"]
    job_skills = ["Python", "Golang"]

    result = calculate_skill_match(candidate_skills, job_skills)
    assert result["match_score"] == 0.0
    assert len(result["matched_skills"]) == 0
    assert len(result["missing_skills"]) == 2

def test_edge_case_no_required_skills_returns_null():
    """
    CRITICAL REQUIREMENT:
    When no required skills exist on the job, returns null match_score
    with an explanatory message.
    """
    candidate_skills = ["Python", "FastAPI"]
    job_skills = []

    result = calculate_skill_match(candidate_skills, job_skills)
    assert result["match_score"] is None
    assert result["matched_skills"] == []
    assert result["missing_skills"] == []
    assert "does not specify any required skills" in result["message"]
