"""
Mnexium SDK Client
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

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
    SystemPromptCreateOptions,
    MemoryCreateOptions,
    MemorySearchOptions,
    ClaimCreateOptions,
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

if TYPE_CHECKING:
    from .chat import Chat
    from .subject import Subject


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _normalize_memory_policy(value: Optional[Union[str, bool]]) -> Optional[Union[str, bool]]:
    if value is False:
        return False
    if isinstance(value, str):
        policy_id = value.strip()
        if policy_id:
            return policy_id
    return None


def _apply_memory_policy_header(
    headers: Dict[str, str],
    memory_policy: Optional[Union[str, bool]],
) -> None:
    normalized = _normalize_memory_policy(memory_policy)
    if normalized is False:
        headers["x-mnx-memory-policy"] = "false"
    elif isinstance(normalized, str):
        headers["x-mnx-memory-policy"] = normalized


def _build_records_payload(records: Any) -> Optional[Dict[str, Any]]:
    if records is None:
        return None

    if isinstance(records, dict):
        source = records
        payload: Dict[str, Any] = {}
        for key in ("recall", "learn", "sync", "tables"):
            if key in source and source[key] is not None:
                payload[key] = source[key]
        return payload

    payload = {
        key: value
        for key, value in {
            "recall": getattr(records, "recall", None),
            "learn": getattr(records, "learn", None),
            "sync": getattr(records, "sync", None),
            "tables": getattr(records, "tables", None),
        }.items()
        if value is not None
    }
    return payload


def _parse_chat_completion_response(raw: Dict[str, Any]) -> ChatCompletionResponse:
    choices: List[ChatCompletionChoice] = []
    raw_choices = _as_list(raw.get("choices"))
    for idx, item in enumerate(raw_choices):
        choice = _as_dict(item)
        message = _as_dict(choice.get("message"))
        choices.append(
            ChatCompletionChoice(
                index=int(choice.get("index", idx)),
                message=ChatMessage(
                    role=str(message.get("role", "assistant")),
                    content=str(message.get("content", "")),
                    name=message.get("name"),
                    tool_call_id=message.get("tool_call_id"),
                ),
                finish_reason=choice.get("finish_reason"),
            )
        )

    mnx = _as_dict(raw.get("mnx"))
    mnx_data = MnxResponseData(
        chat_id=str(mnx.get("chat_id", "")),
        subject_id=str(mnx.get("subject_id", "")),
        provisioned_key=mnx.get("provisioned_key"),
        claim_url=mnx.get("claim_url"),
        records=mnx.get("records"),
    )

    usage_obj: Optional[ChatCompletionUsage] = None
    usage = raw.get("usage")
    if isinstance(usage, dict):
        usage_obj = ChatCompletionUsage(
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            total_tokens=int(usage.get("total_tokens", 0)),
        )

    return ChatCompletionResponse(
        id=str(raw.get("id", "")),
        object=str(raw.get("object", "chat.completion")),
        created=int(raw.get("created", 0)),
        model=str(raw.get("model", "")),
        choices=choices,
        mnx=mnx_data,
        usage=usage_obj,
    )


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
        self._http_client = httpx.Client(timeout=self._timeout)

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
            memory_policy=d.memory_policy,
            max_tokens=d.max_tokens,
            temperature=d.temperature,
            regenerate_key=d.regenerate_key,
            records=d.records,
        )

        # Top-level resources
        self.chat = _ChatResource(self)
        self.memories = _MemoriesResource(self)
        self.claims = _ClaimsResource(self)
        self.state = _StateResource(self)
        self.prompts = _PromptsResource(self)
        self.records = _RecordsResource(self)

    def close(self) -> None:
        """Close the underlying HTTP client and release network resources."""
        self._http_client.close()

    def __enter__(self) -> "Mnexium":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

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
        memory_policy = _normalize_memory_policy(
            _val(options.memory_policy, self._defaults.memory_policy)
        )
        max_tokens = _val(options.max_tokens, self._defaults.max_tokens)
        temperature = options.temperature if options.temperature is not None else self._defaults.temperature
        regenerate_key = _val(options.regenerate_key, self._defaults.regenerate_key, False)
        records_config = options.records if options.records is not None else self._defaults.records
        records_payload = _build_records_payload(records_config)

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

        _apply_memory_policy_header(extra_headers, memory_policy)

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
                **({"memory_policy": memory_policy} if memory_policy is not None else {}),
                "regenerate_key": regenerate_key,
                **({"records": records_payload} if records_payload is not None else {}),
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
        raw_obj = self._request(
            "POST", "/chat/completions", json=body, headers=extra_headers
        )
        raw = _as_dict(raw_obj)

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
            records=mnx_data.get("records"),
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
                response = self._http_client.request(
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

                # Handle 204 No Content and empty bodies safely
                if response.status_code == 204:
                    return None

                text = response.text
                if not text:
                    return None

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

        response = self._http_client.send(
            self._http_client.build_request(
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
# Top-level chat resource
# ------------------------------------------------------------------


class _ChatCompletionsResource:
    """Low-level chat completions API — mirrors JS SDK's mnx.chat.completions."""

    def __init__(self, client: Mnexium) -> None:
        self._client = client

    def create(
        self, options: ChatCompletionOptions
    ) -> Union[ChatCompletionResponse, StreamResponse]:
        """
        Create a chat completion.

        Returns ChatCompletionResponse for non-streaming, StreamResponse for streaming.

        Example::

            response = mnx.chat.completions.create(ChatCompletionOptions(
                model="gpt-4o-mini",
                messages=[ChatMessage(role="user", content="Hello!")],
            ))
        """
        headers: Dict[str, str] = {}
        if options.openai_key:
            headers["x-openai-key"] = options.openai_key
        elif options.anthropic_key:
            headers["x-anthropic-key"] = options.anthropic_key
        elif options.google_key:
            headers["x-google-key"] = options.google_key

        memory_policy = _normalize_memory_policy(options.memory_policy)
        _apply_memory_policy_header(headers, memory_policy)
        records_payload = _build_records_payload(options.records)

        body: Dict[str, Any] = {
            "model": options.model,
            "messages": [
                m.to_dict() if isinstance(m, ChatMessage) else m
                for m in options.messages
            ],
            "stream": options.stream,
            "mnx": {
                k: v
                for k, v in {
                    "subject_id": options.subject_id,
                    "chat_id": options.chat_id,
                    "learn": options.learn,
                    "recall": options.recall,
                    "history": options.history,
                    "log": options.log,
                    "system_prompt": options.system_prompt,
                    "metadata": options.metadata,
                    "memory_policy": memory_policy,
                    "regenerate_key": options.regenerate_key,
                    **({"records": records_payload} if records_payload is not None else {}),
                }.items()
                if v is not None
            },
        }
        if options.max_tokens is not None:
            body["max_tokens"] = options.max_tokens
        if options.temperature is not None:
            body["temperature"] = options.temperature
        if options.top_p is not None:
            body["top_p"] = options.top_p
        if options.stop is not None:
            body["stop"] = options.stop

        # Streaming path
        if options.stream:
            response = self._client._request_raw(
                "POST", "/chat/completions", json=body, headers=headers
            )
            return StreamResponse(
                response,
                chat_id=response.headers.get("x-mnx-chat-id") or options.chat_id or "",
                subject_id=response.headers.get("x-mnx-subject-id") or options.subject_id or "",
                model=options.model,
                provisioned_key=response.headers.get("x-mnx-key-provisioned") or None,
                claim_url=response.headers.get("x-mnx-claim-url") or None,
            )

        # Non-streaming path
        raw = _as_dict(
            self._client._request("POST", "/chat/completions", json=body, headers=headers)
        )
        return _parse_chat_completion_response(raw)


