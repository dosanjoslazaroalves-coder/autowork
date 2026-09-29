from __future__ import annotations
import logging
import re
from typing import Any, Dict, Optional

from sistema_toke.catalogo.catalogo_app import MAPA_APPS, resolver_nome_app
from sistema_toke.catalogo.catalogo_site import CATALOGO_SITES
from sistema_toke.catalogo.catalogo_atalho import CATALOGO_ATALHOS

logger = logging.getLogger(__name__)

def resolver(intencao: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not intencao:
        return None
        
    acao_intencao = intencao.get("intencao")
    alvo = intencao.get("alvo")
    
    if not acao_intencao:
        return None   

    if intencao.get("pronto"):
        return {
            "acao": acao_intencao,
            "parametros": intencao.get("parametros", {})
        }

    if acao_intencao in CATALOGO_ATALHOS:
        # Quando o comando pede para minimizar tudo/as janelas/a tela, a intenção real do usuário é mostrar a área de trabalho
        if acao_intencao == "restaurar_ou_minimizar_janela" and alvo:
            alvo_norm = alvo.lower()
            if alvo_norm in ("tudo", "todas janelas", "janelas", "tela", "telas", "as janelas", "as telas", "todas as janelas"):
                logger.debug("Resolvedor: '%s' com alvo '%s' redirecionado para mostrar_area_de_trabalho.", acao_intencao, alvo)
                return {
                    "acao": "mostrar_area_de_trabalho",
                    "parametros": {}
                }

        logger.debug("Resolvedor: intenção '%s' resolvida para atalho.", acao_intencao)
        return {
            "acao": acao_intencao,
            "parametros": {}
        }
        
    if acao_intencao in ("abrir_app", "abrir_site", "abrir"):
        if not alvo:
            logger.warning("Resolvedor: intenção de abrir sem alvo.")
            return None
            
        alvo_lower = alvo.lower().strip()
        alvo_limpo = re.sub(
            r"^(?:o\s+|a\s+)?(?:site|pagina|página)\s+(?:d[oeao]\s+|da\s+|do\s+|de\s+)?",
            "",
            alvo_lower,
            flags=re.IGNORECASE,
        ).strip()

        candidatos = [alvo_lower]
        if alvo_limpo and alvo_limpo != alvo_lower:
            candidatos.append(alvo_limpo)

        # 1. Se classificado explicitamente como abrir_app, prioriza apps
        if acao_intencao == "abrir_app" or intencao.get("acao") == "abrir_app":
            for c in candidatos:
                nome_real = resolver_nome_app(c)
                if nome_real:
                    logger.debug("Resolvedor: '%s' resolvido para app '%s'", c, nome_real)
                    return {"acao": "abrir_app", "parametros": {"nome": nome_real}}

        # 2. Tenta catálogo de sites
        site_encontrado = None
        for c in candidatos:
            for key, site_info in CATALOGO_SITES.items():
                if c == site_info.nome.lower() or c in [s.lower() for s in site_info.sinonimos]:
                    site_encontrado = site_info
                    break
            if site_encontrado:
                break

        # Tenta também se o alvo terminou com sufixo colado sem ponto pela normalização (ex: 'netflixcom')
        if not site_encontrado:
            for c in candidatos:
                for sufixo in ("combr", "com", "org", "net", "io", "tv", "ai"):
                    if c.endswith(sufixo) and len(c) > len(sufixo):
                        base = c[:-len(sufixo)].strip()
                        if base in CATALOGO_SITES:
                            site_encontrado = CATALOGO_SITES[base]
                            break
                if site_encontrado:
                    break

        if site_encontrado:
            logger.debug("Resolvedor: '%s' resolvido para site '%s'", alvo, site_encontrado.url)
            return {
                "acao": "abrir_site",
                "parametros": {"url": site_encontrado.url}
            }

        # 3. Tenta apps (se ainda não tentou)
        for c in candidatos:
            nome_real = resolver_nome_app(c)
            if nome_real:
                logger.debug("Resolvedor: '%s' resolvido para app '%s'", c, nome_real)
                return {"acao": "abrir_app", "parametros": {"nome": nome_real}}

        # 4. Formato de domínio ou URL direta
        for c in candidatos:
            if re.search(r"\.(?:com|org|net|io|edu|gov|tv|ai|app|dev|me)(?:\.br)?\b", c) or c.startswith(("http://", "https://", "www.")):
                url_final = c if c.startswith(("http://", "https://")) else f"https://{c}"
                logger.debug("Resolvedor: '%s' resolvido para URL direta '%s'", c, url_final)
                return {
                    "acao": "abrir_site",
                    "parametros": {"url": url_final}
                }

        logger.debug("Resolvedor: '%s' não encontrado em apps nem em sites.", alvo)
        return None

    logger.debug("Resolvedor: intenção '%s' não mapeada.", acao_intencao)
    return None
