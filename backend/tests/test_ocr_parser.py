import os
from pathlib import Path
import pymupdf as fitz
from app.services.parser_service import (
    extract_name, extract_email, extract_phone, extract_skills,
    extract_education, extract_experience, parse_resume_text
)
from app.services.ocr_service import extract_text_from_pdf

def test_extract_contact_info():
    sample_text = """
    Alex Rivera
    Senior Software Engineer
    Email: alex.rivera@example.com
    Phone: +1 (555) 234-5678
    Location: San Francisco, CA
    """
    name = extract_name(sample_text)
    email = extract_email(sample_text)
    phone = extract_phone(sample_text)
    assert name == "Alex Rivera"
    assert email == "alex.rivera@example.com"
    assert "5552345678" in phone

def test_extract_skills_taxonomy():
    sample_text = """
    TECHNICAL SKILLS:
    Proficient in Python, FastAPI, and React.js.
    Hands-on experience with PostgreSQL, Docker containerization, Kubernetes, and AWS cloud.
    Familiar with Git and Agile Scrum methodologies. Also use Postman for testing REST API.
    """
    skills = extract_skills(sample_text)
    assert "Python" in skills
    assert "FastAPI" in skills or "Fastapi" in skills
    assert "React" in skills or "React.Js" in skills
    assert "PostgreSQL" in skills or "Postgresql" in skills
    assert "Docker" in skills
    assert "Kubernetes" in skills
    assert "AWS" in skills or "Aws" in skills
    assert "Postman" in skills
    assert "REST API" in skills

def test_pymupdf_digital_pdf_extraction(tmp_path):
    # Dynamically generate a sample PDF using PyMuPDF
    pdf_path = tmp_path / "sample_resume.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        fitz.Point(50, 72),
        "John Doe\njohn.doe@techmail.com\n+91 9123456789\nExpert in Python, TypeScript, React, and PostgreSQL."
    )
    doc.save(str(pdf_path))
    doc.close()

    result = extract_text_from_pdf(str(pdf_path))
    assert result["is_scanned"] is False
    assert result["page_count"] == 1
    assert "John Doe" in result["text"]
    assert "john.doe@techmail.com" in result["text"]

    parsed = parse_resume_text(result["text"])
    assert parsed["name"] == "John Doe"
    assert parsed["email"] == "john.doe@techmail.com"
    assert "Python" in parsed["skills"]
    assert "React" in parsed["skills"]

def test_alex_morgan_sample_resume_extraction():
    """Verify end-to-end extraction accuracy on the Alex Morgan sample resume."""
    # Locate uploaded Alex Morgan resume
    upload_dir = Path("backend/uploads")
    if not upload_dir.exists():
        upload_dir = Path("uploads")

    pdf_files = list(upload_dir.glob("*.pdf"))
    assert len(pdf_files) > 0, "No PDF resume found in upload directory"
    
    # Pick the uploaded test PDF
    pdf_path = str(pdf_files[0])
    result = extract_text_from_pdf(pdf_path)
    text = result["text"]
    assert "ALEX MORGAN" in text or "Alex Morgan" in text

    parsed = parse_resume_text(text)

    # 1. Full name extraction
    assert parsed["name"] == "Alex Morgan", f"Expected 'Alex Morgan', got '{parsed['name']}'"

    # 2. Email extraction
    assert parsed["email"] == "alex.morgan@example.com", f"Expected alex.morgan@example.com, got '{parsed['email']}'"

    # 3. Phone extraction
    assert "2025550147" in parsed["phone"].replace("+", "").replace("-", "")

    # 4. Professional Title
    assert parsed["title"] == "Software Engineer"

    # 5. Work Experience (both roles extracted with structured details)
    assert len(parsed["experience"]) == 2, f"Expected 2 experience entries, got {len(parsed['experience'])}"
    exp1 = parsed["experience"][0]
    assert exp1["title"] == "Software Engineer"
    assert "Northstar Digital" in exp1["company"]
    assert "2024" in exp1["duration"]
    assert "REST APIs using Python and FastAPI" in exp1["description"]

    exp2 = parsed["experience"][1]
    assert exp2["title"] == "Junior Developer"
    assert "BrightPath Solutions" in exp2["company"]
    assert "2022" in exp2["duration"]
    assert "validate, transform, and import" in exp2["description"]

    # 6. Education extraction
    assert len(parsed["education"]) >= 1, f"Expected education entries, got {len(parsed['education'])}"
    edu = parsed["education"][0]
    assert "Bachelor of Science in Computer Science" in edu["degree"]
    assert "Central Texas University" in edu["institution"]
    assert edu["year"] == "2022"

    # 7. Total years of experience
    assert parsed["total_years_exp"] == 3.0

    # 8. Skills extraction & false-positive check
    extracted_skills_lower = [s.lower() for s in parsed["skills"]]
    assert "ocr" not in extracted_skills_lower, "Spurious 'ocr' false positive should not be in extracted skills"
    assert "pymupdf" not in extracted_skills_lower, "Spurious 'pymupdf' false positive should not be in extracted skills"
    assert "fitz" not in extracted_skills_lower, "Spurious 'fitz' false positive should not be in extracted skills"

    # Verify genuine skills are present
    assert "postman" in extracted_skills_lower, "Missing skill 'Postman' should be extracted"
    assert "fastapi" in extracted_skills_lower, "FastAPI should be extracted"
    assert "python" in extracted_skills_lower, "Python should be extracted"
    assert "react" in extracted_skills_lower, "React should be extracted"
    assert "postgresql" in extracted_skills_lower, "PostgreSQL should be extracted"
    assert "docker" in extracted_skills_lower, "Docker should be extracted"
    assert "pytest" in extracted_skills_lower, "Pytest should be extracted"
    assert any("rest" in s for s in extracted_skills_lower), "REST API should be extracted"

    # 9. Bio / Summary
    assert "Software engineer with 3 years of experience" in parsed["bio"]
    assert "Sample fictional resume" not in parsed["bio"]
