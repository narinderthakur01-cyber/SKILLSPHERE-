import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import (
    QuestionBankItem, QuestionBankOption, QuestionDifficultyEnum,
    QuestionStatusEnum, User, RoleEnum
)
from app.db.questions_data import QUESTIONS_DATA

PREDEFINED_QUESTIONS = QUESTIONS_DATA

def seed_question_bank(db: Session = None):
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        print("🌱 Seeding Question Bank with standardized technical questions...")
        admin = db.query(User).filter(User.role == RoleEnum.ADMIN).first()
        admin_id = admin.id if admin else None

        added_count = 0
        updated_count = 0

        for item in PREDEFINED_QUESTIONS:
            existing = db.query(QuestionBankItem).filter(
                QuestionBankItem.question_text == item["question_text"]
            ).first()
            if existing:
                # Update marks or status if needed, but do not create duplicate
                continue

            q = QuestionBankItem(
                technology=item["technology"],
                topic=item["topic"],
                subtopic=item.get("subtopic"),
                difficulty=item["difficulty"],
                question_type="SINGLE_CORRECT_MCQ",
                question_text=item["question_text"],
                explanation=item.get("explanation"),
                marks=item.get("marks", 1),
                tags=item.get("tags", []),
                is_global=True,
                created_by_user_id=admin_id,
                status=QuestionStatusEnum.ACTIVE,
                usage_count=0
            )
            db.add(q)
            db.flush()

            for opt in item["options"]:
                o = QuestionBankOption(
                    question_bank_id=q.id,
                    option_key=opt["key"],
                    option_text=opt["text"],
                    is_correct=opt["is_correct"]
                )
                db.add(o)

            added_count += 1

        db.commit()
        print(f"✅ Question Bank seeded successfully! Added {added_count} new questions. Total active in bank: {db.query(QuestionBankItem).count()}")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding question bank: {e}")
        raise e
    finally:
        if own_session:
            db.close()

if __name__ == "__main__":
    seed_question_bank()
