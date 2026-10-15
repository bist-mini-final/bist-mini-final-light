"""Translate the application's Responses contract into llama.cpp chat calls."""

from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from typing import Any
from uuid import uuid4

from backend.platform.openai.provider import OpenAIProvider
from backend.platform.openai.responses import OpenAIResponseResult, OpenAIResponsesError


def chat_input(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    messages = []
    for item in items:
        if item.get("type") == "function_call_output":
            messages.append({"role": "tool", "tool_call_id": item["call_id"], "content": str(item["output"])})
            continue
        content = item.get("content", "")
        if isinstance(content, list):
            converted = []
            for part in content:
                kind = part.get("type")
                if kind in {"input_text", "output_text", "text"}:
                    converted.append({"type": "text", "text": part["text"]})
                elif kind == "input_image":
                    converted.append({"type": "image_url", "image_url": {"url": part["image_url"]}})
                else:
                    raise OpenAIResponsesError(f"로컬 모델에 지원되지 않는 입력 형식입니다: {kind}")
            content = converted
        messages.append({"role": item.get("role", "user"), "content": content})
    return messages


class LocalChatGateway:
    def __init__(self) -> None:
        self.history: OrderedDict[str, tuple[float, list[dict[str, Any]]]] = OrderedDict()
        self.lock = threading.Lock()

    def payload(self, request: dict[str, Any], model: str) -> dict[str, Any]:
        previous = request.get("previous_response_id")
        messages: list[dict[str, Any]] = []
        if previous:
            with self.lock:
                saved = self.history.pop(previous, None)
            if saved is None or time.monotonic() - saved[0] > 600:
                raise OpenAIResponsesError("로컬 도구 호출 대화가 만료되었습니다. 작업을 다시 실행하세요.")
            messages.extend(saved[1])
        elif request.get("instructions"):
            messages.append({"role": "system", "content": request["instructions"]})
        messages.extend(chat_input(request["input_items"]))
        payload: dict[str, Any] = {"model": model.removeprefix("llamacpp:"), "messages": messages, "temperature": 0}
        if request.get("max_output_tokens") is not None:
            payload["max_tokens"] = request["max_output_tokens"]
        if request.get("text_format") and not request.get("tools"):
            payload["response_format"] = {"type": "json_object", "schema": request["text_format"]["schema"]}
        if request.get("tools"):
            payload["tools"] = [{"type": "function", "function": {key: value for key, value in tool.items() if key != "type"}} for tool in request["tools"]]
        return payload

    @staticmethod
    def structured_final(payload: dict[str, Any], request: dict[str, Any], document: dict[str, Any]) -> dict[str, Any] | None:
        # Keep tool-call grammar separate from the final JSON-schema grammar.
        # Several llama.cpp chat templates cannot combine them in one request.
        if not request.get("tools") or not request.get("text_format"):
            return None
        message = document["choices"][0]["message"]
        if message.get("tool_calls"):
            return None
        schema = request["text_format"]["schema"]
        return {
            **{key: value for key, value in payload.items() if key != "tools"},
            "messages": [*payload["messages"], message, {"role": "user", "content": "Return the final answer using the supplied evidence and this JSON schema. Preserve evidence IDs exactly.\n" + json.dumps(schema, ensure_ascii=False)}],
            "response_format": {"type": "json_object", "schema": schema},
        }

    @staticmethod
    def combined_usage(first: dict[str, Any], final: dict[str, Any]) -> dict[str, Any]:
        return {**final, "usage": {key: (first.get("usage", {}).get(key) or 0) + (final.get("usage", {}).get(key) or 0) for key in ("prompt_tokens", "completion_tokens", "total_tokens")}}

    def result(self, document: dict[str, Any], payload: dict[str, Any], started: float) -> OpenAIResponseResult:
        choices = document.get("choices") or []
        if not choices:
            raise OpenAIResponsesError("llama.cpp 서버가 빈 응답을 반환했습니다")
        choice = choices[0]
        if choice.get("finish_reason") == "length":
            raise OpenAIResponsesError("로컬 모델 출력이 토큰 한도에 도달했습니다. 컨텍스트와 출력 한도를 확인하세요.")
        message = choice["message"]
        calls = tuple({"call_id": call["id"], "name": call["function"]["name"], "arguments": call["function"]["arguments"]} for call in message.get("tool_calls") or [])
        content = message.get("content") or ""
        if not content and not calls:
            raise OpenAIResponsesError("로컬 모델이 답변이나 도구 호출을 반환하지 않았습니다")
        response_id = "local_" + uuid4().hex
        if calls:
            with self.lock:
                self.history[response_id] = (time.monotonic(), [*payload["messages"], message])
                while len(self.history) > 128:
                    self.history.popitem(last=False)
        usage = document.get("usage") or {}
        return OpenAIResponseResult(response_id, content, {
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
            "cached_tokens": 0, "reasoning_tokens": 0,
        }, time.perf_counter() - started, calls, "llamacpp:" + payload["model"])

    def create(self, provider: OpenAIProvider, request: dict[str, Any], model: str) -> OpenAIResponseResult:
        payload = self.payload(request, model)
        started = time.perf_counter()
        try:
            client = provider.with_timeout(request.get("timeout_seconds") or 240)
            document = client.chat.completions.create(**payload).model_dump(mode="json")
            result = self.result(document, payload, started)
            final_payload = self.structured_final(payload, request, document)
            if final_payload is not None:
                final = client.chat.completions.create(**final_payload).model_dump(mode="json")
                return self.result(self.combined_usage(document, final), final_payload, started)
            return result
        except OpenAIResponsesError:
            raise
        except Exception as error:
            raise OpenAIResponsesError(f"llama.cpp 호출 실패: {error}") from error

    async def create_async(self, provider: OpenAIProvider, request: dict[str, Any], model: str) -> OpenAIResponseResult:
        payload = self.payload(request, model)
        started = time.perf_counter()
        try:
            client = await provider.with_timeout_async(request.get("timeout_seconds") or 240)
            response = await client.chat.completions.create(**payload)
            document = response.model_dump(mode="json")
            result = self.result(document, payload, started)
            final_payload = self.structured_final(payload, request, document)
            if final_payload is not None:
                final = await client.chat.completions.create(**final_payload)
                return self.result(self.combined_usage(document, final.model_dump(mode="json")), final_payload, started)
            return result
        except OpenAIResponsesError:
            raise
        except Exception as error:
            raise OpenAIResponsesError(f"llama.cpp 호출 실패: {error}") from error
