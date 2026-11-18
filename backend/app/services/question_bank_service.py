import csv
import io
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.models.models import (
    QuestionBankItem, QuestionBankOption, QuestionCollection,
    QuestionCollectionItem, QuestionDifficultyEnum, QuestionStatusEnum,
    Assessment, AssessmentQuestion, AssessmentQuestionOption,
    CandidateAssessmentAssignment, AssessmentAttempt, AssessmentCandidateAnswer,
    AssessmentResult, AssessmentAssignmentStatusEnum, AttemptStatusEnum,
    AssessmentResultEnum, User, RoleEnum, QuestionImportBatch
)
from app.schemas.schemas import (
    QuestionBankItemCreate, QuestionBankItemUpdate, QuestionBankItemResponse,
    QuestionBankOptionResponse, QuestionCollectionCreate, QuestionCollectionResponse,
    BulkImportPreviewResponse, BulkImportRowValidation, DuplicateCheckResponse,
    AssessmentAnalyticsResponse, BatchImportRequest, BatchImportResponse
)

class QuestionBankService:

    @staticmethod
    def check_duplicate(db: Session, text: str, exclude_id: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """Check for exact or near-duplicate question text."""
        clean_text = text.strip().lower()
        query = db.query(QuestionBankItem).filter(
            QuestionBankItem.status == QuestionStatusEnum.ACTIVE,
            func.lower(QuestionBankItem.question_text) == clean_text
        )
        if exclude_id:
            query = query.filter(QuestionBankItem.id != exclude_id)
        match = query.first()
        if match:
            return True, match.id, f"Identical question already exists under '{match.technology} > {match.topic}'."
        return False, None, None

    @classmethod
    def list_questions(
        cls,
        db: Session,
        user: User,
        technology: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        search: Optional[str] = None,
        status_filter: str = "ACTIVE",
        only_mine: bool = False,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        query = db.query(QuestionBankItem)

        if status_filter != "ALL":
            status_enum = QuestionStatusEnum.ARCHIVED if status_filter.upper() == "ARCHIVED" else QuestionStatusEnum.ACTIVE
            query = query.filter(QuestionBankItem.status == status_enum)

        if technology and technology.strip():
            query = query.filter(func.lower(QuestionBankItem.technology) == technology.strip().lower())

        if topic and topic.strip():
            query = query.filter(func.lower(QuestionBankItem.topic) == topic.strip().lower())

        if difficulty and difficulty.strip() and difficulty.upper() in QuestionDifficultyEnum.__members__:
            query = query.filter(QuestionBankItem.difficulty == QuestionDifficultyEnum[difficulty.upper()])

        if search and search.strip():
            pattern = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(QuestionBankItem.question_text).like(pattern),
                    func.lower(QuestionBankItem.topic).like(pattern),
                    func.lower(QuestionBankItem.technology).like(pattern)
                )
            )

        if only_mine and user:
            query = query.filter(QuestionBankItem.created_by_user_id == user.id)

        total_count = query.count()
        offset = max(0, (page - 1) * limit)
        items = query.order_by(QuestionBankItem.created_at.desc()).offset(offset).limit(limit).all()

        results = []
        for q in items:
            opts = [
                QuestionBankOptionResponse(
                    id=o.id,
                    option_key=o.option_key,
                    option_text=o.option_text,
                    is_correct=o.is_correct
                ) for o in q.options
            ]
            creator_name = q.created_by.name if q.created_by else ("System Admin" if q.is_global else "Unknown")
            results.append(QuestionBankItemResponse(
                id=q.id,
                technology=q.technology,
                topic=q.topic,
                subtopic=q.subtopic,
                difficulty=q.difficulty.value,
                question_type=q.question_type,
                question_text=q.question_text,
                explanation=q.explanation,
                marks=q.marks,
                tags=q.tags or [],
                is_global=q.is_global,
                created_by_user_id=q.created_by_user_id,
                creator_name=creator_name,
                status=q.status.value,
                usage_count=q.usage_count,
                created_at=q.created_at,
                updated_at=q.updated_at,
                options=opts
            ))

        return {
            "total": total_count,
            "page": page,
            "limit": limit,
            "pages": (total_count + limit - 1) // limit if limit > 0 else 1,
            "items": results
        }

    @classmethod
    def create_question(cls, db: Session, user: User, data: QuestionBankItemCreate) -> QuestionBankItem:
        # Validate options
        if len(data.options) < 2 or len(data.options) > 5:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Questions must have between 2 and 5 options.")

        correct_count = sum(1 for o in data.options if o.is_correct)
        if correct_count != 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exactly one option must be marked as correct.")

        diff_enum = QuestionDifficultyEnum.INTERMEDIATE
        if data.difficulty.upper() in QuestionDifficultyEnum.__members__:
            diff_enum = QuestionDifficultyEnum[data.difficulty.upper()]

        is_global = (user.role == RoleEnum.ADMIN)

        q = QuestionBankItem(
            technology=data.technology.strip(),
            topic=data.topic.strip(),
            subtopic=data.subtopic.strip() if data.subtopic else None,
            difficulty=diff_enum,
            question_type="SINGLE_CORRECT_MCQ",
            question_text=data.question_text.strip(),
            explanation=data.explanation.strip() if data.explanation else None,
            marks=data.marks,
            tags=[t.strip().lower() for t in data.tags if t.strip()],
            is_global=is_global,
            created_by_user_id=user.id,
            status=QuestionStatusEnum.ACTIVE,
            usage_count=0
        )
        db.add(q)
        db.flush()

        for opt in data.options:
            o = QuestionBankOption(
                question_bank_id=q.id,
                option_key=opt.option_key.strip().upper(),
                option_text=opt.option_text.strip(),
                is_correct=opt.is_correct
            )
            db.add(o)

        db.commit()
        db.refresh(q)
        return q

    @classmethod
    def update_question(cls, db: Session, user: User, question_id: str, data: QuestionBankItemUpdate) -> QuestionBankItem:
        q = db.query(QuestionBankItem).filter(QuestionBankItem.id == question_id).first()
        if not q:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

        # Recruiter authorization guard
        if user.role != RoleEnum.ADMIN:
            if q.is_global or q.created_by_user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Recruiters cannot edit global predefined questions. Duplicate it to your custom bank instead."
                )

        if data.technology is not None:
            q.technology = data.technology.strip()
        if data.topic is not None:
            q.topic = data.topic.strip()
        if data.subtopic is not None:
            q.subtopic = data.subtopic.strip()
        if data.difficulty is not None and data.difficulty.upper() in QuestionDifficultyEnum.__members__:
            q.difficulty = QuestionDifficultyEnum[data.difficulty.upper()]
        if data.question_text is not None:
            q.question_text = data.question_text.strip()
        if data.explanation is not None:
            q.explanation = data.explanation.strip()
        if data.marks is not None:
            q.marks = data.marks
        if data.tags is not None:
            q.tags = [t.strip().lower() for t in data.tags if t.strip()]
        if data.status is not None and data.status.upper() in QuestionStatusEnum.__members__:
            q.status = QuestionStatusEnum[data.status.upper()]

        if data.options is not None:
            if len(data.options) < 2 or len(data.options) > 5:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Questions must have between 2 and 5 options.")
            correct_count = sum(1 for o in data.options if o.is_correct)
            if correct_count != 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exactly one option must be marked as correct.")

            db.query(QuestionBankOption).filter(QuestionBankOption.question_bank_id == q.id).delete()
            db.flush()
            for opt in data.options:
                o = QuestionBankOption(
                    question_bank_id=q.id,
                    option_key=opt.option_key.strip().upper(),
                    option_text=opt.option_text.strip(),
                    is_correct=opt.is_correct
                )
                db.add(o)

        q.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(q)
        return q

    @classmethod
    def duplicate_question(cls, db: Session, user: User, question_id: str) -> QuestionBankItem:
        source = db.query(QuestionBankItem).filter(QuestionBankItem.id == question_id).first()
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source question not found.")

        new_q = QuestionBankItem(
            technology=source.technology,
            topic=source.topic,
            subtopic=source.subtopic,
            difficulty=source.difficulty,
            question_type=source.question_type,
            question_text=f"{source.question_text} (Copy)",
            explanation=source.explanation,
            marks=source.marks,
            tags=list(source.tags or []),
            is_global=False,
            created_by_user_id=user.id,
            status=QuestionStatusEnum.ACTIVE,
            usage_count=0
        )
        db.add(new_q)
        db.flush()

        for opt in source.options:
            new_opt = QuestionBankOption(
                question_bank_id=new_q.id,
                option_key=opt.option_key,
                option_text=opt.option_text,
                is_correct=opt.is_correct
            )
            db.add(new_opt)

        db.commit()
        db.refresh(new_q)
        return new_q

    @classmethod
    def archive_question(cls, db: Session, user: User, question_id: str) -> None:
        q = db.query(QuestionBankItem).filter(QuestionBankItem.id == question_id).first()
        if not q:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

        if user.role != RoleEnum.ADMIN and q.created_by_user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only archive your own custom questions.")

        q.status = QuestionStatusEnum.ARCHIVED
        q.updated_at = datetime.now(timezone.utc)
        db.commit()

    @classmethod
    def get_technologies_and_topics(cls, db: Session) -> Dict[str, Any]:
        """Fetch all technologies and topics present in active question bank with item counts."""
        items = db.query(QuestionBankItem).filter(QuestionBankItem.status == QuestionStatusEnum.ACTIVE).all()
        tech_map: Dict[str, Dict[str, int]] = {}

        for it in items:
            tech = it.technology
            topic = it.topic
            if tech not in tech_map:
                tech_map[tech] = {}
            tech_map[tech][topic] = tech_map[tech].get(topic, 0) + 1

        formatted = []
        tech_names = []
        topics_by_tech = {}

        for tech, topics in sorted(tech_map.items()):
            tech_names.append(tech)
            topics_by_tech[tech] = [t for t, _ in sorted(topics.items())]
            formatted.append({
                "technology": tech,
                "total_questions": sum(topics.values()),
                "topics": [{"name": top, "count": cnt} for top, cnt in sorted(topics.items())]
            })

        return {
            "technologies": tech_names,
            "topics_by_technology": topics_by_tech,
            "details": formatted
        }

    # ------------------ COLLECTIONS ------------------
    @classmethod
    def create_collection(cls, db: Session, user: User, data: QuestionCollectionCreate) -> QuestionCollection:
        coll = QuestionCollection(
            user_id=user.id,
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            technology=data.technology.strip() if data.technology else None
        )
        db.add(coll)
        db.flush()

        for idx, q_id in enumerate(data.question_ids):
            item = QuestionCollectionItem(
                collection_id=coll.id,
                question_bank_id=q_id,
                order_num=idx + 1
            )
            db.add(item)

        db.commit()
        db.refresh(coll)
        return coll

    @classmethod
    def list_collections(cls, db: Session, user: User) -> List[QuestionCollectionResponse]:
        colls = db.query(QuestionCollection).filter(QuestionCollection.user_id == user.id).all()
        res = []
        for c in colls:
            res.append(QuestionCollectionResponse(
                id=c.id,
                name=c.name,
                description=c.description,
                technology=c.technology,
                question_count=len(c.items),
                created_at=c.created_at,
                updated_at=c.updated_at
            ))
        return res

    @classmethod
    def get_collection(cls, db: Session, user: User, collection_id: str) -> QuestionCollectionResponse:
        c = db.query(QuestionCollection).filter(
            QuestionCollection.id == collection_id,
            QuestionCollection.user_id == user.id
        ).first()
        if not c:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")

        q_responses = []
        for item in sorted(c.items, key=lambda x: x.order_num):
            q = item.question_bank_item
            if not q:
                continue
            opts = [
                QuestionBankOptionResponse(
                    id=o.id,
                    option_key=o.option_key,
                    option_text=o.option_text,
                    is_correct=o.is_correct
                ) for o in q.options
            ]
            q_responses.append(QuestionBankItemResponse(
                id=q.id,
                technology=q.technology,
                topic=q.topic,
                subtopic=q.subtopic,
                difficulty=q.difficulty.value,
                question_type=q.question_type,
                question_text=q.question_text,
                explanation=q.explanation,
                marks=q.marks,
                tags=q.tags or [],
                is_global=q.is_global,
                created_by_user_id=q.created_by_user_id,
                creator_name=q.created_by.name if q.created_by else "System",
                status=q.status.value,
                usage_count=q.usage_count,
                created_at=q.created_at,
                updated_at=q.updated_at,
                options=opts
            ))

        return QuestionCollectionResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            technology=c.technology,
            question_count=len(q_responses),
            created_at=c.created_at,
            updated_at=c.updated_at,
            questions=q_responses
        )

    # ------------------ AUTOMATIC QUESTION SAMPLER ------------------
    @classmethod
    def sample_questions_from_bank(
        cls,
        db: Session,
        technology: str,
        topic: Optional[str] = None,
        count: int = 5,
        difficulty_dist: Optional[Dict[str, int]] = None,
        marks_per_question: Optional[int] = None
    ) -> List[QuestionBankItem]:
        """
        Samples questions from the active question bank according to technology,
        topic, and difficulty distribution without replacement.
        Validates against eligible count and explains shortages clearly without silently returning partial sets.
        """
        base_query = db.query(QuestionBankItem).filter(
            QuestionBankItem.status == QuestionStatusEnum.ACTIVE,
            func.lower(QuestionBankItem.technology) == technology.strip().lower()
        )
        if topic and topic.strip():
            base_query = base_query.filter(func.lower(QuestionBankItem.topic) == topic.strip().lower())

        all_matching = base_query.all()
        total_available = len(all_matching)

        if total_available == 0:
            topic_str = f" and topic '{topic.strip()}'" if topic and topic.strip() else ""
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient questions in Question Bank for technology '{technology}'{topic_str}. "
                    f"Requested {count} questions, but only 0 questions are available. "
                    f"Please lower the question count or upload questions to the bank."
                )
            )

        if total_available < count:
            topic_str = f" and topic '{topic.strip()}'" if topic and topic.strip() else ""
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient questions in Question Bank for technology '{technology}'{topic_str}. "
                    f"Requested {count} questions, but only {total_available} questions are available. "
                    f"Please lower the question count or add more questions to the bank."
                )
            )

        selected_items = []
        if difficulty_dist:
            raw_beginner = int(difficulty_dist.get("BEGINNER") or difficulty_dist.get("beginner") or difficulty_dist.get("beginner_pct") or 0)
            raw_intermediate = int(difficulty_dist.get("INTERMEDIATE") or difficulty_dist.get("intermediate") or difficulty_dist.get("intermediate_pct") or 0)
            raw_advanced = int(difficulty_dist.get("ADVANCED") or difficulty_dist.get("advanced") or difficulty_dist.get("advanced_pct") or 0)

            total_pct = raw_beginner + raw_intermediate + raw_advanced
            if total_pct > 0:
                beg_c = max(0, round(count * (raw_beginner / total_pct)))
                adv_c = max(0, round(count * (raw_advanced / total_pct)))
                int_c = count - beg_c - adv_c
                if int_c < 0:
                    beg_c = max(0, beg_c + int_c)
                    int_c = 0
                normalized_dist = {"BEGINNER": beg_c, "INTERMEDIATE": int_c, "ADVANCED": adv_c}
            else:
                normalized_dist = {}

            # Group matching questions by difficulty
            by_diff = {
                QuestionDifficultyEnum.BEGINNER: [q for q in all_matching if q.difficulty == QuestionDifficultyEnum.BEGINNER],
                QuestionDifficultyEnum.INTERMEDIATE: [q for q in all_matching if q.difficulty == QuestionDifficultyEnum.INTERMEDIATE],
                QuestionDifficultyEnum.ADVANCED: [q for q in all_matching if q.difficulty == QuestionDifficultyEnum.ADVANCED],
            }

            for diff_str, needed_count in normalized_dist.items():
                if needed_count <= 0:
                    continue
                diff_enum = QuestionDifficultyEnum[diff_str.upper()]
                tier_pool = by_diff.get(diff_enum, [])
                take = min(needed_count, len(tier_pool))
                if take > 0:
                    chosen = random.sample(tier_pool, take)
                    selected_items.extend(chosen)

            # If distribution left any unfilled spots, sample from the remainder of all_matching
            selected_ids = {q.id for q in selected_items}
            remainder = [q for q in all_matching if q.id not in selected_ids]
            needed_remaining = count - len(selected_items)
            if needed_remaining > 0 and len(remainder) >= needed_remaining:
                selected_items.extend(random.sample(remainder, needed_remaining))
        else:
            selected_items = random.sample(all_matching, count)

        # Apply uniform marks if requested
        if marks_per_question is not None and marks_per_question > 0:
            for q in selected_items:
                q.marks = marks_per_question

        return selected_items

    @classmethod
    def get_availability(cls, db: Session, technology: Optional[str] = None, topic: Optional[str] = None) -> Dict[str, Any]:
        """Check question availability and counts per difficulty in real time."""
        base_query = db.query(QuestionBankItem).filter(
            QuestionBankItem.status == QuestionStatusEnum.ACTIVE
        )
        if technology and technology.strip():
            base_query = base_query.filter(func.lower(QuestionBankItem.technology) == technology.strip().lower())
        if topic and topic.strip():
            base_query = base_query.filter(func.lower(QuestionBankItem.topic) == topic.strip().lower())

        items = base_query.all()
        by_diff = {"BEGINNER": 0, "INTERMEDIATE": 0, "ADVANCED": 0}
        for item in items:
            diff_key = item.difficulty.value if hasattr(item.difficulty, "value") else str(item.difficulty)
            by_diff[diff_key] = by_diff.get(diff_key, 0) + 1

        return {
            "technology": technology.strip() if technology and technology.strip() else None,
            "topic": topic.strip() if topic and topic.strip() else None,
            "total_available": len(items),
            "by_difficulty": by_diff,
            "beginner_count": by_diff.get("BEGINNER", 0),
            "intermediate_count": by_diff.get("INTERMEDIATE", 0),
            "advanced_count": by_diff.get("ADVANCED", 0),
        }

    # ------------------ BULK CSV IMPORT ------------------
    @classmethod
    def bulk_import_csv(
        cls,
        db: Session,
        user: User,
        csv_content: str,
        commit: bool = False
    ) -> BulkImportPreviewResponse:
        """
        Validates and optionally imports questions from a CSV template.
        Header expected:
        technology,topic,subtopic,difficulty,question_text,explanation,marks,option_a,option_b,option_c,option_d,correct_option,tags
        """
        reader = csv.DictReader(io.StringIO(csv_content))
        row_validations: List[BulkImportRowValidation] = []
        valid_items_to_save = []

        valid_count = 0
        invalid_count = 0

        for idx, row in enumerate(reader, start=1):
            errors = []
            tech = (row.get("technology") or "").strip()
            topic = (row.get("topic") or "").strip()
            subtopic = (row.get("subtopic") or "").strip() or None
            diff_raw = (row.get("difficulty") or "INTERMEDIATE").strip().upper()
            q_text = (row.get("question_text") or "").strip()
            explanation = (row.get("explanation") or "").strip() or None
            marks_raw = (row.get("marks") or "5").strip()
            corr_raw = (row.get("correct_option") or "A").strip().upper()
            tags_raw = (row.get("tags") or "").strip()

            if not tech:
                errors.append("Missing required 'technology'.")
            if not topic:
                errors.append("Missing required 'topic'.")
            if not q_text or len(q_text) < 5:
                errors.append("Question text must be at least 5 characters.")

            # Validate options
            options = []
            for k in ["A", "B", "C", "D", "E"]:
                opt_val = (row.get(f"option_{k.lower()}") or "").strip()
                if opt_val:
                    options.append({"key": k, "text": opt_val, "is_correct": (k == corr_raw)})

            if len(options) < 2:
                errors.append("Each question must provide at least 2 options (option_a, option_b).")
            if not any(o["is_correct"] for o in options):
                errors.append(f"Correct option '{corr_raw}' does not match any provided options.")

            diff_enum = QuestionDifficultyEnum.INTERMEDIATE
            if diff_raw in QuestionDifficultyEnum.__members__:
                diff_enum = QuestionDifficultyEnum[diff_raw]
            else:
                errors.append(f"Invalid difficulty '{diff_raw}'. Must be BEGINNER, INTERMEDIATE, or ADVANCED.")

            try:
                marks = int(marks_raw)
                if marks <= 0:
                    errors.append("Marks must be positive.")
            except ValueError:
                marks = 5
                errors.append("Marks must be a valid integer.")

            # Duplicate check
            if q_text:
                is_dup, _, _ = cls.check_duplicate(db, q_text)
                if is_dup:
                    errors.append("A question with identical text already exists.")

            is_valid = len(errors) == 0
            if is_valid:
                valid_count += 1
                tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
                valid_items_to_save.append({
                    "technology": tech,
                    "topic": topic,
                    "subtopic": subtopic,
                    "difficulty": diff_enum,
                    "question_text": q_text,
                    "explanation": explanation,
                    "marks": marks,
                    "tags": tags,
                    "options": options
                })
            else:
                invalid_count += 1

            row_validations.append(BulkImportRowValidation(
                row_index=idx,
                is_valid=is_valid,
                question_text=q_text or f"Row #{idx}",
                technology=tech or "N/A",
                topic=topic or "N/A",
                difficulty=diff_raw,
                marks=marks,
                errors=errors
            ))

        # If commit is True and there are valid rows, save them
        if commit and valid_items_to_save:
            admin_flag = (user.role == RoleEnum.ADMIN)
            for item in valid_items_to_save:
                q_bank = QuestionBankItem(
                    technology=item["technology"],
                    topic=item["topic"],
                    subtopic=item["subtopic"],
                    difficulty=item["difficulty"],
                    question_type="SINGLE_CORRECT_MCQ",
                    question_text=item["question_text"],
                    explanation=item["explanation"],
                    marks=item["marks"],
                    tags=item["tags"],
                    is_global=admin_flag,
                    created_by_user_id=user.id,
                    status=QuestionStatusEnum.ACTIVE,
                    usage_count=0
                )
                db.add(q_bank)
                db.flush()

                for opt in item["options"]:
                    o = QuestionBankOption(
                        question_bank_id=q_bank.id,
                        option_key=opt["key"],
                        option_text=opt["text"],
                        is_correct=opt["is_correct"]
                    )
                    db.add(o)

            db.commit()

        return BulkImportPreviewResponse(
            total_rows=len(row_validations),
            valid_rows_count=valid_count,
            invalid_rows_count=invalid_count,
            rows=row_validations,
            can_commit=(valid_count > 0)
        )

    # ------------------ STRUCTURED BATCH IMPORT ------------------
    @classmethod
    def batch_import_questions(
        cls,
        db: Session,
        user: User,
        data: BatchImportRequest
    ) -> BatchImportResponse:
        """
        Atomically save recruiter-approved questions into the question bank.
        Preserves recruiter ownership, tracks source file & page, and maintains import batch history.
        """
        if user.role not in [RoleEnum.ADMIN, RoleEnum.RECRUITER]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

        batch = QuestionImportBatch(
            user_id=user.id,
            filename=data.filename,
            file_type=data.file_type,
            file_size=data.file_size or 0,
            total_extracted=len(data.questions),
            total_approved=0,
            technology=data.technology,
            topic=data.topic
        )
        db.add(batch)
        db.flush()

        admin_flag = (user.role == RoleEnum.ADMIN)
        imported_ids = []

        try:
            for q_item in data.questions:
                if not q_item.is_approved:
                    continue

                clean_text = q_item.question_text.strip()
                if len(clean_text) < 5:
                    continue

                if len(q_item.options) < 2 or len(q_item.options) > 5:
                    continue

                correct_count = sum(1 for o in q_item.options if o.is_correct)
                if correct_count != 1:
                    # Verified answer key is mandatory
                    continue

                # Duplicate check: don't insert if exact question exists
                existing = db.query(QuestionBankItem).filter(
                    QuestionBankItem.status == QuestionStatusEnum.ACTIVE,
                    func.lower(QuestionBankItem.question_text) == func.lower(clean_text)
                ).first()
                if existing:
                    continue

                diff_enum = QuestionDifficultyEnum.INTERMEDIATE
                diff_str = (q_item.difficulty or "INTERMEDIATE").upper()
                if diff_str in QuestionDifficultyEnum.__members__:
                    diff_enum = QuestionDifficultyEnum[diff_str]
                elif diff_str == "EASY":
                    diff_enum = QuestionDifficultyEnum.BEGINNER
                elif diff_str in ["MEDIUM", "MED"]:
                    diff_enum = QuestionDifficultyEnum.INTERMEDIATE
                elif diff_str == "HARD":
                    diff_enum = QuestionDifficultyEnum.ADVANCED

                q_bank = QuestionBankItem(
                    technology=q_item.technology or data.technology,
                    topic=q_item.topic or data.topic or "General",
                    subtopic=q_item.subtopic,
                    difficulty=diff_enum,
                    question_type="SINGLE_CORRECT_MCQ",
                    question_text=clean_text,
                    explanation=q_item.explanation,
                    marks=q_item.marks,
                    tags=q_item.tags or [],
                    is_global=admin_flag,
                    created_by_user_id=user.id,
                    status=QuestionStatusEnum.ACTIVE,
                    usage_count=0,
                    source_file=q_item.source_file or data.filename,
                    source_page=q_item.source_page,
                    import_batch_id=batch.id
                )
                db.add(q_bank)
                db.flush()

                for opt in q_item.options:
                    o = QuestionBankOption(
                        question_bank_id=q_bank.id,
                        option_key=opt.option_key.upper(),
                        option_text=opt.option_text.strip(),
                        is_correct=opt.is_correct
                    )
                    db.add(o)

                imported_ids.append(q_bank.id)

            batch.total_approved = len(imported_ids)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to import questions: {str(e)}"
            )

        return BatchImportResponse(
            imported_count=len(imported_ids),
            import_batch_id=batch.id,
            imported_question_ids=imported_ids,
            message=f"Successfully imported {len(imported_ids)} question(s) into Question Bank."
        )

    # ------------------ ASSESSMENT ANALYTICS ------------------
    @classmethod
    def get_assessment_analytics(cls, db: Session, assessment_id: str) -> AssessmentAnalyticsResponse:
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

        assignments = db.query(CandidateAssessmentAssignment).filter(
            CandidateAssessmentAssignment.assessment_id == assessment.id
        ).all()

        total_assigned = len(assignments)
        started_count = sum(1 for a in assignments if a.attempt is not None)
        results = [a.result for a in assignments if a.result is not None]
        completed_count = len(results)

        passed_count = sum(1 for r in results if r.result == AssessmentResultEnum.PASSED)
        failed_count = sum(1 for r in results if r.result == AssessmentResultEnum.FAILED)
        pass_pct = round((passed_count / completed_count * 100.0), 2) if completed_count > 0 else 0.0
        avg_marks = round(sum(r.marks_obtained for r in results) / completed_count, 2) if completed_count > 0 else 0.0

        # Question-level analytics
        questions = db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == assessment.id).order_by(AssessmentQuestion.order_num).all()
        q_analytics = []
        high_failure_questions = []

        difficulty_stats: Dict[str, Dict[str, int]] = {
            "BEGINNER": {"total": 0, "correct": 0},
            "INTERMEDIATE": {"total": 0, "correct": 0},
            "ADVANCED": {"total": 0, "correct": 0}
        }

        for q in questions:
            answers = db.query(AssessmentCandidateAnswer).filter(
                AssessmentCandidateAnswer.question_id == q.id
            ).all()

            att_count = len(answers)
            corr_count = sum(1 for ans in answers if ans.is_correct is True)
            fail_count = att_count - corr_count
            corr_rate = round((corr_count / att_count * 100.0), 1) if att_count > 0 else 0.0
            fail_rate = round((fail_count / att_count * 100.0), 1) if att_count > 0 else 0.0

            diff_level = "INTERMEDIATE"
            if q.bank_question and q.bank_question.difficulty:
                diff_level = q.bank_question.difficulty.value

            if diff_level in difficulty_stats:
                difficulty_stats[diff_level]["total"] += att_count
                difficulty_stats[diff_level]["correct"] += corr_count

            q_info = {
                "question_id": q.id,
                "order_num": q.order_num,
                "question_text": q.question_text,
                "marks": q.marks,
                "difficulty": diff_level,
                "attempts_count": att_count,
                "correct_count": corr_count,
                "correct_rate_percentage": corr_rate,
                "failure_rate_percentage": fail_rate
            }
            q_analytics.append(q_info)

            if att_count >= 1 and fail_rate >= 60.0:
                high_failure_questions.append(q_info)

        return AssessmentAnalyticsResponse(
            assessment_id=assessment.id,
            title=assessment.title,
            total_assigned=total_assigned,
            total_started=started_count,
            total_completed=completed_count,
            total_passed=passed_count,
            total_failed=failed_count,
            pass_percentage=pass_pct,
            average_marks=avg_marks,
            questions_analytics=q_analytics,
            difficulty_performance=difficulty_stats,
            high_failure_questions=high_failure_questions
        )
