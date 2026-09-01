from __future__ import annotations
import logging
from typing import Any, Dict, Optional, Tuple

from sistema_toke.catalogo.catalogo_verbo import MAPA_VERBOS, VERBOS_POR_ACAO
from sistema_toke.catalogo.catalogo_atalho import CATALOGO_ATALHOS
from sistema_toke.catalogo.catalogo_app import MAPA_APPS
from sistema_toke.catalogo.catalogo_site import CATALOGO_SITES
from sistema_toke.normalizador import normalizar

logger = logging.getLogger(__name__)

COMANDOS_FIXOS = {
    "hora": {"intencao": "informar_hora", "acao": "informar_hora", "parametros": {}, "pronto": True},
    "horas": {"intencao": "informar_hora", "acao": "informar_hora", "parametros": {}, "pronto": True},
    "data": {"intencao": "informar_data", "acao": "informar_data", "parametros": {}, "pronto": True},
    "dia": {"intencao": "informar_data", "acao": "informar_data", "parametros": {}, "pronto": True},
    "abrir nova aba": {"intencao": "nova_aba", "acao": "nova_aba", "parametros": {}, "pronto": True},
    "abrir nova guia": {"intencao": "nova_aba", "acao": "nova_aba", "parametros": {}, "pronto": True},
    "aba anterior": {"intencao": "aba_anterior", "acao": "aba_anterior", "parametros": {}, "pronto": True},
    "barra endereco": {"intencao": "barra_endereco", "acao": "barra_endereco", "parametros": {}, "pronto": True},
    "pagina inicial": {"intencao": "pagina_inicial", "acao": "pagina_inicial", "parametros": {}, "pronto": True},
    "janela anonima": {"intencao": "janela_anonima", "acao": "janela_anonima", "parametros": {}, "pronto": True},
    "zoom padrao": {"intencao": "zoom_padrao", "acao": "zoom_padrao", "parametros": {}, "pronto": True},
    "abrir devtools": {"intencao": "devtools", "acao": "devtools", "parametros": {}, "pronto": True},
}

def _construir_mapa_token_acoes() -> Dict[str, list[str]]:
    mapa: Dict[str, list[str]] = {}
    for acao_nome, info in CATALOGO_ATALHOS.items():
        for sinonimo in info["sinonimos"]:
            if sinonimo not in mapa:
                mapa[sinonimo] = []
            mapa[sinonimo].append(acao_nome)
    return mapa

MAPA_TOKEN_PARA_ACOES: Dict[str, list[str]] = _construir_mapa_token_acoes()

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


def _classificar_alvo_abrir(objeto: Optional[str]) -> str:
    if not objeto:
        return "abrir"

    alvo = objeto.lower()
    if alvo in MAPA_APPS:
        return "abrir_app"

    for site in CATALOGO_SITES.values():
        if alvo == site.nome.lower() or alvo in [s.lower() for s in site.sinonimos]:
            return "abrir_site"

    return "abrir"

def _resolver_intencao_por_token(primeiro_token: str, objeto: Optional[str]) -> Optional[Dict[str, Any]]:
    if primeiro_token in VERBOS_POR_ACAO.get("abrir_app", set()) or primeiro_token in VERBOS_POR_ACAO.get("abrir_site", set()):
        return {"intencao": "abrir", "acao": _classificar_alvo_abrir(objeto), "alvo": objeto}

    # Tenta ver se é atalho primeiro
    acoes_possiveis = MAPA_TOKEN_PARA_ACOES.get(primeiro_token)
    if acoes_possiveis:
        if len(acoes_possiveis) == 1:
            return {"intencao": acoes_possiveis[0], "acao": acoes_possiveis[0], "alvo": objeto}
            
        if objeto:
            objeto_lower = objeto.lower()
            for nome_acao in acoes_possiveis:
                info = CATALOGO_ATALHOS.get(nome_acao)
                if info and objeto_lower in info["nome"]:
                    return {"intencao": nome_acao, "acao": nome_acao, "alvo": objeto}
                    
        return {"intencao": acoes_possiveis[0], "acao": acoes_possiveis[0], "alvo": objeto}

    return None

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
        logger.debug("parser: comando fixo reconhecido.")
        return comando

    verbo, objeto = _extrair_verbo_e_objeto(normalizado)
    if verbo is None:
        logger.debug("parser: frase vazia após normalização.")
        return None

    logger.debug("parser: verbo=%r objeto=%r", verbo, objeto)

    intencao = _resolver_intencao_por_token(verbo, objeto)
    if intencao is not None:
        return intencao

    logger.debug("parser: comando não reconhecido: '%s'.", normalizado)
    return None
