# BIST Mini Final Light

IPP 근로학생이 Excel RAG와 BI 서비스 코드를 읽고 로컬에서 실습하는 학습·참고용 복사본입니다.
원본의 Excel 업로드, 구조 분석, 하이브리드 검색, 챗봇, 플레이그라운드, BI·기업 비교 기능을 유지합니다.

**PostgreSQL·pgvector를 준비한 뒤 FastAPI 한 번만 실행하면 됩니다.**
프론트 정적 빌드가 `dist/`에 포함되어 있어 일반 실행에는 Node.js가 필요하지 않습니다.
API가 로컬 작업 프로세스도 함께 시작·종료합니다.

## 처음 한 번 준비

필요한 것: Python 3.12, [uv](https://docs.astral.sh/uv/getting-started/installation/), PostgreSQL 16 이상과 pgvector 0.8 이상.

1. 저장소를 받고 Python 의존성을 설치합니다.

   ```bash
   git clone https://github.com/bist-mini-final/bist-mini-final-light.git
   cd bist-mini-final-light
   uv sync --frozen
   ```

2. PostgreSQL에 **실습 전용 DB**를 한 번 만듭니다. pgAdmin의 Query Tool이나 `psql`에서 실행합니다.

   ```sql
   CREATE DATABASE rag_flow_light;
   ```

   새 DB에 연결하여 실행합니다.

   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

   PostgreSQL·pgvector 설치가 아직 안 되어 있다면 [DB 준비 안내](docs/SETUP.md)를 먼저 확인하세요.

3. `.env.example`을 `.env`로 복사합니다.

   ```powershell
   # Windows PowerShell
   Copy-Item .env.example .env
   ```

   macOS/Linux에서는 `cp .env.example .env`를 사용합니다.
   `.env`의 DB 사용자·암호·주소를 본인 환경에 맞게 수정합니다.

   ```dotenv
   PGVECTOR_URL=postgresql://postgres:본인암호@localhost:5432/rag_flow_light
   OPENAI_API_KEY=본인키
   ```

   OpenAI 모드에서는 LLM 구조 분석·임베딩·답변 실행에 키가 필요하며 API 사용료가 발생합니다. 로컬 llama.cpp 모드에서는 OpenAI 키 없이 실행할 수 있습니다.

## 실행

```bash
uv run python run.py
```

- 화면: <http://127.0.0.1:8765>
- API 문서: <http://127.0.0.1:8765/docs>
- DB 연결 확인: <http://127.0.0.1:8765/readyz>
- 종료: 실행한 터미널에서 `Ctrl+C`

첫 실행 때 앱 테이블을 자동 생성합니다. 실습용 DB의 기존 테이블을 삭제하는 명령은 실행하지 않습니다.
기본 주소는 개인 PC의 루프백 주소이며 로그인은 꺼져 있습니다.
운영 서버나 공용 서비스로 배포하기 위한 구성이 아닙니다.

## 실습 순서

1. `examples/sample_financials.xlsx`를 데이터 소스에서 업로드하고 처리 상태를 확인합니다. 실제 기업 데이터가 아닌 합성 예제입니다.
2. 플레이그라운드에서 Excel 적재 파이프라인의 모듈 입력·출력을 읽어 봅니다.
3. 챗봇에서 `Example IPP Co의 2025년 Revenue는 얼마인가요?`처럼 질문하고 원본 셀 근거를 확인합니다.
4. BI 대시보드와 기업 비교에서 적재된 지표를 확인합니다. 지원되지 않는 엑셀 형태나 지표는 분석이 제한될 수 있습니다.

[코드 읽기 순서와 연습 과제](docs/LEARNING.md) · [설치·문제 해결](docs/SETUP.md) · [원본과 달라진 점](docs/CHANGES.md)

## OpenAI API 또는 로컬 GPU 모델

설정 화면에서 답변 생성, VLM, 임베딩의 제공자를 각각 선택할 수 있습니다.
로컬 기본 구성은 **Qwen3-VL 4B + BGE-M3**이며 CUDA llama.cpp를 사용합니다.
Windows에서 처음 한 번 `pwsh -File scripts/setup_local_windows.ps1`로 준비하면 이후에는 `uv run python run.py` 하나로 로컬 DB·모델 서버까지 함께 실행합니다.
상세 설정과 다른 제공자를 섞어 쓰는 방법은 [로컬 모델 안내](docs/LOCAL_MODELS.md)를 확인하세요.

## 프론트 코드를 수정할 때만

Node.js 22 이상에서 한 번 빌드하면 결과가 루트 `dist/`에 저장됩니다.

```bash
cd frontend
npm ci
npm run build
cd ..
uv run python run.py
```

화면을 실시간으로 수정하려면 FastAPI를 실행한 상태에서 별도 터미널로 `cd frontend` → `npm run dev`를 실행합니다.
개발 화면은 <http://127.0.0.1:5173>이며 `/api` 요청은 FastAPI로 전달됩니다.

## 검사

```bash
uv run pytest -q
uv run ruff check modules backend jobs tests run.py
uv run pyright
```

프론트 검사는 `frontend`에서 `npm run check`로 실행합니다.
DB 통합 검사는 실습 DB와 별도의 테스트 DB 주소를 `INTEGRATION_DATABASE_URL`에 지정해야 실행됩니다.

## 출처

[bist-mini-final](https://github.com/bist-mini-final/bist-mini-final)의 커밋 `0e0d7638b96c9f9db816c3959cec6064a40b5045`를 바탕으로 정리했습니다.
원본 제작: **Team ColdPlay — 김지환, 전명준, 권혁준, 김정원**.
원본 시연 영상·성과 보고·배포 자료는 원본 저장소에서 확인할 수 있습니다.
