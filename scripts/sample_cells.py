"""Validate sample monetary cells against source-scoped pgvector documents."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from openpyxl.utils.cell import get_column_letter

from backend.domains.data_sources.infrastructure.pgvector import PgVectorStore


def expected_sample_cells(
    manifest: dict[str, Any], company: dict[str, Any]
) -> dict[tuple[str, str], Decimal]:
    """Map checked fixture statement rows and years to original Excel coordinates."""
    return {
        (sheet, f"{get_column_letter(column)}{row}"): Decimal(str(values[metric]))
        for sheet, rows in manifest["sheet_rows"].items()
        for row, (metric, _label) in enumerate(rows, 6)
        for column, values in enumerate(company["values"], 2)
        if values.get(metric) is not None
    }


def _same_value(actual: object, expected: Decimal) -> bool:
    try:
        value = Decimal(str(actual))
        return value.is_finite() and abs(value - expected) < Decimal("0.000001")
    except InvalidOperation:
        return False


def indexed_sample_complete(
    index: dict[str, Any], *, vector_store: PgVectorStore, expected: dict[tuple[str, str], Decimal]
) -> bool:
    """Require each numeric fixture cell in this exact collection, not another workbook."""
    cells = vector_store.fetch_cells_by_metadata(
        cell_identifiers=[coord for _sheet, coord in expected],
        collection_name=index["index_id"],
        cell_references=[{"sheet_name": sheet, "cell_coord": coord} for sheet, coord in expected],
        limit=len(expected) * 3,
    )
    verified = {
        key
        for cell in cells
        if (key := (str(cell.get("sheet_name") or ""), str(cell.get("cell_coord") or "")))
        in expected
        and _same_value(cell.get("cell_value"), expected[key])
    }
    return set(expected) <= verified
