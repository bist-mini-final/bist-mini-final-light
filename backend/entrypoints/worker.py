"""Local queue worker process entrypoint."""

from __future__ import annotations

import argparse
import logging
import signal
from collections.abc import Sequence
from threading import Event

from backend.bootstrap.workers import registered_worker_kinds, run_worker


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=registered_worker_kinds())
    parser.add_argument("--loop", action="store_true", help="로컬 큐를 계속 확인합니다")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args, remaining = _parser().parse_known_args(argv)
    if not args.loop:
        return run_worker(args.kind, remaining)
    if args.poll_seconds <= 0:
        raise ValueError("poll-seconds must be positive")
    stopped = Event()
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    while not stopped.is_set():
        try:
            run_worker(args.kind, remaining)
        except Exception:
            logging.getLogger(__name__).exception("로컬 워커 오류: %s", args.kind)
        stopped.wait(args.poll_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
