"""Declarative Local benchmark coordinator job."""

from __future__ import annotations

from .base import WorkerJobDefinition

BENCHMARK_JOB = WorkerJobDefinition(
    job_id="benchmark",
    name="RAG 비교 벤치마크",
    description=(
        "비교 대상 workflow run을 로컬 큐에 순차 제출하고 정확도·지연·"
        "비용을 채점해 PostgreSQL 결과로 확정합니다."
    ),
    queue_name="benchmark",
    worker_kind="benchmark",
    version="2",
)

__all__ = ["BENCHMARK_JOB"]
