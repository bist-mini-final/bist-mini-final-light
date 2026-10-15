"""Optional local worker recipes for large Excel-ingestion shard phases."""

from __future__ import annotations

from .base import WorkerJobDefinition

INGESTION_EMBEDDING_SHARD_JOB = WorkerJobDefinition(
    job_id="ingestion_embedding_shard",
    name="Excel 문서 임베딩 샤드",
    description=(
        "직렬화된 Excel 문서를 API 배치 단위로 claim하여 독립적으로 임베딩하고 "
        "공유 float32 part artifact를 생성합니다."
    ),
    queue_name="ingestion-embedding",
    worker_kind="ingestion-embedding",
)

INGESTION_VECTOR_SHARD_JOB = WorkerJobDefinition(
    job_id="ingestion_vector_shard",
    name="Excel pgvector COPY 샤드",
    description=(
        "완료된 임베딩 artifact의 범위를 결정적 행 ID로 staging collection에 "
        "Binary COPY하고 재시도 시 동일 범위만 교체합니다."
    ),
    queue_name="ingestion-vector",
    worker_kind="ingestion-vector",
)

__all__ = ["INGESTION_EMBEDDING_SHARD_JOB", "INGESTION_VECTOR_SHARD_JOB"]
