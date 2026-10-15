from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from backend.platform.inference.chat import LocalChatGateway
from backend.platform.inference.configuration import ModelSettings
from backend.platform.inference.routing import RoutedEmbeddingEncoder, RoutedResponsesClient
from backend.platform.openai.provider import OpenAIProvider
from backend.platform.openai.responses import OpenAIResponsesError


def completion(message: dict, *, finish_reason: str = "stop") -> dict:
    return {"id": "chat-test", "object": "chat.completion", "created": 0, "model": "test",
            "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}}


def test_local_vision_preserves_image_and_enforces_json_schema() -> None:
    captured = []
    def handle(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer local-no-key"
        return httpx.Response(200, json=completion({"role": "assistant", "content": '{"tables": []}'}))
    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        provider = OpenAIProvider(api_key="local-no-key", base_url="http://localhost:8081/v1", http_client=http)
        result = LocalChatGateway().create(provider, {
            "instructions": "Read the image", "input_items": [{"role": "user", "content": [
                {"type": "input_text", "text": "Find tables"},
                {"type": "input_image", "image_url": "data:image/png;base64,AAAA", "detail": "original"},
            ]}], "text_format": {"schema": {"type": "object"}}, "max_output_tokens": 20,
        }, "llamacpp:qwen3-vl-4b")
    assert captured[0]["model"] == "qwen3-vl-4b"
    assert captured[0]["messages"][1]["content"][1] == {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}
    assert captured[0]["response_format"] == {"type": "json_object", "schema": {"type": "object"}}
    assert "reasoning" not in captured[0] and "store" not in captured[0]
    assert result.content == '{"tables": []}' and result.usage["total_tokens"] == 5


def test_local_tool_round_trip_keeps_full_history_and_tool_call_id() -> None:
    captured = []
    def handle(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        message = {"role": "assistant", "content": None, "tool_calls": [{"id": "call-1", "type": "function", "function": {"name": "lookup", "arguments": '{"cell":"B2"}'}}]} if len(captured) == 1 else {"role": "assistant", "content": "1500"}
        return httpx.Response(200, json=completion(message))
    gateway = LocalChatGateway()
    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        provider = OpenAIProvider(api_key="local", base_url="http://localhost:8081/v1", http_client=http)
        first = gateway.create(provider, {"instructions": "Use evidence", "input_items": [{"role": "user", "content": "Revenue?"}], "tools": [{"type": "function", "name": "lookup", "parameters": {"type": "object"}}]}, "llamacpp:qwen")
        second = gateway.create(provider, {"input_items": [{"type": "function_call_output", "call_id": "call-1", "output": "1500"}], "previous_response_id": first.response_id}, "llamacpp:qwen")
    assert [message["role"] for message in captured[1]["messages"]] == ["system", "user", "assistant", "tool"]
    assert captured[1]["messages"][-1]["tool_call_id"] == "call-1"
    assert second.content == "1500"
    assert not gateway.history


def test_truncated_local_output_is_an_error() -> None:
    with pytest.raises(OpenAIResponsesError, match="토큰 한도"):
        LocalChatGateway().result(completion({"role": "assistant", "content": "partial"}, finish_reason="length"), {"messages": []}, 0)


def test_role_selection_can_mix_cloud_text_and_local_vision() -> None:
    cloud = OpenAIProvider(api_key="cloud-secret")
    client = RoutedResponsesClient(provider=cloud, settings=ModelSettings(vlm_provider="llamacpp"))
    try:
        assert client._local_target({"model": "gpt-5.6-luna", "input_items": [{"role": "user", "content": "hello"}]}) is None
        target = client._local_target({"model": "gpt-5.6-luna", "input_items": [{"role": "user", "content": [{"type": "input_image", "image_url": "data:image/png;base64,AAAA"}]}]})
        assert target is not None and target[1] == "llamacpp:qwen3-vl-4b"
        assert target[0].api_key != "cloud-secret"
    finally:
        client.close()
        cloud.close()


def test_saved_settings_preserve_credentials_and_reject_unknown_keys(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text("OPENAI_API_KEY=keep-secret\nPGVECTOR_URL=keep-db\n", encoding="utf-8")
    settings = ModelSettings(llm_provider="llamacpp", embedding_provider="llamacpp")
    settings.save(path)
    assert ModelSettings.from_file(path) == settings
    assert "OPENAI_API_KEY=keep-secret" in path.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY" not in settings.model_dump()
    with pytest.raises(ValidationError):
        ModelSettings.model_validate({"openai_api_key": "cannot-set-from-browser"})
    with pytest.raises(ValidationError):
        ModelSettings(llama_cpp_llm_url="http://user:password@localhost:8081/v1")


def test_local_embedding_uses_model_namespace_float_encoding_and_batch_limit() -> None:
    captured = []
    def handle(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        captured.append(body)
        return httpx.Response(200, json={"object": "list", "model": "bge-m3", "data": [{"object": "embedding", "index": index, "embedding": [3.0, 4.0]} for index, _ in enumerate(body["input"])], "usage": {"prompt_tokens": 1, "total_tokens": 1}})
    cloud = OpenAIProvider(api_key="cloud-key")
    encoder = RoutedEmbeddingEncoder(provider=cloud, settings=ModelSettings(embedding_provider="llamacpp", llama_cpp_embedding_batch_size=1))
    encoder.local_encoder.provider.close()
    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        encoder.local_encoder.provider = OpenAIProvider(api_key="local", base_url="http://localhost:8083/v1", http_client=http)
        vectors = encoder.encode_for_model(["a", "b"], "llamacpp:bge-m3")
    encoder.close()
    cloud.close()
    assert vectors == [[0.6, 0.8], [0.6, 0.8]]
    assert len(captured) == 2
    assert all(body["model"] == "bge-m3" and body["encoding_format"] == "float" for body in captured)


def test_async_local_completion_uses_async_chat_endpoint() -> None:
    async def scenario() -> None:
        async def handle(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/chat/completions"
            return httpx.Response(200, json=completion({"role": "assistant", "content": "ok"}))
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
            provider = OpenAIProvider(api_key="local", base_url="http://localhost:8081/v1", async_http_client=http)
            result = await LocalChatGateway().create_async(provider, {"input_items": [{"role": "user", "content": "hello"}]}, "llamacpp:qwen")
            assert result.content == "ok"
            await provider.aclose()
    asyncio.run(scenario())
