"""Contexto operacional curto, não persistente, da sessão atual."""
from __future__ import annotations

from threading import RLock
from typing import Any, Mapping


class ContextoExecucao:
    """Mantém apenas referências úteis para a próxima ordem do usuário."""

    def __init__(self) -> None:
        self._dados: dict[str, Any] = {
            "app_atual": None,
            "projeto_atual": None,
            "ultima_acao": None,
            "ultima_tarefa": None,
            "ultimo_alvo": None,
            "ultimo_resultado": None,
        }
        self._lock = RLock()

    def atualizar(self, **dados: Any) -> dict[str, Any]:
        with self._lock:
            self._dados.update({k: v for k, v in dados.items() if v is not None})
            return dict(self._dados)

    def registrar_acao(
        self,
        acao: str,
        parametros: Mapping[str, Any] | None = None,
        resultado: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = dict(parametros or {})
        alvo = params.get("nome") or params.get("aplicativo") or params.get("alvo")
        dados: dict[str, Any] = {
            "ultima_acao": acao,
            "ultimo_alvo": alvo,
            "ultimo_resultado": dict(resultado or {}),
        }
        if acao in {"abrir_app", "abrir_aplicativo"} and alvo:
            dados["app_atual"] = alvo
        if acao in {"abrir_projeto", "abrir_projeto_autowork"} and alvo:
            dados["projeto_atual"] = alvo
        return self.atualizar(**dados)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._dados)

    def resolver_referencia(self, texto: str) -> str:
        """Expande referências simples usando o último alvo conhecido."""
        if not isinstance(texto, str):
            return texto
        contexto = self.snapshot()
        alvo = contexto.get("app_atual") or contexto.get("ultimo_alvo")
        if not alvo:
            return texto
        import re

        if re.search(r"\b(ele|ela|isso|isto|esse app|esse aplicativo)\b", texto, re.I):
            return re.sub(
                r"\b(ele|ela|isso|isto|esse app|esse aplicativo)\b",
                str(alvo),
                texto,
                flags=re.I,
            )
        return texto
