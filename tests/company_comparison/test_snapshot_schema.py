"""Local initialization must include comparison storage, without a manual migration."""

import os
from contextlib import contextmanager
from uuid import uuid4

import psycopg2
import pytest
from psycopg2 import sql

from backend.bootstrap import schema as bootstrap_schema
from backend.platform.postgres.versioned_snapshots import VersionedSnapshotStoreError


def test_snapshot_store_error_survives_context_manager_traceback_assignment() -> None:
    @contextmanager
    def boundary():
        yield

    with pytest.raises(VersionedSnapshotStoreError, match="get_current"):
        with boundary():
            raise VersionedSnapshotStoreError("get_current", "test database error")


@pytest.mark.skipif(not os.getenv("INTEGRATION_DATABASE_URL"), reason="requires local PostgreSQL")
def test_local_bootstrap_creates_scoped_snapshot_storage_idempotently(monkeypatch) -> None:
    database_url = os.environ["INTEGRATION_DATABASE_URL"].replace(
        "postgresql+psycopg://", "postgresql://"
    )
    namespace = "test_snapshots_" + uuid4().hex
    with psycopg2.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(namespace)))

    def scoped_connection(_url: str):
        return psycopg2.connect(database_url, options=f"-csearch_path={namespace},public")

    monkeypatch.setattr(bootstrap_schema, "get_pooled_raw_connection", scoped_connection)
    try:
        assert bootstrap_schema.ensure_application_schema(database_url)
        assert bootstrap_schema.ensure_application_schema(database_url)
        with scoped_connection(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname = %s", (namespace,)
                )
                tables = {row[0] for row in cursor.fetchall()}
                assert {"domain_snapshots", "domain_snapshot_heads"} <= tables
                cursor.execute(
                    "INSERT INTO domain_snapshots (snapshot_id, domain, scope_key, schema_version, source_fingerprint, snapshot_payload, generated_at) VALUES ('sample', 'comparison', 'global', 1, %s, '{}', NOW())",
                    ("a" * 64,),
                )
                cursor.execute(
                    "INSERT INTO domain_snapshot_heads VALUES ('comparison', 'global', 'sample', NOW())"
                )
                with pytest.raises(psycopg2.errors.ForeignKeyViolation):
                    cursor.execute(
                        "INSERT INTO domain_snapshot_heads VALUES ('comparison', 'wrong-scope', 'sample', NOW())"
                    )
    finally:
        with psycopg2.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(namespace)))
