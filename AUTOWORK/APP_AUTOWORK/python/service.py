"""Adapter between the local FastAPI transport and the real AUTOWORK core."""

from __future__ import annotations

import importlib
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any


LOGGER = logging.getLogger("autowork.service")


class CoreUnavailable(RuntimeError):
    """Raised when the real AUTOWORK core cannot be loaded."""


def _default_core_path() -> Path:
    """Find the sibling development checkout without hard-coding a user path."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    # service.py fica em AUTOWORK/APP_AUTOWORK/python; parents[2] já é o
    # checkout do núcleo AUTOWORK. O sufixo /Chat/AUTOWORK duplicava a árvore.
    return Path(__file__).resolve().parents[2]


class AutoworkService:
    """Expose the real core without duplicating its processing pipeline."""

    def __init__(self, core_path: str | None = None) -> None:
        configured_path = None if getattr(sys, "frozen", False) else (core_path or os.environ.get("AUTOWORK_CORE_PATH"))
        self._core_path = Path(configured_path).resolve() if configured_path else _default_core_path()
        self._core = None
        self._lock = RLock()
        self._tts_enabled = os.environ.get("AUTOWORK_TTS_ENABLED", "1").lower() not in {"0", "false", "off", "no"}

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "service": "AUTOWORK", "protocol": 1,
                "pid": os.getpid(), "frozen": bool(getattr(sys, "frozen", False))}

    def status(self) -> dict[str, Any]:
        base = {
            "service": "core-adapter",
            "mode": "local",
            "pid": os.getpid(),
            "time": datetime.now(timezone.utc).isoformat(),
        }
        try:
            core = self._load_core()
            return {**base, "autowork": "online", **core.status()}
        except Exception as exc:
            LOGGER.exception("Falha ao inicializar ou consultar o núcleo real")
            return {**base, "autowork": "offline", "core": "offline",
                    "state": "ERRO", "ready": False, "error": str(exc)}

    def command(self, texto: str) -> dict[str, Any]:
        LOGGER.info("[AutoworkService] encaminhando comando ao núcleo real: %r", texto)
        try:
            result = self._load_core().processar_comando(texto)
        except Exception:
            LOGGER.exception("[AutoworkService] Falha ao processar comando")
            raise
        LOGGER.info("[AutoworkService] resultado status=%s acao=%s estado=%s",
                    result.get("status"), result.get("acao"), result.get("estado"))
        return result

    def start_voice(self) -> dict[str, Any]:
        """Inicia a captura/STT real do mesmo orquestrador do terminal."""
        return self._load_core().start_voice()

    def stop_voice(self) -> dict[str, Any]:
        """Solicita o encerramento da escuta real do núcleo."""
        return self._load_core().stop_voice()

    def handle(self, action: str, payload: object | None = None) -> object:
        if action == "ping":
            return {**self.health(), "service": "AUTOWORK", "time": self.status()["time"]}
        if action == "status":
            return self.status()
        if action == "command":
            if not isinstance(payload, str):
                raise ValueError("payload do comando deve ser texto")
            return self.command(payload)
        if action == "voice.start":
            return self.start_voice()
        if action == "voice.stop":
            return self.stop_voice()
        if action == "voice.status":
            return self.status()
        raise ValueError(f"Ação de transporte não suportada: {action}")

    def _load_core(self):
        if self._core is not None:
            return self._core
        with self._lock:
            if self._core is not None:
                return self._core
            try:
                if not getattr(sys, "frozen", False):
                    if not (self._core_path / "core" / "servico_api.py").is_file():
                        raise FileNotFoundError("core/servico_api.py ausente")
                    if str(self._core_path) not in sys.path:
                        sys.path.insert(0, str(self._core_path))
                modulo = importlib.import_module("core.servico_api")
                self._core = modulo.ServicoApi(
                    tts_enabled=self._tts_enabled,
                    tts_async=True,
                )
                LOGGER.info("[AutoworkService] Núcleo real carregado: %s (frozen=%s)", modulo.__file__,
                            bool(getattr(sys, "frozen", False)))
                return self._core
            except Exception as exc:
                LOGGER.exception("Falha ao carregar o núcleo AUTOWORK")
                raise CoreUnavailable(
                    f"não foi possível carregar o núcleo em '{self._core_path}': {exc}"
                ) from exc
