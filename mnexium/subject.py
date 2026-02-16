"""
Subject - A logical identity (user, agent, org, device) that owns memory, profile, and state
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from .types import (
    ChatHistoryItem,
    ChatHistoryListOptions,
    ChatOptions,
    ProcessOptions,
    ProcessResponse,
)
from .events import EventStream

if TYPE_CHECKING:
    from .client import Mnexium
    from .chat import Chat
    from .streaming import StreamResponse


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


# ------------------------------------------------------------------
# Subject-scoped memories resource
# ------------------------------------------------------------------


class SubjectMemoriesResource:
    """Subject-scoped memories resource."""

    def __init__(self, client: Mnexium, subject_id: str) -> None:
        self._client = client
        self._subject_id = subject_id

    def search(
        self,
        query: str,
        *,
        limit: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> List[Any]:
        """Semantic search over memories."""
        response = self._client._request(
            "GET",
            "/memories/search",
            params={
                "subject_id": self._subject_id,
                "q": query,
                "limit": limit,
                "min_score": min_score,
            },
        )
        return _as_list(_as_dict(response).get("data"))

    def add(
        self,
        text: str,
        *,
        source: Optional[str] = None,
        visibility: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        no_supersede: Optional[bool] = None,
    ) -> Any:
        """Add a memory."""
        body: Dict[str, Any] = {
            "subject_id": self._subject_id,
            "text": text,
            "source": source,
            "visibility": visibility,
            "metadata": metadata,
        }
        if no_supersede is not None:
            body["no_supersede"] = no_supersede
        return self._client._request(
            "POST",
            "/memories",
            json=body,
        )

    def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Any]:
        """List memories."""
        response = self._client._request(
            "GET",
            "/memories",
            params={
                "subject_id": self._subject_id,
                "limit": limit,
                "offset": offset,
            },
        )
        return _as_list(_as_dict(response).get("data"))

    def get(self, memory_id: str) -> Any:
        """Get a specific memory."""
        return self._client._request("GET", f"/memories/{memory_id}")

    def update(
        self,
        memory_id: str,
        *,
        text: Optional[str] = None,
        visibility: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Update a memory."""
        body: Dict[str, Any] = {}
        if text is not None:
            body["text"] = text
        if visibility is not None:
            body["visibility"] = visibility
        if metadata is not None:
            body["metadata"] = metadata
        return self._client._request("PATCH", f"/memories/{memory_id}", json=body)

    def delete(self, memory_id: str) -> None:
        """Delete a memory."""
        self._client._request("DELETE", f"/memories/{memory_id}")

    def superseded(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Any]:
        """List superseded memories."""
        response = self._client._request(
            "GET",
            "/memories/superseded",
            params={
                "subject_id": self._subject_id,
                "limit": limit,
                "offset": offset,
            },
        )
        return _as_list(_as_dict(response).get("data"))

    def restore(self, memory_id: str) -> Any:
        """Restore a superseded memory."""
        return self._client._request("POST", f"/memories/{memory_id}/restore")

    def recalls(
        self,
        *,
        chat_id: Optional[str] = None,
        memory_id: Optional[str] = None,
    ) -> List[Any]:
        """Query recall events."""
        response = self._client._request(
            "GET",
            "/memories/recalls",
            params={
                "chat_id": chat_id,
                "memory_id": memory_id,
            },
        )
        return _as_list(_as_dict(response).get("data"))

    def subscribe(self) -> EventStream:
        """Subscribe to real-time memory events via SSE."""
        return EventStream(self._client, self._subject_id)


# ------------------------------------------------------------------
# Subject-scoped profile resource
# ------------------------------------------------------------------


class SubjectProfileResource:
    """Subject-scoped profile resource."""

    def __init__(self, client: Mnexium, subject_id: str) -> None:
        self._client = client
        self._subject_id = subject_id

    def get(self) -> Any:
        """Get profile."""
        return self._client._request(
            "GET",
            "/profiles",
            params={"subject_id": self._subject_id},
        )

    def update(self, updates: List[Dict[str, Any]]) -> Any:
        """
        Update profile fields.

        Args:
            updates: List of dicts with ``field_key`` and ``value``.
        """
        return self._client._request(
            "PATCH",
            "/profiles",
            json={
                "subject_id": self._subject_id,
                "updates": updates,
            },
        )

    def delete_field(self, field_key: str) -> None:
        """Delete a profile field."""
        self._client._request(
            "DELETE",
            "/profiles",
            json={
                "subject_id": self._subject_id,
                "field_key": field_key,
            },
        )


# ------------------------------------------------------------------
# Subject-scoped state resource
# ------------------------------------------------------------------


class SubjectStateResource:
    """Subject-scoped state resource."""

    def __init__(self, client: Mnexium, subject_id: str) -> None:
        self._client = client
        self._subject_id = subject_id

    def get(self, key: str) -> Optional[Any]:
        """Get state by key. Returns None if not found."""
        from .errors import NotFoundError

        try:
            return self._client._request(
                "GET",
                f"/state/{key}",
                headers={"x-subject-id": self._subject_id},
            )
        except NotFoundError:
            return None

    def set(
        self,
        key: str,
        value: Any,
        *,
        ttl_seconds: Optional[int] = None,
    ) -> Any:
        """Set state."""
        return self._client._request(
            "PUT",
            f"/state/{key}",
            headers={"x-subject-id": self._subject_id},
            json={
                "value": value,
                "ttl_seconds": ttl_seconds,
            },
        )

    def delete(self, key: str) -> None:
        """Delete state."""
        self._client._request(
            "DELETE",
            f"/state/{key}",
            headers={"x-subject-id": self._subject_id},
        )


