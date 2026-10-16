"""Integrity checks for the first-install parallel model downloader."""

from pathlib import Path

import httpx
import pytest

from scripts.download_model_ranges import fetch_range


def test_exact_model_range_is_saved(tmp_path: Path) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            206, headers={"Content-Range": "bytes 2-4/6"}, content=b"cde"
        )
    )
    with httpx.Client(transport=transport) as client:
        part = fetch_range(client, "https://example.com/model", tmp_path / "part.bin", 2, 4, 6)
    assert part.read_bytes() == b"cde"


@pytest.mark.parametrize(
    "headers,content",
    [({"Content-Range": "bytes 0-2/6"}, b"abc"), ({"Content-Range": "bytes 2-4/6"}, b"cd")],
)
def test_wrong_or_incomplete_range_is_never_committed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, headers: dict[str, str], content: bytes
) -> None:
    monkeypatch.setattr("scripts.download_model_ranges.time.sleep", lambda _: None)
    transport = httpx.MockTransport(
        lambda request: httpx.Response(206, headers=headers, content=content)
    )
    part = tmp_path / "part.bin"
    with httpx.Client(transport=transport) as client, pytest.raises(ValueError):
        fetch_range(client, "https://example.com/model", part, 2, 4, 6)
    assert not part.exists()
