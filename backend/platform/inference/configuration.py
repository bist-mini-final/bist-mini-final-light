"""Validated, non-secret model settings shared by the API and workers."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from dotenv import dotenv_values, set_key
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.platform.openai.provider import project_env_value

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class ModelSettings(BaseModel):
    """Non-secret role settings; endpoint aliases must match the running server."""
    model_config = ConfigDict(extra="forbid")

    llm_provider: Literal["openai", "llamacpp"] = "openai"
    vlm_provider: Literal["openai", "llamacpp"] = "openai"
    embedding_provider: Literal["openai", "llamacpp"] = "openai"
    openai_llm_model: str = Field(default="gpt-5.6-luna", min_length=1, max_length=200)
    openai_vlm_model: str = Field(default="gpt-5.6-luna", min_length=1, max_length=200)
    openai_embedding_model: str = Field(default="text-embedding-3-small", min_length=1, max_length=200)
    llama_cpp_llm_url: str = "http://127.0.0.1:8081/v1"
    llama_cpp_vlm_url: str = "http://127.0.0.1:8081/v1"
    llama_cpp_embedding_url: str = "http://127.0.0.1:8083/v1"
    llama_cpp_llm_model: str = Field(default="qwen3-vl-4b", min_length=1, max_length=200)
    llama_cpp_vlm_model: str = Field(default="qwen3-vl-4b", min_length=1, max_length=200)
    llama_cpp_embedding_model: str = Field(default="bge-m3", min_length=1, max_length=200)
    llama_cpp_embedding_dimension: int = Field(default=1024, ge=1, le=16000)
    llama_cpp_embedding_batch_size: int = Field(default=16, ge=1, le=2048)

    @field_validator("llama_cpp_llm_url", "llama_cpp_vlm_url", "llama_cpp_embedding_url")
    @classmethod
    def validate_endpoint(cls, value: str) -> str:
        from urllib.parse import urlsplit

        parts = urlsplit(value)
        if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError("HTTP(S) 서버 주소만 사용할 수 있습니다. 인증 정보는 URL에 넣지 마세요.")
        return value.rstrip("/")

    @classmethod
    def from_environment(cls) -> ModelSettings:
        """Read effective runtime settings through the shared environment resolver."""
        values = {key: project_env_value(key.upper()) for key in cls.model_fields}
        return cls.model_validate({key: value for key, value in values.items() if value is not None})

    @classmethod
    def from_file(cls, path: Path = ENV_FILE) -> ModelSettings:
        """Read a specific .env for editing without returning its API key."""
        values = dotenv_values(path)
        return cls.model_validate({key: values[key.upper()] for key in cls.model_fields if values.get(key.upper()) is not None})

    def save(self, path: Path = ENV_FILE) -> None:
        """Update known non-secret fields while preserving unrelated keys."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        for key, value in self.model_dump().items():
            set_key(str(path), key.upper(), str(value), quote_mode="always")

    def model_for(self, role: str) -> str:
        if getattr(self, f"{role}_provider") == "llamacpp":
            return "llamacpp:" + getattr(self, f"llama_cpp_{role}_model")
        return getattr(self, f"openai_{role}_model")
