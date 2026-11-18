from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Skill
from app.schemas.schemas import SkillResponse

router = APIRouter(prefix="/skills", tags=["Skills"])

@router.get("", response_model=List[SkillResponse])
def get_skills(
    query: Optional[str] = Query(None, description="Search skills by prefix or substring"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieve skill suggestions for job posting and candidate profile autocomplete."""
    q = db.query(Skill)
    if query and query.strip():
        q = q.filter(Skill.skill_name.ilike(f"%{query.strip().lower()}%"))
    skills = q.order_by(Skill.skill_name.asc()).limit(limit).all()
    return [SkillResponse.model_validate(s) for s in skills]
