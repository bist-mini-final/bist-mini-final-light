# BIST Mini Final Light

**Excel RAG·BI 온보딩용 저장소**입니다.
Excel 업로드, 셀 근거 답변, 재무 대시보드와 기업 비교를 실습합니다.
Docker·Kubernetes 없이 실행하며, 정적 프론트가 포함되어 **일반 실행에 Node.js는 필요 없습니다.**

처음이라면 [온보딩 안내](docs/ONBOARDING.md)를 순서대로 따라 하세요.
명령은 저장소 루트에서 실행합니다. Windows는 `C:\Repos\bist-mini-final-light` 같은 영문 경로를 사용하세요.

## 실행 방식 선택

| 방식 | 필요한 것 | DB와 모델 준비 |
| --- | --- | --- |
| Windows 로컬 GPU | Git, uv/Python 3.12, PowerShell 7, NVIDIA GPU·드라이버 | 프로젝트 PostgreSQL·pgvector, CUDA llama.cpp와 Qwen VL/BGE-M3 자동 설치 |
| Windows OpenAI | Git, uv/Python 3.12, PowerShell 7, API 키·사용 가능한 모델 | `-DatabaseOnly`로 프로젝트 DB 설치, 모델은 API 사용 |
| macOS/Linux 또는 기존 DB | Git, uv/Python 3.12, PostgreSQL·pgvector, OpenAI 또는 기존 llama.cpp 서버 | [수동 설치](docs/SETUP.md) |

로컬 GPU는 VRAM 8GB 이상·RAM 16GB 이상·여유 디스크 20GB 이상을 권장합니다.
실제 사용량은 모델과 컨텍스트에 따라 달라집니다. GPU가 없다면 OpenAI 경로를 선택하세요.

## 1. 공통 준비

