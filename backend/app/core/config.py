import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Explicitly load .env files into os.environ (Root .env takes precedence for shared secrets)
_backend_dir = Path(__file__).resolve().parent.parent.parent
if (_backend_dir.parent / ".env").exists():
    load_dotenv(_backend_dir.parent / ".env", override=True)
if (_backend_dir / ".env").exists():
    load_dotenv(_backend_dir / ".env", override=False)

class Settings(BaseSettings):
    PROJECT_NAME: str = "SkillSphere"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration placeholders
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "YOUR_POSTGRES_PASSWORD_HERE")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "skillsphere")
    
    # DATABASE_URL property
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        import sys
        is_test = (
            self.TESTING or
            os.getenv("TESTING", "").lower() == "true" or
            "pytest" in sys.modules or
            any("test" in arg.lower() for arg in sys.argv)
        )
        if is_test:
            return "sqlite:///:memory:"

        explicit_url = os.getenv("DATABASE_URL")
        if explicit_url:
            if explicit_url.startswith("postgresql://"):
                return explicit_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return explicit_url

        # Check if user has set their PostgreSQL credentials
        pwd = self.POSTGRES_PASSWORD
        if pwd and pwd != "YOUR_POSTGRES_PASSWORD_HERE" and pwd.strip() != "":
            return f"postgresql+psycopg2://{self.POSTGRES_USER}:{pwd}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
        # Fallback to local SQLite database when PostgreSQL credentials are still pending
        local_db_path = Path(__file__).resolve().parent.parent.parent / "skillsphere.db"
        return f"sqlite:///{local_db_path}"

    DATABASE_URL: str = ""
    
    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "skillsphere-super-secret-production-grade-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Upload storage
    UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent.parent / "uploads"
    MAX_FILE_SIZE_MB: int = 10
    
    # OCR / Tesseract configuration
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "")
    
    # Seed Admin User
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@skillsphere.local")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "AdminSkillSphere2026!#")
    ADMIN_NAME: str = os.getenv("ADMIN_NAME", "SkillSphere Administrator")
    TESTING: bool = os.getenv("TESTING", "false").lower() == "true"

    # Brevo Transactional Email & Password Reset
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "")
    BREVO_SENDER_EMAIL: str = os.getenv("BREVO_SENDER_EMAIL", "")
    BREVO_SENDER_NAME: str = os.getenv("BREVO_SENDER_NAME", "SkillSphere")
    FRONTEND_BASE_URL: str = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    PASSWORD_RESET_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "15"))
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = int(os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "30"))
    EMAIL_RESEND_COOLDOWN_SECONDS: int = int(os.getenv("EMAIL_RESEND_COOLDOWN_SECONDS", "60"))

    # Cloudinary Media Storage Configuration
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "skillsphere-cloud")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "123456789012345")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "skillsphere-cloudinary-secret")
    CLOUDINARY_SECURE_DELIVERY: bool = os.getenv("CLOUDINARY_SECURE_DELIVERY", "true").lower() == "true"
    CLOUDINARY_UPLOAD_PREFIX: str = os.getenv("CLOUDINARY_UPLOAD_PREFIX", "https://api.cloudinary.com/v1_1")

    # LiveKit / WebRTC Live Video Infrastructure Configuration
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "wss://skillsphere.livekit.cloud")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "devkey")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "secret_livekit_key_skillsphere_2026")
    LIVEKIT_EGRESS_ENABLED: bool = os.getenv("LIVEKIT_EGRESS_ENABLED", "true").lower() == "true"

    # AI Interview Intelligence & Transcription (Optional fallback)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent / ".env")
        extra = "allow"

settings = Settings()
if not settings.DATABASE_URL:
    settings.DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

# Ensure uploads directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
