# examples

공개 가상 테스트 데이터입니다. 전체 BI 실습은 bi/의 18개 파일을 사용합니다. sample_financials.xlsx는 소형 업로드 연습용입니다.

## 먼저 볼 파일

- [bi/README.md](bi/README.md)
- [sample_financials.xlsx](sample_financials.xlsx)
- [generate_sample.py](generate_sample.py)

## 작업과 검사

명령은 저장소 루트 기준입니다. Python 변경은 해당 tests 영역의 pytest·ruff·pyright를 실행합니다.
프론트 변경은 frontend에서 npm run check로 검사하고 루트 dist를 함께 갱신합니다.
구체적인 명령은 [개발 안내](../docs/DEVELOPMENT.md), 전체 연결은 [코드 구조](../docs/ARCHITECTURE.md)를 참고하세요.
