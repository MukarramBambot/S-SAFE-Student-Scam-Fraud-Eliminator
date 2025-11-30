import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger("backend.database")

DB_PATH = Path(__file__).parent / "ssafe.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Initialize the database schema."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Chats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    analysis_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
                )
            """)
            
            # Analysis History (legacy - keep for compatibility)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    input_text TEXT,
                    risk_score INTEGER,
                    verdict TEXT,
                    model_used TEXT
                )
            """)
            
            # Uploaded Files
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_type TEXT,
                    uploaded_at TEXT NOT NULL,
                    stored_path TEXT
                )
            """)
            
            # Company Reports
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT UNIQUE NOT NULL,
                    summary TEXT,
                    risk_level TEXT,
                    last_updated TEXT
                )
            """)
            
            conn.commit()
            logger.info("Database tables initialized at %s", DB_PATH)
    except Exception as e:
        logger.error("Failed to create tables: %s", e)

# ===== USER OPERATIONS =====

def create_user(username: str, email: str, password_hash: str) -> Optional[int]:
    """Create a new user."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            """, (username, email, password_hash))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        logger.error("User already exists: %s", e)
        return None
    except Exception as e:
        logger.error("Failed to create user: %s", e)
        return None

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error("Failed to get user: %s", e)
        return None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error("Failed to get user: %s", e)
        return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error("Failed to get user: %s", e)
        return None

# ===== CHAT OPERATIONS =====

def create_chat(user_id: int, title: str = "New Chat") -> Optional[int]:
    """Create a new chat session."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chats (user_id, title)
                VALUES (?, ?)
            """, (user_id, title))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error("Failed to create chat: %s", e)
        return None

def get_user_chats(user_id: int) -> List[Dict[str, Any]]:
    """Get all chats for a user."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, 
                       (SELECT COUNT(*) FROM messages WHERE chat_id = c.id) as message_count
                FROM chats c
                WHERE c.user_id = ?
                ORDER BY c.created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Failed to get chats: %s", e)
        return []

def get_chat(chat_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific chat."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error("Failed to get chat: %s", e)
        return None

def update_chat_title(chat_id: int, title: str):
    """Update chat title."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE chats SET title = ? WHERE id = ?
            """, (title, chat_id))
            conn.commit()
    except Exception as e:
        logger.error("Failed to update chat title: %s", e)

def delete_chat(chat_id: int):
    """Delete a chat and all its messages."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            conn.commit()
    except Exception as e:
        logger.error("Failed to delete chat: %s", e)

# ===== MESSAGE OPERATIONS =====

def save_message(chat_id: int, sender: str, content: str, analysis_data: Optional[Dict] = None) -> Optional[int]:
    """Save a message to a chat."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            analysis_json = json.dumps(analysis_data) if analysis_data else None
            cursor.execute("""
                INSERT INTO messages (chat_id, sender, content, analysis_data)
                VALUES (?, ?, ?, ?)
            """, (chat_id, sender, content, analysis_json))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error("Failed to save message: %s", e)
        return None

def get_chat_messages(chat_id: int) -> List[Dict[str, Any]]:
    """Get all messages for a chat."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM messages 
                WHERE chat_id = ? 
                ORDER BY created_at ASC
            """, (chat_id,))
            rows = cursor.fetchall()
            messages = []
            for row in rows:
                msg = dict(row)
                if msg['analysis_data']:
                    msg['analysis_data'] = json.loads(msg['analysis_data'])
                messages.append(msg)
            return messages
    except Exception as e:
        logger.error("Failed to get messages: %s", e)
        return []

# ===== LEGACY OPERATIONS (Keep for compatibility) =====

def save_analysis(input_text: str, risk_score: int, verdict: str, model_used: str = "multi-agent") -> int:
    """Save an analysis result to history."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analysis_history (timestamp, input_text, risk_score, verdict, model_used)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now().isoformat(), input_text, risk_score, verdict, model_used))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error("Failed to save analysis: %s", e)
        return -1

def save_uploaded_file(filename: str, file_type: str, stored_path: str) -> int:
    """Save metadata for an uploaded file."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO uploaded_files (filename, file_type, uploaded_at, stored_path)
                VALUES (?, ?, ?, ?)
            """, (filename, file_type, datetime.now().isoformat(), stored_path))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error("Failed to save file metadata: %s", e)
        return -1

def get_recent_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve recent analysis history."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analysis_history ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Failed to get history: %s", e)
        return []

def get_company_report(company_name: str) -> Optional[Dict[str, Any]]:
    """Get a stored company report."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM company_reports WHERE company_name = ?", (company_name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error("Failed to get company report: %s", e)
        return None

def update_company_report(company_name: str, summary: str, risk_level: str):
    """Update or insert a company report."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO company_reports (company_name, summary, risk_level, last_updated)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(company_name) DO UPDATE SET
                    summary=excluded.summary,
                    risk_level=excluded.risk_level,
                    last_updated=excluded.last_updated
            """, (company_name, summary, risk_level, datetime.now().isoformat()))
            conn.commit()
    except Exception as e:
        logger.error("Failed to update company report: %s", e)
