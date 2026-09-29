"""Módulo de entrada de texto do AUTOWORK.

Responsável exclusivamente por:
1. Receber texto digitado pelo usuário;
2. Validar se existe conteúdo;
3. Retornar a mensagem como str limpa;
4. Permitir que o sistema utilize essa entrada continuamente enquanto o AUTOWORK estiver ativo.

Não executa comandos, não decide intenções e não chama executores.
"""
from __future__ import annotations

import logging
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


def validar_texto(texto: Optional[str]) -> Optional[str]:
    """Valida se uma entrada textual contém caracteres válidos.

    Args:
        texto: Texto bruto informado pelo usuário.

    Returns:
        A string sem espaços excedentes nas pontas se houver conteúdo,
        ou None caso a entrada seja nula, vazia ou contenha apenas espaços.
    """
    if texto is None:
        return None
    texto_limpo = texto.strip()
    return texto_limpo if texto_limpo else None


class EntradaTexto:
    """Gerencia a captura e validação da entrada de texto."""

    def __init__(self, prompt: str = "AUTOWORK > ") -> None:
        self.prompt = prompt

    def validar(self, texto: Optional[str]) -> Optional[str]:
        """Valida e higieniza uma cadeia de texto fornecida."""
        return validar_texto(texto)

    def obter_entrada(self) -> Optional[str]:
        """Lê do teclado via terminal, valida se há conteúdo e retorna a str limpa.

        Retorna:
            str com o texto limpo se houver conteúdo, ou None caso a entrada
            seja vazia ou o usuário cancele (Ctrl+C / EOF).
        """
        try:
            linha = input(self.prompt)
        except (KeyboardInterrupt, EOFError):
            return None

        return self.validar(linha)

    def receber_continuamente(self) -> Iterator[str]:
        """Fornece continuamente entradas de texto válidas enquanto o processo rodar.

        Ignora entradas vazias e encerra em caso de interrupção pelo usuário.
        """
        while True:
            try:
                texto = self.obter_entrada()
            except (KeyboardInterrupt, EOFError):
                break

            if texto is not None:
                yield texto


def obter_entrada_texto(prompt: str = "AUTOWORK > ") -> Optional[str]:
    """Função utilitária para leitura pontual de uma linha de texto."""
    return EntradaTexto(prompt=prompt).obter_entrada()
