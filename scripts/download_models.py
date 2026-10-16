"""Download the pinned GGUFs over bounded, resumable HTTPS and verify SHA-256."""

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    """Download Qwen VL, its matching projector, and BGE-M3 into models/.

    SHA-256 values are the official repositories' Git LFS object IDs. Standard
    HTTPS avoids native transfer clients that can stall behind corporate
    proxies. Interrupted .partial files are resumed when supported. This function
    downloads files only: it does not start model servers or alter .env.
    """
    from scripts.download_runtime import download_file

    destination = ROOT / "models"
    jobs = [
        (
            "Qwen/Qwen3-VL-4B-Instruct-GGUF",
            "Qwen3VL-4B-Instruct-Q4_K_M.gguf",
            "66358cb18bb6b3b1b6675aa412c7a88ef01d228f481184d13668e5201c730a0a",
        ),
        (
            "Qwen/Qwen3-VL-4B-Instruct-GGUF",
            "mmproj-Qwen3VL-4B-Instruct-Q8_0.gguf",
            "30ba2c7dd3127a4561b6cba9d13d0f711c91bdb38742e2f56d73c8cb596bd06d",
        ),
        (
            "gpustack/bge-m3-GGUF",
            "bge-m3-Q8_0.gguf",
            "950f4a8e5e19477a6d3c26d2f162233c20002c601f75e4b002e3239997821167",
        ),
    ]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(
                download_file,
                f"https://huggingface.co/{repo}/resolve/main/{filename}",
                destination / filename,
                digest,
            )
            for repo, filename, digest in jobs
        ]
        for future in futures:
            print(future.result(), flush=True)


if __name__ == "__main__":
    main()
