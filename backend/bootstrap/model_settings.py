"""Local learning settings API; credentials are never returned to the browser."""

import asyncio

import httpx
from fastapi import APIRouter

from backend.platform.inference.configuration import ModelSettings
from backend.platform.openai.provider import project_env_value


async def probe_model(settings: ModelSettings, role: str) -> dict[str, str]:
    if getattr(settings, f"{role}_provider") == "openai":
        return {"state": "configured" if project_env_value("OPENAI_API_KEY") else "missing_key", "detail": "OpenAI 키 설정됨 (추론 미검증)" if project_env_value("OPENAI_API_KEY") else "OPENAI_API_KEY가 없습니다"}
    url = getattr(settings, f"llama_cpp_{role}_url")
    expected = getattr(settings, f"llama_cpp_{role}_model")
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(url + "/models")
            response.raise_for_status()
            ids = {item["id"] for item in response.json().get("data", [])}
        if expected not in ids:
            return {"state": "model_missing", "detail": f"서버 모델 별칭이 {expected}와 다릅니다"}
        return {"state": "ready", "detail": f"{expected} 서버 연결됨 (추론 미검증)"}
    except (httpx.HTTPError, ValueError, KeyError):
        return {"state": "unavailable", "detail": "모델 서버에 연결할 수 없습니다. 모델 로딩 로그와 주소를 확인하세요"}


def create_model_settings_router() -> APIRouter:
    router = APIRouter(prefix="/settings/inference", tags=["모델 연결 설정"])

    @router.get("")
    def read_settings() -> ModelSettings:
        return ModelSettings.from_environment()

    @router.get("/status")
    async def model_status() -> dict[str, dict[str, str]]:
        settings = ModelSettings.from_environment()
        roles = ("llm", "vlm", "embedding")
        results = await asyncio.gather(*(probe_model(settings, role) for role in roles))
        return dict(zip(roles, results, strict=True))

    @router.put("")
    def save_settings(settings: ModelSettings) -> dict[str, bool]:
        settings.save()
        return {"saved": True, "restart_required": True}

    return router
