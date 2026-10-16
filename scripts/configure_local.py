"""Select the project-local GPU and PostgreSQL profile, preserving API keys."""

import argparse
import shutil
import sys
from pathlib import Path

from dotenv import set_key

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    """Write the chosen local DB/model profile without deleting existing secrets."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-only",
        action="store_true",
        help="Use local PostgreSQL with OpenAI model providers",
    )
    args = parser.parse_args()
    server = None
    if not args.database_only:
        candidates = [
            ROOT / ".runtime/llama/bin/llama-server.exe",
            ROOT / ".runtime/llama/llama-server.exe",
        ]
        server = next((candidate for candidate in candidates if candidate.is_file()), None)
        if server is None:
            raise FileNotFoundError(
                "llama-server.exe missing after installation; see docs/LOCAL_MODELS.md"
            )
    from backend.platform.inference.configuration import ModelSettings

    path = ROOT / ".env"
    if not path.exists():
        shutil.copyfile(ROOT / ".env.example", path)
    settings = ModelSettings.from_file(path).model_copy(
        update={
            "llm_provider": "openai" if args.database_only else "llamacpp",
            "vlm_provider": "openai" if args.database_only else "llamacpp",
            "embedding_provider": "openai" if args.database_only else "llamacpp",
            "llama_cpp_llm_model": "qwen3-vl-4b",
            "llama_cpp_vlm_model": "qwen3-vl-4b",
            "llama_cpp_embedding_model": "bge-m3",
            "llama_cpp_embedding_dimension": 1024,
        }
    )
    settings.save(path)
    for key, value in {
        "PGVECTOR_URL": "postgresql://postgres@127.0.0.1:5433/rag_flow_light",
        "LOCAL_POSTGRES_AUTOSTART": "true",
        "LOCAL_POSTGRES_PORT": "5433",
        "LLAMA_CPP_AUTOSTART": "false" if args.database_only else "true",
    }.items():
        set_key(str(path), key, value, quote_mode="always")
    if server is not None:
        set_key(
            str(path),
            "LLAMA_CPP_SERVER_PATH",
            server.relative_to(ROOT).as_posix(),
            quote_mode="always",
        )
    print("Local profile saved. Start with: uv run python run.py")


if __name__ == "__main__":
    main()
