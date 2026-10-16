# modules/reader

검색·확장된 셀 근거와 원본 통화·금액 단위로 최종 답변을 생성합니다. 통화나 단위를 한국어 질문에서 추측하지 않습니다.

## 먼저 볼 파일

- [reader.py](reader.py)
- [financial_units.py](financial_units.py): 근거 셀의 정확한 workbook/index에 해당하는 저장 프로필만 조회합니다.

## 작업과 검사

명령은 저장소 루트 기준입니다. Python 변경은 해당 tests 영역의 pytest·ruff·pyright를 실행합니다.
프론트 변경은 frontend에서 npm run check로 검사하고 루트 dist를 함께 갱신합니다.
구체적인 명령은 [개발 안내](../../docs/DEVELOPMENT.md), 전체 연결은 [코드 구조](../../docs/ARCHITECTURE.md)를 참고하세요.
