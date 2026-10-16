# 설정과 데이터 저장 위치

`.env.example`은 설명용 기본값, `.env`는 개인 실행 설정입니다. 설정 변경 후 앱을 재시작합니다.

| 설정 | 의미 |
| --- | --- |
| `PGVECTOR_URL` | 수동 기본 5432, Windows 자동 프로필 `postgresql://postgres@127.0.0.1:5433/rag_flow_light` |
| `DATABASE_URL` | 있으면 PGVECTOR_URL보다 우선. 다른 프로젝트의 터미널 변수를 확인 |
| `LLM_PROVIDER` / `VLM_PROVIDER` / `EMBEDDING_PROVIDER` | 단계별 `openai` / `llamacpp` |
| `OPENAI_API_KEY`, `OPENAI_*_MODEL` | 개인 API 키와 접근 가능한 모델 ID |
| `LOCAL_POSTGRES_AUTOSTART` | 기본 false, 자동 설치에서는 true |
| `LOCAL_POSTGRES_BIN` / `LOCAL_POSTGRES_DATA` / `LOCAL_POSTGRES_PORT` | PG 실행 파일·클러스터·포트. 연결 URL과 일치해야 함 |
| `LLAMA_CPP_AUTOSTART` | 로컬 GPU 자동 프로필에서는 true |
| `LLAMA_CPP_SERVER_PATH` | 설치 스크립트가 찾은 실제 llama-server.exe 경로 |
| `LLAMA_CPP_LLM_GGUF` / `LLAMA_CPP_VLM_GGUF` | Qwen GGUF. 같은 모델 서버를 공유 가능 |
| `LLAMA_CPP_MMPROJ` | VLM 모델과 짝이 맞는 projector |
| `LLAMA_CPP_EMBEDDING_GGUF` | BGE-M3 GGUF |
| `LLAMA_CPP_*_URL` / `LLAMA_CPP_*_MODEL` | 서버 `/v1` 주소와 `/models`의 별칭 |
| `LLAMA_CPP_EMBEDDING_DIMENSION` | BGE-M3 1024; 실제 모델 차원과 일치해야 함 |
| `LOCAL_WORKERS_ENABLED` | 기본 true; false이면 작업이 대기열에 남을 수 있음 |
| `DB_POOL_MIN_SIZE` / `DB_POOL_MAX_SIZE` | 프로세스별 연결 풀 기본 1 / 5 |
| `AUTH_ENABLED` | 개인 루프백 실습 기본 false |

환경 변수와 `.env`가 충돌하면 관련 변수를 정리한 새 터미널에서 실행하세요.
DB 비밀번호의 `@`, `:`, `/`, `#` 등은 URL 인코딩이 필요합니다.
임베딩 모델을 바꾸면 기존 인덱스를 새 모델로 검색할 수 없으므로 파일을 다시 적재합니다.

## 포트

| 포트 | 용도 |
| --- | --- |
| 8765 | FastAPI + 정적 프론트 |
| 5433 | 자동 설치한 프로젝트 PostgreSQL |
| 8081 | Qwen 텍스트·VLM |
| 8083 | BGE-M3 임베딩 |
| 5173 | 프론트 개발 서버를 켰을 때만 사용 |

`run.py`는 자동 실행을 켠 서비스와 네 종류의 로컬 워커를 관리합니다.
직접 uvicorn을 실행하면 로컬 DB·모델 자동 시작은 수행하지 않습니다.
종료할 때 이번 실행이 시작한 서비스만 정리합니다.

## 저장 위치

| 경로 | 내용 | Git 포함 |
| --- | --- | --- |
| `examples/bi/` | 가상 기업 18개 Excel·manifest·추가 수치 JSON | 예 |
| `examples/sample_financials.xlsx` | 소형 업로드·RAG 연습 파일 | 예 |
| `dist/` | 일반 실행용 정적 프론트 | 예 |
| `.runtime/` | 설치 파일·PostgreSQL·llama.cpp 바이너리 | 아니오 |
| `models/` | GGUF·mmproj·다운로드 캐시 | 아니오 |
| `data/postgres/` | PostgreSQL 클러스터 | 아니오 |
| `data/source_files/` | 업로드 Excel 복사본 | 아니오 |
| `data/artifacts/spreadsheets/` | 셀·시트·이미지 중간 결과 | 아니오 |
| `data/artifacts/embeddings/` | 임베딩 산출물 | 아니오 |
| `data/runs/`, `data/workflows/`, `data/cache/` | 실행 기록·사용자 워크플로·캐시 | 아니오 |
| `data/chat_uploads/` | 대화 첨부 | 아니오 |
| `logs/llama-vlm.log`, `logs/llama-embedding.log` | 로컬 모델 로그 | 아니오 |
| `data/postgres-server.log` | 자동 시작한 PG 로그 | 아니오 |

벡터·작업 큐·대화·BI·기업 비교 스냅샷은 PostgreSQL에 저장됩니다.
파일 폴더만 복사하면 DB의 벡터와 대화까지 복사되는 것은 아닙니다.
학생 간 공유에는 공개 샘플을 쓰고 개인 업로드와 `.env`는 공유하지 않습니다.
