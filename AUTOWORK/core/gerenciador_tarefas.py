"""Máquina de estados determinística das tarefas da sessão."""
from __future__ import annotations

import copy
import itertools
from threading import RLock
from typing import Any, Mapping

from core.eventos import (
    ACTION_CANCELLED,
    ACTION_COMPLETED,
    ACTION_FAILED,
    ACTION_STARTED,
    TASK_CANCELLED,
    TASK_COMPLETED,
    TASK_FAILED,
    TASK_STARTED,
    EventBus,
)

STATUS_PENDENTE = "pendente"
STATUS_AGUARDANDO = "aguardando"
STATUS_EXECUTANDO = "executando"
STATUS_CONCLUIDO = "concluido"
STATUS_FALHOU = "falhou"
STATUS_CANCELADO = "cancelado"


class GerenciadorTarefas:
    """Controla uma tarefa ativa e seus estados observados."""

    def __init__(self, eventos: EventBus | None = None) -> None:
        self._eventos = eventos or EventBus()
        self._tarefas: dict[str, dict[str, Any]] = {}
        self._ativa: str | None = None
        self._contador = itertools.count(1)
        self._lock = RLock()

    @property
    def tarefa_ativa_id(self) -> str | None:
        with self._lock:
            return self._ativa

    def criar(self, objetivo: str, acoes: list[Mapping[str, Any]], task_id: str | None = None) -> dict[str, Any]:
        with self._lock:
            identificador = task_id or f"task_{next(self._contador):04d}"
            itens = []
            for indice, acao in enumerate(acoes, 1):
                item = dict(acao)
                item.setdefault("id", f"acao_{indice}")
                item.setdefault("status", STATUS_PENDENTE)
                item.setdefault("depende_de", item.get("dependencias", []))
                itens.append(item)
            tarefa = {
                "task_id": identificador,
                "objetivo": objetivo,
                "status": STATUS_AGUARDANDO,
                "acoes": itens,
                "resultado_final": None,
                "cancelar_tudo": False,
            }
            self._tarefas[identificador] = tarefa
            self._ativa = identificador
        self._eventos.publish(TASK_STARTED, task_id=identificador, tarefa=copy.deepcopy(tarefa))
        return self.snapshot(identificador)

    def iniciar_acao(self, task_id: str, acao_id: Any) -> bool:
        return self._atualizar_acao(task_id, acao_id, STATUS_EXECUTANDO, ACTION_STARTED)

    def concluir_acao(self, task_id: str, acao_id: Any, resultado: Mapping[str, Any]) -> bool:
        with self._lock:
            tarefa = self._tarefas.get(task_id)
            atual = next(
                (acao.get("status") for acao in (tarefa or {}).get("acoes", []) if str(acao.get("id")) == str(acao_id)),
                None,
            )
            if atual in {STATUS_CONCLUIDO, STATUS_FALHOU, STATUS_CANCELADO}:
                return True
        if resultado.get("status") == STATUS_CANCELADO:
            status = STATUS_CANCELADO
            evento = ACTION_CANCELLED
        else:
            status = STATUS_CONCLUIDO if resultado.get("sucesso") or resultado.get("confirmado") else STATUS_FALHOU
            evento = ACTION_COMPLETED if status == STATUS_CONCLUIDO else ACTION_FAILED
        ok = self._atualizar_acao(task_id, acao_id, status, evento, resultado=dict(resultado))
        self._finalizar_se_necessario(task_id)
        return ok

    def cancelar_acao(self, acao_id: Any, task_id: str | None = None) -> bool:
        with self._lock:
            tid = task_id or self._ativa
            tarefa = self._tarefas.get(tid or "")
            if not tarefa:
                return False
            for acao in tarefa["acoes"]:
                if str(acao.get("id")) == str(acao_id) or str(acao.get("alvo", "")).casefold() == str(acao_id).casefold():
                    if acao.get("status") in {STATUS_PENDENTE, STATUS_AGUARDANDO}:
                        acao["status"] = STATUS_CANCELADO
                        acao["erro"] = "cancelado_pelo_usuario"
                        self._eventos.publish(ACTION_CANCELLED, task_id=tid, action_id=acao.get("id"))
                        return True
            return False

    def cancelar_tarefa(self, task_id: str | None = None) -> bool:
        with self._lock:
            tid = task_id or self._ativa
            tarefa = self._tarefas.get(tid or "")
            if not tarefa or tarefa["status"] in {STATUS_CONCLUIDO, STATUS_FALHOU, STATUS_CANCELADO}:
                return False
            tarefa["cancelar_tudo"] = True
            for acao in tarefa["acoes"]:
                if acao.get("status") in {STATUS_PENDENTE, STATUS_AGUARDANDO}:
                    acao["status"] = STATUS_CANCELADO
            tarefa["status"] = STATUS_CANCELADO
        self._eventos.publish(TASK_CANCELLED, task_id=tid)
        return True

    def deve_cancelar(self, task_id: str, acao_id: Any | None = None) -> bool:
        with self._lock:
            tarefa = self._tarefas.get(task_id)
            if not tarefa:
                return False
            if tarefa.get("cancelar_tudo"):
                return True
            if acao_id is None:
                return False
            return any(
                str(a.get("id")) == str(acao_id) and a.get("status") == STATUS_CANCELADO
                for a in tarefa["acoes"]
            )

    def finalizar(self, task_id: str, resultado: Mapping[str, Any]) -> dict[str, Any]:
        with self._lock:
            tarefa = self._tarefas.get(task_id)
            if not tarefa:
                return {}
            if tarefa.get("cancelar_tudo") or resultado.get("status") == "cancelado":
                status = STATUS_CANCELADO
            elif resultado.get("sucesso"):
                status = STATUS_CONCLUIDO
            else:
                status = STATUS_FALHOU
            tarefa["status"] = status
            tarefa["resultado_final"] = dict(resultado)
            if self._ativa == task_id:
                self._ativa = None
            snapshot = copy.deepcopy(tarefa)
        self._eventos.publish(
            TASK_COMPLETED if status == STATUS_CONCLUIDO else TASK_FAILED if status == STATUS_FALHOU else TASK_CANCELLED,
            task_id=task_id,
            tarefa=snapshot,
        )
        return snapshot

    def snapshot(self, task_id: str | None = None) -> dict[str, Any]:
        with self._lock:
            tid = task_id or self._ativa
            return copy.deepcopy(self._tarefas.get(tid or "", {}))

    def listar(self) -> list[dict[str, Any]]:
        with self._lock:
            return copy.deepcopy(list(self._tarefas.values()))

    def _atualizar_acao(self, task_id: str, acao_id: Any, status: str, evento: str, **dados: Any) -> bool:
        with self._lock:
            tarefa = self._tarefas.get(task_id)
            if not tarefa:
                return False
            for acao in tarefa["acoes"]:
                if str(acao.get("id")) == str(acao_id):
                    acao["status"] = status
                    acao.update(dados)
                    tarefa["status"] = STATUS_EXECUTANDO if status == STATUS_EXECUTANDO else tarefa["status"]
                    break
            else:
                return False
        self._eventos.publish(evento, task_id=task_id, action_id=acao_id, status=status, **dados)
        return True

    def _finalizar_se_necessario(self, task_id: str) -> None:
        with self._lock:
            tarefa = self._tarefas.get(task_id)
            if not tarefa or any(a.get("status") in {STATUS_PENDENTE, STATUS_AGUARDANDO, STATUS_EXECUTANDO} for a in tarefa["acoes"]):
                return
