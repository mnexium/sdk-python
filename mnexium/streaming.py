"""
Streaming support for Mnexium SDK

Provides an iterator that yields text chunks from SSE streams,
with access to final metadata after iteration completes.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterator, Optional

from .types import StreamChunk, UsageInfo


class StreamResponse:
    """
    StreamResponse is an iterator that yields text chunks from an SSE stream.

    After iteration completes, metadata like usage, chat_id, etc. are available.

    Example::

        stream = chat.process(ChatProcessOptions(content="Hello", stream=True))
        for chunk in stream:
            print(chunk.content, end="", flush=True)
        print()
        print("Total:", stream.total_content)
        print("Usage:", stream.usage)
    """

    def __init__(
        self,
        response: Any,  # httpx.Response (streaming)
        *,
        chat_id: str = "",
        subject_id: str = "",
        model: str = "",
        provisioned_key: Optional[str] = None,
        claim_url: Optional[str] = None,
    ) -> None:
        self._response = response
        self.chat_id = chat_id
        self.subject_id = subject_id
        self.model = model
        self.provisioned_key = provisioned_key
        self.claim_url = claim_url

        self.total_content: str = ""
        self.usage: Optional[UsageInfo] = None
        self._consumed: bool = False

    def __iter__(self) -> Iterator[StreamChunk]:
        if self._consumed:
            raise RuntimeError("StreamResponse has already been consumed")
        self._consumed = True

        buffer = ""
        try:
            for raw_bytes in self._response.iter_bytes():
                buffer += raw_bytes.decode("utf-8", errors="replace")
                lines = buffer.split("\n")
                buffer = lines.pop()

                for line in lines:
                    trimmed = line.strip()

                    # Skip SSE event type lines and empty lines
                    if trimmed.startswith("event:") or not trimmed.startswith("data:"):
                        continue

                    data = trimmed[5:].strip()
                    if not data or data == "[DONE]":
                        continue

                    try:
                        parsed = json.loads(data)
                        chunk = self._extract_chunk(parsed)
                        if chunk is not None:
                            self.total_content += chunk.content
                            yield chunk
                        self._extract_usage(parsed)
                    except (json.JSONDecodeError, ValueError):
                        pass
        finally:
            self._response.close()

    def text(self) -> str:
        """
        Convenience: collect the full response as a string.
        Consumes the stream if not already consumed.
        """
        if not self._consumed:
            for _ in self:
                pass
        return self.total_content

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_chunk(data: Dict[str, Any]) -> Optional[StreamChunk]:
        # OpenAI format: choices[0].delta.content
        choices = data.get("choices")
        if choices and isinstance(choices, list):
            delta = choices[0].get("delta") or {}
            content = delta.get("content")
            if content:
                return StreamChunk(content=content, raw=data)

        # Anthropic format: content_block_delta with text_delta
        if data.get("type") == "content_block_delta":
            delta = data.get("delta") or {}
            if delta.get("type") == "text_delta":
                return StreamChunk(content=delta.get("text", ""), raw=data)

        # Google Gemini format: candidates[0].content.parts[0].text
        candidates = data.get("candidates")
        if isinstance(candidates, list) and candidates:
            parts = (candidates[0].get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
            if text:
                return StreamChunk(content=text, raw=data)

        return None

    def _extract_usage(self, data: Dict[str, Any]) -> None:
        # OpenAI: usage in final chunk
        if data.get("usage") and isinstance(data["usage"], dict):
            u = data["usage"]
            self.usage = UsageInfo(
                prompt_tokens=u.get("prompt_tokens", 0),
                completion_tokens=u.get("completion_tokens", 0),
                total_tokens=u.get("total_tokens", 0),
            )

        # Anthropic: message_delta with usage
        if data.get("type") == "message_delta" and data.get("usage"):
            u = data["usage"]
            inp = u.get("input_tokens", 0)
            out = u.get("output_tokens", 0)
            self.usage = UsageInfo(
                prompt_tokens=inp,
                completion_tokens=out,
                total_tokens=inp + out,
            )

        # Google: usageMetadata
        um = data.get("usageMetadata")
        if um and isinstance(um, dict):
            self.usage = UsageInfo(
                prompt_tokens=um.get("promptTokenCount", 0),
                completion_tokens=um.get("candidatesTokenCount", 0),
                total_tokens=um.get("totalTokenCount", 0),
            )
