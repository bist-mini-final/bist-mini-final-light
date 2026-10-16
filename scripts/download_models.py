"""Download the selected GGUFs over Hugging Face's resumable HTTPS transport."""

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def main() -> None:
    """Download Qwen VL, its matching projector, and BGE-M3 into models/.

    HTTPS is the default because Xet's native transport can stall behind
    corporate proxies. Set HF_HUB_DISABLE_XET=0 to opt in to Xet. The downloader
    reuses its local cache on reruns. This function
    downloads files only: it does not start model servers or alter .env.
    """
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
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
