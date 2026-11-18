from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import get_password_hash
from app.core.database import SessionLocal, engine, Base
from app.models.models import (
    User, RoleEnum, Candidate, Recruiter, Company, Skill,
    Job, JobSkill, JobTypeEnum, JobStatusEnum
)
from app.services.parser_service import TECH_SKILLS_TAXONOMY

def seed_database(db: Session):
    print("🌱 Starting database seeding...")
    
    # Ensure all tables exist on the active database engine
    Base.metadata.create_all(bind=db.bind)

    # 1. Seed Skills Catalog
    existing_skills_count = db.query(Skill).count()
    if existing_skills_count == 0:
        print("  - Populating standard skills taxonomy...")
        for skill_name in TECH_SKILLS_TAXONOMY:
            skill = Skill(skill_name=skill_name.lower())
            db.add(skill)
        db.commit()
        print(f"  ✓ Added {len(TECH_SKILLS_TAXONOMY)} skills.")
    else:
        print(f"  ✓ Skills table already populated ({existing_skills_count} skills).")

    # 2. Seed Admin User
    admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL.lower()).first()
    if not admin:
        print(f"  - Creating Administrator: {settings.ADMIN_EMAIL}")
        admin = User(
            name=settings.ADMIN_NAME,
            email=settings.ADMIN_EMAIL.lower(),
            password_hash=get_password_hash(settings.ADMIN_PASSWORD),
            role=RoleEnum.ADMIN,
            email_verified=True,
            email_verified_at=datetime.now(timezone.utc)
        )
        db.add(admin)
        db.commit()
        print("  ✓ Admin account created successfully.")
    else:
        print("  ✓ Admin account exists.")

    # 3. Seed Sample Companies
    company1 = db.query(Company).filter(Company.company_name == "TechNova Systems").first()
    if not company1:
        company1 = Company(
            company_name="TechNova Systems",
            description="Leading AI-powered enterprise software and cloud consultancy.",
            website="https://technova.example.com",
            location="Bengaluru, India",
            contact_email="careers@technova.example.com"
        )
        db.add(company1)

    company2 = db.query(Company).filter(Company.company_name == "CloudScale Digital").first()
    if not company2:
        company2 = Company(
            company_name="CloudScale Digital",
            description="High-velocity cloud-native platforms and infrastructure engineering.",
            website="https://cloudscale.example.com",
            location="Remote / Hyderabad, India",
            contact_email="hiring@cloudscale.example.com"
        )
        db.add(company2)
    db.commit()

    # 4. Seed Demo Recruiter
    recruiter_user = db.query(User).filter(User.email == "recruiter@technova.com").first()
    if not recruiter_user:
        print("  - Creating Demo Recruiter: recruiter@technova.com")
        recruiter_user = User(
            name="Sarah Jenkins",
            email="recruiter@technova.com",
            password_hash=get_password_hash("Recruiter123!"),
            role=RoleEnum.RECRUITER,
            email_verified=True,
            email_verified_at=datetime.now(timezone.utc)
        )
        db.add(recruiter_user)
        db.commit()
        db.refresh(recruiter_user)

        recruiter_profile = Recruiter(
            user_id=recruiter_user.id,
            company_id=company1.id,
            designation="Talent Acquisition Partner"
        )
        db.add(recruiter_profile)
        db.commit()
        db.refresh(recruiter_profile)
    else:
        recruiter_profile = recruiter_user.recruiter_profile

    # 5. Seed Demo Candidate
    candidate_user = db.query(User).filter(User.email == "seeker@skillsphere.com").first()
    if not candidate_user:
        print("  - Creating Demo Candidate: seeker@skillsphere.com")
        candidate_user = User(
            name="Alex Rivera",
            email="seeker@skillsphere.com",
            password_hash=get_password_hash("Seeker123!"),
            role=RoleEnum.JOB_SEEKER,
            email_verified=True,
            email_verified_at=datetime.now(timezone.utc)
        )
        db.add(candidate_user)
        db.commit()
        db.refresh(candidate_user)

        cand_profile = Candidate(
            user_id=candidate_user.id,
            phone="+91 9876543210",
            title="Senior Full Stack Software Engineer",
            location="Bengaluru, India",
            bio="Full stack engineer passionate about Python, FastAPI, React, and scalable cloud architectures.",
            education=[{
                "degree": "B.Tech Computer Science",
                "institution": "National Institute of Technology",
                "year": "2021",
                "grade": "8.8 CGPA"
            }],
            experience=[{
                "title": "Software Engineer",
                "company": "Apex Technologies",
                "duration": "2021 - Present",
                "description": "Architected high-throughput REST APIs using FastAPI and built reactive frontend dashboards."
            }],
            total_years_exp=3.5
        )
        db.add(cand_profile)
        db.commit()
        db.refresh(cand_profile)

        # Attach sample skills to Alex
        sample_skills = ["python", "react", "fastapi", "postgresql", "docker", "git", "typescript"]
        for s in sample_skills:
            sk_obj = db.query(Skill).filter(Skill.skill_name == s).first()
            if sk_obj and sk_obj not in cand_profile.skills:
                cand_profile.skills.append(sk_obj)
        db.commit()

    # 6. Seed Sample Jobs
    existing_jobs = db.query(Job).count()
    if existing_jobs == 0 and recruiter_profile:
        print("  - Creating sample job postings...")
        
        job1 = Job(
            recruiter_id=recruiter_profile.id,
            company_id=company1.id,
            title="Senior Full-Stack Engineer (React + FastAPI)",
            description="""We are seeking a seasoned Senior Full-Stack Engineer to join our core product team.
You will be architecting modular RESTful microservices in FastAPI, managing PostgreSQL databases,
and designing high-performance interfaces with React and Tailwind CSS.

Requirements:
- 3+ years of experience with Python (FastAPI/Django) and modern React.
- Strong understanding of relational database modeling and PostgreSQL.
- Experience with Docker and CI/CD pipelines.
- Solid understanding of JWT-based authentication and REST API design.""",
            location="Bengaluru / Hybrid",
            experience_min=3.0,
            experience_max=6.0,
            job_type=JobTypeEnum.FULL_TIME,
            salary_min=1800000.0,
            salary_max=2800000.0,
            status=JobStatusEnum.ACTIVE
        )
        db.add(job1)
        db.commit()
        db.refresh(job1)

        # Job 1 skills
        for s_name in ["python", "fastapi", "react", "postgresql", "docker", "git"]:
            sk = db.query(Skill).filter(Skill.skill_name == s_name).first()
            if sk:
                db.add(JobSkill(job_id=job1.id, skill_id=sk.id, is_required=True))

        job2 = Job(
            recruiter_id=recruiter_profile.id,
            company_id=company1.id,
            title="DevOps & Cloud Infrastructure Specialist",
            description="""Join TechNova Systems to lead our automated cloud platform initiatives.
You will oversee Kubernetes clusters, configure Terraform infrastructure as code,
and streamline automated deployment pipelines across AWS and GCP environments.""",
            location="Remote",
            experience_min=2.0,
            experience_max=5.0,
            job_type=JobTypeEnum.REMOTE,
            salary_min=1600000.0,
            salary_max=2400000.0,
            status=JobStatusEnum.ACTIVE
        )
        db.add(job2)
        db.commit()
        db.refresh(job2)

        # Job 2 skills
        for s_name in ["aws", "docker", "kubernetes", "terraform", "ci/cd", "linux"]:
            sk = db.query(Skill).filter(Skill.skill_name == s_name).first()
            if sk:
                db.add(JobSkill(job_id=job2.id, skill_id=sk.id, is_required=True))

        # Job 3 with NO required skills (test edge-case)
        job3 = Job(
            recruiter_id=recruiter_profile.id,
            company_id=company1.id,
            title="Associate Technical Analyst (Open Domain)",
            description="""An entry-level technical role open to fresh graduates from all backgrounds.
Training will be provided. No specific technical skills are strictly required upfront.""",
            location="Bengaluru, India",
            experience_min=0.0,
            experience_max=1.0,
            job_type=JobTypeEnum.FULL_TIME,
            salary_min=600000.0,
            salary_max=800000.0,
            status=JobStatusEnum.ACTIVE
        )
        db.add(job3)
        db.commit()

        print("  ✓ Sample jobs created.")

    print("🎉 Database seeding completed successfully!")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
