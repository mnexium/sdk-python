"""
Mnexium SDK Client
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional, Union

import httpx

from .types import (
    MnexiumDefaults,
    ProviderConfig,
    ChatOptions,
    ProcessOptions,
    ProcessResponse,
    UsageInfo,
    ChatMessage,
    ChatCompletionOptions,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionUsage,
    MnxResponseData,
    SystemPrompt,
    SystemPromptCreateOptions,
    Memory,
    MemoryCreateOptions,
    MemorySearchOptions,
    MemorySearchResult,
    Claim,
    ClaimCreateOptions,
    Profile,
    AgentState,
    AgentStateSetOptions,
)
from .errors import (
    MnexiumError,
    AuthenticationError,
    RateLimitError,
    APIError,
    NotFoundError,
)
from .providers import detect_provider, extract_response_content
from .streaming import StreamResponse

DEFAULT_BASE_URL = "https://mnexium.com/api/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2


class Mnexium:
    """
    Mnexium SDK client.

    Example::

        mnx = Mnexium(
            api_key="mnx_...",
            openai=ProviderConfig(api_key="sk-..."),
        )
        alice = mnx.subject("user_123")
        response = alice.process("Hello!")
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        openai: Optional[ProviderConfig] = None,
        anthropic: Optional[ProviderConfig] = None,
        google: Optional[ProviderConfig] = None,
        defaults: Optional[MnexiumDefaults] = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
        self._max_retries = max_retries if max_retries is not None else DEFAULT_MAX_RETRIES
        self._provisioned_key: Optional[str] = None

        # Provider configurations
        self._openai_config = openai
        self._anthropic_config = anthropic
        self._google_config = google

        # Defaults with sensible fallbacks
        d = defaults or MnexiumDefaults()
        self._defaults = MnexiumDefaults(
            model=d.model or "gpt-4o-mini",
            log=d.log if d.log is not None else True,
            learn=d.learn if d.learn is not None else True,
            recall=d.recall if d.recall is not None else False,
            history=d.history if d.history is not None else True,
            summarize=d.summarize if d.summarize is not None else False,
            system_prompt=d.system_prompt if d.system_prompt is not None else True,
            profile=d.profile,
            subject_id=d.subject_id,
            chat_id=d.chat_id,
            metadata=d.metadata,
            max_tokens=d.max_tokens,
            temperature=d.temperature,
            regenerate_key=d.regenerate_key,
        )

        # Top-level resources
        self.prompts = _PromptsResource(self)

    # ------------------------------------------------------------------
    # process()
    # ------------------------------------------------------------------

    def process(
        self, input: Union[str, ProcessOptions]
    ) -> Union[ProcessResponse, StreamResponse]:
        """
        Process a message with Mnexium's memory-enhanced AI.

        This is the simplified, recommended API for most use cases.

        Args:
            input: A string message or ProcessOptions for full control.

        Returns:
            ProcessResponse for non-streaming, StreamResponse for streaming.

        Example::

            response = mnx.process("Hello!")
            response = mnx.process(ProcessOptions(
                content="Hello!",
                model="gpt-4o",
                subject_id="user_123",
            ))
        """
        if isinstance(input, str):
            options = ProcessOptions(content=input)
        else:
            options = input

        def _val(opt: Any, default: Any, fallback: Any = None) -> Any:
            if opt is not None:
                return opt
            if default is not None:
                return default
            return fallback

        model = _val(options.model, self._defaults.model, "gpt-4o-mini")
        subject_id = _val(options.subject_id, self._defaults.subject_id)
        chat_id = _val(options.chat_id, self._defaults.chat_id)
        log = _val(options.log, self._defaults.log, True)
        learn = _val(options.learn, self._defaults.learn, True)
        recall = _val(options.recall, self._defaults.recall, False)
        profile = _val(options.profile, self._defaults.profile, False)
        history = _val(options.history, self._defaults.history, True)
        summarize = _val(options.summarize, self._defaults.summarize, False)
        system_prompt = _val(options.system_prompt, self._defaults.system_prompt, True)
        metadata = options.metadata or self._defaults.metadata
        max_tokens = _val(options.max_tokens, self._defaults.max_tokens)
        temperature = options.temperature if options.temperature is not None else self._defaults.temperature
        regenerate_key = _val(options.regenerate_key, self._defaults.regenerate_key, False)

        # Provider headers
        extra_headers: Dict[str, str] = {}
        provider = detect_provider(model)

        if provider == "anthropic" and self._anthropic_config:
            extra_headers["x-anthropic-key"] = self._anthropic_config.api_key
        elif provider == "google" and self._google_config:
            extra_headers["x-google-key"] = self._google_config.api_key
        elif self._openai_config:
            extra_headers["x-openai-key"] = self._openai_config.api_key
        elif self._anthropic_config:
            extra_headers["x-anthropic-key"] = self._anthropic_config.api_key
        elif self._google_config:
            extra_headers["x-google-key"] = self._google_config.api_key

        body: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": options.content}],
            "stream": bool(options.stream),
            "mnx": {
                "subject_id": subject_id,
                "chat_id": chat_id,
                "log": log,
                "learn": learn,
                "recall": recall,
                "profile": profile,
                "history": history,
                "summarize": summarize,
                "system_prompt": system_prompt,
                "metadata": metadata,
                "regenerate_key": regenerate_key,
            },
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if temperature is not None:
            body["temperature"] = temperature

        # Streaming path
        if options.stream:
            response = self._request_raw(
                "POST", "/chat/completions", json=body, headers=extra_headers
            )
            return StreamResponse(
                response,
                chat_id=response.headers.get("x-mnx-chat-id") or chat_id or "",
                subject_id=response.headers.get("x-mnx-subject-id") or subject_id or "",
                model=model,
                provisioned_key=response.headers.get("x-mnx-key-provisioned") or None,
                claim_url=response.headers.get("x-mnx-claim-url") or None,
            )

        # Non-streaming path
        raw = self._request(
            "POST", "/chat/completions", json=body, headers=extra_headers
        )

        content, usage_dict = extract_response_content(raw)

        usage = None
        if usage_dict:
            usage = UsageInfo(
                prompt_tokens=usage_dict.get("prompt_tokens", 0),
                completion_tokens=usage_dict.get("completion_tokens", 0),
                total_tokens=usage_dict.get("total_tokens", 0),
            )

        mnx_data = raw.get("mnx", {})
        return ProcessResponse(
            content=content,
            chat_id=mnx_data.get("chat_id", ""),
            subject_id=mnx_data.get("subject_id", ""),
            model=raw.get("model", model),
            usage=usage,
            provisioned_key=mnx_data.get("provisioned_key"),
            claim_url=mnx_data.get("claim_url"),
            raw=raw,
        )

    # ------------------------------------------------------------------
    # subject() / create_chat()
    # ------------------------------------------------------------------

    def subject(self, subject_id: Optional[str] = None) -> "Subject":
        """
        Get a Subject handle for a given subject ID.

        Creating a Subject does NOT make a network call — it's a lightweight scoped handle.

        Example::

            alice = mnx.subject("user_123")
            await alice.process("Hello!")
            await alice.memories.search("hobbies")
        """
        from .subject import Subject

        return Subject(self, subject_id or str(uuid.uuid4()))

    def create_chat(
        self,
        subject: Union["Subject", str],
        options: Optional[ChatOptions] = None,
    ) -> "Chat":
        """
        Create a chat for a subject.

        Example::

            chat = mnx.create_chat("user_123", ChatOptions(history=True))
        """
        from .chat import Chat

        sid = subject if isinstance(subject, str) else subject.id
        return Chat(self, sid, options)

    # ------------------------------------------------------------------
    # Trial key helpers
    # ------------------------------------------------------------------

    def get_provisioned_key(self) -> Optional[str]:
        """Get the auto-provisioned trial key."""
        return self._provisioned_key

    def get_trial_info(self) -> Optional[Dict[str, str]]:
        """
        Get trial key info including the key and claim URL.

        Returns None if no trial key has been provisioned.
        """
        if not self._provisioned_key:
            return None
        return {
            "key": self._provisioned_key,
            "claim_url": "https://mnexium.com/claim",
        }

    # ------------------------------------------------------------------
    # Internal HTTP methods
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make an API request with retries."""
        url = f"{self._base_url}{path}"

        request_headers: Dict[str, str] = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)

        effective_key = self._api_key or self._provisioned_key
        if effective_key:
            request_headers["x-mnexium-key"] = effective_key

        # Filter None params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.request(
                        method,
                        url,
                        json=json,
                        params=params,
                        headers=request_headers,
                    )

                # Check for provisioned key
                provisioned_key = response.headers.get("x-mnx-key-provisioned")
                if provisioned_key:
                    self._provisioned_key = provisioned_key

                if not response.is_success:
                    self._handle_error_response(response)

                return response.json()

            except (APIError,) as e:
                # Don't retry on client errors (4xx) except rate limits
                if isinstance(e, RateLimitError):
                    last_error = e
                elif isinstance(e, APIError) and e.status < 500:
                    raise
                else:
                    last_error = e

                if attempt == self._max_retries:
                    raise

                time.sleep(2**attempt)

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = e
                if attempt == self._max_retries:
                    raise MnexiumError(f"Request failed: {e}") from e
                time.sleep(2**attempt)

        raise last_error or MnexiumError("Request failed")

    def _request_raw(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make a raw API request (returns streaming Response)."""
        url = f"{self._base_url}{path}"

        request_headers: Dict[str, str] = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)

        effective_key = self._api_key or self._provisioned_key
        if effective_key:
            request_headers["x-mnexium-key"] = effective_key

        if params:
            params = {k: v for k, v in params.items() if v is not None}

        client = httpx.Client(timeout=self._timeout)
        response = client.send(
            client.build_request(
                method,
                url,
                json=json,
                params=params,
                headers=request_headers,
            ),
            stream=True,
        )

        # Check for provisioned key
        provisioned_key = response.headers.get("x-mnx-key-provisioned")
        if provisioned_key:
            self._provisioned_key = provisioned_key

        if not response.is_success:
            body_bytes = response.read()
            response.close()
            try:
                import json as json_mod
                body = json_mod.loads(body_bytes)
            except Exception:
                body = {}
            self._handle_error_response_dict(response.status_code, body)

        return response

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error response from a non-streaming request."""
        try:
            body = response.json()
        except Exception:
            body = {}
        self._handle_error_response_dict(response.status_code, body)

    @staticmethod
    def _handle_error_response_dict(status: int, body: Dict[str, Any]) -> None:
        """Raise the appropriate error based on status code."""
        message = body.get("message") or body.get("error") or "Unknown error"
        code = body.get("error")

        if status == 401:
            raise AuthenticationError(str(message))
        elif status == 404:
            raise NotFoundError(str(message))
        elif status == 429:
            raise RateLimitError(
                str(message),
                current=body.get("current"),
                limit=body.get("limit"),
            )
        else:
            raise APIError(str(message), status, str(code) if code else None)


# ------------------------------------------------------------------
# Top-level prompts resource (not subject-scoped)
# ------------------------------------------------------------------


class _PromptsResource:
    """System prompts management — attached to the Mnexium client, not a subject."""

    def __init__(self, client: Mnexium) -> None:
        self._client = client

    def create(self, options: SystemPromptCreateOptions) -> Any:
        """Create a system prompt."""
        response = self._client._request(
            "POST",
            "/prompts",
            json={
                "name": options.name,
                "prompt_text": options.prompt_text,
                "is_default": options.is_default,
            },
        )
        return response.get("prompt", response)

    def get(self, id: str) -> Any:
        """Get a system prompt."""
        return self._client._request("GET", f"/prompts/{id}")

    def list(self) -> List[Any]:
        """List system prompts."""
        response = self._client._request("GET", "/prompts")
        return response.get("prompts", [])

    def update(
        self,
        id: str,
        *,
        name: Optional[str] = None,
        prompt_text: Optional[str] = None,
        is_default: Optional[bool] = None,
    ) -> Any:
        """Update a system prompt."""
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if prompt_text is not None:
            body["prompt_text"] = prompt_text
        if is_default is not None:
            body["is_default"] = is_default
        return self._client._request("PATCH", f"/prompts/{id}", json=body)

    def delete(self, id: str) -> None:
        """Delete a system prompt."""
        self._client._request("DELETE", f"/prompts/{id}")

    def resolve(
        self,
        *,
        subject_id: Optional[str] = None,
        chat_id: Optional[str] = None,
        combined: Optional[bool] = None,
    ) -> Any:
        """Preview which prompts will be injected."""
        return self._client._request(
            "GET",
            "/prompts/resolve",
            params={
                "subject_id": subject_id,
                "chat_id": chat_id,
                "combined": combined,
            },
        )
