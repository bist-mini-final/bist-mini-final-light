"""Expose source-scoped workbook units to the Reader without guessing defaults."""

from __future__ import annotations

import json
from typing import Protocol

from backend.domains.data_sources.domain.workbook_profiles import WorkbookProfile
from backend.shared.application.cell_evidence import CellEvidenceDTO


class WorkbookUnitsPort(Protocol):
    def get(self, *, workbook_hash: str, index_id: str) -> WorkbookProfile | None: ...


UNIT_INSTRUCTIONS = (
    "[통화·금액 단위 규칙] 원본 문서의 통화·금액 단위를 그대로 보존하십시오. "
    "각 파일의 currency와 amount_scale을 해당 파일의 금액에 적용하고, 서로 다른 "
    "파일의 단위를 섞거나 환율 없이 환산하지 마십시오. 비율·주당 금액 등 별도 단위가 "
    "명시된 지표는 그 표기를 따르십시오. 단위 근거가 없으면 숫자와 함께 '단위 미확인'을 "
    "표시하고 한국어 질문이라는 이유로 원·억원 등 통화를 추측하지 마십시오."
)


def render_workbook_units(cells: list[CellEvidenceDTO], profiles: WorkbookUnitsPort | None) -> str:
    """Look up only the exact workbook/index pairs present in citable evidence."""
    facts: list[dict[str, str | None]] = []
    seen: set[tuple[str, str]] = set()
    if profiles is not None:
        for cell in cells:
            identity = (cell.workbook_hash, cell.index_id or "")
            if not all(identity) or identity in seen:
                continue
            seen.add(identity)
            profile = profiles.get(workbook_hash=identity[0], index_id=identity[1])
            if profile is not None and (profile.workbook_hash, profile.index_id) == identity:
                facts.append(
                    {
                        "file_name": profile.file_name,
                        "index_id": profile.index_id,
                        "currency": profile.currency,
                        "amount_scale": profile.amount_scale.value
                        if profile.amount_scale
                        else None,
                    }
                )
    return "[원본 문서의 통화·금액 단위]\n" + json.dumps(facts, ensure_ascii=False)
