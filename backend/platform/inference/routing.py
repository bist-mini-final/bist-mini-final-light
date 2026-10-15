"""Route LLM, vision and embedding calls to independently selected providers."""

from __future__ import annotations

from typing import Any

from backend.platform.inference.chat import LocalChatGateway
from backend.platform.inference.configuration import ModelSettings
from backend.platform.openai.embeddings import OpenAIEmbeddingEncoder
from backend.platform.openai.provider import OpenAIProvider
from backend.platform.openai.responses import OpenAIResponseResult, OpenAIResponsesClient


class RoutedResponsesClient(OpenAIResponsesClient):
    def __init__(self, *, provider: OpenAIProvider, settings: ModelSettings | None = None) -> None:
        super().__init__(provider=provider)
        self.settings = settings or ModelSettings.from_environment()
        self.local_providers = {
            role: OpenAIProvider(api_key="local-no-key", base_url=getattr(self.settings, f"llama_cpp_{role}_url"), timeout_seconds=240, max_retries=0)
            for role in ("llm", "vlm")
        }
        self.local_chat = LocalChatGateway()

    def _local_target(self, request: dict[str, Any]) -> tuple[OpenAIProvider, str] | None:
        vision = any(isinstance(item.get("content"), list) and any(part.get("type") == "input_image" for part in item["content"]) for item in request["input_items"])
        role = "vlm" if vision else "llm"
        model = request["model"]
        if getattr(self.settings, f"{role}_provider") != "llamacpp" and not model.startswith("llamacpp:"):
            return None
        local_model = model if model.startswith("llamacpp:") else self.settings.model_for(role)
        return self.local_providers[role], local_model

    def create_response(self, **kwargs: Any) -> OpenAIResponseResult:
        target = self._local_target(kwargs)
        if target is None:
            return super().create_response(**kwargs)
        return self.local_chat.create(target[0], kwargs, target[1])

    async def create_response_async(self, **kwargs: Any) -> OpenAIResponseResult:
        target = self._local_target(kwargs)
        if target is None:
            return await super().create_response_async(**kwargs)
        return await self.local_chat.create_async(target[0], kwargs, target[1])

    def close(self) -> None:
        for provider in self.local_providers.values():
            provider.close()

    async def aclose(self) -> None:
        for provider in self.local_providers.values():
            await provider.aclose()


class RoutedEmbeddingEncoder(OpenAIEmbeddingEncoder):
    def __init__(self, *, provider: OpenAIProvider, settings: ModelSettings | None = None) -> None:
        self.settings = settings or ModelSettings.from_environment()
        super().__init__(model_name=self.settings.model_for("embedding"), provider=provider)
        self.local_encoder = OpenAIEmbeddingEncoder(
            api_key="local-no-key", base_url=self.settings.llama_cpp_embedding_url, timeout_seconds=240,
        )

    def _fetch_batch(self, batch_index: int, batch_items: Any, model_name: str) -> Any:
        if model_name.startswith("llamacpp:"):
            return self.local_encoder._fetch_batch(batch_index, batch_items, model_name.removeprefix("llamacpp:"))
        return super()._fetch_batch(batch_index, batch_items, model_name)

    async def _fetch_batch_async(self, batch_index: int, batch_items: Any, model_name: str) -> Any:
        if model_name.startswith("llamacpp:"):
            return await self.local_encoder._fetch_batch_async(batch_index, batch_items, model_name.removeprefix("llamacpp:"))
        return await super()._fetch_batch_async(batch_index, batch_items, model_name)

    def encode_for_model(self, queries: list[str], model_name: str, batch_size: int = 2048) -> list[list[float]]:
        if model_name.startswith("llamacpp:"):
            batch_size = min(batch_size, self.settings.llama_cpp_embedding_batch_size)
        return super().encode_for_model(queries, model_name, batch_size)

    async def encode_for_model_async(self, queries: list[str], model_name: str, batch_size: int = 2048) -> list[list[float]]:
        if model_name.startswith("llamacpp:"):
            batch_size = min(batch_size, self.settings.llama_cpp_embedding_batch_size)
        return await super().encode_for_model_async(queries, model_name, batch_size)

    def close(self) -> None:
        self.local_encoder.close()

    async def aclose(self) -> None:
        await self.local_encoder.aclose()
