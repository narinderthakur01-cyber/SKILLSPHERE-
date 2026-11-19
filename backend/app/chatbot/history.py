import os
import sqlite3
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.core.config import settings

class SessionOwnershipError(Exception):
    """Raised when a user attempts to access or modify a session owned by another user."""
    pass

class ChatHistoryStore(ABC):
    """
    Abstract interface for SkillSphere Assistant conversation history storage.
    Enforces identical method signatures and strict ownership verification across all storage backends.
    """

    @abstractmethod
    def get_or_create_session(
        self,
        session_id: Optional[str],
        user_id: str,
        user_role: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve existing session verifying ownership, or create a new session bound to user_id."""
        pass

    @abstractmethod
    def get_session(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session record. Raises SessionOwnershipError if user_id does not match owner."""
        pass

    @abstractmethod
    def add_message(
        self,
        session_id: str,
        user_id: str,
        sender: str,
        content: str,
        intent: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """Append user or assistant message to the session."""
        pass

    @abstractmethod
    def get_session_messages(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve all messages for a session in ascending chronological order."""
        pass

    @abstractmethod
    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete session and all its associated messages. Enforces ownership."""
        pass

    @abstractmethod
    def update_session_topic(self, session_id: str, user_id: str, last_topic: str) -> bool:
        """Update active topic for context-aware conversation tracking."""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Verify storage backend connectivity."""
        pass


class SQLiteHistoryStore(ChatHistoryStore):
    """
    Local SQLite conversation history store for assignment evaluation and offline development.
    Stores records in an isolated local database file with strict user isolation.
    """

    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            configured_path = getattr(settings, "CHATBOT_SQLITE_PATH", "")
            if configured_path:
                db_path = configured_path
            else:
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                data_dir = os.path.join(backend_dir, "data")
                os.makedirs(data_dir, exist_ok=True)
                db_path = os.path.join(data_dir, "chatbot_history.db")
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        """Initialize tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chatbot_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_role TEXT NOT NULL,
                    title TEXT,
                    last_topic TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chatbot_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT,
                    confidence REAL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES chatbot_sessions(id) ON DELETE CASCADE
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS ix_cb_sessions_user_id ON chatbot_sessions(user_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_cb_messages_session_created ON chatbot_messages(session_id, created_at);")
            conn.commit()

    def get_or_create_session(
        self,
        session_id: Optional[str],
        user_id: str,
        user_role: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        now_str = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            if session_id:
                row = conn.execute("SELECT * FROM chatbot_sessions WHERE id = ?", (session_id,)).fetchone()
                if row:
                    if row["user_id"] != user_id:
                        raise SessionOwnershipError(f"Forbidden: User {user_id} does not own session {session_id}")
                    return dict(row)

            # Create new session
            new_id = session_id or str(uuid.uuid4())
            initial_title = title or "New Conversation"
            conn.execute(
                """
                INSERT INTO chatbot_sessions (id, user_id, user_role, title, last_topic, created_at, updated_at)
                VALUES (?, ?, ?, ?, NULL, ?, ?)
                """,
                (new_id, user_id, user_role, initial_title, now_str, now_str)
            )
            conn.commit()
            return {
                "id": new_id,
                "user_id": user_id,
                "user_role": user_role,
                "title": initial_title,
                "last_topic": None,
                "created_at": now_str,
                "updated_at": now_str
            }

    def get_session(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM chatbot_sessions WHERE id = ?", (session_id,)).fetchone()
            if not row:
                return None
            if row["user_id"] != user_id:
                raise SessionOwnershipError(f"Forbidden: User {user_id} does not own session {session_id}")
            return dict(row)

    def add_message(
        self,
        session_id: str,
        user_id: str,
        sender: str,
        content: str,
        intent: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        session = self.get_session(session_id, user_id)
        if not session:
            raise KeyError(f"Session {session_id} not found.")

        msg_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chatbot_messages (id, session_id, sender, content, intent, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (msg_id, session_id, sender, content, intent, confidence, now_str)
            )
            # Update session updated_at
            conn.execute("UPDATE chatbot_sessions SET updated_at = ? WHERE id = ?", (now_str, session_id))
            conn.commit()

        return {
            "id": msg_id,
            "session_id": session_id,
            "sender": sender,
            "content": content,
            "intent": intent,
            "confidence": confidence,
            "created_at": now_str
        }

    def get_session_messages(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        self.get_session(session_id, user_id) # validates ownership or raises
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chatbot_messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_session(self, session_id: str, user_id: str) -> bool:
        session = self.get_session(session_id, user_id)
        if not session:
            return False
        with self._get_connection() as conn:
            conn.execute("DELETE FROM chatbot_messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM chatbot_sessions WHERE id = ?", (session_id,))
            conn.commit()
        return True

    def update_session_topic(self, session_id: str, user_id: str, last_topic: str) -> bool:
        self.get_session(session_id, user_id)
        now_str = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE chatbot_sessions SET last_topic = ?, updated_at = ? WHERE id = ?",
                (last_topic, now_str, session_id)
            )
            conn.commit()
        return True

    def is_healthy(self) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute("SELECT 1;").fetchone()
                return True
        except Exception:
            return False


class PostgresHistoryStore(ChatHistoryStore):
    """
    Production PostgreSQL conversation history store.
    Uses dedicated, isolated tables ('chatbot_sessions', 'chatbot_messages') without altering existing business schemas.
    """

    def __init__(self):
        from app.core import database as db_core
        from sqlalchemy import text
        self.db_core = db_core
        self.text = text
        self.engine = db_core.engine
        
        # Verify connection on startup
        if not self.is_healthy():
            raise RuntimeError(
                "PostgreSQL chatbot storage is explicitly configured via CHATBOT_STORAGE='postgres', "
                "but the configured database is unreachable or invalid."
            )
        self._init_tables()

    def _init_tables(self):
        """Create isolated chatbot tables if they do not exist."""
        with self.engine.begin() as conn:
            conn.execute(self.text("""
                CREATE TABLE IF NOT EXISTS chatbot_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    user_role VARCHAR(20) NOT NULL,
                    title VARCHAR(150),
                    last_topic VARCHAR(100),
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                );
            """))
            conn.execute(self.text("""
                CREATE TABLE IF NOT EXISTS chatbot_messages (
                    id VARCHAR(36) PRIMARY KEY,
                    session_id VARCHAR(36) NOT NULL REFERENCES chatbot_sessions(id) ON DELETE CASCADE,
                    sender VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    intent VARCHAR(100),
                    confidence FLOAT,
                    created_at TIMESTAMPTZ NOT NULL
                );
            """))
            conn.execute(self.text("CREATE INDEX IF NOT EXISTS ix_pg_cb_sessions_user_id ON chatbot_sessions(user_id);"))
            conn.execute(self.text("CREATE INDEX IF NOT EXISTS ix_pg_cb_messages_session_created ON chatbot_messages(session_id, created_at);"))

    def get_or_create_session(
        self,
        session_id: Optional[str],
        user_id: str,
        user_role: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        now_dt = datetime.now(timezone.utc)
        with self.engine.begin() as conn:
            if session_id:
                row = conn.execute(
                    self.text("SELECT * FROM chatbot_sessions WHERE id = :sid"),
                    {"sid": session_id}
                ).mappings().fetchone()
                if row:
                    if row["user_id"] != user_id:
                        raise SessionOwnershipError(f"Forbidden: User {user_id} does not own session {session_id}")
                    return dict(row)

            new_id = session_id or str(uuid.uuid4())
            initial_title = title or "New Conversation"
            conn.execute(
                self.text("""
                    INSERT INTO chatbot_sessions (id, user_id, user_role, title, last_topic, created_at, updated_at)
                    VALUES (:id, :uid, :role, :title, NULL, :created_at, :updated_at)
                """),
                {
                    "id": new_id,
                    "uid": user_id,
                    "role": user_role,
                    "title": initial_title,
                    "created_at": now_dt,
                    "updated_at": now_dt
                }
            )
            return {
                "id": new_id,
                "user_id": user_id,
                "user_role": user_role,
                "title": initial_title,
                "last_topic": None,
                "created_at": now_dt.isoformat(),
                "updated_at": now_dt.isoformat()
            }

    def get_session(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        with self.engine.connect() as conn:
            row = conn.execute(
                self.text("SELECT * FROM chatbot_sessions WHERE id = :sid"),
                {"sid": session_id}
            ).mappings().fetchone()
            if not row:
                return None
            if row["user_id"] != user_id:
                raise SessionOwnershipError(f"Forbidden: User {user_id} does not own session {session_id}")
            res = dict(row)
            if isinstance(res.get("created_at"), datetime):
                res["created_at"] = res["created_at"].isoformat()
            if isinstance(res.get("updated_at"), datetime):
                res["updated_at"] = res["updated_at"].isoformat()
            return res

    def add_message(
        self,
        session_id: str,
        user_id: str,
        sender: str,
        content: str,
        intent: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        self.get_session(session_id, user_id)
        msg_id = str(uuid.uuid4())
        now_dt = datetime.now(timezone.utc)
        with self.engine.begin() as conn:
            conn.execute(
                self.text("""
                    INSERT INTO chatbot_messages (id, session_id, sender, content, intent, confidence, created_at)
                    VALUES (:id, :sid, :sender, :content, :intent, :confidence, :created_at)
                """),
                {
                    "id": msg_id,
                    "sid": session_id,
                    "sender": sender,
                    "content": content,
                    "intent": intent,
                    "confidence": confidence,
                    "created_at": now_dt
                }
            )
            conn.execute(
                self.text("UPDATE chatbot_sessions SET updated_at = :updated_at WHERE id = :sid"),
                {"updated_at": now_dt, "sid": session_id}
            )
        return {
            "id": msg_id,
            "session_id": session_id,
            "sender": sender,
            "content": content,
            "intent": intent,
            "confidence": confidence,
            "created_at": now_dt.isoformat()
        }

    def get_session_messages(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        self.get_session(session_id, user_id)
        with self.engine.connect() as conn:
            rows = conn.execute(
                self.text("SELECT * FROM chatbot_messages WHERE session_id = :sid ORDER BY created_at ASC"),
                {"sid": session_id}
            ).mappings().fetchall()
            messages = []
            for r in rows:
                item = dict(r)
                if isinstance(item.get("created_at"), datetime):
                    item["created_at"] = item["created_at"].isoformat()
                messages.append(item)
            return messages

    def delete_session(self, session_id: str, user_id: str) -> bool:
        session = self.get_session(session_id, user_id)
        if not session:
            return False
        with self.engine.begin() as conn:
            conn.execute(self.text("DELETE FROM chatbot_messages WHERE session_id = :sid"), {"sid": session_id})
            conn.execute(self.text("DELETE FROM chatbot_sessions WHERE id = :sid"), {"sid": session_id})
        return True

    def update_session_topic(self, session_id: str, user_id: str, last_topic: str) -> bool:
        self.get_session(session_id, user_id)
        now_dt = datetime.now(timezone.utc)
        with self.engine.begin() as conn:
            conn.execute(
                self.text("UPDATE chatbot_sessions SET last_topic = :topic, updated_at = :updated_at WHERE id = :sid"),
                {"topic": last_topic, "updated_at": now_dt, "sid": session_id}
            )
        return True

    def is_healthy(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(self.text("SELECT 1;"))
                return True
        except Exception:
            return False


_global_history_store: Optional[ChatHistoryStore] = None

def get_history_store() -> ChatHistoryStore:
    """
    Factory function returning the configured ChatHistoryStore singleton.
    Defaults to SQLite for local development and grading.
    Switches to PostgreSQL only when explicitly configured via CHATBOT_STORAGE='postgres'.
    """
    global _global_history_store
    if _global_history_store is not None:
        return _global_history_store

    backend = getattr(settings, "CHATBOT_STORAGE", "sqlite").lower().strip()
    if backend == "postgres":
        _global_history_store = PostgresHistoryStore()
    elif backend == "sqlite":
        _global_history_store = SQLiteHistoryStore()
    else:
        raise ValueError(f"Unsupported CHATBOT_STORAGE configuration: '{backend}'. Expected 'sqlite' or 'postgres'.")

    return _global_history_store
