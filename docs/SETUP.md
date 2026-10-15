# 로컬 환경 준비와 문제 해결

## PostgreSQL과 pgvector

PostgreSQL 16 이상과 pgvector 0.8 이상을 사용합니다. DB를 로컬에 설치하거나 접근 가능한 실습용 PostgreSQL 서버를 사용하세요.
앱 실행에 Docker, Compose, Kubernetes, Helm, KEDA, Redis는 사용하지 않습니다.
Windows에서 프로젝트 전용 DB와 GPU 모델을 함께 설치하려면 [로컬 모델 설치 안내](LOCAL_MODELS.md)를 사용하세요. 영문 경로에 저장소를 두고 설치하면 이후 `uv run python run.py` 하나로 실행할 수 있습니다.

- Windows: [PostgreSQL 설치 프로그램](https://www.postgresql.org/download/windows/)으로 DB를 설치합니다. pgvector는 별도 확장이므로 [공식 Windows 설치 안내](https://github.com/pgvector/pgvector#windows)를 따라 설치해야 합니다. 확장 빌드가 필요하면 담당자에게 실습 DB 준비를 요청해도 됩니다.
- macOS: [pgvector 공식 설치 안내](https://github.com/pgvector/pgvector#installation)의 Homebrew 또는 Postgres.app 방법을 참고합니다.
- Linux: 같은 공식 문서의 APT/Yum 패키지 또는 소스 설치 방법을 사용합니다.

관리자 계정으로 `rag_flow_light`를 만들고, 해당 DB에서 `CREATE EXTENSION IF NOT EXISTS vector;`를 실행합니다.
앱 계정은 실습 DB에 연결하고 테이블·인덱스를 만들 권한이 필요합니다.
여러 학생이 하나의 서버를 사용하면 학생마다 별도 DB와 계정을 만들어 `.env`를 다르게 설정하세요.

비밀번호에 `@`, `:`, `/`, `#` 등이 있으면 연결 URL에서 퍼센트 인코딩해야 합니다.
`.env`는 Git에서 제외됩니다. 개인 API 키와 DB 비밀번호를 문서나 코드에 넣지 마세요.

## 실행 방식

`uv sync --frozen` 후 `uv run python run.py`를 사용합니다.
또는 `uv run uvicorn backend.entrypoints.asgi:app --host 127.0.0.1 --port 8765`로 직접 실행할 수 있습니다.

API 시작 시 스키마 초기화가 끝난 뒤 workflow, BI materialization, BI question, benchmark 큐를 처리하는 로컬 프로세스 네 개를 자동 시작합니다.
기본적으로 큰 Excel 파일의 추가 샤드 워커는 사용하지 않습니다.
진행률은 PostgreSQL을 관찰하는 SSE 스트림으로 전달합니다.

개발 중에는 `--reload`를 붙일 수 있습니다. 서버가 다시 시작되면 로컬 워커도 교체됩니다.
개인 실습에서는 API 프로세스 하나만 실행하세요. `--workers`로 여러 API 프로세스를 실행할 필요가 없습니다.
실행 중인 작업은 서버 종료 시 중단될 수 있습니다. 강제 종료된 작업의 DB lease는 약 180초 후 다시 처리할 수 있습니다.
작업을 시작한 채 서버를 반복 재시작하면 외부 모델 호출이 반복될 수 있습니다.

`.env` 설정:

| 설정 | 기본값·의미 |
| --- | --- |
| `PGVECTOR_URL` | 실습 DB 연결 URL |
| `OPENAI_API_KEY` | OpenAI 실행 방식을 선택한 기능에 필요한 키 |
| `LOCAL_WORKERS_ENABLED` | `true`; `false`면 API 조회만 실행하며 작업은 큐에 남습니다 |
| `DB_POOL_MIN_SIZE` / `DB_POOL_MAX_SIZE` | 각 프로세스의 DB 연결 수, `1` / `5` |
| `INGESTION_SHARDS_ENABLED` | `false`; 고급 실습 시에만 활성화 |

`DATABASE_URL` 환경 변수가 있으면 `PGVECTOR_URL`보다 우선합니다. 의도하지 않은 DB로 연결되면 터미널의 해당 변수도 확인하세요.
업로드·중간 결과·실행 기록 파일은 `data/` 아래에 생기고 Git에서 제외됩니다.
DB 스키마 변경을 실습할 때는 Alembic 마이그레이션도 유지하고 있으므로 `uv run alembic upgrade head`를 사용할 수 있습니다.

## 자주 만나는 문제

| 증상 | 확인할 내용 |
| --- | --- |
| PostgreSQL에 연결할 수 없다는 시작 오류 | DB 서비스 실행 여부, `.env`의 포트·DB 이름·계정·암호 |
| `extension "vector" is not available` | PostgreSQL 서버에 pgvector 확장 파일을 먼저 설치했는지 확인 |
| `permission denied` 또는 스키마 초기화 실패 | 앱 계정의 테이블·인덱스 생성 권한 및 실습 전용 DB 연결 여부 |
| 화면이 503 / Frontend assets are not available | 저장소의 `dist/index.html` 확인; 프론트 수정 후에는 `npm run build` |
| 업로드·질문이 계속 대기 | FastAPI 터미널의 로컬 워커 로그와 `LOCAL_WORKERS_ENABLED` 확인 |
| 키 관련 오류, 401 또는 모델 권한 오류 | 개인 API 키·잔액·모델 접근 권한 확인 |
| 포트 8765 사용 중 | 기존 실행을 종료하거나 직접 uvicorn 명령의 `--port` 변경 |

프론트 정적 빌드는 서버 시작 전에 준비되어 있어야 합니다. 프론트 변경 후 API도 재시작하세요.
원본처럼 특정 재무 엑셀 형식에 맞춘 기능이 있어 모든 Excel 파일에서 BI가 동일하게 작동하지는 않습니다.
