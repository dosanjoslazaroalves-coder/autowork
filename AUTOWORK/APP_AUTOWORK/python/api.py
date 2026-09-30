"""Local FastAPI bridge for the AUTOWORK desktop application."""

from __future__ import annotations

import logging
import os
import sys
import threading
from dataclasses import dataclass

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from service import AutoworkService, CoreUnavailable


LOGGER = logging.getLogger("autowork.api")
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


class CommandRequest(BaseModel):
    texto: str = Field(min_length=1, max_length=4000)


@dataclass(frozen=True)
class ApiSettings:
    host: str = os.environ.get("AUTOWORK_API_HOST", "127.0.0.1")
    port: int = int(os.environ.get("AUTOWORK_API_PORT", "47100"))

    def validate(self) -> None:
        if self.host not in LOCAL_HOSTS:
            raise ValueError(
                "AUTOWORK_API_HOST must be a loopback address "
                "(127.0.0.1, localhost or ::1)"
            )
        if not 1 <= self.port <= 65535:
            raise ValueError("AUTOWORK_API_PORT must be between 1 and 65535")


service = AutoworkService()
app = FastAPI(
    title="AUTOWORK Local API",
    version="0.3.0",
    docs_url=None,
    redoc_url=None,
)


@app.get("/health")
def health() -> dict[str, object]:
    LOGGER.info("[FastAPI] GET /health")
    return service.health()


@app.get("/api/status")
def status() -> dict[str, object]:
    LOGGER.debug("[FastAPI] GET /api/status")
    return {**service.status(), "api": "online"}


@app.post("/api/command")
def command(request: CommandRequest) -> dict[str, object]:
    LOGGER.info("[FastAPI] POST /api/command comando recebido: %r", request.texto)
    try:
        result = service.command(request.texto)
        LOGGER.info("[FastAPI] POST /api/command concluído status=%s acao=%s estado=%s",
                    result.get("status"), result.get("acao"), result.get("estado"))
        return result
    except CoreUnavailable as exc:
        LOGGER.error("[FastAPI] Núcleo AUTOWORK indisponível: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        LOGGER.warning("[FastAPI] Comando inválido: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        LOGGER.exception("[FastAPI] Erro ao processar comando pelo núcleo AUTOWORK")
        raise HTTPException(status_code=500, detail="Erro interno do AUTOWORK") from exc


def configure_logging() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    logging.basicConfig(
        level=os.environ.get("AUTOWORK_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def monitor_owner(server: uvicorn.Server) -> None:
    """Stop a desktop-owned sidecar on stdin shutdown or owner termination."""
    parent_pid = os.environ.get("AUTOWORK_PARENT_PID")
    if not parent_pid:
        return  # Manually started API remains independent from Electron.
    import psutil

    try:
        owner = psutil.Process(int(parent_pid))
        owner_created = owner.create_time()
    except (ValueError, psutil.Error):
        LOGGER.exception("Processo proprietário indisponível; encerrando sidecar")
        server.should_exit = True
        return

    def watch_parent() -> None:
        while not server.should_exit:
            try:
                if not owner.is_running() or owner.create_time() != owner_created:
                    break
            except psutil.Error:
                break
            threading.Event().wait(0.5)
        if not server.should_exit:
            LOGGER.info("Electron proprietário encerrou; desligando API")
            server.should_exit = True

    def watch_input() -> None:
        try:
            if sys.stdin is not None:
                for line in sys.stdin:
                    if line.strip() == "shutdown":
                        LOGGER.info("Encerramento solicitado pelo Electron proprietário")
                        server.should_exit = True
                        return
        except (OSError, ValueError):
            LOGGER.warning("Canal de controle stdin indisponível", exc_info=True)
        # EOF on the pipe is not an explicit shutdown request. The owner PID
        # watcher above is responsible for stopping the sidecar if Electron
        # really exits, while normal shutdown sends the explicit line above.

    threading.Thread(target=watch_parent, daemon=True, name="autowork-owner").start()
    threading.Thread(target=watch_input, daemon=True, name="autowork-control").start()


def main() -> None:
    configure_logging()
    settings = ApiSettings()
    settings.validate()
    LOGGER.info("[FastAPI] iniciando executável=%s cwd=%s PID=%s host=%s porta=%s owner=%s",
                sys.executable, os.getcwd(), os.getpid(), settings.host, settings.port,
                os.environ.get("AUTOWORK_PARENT_PID", "manual"))
    server = uvicorn.Server(uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_config=None,
        access_log=True,
        timeout_graceful_shutdown=5,
    ))
    monitor_owner(server)
    if not server.should_exit:
        server.run()


if __name__ == "__main__":
    main()
