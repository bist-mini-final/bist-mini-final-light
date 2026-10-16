# 문서 안내

처음 실행: **[온보딩](ONBOARDING.md) → [샘플 실습](SAMPLE_DATA.md)**.
처음 수정: **[구조](ARCHITECTURE.md) → [개발](DEVELOPMENT.md) → [연습 과제](LEARNING.md)**.

| 문서 | 내용 |
| --- | --- |
| [ONBOARDING.md](ONBOARDING.md) | 도구 설치부터 첫 실습까지 |
| [SETUP.md](SETUP.md) | OS별 수동 DB 설치와 오류 해결 |
| [LOCAL_MODELS.md](LOCAL_MODELS.md) | GPU 모델, 서버·별칭, 제공자 전환 |
| [CONFIGURATION.md](CONFIGURATION.md) | 환경 변수, 포트, 파일·로그 위치 |
| [SAMPLE_DATA.md](SAMPLE_DATA.md) | 가상 데이터 위치와 기대값 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 폴더 역할과 데이터 흐름 |
| [DEVELOPMENT.md](DEVELOPMENT.md) | 빌드·검사·docstring 규칙 |
| [READINESS.md](READINESS.md) | 확인 범위와 환경 의존성 |
| [LEARNING.md](LEARNING.md) | 코드 읽기와 연습 과제 |
| [CHANGES.md](CHANGES.md) | 원본과 경량판의 차이 |

설정 기본값은 `.env.example`, 의존성은 `pyproject.toml`·`uv.lock`·`frontend/package-lock.json`이 기준입니다.
문서에 개인 키·DB 비밀번호·개인 PC 모델 경로를 넣지 않습니다.
