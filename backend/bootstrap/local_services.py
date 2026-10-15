"""Optional project-local PostgreSQL and CUDA llama.cpp process ownership."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urlsplit

import httpx
import psycopg2
from psycopg2 import sql

logger = logging.getLogger(__name__)


class LocalServices:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.children: list[tuple[subprocess.Popen[bytes], BinaryIO]] = []
        self.postgres_started = False

    def path(self, name: str, default: str) -> Path:
        path = Path(os.getenv(name, default))
        return path if path.is_absolute() else self.root / path

    @staticmethod
    def enabled(name: str) -> bool:
        return os.getenv(name, "false").lower() in {"true", "1", "yes"}

    def command(self, arguments: list[str]) -> None:
        # A background PostgreSQL process can inherit pipe handles on Windows.
        # File output avoids communicate() waiting forever for the server's EOF.
        with tempfile.TemporaryFile() as output:
            result = subprocess.run(arguments, stdout=output, stderr=subprocess.STDOUT, cwd=Path(arguments[0]).parent, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            output.seek(0)
            message = output.read().decode("utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(f"{Path(arguments[0]).name} 실행 실패:\n{message}")
        if message:
            logger.info("%s", message.strip())

    def postgres(self) -> None:
        binaries = self.path("LOCAL_POSTGRES_BIN", ".runtime/postgres/Library/bin")
        data = self.path("LOCAL_POSTGRES_DATA", "data/postgres")
        port = os.getenv("LOCAL_POSTGRES_PORT", "5433")
        control = binaries / ("pg_ctl.exe" if os.name == "nt" else "pg_ctl")
        if not control.is_file():
            raise RuntimeError("로컬 PostgreSQL 실행 파일이 없습니다. 설치 안내를 확인하세요.")
        if not (data / "PG_VERSION").is_file():
            if os.name == "nt" and (not str(data).isascii() or not str(binaries).isascii()):
                raise RuntimeError("Windows PostgreSQL은 영문 경로에 설치하세요. LOCAL_POSTGRES_BIN과 LOCAL_POSTGRES_DATA를 영문 경로로 지정할 수 있습니다.")
            self.command([str(binaries / ("initdb.exe" if os.name == "nt" else "initdb")), "-D", str(data), "-U", "postgres", "--auth=trust", "--encoding=UTF8", "--locale=C"])
        status = subprocess.run([str(control), "-D", str(data), "status"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        if status.returncode != 0:
            self.command([str(control), "-D", str(data), "-l", str(data.parent / "postgres-server.log"), "-o", f"-h 127.0.0.1 -p {int(port)}", "-w", "start"])
            self.postgres_started = True
        connection = psycopg2.connect(host="127.0.0.1", port=int(port), user="postgres", dbname="postgres")
        try:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'rag_flow_light'")
                if cursor.fetchone() is None:
                    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier("rag_flow_light")))
        finally:
            connection.close()

    def model(self, role: str, port: int) -> None:
        server = self.path("LLAMA_CPP_SERVER_PATH", ".runtime/llama/llama-server.exe" if os.name == "nt" else ".runtime/llama/llama-server")
        embedding = role == "embedding"
        default_model = "models/bge-m3-Q8_0.gguf" if embedding else "models/Qwen3VL-4B-Instruct-Q4_K_M.gguf"
        model = self.path(f"LLAMA_CPP_{role.upper()}_GGUF", default_model)
        if not server.is_file() or not model.is_file():
            logger.warning("%s 로컬 실행 파일이나 GGUF가 없습니다. 다운로드 후 서버를 다시 시작하세요.", role)
            return
        arguments = [str(server), "-m", str(model), "--host", "127.0.0.1", "--port", str(port), "--alias", os.getenv(f"LLAMA_CPP_{role.upper()}_MODEL", "bge-m3" if embedding else "qwen3-vl-4b"), "--device", "CUDA0", "-ngl", "99", "--parallel", "1", "-c", "8192" if embedding else "16384"]
        if embedding:
            arguments.extend(["--embedding", "--pooling", "cls", "-b", "8192", "-ub", "8192"])
        else:
            projector = self.path("LLAMA_CPP_MMPROJ", "models/mmproj-Qwen3VL-4B-Instruct-Q8_0.gguf")
            if not projector.is_file():
                logger.warning("Qwen VL mmproj 파일이 없습니다. 다운로드 후 서버를 다시 시작하세요.")
                return
            arguments.extend(["--mmproj", str(projector), "--jinja", "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0"])
        logs = self.root / "logs"
        logs.mkdir(exist_ok=True)
        log = (logs / f"llama-{role}.log").open("ab")
        environment = dict(os.environ)
        if not embedding:
            environment.setdefault("LLAMA_ARG_REASONING", "off")
        cuda_dll_dir = environment.get("LLAMA_CPP_CUDA_DLL_DIR")
        if cuda_dll_dir:
            environment["PATH"] = cuda_dll_dir + os.pathsep + environment.get("PATH", "")
        try:
            process = subprocess.Popen(arguments, cwd=self.root, env=environment, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except BaseException:
            log.close()
            raise
        self.children.append((process, log))
        logger.info("CUDA llama.cpp %s 서버 시작 (port=%s)", role, port)

    def start(self) -> None:
        try:
            if self.enabled("LOCAL_POSTGRES_AUTOSTART"):
                self.postgres()
            if self.enabled("LLAMA_CPP_AUTOSTART"):
                self.start_models()
        except BaseException:
            self.stop()
            raise

    def start_models(self) -> None:
        started: set[str] = set()
        for role in ("vlm", "llm", "embedding"):
            if os.getenv(f"{role.upper()}_PROVIDER", "openai") != "llamacpp":
                continue
            url = os.getenv(f"LLAMA_CPP_{role.upper()}_URL", "http://127.0.0.1:8083/v1" if role == "embedding" else "http://127.0.0.1:8081/v1")
            if url in started:
                continue
            parts = urlsplit(url)
            if parts.hostname not in {"localhost", "127.0.0.1"} or not parts.port:
                continue
            try:
                response = httpx.get(url.rstrip("/") + "/models", timeout=1)
                response.raise_for_status()
            except httpx.HTTPError:
                self.model(role, parts.port)
            started.add(url)

    def stop(self) -> None:
        for process, _ in self.children:
            if process.poll() is None:
                process.terminate()
        for process, log in self.children:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            log.close()
        self.children.clear()
        if self.postgres_started:
            binaries = self.path("LOCAL_POSTGRES_BIN", ".runtime/postgres/Library/bin")
            data = self.path("LOCAL_POSTGRES_DATA", "data/postgres")
            self.command([str(binaries / ("pg_ctl.exe" if os.name == "nt" else "pg_ctl")), "-D", str(data), "-m", "fast", "-w", "stop"])
            self.postgres_started = False
