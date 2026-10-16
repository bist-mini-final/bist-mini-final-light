"""Installer profiles preserve secrets and do not require a GPU for the API path."""

import pytest
from dotenv import dotenv_values

from scripts import configure_local


@pytest.mark.parametrize("database_only", [True, False])
def test_profile_preserves_api_key_and_discovers_installed_binary(
    tmp_path, monkeypatch, database_only
):
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=private-test-value\nCUSTOM_SETTING=preserve-me\n", encoding="utf-8"
    )
    if not database_only:
        server = tmp_path / ".runtime/llama/bin/llama-server.exe"
        server.parent.mkdir(parents=True)
        server.write_bytes(b"fake binary; never executed")
    monkeypatch.setattr(configure_local, "ROOT", tmp_path)
    monkeypatch.setattr(
        "sys.argv", ["configure_local.py", *(["--database-only"] if database_only else [])]
    )
    configure_local.main()
    values = dotenv_values(tmp_path / ".env")
    assert values["OPENAI_API_KEY"] == "private-test-value"
    assert values["CUSTOM_SETTING"] == "preserve-me"
    assert values["LLM_PROVIDER"] == ("openai" if database_only else "llamacpp")
    assert values["LLAMA_CPP_AUTOSTART"] == ("false" if database_only else "true")
    assert values["PGVECTOR_URL"] is not None
    assert ":5433/" in values["PGVECTOR_URL"]
    if not database_only:
        assert values["LLAMA_CPP_SERVER_PATH"] == ".runtime/llama/bin/llama-server.exe"


def test_failed_binary_discovery_does_not_overwrite_existing_profile(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    original = "OPENAI_API_KEY=preserve-test-value\n"
    path.write_text(original, encoding="utf-8")
    monkeypatch.setattr(configure_local, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["configure_local.py"])
    with pytest.raises(FileNotFoundError):
        configure_local.main()
    assert path.read_text(encoding="utf-8") == original
