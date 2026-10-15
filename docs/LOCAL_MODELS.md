# OpenAI API와 GPU llama.cpp 선택

설정 화면의 **모델 실행 방식**에서 답변 생성·질문 분해, VLM, 임베딩을 각각 `OpenAI API` 또는 `로컬 llama.cpp`로 선택합니다.
저장 후 FastAPI를 종료하고 `uv run python run.py`로 다시 실행해야 API와 워커에 같은 설정이 적용됩니다.
OpenAI 키는 `.env`의 `OPENAI_API_KEY`에 넣으며 브라우저에 반환하지 않습니다.

## 기본 로컬 모델

| 기능 | 모델·양자화 | API | 모델 별칭 |
| --- | --- | --- | --- |
| 답변 생성·질문 분해·VLM | Qwen3-VL-4B-Instruct Q4_K_M, mmproj Q8_0 | `http://127.0.0.1:8081/v1` | `qwen3-vl-4b` |
| 임베딩 | BGE-M3 Q8_0, 1024차원 | `http://127.0.0.1:8083/v1` | `bge-m3` |

Qwen 서버 하나를 텍스트와 이미지 분석이 공유하며 두 개의 Qwen 모델을 동시에 올리지 않습니다.
로컬 모델은 OpenAI API로 자동 우회하지 않습니다. 서버가 꺼져 있거나 출력 형식이 잘못되면 해당 작업에 오류가 표시됩니다.
로컬 호출의 API 사용료는 0으로 기록하며 GPU·전력 비용을 계산하지는 않습니다.
도구를 사용하는 답변은 도구 실행 후 별도 요청으로 최종 JSON을 생성합니다. 도구 문법과 JSON 출력 제약을 동시에 처리하지 못하는 llama.cpp 템플릿에 대응하며 두 요청의 토큰 사용량을 함께 기록합니다.

## Windows 처음 한 번 설치

Python 3.12, uv, NVIDIA GPU 드라이버가 준비된 PC에서 실행합니다.
Windows에서는 PostgreSQL 초기화 시 한글 경로 오류가 발생할 수 있으므로 `C:\Repos\bist-mini-final-light` 같은 영문 경로에 저장소를 받으세요.
앱 폴더를 옮길 수 없다면 `.env`의 `LOCAL_POSTGRES_BIN`, `LOCAL_POSTGRES_DATA`에 영문 절대 경로를 지정하세요.

```powershell
pwsh -File scripts/setup_local_windows.ps1
uv run python run.py
```

설치 스크립트는 프로젝트의 `.runtime/`에 PostgreSQL 16·pgvector와 CUDA llama.cpp를 설치하고, `models/`에 GGUF를 받습니다.
기존 시스템 PostgreSQL은 변경하지 않으며 로컬 실습 DB는 5433 포트를 사용합니다.
DB는 루프백 주소에만 열리고 프로젝트 로컬 클러스터의 접속은 trust 방식입니다.
모델 다운로드가 중단되면 스크립트를 다시 실행해 재개할 수 있습니다.
이 폴더와 DB 데이터, `.env`는 Git에서 제외됩니다.

설치 후에는 **`uv run python run.py` 하나로** 프로젝트 DB, CUDA 모델 서버, FastAPI·프론트·워커가 시작됩니다.
처음 모델 로딩에는 시간이 걸릴 수 있습니다. 모델 실행 로그는 `logs/llama-vlm.log`, `logs/llama-embedding.log`에 기록합니다.
터미널에서 `Ctrl+C`를 누르면 이 실행이 시작한 서비스도 종료됩니다. 이미 별도로 실행 중이던 서버는 종료하지 않습니다.
GPU 메모리가 부족하면 Qwen 컨텍스트 크기를 줄이거나 수동 서버 실행 설정을 조정하세요.
자동 실행에서는 긴 사고 토큰 생성을 기본으로 끕니다. 이를 지원하는 모델에서 사고 모드를 사용하려면 `.env`에 `LLAMA_ARG_REASONING=on`을 지정하세요.

