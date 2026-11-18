import re
from typing import Dict, List, Any, Optional

# Curated taxonomy of tech skills for deterministic matching (without OCR library false positives)
TECH_SKILLS_TAXONOMY = [
    # Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "c", "go", "golang", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "dart", "sql", "html", "html5", "css", "css3", "bash", "shell",
    # Frontend
    "react", "react.js", "next.js", "vue", "vue.js", "angular", "svelte", "redux", "zustand",
    "tailwind", "tailwind css", "tailwindcss", "bootstrap", "material-ui", "sass", "webpack", "vite",
    # Backend & Frameworks
    "fastapi", "flask", "django", "express", "express.js", "node.js", "nestjs", "spring",
    "spring boot", "asp.net", ".net", "laravel", "ruby on rails", "gin", "fiber", "graphql",
    "rest api", "restful api", "restful apis",
    # Databases & Caching
    "postgresql", "postgres", "mysql", "mongodb", "sqlite", "redis", "elasticsearch", "cassandra",
    "dynamodb", "mariadb", "oracle", "neo4j", "firebase", "supabase", "sqlalchemy", "prisma", "hibernate",
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "terraform", "ansible", "jenkins", "github actions", "gitlab ci", "ci/cd", "linux", "nginx",
    "apache", "serverless", "lambda", "ec2", "s3", "cloudformation", "helm", "prometheus", "grafana",
    # AI / ML / Data Science
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch",
    "keras", "scikit-learn", "pandas", "numpy", "opencv",
    "huggingface", "llm", "genai", "langchain", "spark", "hadoop", "kafka", "airflow",
    # Methodologies & Tools
    "git", "github", "gitlab", "jira", "agile", "scrum", "kanban", "unit testing", "pytest",
    "jest", "cypress", "selenium", "postman", "microservices", "system design", "oop", "jwt", "oauth"
]

SKILL_DISPLAY_MAP = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "java": "Java",
    "c++": "C++",
    "c#": "C#",
    "c": "C",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "sql": "SQL",
    "html": "HTML",
    "html5": "HTML5",
    "css": "CSS",
    "css3": "CSS3",
    "react": "React",
    "react.js": "React",
    "next.js": "Next.js",
    "vue": "Vue",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "redux": "Redux",
    "tailwind": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "bootstrap": "Bootstrap",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "express": "Express",
    "express.js": "Express",
    "node.js": "Node.js",
    "nestjs": "NestJS",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "graphql": "GraphQL",
    "rest api": "REST API",
    "restful api": "RESTful API",
    "restful apis": "RESTful API",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "sqlite": "SQLite",
    "redis": "Redis",
    "sqlalchemy": "SQLAlchemy",
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "ci/cd": "CI/CD",
    "linux": "Linux",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "jira": "Jira",
    "agile": "Agile",
    "scrum": "Scrum",
    "pytest": "Pytest",
    "jest": "Jest",
    "postman": "Postman",
    "jwt": "JWT",
    "oauth": "OAuth",
    "microservices": "Microservices"
}

def clean_text_for_parsing(text: str) -> str:
    """Strip out sample disclaimers, test watermarks, and footer boilerplate before parsing."""
    cleaned_lines = []
    for line in text.splitlines():
        lower = line.lower()
        if "sample fictional resume" in lower or "for skillsphere resume-upload" in lower or "illustrative" in lower:
            # Reached test disclaimer footer; do not include
            break
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def extract_email(text: str) -> str:
    """Extract first valid email address from text."""
    email_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    matches = re.findall(email_regex, text)
    if matches:
        return matches[0].strip().rstrip('.')
    return ""

def extract_phone(text: str) -> str:
    """Extract valid phone number (International or standard formats)."""
    phone_regex = r'(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})|(?:(?:\+91|0)?[6-9]\d{9})'
    matches = re.findall(phone_regex, text)
    if matches:
        cleaned = re.sub(r'[^\d+]', '', matches[0])
        return cleaned
    return ""

