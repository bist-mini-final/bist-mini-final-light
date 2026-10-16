"""Sample validation must inspect exact cells, not just table names or total chunk count."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from scripts.sample_cells import indexed_sample_complete


@pytest.mark.parametrize("value,complete", [("10", True), ("11", False), ("NaN", False)])
def test_sample_cells_check_sheet_coordinate_value_and_collection(
    value: str, complete: bool
) -> None:
    store = MagicMock()
    store.fetch_cells_by_metadata.return_value = [
        {"sheet_name": "Cash Flow", "cell_coord": "F6", "cell_value": value}
    ]
    assert (
        indexed_sample_complete(
            {"index_id": "expected-index"},
            vector_store=store,
            expected={("Cash Flow", "F6"): Decimal("10")},
        )
        is complete
    )
    assert store.fetch_cells_by_metadata.call_args.kwargs["collection_name"] == "expected-index"


def test_same_coordinate_on_another_sheet_does_not_satisfy_missing_cash_flow() -> None:
    store = MagicMock()
    store.fetch_cells_by_metadata.return_value = [
        {"sheet_name": "Income Statement", "cell_coord": "F6", "cell_value": "10"}
    ]
    assert not indexed_sample_complete(
        {"index_id": "expected-index"},
        vector_store=store,
        expected={("Cash Flow", "F6"): Decimal("10")},
    )
