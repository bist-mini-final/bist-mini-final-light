# 가상 데이터로 기능 확인

위치: **`examples/bi/`**. 기본 Windows clone 경로는 `C:\Repos\bist-mini-final-light\examples\bi`입니다.
18개 가상 기업·가상 수치를 독립적인 새 표로 옮겼습니다. 실제 기업의 공시가 아닙니다.
매크로·외부 연결·숨겨진 공급사 정보와 유료 원본 서식은 포함하지 않습니다.
공개 범위는 [데이터 README](../examples/bi/README.md)를 참고하세요.

| 목적 | 파일 | 기대 결과 |
| --- | --- | --- |
| 가벼운 업로드·챗봇 | `examples/sample_financials.xlsx` | Example IPP Co FY2025 Revenue 1500 USD. 일부 BI 지표 없음 |
| 첫 정상 BI | `examples/bi/01_amesoft.xlsx` | Demo Amesoft, 5개 결산 기간과 모든 카드 필수 지표 |
| 성장 사례 | `examples/bi/17_bistelligence.xlsx` | FY2025 매출 18000·영업이익 2610 USD 백만 |
| 하락·적자 사례 | `examples/bi/16_dh_innovation.xlsx` | FY2025 매출 12400·영업이익 -372 USD 백만 |
| 기업 비교 | 18개 전체 | 근거가 완전한 기업 중 두 개 선택·비교 |

## 적재와 질문

앱을 켜 두고 별도 터미널에서 실행합니다.

```powershell
uv run python scripts/load_bi_samples.py --limit 1
```

첫 파일만 처리합니다. 전체는 `--limit 1` 없이 실행합니다.
같은 파일·SHA-256 인덱스는 재사용합니다. 파일당 제한 시간은 기본 1800초이며 `--timeout 2400`처럼 바꿉니다.
세 시트와 원본 수치 셀이 실제 pgvector에 모두 포함된 인덱스만 재사용합니다. VLM 부분 결과는 캐시를 끄고 최대 3회 재분석하며, 끝까지 불완전하면 BI를 발행하지 않고 오류를 표시합니다. 새 인덱스의 완전성을 확인한 뒤 같은 샘플 파일·SHA-256의 이전 불완전 인덱스만 정리합니다.
일반 VLM·임베딩 적재를 사용하므로 OpenAI 모드에서는 비용이 발생합니다.

챗봇에서 아래처럼 기업명을 포함해 질문합니다. 별도의 인덱스 선택 메뉴는 없습니다.

| 질문 | 기대 수치 (USD 백만) | 셀 |
| --- | --- | --- |
| Demo Amesoft의 2025년 매출은? | 약 13698.6020028 | `Income Statement!F6` |
| Demo Bistelligence의 2025년 영업이익은? | 2610 | `Income Statement!F7` |
| Demo DH Innovation의 2025년 영업이익은? | -372 | `Income Statement!F7` |

표시는 `$13,698.6M`처럼 축약될 수 있습니다. 이 예제에서 M은 USD 백만입니다.
LLM 답변은 원본 셀까지 대조합니다. 답이 틀리면 데이터 소스의 적재 상태·질문의 기업명·검색 문맥·셀 근거를 확인하세요.

## BI와 기업 비교

BI에서 Demo 기업을 선택합니다. 매출 및 성장·수익성·현금흐름·재무 안정성·재무 규모를 확인하고,
**카드 추가**로 히트맵을 켭니다. 기업 비교는 근거가 완전한 기업이 최소 두 개 필요합니다.
이전 `Example IPP Co`가 비교에서 제외되어도 18개 Demo 기업은 별도로 사용할 수 있습니다.

샘플 BI는 **실제 셀·manifest를 검증한 뒤 기존 Decimal 계산기로 생성**합니다.
이는 LLM 지표 추출의 정확도를 증명하는 검사가 아닙니다. 화면에도 생성 방식을 표시합니다.
RAG 추출은 **데이터 초기화 및 재생성**으로 별도 실습하며 시간·정확도는 모델에 따라 달라집니다.

## 구성·결측·추가 데이터

- `Income Statement`: 매출·영업이익·순이익, FY2021–FY2025
- `Balance Sheet`: 현금·차입금·자산·부채·자본
- `Cash Flow`: 영업현금흐름·음수 CapEx
- `manifest.json`: 회사·파일명·SHA-256·기대값·행 위치
- `data_archive.json`: 추가 실습용 재무 지표 4,846개 행. 과거·미래 가상 기간도 포함하며 자동 Excel 적재 대상은 아님

원자료에 없는 단기차입금은 빈 값입니다. 총차입금은 보고된 값을 사용합니다.
FY2021 성장률은 이전 연도 비교 대상이 없어 계산하지 않습니다.

값을 바꿔 실습할 때는 복사본을 새 파일명으로 만들고 일반 업로드하세요.
샘플 도구는 체크인 파일의 해시·셀 값이 달라지면 거부합니다.
소형 예제 생성은 `uv run python examples/generate_sample.py`이며 기존 소형 파일을 덮어씁니다.
