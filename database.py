import sqlite3
import json
import time
import os

DB_NAME = "interview_data.db"

class Database:
    def __init__(self):
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(DB_NAME, check_same_thread=False)

    def init_db(self):
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password_hash TEXT,
            full_name TEXT,
            created_at REAL
        )
        ''')

        # Sessions Table (Updated to include user_id)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            timestamp REAL,
            persona TEXT,
            topic TEXT,
            difficulty TEXT,
            summary TEXT,
            scores JSON,
            analytics JSON,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')
        
        # Messages Table (Chat History)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp REAL,
            rating INTEGER,
            feedback TEXT,
            improved_answer TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {DB_NAME}")

    def create_user(self, user_id, email, password_hash, full_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO users (id, email, password_hash, full_name, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, email, password_hash, full_name, time.time()))
            conn.commit()
            print(f"👤 DB: Created user {email}")
            return True
        except sqlite3.IntegrityError:
            print(f"⚠️ DB: User {email} already exists")
            return False
        finally:
            conn.close()

    def get_user_by_email(self, email):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
        
    def get_user_by_id(self, user_id):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def create_session(self, session_id, user_id, persona, topic, difficulty):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO sessions (session_id, user_id, timestamp, persona, topic, difficulty)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, user_id, time.time(), persona, topic, difficulty))
            conn.commit()
            print(f"📝 DB: Created session {session_id} for user {user_id}")
        except sqlite3.IntegrityError:
            print(f"⚠️ DB: Session {session_id} already exists")
        finally:
            conn.close()

    def add_message(self, session_id, role, content, rating=None, feedback=None, improved_answer=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO messages (session_id, role, content, timestamp, rating, feedback, improved_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, role, content, time.time(), rating, feedback, improved_answer))
        conn.commit()
        conn.close()

    def get_session(self, session_id):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None

    def get_user_sessions(self, user_id):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM sessions 
            WHERE user_id = ? 
            ORDER BY timestamp DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_messages(self, session_id):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC', (session_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_session_analytics(self, session_id, analytics, summary, scores):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE sessions 
        SET analytics = ?, summary = ?, scores = ?
        WHERE session_id = ?
        ''', (json.dumps(analytics), summary, json.dumps(scores), session_id))
        conn.commit()
        conn.close()

    def update_message_analysis(self, message_id, rating, feedback, improved_answer):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE messages 
        SET rating = ?, feedback = ?, improved_answer = ?
        WHERE id = ?
        ''', (rating, feedback, improved_answer, message_id))
        conn.commit()
        conn.close()
