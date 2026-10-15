"""Select the project-local GPU and PostgreSQL profile, preserving API keys."""

import shutil
import sys
from pathlib import Path

from dotenv import set_key

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))



def main() -> None:
    from backend.platform.inference.configuration import ModelSettings
    path = ROOT / ".env"
    if not path.exists():
        shutil.copyfile(ROOT / ".env.example", path)
    settings = ModelSettings.from_file(path).model_copy(update={
        "llm_provider": "llamacpp", "vlm_provider": "llamacpp", "embedding_provider": "llamacpp",
        "llama_cpp_llm_model": "qwen3-vl-4b", "llama_cpp_vlm_model": "qwen3-vl-4b",
        "llama_cpp_embedding_model": "bge-m3", "llama_cpp_embedding_dimension": 1024,
    })
    settings.save(path)
    for key, value in {
        "PGVECTOR_URL": "postgresql://postgres@127.0.0.1:5433/rag_flow_light",
        "LOCAL_POSTGRES_AUTOSTART": "true", "LOCAL_POSTGRES_PORT": "5433",
        "LLAMA_CPP_AUTOSTART": "true",
    }.items():
        set_key(str(path), key, value, quote_mode="always")
    print("Local profile saved. Start with: uv run python run.py")


if __name__ == "__main__":
    main()
