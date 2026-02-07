"""
Provider detection and response normalization
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def detect_provider(model: str) -> Optional[str]:
    """Detect provider from model name."""
    lower = model.lower()

    if "claude" in lower:
        return "anthropic"
    if "gemini" in lower or "palm" in lower:
        return "google"
    if "gpt" in lower or "o1" in lower or "o3" in lower or "davinci" in lower:
        return "openai"

    return None


def extract_response_content(raw: Dict[str, Any]) -> Tuple[str, Optional[Dict[str, int]]]:
    """
    Extract content and usage from provider-specific response format.

    Returns (content, usage_dict_or_None).
    """
    # Anthropic format: content is array of blocks
    if "content" in raw and isinstance(raw.get("content"), list):
        content = ""
        for block in raw["content"]:
            if isinstance(block, dict) and block.get("type") == "text":
                content += block.get("text", "")
        usage = None
        if raw.get("usage"):
            u = raw["usage"]
            input_t = u.get("input_tokens", 0)
            output_t = u.get("output_tokens", 0)
            usage = {
                "prompt_tokens": input_t,
                "completion_tokens": output_t,
                "total_tokens": input_t + output_t,
            }
        return content, usage

    # Google/Gemini format: candidates[0].content.parts
    candidates = raw.get("candidates")
    if isinstance(candidates, list) and len(candidates) > 0:
        content = ""
        parts = (candidates[0].get("content") or {}).get("parts") or []
        for part in parts:
            if isinstance(part, dict) and part.get("text"):
                content += part["text"]
        usage = None
        um = raw.get("usageMetadata")
        if um:
            usage = {
                "prompt_tokens": um.get("promptTokenCount", 0),
                "completion_tokens": um.get("candidatesTokenCount", 0),
                "total_tokens": um.get("totalTokenCount", 0),
            }
        return content, usage

    # OpenAI format (default): choices[0].message.content
    choices = raw.get("choices") or []
    content = ""
    if choices:
        msg = choices[0].get("message") or {}
        content = msg.get("content", "")
    return content, raw.get("usage")
