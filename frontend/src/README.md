# frontend/src

라우팅·페이지·기능 화면·공통 UI·스타일을 분리한 React 소스입니다.

## 먼저 볼 파일

- [app/](app/)
- [pages/](pages/)
- [features/](features/)
- [shared/](shared/)
- [styles/](styles/)
- [test/](test/)

## 작업과 검사

명령은 저장소 루트 기준입니다. Python 변경은 해당 tests 영역의 pytest·ruff·pyright를 실행합니다.
프론트 변경은 frontend에서 npm run check로 검사하고 루트 dist를 함께 갱신합니다.
구체적인 명령은 [개발 안내](../../docs/DEVELOPMENT.md), 전체 연결은 [코드 구조](../../docs/ARCHITECTURE.md)를 참고하세요.
