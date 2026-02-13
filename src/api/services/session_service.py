# Session Service - Conversation History Management

import sqlite3
from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from pathlib import Path

from src.api.models.session import (
    Session, SessionCreate, SessionList, SessionDetail,
    SessionUpdate, SessionMessage
)


class SessionService:
    """Service for managing conversation sessions with SQLite storage."""
    
    def __init__(self, db_path: str = "data/sessions.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    bookmarked INTEGER DEFAULT 0,
                    tags TEXT DEFAULT '[]'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session 
                ON messages(session_id)
            """)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts 
                USING fts5(content, session_id)
            """)
            conn.commit()
    
    async def create_session(self, title: Optional[str] = None) -> Session:
        """Create a new conversation session."""
        session_id = str(uuid4())
        now = datetime.now()
        title = title or "New Conversation"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, title, now, now)
            )
            conn.commit()
        
        return Session(
            id=session_id,
            title=title,
            created_at=now,
            updated_at=now,
            message_count=0
        )
    
    async def list_sessions(
        self,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        bookmarked_only: bool = False
    ) -> SessionList:
        """List sessions with pagination and search."""
        offset = (page - 1) * per_page
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Build query
            where_clauses = []
            params = []
            
            if bookmarked_only:
                where_clauses.append("s.bookmarked = 1")
            
            if search:
                where_clauses.append("""
                    s.id IN (
                        SELECT session_id FROM messages_fts 
                        WHERE content MATCH ?
                    )
                """)
                params.append(search)
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Get total count
            count_result = conn.execute(
                f"SELECT COUNT(*) FROM sessions s WHERE {where_sql}",
                params
            ).fetchone()
            total = count_result[0]
            
            # Get sessions with message count
            query = f"""
                SELECT s.*, 
                       (SELECT COUNT(*) FROM messages WHERE session_id = s.id) as message_count,
                       (SELECT content FROM messages WHERE session_id = s.id ORDER BY created_at LIMIT 1) as preview
                FROM sessions s
                WHERE {where_sql}
                ORDER BY s.updated_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([per_page, offset])
            
            rows = conn.execute(query, params).fetchall()
            
            sessions = [
                Session(
                    id=row["id"],
                    title=row["title"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    message_count=row["message_count"],
                    preview=row["preview"][:100] if row["preview"] else None,
                    bookmarked=bool(row["bookmarked"]),
                    tags=eval(row["tags"]) if row["tags"] else []
                )
                for row in rows
            ]
        
        return SessionList(
            sessions=sessions,
            total=total,
            page=page,
            per_page=per_page
        )
    
    async def get_session_with_messages(self, session_id: str) -> Optional[SessionDetail]:
        """Get a session with all its messages."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get session
            session_row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,)
            ).fetchone()
            
            if not session_row:
                return None
            
            # Get messages
            message_rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at",
                (session_id,)
            ).fetchall()
            
            session = Session(
                id=session_row["id"],
                title=session_row["title"],
                created_at=datetime.fromisoformat(session_row["created_at"]),
                updated_at=datetime.fromisoformat(session_row["updated_at"]),
                message_count=len(message_rows),
                bookmarked=bool(session_row["bookmarked"]),
                tags=eval(session_row["tags"]) if session_row["tags"] else []
            )
            
            messages = [
                SessionMessage(
                    id=row["id"],
                    session_id=row["session_id"],
                    role=row["role"],
                    content=row["content"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    metadata=eval(row["metadata"]) if row["metadata"] else None
                )
                for row in message_rows
            ]
        
        return SessionDetail(session=session, messages=messages)
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> SessionMessage:
        """Add a message to a session."""
        message_id = str(uuid4())
        now = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            # Ensure session exists
            existing = conn.execute(
                "SELECT id FROM sessions WHERE id = ?",
                (session_id,)
            ).fetchone()
            
            if not existing:
                # Auto-create session
                conn.execute(
                    "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (session_id, "New Conversation", now, now)
                )
            
            # Add message
            conn.execute(
                "INSERT INTO messages (id, session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (message_id, session_id, role, content, str(metadata) if metadata else None, now)
            )
            
            # Update session timestamp
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id)
            )
            
            # Add to FTS index
            conn.execute(
                "INSERT INTO messages_fts (content, session_id) VALUES (?, ?)",
                (content, session_id)
            )
            
            # Auto-update title from first user message
            if role == "user":
                conn.execute("""
                    UPDATE sessions 
                    SET title = COALESCE(
                        (SELECT SUBSTR(content, 1, 50) FROM messages 
                         WHERE session_id = ? AND role = 'user' 
                         ORDER BY created_at LIMIT 1),
                        title
                    )
                    WHERE id = ? AND title = 'New Conversation'
                """, (session_id, session_id))
            
            conn.commit()
        
        return SessionMessage(
            id=message_id,
            session_id=session_id,
            role=role,
            content=content,
            created_at=now,
            metadata=metadata
        )
    
    async def update_session(
        self,
        session_id: str,
        update: SessionUpdate
    ) -> Optional[Session]:
        """Update session properties."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            updates = []
            params = []
            
            if update.title is not None:
                updates.append("title = ?")
                params.append(update.title)
            
            if update.bookmarked is not None:
                updates.append("bookmarked = ?")
                params.append(1 if update.bookmarked else 0)
            
            if update.tags is not None:
                updates.append("tags = ?")
                params.append(str(update.tags))
            
            if not updates:
                return await self._get_session(conn, session_id)
            
            updates.append("updated_at = ?")
            params.append(datetime.now())
            params.append(session_id)
            
            conn.execute(
                f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
            
            return await self._get_session(conn, session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "DELETE FROM sessions WHERE id = ?",
                (session_id,)
            )
            conn.commit()
            return result.rowcount > 0
    
    async def toggle_bookmark(self, session_id: str) -> Optional[Session]:
        """Toggle bookmark status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            conn.execute(
                "UPDATE sessions SET bookmarked = NOT bookmarked, updated_at = ? WHERE id = ?",
                (datetime.now(), session_id)
            )
            conn.commit()
            
            return await self._get_session(conn, session_id)
    
    async def resume_session(self, session_id: str) -> Optional[SessionDetail]:
        """Resume a session - same as get_session_with_messages."""
        return await self.get_session_with_messages(session_id)
    
    async def get_context_summary(self, session_id: str) -> str:
        """Get a summary of session context for resuming."""
        detail = await self.get_session_with_messages(session_id)
        if not detail or not detail.messages:
            return "No previous context."
        
        # Summarize last few exchanges
        recent = detail.messages[-6:]
        summary = f"Previous conversation about: {detail.session.title}\n"
        summary += f"Last {len(recent)} messages exchanged."
        return summary
    
    async def export_as_markdown(self, session: SessionDetail) -> str:
        """Export session as markdown."""
        md = f"# {session.session.title}\n\n"
        md += f"*Created: {session.session.created_at}*\n\n---\n\n"
        
        for msg in session.messages:
            role = "**You**" if msg.role == "user" else "**ODAOS**"
            md += f"{role}: {msg.content}\n\n"
        
        return md
    
    async def _get_session(self, conn, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,)
        ).fetchone()
        
        if not row:
            return None
        
        msg_count = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = ?",
            (session_id,)
        ).fetchone()[0]
        
        return Session(
            id=row["id"],
            title=row["title"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            message_count=msg_count,
            bookmarked=bool(row["bookmarked"]),
            tags=eval(row["tags"]) if row["tags"] else []
        )
