from typing import List, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.models import User, RoleEnum, Candidate, Recruiter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )
    return user

def require_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """Enforce email verification for all non-admin protected operations."""
    if current_user.role != RoleEnum.ADMIN and not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address to continue."
        )
    return current_user

def require_role(allowed_roles: List[RoleEnum]):
    """Enforce role-based access control and email verification dependency."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Insufficient privileges. Required one of: {[r.value for r in allowed_roles]}"
            )
        if current_user.role != RoleEnum.ADMIN and not current_user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required. Please verify your email address to continue."
            )
        return current_user
    return role_checker

def get_current_candidate(
    current_user: User = Depends(require_role([RoleEnum.JOB_SEEKER])),
    db: Session = Depends(get_db)
) -> Candidate:
    """Return Candidate profile of current logged-in Job Seeker."""
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        # Auto-create empty profile if missing
        candidate = Candidate(user_id=current_user.id)
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
    return candidate

def get_current_admin(
    current_user: User = Depends(require_role([RoleEnum.ADMIN]))
) -> User:
    """Return User if current user has ADMIN role."""
    return current_user

def get_current_recruiter(
    current_user: User = Depends(require_role([RoleEnum.RECRUITER])),
    db: Session = Depends(get_db)
) -> Recruiter:
    """Return Recruiter profile of current logged-in Recruiter."""
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
    if not recruiter:
        recruiter = Recruiter(user_id=current_user.id)
        db.add(recruiter)
        db.commit()
        db.refresh(recruiter)
    return recruiter
