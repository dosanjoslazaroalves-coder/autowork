from __future__ import annotations
import logging
import re
from typing import Any, Dict, Optional, Tuple

from sistema_toke.catalogo.catalogo_verbo import MAPA_VERBOS, VERBOS_POR_ACAO
from sistema_toke.catalogo.catalogo_atalho import (
    CATALOGO_ATALHOS,
    SINONIMOS_GENERICOS,
)
from sistema_toke.catalogo.catalogo_app import MAPA_APPS, resolver_nome_app
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
    "abrir inspetor": {"intencao": "devtools", "acao": "devtools", "parametros": {}, "pronto": True},
    "abrir inspector": {"intencao": "devtools", "acao": "devtools", "parametros": {}, "pronto": True},
    "abrir console": {"intencao": "console", "acao": "console", "parametros": {}, "pronto": True},
}

_SINONIMOS_GENERICOS = {s.lower() for s in SINONIMOS_GENERICOS}

# Palavras de objeto que sozinhas não devem decidir a ação.
_PALAVRAS_FRACAS = {
    "pagina", "página", "janela", "tela", "site", "aba", "guia",
    "zoom", "app", "aplicativo", "programa", "tab",
}

_VERBOS_ABRIR = VERBOS_POR_ACAO.get("abrir_app", set()) | VERBOS_POR_ACAO.get("abrir_site", set()) | {"abrir site"}
_VERBOS_MOSTRAR = {"mostrar", "exibir"}


def _construir_mapa_token_acoes() -> Dict[str, list[str]]:
    mapa: Dict[str, list[str]] = {}
    for acao_nome, info in CATALOGO_ATALHOS.items():
        for sinonimo in info["sinonimos"]:
            chave = sinonimo.lower()
            if chave not in mapa:
                mapa[chave] = []
            if acao_nome not in mapa[chave]:
                mapa[chave].append(acao_nome)
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


def _limpar_alvo_abrir(objeto: Optional[str]) -> str:
    if not objeto:
        return ""
    alvo = objeto.strip()
    candidato = re.sub(
        r"^(?:o\s+|a\s+)?(?:site|pagina|página)\s+(?:d[oeao]\s+|da\s+|do\s+|de\s+)?",
        "",
        alvo,
        flags=re.IGNORECASE,
    ).strip()
    return candidato if candidato else alvo


def _eh_alvo_site(alvo: str) -> bool:
    if not alvo:
        return False
    alvo_lower = alvo.lower()
    if re.search(r"\.(?:com|org|net|io|edu|gov|tv|ai|app|dev|me)(?:\.br)?\b", alvo_lower):
        return True
    if alvo_lower.startswith(("http://", "https://", "www.")):
        return True
    for site in CATALOGO_SITES.values():
        if alvo_lower == site.nome.lower() or alvo_lower in [s.lower() for s in site.sinonimos]:
            return True
    return False


def _classificar_alvo_abrir(objeto: Optional[str]) -> tuple[str, Optional[str]]:
    if not objeto:
        return "abrir", None

    alvo_original = objeto.strip()
    alvo_limpo = _limpar_alvo_abrir(alvo_original)

    if resolver_nome_app(alvo_original):
        return "abrir_app", alvo_original
    if resolver_nome_app(alvo_limpo):
        return "abrir_app", alvo_limpo

    if _eh_alvo_site(alvo_limpo):
        return "abrir_site", alvo_limpo
    if _eh_alvo_site(alvo_original):
        return "abrir_site", alvo_original

    if re.search(r"\b(?:site|pagina|página)\b", alvo_original, re.IGNORECASE) and alvo_limpo:
        return "abrir_site", alvo_limpo

    return "abrir", alvo_original


def _pontuar_acao(nome_acao: str, objeto_lower: str) -> int:
    info = CATALOGO_ATALHOS.get(nome_acao)
    if not info or not objeto_lower:
        return 0

    palavras_objeto = set(objeto_lower.split())
    score = 0
    for sinonimo in info.get("sinonimos", []):
        s = sinonimo.lower().strip()
        if not s or s in _SINONIMOS_GENERICOS:
            continue
        if s == objeto_lower or re.search(rf"\b{re.escape(s)}\b", objeto_lower):
            palavras = s.split()
            valor = 10 * len(palavras) + len(s)
            if s in _PALAVRAS_FRACAS or (len(palavras) == 1 and s in _PALAVRAS_FRACAS):
                valor = 1
            elif len(palavras) == 1 and s in palavras_objeto and s in _PALAVRAS_FRACAS:
                valor = 1
            score = max(score, valor)

    palavras_nome = set(info["nome"].replace("_", " ").split()) - {
        "fechar", "abrir", "iniciar", "executar", "de", "ou", "o", "a", "em", "para", "nav",
    }
    if palavras_objeto & palavras_nome:
        especificas = (palavras_objeto & palavras_nome) - _PALAVRAS_FRACAS
        if especificas:
            score = max(score, 5)
        else:
            score = max(score, 1)
    return score


