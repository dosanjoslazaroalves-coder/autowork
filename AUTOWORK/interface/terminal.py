"""Funções de exibição no terminal — desacopladas da lógica de voz."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def mostrar_banner() -> None:
    """Exibe o cabeçalho ASCII do AUTOWORK no terminal."""
    print()
    print("=" * 45)
    print("            AUTOWORK")
    print("=" * 45)


def mostrar_status(mensagem: str) -> None:
    """Exibe mensagem de status no terminal."""
    print(f"\n[STATUS] {mensagem}")


def mostrar_resultado(
    texto: str,
    normalizado: Optional[str],
    comando: Optional[Dict[str, Any]],
    resultado_execucao: Optional[Dict[str, Any]] = None,
) -> None:
    """Formata e exibe o resultado de um comando processado."""
    print()
    print("  ▶ Texto capturado:    %s" % texto)

    if normalizado:
        print("  ▶ Texto normalizado:  %s" % normalizado)

    if comando is None:
        print("  ▶ Parser:             Não reconhecido")
        return

    acao = comando.get("acao", "")
    parametros = comando.get("parametros", {})

    print("  ▶ Ação reconhecida:    %s" % acao)

    if parametros:
        for chave, valor in parametros.items():
            print("  ▶   %s: %s" % (chave, valor))

    if resultado_execucao:
        status = resultado_execucao.get("status", "?")
        print("  ▶ Status:              %s" % status)

        mensagem = resultado_execucao.get("mensagem", "")
        if mensagem:
            print("  ▶ %s" % mensagem)

        erro = resultado_execucao.get("erro")
        if erro:
            print("  ▶ Erro:                %s" % erro)

        dados = resultado_execucao.get("dados")
        if dados:
            print(
                "  ▶ Dados extraídos:     "
                "(Estruturados para o Agente IA)"
            )
