import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.models import Candidate, CandidateTechnology, Resume

# Canonical taxonomy mapping: alias/variation -> (canonical_name, category)
TECH_NORMALIZATION_MAP: Dict[str, Tuple[str, str]] = {
    # Programming Languages
    "python": ("Python", "LANGUAGE"),
    "python3": ("Python", "LANGUAGE"),
    "py": ("Python", "LANGUAGE"),
    "javascript": ("JavaScript", "LANGUAGE"),
    "js": ("JavaScript", "LANGUAGE"),
    "ecmascript": ("JavaScript", "LANGUAGE"),
    "typescript": ("TypeScript", "LANGUAGE"),
    "ts": ("TypeScript", "LANGUAGE"),
    "java": ("Java", "LANGUAGE"),
    "c++": ("C++", "LANGUAGE"),
    "cpp": ("C++", "LANGUAGE"),
    "c#": ("C#", "LANGUAGE"),
    "csharp": ("C#", "LANGUAGE"),
    "c": ("C", "LANGUAGE"),
    "go": ("Go", "LANGUAGE"),
    "golang": ("Go", "LANGUAGE"),
    "rust": ("Rust", "LANGUAGE"),
    "ruby": ("Ruby", "LANGUAGE"),
    "php": ("PHP", "LANGUAGE"),
    "sql": ("SQL", "LANGUAGE"),
    "kotlin": ("Kotlin", "LANGUAGE"),
    "swift": ("Swift", "LANGUAGE"),
    "scala": ("Scala", "LANGUAGE"),
    "bash": ("Bash", "LANGUAGE"),
    "shell": ("Bash", "LANGUAGE"),

    # Frameworks & Libraries
    "react": ("React", "FRAMEWORK"),
    "reactjs": ("React", "FRAMEWORK"),
    "react.js": ("React", "FRAMEWORK"),
    "node": ("Node.js", "FRAMEWORK"),
    "nodejs": ("Node.js", "FRAMEWORK"),
    "node.js": ("Node.js", "FRAMEWORK"),
    "fastapi": ("FastAPI", "FRAMEWORK"),
    "django": ("Django", "FRAMEWORK"),
    "flask": ("Flask", "FRAMEWORK"),
    "spring": ("Spring Boot", "FRAMEWORK"),
    "spring boot": ("Spring Boot", "FRAMEWORK"),
    "springboot": ("Spring Boot", "FRAMEWORK"),
    "express": ("Express", "FRAMEWORK"),
    "expressjs": ("Express", "FRAMEWORK"),
    "express.js": ("Express", "FRAMEWORK"),
    "nestjs": ("NestJS", "FRAMEWORK"),
    "next.js": ("Next.js", "FRAMEWORK"),
    "nextjs": ("Next.js", "FRAMEWORK"),
    "vue": ("Vue", "FRAMEWORK"),
    "vue.js": ("Vue", "FRAMEWORK"),
    "angular": ("Angular", "FRAMEWORK"),
    "redux": ("Redux", "FRAMEWORK"),
    "tailwind": ("Tailwind CSS", "FRAMEWORK"),
    "tailwindcss": ("Tailwind CSS", "FRAMEWORK"),
    "tensorflow": ("TensorFlow", "FRAMEWORK"),
    "pytorch": ("PyTorch", "FRAMEWORK"),
    "scikit-learn": ("Scikit-learn", "FRAMEWORK"),
    "pandas": ("Pandas", "FRAMEWORK"),
    "numpy": ("NumPy", "FRAMEWORK"),

    # Databases & Caching
    "postgresql": ("PostgreSQL", "DATABASE"),
    "postgres": ("PostgreSQL", "DATABASE"),
    "pgsql": ("PostgreSQL", "DATABASE"),
    "mysql": ("MySQL", "DATABASE"),
    "mongodb": ("MongoDB", "DATABASE"),
    "mongo": ("MongoDB", "DATABASE"),
    "redis": ("Redis", "DATABASE"),
    "sqlite": ("SQLite", "DATABASE"),
    "elasticsearch": ("Elasticsearch", "DATABASE"),
    "dynamodb": ("DynamoDB", "DATABASE"),
    "cassandra": ("Cassandra", "DATABASE"),

    # Tools, Cloud & DevOps
    "docker": ("Docker", "TOOL"),
    "kubernetes": ("Kubernetes", "TOOL"),
    "k8s": ("Kubernetes", "TOOL"),
    "git": ("Git", "TOOL"),
    "github": ("GitHub", "TOOL"),
    "gitlab": ("GitLab", "TOOL"),
    "aws": ("AWS", "CLOUD"),
    "amazon web services": ("AWS", "CLOUD"),
    "azure": ("Azure", "CLOUD"),
    "gcp": ("GCP", "CLOUD"),
    "google cloud": ("GCP", "CLOUD"),
    "linux": ("Linux", "TOOL"),
    "ci/cd": ("CI/CD", "TOOL"),
    "terraform": ("Terraform", "TOOL"),
    "nginx": ("Nginx", "TOOL"),
    "kafka": ("Kafka", "TOOL")
}

