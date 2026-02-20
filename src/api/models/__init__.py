# API Models Package

from src.api.models.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    StreamEvent,
    QuickReply,
    InsightCard
)
from src.api.models.viz import (
    VizRequest,
    VizResponse,
    ChartData,
    SmartNarrative
)
from src.api.models.session import (
    Session,
    SessionCreate,
    SessionList
)
from src.api.models.prompt import (
    Prompt,
    PromptSummary,
    PromptCategory,
    PromptParameter,
    PromptExecuteRequest,
    PromptExecuteResponse,
    PromptFavorite,
    PromptHistoryEntry,
    PromptCreate,
    PromptUpdate,
    PromptListResponse,
    FavoriteToggleResponse,
    PromptHistoryResponse
)

__all__ = [
    "ChatMessage", "ChatRequest", "ChatResponse", "StreamEvent",
    "QuickReply", "InsightCard",
    "VizRequest", "VizResponse", "ChartData", "SmartNarrative",
    "Session", "SessionCreate", "SessionList",
    "Prompt", "PromptSummary", "PromptCategory", "PromptParameter",
    "PromptExecuteRequest", "PromptExecuteResponse",
    "PromptFavorite", "PromptHistoryEntry",
    "PromptCreate", "PromptUpdate", "PromptListResponse",
    "FavoriteToggleResponse", "PromptHistoryResponse",
]

