from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

Base = declarative_base()

def get_engine():
    import os, sys
    is_test = (
        getattr(settings, "TESTING", False) or
        (os.getenv("TESTING", "").lower() == "true") or
        ("pytest" in sys.modules) or
        any("test" in arg.lower() for arg in sys.argv)
    )
    if is_test:
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False}
        )
    db_url = settings.SQLALCHEMY_DATABASE_URI
    engine_kwargs = {"pool_pre_ping": True}
    if not db_url.startswith("sqlite"):
        engine_kwargs.update({"pool_size": 10, "max_overflow": 20})
    else:
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(db_url, **engine_kwargs)

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency providing a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
