# Pydantic Models for Prompt Library

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from uuid import uuid4


# ============================================================================
# Core Prompt Models
# ============================================================================

class PromptParameter(BaseModel):
    """Definition of a single prompt parameter."""
    name: str
    type: Literal["string", "integer", "float", "date", "enum"] = "string"
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None
    enum_values: Optional[List[str]] = None  # For dropdown options


class Prompt(BaseModel):
    """Full prompt representation with all details."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    category: str
    title: str
    description: str
    prompt_template: str
    parameters: List[PromptParameter] = []
    default_values: Dict[str, Any] = {}
    expected_output: Optional[str] = None
    tags: List[str] = []
    difficulty_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    estimated_runtime: str = "< 30s"
    requires_approval: bool = False
    is_active: bool = True
    usage_count: int = 0
    average_runtime: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PromptSummary(BaseModel):
    """Lightweight prompt for list views — fewer fields than full Prompt."""
    id: str
    category: str
    title: str
    description: str
    tags: List[str] = []
    difficulty_level: str = "beginner"
    estimated_runtime: str = "< 30s"
    requires_approval: bool = False
    usage_count: int = 0
    is_favorited: bool = False


# ============================================================================
# Category Models
# ============================================================================

class PromptCategory(BaseModel):
    """Prompt category with metadata and count."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    display_name: str
    description: Optional[str] = None
    icon: str = "📁"
    sort_order: int = 0
    parent_category_id: Optional[str] = None
    prompt_count: int = 0


# ============================================================================
# Execution Models
# ============================================================================

class PromptExecuteRequest(BaseModel):
    """Request body for executing a prompt with parameters."""
    parameters: Dict[str, Any] = {}
    session_id: Optional[str] = None
    custom_query: Optional[str] = None  # User-edited query that overrides the template


class PromptExecuteResponse(BaseModel):
    """Response after prompt execution completes."""
    execution_id: str
    prompt_id: str
    status: Literal["success", "error", "timeout"] = "success"
    execution_time_ms: int = 0
    result_summary: Optional[str] = None
    session_id: Optional[str] = None


# ============================================================================
# Favorites & History Models
# ============================================================================

class PromptFavorite(BaseModel):
    """A user's favorited prompt."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    prompt_id: str
    added_at: datetime = Field(default_factory=datetime.now)
    # Embedded prompt summary for convenience
    prompt: Optional[PromptSummary] = None


class PromptHistoryEntry(BaseModel):
    """Record of a prompt execution."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    prompt_id: str
    prompt_title: Optional[str] = None
    parameters_used: Dict[str, Any] = {}
    executed_at: datetime = Field(default_factory=datetime.now)
    execution_time_ms: int = 0
    status: Literal["success", "error", "timeout", "running"] = "running"
    result_summary: Optional[str] = None


# ============================================================================
# Request/Response Models for API
# ============================================================================

class PromptCreate(BaseModel):
    """Admin request to create a new prompt."""
    category: str
    title: str
    description: str
    prompt_template: str
    parameters: List[PromptParameter] = []
    default_values: Dict[str, Any] = {}
    expected_output: Optional[str] = None
    tags: List[str] = []
    difficulty_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    estimated_runtime: str = "< 30s"
    requires_approval: bool = False


class PromptUpdate(BaseModel):
    """Admin request to update an existing prompt."""
    category: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    prompt_template: Optional[str] = None
    parameters: Optional[List[PromptParameter]] = None
    default_values: Optional[Dict[str, Any]] = None
    expected_output: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    estimated_runtime: Optional[str] = None
    requires_approval: Optional[bool] = None
    is_active: Optional[bool] = None


class PromptListResponse(BaseModel):
    """Paginated list of prompts."""
    prompts: List[PromptSummary]
    total: int
    page: int = 1
    per_page: int = 20


class FavoriteToggleResponse(BaseModel):
    """Response from toggling a favorite."""
    prompt_id: str
    favorited: bool


class PromptHistoryResponse(BaseModel):
    """Paginated execution history."""
    history: List[PromptHistoryEntry]
    total: int
    limit: int = 20
    offset: int = 0
