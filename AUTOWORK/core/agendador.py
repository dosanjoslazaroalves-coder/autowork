"""Agendamento efêmero de ações durante a sessão atual."""
from __future__ import annotations

import itertools
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Callable
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class Agendador:
    def __init__(self, timezone: str = "America/Sao_Paulo", agora: Callable[[], datetime] | None = None) -> None:
        self.timezone = timezone
        self._agora = agora or (lambda: datetime.now(ZoneInfo(self.timezone)))
        self._timers: dict[str, threading.Timer] = {}
        self._contador = itertools.count(1)
        self._lock = threading.RLock()

    def agendar(self, callback: Callable[[], Any], *, atraso: float, descricao: str = "") -> dict[str, Any]:
        atraso = max(0.0, float(atraso))
        identificador = f"schedule_{next(self._contador):04d}"

        def executar() -> None:
            try:
                callback()
            finally:
                with self._lock:
                    self._timers.pop(identificador, None)

        timer = threading.Timer(atraso, executar)
        timer.daemon = True
        with self._lock:
            self._timers[identificador] = timer
        timer.start()
        alvo = self._agora() + timedelta(seconds=atraso)
        logger.info("[AGENDADOR] %s para %s (%s)", identificador, alvo.isoformat(), descricao)
        return {"schedule_id": identificador, "status": "agendado", "executar_em": alvo.isoformat(), "descricao": descricao}

    def cancelar(self, schedule_id: str) -> bool:
        with self._lock:
            timer = self._timers.pop(schedule_id, None)
        if timer is None:
            return False
        timer.cancel()
        return True

    def listar(self) -> list[str]:
        with self._lock:
            return list(self._timers)

    def fechar(self) -> None:
        with self._lock:
            timers = list(self._timers.values())
            self._timers.clear()
        for timer in timers:
            timer.cancel()
