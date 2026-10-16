"""Start the learning application, its frontend and local workers."""

import logging
from pathlib import Path

import dotenv
import uvicorn


def main() -> None:
    """Load .env, start owned local services, serve port 8765, and clean up on exit.

    Use this entry point for the automatic PostgreSQL/model profile. Direct
    uvicorn execution starts the API/workers but does not own those services.
    """
    root = Path(__file__).resolve().parent
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    dotenv.load_dotenv(root / ".env")
    from backend.bootstrap.local_services import LocalServices

    services = LocalServices(root)
    try:
        services.start()
        uvicorn.run("backend.entrypoints.asgi:app", host="127.0.0.1", port=8765, loop="backend.bootstrap.event_loop:selector_loop_factory")
    finally:
        services.stop()


if __name__ == "__main__":
    main()
