"""Start the learning application, its frontend and local workers."""

from pathlib import Path

import dotenv
import uvicorn


def main() -> None:
    dotenv.load_dotenv(Path(__file__).resolve().parent / ".env")
    uvicorn.run("backend.entrypoints.asgi:app", host="127.0.0.1", port=8765)


if __name__ == "__main__":
    main()
