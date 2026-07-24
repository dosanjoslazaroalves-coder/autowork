"""
parser.py — Parser rápido de comandos para AUTOWORK.

Responsabilidade única:
    Receber texto normalizado e descobrir qual ação o usuário deseja,
    consultando o catálogo de ações.

Sem IA. Sem Ollama. Sem LLM.
Sem if/elif para cada ação.
APENAS lookup no CATALOGO_ACOES e MAPA_TOKEN_PARA_ACOES.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from catalogo import (
    CATALOGO_ACOES,
    CATALOGO_SITES,
    COMANDOS_FIXOS,
    MAPA_APPS,
    MAPA_SITES,
    MAPA_TOKEN_PARA_ACOES,
)
from normalizador import normalizar

logger = logging.getLogger(__name__)


def _gerar_fala(acao: str, parametros: Dict[str, Any], sucesso: bool = True) -> str:
    """Gera uma mensagem de fala amigável para o usuário."""
    if not sucesso:
        return "Não foi possível executar o comando."

    acoes_fala = {
        "abrir_app": "Abrindo {nome}.",
        "abrir_site": "Abrindo {url}.",
        "informar_hora": "Consultando a hora atual.",
        "informar_data": "Consultando a data atual.",
    }

    template = acoes_fala.get(acao, "Comando reconhecido.")
    try:
        return template.format(**parametros)
    except (KeyError, ValueError):
        return template


def _montar_comando(
    acao: str,
    parametros: Dict[str, Any],
    confianca: float = 1.0,
    confirmacao: bool = False,
) -> Dict[str, Any]:
    """Monta o dicionário de comando no formato padrão."""
    return {
        "acao": acao,
        "parametros": parametros,
        "confirmacao": confirmacao,
        "confianca": confianca,
        "fala": _gerar_fala(acao, parametros),
    }


def _resolver_acao_por_token(primeiro_token: str, objeto: Optional[str]) -> Optional[Dict[str, Any]]:
    """Descobre a ação a partir do primeiro token da frase normalizada.

    Estratégia:
        1. Consulta MAPA_TOKEN_PARA_ACOES[primeiro_token]
        2. Se retornar apenas 1 ação → usa ela
        3. Se retornar múltiplas (ex: "encaixar") → usa o objeto para desempatar
        4. Se a ação for "abrir_app" → resolve o nome do app via MAPA_APPS
    """
    acoes_possiveis = MAPA_TOKEN_PARA_ACOES.get(primeiro_token)

    if not acoes_possiveis:
        return None

    # Caso 1: apenas uma ação possível
    if len(acoes_possiveis) == 1:
        nome_acao = acoes_possiveis[0]
        return _montar_comando_com_objeto(nome_acao, objeto)

    # Caso 2: múltiplas ações (ex: "abrir_app" + "abrir_site")
    # Desambiguação inteligente: verifica se o objeto é site, app ou janela
    if objeto:
        objeto_lower = objeto.lower()

        # Se abrir_site e abrir_app estão empatados, consulta MAPA_SITES primeiro
        if "abrir_site" in acoes_possiveis and "abrir_app" in acoes_possiveis:
            # Verifica se o objeto é um site conhecido
            if MAPA_SITES.get(objeto_lower):
                logger.debug(
                    "parser: desempatado 'abrir_site' por objeto='%s' (encontrado em MAPA_SITES)",
                    objeto,
                )
                return _montar_comando_com_objeto("abrir_site", objeto)
            # Se não for site, tenta como app
            if MAPA_APPS.get(objeto_lower):
                logger.debug(
                    "parser: desempatado 'abrir_app' por objeto='%s' (encontrado em MAPA_APPS)",
                    objeto,
                )
                return _montar_comando_com_objeto("abrir_app", objeto)

        # Desambiguação genérica: verifica se objeto está no nome da ação
        for nome_acao in acoes_possiveis:
            info = CATALOGO_ACOES.get(nome_acao)
            if info and objeto_lower in info.nome:
                logger.debug(
                    "parser: desempatado '%s' por objeto='%s'",
                    nome_acao, objeto,
                )
                return _montar_comando_com_objeto(nome_acao, objeto)

    # Se não conseguiu desempatar, tenta abrir_site primeiro (mais provável)
    if "abrir_site" in acoes_possiveis:
        logger.debug(
            "parser: sem desempate claro, tentando 'abrir_site' para '%s'",
            primeiro_token,
        )
        return _montar_comando_com_objeto("abrir_site", objeto)

    logger.debug(
        "parser: múltiplas ações para '%s', usando primeira: %s",
        primeiro_token, acoes_possiveis[0],
    )
    return _montar_comando_com_objeto(acoes_possiveis[0], objeto)


def _montar_comando_com_objeto(nome_acao: str, objeto: Optional[str]) -> Optional[Dict[str, Any]]:
    """Monta o comando tratando o objeto de acordo com o tipo de ação."""
    info = CATALOGO_ACOES.get(nome_acao)

    if info is None:
        logger.warning("parser: ação '%s' não encontrada no catálogo.", nome_acao)
        return None

    if nome_acao == "abrir_app" and objeto:
        nome_real = MAPA_APPS.get(objeto.lower())
        if nome_real:
            logger.debug(
                "parser: app resolvido: alias='%s' → nome_real='%s'",
                objeto, nome_real,
            )
            return _montar_comando(nome_acao, {"nome": nome_real})

        logger.debug("parser: app '%s' não encontrado no MAPA_APPS.", objeto)
        return None

    # Ação abrir_site → resolve a URL do site via MAPA_SITES e CATALOGO_SITES
    if nome_acao == "abrir_site" and objeto:
        site_canonico = MAPA_SITES.get(objeto.lower())
        if site_canonico:
            site_info = CATALOGO_SITES.get(site_canonico)
            if site_info:
                logger.debug(
                    "parser: site resolvido: alias='%s' → url='%s'",
                    objeto, site_info.url,
                )
                return _montar_comando(nome_acao, {"url": site_info.url})

        logger.debug(
            "parser: site '%s' não encontrado no CATALOGO_SITES.", objeto,
        )
        return None

    # Demais ações (janela, hora, etc.) → sem parâmetros ou com objeto direto
    if info.parametros:
        return _montar_comando(nome_acao, {info.parametros[0]: objeto or ""})

    return _montar_comando(nome_acao, {})


def _extrair_primeiro_token(normalizado: str) -> tuple[Optional[str], Optional[str]]:
    """Extrai o primeiro token (verbo/acao) e o resto (objeto) da frase normalizada."""
    partes = normalizado.strip().split(maxsplit=1)
    if not partes:
        return None, None
    primeiro = partes[0]
    resto = partes[1] if len(partes) > 1 else None
    return primeiro, resto


def parse(texto: str) -> Optional[Dict[str, Any]]:
    """Tenta reconhecer um comando rápido a partir do texto.

    Fluxo:
        1. Normaliza o texto (verbo + objeto)
        2. Extrai o primeiro token (verbo)
        3. Consulta MAPA_TOKEN_PARA_ACOES para descobrir a ação
        4. Se for "abrir_app", resolve o nome do aplicativo

    Args:
        texto: Texto livre falado pelo usuário.

    Returns:
        Dicionário no formato:
            { "acao": str, "parametros": dict, "confirmacao": bool,
              "confianca": float, "fala": str }
        ou None se o comando não foi reconhecido.

    Exemplos:
        parse("fecha a janela")
        → {"acao": "fechar_janela", "parametros": {}, ...}

        parse("abra o chrome")
        → {"acao": "abrir_app", "parametros": {"nome": "Google Chrome"}, ...}

        parse("hora")
        → {"acao": "informar_hora", "parametros": {}, ...}
    """
    if not texto or not texto.strip():
        logger.debug("parser: texto vazio.")
        return None

    logger.debug("parser: texto original='%s'", texto)

    # 1. Normaliza o texto
    normalizado = normalizar(texto)
    if normalizado is None:
        logger.debug("parser: normalização falhou.")
        return None

    logger.debug("parser: normalizado='%s'", normalizado)

    # 2. Tenta comando fixo primeiro (match exato, ex: "hora", "data")
    comando = COMANDOS_FIXOS.get(normalizado)
    if comando is not None:
        logger.debug("parser: comando fixo reconhecido: %s", comando["acao"])
        return _montar_comando(comando["acao"], comando.get("parametros", {}))

    # 3. Extrai primeiro token (verbo) e objeto
    primeiro_token, objeto = _extrair_primeiro_token(normalizado)
    if primeiro_token is None:
        logger.debug("parser: frase vazia após normalização.")
        return None

    logger.debug("parser: token=%r objeto=%r", primeiro_token, objeto)

    # 4. Resolve ação via catálogo
    comando = _resolver_acao_por_token(primeiro_token, objeto)
    if comando is not None:
        return comando

    # 5. Não reconheceu
    logger.debug("parser: comando não reconhecido: '%s'.", normalizado)
    return None

