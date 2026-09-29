from .catalogo_verbo import MAPA_VERBOS, VERBOS_POR_ACAO, PALAVRAS_DESCARTE, VERBO_ABRIR_SITE_CANONICO
from .catalogo_app import (
    CATALOGO_APPS,
    MAPA_APPS,
    AppInfo,
    normalizar_nome_app,
    resolver_nome_app,
)
from .catalogo_site import CATALOGO_SITES, SiteInfo
from .catalogo_atalho import CATALOGO_ATALHOS, AtalhoInfo, SINONIMOS_GENERICOS

__all__ = [
    "MAPA_VERBOS",
    "VERBOS_POR_ACAO",
    "PALAVRAS_DESCARTE",
    "VERBO_ABRIR_SITE_CANONICO",
    "MAPA_APPS",
    "CATALOGO_APPS",
    "AppInfo",
    "normalizar_nome_app",
    "resolver_app",
    "resolver_nome_app",
    "CATALOGO_SITES",
    "SiteInfo",
    "CATALOGO_ATALHOS",
    "AtalhoInfo",
    "SINONIMOS_GENERICOS",
]
