"""Fila de execução serial com prioridades e cancelamento cooperativo."""
from __future__ import annotations

import itertools
import logging
import queue
import threading
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class Prioridade(IntEnum):
    CRITICA = 0
    ALTA = 10
    NORMAL = 20
    BAIXA = 30


@dataclass(order=True)
class ItemFila:
    prioridade: int
    sequencia: int
    item_id: str = field(compare=False)
    funcao: Callable[[], Any] = field(compare=False)
    cancelado: bool = field(default=False, compare=False)


class FilaExecucao:
    """Executa no máximo um comando por vez; a ordem dentro da prioridade é estável."""

    def __init__(self, nome: str = "autowork-fila") -> None:
        self._fila: queue.PriorityQueue[ItemFila] = queue.PriorityQueue()
        self._itens: dict[str, ItemFila] = {}
        self._sequencia = itertools.count()
        self._contador = itertools.count(1)
        self._encerrar = threading.Event()
        self._lock = threading.RLock()
        self._worker = threading.Thread(target=self._loop, name=nome, daemon=True)
        self._worker.start()

    def submeter(self, funcao: Callable[[], Any], prioridade: Prioridade = Prioridade.NORMAL) -> str:
        item_id = f"queue_{next(self._contador):04d}"
        item = ItemFila(int(prioridade), next(self._sequencia), item_id, funcao)
        with self._lock:
            self._itens[item_id] = item
        self._fila.put(item)
        logger.info("[FILA] %s enfileirado prioridade=%s", item_id, prioridade.name)
        return item_id

    def cancelar(self, item_id: str) -> bool:
        with self._lock:
            item = self._itens.get(item_id)
            if item is None:
                return False
            item.cancelado = True
            return True

    def tamanho(self) -> int:
        with self._lock:
            return sum(not item.cancelado for item in self._itens.values())

    def fechar(self) -> None:
        self._encerrar.set()
        self._fila.put(ItemFila(10**9, next(self._sequencia), "__stop__", lambda: None))

    def _loop(self) -> None:
        while not self._encerrar.is_set():
            item = self._fila.get()
            if item.item_id == "__stop__":
                break
            with self._lock:
                self._itens.pop(item.item_id, None)
            if item.cancelado:
                continue
            try:
                item.funcao()
            except Exception:
                logger.exception("[FILA] falha no item %s", item.item_id)