# ------------------------------------------------------------------
# Subject-scoped claims resource
# ------------------------------------------------------------------


class SubjectClaimsResource:
    """Subject-scoped claims resource."""

    def __init__(self, client: Mnexium, subject_id: str) -> None:
        self._client = client
        self._subject_id = subject_id

    def get(self, slot: str) -> Optional[Any]:
        """Get a claim by slot. Returns None if not found."""
        from .errors import NotFoundError

        try:
            return self._client._request(
                "GET",
                f"/claims/subject/{self._subject_id}/slot/{slot}",
            )
        except NotFoundError:
            return None

    def set(
        self,
        predicate: str,
        value: Any,
        *,
        confidence: Optional[float] = None,
        source: Optional[str] = None,
    ) -> Any:
        """Set a claim."""
        return self._client._request(
            "POST",
            "/claims",
            json={
                "subject_id": self._subject_id,
                "predicate": predicate,
                "object_value": value,
                "confidence": confidence,
                "source_type": source,
            },
        )

    def list(self) -> Dict[str, Any]:
        """List all claim slots."""
        return _as_dict(self._client._request(
            "GET",
            f"/claims/subject/{self._subject_id}/slots",
        ))

    def truth(self) -> Any:
        """Get current truth (all active values)."""
        return self._client._request(
            "GET",
            f"/claims/subject/{self._subject_id}/truth",
        )

    def history(self) -> List[Any]:
        """Get claim history."""
        response = self._client._request(
            "GET",
            f"/claims/subject/{self._subject_id}/history",
        )
        data = _as_dict(response)
        return _as_list(data.get("data")) or _as_list(data.get("claims"))

    def retract(self, claim_id: str) -> Any:
        """Retract a claim."""
        return self._client._request("POST", f"/claims/{claim_id}/retract")


# ------------------------------------------------------------------
# Subject-scoped chats resource
# ------------------------------------------------------------------


class SubjectChatsResource:
    """Subject-scoped chats resource (for listing chat history)."""

    def __init__(self, client: Mnexium, subject_id: str) -> None:
        self._client = client
        self._subject_id = subject_id

    def list(self, options: Optional[ChatHistoryListOptions] = None) -> List[ChatHistoryItem]:
        """List recent chats."""
        opts = options or ChatHistoryListOptions()
        response = self._client._request(
            "GET",
            "/chat/history/list",
            params={
                "subject_id": self._subject_id,
                "limit": opts.limit,
                "offset": opts.offset,
            },
        )
        chats = _as_list(_as_dict(response).get("chats"))
        return [
            ChatHistoryItem(
                chat_id=c.get("chat_id", ""),
                subject_id=c.get("subject_id", ""),
                created_at=c.get("created_at", ""),
                message_count=c.get("message_count"),
                last_message_at=c.get("last_message_at"),
            )
            for c in chats
        ]

    def read(self, chat_id: str) -> List[Any]:
        """Read messages from a specific chat."""
        response = self._client._request(
            "GET",
            "/chat/history/read",
            params={
                "subject_id": self._subject_id,
                "chat_id": chat_id,
            },
        )
        return _as_list(_as_dict(response).get("data"))

    def delete(self, chat_id: str) -> None:
        """Delete a chat."""
        self._client._request(
            "DELETE",
            "/chat/history/delete",
            params={
                "subject_id": self._subject_id,
                "chat_id": chat_id,
            },
        )


# ------------------------------------------------------------------
# Subject
# ------------------------------------------------------------------


class Subject:
    """
    Subject represents a logical identity (user, agent, org, device).

    Creating a Subject does NOT make a network call — it's a lightweight scoped handle.

    Example::

        alice = mnx.subject("user_123")
        response = alice.process("Hello!")
        results = alice.memories.search("hobbies")
    """

    def __init__(self, client: Mnexium, subject_id: str) -> None:
        self.id = subject_id
        self._client = client

        self.memories = SubjectMemoriesResource(client, subject_id)
        self.profile = SubjectProfileResource(client, subject_id)
        self.state = SubjectStateResource(client, subject_id)
        self.claims = SubjectClaimsResource(client, subject_id)
        self.chats = SubjectChatsResource(client, subject_id)

    def process(
        self, input: Union[str, ProcessOptions]
    ) -> Union[ProcessResponse, StreamResponse]:
        """
        Process a message with an ephemeral chat (no persistent chat_id).

        Example::

            response = alice.process("What's my favorite color?")
        """
        if isinstance(input, str):
            opts = ProcessOptions(content=input)
        else:
            opts = input
        opts.subject_id = self.id
        return self._client.process(opts)

    def create_chat(self, options: Optional[ChatOptions] = None) -> Chat:
        """
        Create a chat session for multi-turn conversation.

        Example::

            chat = alice.create_chat(ChatOptions(history=True))
            chat.process("Hello!")
            chat.process("What did I just say?")
        """
        return self._client.create_chat(self, options)
