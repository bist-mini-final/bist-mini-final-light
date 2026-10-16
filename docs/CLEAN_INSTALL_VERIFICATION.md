# 새 클론 설치·실습 검증

2026-10-16, Windows에서 README 순서로 실제 설치와 실습을 검증했습니다.
기준 코드: `18139a7` 및 이 보고서를 포함한 이후 문서 커밋.

## 분리한 범위

GitHub에서 `C:\Repos\bist-mini-final-light-onboarding-test-20261016`에 새로 clone했습니다.
기존 `.env`, `.venv`, DB, 모델·실행 파일을 복사하지 않았습니다.
uv·Hugging Face·micromamba 캐시도 검증 폴더 아래 별도로 지정했습니다.
설치 중 발견한 문제는 저장소에 수정한 뒤 같은 클론에서 다시 실행했습니다.

OS를 재설치한 새 PC 검증은 아닙니다. 기존 Git·uv·PowerShell·NVIDIA 드라이버는 사용했습니다.
일반 실행에 Node.js·Docker·Compose·Kubernetes는 사용하지 않았습니다.

| 항목 | 실제 환경 |
| --- | --- |
| Git / uv / PowerShell | 2.56.0.windows.2 / 0.12.23 / 7.6.5 |
| Python | uv로 새로 받은 CPython 3.12.15, 별도 `.venv` |
| DB | 새 프로젝트 클러스터, PostgreSQL 16.15 + pgvector 0.8.6 |
| GPU | RTX 5050 Laptop, VRAM 8GB, 드라이버 610.74 |
| llama.cpp | 공식 b11429 CUDA 12.4 Windows 배포 파일 |
| 모델 | Qwen3-VL 4B Q4_K_M + 대응 mmproj Q8_0, BGE-M3 Q8_0 |
| 포트 | API 8765, DB 5433, Qwen 8081, BGE-M3 8083 |

CUDA 배포 ZIP 2개와 GGUF 3개를 직접 내려받고 SHA-256을 확인했습니다.
GitHub·Hugging Face 전송 속도가 느려 다운로드가 가장 오래 걸렸습니다.
모델 서버의 별칭과 CUDA GPU 인식도 확인했습니다. OpenAI 키 없이 로컬 제공자만 사용했습니다.

## 실행한 순서

각 명령은 새 클론 루트에서 실행했습니다. 서버가 실행 중인 동안 다음 명령은 별도 터미널에서 실행합니다.

```powershell
uv python install 3.12
uv sync --frozen
pwsh -File scripts/setup_local_windows.ps1
uv run python scripts/check_environment.py
uv run python run.py
```

```powershell
uv run python scripts/check_environment.py --online
uv run python scripts/load_bi_samples.py --limit 1
# 챗봇의 첫 질문과 BI를 확인한 뒤 전체 실습
uv run python scripts/load_bi_samples.py
```

기본 포트를 사용하기 위해 기존 실습 앱은 잠시 종료했습니다.
시작 직후 DB의 `data_directory`가 새 클론 아래인지 확인했고, 인덱스와 BI 기업이 각각 0개였습니다.
`vector`, `domain_snapshots`, `domain_snapshot_heads`도 수동 마이그레이션 없이 생성됐습니다.

## 실제 결과

| 검사 | 결과 |
| --- | --- |
| 실행 전·온라인 환경 검사 | 모두 통과 |
| 첫 샘플 | `Ready: Demo Amesoft (ready, 5 years)` |
| 챗봇 질문 | `Demo Amesoft의 2025년 매출은 얼마인가요? 원본 셀 근거도 알려주세요.` |
| 로컬 답변 | `Demo Amesoft의 2025년 매출은 13,698.60 USD 백만입니다.` |
| 답변 근거 | `01_amesoft.xlsx`, `Income Statement!F6`, 원본값 약 `13698.6020028` |
| 전체 적재 | 인덱스 18개, BI 기업 18개 모두 `ready`, 기업당 5개 결산 기간 |
| 실제 검색 데이터 | 원본 수치 셀 1,080개 모두 해당 인덱스에 존재하고 값 일치, 문서 2,170개 |
| BI 카드 | 모든 필수 지표 사용 가능; 첫 기업의 기본 5개 카드와 추가 히트맵 표시 확인 |
| 기업 비교 API | `ready`, 기업 18개, 셀 근거 252개, 제외 기업 0개 |
| 기업 비교 화면 | Amesoft·Nexora 선택, 점수·성장률·수익성·매출 추이 비교 정상 |
| 회귀 검사 | 새 가상환경과 별도 테스트 DB에서 **429개 통과**, 건너뛴 검사 없음 |
| 정적 검사 | 전체 ruff 통과, pyright 오류 0·경고 0 |

문서 수는 VLM이 선택한 표 영역과 직렬화 결과에 따라 달라질 수 있습니다.
완료 기준은 문서 수 고정값보다 원본 수치 셀의 누락 여부·실제 값·근거 연결입니다.
pytest에는 Starlette의 TestClient 의존성 사용 중단 경고 1개가 있었으며 검사 실패는 없었습니다.

## 검증 중 발견해 수정한 문제

1. 큰 런타임·모델 다운로드의 진행 표시와 재개 처리가 부족했습니다.
   제한 시간·재시도·구간 다운로드·공식 SHA-256 검증을 추가했습니다.
2. 문서의 수동 실행 경로와 실제 압축 해제 경로가 달랐고, 없는 챗봇 인덱스 선택 메뉴를 안내했습니다.
   설치 결과와 실제 화면에 맞췄습니다.
3. 원본 프로필에 저장된 `USD / millions`가 Reader에 전달되지 않아 `원`으로 답하거나 배율을 생략했습니다.
   근거의 정확한 workbook/index 프로필과 표시 단위를 전달하고, 한국어 질문에서 단위를 추측하지 않도록 했습니다.
4. VLM이 표 위 제목을 전체 표 범위에서 제외해 일부 시트가 실패했습니다.
   시트 안·같은 열 범위에 있는 제목만 표 범위에 포함하도록 보정하며 시트 밖 좌표는 계속 거부합니다.
5. 표 이름은 모두 있어도 현금흐름 셀이 빠진 인덱스와 이전 부분 인덱스가 발견됐습니다.
   샘플 도구가 실제 수치 셀을 확인하고 캐시 없이 최대 3회 재분석하며, 완전한 새 결과가 확인된 뒤 이전 부분 인덱스만 정리합니다.

## 검증의 한계

이 결과는 위 Windows·GPU 환경과 포함된 가상 샘플에 대한 것입니다.
macOS/Linux 수동 설치, 다른 GPU·사내 네트워크, OpenAI 계정의 모델 권한·과금은 이번 새 클론 검증 범위에 포함하지 않았습니다.
4B 모델의 모든 질문·모든 Excel에 대한 정확도를 보장하지 않으므로 답변은 원본 셀과 대조합니다.
샘플 BI는 원본 셀과 manifest로 직접 계산하며, LLM 지표 추출 성공과 구분합니다.

다음 실습은 [온보딩](ONBOARDING.md), [샘플 데이터](SAMPLE_DATA.md)를 참고하세요.
