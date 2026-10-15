# 코드를 읽는 순서

전체를 한 번에 읽기보다 Excel 한 파일과 질문 한 개가 이동하는 경로를 따라갑니다.

1. `run.py` → `backend/entrypoints/asgi.py` → `backend/bootstrap/http.py`: FastAPI 앱이 만들어지고 API·정적 프론트가 연결되는 지점입니다.
2. `backend/bootstrap/application.py`: DB 저장소, 모듈 레지스트리, 실행 서비스가 조립됩니다. `lifecycle.py`와 `local_workers.py`에서 로컬 워커의 수명을 관리합니다.
3. `jobs/excel_ingestion.py`: Excel 입력에서 구조 분석, 셀 직렬화, 임베딩, pgvector 적재까지 모듈의 연결을 확인합니다.
4. `jobs/rag_pipeline.py`: 질문 분해, 임베딩, 벡터·키워드 검색, RRF 결합, 문맥 확장, 답변 생성 순서를 확인합니다.
5. `modules/`: 각 모듈의 입력·출력 Pydantic 모델과 `execute()`를 읽습니다. 공통 실행·외부 모델 호출 처리는 `modules/common`에 모여 있습니다.
6. `backend/domains/workflow/`: 그래프 검증, 실행 상태 저장, 재시도·취소가 어떤 역할로 나뉘는지 확인합니다.
7. `frontend/src/features/`: 데이터 소스, 플레이그라운드, 챗봇, BI 화면이 API와 연결되는 부분을 확인합니다.

## 질문 하나의 흐름

```text
브라우저 → FastAPI → PostgreSQL 작업 큐 → 로컬 workflow 워커
                                       ↓
              질문 분해 → 하이브리드 검색 → 근거 확장 → 답변
                                       ↓
브라우저 ← SSE 상태·결과 ← PostgreSQL 실행 상태
```

프로세스를 나눈 이유는 Excel 처리·외부 API 호출이 오래 걸려도 화면 요청을 계속 처리하기 위해서입니다.
학생이 별도 워커 명령을 실행할 필요는 없습니다. API가 함께 관리합니다.
DB 큐는 실행 상태·재시작·취소를 유지하기 위한 부분이므로 남겼습니다.

## 단계별 연습

- `/docs`에서 모듈 목록과 워크플로 조회 API를 호출하고 프론트의 네트워크 응답과 비교합니다.
- `examples/generate_sample.py`의 합성 매출 값을 바꾼 새 Excel 파일을 만들어 처리 결과를 비교합니다.
- `examples/bi/README.md`에 따라 18개 가상 기업을 적재하고 성장·정체·하락 기업의 6종 BI 카드를 비교합니다. 셀 기반 샘플 대시보드와 RAG로 재생성한 결과의 지표 값·근거를 대조합니다.
- 플레이그라운드에서 검색 개수를 바꾸고 근거와 답변이 어떻게 달라지는지 확인합니다.
- `tests/modules/test_rrf_fusion.py`를 읽고 벡터 검색과 키워드 검색의 결합을 이해합니다.
- 모듈 하나의 입력 검증 또는 에러 처리를 개선하고 관련 테스트를 실행합니다.

API 키 없이 시작할 때는 화면 탐색, Pydantic 계약, 그래프 검증, 순수 함수 테스트부터 진행하면 됩니다.
숫자 계산은 원본의 `Decimal` 기반 방식을 유지합니다. 재무 계산을 수정할 때 단순한 `float` 합산으로 바꾸지 마세요.