class _ChatResource:
    """Chat resource — exposes chat.completions."""

    def __init__(self, client: Mnexium) -> None:
        self.completions = _ChatCompletionsResource(client)


# ------------------------------------------------------------------
# Top-level memories resource
# ------------------------------------------------------------------


class _MemoriesResource:
    """Top-level memories management — matches backend contracts."""

    def __init__(self, client: Mnexium) -> None:
        self._client = client

    def create(self, options: MemoryCreateOptions) -> Any:
        """Create a memory."""
        return self._client._request(
            "POST",
            "/memories",
            json={
                "subject_id": options.subject_id,
                "text": options.text,
                "source": options.source,
                "visibility": options.visibility,
                "metadata": options.metadata,
            },
        )

    def get(self, id: str) -> Any:
        """Get a memory by ID."""
        return self._client._request("GET", f"/memories/{id}")

    def list(
        self,
        subject_id: str,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Any]:
        """List memories for a subject."""
        response = self._client._request(
            "GET",
            "/memories",
            params={
                "subject_id": subject_id,
                "limit": limit,
                "offset": offset,
            },
        )
        return _as_list(_as_dict(response).get("data"))

    def search(self, options: MemorySearchOptions) -> List[Any]:
        """Search memories using the recall pipeline."""
        response = self._client._request(
            "GET",
            "/memories/search",
            params={
                "subject_id": options.subject_id,
                "q": options.query,
                "limit": options.limit,
                "min_score": options.min_score,
            },
        )
        return _as_list(_as_dict(response).get("data"))

    def delete(self, id: str) -> None:
        """Delete a memory."""
        self._client._request("DELETE", f"/memories/{id}")


