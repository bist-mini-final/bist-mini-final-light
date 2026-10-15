"""Local snapshot storage matching migrations 0003 and 0004."""

from typing import Final

SNAPSHOT_SCHEMA_SQL: Final = """
CREATE TABLE IF NOT EXISTS domain_snapshots (
    snapshot_id VARCHAR(128) PRIMARY KEY,
    domain VARCHAR(64) NOT NULL,
    scope_key VARCHAR(128) NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version > 0),
    source_fingerprint CHAR(64) NOT NULL
        CHECK (source_fingerprint ~ '^[a-f0-9]{64}$'),
    snapshot_payload JSONB NOT NULL
        CHECK (jsonb_typeof(snapshot_payload) = 'object'),
    generated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_domain_snapshots_scoped_identity
        UNIQUE (domain, scope_key, snapshot_id)
);

CREATE TABLE IF NOT EXISTS domain_snapshot_heads (
    domain VARCHAR(64) NOT NULL,
    scope_key VARCHAR(128) NOT NULL,
    current_snapshot_id VARCHAR(128) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (domain, scope_key),
    CONSTRAINT fk_domain_snapshot_heads_scoped_snapshot
        FOREIGN KEY (domain, scope_key, current_snapshot_id)
        REFERENCES domain_snapshots(domain, scope_key, snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_domain_snapshots_history
    ON domain_snapshots(domain, scope_key, generated_at DESC);
"""
