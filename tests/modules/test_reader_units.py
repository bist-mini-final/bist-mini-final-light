"""Reader monetary units must come from each cited workbook, never the question language."""

import json
from unittest.mock import MagicMock

from backend.domains.data_sources.domain.workbook_profiles import (
    WorkbookAmountScale,
    WorkbookProfile,
)
from backend.shared.application.cell_evidence import CellEvidenceDTO
from modules.common.base_module import DocumentContextDTO, QueryContextDTO
from modules.reader.financial_units import render_workbook_units
from modules.reader.reader import ReaderConfigDTO, ReaderInputDTO, ReaderModule
from modules.retrieval.context_expander import ContextCellDTO, ContextDTO


def source_cell(index: str, digest: str) -> CellEvidenceDTO:
    return CellEvidenceDTO(
        evidence_id="E1",
        index_id=index,
        workbook_hash=digest,
        file_name=index + ".xlsx",
        sheet_name="Income Statement",
        cell_coord="F6",
        cell_value="13698.6",
        source_text="Cell Value: 13698.6",
    )


def profile(index: str, digest: str, currency: str) -> WorkbookProfile:
    return WorkbookProfile(
        profile_version="1",
        file_name=index + ".xlsx",
        workbook_hash=digest,
        index_id=index,
        status="partial",
        currency=currency,
        amount_scale=WorkbookAmountScale.MILLIONS,
    )


def test_units_are_scoped_to_each_cited_workbook_and_deduplicated() -> None:
    first, second = source_cell("idx-usd", "a" * 64), source_cell("idx-jpy", "b" * 64)
    profiles = MagicMock()
    profiles.get.side_effect = lambda **keys: profile(
        keys["index_id"], keys["workbook_hash"], "USD" if keys["index_id"] == "idx-usd" else "JPY"
    )
    facts = json.loads(render_workbook_units([first, first, second], profiles).split("\n", 1)[1])
    assert [(item["index_id"], item["currency"], item["amount_scale"]) for item in facts] == [
        ("idx-usd", "USD", "millions"),
        ("idx-jpy", "JPY", "millions"),
    ]
    assert profiles.get.call_count == 2


def test_unknown_or_mismatched_units_have_no_currency_default() -> None:
    cell = source_cell("idx-usd", "a" * 64)
    assert render_workbook_units([cell], None).endswith("[]")
    profiles = MagicMock()
    profiles.get.return_value = profile("idx-other", "b" * 64, "KRW")
    assert render_workbook_units([cell], profiles).endswith("[]")


def test_reader_prompt_includes_original_units_and_no_guessing_rule() -> None:
    cell = source_cell("idx-usd", "a" * 64)
    profiles = MagicMock()
    profiles.get.return_value = profile("idx-usd", "a" * 64, "USD")
    reader = ReaderModule(MagicMock(), MagicMock(), workbook_units=profiles)
    messages, *_ = reader._request(
        ReaderInputDTO(
            context_json=ContextDTO(
                query_context=QueryContextDTO(question_id="q1", question_text="2025년 매출은?"),
                document_context=DocumentContextDTO(
                    file_name=cell.file_name,
                    workbook_hash=cell.workbook_hash,
                    index_id=cell.index_id,
                ),
                cells=[ContextCellDTO.model_validate(cell.model_dump(exclude={"evidence_id"}))],
            )
        ),
        ReaderConfigDTO(),
    )
    assert "한국어 질문이라는 이유로" in messages[0]["content"]
    assert '"currency": "USD"' in messages[1]["content"]
    assert '"amount_scale": "millions"' in messages[1]["content"]
    assert '"display_unit": "USD 백만"' in messages[1]["content"]
