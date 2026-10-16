# 개발·검사·문서 작성

명령은 저장소 루트에서 실행합니다. 처음 준비는 [ONBOARDING.md](ONBOARDING.md)를 따릅니다.

## Python 검사

```powershell
uv sync --frozen
uv run pytest -q
uv run ruff check modules backend jobs scripts tests run.py
uv run pyright
```

DB 통합 검사는 `INTEGRATION_DATABASE_URL`이 없으면 건너뜁니다.
전용 테스트 DB와 vector 확장을 준비한 뒤 주소를 설정합니다.

```powershell
$env:INTEGRATION_DATABASE_URL='postgresql://test_user:YOUR_PASSWORD@127.0.0.1:5433/rag_flow_test'
uv run pytest -q
Remove-Item Env:INTEGRATION_DATABASE_URL
```

수정한 영역부터 `uv run pytest tests/bi tests/company_comparison -q`처럼 검사합니다.
복잡도 기준은 `tests/modules/test_complexity_budget.py`에 있습니다.

## 프론트

Node.js 22 이상을 설치하고 새 터미널에서 실행합니다.

```powershell
cd frontend
npm ci
npm run check
```

lint·타입·테스트·빌드를 수행합니다. 결과는 루트 `dist/`이며 일반 실행용으로 함께 커밋합니다.
`dist/`를 직접 수정하지 않습니다. 실시간 개발은 API를 켜 두고 `npm run dev`를 사용합니다.
개발 주소는 5173, API 프록시는 8765입니다. 정적 빌드를 바꾸면 브라우저도 새로고침합니다.

## DB 변경

일반 실행은 새 실습 DB를 멱등 초기화합니다. 버전별 실습은 `uv run alembic upgrade head`를 사용합니다.
자동 초기화된 DB를 무조건 stamp하지 말고 실제 스키마와 이력을 먼저 대조합니다.
테이블을 추가하면 마이그레이션과 로컬 초기화 양쪽을 확인합니다.
기업 비교에는 `domain_snapshots`와 `domain_snapshot_heads`가 모두 필요합니다.

## Docstring·README 규칙

- 모듈 첫 줄에는 책임을, 공개 함수·클래스에는 필요한 입력·출력·실패 조건을 설명합니다.
- DB 변경, 파일 덮어쓰기, 서비스 시작/종료, 비용이 드는 호출 등 부작용은 명시합니다.
- 이름이나 대입을 반복하는 주석을 대량 추가하지 않습니다.
- 컴포넌트·훅에는 역할과 사용자가 알아야 하는 상태·부작용을 설명합니다.
- 설정을 바꾸면 `.env.example`과 해당 디렉터리 README·사용 문서를 함께 수정합니다.
- 명령의 실행 디렉터리를 명시하고 키·개인 비밀번호를 넣지 않습니다.

`.agents/rules/code-style-guide.md`의 Decimal 계산, Pydantic 계약, 모듈 기반 클래스를 유지합니다.
의미 있는 회귀 검사와 실제 API/화면 확인을 마친 뒤 문서 링크·예제 경로·Git 포함 파일도 점검합니다.
