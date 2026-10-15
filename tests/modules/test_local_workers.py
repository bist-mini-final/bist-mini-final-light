"""Verify that local worker processes belong to the API lifecycle."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from backend.bootstrap.local_workers import LocalWorkers


def test_api_starts_each_local_queue_and_stops_every_child(tmp_path: Path) -> None:
    processes = [Mock() for _ in range(4)]
    for process in processes:
        process.poll.return_value = None
    with patch("backend.bootstrap.local_workers.subprocess.Popen", side_effect=processes) as spawn:
        workers = LocalWorkers(tmp_path)
        workers.start()
        commands = [call.args[0] for call in spawn.call_args_list]
        assert {command[-2] for command in commands} == {
            "workflow", "bi-materialization", "bi-question", "benchmark",
        }
        assert all(command[-1] == "--loop" for command in commands)
        assert all(call.kwargs["cwd"] == tmp_path for call in spawn.call_args_list)
        workers.stop()
    for process in processes:
        process.terminate.assert_called_once()
        process.wait.assert_called_once_with(timeout=5)
    assert not workers.processes


def test_partial_startup_failure_does_not_leave_a_child_running(tmp_path: Path) -> None:
    process = Mock()
    process.poll.return_value = None
    with patch("backend.bootstrap.local_workers.subprocess.Popen", side_effect=[process, OSError("spawn failed")]):
        workers = LocalWorkers(tmp_path)
        with pytest.raises(OSError, match="spawn failed"):
            workers.start()
    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)
    assert not workers.processes


def test_shard_workers_are_optional(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INGESTION_SHARDS_ENABLED", "true")
    process = Mock()
    with patch("backend.bootstrap.local_workers.subprocess.Popen", return_value=process) as spawn:
        workers = LocalWorkers(tmp_path)
        workers.start()
        assert spawn.call_count == 6
        assert "ingestion-embedding" in workers.processes
        assert "ingestion-vector" in workers.processes
        workers.stop()
