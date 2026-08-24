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

from sistema_toke.catalogo import (
    CATALOGO_ACOES,
    CATALOGO_SITES,
    COMANDOS_FIXOS,
    MAPA_APPS,
    MAPA_SITES,
    MAPA_TOKEN_PARA_ACOES,
    MAPA_VERBOS,
)
from sistema_toke.normalizador import normalizar

logger = logging.getLogger(__name__)


def _gerar_fala(acao: str, parametros: Dict[str, Any], sucesso: bool = True) -> str:

    if not sucesso:
        return "Não foi possível executar o comando."

    acoes_fala = {
        "abrir_app": "Abrindo {nome}.",
        "abrir_site": "Abrindo Site {url}.",
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

    return {
        "acao": acao,
        "parametros": parametros,
        "confirmacao": confirmacao,
        "confianca": confianca,
        "fala": _gerar_fala(acao, parametros),
    }


def _resolver_acao_por_token(primeiro_token: str, objeto: Optional[str]) -> Optional[Dict[str, Any]]:

    acoes_possiveis = MAPA_TOKEN_PARA_ACOES.get(primeiro_token)

    if not acoes_possiveis:
        return None

    if len(acoes_possiveis) == 1:
        nome_acao = acoes_possiveis[0]
        return _montar_comando_com_objeto(nome_acao, objeto)

    if objeto:
        objeto_lower = objeto.lower()

        if "abrir_app" in acoes_possiveis and MAPA_APPS.get(objeto_lower):
            logger.debug(
                "parser: desempatado 'abrir_app' por objeto='%s' (encontrado em MAPA_APPS)",
                objeto,
            )
            return _montar_comando_com_objeto("abrir_app", objeto)

        for nome_acao in acoes_possiveis:
            info = CATALOGO_ACOES.get(nome_acao)
            if info and objeto_lower in info.nome:
                logger.debug(
                    "parser: desempatado '%s' por objeto='%s'",
                    nome_acao, objeto,
                )
                return _montar_comando_com_objeto(nome_acao, objeto)

    logger.debug(
        "parser: múltiplas ações para '%s', usando primeira: %s",
        primeiro_token, acoes_possiveis[0],
    )
    return _montar_comando_com_objeto(acoes_possiveis[0], objeto)


def _montar_comando_com_objeto(nome_acao: str, objeto: Optional[str]) -> Optional[Dict[str, Any]]:

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

    if info.parametros:
        return _montar_comando(nome_acao, {info.parametros[0]: objeto or ""})

    return _montar_comando(nome_acao, {})


def _extrair_verbo_e_objeto(normalizado: str) -> tuple[Optional[str], Optional[str]]:
    texto = normalizado.strip()
    if not texto:
        return None, None

    verbos_canonicos = sorted(set(MAPA_VERBOS.values()), key=len, reverse=True)
    for verbo in verbos_canonicos:
        if texto == verbo:
            return verbo, None

        prefixo = f"{verbo} "
        if texto.startswith(prefixo):
            objeto = texto[len(prefixo):].strip()
            return verbo, objeto if objeto else None

    partes = texto.split(maxsplit=1)
    primeiro = partes[0]
    resto = partes[1] if len(partes) > 1 else None
    return primeiro, resto


def parse(texto: str) -> Optional[Dict[str, Any]]:

    if not texto or not texto.strip():
        logger.debug("parser: texto vazio.")
        return None

    logger.debug("parser: texto original='%s'", texto)

    normalizado = normalizar(texto)
    if normalizado is None:
        logger.debug("parser: normalização falhou.")
        return None

    logger.debug("parser: normalizado='%s'", normalizado)

    comando = COMANDOS_FIXOS.get(normalizado)
    if comando is not None:
        logger.debug("parser: comando fixo reconhecido: %s", comando["acao"])
        return _montar_comando(comando["acao"], comando.get("parametros", {}))

    verbo, objeto = _extrair_verbo_e_objeto(normalizado)
    if verbo is None:
        logger.debug("parser: frase vazia após normalização.")
        return None

    logger.debug("parser: verbo=%r objeto=%r", verbo, objeto)

    comando = _resolver_acao_por_token(verbo, objeto)
    if comando is not None:
        return comando

    logger.debug("parser: comando não reconhecido: '%s'.", normalizado)
    return None

