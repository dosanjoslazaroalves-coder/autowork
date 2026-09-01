from __future__ import annotations
import logging
from typing import Any, Dict, Optional

from sistema_toke.catalogo.catalogo_app import MAPA_APPS
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
        logger.debug("Resolvedor: intenção '%s' resolvida para atalho.", acao_intencao)
        return {
            "acao": acao_intencao,
            "parametros": {}
        }
        
    
    if acao_intencao in ("abrir_app", "abrir_site", "abrir"):
        if not alvo:
            logger.warning("Resolvedor: intenção de abrir sem alvo.")
            return None
            
        alvo_lower = alvo.lower()
        
        
        nome_real = MAPA_APPS.get(alvo_lower)
        if nome_real:
            logger.debug("Resolvedor: '%s' resolvido para app '%s'", alvo_lower, nome_real)
            return {
                "acao": "abrir_app",
                "parametros": {"nome": nome_real}
            }
            
        
        from sistema_toke.catalogo.catalogo_site import CATALOGO_SITES
        
        
        site_encontrado = None
        for key, site_info in CATALOGO_SITES.items():
            if alvo_lower == site_info.nome.lower() or alvo_lower in [s.lower() for s in site_info.sinonimos]:
                site_encontrado = site_info
                break
                
        if site_encontrado:
            logger.debug("Resolvedor: '%s' resolvido para site '%s'", alvo_lower, site_encontrado.url)
            return {
                "acao": "abrir_site",
                "parametros": {"url": site_encontrado.url}
            }
            
        logger.debug("Resolvedor: '%s' não encontrado em apps nem em sites.", alvo)
        return None

    logger.debug("Resolvedor: intenção '%s' não mapeada.", acao_intencao)
    return None

