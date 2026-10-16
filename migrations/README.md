# migrations

Alembic 스키마 이력입니다. 새 실습 DB의 기본 테이블은 앱이 자동 초기화합니다. 버전 실습은 별도 DB에서 수행하세요.

## 먼저 볼 파일

- [env.py](env.py)
- [versions/](versions/)

## 작업과 검사

명령은 저장소 루트 기준입니다. Python 변경은 해당 tests 영역의 pytest·ruff·pyright를 실행합니다.
프론트 변경은 frontend에서 npm run check로 검사하고 루트 dist를 함께 갱신합니다.
구체적인 명령은 [개발 안내](../docs/DEVELOPMENT.md), 전체 연결은 [코드 구조](../docs/ARCHITECTURE.md)를 참고하세요.
