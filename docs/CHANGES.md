# 원본과 경량판의 차이

원본 기준 커밋: `0e0d7638b96c9f9db816c3959cec6064a40b5045`.
원본 저장소: <https://github.com/bist-mini-final/bist-mini-final>.

| 유지 | 경량판에서 변경·제외 |
| --- | --- |
| Excel 구조 분석·셀 근거·RAG 모듈 | Kubernetes·k3d·Helm·KEDA 배포 파일과 렌더러 제외 |
| PostgreSQL·pgvector·FTS·작업 큐 | DB 큐를 로컬 Python 작업 프로세스가 처리 |
| React 화면·FastAPI API | 정적 빌드를 FastAPI가 제공; Node는 화면 수정 시에만 필요 |
| 챗봇·플레이그라운드·BI·기업 비교·벤치마크 코드 | 클러스터 ScaledJob·Job·Pod 관제 화면과 API 제외 |
| 진행률 SSE·실행 기록·재시도·취소 | Redis 중계 제거, 단일 API가 DB 상태를 관찰 |
| 핵심 모듈·서비스 테스트, Alembic | 클러스터 배포 계약·Redis 전용 테스트 제외 |
| 원본 제작자 표기 | 대용량 GIF·MP4, 과거 평가 원본, 운영·배포 보고서 제외 |

앱 실행을 위한 Dockerfile·Compose·Nginx 설정도 없습니다.
GitHub Actions의 자동 테스트에는 임시 PostgreSQL·pgvector 서비스를 사용하지만, 학생의 로컬 실행에는 컨테이너가 필요 없습니다.
원본의 커밋 이력·대용량 미디어를 함께 복제하지 않고 학습판 코드의 별도 이력을 시작합니다.
기존 원본의 DB를 연결하는 마이그레이션 용도가 아닌 새 실습 DB를 기준으로 합니다.
