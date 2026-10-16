# modules/embedding

셀 텍스트와 질문의 벡터를 만듭니다. 제공자·모델·차원을 저장 인덱스와 맞춥니다.

## 먼저 볼 파일

- [cell_text_embedder.py](cell_text_embedder.py)
- [query_embedder.py](query_embedder.py)

## 작업과 검사

명령은 저장소 루트 기준입니다. Python 변경은 해당 tests 영역의 pytest·ruff·pyright를 실행합니다.
프론트 변경은 frontend에서 npm run check로 검사하고 루트 dist를 함께 갱신합니다.
구체적인 명령은 [개발 안내](../../docs/DEVELOPMENT.md), 전체 연결은 [코드 구조](../../docs/ARCHITECTURE.md)를 참고하세요.
