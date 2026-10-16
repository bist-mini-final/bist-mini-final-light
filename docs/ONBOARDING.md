# 처음부터 따라 하는 온보딩

목표: **앱 실행 → 샘플 적재 → 셀 근거 답변 → BI → 두 기업 비교**.
명령은 한 줄씩 실행합니다. 서버가 실행 중이면 다음 명령은 새 터미널에서 실행하세요.
일반 실행에는 프론트 빌드나 가상환경 활성화가 필요 없습니다.

## 1. 도구 설치

| 도구 | 용도 | 설치·확인 |
| --- | --- | --- |
| Git | 저장소 다운로드 | [공식 설치](https://git-scm.com/downloads), `git --version` |
| uv | Python·패키지·가상환경 관리 | [공식 설치](https://docs.astral.sh/uv/getting-started/installation/), `uv --version` |
| Python 3.12 | API·작업 프로세스 | `uv python install 3.12` |
| PowerShell 7 | Windows 자동 설치 | [Microsoft 안내](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows), `pwsh --version` |
| PostgreSQL·pgvector | 벡터·작업·대화·BI 저장 | 자동 설치 또는 [수동 준비](SETUP.md) |
| NVIDIA 드라이버 | 로컬 GPU 선택 시에만 필요 | [공식 드라이버](https://www.nvidia.com/Download/index.aspx), `nvidia-smi` |
| Node.js 22 이상 | **프론트 수정 시에만** 필요 | [공식 다운로드](https://nodejs.org/en/download), `node --version`, `npm --version` |

Windows에서 WinGet을 쓸 수 있다면 다음으로 설치합니다.

```powershell
winget install --id Git.Git -e
winget install --id astral-sh.uv -e
winget install --id Microsoft.PowerShell -e
```

설치 후 터미널을 닫았다 다시 엽니다. `uv`, `pwsh`를 못 찾으면 새 터미널의 PATH를 확인합니다.
자동 설치에는 Windows의 `tar`도 필요합니다. `tar --version`으로 확인합니다.

## 2. 저장소 준비

```powershell
git clone https://github.com/bist-mini-final/bist-mini-final-light.git C:\Repos\bist-mini-final-light
cd C:\Repos\bist-mini-final-light
uv python install 3.12
uv sync --frozen
```

루트에 `run.py`, `.env.example`, `pyproject.toml`, `examples/`가 보여야 합니다.
Windows PostgreSQL 초기화는 한글 경로에서 실패할 수 있어 영문 경로를 권장합니다.
macOS/Linux는 원하는 경로에 clone한 뒤 같은 uv 명령을 실행합니다.

## 3. 설치 경로 선택

### A. Windows NVIDIA GPU

```powershell
pwsh -File scripts/setup_local_windows.ps1
```

`.runtime/postgres/`에 PostgreSQL 16·pgvector, `.runtime/llama/`에 CUDA llama.cpp,
`models/`에 Qwen3-VL 4B·mmproj·BGE-M3가 생깁니다. `.env`도 로컬 프로필로 작성됩니다.
NVIDIA 드라이버는 먼저 설치해야 하며 CUDA Toolkit은 별도 설치하지 않습니다.
다운로드가 수 GB이고 캐시도 공간을 사용합니다. GGUF 다운로드가 끊기면 같은 명령을 다시 실행합니다.
기존 모델 재사용은 [LOCAL_MODELS.md](LOCAL_MODELS.md)를 참고하세요.

### B. Windows OpenAI API

```powershell
pwsh -File scripts/setup_local_windows.ps1 -DatabaseOnly
notepad .env
```

`OPENAI_API_KEY`와 사용 가능한 `OPENAI_LLM_MODEL`, `OPENAI_VLM_MODEL`, `OPENAI_EMBEDDING_MODEL`을 입력합니다.
이 경로는 GPU 실행 파일과 GGUF를 받지 않고 DB만 설치합니다. 세 제공자는 `openai`가 됩니다.
설치 스크립트는 키를 지우지 않지만 **DB 주소와 제공자를 선택한 프로필로 변경**합니다.
기존 설정을 유지해야 한다면 `.env`를 먼저 개인 로컬 위치에 백업하세요.

### C. 기존 DB / macOS / Linux

[SETUP.md](SETUP.md)에 따라 DB와 확장을 준비한 뒤 `.env.example`을 `.env`로 복사합니다.
본인 DB 주소·제공자를 입력합니다. Windows 전용 설치 스크립트는 사용하지 않습니다.

## 4. 실행 전후 확인

```powershell
uv run python scripts/check_environment.py
uv run python run.py
```

`[FAIL]`이 있으면 안내부터 해결합니다. 점검 명령은 설치·DB 변경·답변 생성을 하지 않습니다.
`Uvicorn running on http://127.0.0.1:8765`가 나온 터미널은 켜 둡니다.
자동 프로필은 DB 클러스터·실습 DB·테이블을 필요한 경우 생성합니다.
로컬 모델 로딩은 API 시작보다 늦게 끝날 수 있습니다.

브라우저에서 <http://127.0.0.1:8765/settings>를 엽니다.
DB 연결을 확인하고 **서버 연결 확인**을 누릅니다. 이 버튼은 현재 적용된 설정을 검사합니다.
설정을 바꿨다면 **모델 설정 저장 → Ctrl+C로 앱 종료 → run.py 재실행**하세요.
별도 터미널에서 다음으로 API·DB·모델 별칭을 확인합니다.

```powershell
cd C:\Repos\bist-mini-final-light
uv run python scripts/check_environment.py --online
```

OpenAI 키 유무는 검사하지만 잔액·모델 접근 권한은 보장하지 않습니다.
터미널의 `DATABASE_URL`은 `.env`의 `PGVECTOR_URL`보다 우선합니다.

## 5. 첫 실습 완료하기

```powershell
uv run python scripts/load_bi_samples.py --limit 1
```

`Ready: Demo Amesoft`를 확인합니다. 데이터 소스에서 `01_amesoft.xlsx`를 찾습니다.
챗봇에서 해당 인덱스를 선택해 2025년 매출을 물어보고 `Income Statement!F6`을 대조하세요.
BI에서 Demo Amesoft를 선택합니다. 질문·기대값은 [SAMPLE_DATA.md](SAMPLE_DATA.md)에 있습니다.

```powershell
uv run python scripts/load_bi_samples.py
```

전체 18개를 준비하면 기업 비교에서 두 기업을 선택할 수 있습니다.
BI의 **카드 추가**로 히트맵을 켭니다. 샘플 BI는 셀 기반 계산이며,
RAG 지표 추출은 **데이터 초기화 및 재생성**으로 별도 실습합니다.

## 6. 다음 날 실행 / 업데이트

설치 스크립트를 매일 실행할 필요는 없습니다.

```powershell
cd C:\Repos\bist-mini-final-light
uv run python run.py
```

업데이트는 작업이 끝난 뒤 앱을 종료하고 실행합니다.

```powershell
git pull --ff-only
uv sync --frozen
uv run python run.py
```

직접 수정한 파일 때문에 pull이 거부되면 변경을 보존한 뒤 담당자와 확인하세요.
업데이트 후 브라우저도 새로고침합니다. `.env`, 모델·DB 데이터는 Git 업데이트 대상이 아닙니다.
오류 해결과 저장 위치는 [SETUP.md](SETUP.md), [CONFIGURATION.md](CONFIGURATION.md)를 참고하세요.
