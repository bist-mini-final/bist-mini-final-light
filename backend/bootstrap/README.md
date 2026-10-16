# backend/bootstrap

도메인·저장소·모델 의존성을 조립하고 자원 수명과 로컬 서비스를 관리합니다.

## 먼저 볼 파일

- [application.py](application.py)
- [runtime.py](runtime.py)
- [lifecycle.py](lifecycle.py)
- [local_services.py](local_services.py)
- [schema.py](schema.py)
- [sample_data.py](sample_data.py)

## 작업과 검사

명령은 저장소 루트 기준입니다. Python 변경은 해당 tests 영역의 pytest·ruff·pyright를 실행합니다.
프론트 변경은 frontend에서 npm run check로 검사하고 루트 dist를 함께 갱신합니다.
구체적인 명령은 [개발 안내](../../docs/DEVELOPMENT.md), 전체 연결은 [코드 구조](../../docs/ARCHITECTURE.md)를 참고하세요.
