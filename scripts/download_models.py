"""Download the selected GGUFs using Hugging Face's resumable Xet client."""

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def main() -> None:
    os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")
    from huggingface_hub import hf_hub_download

    destination = Path(__file__).resolve().parents[1] / "models"
    jobs = [
        ("Qwen/Qwen3-VL-4B-Instruct-GGUF", "Qwen3VL-4B-Instruct-Q4_K_M.gguf"),
        ("Qwen/Qwen3-VL-4B-Instruct-GGUF", "mmproj-Qwen3VL-4B-Instruct-Q8_0.gguf"),
        ("gpustack/bge-m3-GGUF", "bge-m3-Q8_0.gguf"),
    ]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(hf_hub_download, repo, filename, local_dir=destination) for repo, filename in jobs]
        for future in futures:
            print(future.result(), flush=True)


if __name__ == "__main__":
    main()
