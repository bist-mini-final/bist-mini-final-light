"""Uvicorn loop factory compatible with psycopg's async driver on Windows."""

import asyncio


def selector_loop_factory() -> asyncio.AbstractEventLoop:
    return asyncio.SelectorEventLoop()
