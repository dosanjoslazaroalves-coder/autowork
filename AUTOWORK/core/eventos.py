"""Barramento de eventos leve para desacoplar o núcleo do AUTOWORK.

Os eventos são somente notificações em memória da sessão atual. Um listener
com defeito nunca deve interromper a execução da ação que o originou.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from threading import RLock
from typing import Any, Callable, DefaultDict

logger = logging.getLogger(__name__)

ACTION_STARTED = "ACTION_STARTED"
ACTION_COMPLETED = "ACTION_COMPLETED"
ACTION_FAILED = "ACTION_FAILED"
ACTION_CANCELLED = "ACTION_CANCELLED"
TASK_STARTED = "TASK_STARTED"
TASK_COMPLETED = "TASK_COMPLETED"
TASK_FAILED = "TASK_FAILED"
TASK_CANCELLED = "TASK_CANCELLED"
USER_INTERRUPTED = "USER_INTERRUPTED"
ASSISTANT_LISTENING = "ASSISTANT_LISTENING"
ASSISTANT_UNDERSTANDING = "ASSISTANT_UNDERSTANDING"
ASSISTANT_PLANNING = "ASSISTANT_PLANNING"
ASSISTANT_EXECUTING = "ASSISTANT_EXECUTING"
ASSISTANT_WAITING = "ASSISTANT_WAITING"

Listener = Callable[[dict[str, Any]], None]


class EventBus:
    """Publica eventos tipados dentro da sessão do assistente."""

    def __init__(self) -> None:
        self._listeners: DefaultDict[str, list[Listener]] = defaultdict(list)
        self._lock = RLock()

    def subscribe(self, evento: str, listener: Listener) -> None:
        with self._lock:
            if listener not in self._listeners[evento]:
                self._listeners[evento].append(listener)

    def unsubscribe(self, evento: str, listener: Listener) -> None:
        with self._lock:
            if listener in self._listeners.get(evento, []):
                self._listeners[evento].remove(listener)

    def publish(self, evento: str, **dados: Any) -> dict[str, Any]:
        payload = {"evento": evento, **dados}
        with self._lock:
            listeners = list(self._listeners.get(evento, [])) + list(
                self._listeners.get("*", [])
            )
        for listener in listeners:
            try:
                listener(payload)
            except Exception:
                logger.debug("Listener falhou para %s.", evento, exc_info=True)
        return payload