def extract_name(text: str) -> str:
    """
    Robust extraction of candidate name from the top header lines of a resume.
    Handles all-caps ('ALEX MORGAN' -> 'Alex Morgan'), skips contact/title/link lines.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""

    disallowed_keywords = [
        "resume", "curriculum", "vitae", "cv", "summary", "profile", "contact",
        "developer", "engineer", "designer", "architect", "manager", "analyst",
        "specialist", "intern", "lead", "http", "https", "linkedin", "github",
        "phone", "email", "education", "experience", "skills", "projects"
    ]

    # Look through the top 5 non-empty lines
    for line in lines[:5]:
        # Skip lines containing email, URLs, or delimiters indicating contact/links/titles
        if "@" in line or "|" in line or "/" in line or "\\" in line:
            continue
        # Skip lines with phone numbers or many digits
        if len(re.findall(r'\d', line)) >= 4:
            continue
        lower_line = line.lower()
        if any(kw in lower_line for kw in disallowed_keywords):
            continue

        words = line.split()
        if 2 <= len(words) <= 4 and all(re.match(r'^[A-Za-z\.\'-]+$', w) for w in words):
            # Format nicely as Title Case
            return " ".join(w.capitalize() if not w.isupper() else w.title() for w in words)

    # Fallback to first line if it looks plausible
    first_line = lines[0]
    first_words = first_line.split()
    if 1 <= len(first_words) <= 4 and all(re.match(r'^[A-Za-z\.\'-]+$', w) for w in first_words):
        return " ".join(w.capitalize() if not w.isupper() else w.title() for w in first_words)

    return ""

def extract_skills(text: str) -> List[str]:
    """Identify matching tech skills from text using boundary-aware regex matching."""
    cleaned = clean_text_for_parsing(text)
    lower_text = " " + cleaned.lower() + " "
    matched_skills = set()

    for skill in TECH_SKILLS_TAXONOMY:
        # Match skill with word boundaries or punctuation boundaries
        pattern = r'(?<![a-z0-9])' + re.escape(skill) + r'(?![a-z0-9])'
        if re.search(pattern, lower_text):
            display_name = SKILL_DISPLAY_MAP.get(skill, skill.title())
            matched_skills.add(display_name)

    return sorted(list(matched_skills))

def extract_education(text: str) -> List[Dict[str, Any]]:
    """Identify education entries (degree, institution, graduation year)."""
    cleaned = clean_text_for_parsing(text)
    lines = cleaned.splitlines()
    education_entries = []
    in_edu_section = False

    header_edu = re.compile(
        r'^(EDUCATION|ACADEMIC\s+BACKGROUND|ACADEMICS|EDUCATION\s+&\s+CREDENTIALS)\s*:?$',
        re.I
    )
    header_terminators = re.compile(
        r'^(CERTIFICATIONS|COURSES|PROJECTS|SKILLS|TECHNICAL\s+SKILLS|EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|PUBLICATIONS)\s*:?$',
        re.I
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if header_edu.match(stripped):
            in_edu_section = True
            continue
        elif in_edu_section and header_terminators.match(stripped):
            in_edu_section = False
            break

        if in_edu_section:
            if "|" in stripped:
                parts = [p.strip() for p in stripped.split("|")]
                degree = parts[0]
                institution = parts[1] if len(parts) > 1 else ""
                year_part = parts[2] if len(parts) > 2 else ""
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', year_part or stripped)
                year = year_match.group(0) if year_match else (year_part or None)

                education_entries.append({
                    "degree": degree,
                    "institution": institution,
                    "year": year,
                    "grade": ""
                })
            else:
                # If keywords match degree/institution
                edu_keywords = ["bachelor", "master", "ph.d", "b.tech", "m.tech", "b.s", "m.s", "b.e", "m.e", "degree", "university", "college"]
                if any(k in stripped.lower() for k in edu_keywords):
                    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', stripped)
                    year = year_match.group(0) if year_match else None
                    education_entries.append({
                        "degree": stripped,
                        "institution": "",
                        "year": year,
                        "grade": ""
                    })

    return education_entries[:5]

def extract_experience(text: str) -> List[Dict[str, Any]]:
    """Identify experience timeline and work entries."""
    cleaned = clean_text_for_parsing(text)
    lines = cleaned.splitlines()
    experience_entries = []
    in_exp_section = False
    current_item = None

    header_exp = re.compile(
        r'^(PROFESSIONAL\s+EXPERIENCE|WORK\s+EXPERIENCE|EXPERIENCE|EMPLOYMENT\s+HISTORY|WORK\s+HISTORY)\s*:?$',
        re.I
    )
    header_terminators = re.compile(
        r'^(PROJECTS|TECHNICAL\s+PROJECTS|EDUCATION|ACADEMICS|CERTIFICATIONS|SKILLS|TECHNICAL\s+SKILLS)\s*:?$',
        re.I
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if header_exp.match(stripped):
            in_exp_section = True
            continue
        elif in_exp_section and header_terminators.match(stripped):
            in_exp_section = False
            if current_item:
                experience_entries.append(current_item)
                current_item = None
            break

        if in_exp_section:
            # Job entry header line typically contains pipe or date range
            if "|" in stripped:
                if current_item:
                    experience_entries.append(current_item)
                parts = [p.strip() for p in stripped.split("|")]
                title = parts[0]
                company = parts[1] if len(parts) > 1 else ""
                duration = parts[2] if len(parts) > 2 else ""
                current_item = {
                    "title": title,
                    "company": company,
                    "duration": duration,
                    "description": ""
                }
            elif current_item:
                bullet = stripped.lstrip("•-* ").strip()
                if bullet:
                    if current_item["description"]:
                        current_item["description"] += " " + bullet
                    else:
                        current_item["description"] = bullet

    if current_item:
        experience_entries.append(current_item)

    return experience_entries[:5]

def extract_total_experience(text: str, experience_entries: List[Dict[str, Any]]) -> float:
    """Extract total years of experience from summary or calculated from parsed roles."""
    # 1. Search text for "X years of experience"
    exp_regex = r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience'
    match = re.search(exp_regex, text, re.I)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    # 2. Heuristic from experience entries date ranges
    years_found = set()
    for entry in experience_entries:
        duration = entry.get("duration", "")
        matches = re.findall(r'\b(19\d{2}|20\d{2})\b', duration)
        for y in matches:
            years_found.add(int(y))

    if len(years_found) >= 2:
        span = max(years_found) - min(years_found)
        return float(max(1.0, span))
    elif len(experience_entries) > 0:
        return float(len(experience_entries))

    return 0.0

def extract_bio(text: str) -> str:
    """Extract professional summary / bio section from resume text."""
    lines = text.splitlines()
    in_summary = False
    summary_lines = []
    header_sum = re.compile(r'^(PROFESSIONAL\s+SUMMARY|SUMMARY|PROFILE|OBJECTIVE|ABOUT\s+ME)\s*:?$', re.I)
    header_other = re.compile(r'^(TECHNICAL\s+SKILLS|SKILLS|EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EDUCATION|PROJECTS)\s*:?$', re.I)

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if header_sum.match(line):
            in_summary = True
            continue
        elif in_summary and header_other.match(line):
            break
        if in_summary:
            summary_lines.append(line)

    if summary_lines:
        return " ".join(summary_lines)

    return text[:300].strip() + ("..." if len(text) > 300 else "")

def parse_resume_text(text: str) -> Dict[str, Any]:
    """Combine extractors into a complete structured candidate profile dictionary."""
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)
    total_years_exp = extract_total_experience(text, experience)
    bio = extract_bio(text)

    # Determine candidate title: from line 1 if piped, or from first experience entry
    title = ""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) > 1 and "|" in lines[1]:
        title = lines[1].split("|")[0].strip()
    elif experience:
        title = experience[0].get("title", "")

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "title": title,
        "bio": bio,
        "skills": skills,
        "education": education,
        "experience": experience,
        "total_years_exp": total_years_exp
    }
