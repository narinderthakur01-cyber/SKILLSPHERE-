import os
import io
import re
import csv
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
import pytesseract
import pymupdf as fitz
import docx
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import (
    QuestionBankItem, QuestionBankOption, QuestionDifficultyEnum,
    QuestionStatusEnum, User, RoleEnum, QuestionImportBatch
)
from app.services.ocr_service import preprocess_image, is_tesseract_available
from app.services.question_bank_service import QuestionBankService

class QuestionExtractorService:

    SUPPORTED_EXTENSIONS = {
        ".pdf", ".docx", ".xlsx", ".xls", ".csv", ".txt", ".jpg", ".jpeg", ".png"
    }

    @classmethod
    def calculate_jaccard_similarity(cls, text1: str, text2: str) -> float:
        """Calculate token-based Jaccard similarity for semantic/lexical duplicate detection."""
        tokens1 = set(re.findall(r"\w+", text1.lower()))
        tokens2 = set(re.findall(r"\w+", text2.lower()))
        if not tokens1 or not tokens2:
            return 0.0
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        return float(intersection) / float(union) if union > 0 else 0.0

    @classmethod
    def extract_from_file(
        cls,
        file_path: str,
        filename: str,
        content_type: str,
        technology_hint: str = "Python",
        topic_hint: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Main extraction entry point.
        Extracts questions from PDF, DOCX, XLSX, CSV, TXT, or Image files,
        parses MCQs, options, correct answers, explanations, marks, and checks duplicates.
        """
        ext = Path(filename).suffix.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format '{ext}'. Supported: {', '.join(sorted(cls.SUPPORTED_EXTENSIONS))}")

        extracted_items = []
        is_scanned = False

        if ext == ".pdf":
            extracted_items, is_scanned = cls._extract_from_pdf(file_path, technology_hint, topic_hint)
        elif ext == ".docx":
            extracted_items = cls._extract_from_docx(file_path, technology_hint, topic_hint)
        elif ext in [".xlsx", ".xls"]:
            extracted_items = cls._extract_from_excel(file_path, technology_hint, topic_hint)
        elif ext == ".csv":
            extracted_items = cls._extract_from_csv(file_path, technology_hint, topic_hint)
        elif ext == ".txt":
            extracted_items = cls._extract_from_txt(file_path, technology_hint, topic_hint)
        elif ext in [".jpg", ".jpeg", ".png"]:
            extracted_items, is_scanned = cls._extract_from_image(file_path, technology_hint, topic_hint)

        # Post-process, validate, and check duplicates
        validated_items = []
        valid_count = 0
        missing_answer_count = 0
        duplicate_count = 0

        # Query existing questions in DB if session is available for similarity comparison
        existing_questions = []
        if db is not None:
            existing_questions = db.query(QuestionBankItem.id, QuestionBankItem.question_text).filter(
                QuestionBankItem.status == QuestionStatusEnum.ACTIVE
            ).all()

        seen_in_batch = set()

        for idx, item in enumerate(extracted_items, start=1):
            q_text = (item.get("question_text") or "").strip()
            options = item.get("options") or []
            correct_key = item.get("correct_option")
            explanation = (item.get("explanation") or "").strip() or None
            marks = item.get("marks") or 1
            diff_raw = (item.get("difficulty") or "INTERMEDIATE").upper()
            tech = (item.get("technology") or technology_hint or "General").strip()
            topic = (item.get("topic") or topic_hint or "General").strip()
            page_num = item.get("source_page") or 1

            diff_enum = QuestionDifficultyEnum.INTERMEDIATE
            if diff_raw in QuestionDifficultyEnum.__members__:
                diff_enum = QuestionDifficultyEnum[diff_raw]
            elif diff_raw == "EASY":
                diff_enum = QuestionDifficultyEnum.BEGINNER
            elif diff_raw in ["MEDIUM", "MED"]:
                diff_enum = QuestionDifficultyEnum.INTERMEDIATE
            elif diff_raw == "HARD":
                diff_enum = QuestionDifficultyEnum.ADVANCED

            errors = []
            if not q_text or len(q_text) < 5:
                errors.append("Question prompt is too short (min 5 characters).")

            if len(options) < 2:
                errors.append(f"Insufficient options found ({len(options)}). Minimum 2 required.")
            elif len(options) > 5:
                # Trim to top 5 options
                options = options[:5]

            # Verify options and correct answer
            has_correct_key = False
            for opt in options:
                if correct_key and str(opt.get("option_key")).upper() == str(correct_key).upper():
                    opt["is_correct"] = True
                    has_correct_key = True
                else:
                    opt["is_correct"] = bool(opt.get("is_correct", False))
                    if opt["is_correct"]:
                        has_correct_key = True

            validation_status = "VALID"
            similar_to_id = None
            similarity_reason = None

            # Duplicate detection
            clean_q = re.sub(r"\s+", " ", q_text.lower()).strip()
            if clean_q in seen_in_batch:
                validation_status = "EXACT_DUPLICATE"
                errors.append("Duplicate question within this uploaded file.")
                duplicate_count += 1
            else:
                seen_in_batch.add(clean_q)

                if db is not None:
                    # Check exact DB duplicate
                    is_dup, dup_id, msg = QuestionBankService.check_duplicate(db, q_text)
                    if is_dup:
                        validation_status = "EXACT_DUPLICATE"
                        similar_to_id = dup_id
                        similarity_reason = msg
                        duplicate_count += 1
                    else:
                        # Check semantic/lexical similarity (> 0.75 Jaccard)
                        for eq_id, eq_text in existing_questions:
                            sim = cls.calculate_jaccard_similarity(q_text, eq_text)
                            if sim >= 0.75:
                                validation_status = "SIMILAR_DUPLICATE"
                                similar_to_id = eq_id
                                similarity_reason = f"High similarity ({int(sim*100)}%) with question: '{eq_text[:60]}...'"
                                break

            if validation_status not in ["EXACT_DUPLICATE", "SIMILAR_DUPLICATE"]:
                if len(options) < 2:
                    validation_status = "INVALID_OPTIONS"
                elif not has_correct_key:
                    validation_status = "MISSING_ANSWER"
                    missing_answer_count += 1
                else:
                    valid_count += 1

            validated_items.append({
                "temp_id": f"q_{idx}",
                "row_index": idx,
                "question_text": q_text,
                "options": options,
                "correct_option": correct_key if has_correct_key else None,
                "has_correct_answer": has_correct_key,
                "explanation": explanation,
                "marks": max(1, marks),
                "difficulty": diff_enum.value,
                "technology": tech,
                "topic": topic,
                "source_file": filename,
                "source_page": page_num,
                "validation_status": validation_status,
                "errors": errors,
                "similar_to_id": similar_to_id,
                "similarity_reason": similarity_reason,
                "is_approved": (validation_status == "VALID")
            })

        return {
            "filename": filename,
            "file_type": ext.lstrip(".").upper(),
            "is_scanned": is_scanned,
            "total_extracted": len(validated_items),
            "valid_count": valid_count,
            "missing_answer_count": missing_answer_count,
            "duplicate_count": duplicate_count,
            "questions": validated_items
        }

    # =========================================================================
    # FILE EXTRACTORS
    # =========================================================================

    @classmethod
    def _extract_from_pdf(
        cls, file_path: str, tech_hint: str, topic_hint: Optional[str]
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """Extract text page by page with PyMuPDF and fallback to Tesseract OCR for scanned pages."""
        doc = fitz.open(file_path)
        total_pages = len(doc)
        pages_content = []
        is_scanned = False

        for p_idx in range(total_pages):
            page = doc.load_page(p_idx)
            text = page.get_text().strip()
            page_num = p_idx + 1

            # If digital text is empty or minimal, trigger OCR on page image
            if len(text) < 40:
                is_scanned = True
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                if is_tesseract_available():
                    processed = preprocess_image(img)
                    try:
                        text = pytesseract.image_to_string(processed).strip()
                    except Exception:
                        text = ""
                else:
                    text = ""

            if text:
                pages_content.append((page_num, text))

        doc.close()
        items = cls._parse_text_blocks(pages_content, tech_hint, topic_hint)
        return items, is_scanned

    @classmethod
    def _extract_from_docx(
        cls, file_path: str, tech_hint: str, topic_hint: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Extract paragraphs and tables from Word DOCX document."""
        import docx
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

        # Also extract any table content
        table_lines = []
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    table_lines.append(" | ".join(row_cells))

        combined_text = "\n".join(paragraphs + table_lines)
        return cls._parse_text_blocks([(1, combined_text)], tech_hint, topic_hint)

    @classmethod
    def _extract_from_excel(
        cls, file_path: str, tech_hint: str, topic_hint: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Extract MCQs from Excel workbook using openpyxl or pandas."""
        import pandas as pd
        df = pd.read_excel(file_path)
        return cls._parse_tabular_dataframe(df, tech_hint, topic_hint)

    @classmethod
    def _extract_from_csv(
        cls, file_path: str, tech_hint: str, topic_hint: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Extract MCQs from CSV file either as tabular columns or raw text lines."""
        import pandas as pd
        try:
            df = pd.read_csv(file_path)
            # If standard columns exist, parse as table
            if len(df.columns) >= 3 and any("question" in str(c).lower() for c in df.columns):
                return cls._parse_tabular_dataframe(df, tech_hint, topic_hint)
        except Exception:
            pass

        # Fallback to text lines
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            with open(file_path, "r", encoding="latin-1", errors="ignore") as f:
                content = f.read()
        return cls._parse_text_blocks([(1, content)], tech_hint, topic_hint)

    @classmethod
    def _extract_from_txt(
        cls, file_path: str, tech_hint: str, topic_hint: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Extract MCQs from plain text file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            with open(file_path, "r", encoding="latin-1", errors="ignore") as f:
                content = f.read()
        return cls._parse_text_blocks([(1, content)], tech_hint, topic_hint)

    @classmethod
    def _extract_from_image(
        cls, file_path: str, tech_hint: str, topic_hint: Optional[str]
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """Extract MCQs from JPG or PNG image using preprocessing + Tesseract OCR."""
        if not is_tesseract_available():
            return [], True

        img = Image.open(file_path)
        processed = preprocess_image(img)
        try:
            text = pytesseract.image_to_string(processed).strip()
        except Exception:
            text = ""
        items = cls._parse_text_blocks([(1, text)], tech_hint, topic_hint)
        return items, True

    # =========================================================================
    # TABULAR PARSER (EXCEL & CSV)
    # =========================================================================

    @classmethod
    def _parse_tabular_dataframe(
        cls, df, tech_hint: str, topic_hint: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Parse DataFrame rows with column normalization."""
        col_map = {}
        for col in df.columns:
            clean_col = str(col).strip().lower().replace(" ", "_").replace("-", "_")
            if any(k in clean_col for k in ["question_text", "question", "prompt", "q_text"]):
                col_map["question_text"] = col
            elif clean_col in ["option_a", "opt_a", "option1", "opt1", "choice_a"]:
                col_map["option_a"] = col
            elif clean_col in ["option_b", "opt_b", "option2", "opt2", "choice_b"]:
                col_map["option_b"] = col
            elif clean_col in ["option_c", "opt_c", "option3", "opt3", "choice_c"]:
                col_map["option_c"] = col
            elif clean_col in ["option_d", "opt_d", "option4", "opt4", "choice_d"]:
                col_map["option_d"] = col
            elif clean_col in ["option_e", "opt_e", "option5", "opt5", "choice_e"]:
                col_map["option_e"] = col
            elif any(k in clean_col for k in ["correct_option", "correct_answer", "answer", "ans", "correct", "key"]):
                col_map["correct_option"] = col
            elif any(k in clean_col for k in ["explanation", "exp", "rationale", "solution"]):
                col_map["explanation"] = col
            elif any(k in clean_col for k in ["difficulty", "diff", "level"]):
                col_map["difficulty"] = col
            elif any(k in clean_col for k in ["marks", "points", "score"]):
                col_map["marks"] = col
            elif any(k in clean_col for k in ["technology", "tech", "subject"]):
                col_map["technology"] = col
            elif any(k in clean_col for k in ["topic", "subtopic"]):
                col_map["topic"] = col

        items = []
        for idx, row in df.iterrows():
            q_col = col_map.get("question_text")
            q_text = str(row[q_col]).strip() if q_col and pd.notna(row.get(q_col)) else ""
            if not q_text or q_text.lower() in ["nan", "none", ""]:
                continue

            options = []
            for key in ["A", "B", "C", "D", "E"]:
                opt_col = col_map.get(f"option_{key.lower()}")
                if opt_col and pd.notna(row.get(opt_col)):
                    val = str(row[opt_col]).strip()
                    if val and val.lower() != "nan":
                        options.append({"option_key": key, "option_text": val, "is_correct": False})

            corr_col = col_map.get("correct_option")
            corr_raw = str(row[corr_col]).strip().upper() if corr_col and pd.notna(row.get(corr_col)) else None
            # If answer is 'Option A' or 'A', sanitize to 'A'
            if corr_raw:
                m = re.search(r"([A-E])", corr_raw)
                corr_key = m.group(1) if m else corr_raw
            else:
                corr_key = None

            exp_col = col_map.get("explanation")
            exp = str(row[exp_col]).strip() if exp_col and pd.notna(row.get(exp_col)) and str(row[exp_col]).lower() != "nan" else None

            diff_col = col_map.get("difficulty")
            diff = str(row[diff_col]).strip().upper() if diff_col and pd.notna(row.get(diff_col)) else "INTERMEDIATE"

            marks_col = col_map.get("marks")
            try:
                marks = int(row[marks_col]) if marks_col and pd.notna(row.get(marks_col)) else 1
            except Exception:
                marks = 1

            tech_col = col_map.get("technology")
            tech = str(row[tech_col]).strip() if tech_col and pd.notna(row.get(tech_col)) and str(row[tech_col]).lower() != "nan" else tech_hint

            topic_col = col_map.get("topic")
            topic = str(row[topic_col]).strip() if topic_col and pd.notna(row.get(topic_col)) and str(row[topic_col]).lower() != "nan" else topic_hint

            items.append({
                "question_text": q_text,
                "options": options,
                "correct_option": corr_key,
                "explanation": exp,
                "marks": max(1, marks),
                "difficulty": diff,
                "technology": tech,
                "topic": topic,
                "source_page": idx + 1
            })

        return items

    # =========================================================================
    # UNSTRUCTURED / DOCUMENT TEXT PARSER
    # =========================================================================

    @classmethod
    def _parse_text_blocks(
        cls,
        pages_content: List[Tuple[int, str]],
        tech_hint: str,
        topic_hint: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Robust multi-pattern regex engine for unstructured question text from PDF, DOCX, TXT, OCR.
        Identifies questions, options (A-D/E), answer keys, explanations, marks, and difficulty.
        """
        extracted = []

        for page_num, text in pages_content:
            # Clean up carriage returns
            clean_text = text.replace("\r\n", "\n").replace("\r", "\n")
            
            # Split text by question header patterns
            # e.g., "1.", "Q1:", "Question 1.", "1)", "[1]"
            q_split_pattern = r"(?:^|\n)\s*(?:(?:Q(?:uestion)?\.?\s*#?(\d+)|(\d+)[\.\)\]]|\#(\d+))[\s\:\-\.]+)"
            matches = list(re.finditer(q_split_pattern, clean_text, flags=re.IGNORECASE))

            if not matches:
                # If no numbered pattern matches, try fallback: split by double newlines and check for options
                blocks = re.split(r"\n\s*\n+", clean_text)
                for b_idx, block in enumerate(blocks, start=1):
                    item = cls._parse_single_question_block(block, tech_hint, topic_hint, page_num)
                    if item:
                        extracted.append(item)
                continue

            for i in range(len(matches)):
                start = matches[i].start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(clean_text)
                block = clean_text[start:end].strip()

                item = cls._parse_single_question_block(block, tech_hint, topic_hint, page_num)
                if item:
                    extracted.append(item)

        return extracted

    @classmethod
    def _parse_single_question_block(
        cls,
        block: str,
        tech_hint: str,
        topic_hint: Optional[str],
        page_num: int
    ) -> Optional[Dict[str, Any]]:
        """Parses a single MCQ block into prompt, options, answer key, explanation, and metadata."""
        if not block or len(block.strip()) < 10:
            return None

        # Look for answer key
        ans_match = re.search(
            r"(?:^|\n)\s*(?:Correct\s*(?:Answer|Option)?|Answer|Ans|Key)\s*[\:\-\=]?\s*[\(\[]?([A-Ea-e])[\)\]]?",
            block,
            flags=re.IGNORECASE
        )
        correct_key = ans_match.group(1).upper() if ans_match else None

        # Look for explanation
        exp_match = re.search(
            r"(?:^|\n)\s*(?:Explanation|Rationale|Exp|Solution)\s*[\:\-\=]\s*(.+?)(?=(?:\n\s*(?:Difficulty|Marks?|Answer|Ans|Q\d+|\d+[\.\)])|\Z))",
            block,
            flags=re.IGNORECASE | re.DOTALL
        )
        explanation = exp_match.group(1).strip() if exp_match else None

        # Look for difficulty
        diff_match = re.search(
            r"(?:^|\n)\s*Difficulty\s*[\:\-\=]\s*(BEGINNER|INTERMEDIATE|ADVANCED|EASY|MEDIUM|HARD)",
            block,
            flags=re.IGNORECASE
        )
        difficulty = diff_match.group(1).upper() if diff_match else "INTERMEDIATE"

        # Look for marks
        marks_match = re.search(
            r"(?:(?:^|\n)\s*(?:Marks?|Points?)\s*[\:\-\=]\s*(\d+)|\[(\d+)\s*(?:marks?|pts?)\])",
            block,
            flags=re.IGNORECASE
        )
        marks = 1
        if marks_match:
            try:
                marks = int(marks_match.group(1) or marks_match.group(2))
            except Exception:
                marks = 1

        # Look for topic or technology override in block
        topic_match = re.search(r"(?:^|\n)\s*Topic\s*[\:\-\=]\s*([^\n]+)", block, flags=re.IGNORECASE)
        topic = topic_match.group(1).strip() if topic_match else topic_hint

        tech_match = re.search(r"(?:^|\n)\s*(?:Technology|Subject)\s*[\:\-\=]\s*([^\n]+)", block, flags=re.IGNORECASE)
        tech = tech_match.group(1).strip() if tech_match else tech_hint

        # Strip answer/explanation/metadata lines before extracting question prompt and options
        meta_boundary = len(block)
        for m in [ans_match, exp_match, diff_match]:
            if m and m.start() < meta_boundary:
                meta_boundary = m.start()

        body = block[:meta_boundary].strip()

        # Extract Options: A), B), C), D), E) or (A), [A], a., etc.
        # Find all option prefixes
        opt_pattern = r"(?:^|\n)\s*(?:[\(\[]?([A-Ea-e])[\.\)\]\:\-]|\b([A-Ea-e])\b[\.\)])\s*"
        opt_matches = list(re.finditer(opt_pattern, body))

        if not opt_matches or len(opt_matches) < 2:
            return None

        # The question prompt is everything before the first option match
        first_opt_start = opt_matches[0].start()
        q_raw = body[:first_opt_start].strip()

        # Clean leading numbers from question text (e.g. "1. What is..." -> "What is...")
        clean_q = re.sub(r"^(?:Q(?:uestion)?\.?\s*#?\d+|\d+[\.\)\]]|\#\d+)[\s\:\-\.]*", "", q_raw, flags=re.IGNORECASE).strip()
        if not clean_q:
            clean_q = q_raw

        options = []
        for j in range(len(opt_matches)):
            opt_key = (opt_matches[j].group(1) or opt_matches[j].group(2)).upper()
            opt_start = opt_matches[j].end()
            opt_end = opt_matches[j + 1].start() if j + 1 < len(opt_matches) else len(body)
            opt_text = body[opt_start:opt_end].strip()

            options.append({
                "option_key": opt_key,
                "option_text": opt_text,
                "is_correct": (correct_key is not None and opt_key == correct_key)
            })

        return {
            "question_text": clean_q,
            "options": options,
            "correct_option": correct_key,
            "explanation": explanation,
            "marks": max(1, marks),
            "difficulty": difficulty,
            "technology": tech or "General",
            "topic": topic or "General",
            "source_page": page_num
        }