# ------------------------------------------------------------------
# Top-level claims resource
# ------------------------------------------------------------------


class _ClaimsResource:
    """Top-level claims management."""

    def __init__(self, client: Mnexium) -> None:
        self._client = client

    def create(self, options: ClaimCreateOptions) -> Any:
        """Create a claim."""
        return self._client._request(
            "POST",
            "/claims",
            json={
                "subject_id": options.subject_id,
                "slot": options.slot,
                "value": options.value,
                "confidence": options.confidence,
                "source": options.source,
                "source_memory_id": options.source_memory_id,
            },
        )

    def get(self, id: str) -> Any:
        """Get a claim by ID."""
        return self._client._request("GET", f"/claims/{id}")

    def get_by_slot(self, subject_id: str, slot: str) -> Optional[Any]:
        """Get a claim by subject and slot. Returns None if not found."""
        try:
            return self._client._request(
                "GET", f"/claims/subject/{subject_id}/slot/{slot}"
            )
        except NotFoundError:
            return None

    def list_slots(self, subject_id: str) -> Dict[str, Any]:
        """List all claim slots for a subject."""
        return _as_dict(self._client._request(
            "GET", f"/claims/subject/{subject_id}/slots"
        ))

    def retract(self, id: str) -> None:
        """Retract a claim."""
        self._client._request("POST", f"/claims/{id}/retract")


# ------------------------------------------------------------------
# Top-level state resource
# ------------------------------------------------------------------


class _StateResource:
    """Top-level agent state management — uses x-subject-id header per backend contract."""

    def __init__(self, client: Mnexium) -> None:
        self._client = client

    def get(self, key: str, subject_id: Optional[str] = None) -> Optional[Any]:
        """Get state by key. Returns None if not found."""
        try:
            return self._client._request(
                "GET",
                f"/state/{key}",
                headers={"x-subject-id": subject_id} if subject_id else None,
            )
        except NotFoundError:
            return None

    def set(self, options: AgentStateSetOptions) -> Any:
        """Set state."""
        headers: Dict[str, str] = {}
        if options.subject_id:
            headers["x-subject-id"] = options.subject_id
        return self._client._request(
            "PUT",
            f"/state/{options.key}",
            headers=headers or None,
            json={
                "value": options.value,
                "ttl_seconds": options.ttl_seconds,
            },
        )

    def delete(self, key: str, subject_id: Optional[str] = None) -> None:
        """Delete state."""
        self._client._request(
            "DELETE",
            f"/state/{key}",
            headers={"x-subject-id": subject_id} if subject_id else None,
        )


