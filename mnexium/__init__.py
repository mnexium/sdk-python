"""
Mnexium SDK for Python
Add memory to your AI applications
"""

from .client import Mnexium
from .chat import Chat
from .subject import Subject
from .streaming import StreamResponse
from .events import EventStream
from .errors import (
    MnexiumError,
    AuthenticationError,
    RateLimitError,
    APIError,
    NotFoundError,
    ValidationError,
)
from .types import (
    # Configuration
    ProviderConfig,
    MnexiumDefaults,
    # Chat API
    ChatOptions,
    ChatProcessOptions,
    # Chat History
    ChatHistoryListOptions,
    ChatHistoryItem,
    # Process API
    ProcessOptions,
    ProcessResponse,
    UsageInfo,
    # Chat Completions (advanced)
    ChatMessage,
    MnxOptions,
    MnxRecordsConfig,
    ChatCompletionOptions,
    ChatCompletionResponse,
    # Resources
    Memory,
    MemoryCreateOptions,
    MemorySearchOptions,
    MemorySearchResult,
    Claim,
    ClaimCreateOptions,
    Profile,
    AgentState,
    AgentStateSetOptions,
    SystemPrompt,
    SystemPromptCreateOptions,
    # Records
    RecordFieldDef,
    RecordSchema,
    RecordSchemaDefineOptions,
    MnxRecord,
    RecordInsertOptions,
    RecordQueryOptions,
    RecordSearchResult,
    # Stream types
    StreamChunk,
    MemoryEvent,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "Mnexium",
    "Chat",
    "Subject",
    "StreamResponse",
    "EventStream",
    # Errors
    "MnexiumError",
    "AuthenticationError",
    "RateLimitError",
    "APIError",
    "NotFoundError",
    "ValidationError",
    # Configuration
    "ProviderConfig",
    "MnexiumDefaults",
    # Chat API
    "ChatOptions",
    "ChatProcessOptions",
    # Chat History
    "ChatHistoryListOptions",
    "ChatHistoryItem",
    # Process API
    "ProcessOptions",
    "ProcessResponse",
    "UsageInfo",
    # Chat Completions (advanced)
    "ChatMessage",
    "MnxOptions",
    "MnxRecordsConfig",
    "ChatCompletionOptions",
    "ChatCompletionResponse",
    # Resources
    "Memory",
    "MemoryCreateOptions",
    "MemorySearchOptions",
    "MemorySearchResult",
    "Claim",
    "ClaimCreateOptions",
    "Profile",
    "AgentState",
    "AgentStateSetOptions",
    "SystemPrompt",
    "SystemPromptCreateOptions",
    # Records
    "RecordFieldDef",
    "RecordSchema",
    "RecordSchemaDefineOptions",
    "MnxRecord",
    "RecordInsertOptions",
    "RecordQueryOptions",
    "RecordSearchResult",
    # Stream types
    "StreamChunk",
    "MemoryEvent",
]
