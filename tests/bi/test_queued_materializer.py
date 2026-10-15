from datetime import UTC, date, datetime
from unittest.mock import Mock

import pytest

from backend.domains.bi.application.queued_materializer import (
    BiQueuedMaterializer,
    BiQueuedMaterializerServices,
)
from backend.domains.bi.domain.materialization_models import BiDocumentProfile
from backend.domains.bi.domain.models import (
    BiMaterializationRequest,
    BiMaterializationSource,
    BiPeriod,
    CompanyId,
    IndexId,
    JobId,
    MaterializationStatus,
    PeriodId,
    PeriodKind,
)


@pytest.mark.parametrize("end_date", [None, date(2030, 12, 31)])
def test_no_eligible_periods_explains_source_problem_without_publishing_empty_snapshot(
    end_date,
) -> None:
    profiler, questions, store, clock = Mock(), Mock(), Mock(), Mock()
    clock.now.return_value = datetime(2026, 10, 16, tzinfo=UTC)
    profiler.profile.return_value = BiDocumentProfile(
        periods=(
            BiPeriod(
                period_id=PeriodId("fy-test"),
                kind=PeriodKind.FY,
                label="FY",
                source_label="FY",
                end_date=end_date,
                ordinal=0,
            ),
        )
    )
    request = BiMaterializationRequest(
        company_id=CompanyId("company-test"),
        display_name="Test",
        source=BiMaterializationSource(
            file_name="test.xlsx",
            workbook_hash="a" * 64,
            index_id=IndexId("index-test"),
        ),
    )
    outcome = BiQueuedMaterializer(
        BiQueuedMaterializerServices(profiler, questions, store, clock)
    ).materialize(request, JobId("job-test"))
    assert outcome.job.status is MaterializationStatus.FAILED
    assert outcome.job.error_code == "eligible_periods_missing"
    assert outcome.job.message is not None
    assert "결산 종료일" in outcome.job.message
    assert outcome.snapshot is None
    store.publish.assert_not_called()
    questions.queue_materialization_questions.assert_not_called()