# ------------------------------------------------------------------
# Top-level prompts resource (not subject-scoped)
# ------------------------------------------------------------------


class _RecordsResource:
    """Records management — structured data with schemas, CRUD, query, and semantic search."""

    def __init__(self, client: Mnexium) -> None:
        self._client = client

    def define_schema(
        self,
        type_name: str,
        fields: Dict[str, Any],
        *,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Any:
        """Define or update a record schema."""
        return self._client._request(
            "POST",
            "/records/schemas",
            json={
                "type_name": type_name,
                "fields": fields,
                "display_name": display_name,
                "description": description,
            },
        )

    def get_schema(self, type_name: str) -> Optional[Any]:
        """Get a schema by type name."""
        try:
            return self._client._request("GET", f"/records/schemas/{type_name}")
        except NotFoundError:
            return None

    def list_schemas(self) -> List[Any]:
        """List all schemas for the project."""
        response = self._client._request("GET", "/records/schemas")
        return _as_list(_as_dict(response).get("schemas"))

    def insert(
        self,
        type_name: str,
        data: Dict[str, Any],
        *,
        owner_id: Optional[str] = None,
        visibility: Optional[str] = None,
        collaborators: Optional[List[str]] = None,
    ) -> Any:
        """Insert a new record."""
        body: Dict[str, Any] = {"data": data}
        if owner_id is not None:
            body["owner_id"] = owner_id
        if visibility is not None:
            body["visibility"] = visibility
        if collaborators is not None:
            body["collaborators"] = collaborators
        return self._client._request("POST", f"/records/{type_name}", json=body)

    def get(self, type_name: str, record_id: str) -> Optional[Any]:
        """Get a record by ID."""
        try:
            return self._client._request("GET", f"/records/{type_name}/{record_id}")
        except NotFoundError:
            return None

    def update(self, type_name: str, record_id: str, data: Dict[str, Any]) -> Any:
        """Update a record (partial merge)."""
        return self._client._request(
            "PUT", f"/records/{type_name}/{record_id}", json={"data": data}
        )

    def delete(self, type_name: str, record_id: str) -> None:
        """Soft-delete a record."""
        self._client._request("DELETE", f"/records/{type_name}/{record_id}")

    def query(
        self,
        type_name: str,
        *,
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Any]:
        """Query records with JSONB filters."""
        body: Dict[str, Any] = {}
        if where is not None:
            body["where"] = where
        if order_by is not None:
            body["order_by"] = order_by
        if limit is not None:
            body["limit"] = limit
        if offset is not None:
            body["offset"] = offset
        response = self._client._request(
            "POST", f"/records/{type_name}/query", json=body
        )
        return _as_list(_as_dict(response).get("records"))

    def search(
        self,
        type_name: str,
        query: str,
        *,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Semantic search across records."""
        body: Dict[str, Any] = {"query": query}
        if limit is not None:
            body["limit"] = limit
        response = self._client._request(
            "POST", f"/records/{type_name}/search", json=body
        )
        return _as_list(_as_dict(response).get("records"))


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
        data = _as_dict(response)
        prompt = data.get("prompt")
        return prompt if prompt is not None else data

    def get(self, id: str) -> Any:
        """Get a system prompt."""
        return self._client._request("GET", f"/prompts/{id}")

    def list(self) -> List[Any]:
        """List system prompts."""
        response = self._client._request("GET", "/prompts")
        return _as_list(_as_dict(response).get("prompts"))

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
