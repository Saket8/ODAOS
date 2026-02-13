# Pydantic Models for Session Management

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import uuid4


class SessionCreate(BaseModel):
    """Request to create a new session."""
    title: Optional[str] = None


class Session(BaseModel):
    """Session with conversation history."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = "New Conversation"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    message_count: int = 0
    preview: Optional[str] = None  # First message preview
    bookmarked: bool = False
    tags: List[str] = []


class SessionList(BaseModel):
    """Paginated list of sessions."""
    sessions: List[Session]
    total: int
    page: int = 1
    per_page: int = 20


class SessionMessage(BaseModel):
    """Message within a session."""
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime
    metadata: Optional[dict] = None


class SessionDetail(BaseModel):
    """Full session with all messages."""
    session: Session
    messages: List[SessionMessage]


class SessionUpdate(BaseModel):
    """Update session properties."""
    title: Optional[str] = None
    bookmarked: Optional[bool] = None
    tags: Optional[List[str]] = None
