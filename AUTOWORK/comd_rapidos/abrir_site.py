from __future__ import annotations

import logging
import webbrowser
from urllib.parse import urlparse

from sistema_toke.contrato import montar

logger = logging.getLogger(__name__)

ESQUEMAS_PERMITIDOS = frozenset({"http", "https"})


def abrir_site(url: str) -> dict:
    """Abre um site no navegador padrão com validação de segurança e verificação de execução."""
    if not url or not url.strip():
        logger.error("URL inválida: valor vazio ou None.")
        return montar(
            executado=False,
            confirmado=False,
            mensagem="URL não pode ser vazia.",
            erro="URL vazia",
        )

    url = url.strip()

    parsed_inicial = urlparse(url)
    if parsed_inicial.scheme and parsed_inicial.scheme.lower() not in ESQUEMAS_PERMITIDOS:
        logger.warning("Tentativa de abrir URL com esquema não permitido: %r", url)
        return montar(
            executado=False,
            confirmado=False,
            mensagem=f"URL não permitida por motivos de segurança: {url}",
            erro=f"Esquema {parsed_inicial.scheme!r} não permitido",
        )

    # Se a URL não contiver esquema, assume HTTPS com segurança
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme not in ESQUEMAS_PERMITIDOS or not parsed.netloc:
        logger.warning("Tentativa de abrir URL com esquema não permitido ou inválida: %r", url)
        return montar(
            executado=False,
            confirmado=False,
            mensagem=f"URL não permitida ou inválida por motivos de segurança: {url}",
            erro=f"Esquema {scheme!r} não permitido",
        )

    logger.info("Abrindo site seguro: %s", url)

    from sistema_toke.verificador import (
        capturar_janela_ativa,
        esperar_titulo_compativel,
        janela_parece_navegador,
    )

    antes = capturar_janela_ativa()
    hwnd_antes = antes.hwnd if antes else None

    try:
        aberto = webbrowser.open(url)
    except Exception as exc:
        logger.exception("Erro inesperado ao abrir site '%s': %s", url, exc)
        return montar(
            executado=False,
            confirmado=False,
            mensagem=f"Erro ao abrir o site {url}: {exc}",
            erro=str(exc),
        )

    if not aberto:
        logger.error("Falha ao abrir navegador para: %s", url)
        return montar(
            executado=False,
            confirmado=False,
            mensagem=f"Não foi possível abrir o navegador para: {url}",
            erro="webbrowser.open retornou False",
        )

    # Extrai o nome central do domínio para verificação de título (ex: 'youtube' de 'www.youtube.com')
    dominio = parsed.netloc.lower()
    partes = dominio.split(".")
    termo_busca = partes[-2] if len(partes) >= 2 and partes[-2] not in ("com", "org", "net", "gov", "edu") else partes[0]

    encontrada = esperar_titulo_compativel(
        termo_busca,
        hwnd_anterior=hwnd_antes,
        timeout_ms=1500,
    )

    detalhes = {"url": url}
    if encontrada is not None:
        detalhes["janela"] = str(encontrada)
    elif janela_parece_navegador(capturar_janela_ativa()):
        detalhes["navegador_ativo"] = True

    return montar(
        executado=True,
        confirmado=True,
        mensagem=f"Site {url} aberto com sucesso.",
        detalhes=detalhes,
    )
