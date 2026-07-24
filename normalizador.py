from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from catalogo import (
    MAPA_VERBOS,
    PALAVRAS_DESCARTE,
    VERBOS_POR_ACAO,
)

logger = logging.getLogger(__name__)

"""
normalizador.py — Normalização de linguagem natural para o Command Parser.

Responsabilidade única: transformar variações de fala livre em texto
padronizado no formato "verbo objeto".

Sem IA. Sem LLM. Sem Ollama. Apenas regras determinísticas.

Arquitetura:
    1. Limpeza (lowercase, pontuação, espaços)
    2. Tokenização
    3. Varredura de verbos em qualquer posição
    4. Extração do objeto (remove descartáveis, mantém nomes compostos)
    5. Montagem no formato canônico

Futuro: adicionar VERBOS_FECHAR, VERBOS_PESQUISAR etc. sem alterar
a lógica principal — basta estender MAPA_VERBOS e PALAVRAS_DESCARTE.
"""

# Expressão regular para remover pontuação.
# Mantém letras, números, espaços e hífens (para nomes compostos).
_RE_PONTUACAO = re.compile(r"[^\w\s-]", re.UNICODE)


# ──────────────────────────────────────────────
# Etapas do pipeline
# ──────────────────────────────────────────────


def _remover_pontuacao(texto: str) -> str:
    """Remove caracteres de pontuação (!?,.;:) mantendo palavras e hífens."""
    return _RE_PONTUACAO.sub("", texto)


def _limpar(texto: str) -> str:
    """Aplica pipeline de limpeza: lowercase → remove pontuação → remove espaços duplicados."""
    # 1. Minúsculas
    resultado = texto.lower().strip()
    # 2. Remove pontuação
    resultado = _remover_pontuacao(resultado)
    # 3. Remove espaços duplicados
    resultado = " ".join(resultado.split())
    return resultado


def _tokenizar(texto: str) -> List[str]:
    """Divide o texto em tokens (palavras)."""
    return texto.split()


def _encontrar_verbo(tokens: List[str]) -> Optional[Tuple[int, str]]:
    """Varre TODOS os tokens da frase em busca do primeiro verbo conhecido.

    Percorre cada token e verifica se ele (ou um bigrama token[i] + token[i+1])
    está no MAPA_VERBOS.

    Args:
        tokens: Lista de tokens da frase.

    Returns:
        (indice_do_verbo, verbo_canonico) ou None se nenhum verbo for encontrado.

    Exemplo:
        tokens = ["por", "favor", "abra", "o", "chrome"]
        → (2, "abrir")   # índice 2 = "abra", canônico = "abrir"
    """
    if not tokens:
        return None

    for i, token in enumerate(tokens):
        token_lower = token.lower()

        # Tenta token simples
        if token_lower in MAPA_VERBOS:
            return (i, MAPA_VERBOS[token_lower])

        # Tenta bigrama (ex: "por favor" como expressão, mas favor está em descarte)
        if i + 1 < len(tokens):
            bigrama = f"{token_lower} {tokens[i + 1].lower()}"
            if bigrama in MAPA_VERBOS:
                return (i, MAPA_VERBOS[bigrama])

    return None


def _remover_descartaveis(tokens: List[str]) -> List[str]:
    """Remove palavras descartáveis (artigos, preposições, pronomes, etc.)."""
    return [t for t in tokens if t.lower() not in PALAVRAS_DESCARTE]


def _extrair_objeto(tokens: List[str], inicio: int) -> Optional[str]:
    """Extrai o objeto do comando a partir dos tokens após o verbo.

    Passos:
        1. Pega todos os tokens a partir de 'inicio'
        2. Remove palavras descartáveis
        3. Junta o restante preservando nomes compostos

    Args:
        tokens: Lista completa de tokens da frase.
        inicio: Índice do primeiro token após o verbo.

    Returns:
        String do objeto (ex: "visual studio code", "chrome") ou None.
    """
    if inicio >= len(tokens):
        return None

    # Pega tokens a partir do índice do verbo + 1
    resto = tokens[inicio:]

    # Remove descartáveis
    resto_limpo = _remover_descartaveis(resto)

    if not resto_limpo:
        return None

    objeto = " ".join(resto_limpo).strip()
    return objeto if objeto else None


