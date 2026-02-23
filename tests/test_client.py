"""
Tests for Mnexium Python SDK — covers the same fixes as the JS SDK tests.
"""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from mnexium import Mnexium
from mnexium.types import (
    ChatCompletionOptions,
    ChatMessage,
    ProcessOptions,
    MemorySearchOptions,
    AgentStateSetOptions,
)


def _mock_response(status_code=200, json_body=None, text="", headers=None):
    """Build a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    resp.headers = headers or {}

    if json_body is not None:
        body_text = json.dumps(json_body)
        resp.text = body_text
        resp.json.return_value = json_body
    else:
        resp.text = text
        resp.json.side_effect = json.JSONDecodeError("", "", 0)

    return resp


def _mock_streaming_response(status_code=200, chunks=None, headers=None):
    """Build a mock httpx.Response for streaming."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    resp.headers = headers or {}

    def iter_bytes():
        for chunk in (chunks or []):
            yield chunk.encode("utf-8")

    resp.iter_bytes = iter_bytes
    resp.close = MagicMock()
    return resp


# ---------------------------------------------------------------
# Fix 1: _request handles 204 / empty body safely
# ---------------------------------------------------------------


class TestEmptyResponseHandling:
    def test_handles_204_no_content(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        mock_resp = _mock_response(status_code=204)

        with patch.object(mnx._http_client, "request", return_value=mock_resp):
            result = mnx.memories.delete("mem_123")
            assert result is None

    def test_handles_200_empty_body(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        mock_resp = _mock_response(status_code=200, text="")

        with patch.object(mnx._http_client, "request", return_value=mock_resp):
            result = mnx.prompts.delete("sp_123")
            assert result is None

    def test_parses_json_responses_correctly(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        mock_resp = _mock_response(
            json_body={"data": [{"id": "mem_1", "text": "hello"}], "count": 1}
        )

        with patch.object(mnx._http_client, "request", return_value=mock_resp):
            result = mnx.memories.list("subj_1")
            assert len(result) == 1
            assert result[0]["id"] == "mem_1"


# ---------------------------------------------------------------
# Fix 2: chat.completions.create streaming
# ---------------------------------------------------------------


class TestChatCompletionsCreate:
    def test_returns_stream_response_when_stream_true(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        sse_chunks = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n',
            "data: [DONE]\n\n",
        ]
        mock_resp = _mock_streaming_response(
            chunks=sse_chunks,
            headers={
                "x-mnx-chat-id": "c1",
                "x-mnx-subject-id": "s1",
            },
        )

        # Mock the build_request + send path used by _request_raw
        with patch.object(mnx._http_client, "build_request"), \
             patch.object(mnx._http_client, "send", return_value=mock_resp):
            stream = mnx.chat.completions.create(
                ChatCompletionOptions(
                    model="gpt-4o-mini",
                    messages=[ChatMessage(role="user", content="Hi")],
                    stream=True,
                )
            )

            content = ""
            for chunk in stream:
                content += chunk.content
            assert content == "Hello"

    def test_returns_typed_response_when_stream_false(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        body = {
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4o-mini",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hi!"},
                    "finish_reason": "stop",
                }
            ],
            "mnx": {"chat_id": "c1", "subject_id": "s1"},
        }
        mock_resp = _mock_response(json_body=body)

        with patch.object(mnx._http_client, "request", return_value=mock_resp):
            result = mnx.chat.completions.create(
                ChatCompletionOptions(
                    model="gpt-4o-mini",
                    messages=[ChatMessage(role="user", content="Hi")],
                )
            )
            assert result.choices[0].message.content == "Hi!"


class TestMemoryPolicyOverride:
    def test_process_non_stream_includes_memory_policy_body_and_header(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        body = {
            "choices": [{"message": {"content": "ok"}}],
            "mnx": {"chat_id": "c1", "subject_id": "s1"},
            "model": "gpt-4o-mini",
        }
        mock_resp = _mock_response(json_body=body)

        with patch.object(mnx._http_client, "request", return_value=mock_resp) as mock_req:
            mnx.process(ProcessOptions(content="hi", memory_policy="mpol_123"))

            call_args = mock_req.call_args
            json_body = call_args[1].get("json", {})
            assert json_body.get("mnx", {}).get("memory_policy") == "mpol_123"
            headers = call_args[1].get("headers", {})
            assert headers.get("x-mnx-memory-policy") == "mpol_123"

    def test_process_stream_false_memory_policy_sets_false_header_and_body(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        mock_resp = _mock_streaming_response(
            chunks=["data: [DONE]\\n\\n"],
            headers={"x-mnx-chat-id": "c1", "x-mnx-subject-id": "s1"},
        )

        with patch.object(mnx._http_client, "build_request") as mock_build, patch.object(
            mnx._http_client, "send", return_value=mock_resp
        ):
            mnx.process(ProcessOptions(content="hi", stream=True, memory_policy=False))

            _, kwargs = mock_build.call_args
            json_body = kwargs.get("json", {})
            assert json_body.get("mnx", {}).get("memory_policy") is False
            headers = kwargs.get("headers", {})
            assert headers.get("x-mnx-memory-policy") == "false"

    def test_chat_completions_non_stream_includes_memory_policy_body_and_header(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        body = {
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4o-mini",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hi!"},
                    "finish_reason": "stop",
                }
            ],
            "mnx": {"chat_id": "c1", "subject_id": "s1"},
        }
        mock_resp = _mock_response(json_body=body)

        with patch.object(mnx._http_client, "request", return_value=mock_resp) as mock_req:
            mnx.chat.completions.create(
                ChatCompletionOptions(
                    model="gpt-4o-mini",
                    messages=[ChatMessage(role="user", content="Hi")],
                    memory_policy="mpol_123",
                )
            )

            call_args = mock_req.call_args
            json_body = call_args[1].get("json", {})
            assert json_body.get("mnx", {}).get("memory_policy") == "mpol_123"
            headers = call_args[1].get("headers", {})
            assert headers.get("x-mnx-memory-policy") == "mpol_123"

    def test_chat_completions_stream_false_memory_policy_sets_false_header_and_body(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        mock_resp = _mock_streaming_response(
            chunks=["data: [DONE]\\n\\n"],
            headers={"x-mnx-chat-id": "c1", "x-mnx-subject-id": "s1"},
        )

        with patch.object(mnx._http_client, "build_request") as mock_build, patch.object(
            mnx._http_client, "send", return_value=mock_resp
        ):
            mnx.chat.completions.create(
                ChatCompletionOptions(
                    model="gpt-4o-mini",
                    messages=[ChatMessage(role="user", content="Hi")],
                    stream=True,
                    memory_policy=False,
                )
            )

            _, kwargs = mock_build.call_args
            json_body = kwargs.get("json", {})
            assert json_body.get("mnx", {}).get("memory_policy") is False
            headers = kwargs.get("headers", {})
            assert headers.get("x-mnx-memory-policy") == "false"


# ---------------------------------------------------------------
# Fix 3: Resource contracts match backend
# ---------------------------------------------------------------


class TestResourceContracts:
    def test_memories_list_parses_data_response(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        mock_resp = _mock_response(
            json_body={"data": [{"id": "mem_1"}], "count": 1}
        )

        with patch.object(mnx._http_client, "request", return_value=mock_resp) as mock_req:
            result = mnx.memories.list("subj_1")
            assert len(result) == 1

            # Verify GET method
            call_args = mock_req.call_args
            assert call_args[0][0] == "GET"
            assert "/memories" in call_args[0][1]

    def test_memories_search_uses_get_with_q_param(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        mock_resp = _mock_response(
            json_body={"data": [{"id": "mem_1", "score": 90}], "count": 1}
        )

        with patch.object(mnx._http_client, "request", return_value=mock_resp) as mock_req:
            result = mnx.memories.search(
                MemorySearchOptions(subject_id="subj_1", query="hobbies")
            )
            assert len(result) == 1

            call_args = mock_req.call_args
            assert call_args[0][0] == "GET"
            assert "/memories/search" in call_args[0][1]
            # Check q param is passed
            params = call_args[1].get("params", {})
            assert params.get("q") == "hobbies"

    def test_state_set_uses_put_with_subject_header(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        mock_resp = _mock_response(json_body={"ok": True})

        with patch.object(mnx._http_client, "request", return_value=mock_resp) as mock_req:
            mnx.state.set(
                AgentStateSetOptions(key="mood", value="happy", subject_id="subj_1")
            )

            call_args = mock_req.call_args
            assert call_args[0][0] == "PUT"
            assert "/state/mood" in call_args[0][1]
            headers = call_args[1].get("headers", {})
            assert headers.get("x-subject-id") == "subj_1"
            # Body should NOT contain subject_id
            body = call_args[1].get("json", {})
            assert "subject_id" not in body

    def test_state_get_uses_subject_header(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        mock_resp = _mock_response(json_body={"key": "mood", "value": "happy"})

        with patch.object(mnx._http_client, "request", return_value=mock_resp) as mock_req:
            mnx.state.get("mood", "subj_1")

            call_args = mock_req.call_args
            assert call_args[0][0] == "GET"
            headers = call_args[1].get("headers", {})
            assert headers.get("x-subject-id") == "subj_1"

    def test_state_delete_uses_subject_header(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        mock_resp = _mock_response(status_code=204)

        with patch.object(mnx._http_client, "request", return_value=mock_resp) as mock_req:
            mnx.state.delete("mood", "subj_1")

            call_args = mock_req.call_args
            assert call_args[0][0] == "DELETE"
            headers = call_args[1].get("headers", {})
            assert headers.get("x-subject-id") == "subj_1"

    def test_subject_profile_delete_field_uses_query_params(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        mock_resp = _mock_response(status_code=204)

        with patch.object(mnx._http_client, "request", return_value=mock_resp) as mock_req:
            user = mnx.subject("subj_1")
            user.profile.delete_field("language")

            call_args = mock_req.call_args
            assert call_args[0][0] == "DELETE"
            assert "/profiles" in call_args[0][1]
            params = call_args[1].get("params", {})
            assert params.get("subject_id") == "subj_1"
            assert params.get("field_key") == "language"


# ---------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------


class TestErrorHandling:
    def test_raises_on_4xx(self):
        mnx = Mnexium(api_key="test-key", max_retries=0)
        mock_resp = _mock_response(status_code=404, json_body={"error": "not_found"})

        with patch.object(mnx._http_client, "request", return_value=mock_resp):
            with pytest.raises(Exception):
                mnx.memories.get("mem_nonexistent")

    def test_does_not_retry_on_4xx(self):
        mnx = Mnexium(api_key="test-key", max_retries=2)
        mock_resp = _mock_response(status_code=400, json_body={"error": "bad_request"})

        with patch.object(mnx._http_client, "request", return_value=mock_resp) as mock_req:
            with pytest.raises(Exception):
                mnx.memories.get("mem_bad")
            assert mock_req.call_count == 1
