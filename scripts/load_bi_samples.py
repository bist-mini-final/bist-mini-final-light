"""Upload the fictional samples normally, then build reproducible BI demo cards."""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    """Index checked-in fixtures and publish cell-verified BI demo snapshots.

    Requires the running local API and the same database configuration. Reuses
    matching workbook indexes; ordinary RAG metric extraction remains separate.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://127.0.0.1:8765")
    parser.add_argument("--limit", type=int, default=18)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    if not 1 <= args.limit <= 18 or args.timeout <= 0:
        parser.error("limit must be 1..18 and timeout must be positive")
    if urlsplit(args.api_url).hostname not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("Run against the local application using the same .env database settings")
    load_dotenv(ROOT / ".env")
    from backend.bootstrap.sample_data import build_sample_snapshot, read_sample_manifest
    from backend.domains.bi.domain.models import (
        BiMaterializationJob,
        BiMaterializationRequest,
        BiMaterializationSource,
        CompanyId,
        IndexId,
        MaterializationStatus,
        MetricStatus,
    )
    from backend.domains.bi.infrastructure.postgres.store import PostgresBiStore

    directory = ROOT / "examples" / "bi"
    manifest = read_sample_manifest(directory)
    store = PostgresBiStore()
    base = args.api_url.rstrip("/") + "/api/v1"
    with httpx.Client(timeout=60) as client:
        client.get(base + "/data-sources/db-status").raise_for_status()
        for company in manifest["companies"][: args.limit]:
            path = directory / company["file"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != company["sha256"]:
                raise ValueError(f"Changed fixture: {path.name}")
            response = client.get(base + "/data-sources/indexes")
            response.raise_for_status()
            index = next(
                (
                    item
                    for item in response.json()["indexes"]
                    if item.get("file_name") == path.name
                    and item.get("workbook_hash") == company["sha256"]
                ),
                None,
            )
            if index is None:
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
                    raise RuntimeError(f"No ingestion job: {response.text}")
                run_id = job["job_id"]
                print(f"Indexing {path.name}: {run_id}", flush=True)
                deadline = time.monotonic() + args.timeout
                while time.monotonic() < deadline:
                    response = client.get(base + "/data-sources/ingestion-jobs/" + run_id)
                    response.raise_for_status()
                    job = response.json()
                    if job["status"] == "completed":
                        index = job["index"]
                        if index.get("luna_output", {}).get("failed_sheets"):
                            raise RuntimeError(f"Partial sheet ingestion: {path.name}")
                        break
                    if job["status"] not in {"queued", "running"}:
                        raise RuntimeError(f"Ingestion failed: {job.get('error')}")
                    time.sleep(2)
                else:
                    raise TimeoutError(path.name)
            assert index is not None
            index_id = index["index_id"]
            response = client.put(
                base + "/data-sources/indexes/" + index_id + "/company",
                json={"company_name": company["name"]},
            )
            response.raise_for_status()
            candidates_response = client.get(base + "/bi/materialization-candidates")
            candidates_response.raise_for_status()
            candidates = candidates_response.json()["candidates"]
            companies_response = client.get(base + "/bi/companies")
            companies_response.raise_for_status()
            entries = [*candidates, *companies_response.json()["companies"]]
            entry = next(
                item for item in entries if (item.get("source") or {}).get("index_id") == index_id
            )
            request = BiMaterializationRequest(
                company_id=CompanyId(entry["company_id"]),
                display_name=company["name"],
                source=BiMaterializationSource(
                    file_name=path.name, workbook_hash=company["sha256"], index_id=IndexId(index_id)
                ),
            )
            now = datetime.now(UTC)
            snapshot = build_sample_snapshot(directory, manifest, company, request, now=now)
            assert snapshot.refresh.job_id is not None
            reported = sum(
                observation.status is MetricStatus.AVAILABLE
                for series in snapshot.metrics.values()
                for observation in series.observations
            )
            job = BiMaterializationJob(
                job_id=snapshot.refresh.job_id,
                company_id=request.company_id,
                workbook_hash=request.source.workbook_hash,
                status=MaterializationStatus.READY,
                completed_requests=reported,
                total_requests=reported,
                message=snapshot.refresh.message,
                started_at=now,
                updated_at=now,
            )
            store.enqueue(request, job)
            store.publish(snapshot)
            store.save_job(
                job.model_copy(update={"published_snapshot_id": snapshot.snapshot.snapshot_id})
            )
            print(
                f"Ready: {company['name']} ({snapshot.snapshot.status.value}, {len(snapshot.periods)} years)",
                flush=True,
            )


if __name__ == "__main__":
    main()