## 이미 실행 중인 llama.cpp 사용

자동 실행을 끄고 본인의 서버 주소·별칭을 설정할 수 있습니다.

```dotenv
LLM_PROVIDER=llamacpp
VLM_PROVIDER=llamacpp
EMBEDDING_PROVIDER=llamacpp
LLAMA_CPP_AUTOSTART=false
LLAMA_CPP_LLM_URL=http://127.0.0.1:8081/v1
LLAMA_CPP_VLM_URL=http://127.0.0.1:8081/v1
LLAMA_CPP_EMBEDDING_URL=http://127.0.0.1:8083/v1
LLAMA_CPP_LLM_MODEL=qwen3-vl-4b
LLAMA_CPP_VLM_MODEL=qwen3-vl-4b
LLAMA_CPP_EMBEDDING_MODEL=bge-m3
LLAMA_CPP_EMBEDDING_DIMENSION=1024
```

VLM 서버에는 GGUF와 대응하는 mmproj가 함께 필요합니다. 도구 호출을 위해 지원되는 채팅 템플릿과 `--jinja`를 사용합니다.
BGE-M3 서버는 `--embedding --pooling cls`로 실행합니다. 수동 실행 예:

```powershell
.runtime/llama/llama-server.exe -m models/Qwen3VL-4B-Instruct-Q4_K_M.gguf --mmproj models/mmproj-Qwen3VL-4B-Instruct-Q8_0.gguf --alias qwen3-vl-4b --host 127.0.0.1 --port 8081 -ngl 99 -c 16384 --parallel 1 --jinja -fa on -ctk q8_0 -ctv q8_0
.runtime/llama/llama-server.exe -m models/bge-m3-Q8_0.gguf --alias bge-m3 --host 127.0.0.1 --port 8083 -ngl 99 -c 8192 --parallel 1 --embedding --pooling cls -b 8192 -ub 8192
```

각 서버 명령은 별도 터미널에서 실행합니다. 기존 PostgreSQL을 유지하려면 `LOCAL_POSTGRES_AUTOSTART=false`와 본인의 `PGVECTOR_URL`을 사용합니다.

이미 Qwen3.5 4B 멀티모달 GGUF가 있다면 이를 지원하는 llama.cpp 버전과 함께 재사용할 수 있습니다.
`LLAMA_CPP_SERVER_PATH`, `LLAMA_CPP_LLM_GGUF`, `LLAMA_CPP_VLM_GGUF`, `LLAMA_CPP_MMPROJ`에 대응하는 파일 경로를 지정하고 LLM·VLM 별칭도 실제 서버 별칭으로 바꾸세요.
서로 다른 프로젝트가 GPU를 사용 중이면 메모리 부족이 발생할 수 있으므로 해당 모델 서버의 사용 상태를 확인하세요.

## 임베딩 전환 주의점

OpenAI 벡터와 BGE-M3 벡터는 같은 검색 공간이 아닙니다. 로컬 모델은 `llamacpp:bge-m3`처럼 제공자를 포함한 ID로 저장합니다.
모델을 바꾸면 Excel 파일을 다시 적재해 별도 인덱스를 만드세요. GGUF 자체를 교체할 때도 새 별칭을 사용하세요.
기존 OpenAI 인덱스를 검색하려면 해당 OpenAI 임베딩 모델과 키가 여전히 필요합니다.
모델 출력의 차원과 설정한 차원이 다르면 적재를 거부하여 잘못된 검색을 막습니다.

4B 로컬 모델의 복잡한 표 인식·재무 답변 정확도는 별도 확인이 필요합니다. 큰 시트는 이미지·컨텍스트 한도를 넘을 수 있으므로 작은 실습 예제부터 시작하세요.

구현 기준: [llama.cpp 서버 API](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md), [멀티모달·mmproj 안내](https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md), [OpenAI 구조화 출력](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat).
모델 출처: [Qwen 공식 GGUF](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct-GGUF), [GPUStack BGE-M3 GGUF](https://huggingface.co/gpustack/bge-m3-GGUF).
