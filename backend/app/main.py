import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core import database as db_core
from app.api.v1 import (
    auth, resumes, jobs, applications, recruiter, admin, skills,
    interviews, evaluations, notifications, messages, saved_jobs, audit, practice,
    assessments, question_bank, proctoring, media, video_assessments, chat, tickets
)
from app.db.seed import seed_database
from app.db.seed_question_bank import seed_question_bank
from app.db.migrations import run_schema_migrations

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist and seed default skills and admin (skipped in unit test runs)
    is_testing = (
        getattr(settings, "TESTING", False) or
        os.getenv("TESTING", "").lower() == "true" or
        "pytest" in sys.modules or
        any("test" in arg.lower() for arg in sys.argv) or
        "sqlite" in str(getattr(db_core.engine.url, "database", "")).lower() or
        "sqlite" in str(getattr(db_core.engine, "name", "")).lower()
    )
    if not is_testing:
        print("🚀 Initializing SkillSphere database schema and seeds...")
        try:
            db = db_core.SessionLocal()
            try:
                db_core.Base.metadata.create_all(bind=db.bind)
                run_schema_migrations(db.bind)
                seed_database(db)
                seed_question_bank(db)
            finally:
                db.close()
        except Exception as e:
            print(f"⚠️ Startup database warning: {e}")
    yield
    print("🛑 Shutting down SkillSphere backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SkillSphere: Job Recruitment & Resume OCR Intelligence Platform API",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://skillsphere-uzt5.onrender.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ],
    allow_origin_regex=r"^https:\/\/.*\.onrender\.com$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for resume downloads
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Include Modular API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(resumes.router, prefix=settings.API_V1_STR)
app.include_router(saved_jobs.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(applications.router, prefix=settings.API_V1_STR)
app.include_router(recruiter.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(skills.router, prefix=settings.API_V1_STR)
app.include_router(interviews.router, prefix=settings.API_V1_STR)
app.include_router(evaluations.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
app.include_router(messages.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(practice.router, prefix=settings.API_V1_STR)
app.include_router(assessments.router, prefix=settings.API_V1_STR)
app.include_router(question_bank.router, prefix=settings.API_V1_STR)
app.include_router(proctoring.router, prefix=settings.API_V1_STR)
app.include_router(media.router, prefix=settings.API_V1_STR)
app.include_router(video_assessments.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(tickets.router, prefix=settings.API_V1_STR)
app.include_router(tickets.admin_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "api_docs": "/docs",
        "endpoints_prefix": settings.API_V1_STR
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
