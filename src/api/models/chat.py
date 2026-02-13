# Pydantic Models for Chat API

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from uuid import uuid4


class ChatMessage(BaseModel):
    """A single message in a conversation."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["user", "assistant"] = "user"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[dict] = None


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    include_viz: bool = True
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """Response from chat endpoint (non-streaming)."""
    message_id: str
    content: str
    session_id: str
    suggestions: List[str] = []
    chart_data: Optional[dict] = None


class StreamEvent(BaseModel):
    """Event sent via SSE stream."""
    type: Literal["token", "chart", "suggestions", "insight", "done", "error"]
    content: Optional[str] = None
    data: Optional[dict] = None


class QuickReply(BaseModel):
    """Quick reply suggestion button."""
    text: str
    query: str
    category: Optional[str] = None


class InsightCard(BaseModel):
    """AI-generated proactive insight."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    severity: Literal["info", "warning", "critical"] = "info"
    action: Optional[str] = None
    related_query: Optional[str] = None
