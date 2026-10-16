"""Do not publish successful-looking demo BI from a cached partial sample index."""

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from backend.domains.data_sources.application.ingestion_jobs import (
    IngestionJobService,
    IngestionRequest,
)
from backend.domains.workflow.infrastructure.job_catalog import workflow_from_job
from jobs import EXCEL_INGESTION_JOB
from scripts.sample_ingestion import ensure_sample_index


def response(data: dict) -> httpx.Response:
    return httpx.Response(200, json=data, request=httpx.Request("GET", "http://localhost/test"))


def complete_index() -> dict:
    return {
        "index_id": "sample",
        "document_count": 120,
        "tables": [
            {"sheet_name": name} for name in ("Income Statement", "Balance Sheet", "Cash Flow")
        ],
    }


def test_complete_matching_index_is_reused() -> None:
    client = MagicMock(spec=httpx.Client)
    client.get.return_value = response(complete_index())
    result = ensure_sample_index(
        client,
        "http://localhost/api",
        Path("sample.xlsx"),
        {"index_id": "sample"},
        {"Income Statement", "Balance Sheet", "Cash Flow"},
        30,
    )
    assert result["document_count"] == 120
    client.post.assert_not_called()


def test_new_partial_index_retries_without_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "sample.xlsx"
    path.write_bytes(b"fixture")
    client = MagicMock(spec=httpx.Client)
    client.post.side_effect = [
        response({"ingestion_job": {"job_id": "first"}}),
        response({"job_id": "second"}),
    ]
    results = iter(
        [{"document_count": 70, "tables": [{"sheet_name": "Balance Sheet"}]}, complete_index()]
    )
    monkeypatch.setattr("scripts.sample_ingestion.wait_for_index", lambda *args: next(results))
    result = ensure_sample_index(
        client,
        "http://localhost/api",
        path,
        None,
        {"Income Statement", "Balance Sheet", "Cash Flow"},
        30,
    )
    assert result["document_count"] == 120
    assert client.post.call_args.kwargs["json"]["use_cache"] is False


def test_cached_partial_index_is_never_accepted_after_retry_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock(spec=httpx.Client)
    partial = {
        "index_id": "sample",
        "document_count": 70,
        "tables": [{"sheet_name": "Balance Sheet"}],
    }
    client.get.return_value = response(partial)
    client.post.return_value = response({"job_id": "retry"})
    monkeypatch.setattr("scripts.sample_ingestion.wait_for_index", lambda *args: partial)
    with pytest.raises(RuntimeError, match="after 3 attempts"):
        ensure_sample_index(
            client,
            "http://localhost/api",
            Path("sample.xlsx"),
            partial,
            {"Income Statement", "Balance Sheet", "Cash Flow"},
            30,
        )
    assert client.post.call_count == 3
    client.delete.assert_not_called()


def test_all_sheet_names_do_not_hide_missing_numeric_cells(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock(spec=httpx.Client)
    client.get.return_value = response(complete_index())
    client.post.return_value = response({"job_id": "retry"})
    validate = MagicMock(side_effect=[False, True])
    monkeypatch.setattr("scripts.sample_ingestion.wait_for_index", lambda *args: complete_index())
    result = ensure_sample_index(
        client,
        "http://localhost/api",
        Path("sample.xlsx"),
        complete_index(),
        {"Income Statement", "Balance Sheet", "Cash Flow"},
        30,
        validate,
    )
    assert result["index_id"] == "sample"
    assert client.post.call_args.kwargs["json"]["use_cache"] is False
    client.delete.assert_not_called()


@pytest.mark.parametrize("use_cache", [True, False])
def test_ingestion_request_preserves_explicit_cache_choice(use_cache: bool) -> None:
    workflows, runs, executor, dispatcher = (MagicMock() for _ in range(4))
    workflows.load.return_value = workflow_from_job(EXCEL_INGESTION_JOB)
    service = IngestionJobService(
        workflow_store=workflows,
        run_store=runs,
        workflow_executor=executor,
        workflow_dispatcher=dispatcher,
    )
    service.create_run(IngestionRequest(file_name="sample.xlsx", use_cache=use_cache))
    assert executor.create_run.call_args.args[1].use_cache is use_cache
