"""Require all sample sheets; retry partial VLM results without reusing cached failures."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import httpx


def complete_sample_index(index: dict[str, Any], required_sheets: set[str]) -> bool:
    """A nonempty index must cover every known sample statement, without failed sheets."""
    structure = index.get("luna_output") or {}
    tables = index.get("tables") or structure.get("tables") or []
    covered = {table.get("sheet_name") for table in tables}
    return (
        bool(index.get("document_count"))
        and required_sheets <= covered
        and not structure.get("failed_sheets")
    )


def wait_for_index(client: httpx.Client, base: str, run_id: str, timeout: int) -> dict[str, Any]:
    """Poll a durable job to completion; real execution failures remain explicit."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(base + "/data-sources/ingestion-jobs/" + run_id)
        response.raise_for_status()
        job = response.json()
        if job["status"] == "completed":
            return job["index"]
        if job["status"] not in {"queued", "running"}:
            raise RuntimeError(f"Ingestion failed: {job.get('error')}")
        time.sleep(2)
    raise TimeoutError(f"Ingestion timed out: {run_id}")


def ensure_sample_index(
    client: httpx.Client,
    base: str,
    path: Path,
    index: dict[str, Any] | None,
    required_sheets: set[str],
    timeout: int,
) -> dict[str, Any]:
    """Reuse complete matching fixtures; reanalyze partial results at most three times."""
    if index is not None:
        response = client.get(base + "/data-sources/indexes/" + index["index_id"])
        response.raise_for_status()
        if complete_sample_index(response.json(), required_sheets):
            return response.json()
        print(f"Reanalyzing incomplete index: {path.name}", flush=True)
    for attempt in range(1, 4):
        if index is None and attempt == 1:
            with path.open("rb") as file:
                response = client.post(
                    base + "/data-sources/files/upload",
                    files={
                        "file": (
                            path.name,
                            file,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    },
                )
            response.raise_for_status()
            job = response.json().get("ingestion_job")
            if job is None:
                raise RuntimeError(f"No ingestion job: {path.name}")
        else:
            response = client.post(
                base + "/data-sources/ingestion-jobs",
                json={"file_name": path.name, "use_cache": False},
            )
            response.raise_for_status()
            job = response.json()
        run_id = job["job_id"]
        print(f"Indexing {path.name} (attempt {attempt}/3): {run_id}", flush=True)
        result = wait_for_index(client, base, run_id, timeout)
        if complete_sample_index(result, required_sheets):
            return result
        print(f"Partial sheet result: {path.name}; retrying without cache", flush=True)
    raise RuntimeError(f"Incomplete sample after 3 attempts: {path.name}; inspect VLM job logs")
