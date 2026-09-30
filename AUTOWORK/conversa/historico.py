"""Memória conversacional em processo compartilhada pelos provedores."""
from __future__ import annotations

from typing import Any


class HistoricoConversa:
    """Mantém as mensagens recentes sem criar persistência nova."""

    def __init__(self, max_history: int = 20) -> None:
        self.max_history = max(1, int(max_history))
        self._mensagens: list[dict[str, str]] = []

    @property
    def mensagens(self) -> list[dict[str, str]]:
        """Retorna uma cópia das mensagens para evitar mutações externas."""
        return [dict(mensagem) for mensagem in self._mensagens]

    def limpar(self, mensagem_sistema: str) -> None:
        self._mensagens = [{"role": "system", "content": mensagem_sistema}]

    def adicionar(self, role: str, content: str) -> None:
        self._mensagens.append({"role": role, "content": content})
        self._limitar()

    def remover_ultima_mensagem_usuario(self) -> None:
        if len(self._mensagens) > 1 and self._mensagens[-1]["role"] == "user":
            self._mensagens.pop()

    def _limitar(self) -> None:
        if not self._mensagens:
            return
        sistema = self._mensagens[0]
        recentes = self._mensagens[1:]
        if len(recentes) > self.max_history:
            recentes = recentes[-self.max_history :]
        self._mensagens = [sistema, *recentes]

