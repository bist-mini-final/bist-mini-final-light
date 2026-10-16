"""Interrupted/ignored-range downloads must never publish corrupted runtimes."""

import hashlib

import httpx
import pytest

from scripts import download_runtime


def test_server_ignoring_range_restarts_without_duplicate_bytes(tmp_path):
    payload = b"complete-runtime-archive"
    partial = tmp_path / "runtime.zip.partial"
    partial.write_bytes(payload[:5])
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=payload))
    ) as client:
        download_runtime.download_once(client, "https://example.test/runtime.zip", partial)
    assert partial.read_bytes() == payload


def test_resume_requires_matching_content_range(tmp_path):
    partial = tmp_path / "runtime.zip.partial"
    partial.write_bytes(b"first")
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                206, headers={"Content-Range": "bytes 9-12/13"}, content=b"last"
            )
        )
    ) as client:
        with pytest.raises(ValueError, match="resume range"):
            download_runtime.download_once(client, "https://example.test/runtime.zip", partial)
    assert partial.read_bytes() == b""


def test_bad_checksum_does_not_replace_existing_archive(tmp_path, monkeypatch):
    destination = tmp_path / "runtime.zip"
    destination.write_bytes(b"old archive")
    monkeypatch.setattr(
        download_runtime,
        "download_once",
        lambda client, url, partial: partial.write_bytes(b"corrupt"),
    )
    monkeypatch.setattr(download_runtime.time, "sleep", lambda seconds: None)
    with pytest.raises(RuntimeError, match="download failed"):
        download_runtime.download_file(
            "https://example.test/runtime.zip", destination, hashlib.sha256(b"correct").hexdigest()
        )
    assert destination.read_bytes() == b"old archive"