[Git](https://git-scm.com/downloads), [uv](https://docs.astral.sh/uv/getting-started/installation/),
[PowerShell 7](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows)을 설치한 뒤 새 터미널을 엽니다.
Python은 uv로 설치할 수 있습니다.

```powershell
git clone https://github.com/bist-mini-final/bist-mini-final-light.git C:\Repos\bist-mini-final-light
cd C:\Repos\bist-mini-final-light
uv python install 3.12
uv sync --frozen
```

가상환경 활성화 없이 이후에도 `uv run`을 사용합니다.

## 2-A. Windows 로컬 GPU

```powershell
pwsh -File scripts/setup_local_windows.ps1
uv run python scripts/check_environment.py
uv run python run.py
```

설치 스크립트가 PostgreSQL 16·pgvector, CUDA llama.cpp, **Qwen3-VL 4B + BGE-M3**를 받고 `.env`를 작성합니다.
다운로드는 수 GB이므로 처음에는 기다려야 합니다. 기존 시스템 PostgreSQL은 수정하지 않습니다.
기존 Qwen3.5 모델 재사용은 [로컬 모델 안내](docs/LOCAL_MODELS.md)를 참고하세요.

## 2-B. Windows OpenAI

```powershell
pwsh -File scripts/setup_local_windows.ps1 -DatabaseOnly
notepad .env
```

`OPENAI_API_KEY`와 계정에서 사용할 수 있는 `OPENAI_LLM_MODEL`, `OPENAI_VLM_MODEL`,
`OPENAI_EMBEDDING_MODEL`을 입력합니다. VLM은 이미지 입력·구조화 출력을 지원해야 합니다.
기본 모델 ID의 계정별 접근 권한은 보장하지 않습니다. OpenAI 사용료가 발생합니다.

```powershell
uv run python scripts/check_environment.py
uv run python run.py
```

기존 DB 또는 macOS/Linux는 [설치 안내](docs/SETUP.md)를 따르세요.
앱 실행 터미널을 켜 두고, 종료할 때 `Ctrl+C`를 누릅니다.

## 3. 정상 실행 확인

- [설정 화면](http://127.0.0.1:8765/settings): DB 연결, 모델 제공자·ID, 서버 연결 확인
- [준비 상태](http://127.0.0.1:8765/readyz): HTTP 200 확인. 모델 응답까지 보장하는 것은 아닙니다.
- [API 문서](http://127.0.0.1:8765/docs): API 입력·출력 확인

별도 터미널에서 `uv run python scripts/check_environment.py --online`으로 API·DB·모델 준비 상태를 검사합니다.
설정 화면에서 제공자를 바꾸면 **모델 설정 저장 → 앱 종료 → 재실행**합니다.
임베딩 모델을 바꾸면 Excel도 다시 적재합니다.

## 4. 가상 데이터로 첫 실습

**가상 데이터 저장 위치: [`examples/bi/`](examples/bi/README.md)**

18개 가상 기업 × 재무제표 3개 시트 × FY2021–FY2025입니다. 유료 원본 서식은 포함하지 않습니다.
첫 파일은 [`01_amesoft.xlsx`](examples/bi/01_amesoft.xlsx)입니다.
앱을 실행한 상태에서 별도 터미널로 먼저 한 기업을 준비합니다.

```powershell
uv run python scripts/load_bi_samples.py --limit 1
```

`Ready: Demo Amesoft (ready, 5 years)`를 확인합니다.
데이터 소스와 BI에서 Demo Amesoft를 확인하세요. 챗봇에서 기업명을 포함해
`Demo Amesoft의 2025년 매출은 얼마인가요?`라고 질문합니다.
기대값은 약 **13,698.602 USD 백만**, 근거는 `Income Statement!F6`입니다.

전체 기업과 기업 비교는 다음으로 준비합니다.

```powershell
uv run python scripts/load_bi_samples.py
```

BI의 **카드 추가**로 히트맵을 켜고, 기업 비교에서 두 기업을 선택하세요.
샘플 BI는 실제 셀에서 직접 계산합니다. **LLM 지표 추출 결과가 아닙니다.**
RAG 추출 실습은 **데이터 초기화 및 재생성**으로 별도 진행합니다.
소형 `examples/sample_financials.xlsx`는 업로드 연습용이며 모든 BI 지표를 갖추지 않았습니다.

## 문서와 코드 안내

| 문서 | 내용 |
| --- | --- |
| [온보딩](docs/ONBOARDING.md) | 필수 도구 설치 → 첫 실행 → 실습 완료 |
| [설치·문제 해결](docs/SETUP.md) | OS별 DB 설치, 포트·권한·모델 오류 |
| [로컬 모델](docs/LOCAL_MODELS.md) | GPU, GGUF·mmproj·별칭·기존 서버 |
| [설정·데이터 위치](docs/CONFIGURATION.md) | 환경 변수, 포트, 파일·로그 위치 |
| [샘플 데이터](docs/SAMPLE_DATA.md) | 가상 파일, 테스트 질문과 기대값 |
| [코드 구조](docs/ARCHITECTURE.md) | 폴더 역할, 데이터 흐름, 수정 지점 |
| [개발·검사](docs/DEVELOPMENT.md) | 프론트 빌드, 테스트, docstring 규칙 |
| [점검 결과](docs/READINESS.md) | 확인 범위와 환경 의존성 |
| [새 클론 검증](docs/CLEAN_INSTALL_VERIFICATION.md) | README 설치·샘플 적재·셀 근거 답변·기업 비교 실제 결과 |

전체 문서 목록은 [docs/README.md](docs/README.md), 실습 과제는 [LEARNING.md](docs/LEARNING.md)에 있습니다.
각 주요 디렉터리의 `README.md`에도 진입 파일과 관련 검사 방법을 정리했습니다.

## 출처

[bist-mini-final](https://github.com/bist-mini-final/bist-mini-final)의 커밋 `0e0d7638b96c9f9db816c3959cec6064a40b5045`를 기반으로 정리했습니다.
원본 제작: **Team ColdPlay — 김지환, 전명준, 권혁준, 김정원**.
[경량판의 변경 범위](docs/CHANGES.md)를 참고하세요.
