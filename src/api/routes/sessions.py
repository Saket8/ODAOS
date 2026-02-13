# Session Management API Routes

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from uuid import uuid4

from src.api.models.session import (
    Session, SessionCreate, SessionList, SessionDetail, SessionUpdate
)
from src.api.services.session_service import SessionService


router = APIRouter()
session_service = SessionService()


@router.get("/", response_model=SessionList)
async def list_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    bookmarked_only: bool = False
):
    """
    List all conversation sessions.
    
    - Paginated for performance
    - Searchable by content
    - Filter by bookmarked status
    """
    sessions = await session_service.list_sessions(
        page=page,
        per_page=per_page,
        search=search,
        bookmarked_only=bookmarked_only
    )
    return sessions


@router.post("/", response_model=Session)
async def create_session(request: SessionCreate):
    """Create a new conversation session."""
    session = await session_service.create_session(
        title=request.title
    )
    return session


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str):
    """Get a session with all its messages."""
    session = await session_service.get_session_with_messages(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}", response_model=Session)
async def update_session(session_id: str, update: SessionUpdate):
    """Update session properties (title, bookmarked, tags)."""
    session = await session_service.update_session(session_id, update)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its messages."""
    success = await session_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}


@router.post("/{session_id}/bookmark")
async def toggle_bookmark(session_id: str):
    """Toggle bookmark status for a session."""
    session = await session_service.toggle_bookmark(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"bookmarked": session.bookmarked}


@router.get("/{session_id}/export")
async def export_session(
    session_id: str,
    format: str = Query("json", regex="^(json|pdf|markdown)$")
):
    """Export session in specified format."""
    session = await session_service.get_session_with_messages(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if format == "json":
        return session
    elif format == "markdown":
        md = await session_service.export_as_markdown(session)
        return {"content": md, "format": "markdown"}
    elif format == "pdf":
        # PDF generation would require additional library
        return {"status": "pdf_export_not_implemented_yet"}


@router.post("/{session_id}/resume")
async def resume_session(session_id: str):
    """
    Resume a previous session.
    Returns session context for continuing the conversation.
    """
    session = await session_service.resume_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session": session.session,
        "context_summary": await session_service.get_context_summary(session_id),
        "last_messages": session.messages[-5:] if len(session.messages) > 5 else session.messages
    }
