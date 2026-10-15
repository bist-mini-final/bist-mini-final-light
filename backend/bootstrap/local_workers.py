"""Own the local worker processes for the lifetime of one FastAPI server."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalWorkers:
    """Poll the existing database queues without an external scheduler."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.processes: dict[str, subprocess.Popen[bytes]] = {}

    def start(self) -> None:
        kinds = ["workflow", "bi-materialization", "bi-question", "benchmark"]
        if os.getenv("INGESTION_SHARDS_ENABLED", "false").lower() in {"true", "1", "yes"}:
            kinds.extend(["ingestion-embedding", "ingestion-vector"])
        try:
            for kind in kinds:
                self.processes[kind] = self._spawn(kind)
                logger.info("로컬 워커 시작: %s", kind)
        except BaseException:
            self.stop()
            raise

    def _spawn(self, kind: str) -> subprocess.Popen[bytes]:
        return subprocess.Popen(
            [sys.executable, "-m", "backend.entrypoints.worker", kind, "--loop"],
            cwd=self.project_dir,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

    def stop(self) -> None:
        # Signal every child first, then wait; one blocked task cannot leave the
        # other workers running after the API has released its resources.
        for process in self.processes.values():
            if process.poll() is None:
                process.terminate()
        for kind, process in self.processes.items():
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            logger.info("로컬 워커 종료: %s", kind)
        self.processes.clear()

    async def monitor(self) -> None:
        while True:
            await asyncio.sleep(1)
            for kind, process in self.processes.items():
                code = process.poll()
                if code is not None:
                    logger.warning("로컬 워커 재시작: %s (exit=%s)", kind, code)
                    try:
                        self.processes[kind] = self._spawn(kind)
                    except OSError:
                        logger.exception("로컬 워커를 재시작하지 못했습니다: %s", kind)


@asynccontextmanager
async def local_worker_lifespan(project_dir: Path, *, enabled: bool) -> AsyncIterator[None]:
    if not enabled:
        yield
        return
    workers = LocalWorkers(project_dir)
    workers.start()
    monitor = asyncio.create_task(workers.monitor())
    try:
        yield
    finally:
        monitor.cancel()
        try:
            with suppress(asyncio.CancelledError):
                await monitor
        finally:
            await asyncio.to_thread(workers.stop)


__all__ = ["LocalWorkers", "local_worker_lifespan"]