def _melhor_acao(acoes: list[str], objeto: Optional[str]) -> Optional[str]:
    if not acoes:
        return None
    if not objeto:
        return acoes[0]

    objeto_lower = objeto.lower()
    melhor: Optional[str] = None
    melhor_score = 0
    for nome_acao in acoes:
        pontos = _pontuar_acao(nome_acao, objeto_lower)
        if pontos > melhor_score:
            melhor_score = pontos
            melhor = nome_acao
    if melhor_score > 0:
        return melhor
    return None


def _desambiguar_navegacao(verbo: str, objeto: Optional[str], acao: str) -> str:
    if not objeto:
        return acao
    obj = objeto.lower()
    tem_aba = bool(re.search(r"\b(?:aba|guia|tab)\b", obj))
    tem_pagina = bool(re.search(r"\b(?:pagina|página|site)\b", obj))

    if verbo == "voltar":
        if tem_aba and not tem_pagina:
            return "aba_anterior"
        return "voltar_pagina"
    if verbo == "avancar":
        if tem_aba and not tem_pagina:
            return "proxima_aba"
        return "avancar_pagina"
    return acao


def _resolver_intencao_por_token(primeiro_token: str, objeto: Optional[str]) -> Optional[Dict[str, Any]]:
    if primeiro_token in _VERBOS_ABRIR:
        if objeto:
            alvo_app = objeto.strip().lower()
            alvo_limpo = _limpar_alvo_abrir(objeto).lower()
            eh_app = bool(resolver_nome_app(alvo_app) or resolver_nome_app(alvo_limpo))
            eh_site = _eh_alvo_site(alvo_limpo) or _eh_alvo_site(alvo_app)
            if not eh_app and not eh_site:
                acao_atalho = _melhor_acao(list(CATALOGO_ATALHOS), objeto)
                if acao_atalho:
                    return {"intencao": acao_atalho, "acao": acao_atalho, "alvo": objeto}

        acao_abrir, alvo_resolvido = _classificar_alvo_abrir(objeto)
        return {"intencao": "abrir", "acao": acao_abrir, "alvo": alvo_resolvido}

    acoes_possiveis = MAPA_TOKEN_PARA_ACOES.get(primeiro_token)
    if acoes_possiveis:
        if len(acoes_possiveis) == 1 and not objeto:
            acao = _desambiguar_navegacao(primeiro_token, objeto, acoes_possiveis[0])
            return {"intencao": acao, "acao": acao, "alvo": objeto}

        if objeto:
            objeto_lower = objeto.lower()
            palavras_objeto = set(objeto_lower.split())

            if "fechar_janela" in acoes_possiveis:
                if resolver_nome_app(objeto_lower) or any(resolver_nome_app(p) for p in palavras_objeto):
                    return {"intencao": "fechar_janela", "acao": "fechar_janela", "alvo": objeto}

            escolhida = _melhor_acao(acoes_possiveis, objeto)
            if not escolhida and primeiro_token in ("inspecionar", "depurar"):
                escolhida = "devtools"
            if not escolhida and primeiro_token == "buscar":
                escolhida = "buscar_na_pagina"
            if not escolhida and primeiro_token in _VERBOS_MOSTRAR:
                escolhida = _melhor_acao(list(CATALOGO_ATALHOS), objeto)
            if escolhida:
                escolhida = _desambiguar_navegacao(primeiro_token, objeto, escolhida)
                return {"intencao": escolhida, "acao": escolhida, "alvo": objeto}
            return None

        acao = _desambiguar_navegacao(primeiro_token, objeto, acoes_possiveis[0])
        return {"intencao": acao, "acao": acao, "alvo": objeto}

    if primeiro_token in _VERBOS_MOSTRAR and objeto:
        acao_atalho = _melhor_acao(list(CATALOGO_ATALHOS), objeto)
        if acao_atalho:
            return {"intencao": acao_atalho, "acao": acao_atalho, "alvo": objeto}

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
        # O normalizador pode remover "site" como palavra descartável, mas
        # esse marcador explícito deve vencer um alias de aplicativo homônimo.
        if (
            intencao.get("acao") == "abrir_app"
            and re.match(
                r"^(?:abrir|abra|abre|acessar|acesse|entrar|entre)\s+"
                r"(?:o\s+|a\s+)?site\b",
                texto.strip().lower(),
            )
        ):
            intencao["acao"] = "abrir_site"
        return intencao

    logger.debug("parser: comando não reconhecido: '%s'.", normalizado)
    return None
