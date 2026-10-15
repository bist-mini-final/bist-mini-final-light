"""The public fixtures must retain cell evidence and cover every BI card."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

import pytest

from backend.bootstrap.sample_data import build_sample_snapshot, read_sample_manifest
from backend.domains.bi.domain.catalog import METRIC_CATALOG, MetricDisplayRole
from backend.domains.bi.domain.models import (
    BiMaterializationRequest,
    BiMaterializationSource,
    CompanyId,
    IndexId,
    MetricId,
    MetricStatus,
    SnapshotStatus,
)

DIRECTORY = Path(__file__).resolve().parents[2] / "examples" / "bi"
MANIFEST = read_sample_manifest(DIRECTORY)


def request_for(company: dict) -> BiMaterializationRequest:
    return BiMaterializationRequest(
        company_id=CompanyId(company["id"]),
        display_name=company["name"],
        source=BiMaterializationSource(
            file_name=company["file"],
            workbook_hash=company["sha256"],
            index_id=IndexId("sample-index"),
        ),
    )


@pytest.mark.parametrize("company", MANIFEST["companies"], ids=lambda company: company["id"])
def test_fictional_workbook_populates_every_primary_metric_with_real_cell_evidence(
    company: dict,
) -> None:
    snapshot = build_sample_snapshot(
        DIRECTORY, MANIFEST, company, request_for(company), now=datetime(2026, 10, 16, tzinfo=UTC)
    )
    assert snapshot.snapshot.status is SnapshotStatus.READY
    assert len(snapshot.periods) == 5
    for metric_id, definition in METRIC_CATALOG.items():
        if definition.display_role is MetricDisplayRole.PRIMARY:
            observations = snapshot.metrics[metric_id].observations
            # First-year YoY has no preceding year; every later point is real.
            assert all(item.status is MetricStatus.AVAILABLE for item in observations[1:])
            assert all(
                item.evidence for item in observations if item.status is MetricStatus.AVAILABLE
            )
    assert (
        snapshot.metrics[MetricId.REVENUE_YOY_GROWTH].observations[0].status
        is MetricStatus.NOT_MEANINGFUL
    )
    assert all(
        item.status is MetricStatus.MISSING
        for item in snapshot.metrics[MetricId.SHORT_TERM_DEBT].observations
    )
    for index in range(5):

        def number(metric: MetricId, position: int = index) -> Decimal:
            result = snapshot.metrics[metric].observations[position].normalized_value
            assert result is not None
            return result

        assert number(MetricId.FREE_CASH_FLOW) == number(MetricId.OPERATING_CASH_FLOW) + number(
            MetricId.CAPITAL_EXPENDITURE
        )
        assert number(MetricId.NET_DEBT) == number(MetricId.TOTAL_DEBT) - number(
            MetricId.CASH_AND_SHORT_TERM_INVESTMENTS
        )


@pytest.mark.parametrize("company", MANIFEST["companies"], ids=lambda company: company["id"])
def test_public_workbooks_have_no_active_or_original_template_parts(company: dict) -> None:
    with ZipFile(DIRECTORY / company["file"]) as package:
        names = package.namelist()
        assert not any(
            any(
                part in name.lower()
                for part in (
                    "vba",
                    "externallink",
                    "customxml",
                    "connections",
                    "embedding",
                    "signature",
                )
            )
            for name in names
        )
        xml = "\n".join(
            package.read(name).decode("utf-8") for name in names if name.endswith(".xml")
        )
        assert not any(
            marker in xml.lower()
            for marker in (
                "__snloffice",
                "s&p global",
                "capital iq",
                "sheetprotection",
                "workbookprotection",
                'state="hidden"',
                'state="veryhidden"',
            )
        )


def test_changed_workbook_cannot_be_published_as_verified_sample(tmp_path: Path) -> None:
    company = MANIFEST["companies"][0]
    (tmp_path / company["file"]).write_bytes(
        (DIRECTORY / company["file"]).read_bytes() + b"changed"
    )
    with pytest.raises(ValueError, match="hash"):
        build_sample_snapshot(tmp_path, MANIFEST, company, request_for(company))
