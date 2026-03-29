"""
Async Database Repository using aiosqlite with connection pooling

Replaces the synchronous database.py with async operations for better performance.
"""
import aiosqlite
import json
import time
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseRepository:
    """
    Async database repository with connection pooling.
    
    Uses aiosqlite for non-blocking database operations.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize database repository.
        
        Args:
            db_path: Path to SQLite database file (defaults to settings.DB_PATH)
        """
        self.db_path = db_path or settings.DB_PATH
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Establish database connection and initialize schema"""
        if self._connection is not None:
            logger.warning("Database already connected")
            return
        
        # Ensure parent directory exists
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect with WAL mode for better concurrency
        self._connection = await aiosqlite.connect(self.db_path)
        
        # Enable Write-Ahead Logging for concurrent reads/writes
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA synchronous=NORMAL")
        await self._connection.execute("PRAGMA foreign_keys=ON")
        
        # Initialize schema
        await self._init_schema()
        
        logger.info(f"✅ Database connected: {self.db_path}")
    
    async def close(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Database connection closed")
    
    async def _init_schema(self):
        """Initialize database tables"""
        
        # Users Table
        await self._connection.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at REAL NOT NULL
        )
        ''')
        
        # Create index on email for faster lookups
        await self._connection.execute('''
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        ''')
        
        # Sessions Table
        await self._connection.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            persona TEXT,
            topic TEXT,
            difficulty TEXT,
            job_description TEXT,
            summary TEXT,
            scores TEXT,
            analytics TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        # Create index on user_id for faster session lookups
        await self._connection.execute('''
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)
        ''')

        # Compound index for user timelines
        await self._connection.execute('''
        CREATE INDEX IF NOT EXISTS idx_sessions_user_timestamp_desc
        ON sessions(user_id, timestamp DESC)
        ''')
        
        # Messages Table (Chat History)
        await self._connection.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp REAL NOT NULL,
            rating INTEGER,
            feedback TEXT,
            evidence_json TEXT,
            improved_answer TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
        ''')

        # Evidence table for richer, queryable scorer inputs and auditability.
        await self._connection.execute('''
        CREATE TABLE IF NOT EXISTS turn_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            message_id INTEGER,
            payload_json TEXT NOT NULL,
            timestamp REAL NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE SET NULL
        )
        ''')

        await self._connection.execute('''
        CREATE INDEX IF NOT EXISTS idx_turn_evidence_session_timestamp
        ON turn_evidence(session_id, timestamp ASC)
        ''')
        
        # Create index on session_id for faster message retrieval
        await self._connection.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)
        ''')

        # Compound index for ordered transcript retrieval
        await self._connection.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_session_timestamp_asc
        ON messages(session_id, timestamp ASC)
        ''')
        
        await self._connection.commit()
        await self._apply_migrations()
        logger.info("Database schema initialized")

    async def _apply_migrations(self):
        """Apply additive schema migrations for existing databases."""
        await self._ensure_column("sessions", "job_description", "TEXT")
        await self._ensure_column("sessions", "resume_text", "TEXT")  # Phase 4: Resume persistence
        await self._ensure_column("messages", "evidence_json", "TEXT")
        await self._connection.commit()

    async def _ensure_column(self, table: str, column: str, column_def: str):
        """Add a column if it does not exist."""
        async with self._connection.execute(f"PRAGMA table_info({table})") as cursor:
            rows = await cursor.fetchall()
            existing = {row[1] for row in rows}

        if column not in existing:
            await self._connection.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {column_def}"
            )
            logger.info("Applied migration: added column %s.%s", table, column)
    
    # ===== USER OPERATIONS =====
    
    async def create_user(self, user_id: str, email: str, password_hash: str, full_name: str) -> bool:
        """
        Create a new user.
        
        Args:
            user_id: Unique user identifier
            email: User email (must be unique)
            password_hash: Hashed password
            full_name: User's full name
            
        Returns:
            True if user created, False if email already exists
        """
        try:
            await self._connection.execute(
                '''
                INSERT INTO users (id, email, password_hash, full_name, created_at)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (user_id, email, password_hash, full_name, time.time())
            )
            await self._connection.commit()
            logger.info(f"👤 Created user: {email}")
            return True
        except aiosqlite.IntegrityError:
            logger.warning(f"⚠️ User already exists: {email}")
            return False
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by email.
        
        Args:
            email: User email
            
        Returns:
            User dict or None if not found
        """
        async with self._connection.execute(
            'SELECT * FROM users WHERE email = ?',
            (email,)
        ) as cursor:
            cursor.row_factory = aiosqlite.Row
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User dict or None if not found
        """
        async with self._connection.execute(
            'SELECT * FROM users WHERE id = ?',
            (user_id,)
        ) as cursor:
            cursor.row_factory = aiosqlite.Row
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    # ===== SESSION OPERATIONS =====
    
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        persona: str,
        topic: str,
        difficulty: str,
        job_description: str | None = None,
        resume_text: str | None = None,
    ) -> bool:
        """
        Create a new interview session.
        
        Args:
            session_id: Unique session identifier
            user_id: User who owns this session
            persona: Interview persona
            topic: Interview topic
            difficulty: Difficulty level
            job_description: Optional job description
            resume_text: Optional resume/CV text
            
        Returns:
            True if session created, False if session already exists
        """
        try:
            await self._connection.execute(
                '''
                INSERT INTO sessions (session_id, user_id, timestamp, persona, topic, difficulty, job_description, resume_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (session_id, user_id, time.time(), persona, topic, difficulty, job_description, resume_text)
            )
            await self._connection.commit()
            logger.info(f"📝 Created session {session_id} for user {user_id}")
            return True
        except aiosqlite.IntegrityError:
            logger.warning(f"⚠️ Session already exists: {session_id}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session dict or None if not found
        """
        async with self._connection.execute(
            'SELECT * FROM sessions WHERE session_id = ?',
            (session_id,)
        ) as cursor:
            cursor.row_factory = aiosqlite.Row
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of session dicts (ordered by timestamp DESC)
        """
        async with self._connection.execute(
            '''
            SELECT * FROM sessions 
            WHERE user_id = ? 
            ORDER BY timestamp DESC
            ''',
            (user_id,)
        ) as cursor:
            cursor.row_factory = aiosqlite.Row
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def session_belongs_to_user(self, session_id: str, user_id: str) -> bool:
        """Check if a session is owned by a user."""
        async with self._connection.execute(
            '''
            SELECT 1
            FROM sessions
            WHERE session_id = ? AND user_id = ?
            LIMIT 1
            ''',
            (session_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None
    
    async def update_session_analytics(
        self,
        session_id: str,
        analytics: Dict[str, Any],
        summary: str,
        scores: Dict[str, Any]
    ) -> None:
        """
        Update session analytics, summary, and scores.
        
        Args:
            session_id: Session ID
            analytics: Analytics data
            summary: Session summary
            scores: Score data
        """
        await self._connection.execute(
            '''
            UPDATE sessions 
            SET analytics = ?, summary = ?, scores = ?
            WHERE session_id = ?
            ''',
            (json.dumps(analytics), summary, json.dumps(scores), session_id)
        )
        await self._connection.commit()
    
    # ===== MESSAGE OPERATIONS =====
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        rating: Optional[int] = None,
        feedback: Optional[str] = None,
        evidence_json: Optional[Dict[str, Any]] = None,
        improved_answer: Optional[str] = None
    ) -> int:
        """
        Add a message to the session.
        
        Args:
            session_id: Session ID
            role: Message role ('user' or 'ai')
            content: Message content
            rating: Optional rating
            feedback: Optional feedback
            improved_answer: Optional improved answer
        """
        cursor = await self._connection.execute(
            '''
            INSERT INTO messages (session_id, role, content, timestamp, rating, feedback, evidence_json, improved_answer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                session_id,
                role,
                content,
                time.time(),
                rating,
                feedback,
                json.dumps(evidence_json) if evidence_json else None,
                improved_answer,
            )
        )
        await self._connection.commit()
        return int(cursor.lastrowid)

    async def add_turn_evidence(
        self,
        session_id: str,
        payload: Dict[str, Any],
        message_id: Optional[int] = None,
    ) -> int:
        """Store structured per-turn evidence used by scorer and audits."""
        cursor = await self._connection.execute(
            '''
            INSERT INTO turn_evidence (session_id, message_id, payload_json, timestamp)
            VALUES (?, ?, ?, ?)
            ''',
            (session_id, message_id, json.dumps(payload), time.time()),
        )
        await self._connection.commit()
        return int(cursor.lastrowid)
    
    async def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of message dicts (ordered by timestamp ASC)
        """
        async with self._connection.execute(
            'SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC',
            (session_id,)
        ) as cursor:
            cursor.row_factory = aiosqlite.Row
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def update_message_analysis(
        self,
        message_id: int,
        rating: int,
        feedback: str,
        improved_answer: str
    ) -> None:
        """
        Update message analysis data.
        
        Args:
            message_id: Message ID
            rating: Rating score
            feedback: Feedback text
            improved_answer: Improved answer text
        """
        await self._connection.execute(
            '''
            UPDATE messages 
            SET rating = ?, feedback = ?, improved_answer = ?
            WHERE id = ?
            ''',
            (rating, feedback, improved_answer, message_id)
        )
        await self._connection.commit()

    def is_connected(self) -> bool:
        """Return True when repository has an active connection."""
        return self._connection is not None


# Global database instance
db_repository: Optional[DatabaseRepository] = None


async def get_db() -> DatabaseRepository:
    """
    Dependency function for FastAPI routes.
    
    Returns:
        Global database repository instance
    """
    global db_repository
    if db_repository is None:
        raise RuntimeError("Database not initialized. Call init_db() during startup.")
    return db_repository


async def init_db(db_path: str = None) -> DatabaseRepository:
    """
    Initialize global database instance.
    
    Args:
        db_path: Optional custom database path
        
    Returns:
        Initialized database repository
    """
    global db_repository
    
    # Close existing connection if it exists
    if db_repository is not None:
        await db_repository.close()
    
    db_repository = DatabaseRepository(db_path)
    await db_repository.connect()
    return db_repository


async def close_db():
    """Close global database connection"""
    global db_repository
    if db_repository:
        await db_repository.close()
        db_repository = None
