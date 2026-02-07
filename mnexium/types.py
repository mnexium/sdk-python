"""
Mnexium SDK Types
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


# ============================================================
# Configuration
# ============================================================


@dataclass
class ProviderConfig:
    """Provider API key configuration."""

    api_key: str


@dataclass
class MnexiumDefaults:
    """Default settings for all process() calls."""

    model: Optional[str] = None
    subject_id: Optional[str] = None
    chat_id: Optional[str] = None
    log: Optional[bool] = None
    learn: Optional[Union[bool, str]] = None  # bool or "force"
    recall: Optional[bool] = None
    profile: Optional[bool] = None
    history: Optional[bool] = None
    summarize: Optional[Union[bool, str]] = None  # bool or "light"/"balanced"/"aggressive"
    system_prompt: Optional[Union[bool, str]] = None  # bool or prompt ID
    metadata: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    regenerate_key: Optional[bool] = None


# ============================================================
# Chat Options
# ============================================================


@dataclass
class ChatOptions:
    """Options for creating a Chat."""

    chat_id: Optional[str] = None
    model: Optional[str] = None
    log: Optional[bool] = None
    learn: Optional[Union[bool, str]] = None
    recall: Optional[bool] = None
    profile: Optional[bool] = None
    history: Optional[bool] = None
    summarize: Optional[Union[bool, str]] = None
    system_prompt: Optional[Union[bool, str]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================================
# Process API (simplified interface)
# ============================================================


@dataclass
class ProcessOptions:
    """Options for the simplified process() API."""

    content: str
    model: Optional[str] = None
    subject_id: Optional[str] = None
    chat_id: Optional[str] = None
    log: Optional[bool] = None
    learn: Optional[Union[bool, str]] = None
    recall: Optional[bool] = None
    profile: Optional[bool] = None
    history: Optional[bool] = None
    summarize: Optional[Union[bool, str]] = None
    system_prompt: Optional[Union[bool, str]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    regenerate_key: Optional[bool] = None


@dataclass
class UsageInfo:
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ProcessResponse:
    """Response from process()."""

    content: str
    chat_id: str
    subject_id: str
    model: str
    usage: Optional[UsageInfo] = None
    provisioned_key: Optional[str] = None
    claim_url: Optional[str] = None
    raw: Optional[Any] = None


@dataclass
class ChatProcessOptions:
    """Options for chat.process() — content plus per-message overrides."""

    content: str
    model: Optional[str] = None
    log: Optional[bool] = None
    learn: Optional[Union[bool, str]] = None
    recall: Optional[bool] = None
    profile: Optional[bool] = None
    history: Optional[bool] = None
    summarize: Optional[Union[bool, str]] = None
    system_prompt: Optional[Union[bool, str]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    regenerate_key: Optional[bool] = None


# ============================================================
# Chat History
# ============================================================


@dataclass
class ChatHistoryListOptions:
    """Options for listing chat history."""

    limit: Optional[int] = None
    offset: Optional[int] = None


@dataclass
class ChatHistoryItem:
    """A chat history item."""

    chat_id: str
    subject_id: str
    created_at: str
    message_count: Optional[int] = None
    last_message_at: Optional[str] = None


# ============================================================
# Chat Completions (advanced / low-level)
# ============================================================


@dataclass
class ChatMessage:
    """A chat message."""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name is not None:
            d["name"] = self.name
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        return d


@dataclass
class MnxOptions:
    """Mnexium-specific options for requests."""

    subject_id: Optional[str] = None
    chat_id: Optional[str] = None
    learn: Optional[Union[bool, str]] = None
    recall: Optional[bool] = None
    history: Optional[bool] = None
    log: Optional[bool] = None
    system_prompt: Optional[Union[bool, str]] = None
    metadata: Optional[Dict[str, Any]] = None
    regenerate_key: Optional[bool] = None


@dataclass
class ChatCompletionOptions:
    """Options for chat completion requests."""

    model: str
    messages: List[ChatMessage] = field(default_factory=list)
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    google_key: Optional[str] = None
    stream: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    # Mnx options
    subject_id: Optional[str] = None
    chat_id: Optional[str] = None
    learn: Optional[Union[bool, str]] = None
    recall: Optional[bool] = None
    history: Optional[bool] = None
    log: Optional[bool] = None
    system_prompt: Optional[Union[bool, str]] = None
    metadata: Optional[Dict[str, Any]] = None
    regenerate_key: Optional[bool] = None


@dataclass
class ChatCompletionChoice:
    """A chat completion choice."""

    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


@dataclass
class ChatCompletionUsage:
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class MnxResponseData:
    """Mnexium response metadata."""

    chat_id: str
    subject_id: str
    provisioned_key: Optional[str] = None
    claim_url: Optional[str] = None


@dataclass
class ChatCompletionResponse:
    """Chat completion response."""

    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    mnx: MnxResponseData
    usage: Optional[ChatCompletionUsage] = None


# ============================================================
# Memories
# ============================================================


@dataclass
class Memory:
    """A memory object."""

    id: str
    project_id: str
    subject_id: str
    text: str
    created_at: str
    source: Optional[str] = None
    visibility: Optional[str] = None  # "private" or "shared"
    metadata: Optional[Dict[str, Any]] = None
    updated_at: Optional[str] = None
    is_deleted: Optional[bool] = None
    superseded_by: Optional[str] = None


@dataclass
class MemoryCreateOptions:
    """Options for creating a memory."""

    subject_id: str
    text: str
    source: Optional[str] = None
    visibility: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MemorySearchOptions:
    """Options for searching memories."""

    subject_id: str
    query: str
    limit: int = 10
    min_score: float = 0.7
    include_deleted: bool = False
    include_superseded: bool = False


@dataclass
class MemorySearchResult:
    """A memory search result."""

    memory: Memory
    score: float


# ============================================================
# Claims
# ============================================================


@dataclass
class Claim:
    """A claim (structured fact) about a subject."""

    id: str
    project_id: str
    subject_id: str
    slot: str
    value: Any
    created_at: str
    confidence: Optional[float] = None
    source: Optional[str] = None
    source_memory_id: Optional[str] = None
    updated_at: Optional[str] = None
    retracted_at: Optional[str] = None


@dataclass
class ClaimCreateOptions:
    """Options for creating a claim."""

    subject_id: str
    slot: str
    value: Any
    confidence: Optional[float] = None
    source: Optional[str] = None
    source_memory_id: Optional[str] = None


# ============================================================
# Profiles
# ============================================================


@dataclass
class Profile:
    """A subject profile."""

    subject_id: str
    project_id: str
    claims: Dict[str, Any]
    memory_count: int
    last_active: Optional[str] = None


# ============================================================
# Agent State
# ============================================================


@dataclass
class AgentState:
    """Agent state object."""

    key: str
    value: Any
    created_at: str
    subject_id: Optional[str] = None
    ttl_seconds: Optional[int] = None
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None


@dataclass
class AgentStateSetOptions:
    """Options for setting agent state."""

    key: str
    value: Any
    subject_id: Optional[str] = None
    ttl_seconds: Optional[int] = None


# ============================================================
# System Prompts
# ============================================================


@dataclass
class SystemPrompt:
    """A system prompt."""

    id: str
    project_id: str
    name: str
    prompt_text: str
    created_at: str
    is_default: Optional[bool] = None
    updated_at: Optional[str] = None


@dataclass
class SystemPromptCreateOptions:
    """Options for creating a system prompt."""

    name: str
    prompt_text: str
    is_default: bool = False


# ============================================================
# Stream types
# ============================================================


@dataclass
class StreamChunk:
    """An incremental streaming chunk."""

    content: str
    raw: Optional[Any] = None


@dataclass
class MemoryEvent:
    """A real-time memory event."""

    type: str  # "connected", "memory.created", "memory.updated", etc.
    data: Dict[str, Any] = field(default_factory=dict)
