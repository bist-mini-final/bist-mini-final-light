# frontend/src/features/settings

모델 제공자·서버·별칭 입력, DB 연결 상태, 읽기 전용 RAG 설정을 표시합니다. 저장 후 앱 재시작이 필요합니다.

## 먼저 볼 파일

- [SettingsView.tsx](SettingsView.tsx)
- [InferenceSettingsPanel.tsx](InferenceSettingsPanel.tsx)
- [settings.css](settings.css)
- [__tests__/](__tests__/)

## 작업과 검사

명령은 저장소 루트 기준입니다. Python 변경은 해당 tests 영역의 pytest·ruff·pyright를 실행합니다.
프론트 변경은 frontend에서 npm run check로 검사하고 루트 dist를 함께 갱신합니다.
구체적인 명령은 [개발 안내](../../../../docs/DEVELOPMENT.md), 전체 연결은 [코드 구조](../../../../docs/ARCHITECTURE.md)를 참고하세요.
