# scripts

처음 설치·모델 다운로드·설정·환경 점검·샘플 적재를 위한 명령입니다. 설치는 파일을 다운로드하고 .env를 선택 프로필로 변경합니다.

## 먼저 볼 파일

- [setup_local_windows.ps1](setup_local_windows.ps1)
- [configure_local.py](configure_local.py)
- [download_models.py](download_models.py)
- [download_runtime.py](download_runtime.py)
- [download_model_ranges.py](download_model_ranges.py)
- [check_environment.py](check_environment.py)
- [load_bi_samples.py](load_bi_samples.py)
- [sample_ingestion.py](sample_ingestion.py): 샘플 세 시트의 적재 완전성과 부분 결과 재시도

## 작업과 검사

명령은 저장소 루트 기준입니다. Python 변경은 해당 tests 영역의 pytest·ruff·pyright를 실행합니다.
프론트 변경은 frontend에서 npm run check로 검사하고 루트 dist를 함께 갱신합니다.
구체적인 명령은 [개발 안내](../docs/DEVELOPMENT.md), 전체 연결은 [코드 구조](../docs/ARCHITECTURE.md)를 참고하세요.

## 자주 실행하는 명령

```powershell
# 로컬 GPU 전체 설치 (다운로드 및 .env 변경)
pwsh -File scripts/setup_local_windows.ps1
# GPU 없는 OpenAI용 DB 설치
pwsh -File scripts/setup_local_windows.ps1 -DatabaseOnly
# 파일·설정 확인만 수행
uv run python scripts/check_environment.py
# 앱을 켠 뒤 API·DB·로컬 모델 준비 상태 확인
uv run python scripts/check_environment.py --online
# 첫 샘플 / 전체 샘플 적재 (VLM·임베딩 실행)
uv run python scripts/load_bi_samples.py --limit 1
uv run python scripts/load_bi_samples.py
```

`configure_local.py`는 .env의 DB·제공자를 선택 프로필로 바꾸며 개인 키를 보존합니다.
`download_models.py`는 GGUF 다운로드만 수행합니다.
샘플 적재 명령은 일반 업로드·임베딩을 수행하고 실제 셀 기반 BI를 발행합니다.