def _exibir_debug(
    texto_original: str,
    texto_limpo: str,
    tokens: List[str],
    verbo_info: Optional[Tuple[int, str]],
    objeto: Optional[str],
    resultado: Optional[str],
) -> None:
    """Exibe informações detalhadas de debug no terminal e via logging."""
    logger.debug("=== normalizador debug ===")
    logger.debug("Original : %r", texto_original)
    logger.debug("Limpo    : %r", texto_limpo)
    logger.debug("Tokens   : %s", tokens)

    if verbo_info:
        idx, verbo = verbo_info
        logger.debug("Verbo    : [%d] %r → canônico=%r", idx, tokens[idx], verbo)
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
        idx, verbo = verbo_info
        print("  Verbo:         %s (canônico: %s, índice: %d)" % (tokens[idx], verbo, idx))
    else:
        print("  Verbo:         não encontrado")

    print("  Objeto:        %s" % (objeto or "não encontrado"))
    print("  Normalizado:   %s" % (resultado or "None"))
    print()


# ──────────────────────────────────────────────
# Função pública
# ──────────────────────────────────────────────


def normalizar(texto: str) -> Optional[str]:
    """Normaliza o texto do usuário para uma forma canônica.

    A função percorre TODOS os tokens da frase (não apenas o primeiro)
    em busca de verbos conhecidos. Isso permite lidar com linguagem
    natural como "Por favor abra o Chrome", "Você consegue abrir o
    Spotify?", etc.

    Args:
        texto: Texto livre falado pelo usuário.

    Returns:
        String normalizada no formato 'verbo objeto', ex: "abrir chrome",
        "abrir visual studio code", ou o texto limpo se for um comando
        fixo como "hora", "data".

        Retorna None se o texto for vazio ou inválido.

    Exemplos:
        "Abra o Chrome"           → "abrir chrome"
        "Por favor abra o Chrome" → "abrir chrome"
        "Você consegue abrir o Spotify?" → "abrir spotify"
        "Gostaria de iniciar o Visual Studio Code." → "abrir visual studio code"
        "Que horas são?"          → "hora"
    """
    if not texto or not texto.strip():
        logger.debug("normalizador: texto vazio ou None.")
        return None

    texto_original = texto.strip()

    # ── 1. Limpeza ──
    texto_limpo = _limpar(texto_original)
    if not texto_limpo:
        logger.debug("normalizador: texto ficou vazio após limpeza.")
        return None

    # ── 2. Tokenização ──
    tokens = _tokenizar(texto_limpo)
    if not tokens:
        return None

    # ── 3. Encontrar verbo (varredura completa) ──
    verbo_info = _encontrar_verbo(tokens)

    if verbo_info is None:
        # Nenhum verbo conhecido encontrado.
        # Pode ser um comando fixo como "hora", "data".
        # Remove descartáveis e retorna o que sobrar.
        restante = _remover_descartaveis(tokens)
        if not restante:
            logger.debug("normalizador: sem verbo e sem tokens após remoção.")
            _exibir_debug(texto_original, texto_limpo, tokens, None, None, None)
            return None

        resultado = " ".join(restante).strip()
        logger.debug("normalizador: sem verbo, retornando texto limpo=%r", resultado)
        _exibir_debug(texto_original, texto_limpo, tokens, None, None, resultado)
        return resultado

    idx_verbo, verbo_canonico = verbo_info

    # ── 4. Extrair objeto a partir do token após o verbo ──
    objeto = _extrair_objeto(tokens, idx_verbo + 1)

    if not objeto:
        logger.debug(
            "normalizador: verbo '%s' encontrado mas sem objeto identificável.",
            verbo_canonico,
        )
        _exibir_debug(texto_original, texto_limpo, tokens, verbo_info, None, None)
        return None

    # ── 5. Montar resultado canônico ──
    resultado = f"{verbo_canonico} {objeto}"
    logger.debug("normalizador: normalizado=%r", resultado)
    _exibir_debug(texto_original, texto_limpo, tokens, verbo_info, objeto, resultado)
    return resultado