class TechDetectionService:
    @classmethod
    def detect_technologies_from_text(cls, text: str) -> List[Dict[str, Any]]:
        """
        Scan resume text with boundary-aware regex matching.
        Returns a list of deduplicated, normalized technology dicts.
        """
        if not text:
            return []

        lower_text = " " + text.lower() + " "
        detected: Dict[str, Dict[str, Any]] = {}

        for pattern_str, (canonical_name, category) in TECH_NORMALIZATION_MAP.items():
            # Boundary-aware regex to avoid false positives (e.g., 'go' inside 'algorithm', 'c' inside 'cloud')
            if pattern_str in ("c", "go", "r"):
                # Strict boundary check for single/short letters
                regex = r'(?<![a-zA-Z0-9_#+])' + re.escape(pattern_str) + r'(?![a-zA-Z0-9_#+])'
            elif "+" in pattern_str or "#" in pattern_str:
                regex = r'(?<![a-zA-Z0-9])' + re.escape(pattern_str) + r'(?![a-zA-Z0-9])'
            else:
                regex = r'(?<![a-z0-9])' + re.escape(pattern_str) + r'(?![a-z0-9])'

            if re.search(regex, lower_text):
                if canonical_name not in detected:
                    detected[canonical_name] = {
                        "technology_name": canonical_name,
                        "category": category,
                        "is_resume_detected": True,
                        "proficiency_level": "INTERMEDIATE"
                    }

        return sorted(list(detected.values()), key=lambda x: (x["category"], x["technology_name"]))

    @classmethod
    def sync_candidate_technologies(cls, db: Session, candidate_id: str, resume_text: Optional[str] = None) -> List[CandidateTechnology]:
        """
        Detect technologies from candidate's latest resume and persist into candidate_technologies.
        Preserves manually added technologies and updates resume-detected ones.
        """
        if not resume_text:
            # Fetch latest candidate resume
            latest_resume = db.query(Resume).filter(
                Resume.candidate_id == candidate_id
            ).order_by(Resume.upload_date.desc()).first()
            if latest_resume and latest_resume.extracted_text:
                resume_text = latest_resume.extracted_text
            else:
                resume_text = ""

        detected_list = cls.detect_technologies_from_text(resume_text)

        # Query existing candidate technologies
        existing_records = db.query(CandidateTechnology).filter(
            CandidateTechnology.candidate_id == candidate_id
        ).all()
        existing_map = {rec.technology_name: rec for rec in existing_records}

        # Add newly detected technologies that don't exist yet
        for item in detected_list:
            tech_name = item["technology_name"]
            if tech_name not in existing_map:
                new_tech = CandidateTechnology(
                    candidate_id=candidate_id,
                    technology_name=tech_name,
                    category=item["category"],
                    is_resume_detected=True,
                    proficiency_level=item["proficiency_level"]
                )
                db.add(new_tech)

        db.commit()

        # Return refreshed list
        return db.query(CandidateTechnology).filter(
            CandidateTechnology.candidate_id == candidate_id
        ).order_by(CandidateTechnology.category, CandidateTechnology.technology_name).all()
