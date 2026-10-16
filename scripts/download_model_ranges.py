"""Fetch large, pinned models in bounded parallel ranges, then verify the whole file."""

from __future__ import annotations

import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

from scripts.download_runtime import checksum

CHUNK_SIZE = 8 * 1048576


def fetch_range(
    client: httpx.Client, url: str, part: Path, start: int, end: int, size: int
) -> Path:
    """Resume completed chunks; reject ignored or mismatched HTTP ranges."""
    expected = end - start + 1
    if part.is_file() and part.stat().st_size == expected:
        return part
    for attempt in range(3):
        try:
            with client.stream(
                "GET",
                f"{url}?download=true&part={start}&attempt={attempt}",
                headers={"Range": f"bytes={start}-{end}"},
            ) as response:
                response.raise_for_status()
                if (
                    response.status_code != 206
                    or response.headers.get("content-range") != f"bytes {start}-{end}/{size}"
                ):
                    raise ValueError("Server did not return the requested model range")
                temporary = part.with_suffix(".partial")
                with temporary.open("wb") as file:
                    for chunk in response.iter_bytes(1048576):
                        file.write(chunk)
                if temporary.stat().st_size != expected:
                    raise ValueError("Incomplete model range")
                temporary.replace(part)
                return part
        except (httpx.HTTPError, ValueError):
            if attempt == 2:
                raise
            time.sleep(2)
    raise AssertionError("Unreachable")


def download_model(url: str, destination: Path, digest: str, size: int) -> Path:
    """Reuse this installation's bytes, never expose an unverified final GGUF."""
    if not url.startswith("https://"):
        raise ValueError("Model downloads require HTTPS")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and checksum(destination) == digest:
        print(f"Verified existing model: {destination.name}", flush=True)
        return destination
    parts = destination.with_name(destination.name + ".parts")
    parts.mkdir(exist_ok=True)
    ranges = list(range(0, size, CHUNK_SIZE))
    partial = destination.with_name(destination.name + ".partial")
    # Import complete chunks from an interrupted sequential download.
    if partial.is_file():
        with partial.open("rb") as source:
            for start in ranges:
                chunk = source.read(min(CHUNK_SIZE, size - start))
                if len(chunk) != min(CHUNK_SIZE, size - start):
                    break
                part = parts / f"{start:012d}.bin"
                if not part.is_file():
                    part.write_bytes(chunk)
    with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(120, connect=30)) as client:
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [
                pool.submit(
                    fetch_range,
                    client,
                    url,
                    parts / f"{start:012d}.bin",
                    start,
                    min(start + CHUNK_SIZE, size) - 1,
                    size,
                )
                for start in ranges
            ]
            for count, future in enumerate(as_completed(futures), 1):
                future.result()
                if count % 8 == 0 or count == len(ranges):
                    print(f"{destination.name}: {count}/{len(ranges)} chunks", flush=True)
    assembled = destination.with_name(destination.name + ".assembled")
    with assembled.open("wb") as output:
        for start in ranges:
            with (parts / f"{start:012d}.bin").open("rb") as source:
                shutil.copyfileobj(source, output)
    if checksum(assembled) != digest:
        # Discard corrupt chunks so a rerun cannot repeatedly reuse them.
        for start in ranges:
            (parts / f"{start:012d}.bin").unlink(missing_ok=True)
        partial.unlink(missing_ok=True)
        assembled.unlink()
        raise ValueError(f"SHA-256 mismatch: {destination.name}; rerun setup")
    assembled.replace(destination)
    partial.unlink(missing_ok=True)
    for start in ranges:
        (parts / f"{start:012d}.bin").unlink()
    print(f"Verified SHA-256: {destination.name}", flush=True)
    return destination
