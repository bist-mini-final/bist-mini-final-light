"""Read-only onboarding checks; use --online after starting the application."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx
import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def report(label: str, passed: bool, detail: str) -> bool:
    """Print one actionable result, without credentials or database URLs."""
    print(f"[{'OK' if passed else 'FAIL'}] {label}: {detail}")
    return passed


def check_files() -> bool:
    """Check the files required by either onboarding path, without modifying them."""
    checks = [
        report(
            "Python", sys.version_info >= (3, 11), sys.version.split()[0] + " (recommended: 3.12)"
        ),
        report("Environment", (ROOT / ".env").is_file(), ".env required; see docs/ONBOARDING.md"),
        report(
            "Frontend",
            (ROOT / "dist/index.html").is_file(),
            "dist/index.html required; Node.js is only needed to rebuild",
        ),
        report(
            "BI samples",
            len(list((ROOT / "examples/bi").glob("*.xlsx"))) == 18,
            "examples/bi: expected 18 workbooks",
        ),
    ]
    if os.getenv("LOCAL_POSTGRES_AUTOSTART", "").lower() == "true":
        directory = Path(os.getenv("LOCAL_POSTGRES_BIN", ".runtime/postgres/Library/bin"))
        directory = directory if directory.is_absolute() else ROOT / directory
        checks.append(
            report(
                "Local PostgreSQL",
                (directory / ("pg_ctl.exe" if os.name == "nt" else "pg_ctl")).is_file(),
                "Rerun scripts/setup_local_windows.ps1 if missing",
            )
        )
    return all(checks)


def check_models(online: bool) -> bool:
    """Validate selected providers and local files; optional probes never generate tokens."""
    from backend.platform.inference.configuration import ModelSettings

    try:
        settings = ModelSettings.from_environment()
    except ValueError:
        return report(
            "Model settings", False, "Invalid provider/URL/dimension; compare .env.example"
        )
    checks = []
    for role in ("llm", "vlm", "embedding"):
        provider = getattr(settings, f"{role}_provider")
        if provider == "openai":
            checks.append(
                report(
                    role,
                    bool(os.getenv("OPENAI_API_KEY")),
                    "OpenAI key presence only; account/model access is not tested",
                )
            )
            continue
        if os.getenv("LLAMA_CPP_AUTOSTART", "").lower() == "true":
            names = ["LLAMA_CPP_SERVER_PATH", f"LLAMA_CPP_{role.upper()}_GGUF"]
            if role != "embedding":
                names.append("LLAMA_CPP_MMPROJ")
            for name in names:
                path = Path(os.getenv(name, ""))
                path = path if path.is_absolute() else ROOT / path
                checks.append(
                    report(
                        name,
                        bool(os.getenv(name)) and path.is_file(),
                        "Configured local file must exist",
                    )
                )
        if online:
            try:
                response = httpx.get(
                    getattr(settings, f"llama_cpp_{role}_url") + "/models", timeout=5
                )
                response.raise_for_status()
                model_ids = {item["id"] for item in response.json()["data"]}
                checks.append(
                    report(
                        role,
                        getattr(settings, f"llama_cpp_{role}_model") in model_ids,
                        "Server reachable; configured alias must match /models",
                    )
                )
            except (httpx.HTTPError, ValueError, KeyError):
                checks.append(
                    report(role, False, "Model server not ready; inspect logs/llama-*.log")
                )
    return all(checks)


def check_online() -> bool:
    """Probe loopback API and the configured PostgreSQL schema using SELECT only."""
    try:
        response = httpx.get("http://127.0.0.1:8765/readyz", timeout=5)
        api_ok = report("API", response.status_code == 200, "http://127.0.0.1:8765/readyz")
    except httpx.HTTPError:
        api_ok = report("API", False, "Start uv run python run.py in another terminal")
    from backend.core.settings import PGVECTOR_URL

    try:
        with psycopg2.connect(
            PGVECTOR_URL.replace("postgresql+psycopg://", "postgresql://"), connect_timeout=5
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")
                vector = cursor.fetchone()
                cursor.execute(
                    "SELECT to_regclass('domain_snapshots'), to_regclass('domain_snapshot_heads'), to_regclass('workflow_runs')"
                )
                tables = cursor.fetchone()
        db_ok = report(
            "DB / pgvector / application tables",
            bool(vector and tables and all(tables)),
            "App startup creates tables; startup must finish first",
        )
    except psycopg2.Error:
        db_ok = report(
            "DB",
            False,
            "Check DB service, .env and DATABASE_URL override; credentials are not printed",
        )
    return api_ok and db_ok


def main() -> None:
    """Exit zero only when all requested checks pass; never install or change settings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--online", action="store_true", help="Probe running API, DB and local model aliases"
    )
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    results = [check_files(), check_models(args.online)]
    if args.online:
        results.append(check_online())
    print("See docs/ONBOARDING.md and docs/SETUP.md for the next step.")
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
