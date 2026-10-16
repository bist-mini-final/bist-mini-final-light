"""Download a pinned runtime archive with bounded retries and SHA-256 validation."""

from __future__ import annotations

import argparse
import hashlib
import time
from pathlib import Path

import httpx


def checksum(path: Path) -> str:
    """Hash a file incrementally without loading a CUDA archive into memory."""
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def download_once(client: httpx.Client, url: str, partial: Path) -> None:
    """Resume when supported; restart safely when the server ignores Range."""
    offset = partial.stat().st_size if partial.is_file() else 0
    headers = {"Range": f"bytes={offset}-"} if offset else {}
    print(f"Connecting: {partial.name} (resume {offset // 1048576} MiB)", flush=True)
    with client.stream("GET", url, headers=headers) as response:
        if offset and response.status_code in {400, 416, 501}:
            partial.write_bytes(b"")
        response.raise_for_status()
        append = offset > 0 and response.status_code == 206
        if append and not response.headers.get("content-range", "").startswith(f"bytes {offset}-"):
            partial.write_bytes(b"")
            raise ValueError("Server returned an incorrect resume range")
        downloaded = offset if append else 0
        next_progress = downloaded + 8 * 1048576
        with partial.open("ab" if append else "wb") as file:
            for chunk in response.iter_bytes(1048576):
                file.write(chunk)
                downloaded += len(chunk)
                if downloaded >= next_progress:
                    print(f"Downloaded: {downloaded // 1048576} MiB", flush=True)
                    next_progress = downloaded + 8 * 1048576


def download_file(url: str, destination: Path, expected_sha256: str) -> Path:
    """Write only a verified final archive; retain interrupted bytes for reruns."""
    if not url.startswith("https://"):
        raise ValueError("Runtime downloads require HTTPS")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and checksum(destination) == expected_sha256:
        print(f"Verified existing archive: {destination.name}", flush=True)
        return destination
    partial = destination.with_name(destination.name + ".partial")
    with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(60, connect=30)) as client:
        for attempt in range(1, 4):
            try:
                if not partial.is_file() or checksum(partial) != expected_sha256:
                    download_once(client, url, partial)
                if checksum(partial) != expected_sha256:
                    partial.write_bytes(b"")
                    raise ValueError("SHA-256 mismatch")
                partial.replace(destination)
                print(f"Verified SHA-256: {destination.name}", flush=True)
                return destination
            except (httpx.HTTPError, ValueError) as error:
                print(
                    f"Attempt {attempt}/3 failed: {type(error).__name__}. Retrying is safe.",
                    flush=True,
                )
                if attempt == 3:
                    raise RuntimeError(
                        "Runtime download failed. Check network access and rerun setup."
                    ) from error
                time.sleep(2)
    raise AssertionError("Unreachable")


def main() -> None:
    """CLI used by the Windows installer; never execute downloaded archives."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if len(args.sha256) != 64 or any(
        character not in "0123456789abcdef" for character in args.sha256
    ):
        parser.error("sha256 must be 64 lowercase hexadecimal characters")
    download_file(args.url, args.destination, args.sha256)


if __name__ == "__main__":
    main()
