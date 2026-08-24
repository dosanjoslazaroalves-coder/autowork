from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from sistema_toke.catalogo import (
    MAPA_VERBOS,
    PALAVRAS_DESCARTE,
    VERBOS_POR_ACAO,
)

logger = logging.getLogger(__name__)


_RE_PONTUACAO = re.compile(r"[^\w\s-]", re.UNICODE)


def _remover_pontuacao(texto: str) -> str:
    return _RE_PONTUACAO.sub("", texto)


def _limpar(texto: str) -> str:

    resultado = texto.lower().strip()
    resultado = _remover_pontuacao(resultado)
    resultado = " ".join(resultado.split())
    return resultado


def _tokenizar(texto: str) -> List[str]:
    return texto.split()


def _encontrar_verbo(tokens: List[str]) -> Optional[Tuple[int, int, str]]:
    if not tokens:
        return None

    for i, token in enumerate(tokens):
        token_lower = token.lower()

        if i + 1 < len(tokens):
            bigrama = f"{token_lower} {tokens[i + 1].lower()}"
            if bigrama in MAPA_VERBOS:
                return (i, i + 2, MAPA_VERBOS[bigrama])

        if token_lower in MAPA_VERBOS:
            return (i, i + 1, MAPA_VERBOS[token_lower])

    return None


def _remover_descartaveis(tokens: List[str]) -> List[str]:

    return [t for t in tokens if t.lower() not in PALAVRAS_DESCARTE]


def _extrair_objeto(tokens: List[str], inicio: int) -> Optional[str]:

    if inicio >= len(tokens):
        return None

    resto = tokens[inicio:]

    resto_limpo = _remover_descartaveis(resto)

    if not resto_limpo:
        return None

    objeto = " ".join(resto_limpo).strip()
    return objeto if objeto else None


def _exibir_debug(
    texto_original: str,
    texto_limpo: str,
    tokens: List[str],
    verbo_info: Optional[Tuple[int, int, str]],
    objeto: Optional[str],
    resultado: Optional[str],
) -> None:

    logger.debug("=== normalizador debug ===")
    logger.debug("Original : %r", texto_original)
    logger.debug("Limpo    : %r", texto_limpo)
    logger.debug("Tokens   : %s", tokens)

    if verbo_info:
        idx_inicio, idx_fim, verbo = verbo_info
        trecho_verbo = " ".join(tokens[idx_inicio:idx_fim])
        logger.debug("Verbo    : [%d:%d] %r → canônico=%r", idx_inicio, idx_fim, trecho_verbo, verbo)
    else:
        logger.debug("Verbo    : não encontrado")

    logger.debug("Objeto   : %r", objeto)
    logger.debug("Resultado: %r", resultado)
    logger.debug("===========================")

    # Print para terminal durante desenvolvimento
    print("  Texto original: %s" % texto_original)
    print("  Texto limpo:   %s" % texto_limpo)
    print("  Tokens:        %s" % tokens)

    if verbo_info:
        idx_inicio, idx_fim, verbo = verbo_info
        trecho_verbo = " ".join(tokens[idx_inicio:idx_fim])
        print("  Verbo:         %s (canônico: %s, índice: %d:%d)" % (trecho_verbo, verbo, idx_inicio, idx_fim))
    else:
        print("  Verbo:         não encontrado")

    print("  Objeto:        %s" % (objeto or "não encontrado"))
    print("  Normalizado:   %s" % (resultado or "None"))
    print()


def normalizar(texto: str) -> Optional[str]:

    if not texto or not texto.strip():
        logger.debug("normalizador: texto vazio ou None.")
        return None

    texto_original = texto.strip()

    texto_limpo = _limpar(texto_original)
    if not texto_limpo:
        logger.debug("normalizador: texto ficou vazio após limpeza.")
        return None

    tokens = _tokenizar(texto_limpo)
    if not tokens:
        return None

    verbo_info = _encontrar_verbo(tokens)

    if verbo_info is None:

        restante = _remover_descartaveis(tokens)
        if not restante:
            logger.debug("normalizador: sem verbo e sem tokens após remoção.")
            _exibir_debug(texto_original, texto_limpo, tokens, None, None, None)
            return None

        resultado = " ".join(restante).strip()
        logger.debug("normalizador: sem verbo, retornando texto limpo=%r", resultado)
        _exibir_debug(texto_original, texto_limpo, tokens, None, None, resultado)
        return resultado

    _, idx_fim_verbo, verbo_canonico = verbo_info

    objeto = _extrair_objeto(tokens, idx_fim_verbo)

    if not objeto:
        logger.debug(
            "normalizador: verbo '%s' encontrado mas sem objeto identificável.",
            verbo_canonico,
        )
        _exibir_debug(texto_original, texto_limpo, tokens, verbo_info, None, None)
        return None

    resultado = f"{verbo_canonico} {objeto}"
    logger.debug("normalizador: normalizado=%r", resultado)
    _exibir_debug(texto_original, texto_limpo, tokens, verbo_info, objeto, resultado)
    return resultado
