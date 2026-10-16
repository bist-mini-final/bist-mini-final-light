# modules

파이프라인 개별 작업의 유일한 구현 위치입니다. backend 안에 같은 모듈을 중복 작성하지 않습니다.

## 먼저 볼 파일

- [common/](common/)
- [registry.py](registry.py)
- [reader/](reader/)
- [structure/](structure/)
- [embedding/](embedding/)
- [retrieval/](retrieval/)
- [query/](query/)
- [storage/](storage/)

## 작업과 검사

명령은 저장소 루트 기준입니다. Python 변경은 해당 tests 영역의 pytest·ruff·pyright를 실행합니다.
프론트 변경은 frontend에서 npm run check로 검사하고 루트 dist를 함께 갱신합니다.
구체적인 명령은 [개발 안내](../docs/DEVELOPMENT.md), 전체 연결은 [코드 구조](../docs/ARCHITECTURE.md)를 참고하세요.
