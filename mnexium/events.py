"""
Real-time event stream for memory notifications via SSE

Connects to GET /api/v1/events/memories and yields typed events.

Events:
  - connected: Initial connection confirmation
  - memory.created: New memory created
  - memory.updated: Memory updated
  - memory.deleted: Memory deleted
  - memory.superseded: Memory superseded
  - profile.updated: Profile updated
  - heartbeat: Keepalive (every 30s)
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Iterator

from .types import MemoryEvent

if TYPE_CHECKING:
    from .client import Mnexium


class EventStream:
    """
    EventStream is an iterator that yields real-time memory events.

    Example::

        events = user.memories.subscribe()
        for event in events:
            if event.type == "memory.created":
                print("New memory:", event.data)
        # To stop listening:
        events.close()
    """

    def __init__(
        self,
        client: Mnexium,
        subject_id: str,
    ) -> None:
        self._client = client
        self._subject_id = subject_id
        self._response: Any = None  # httpx.Response
        self._closed: bool = False
        self._connected: bool = False

    def __iter__(self) -> Iterator[MemoryEvent]:
        self._response = self._client._request_raw(
            "GET",
            "/events/memories",
            params={"subject_id": self._subject_id},
        )
        self._connected = True

        buffer = ""
        current_event = ""

        try:
            for raw_bytes in self._response.iter_bytes():
                if self._closed:
                    break

                buffer += raw_bytes.decode("utf-8", errors="replace")
                lines = buffer.split("\n")
                buffer = lines.pop()

                for line in lines:
                    trimmed = line.strip()

                    if trimmed.startswith("event:"):
                        current_event = trimmed[6:].strip()
                        continue

                    if trimmed.startswith("data:"):
                        data = trimmed[5:].strip()
                        if not data:
                            continue
                        try:
                            parsed = json.loads(data)
                            event_type = current_event or "unknown"
                            current_event = ""
                            yield MemoryEvent(type=event_type, data=parsed)
                        except (json.JSONDecodeError, ValueError):
                            pass

                    # Empty line resets event type
                    if trimmed == "":
                        current_event = ""
        finally:
            self._connected = False
            if self._response is not None:
                self._response.close()

    def close(self) -> None:
        """Close the event stream."""
        self._closed = True
        self._connected = False
        if self._response is not None:
            try:
                self._response.close()
            except Exception:
                pass

    @property
    def is_connected(self) -> bool:
        """Whether the stream is currently connected."""
        return self._connected
