"""
abrir_site.py — Abertura de sites no navegador padrão.

Responsabilidade única:
    Receber uma URL e abrir o navegador padrão utilizando exclusivamente
    a biblioteca padrão ``webbrowser``.

Uso:
    from abrir_site import abrir_site
    abrir_site("https://www.youtube.com")
"""

from __future__ import annotations

import logging
import webbrowser
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def abrir_site(url: str) -> None:


    if not url or not url.strip():
        logger.error("URL inválida: valor vazio ou None.")
        raise ValueError("URL não pode ser vazia.")

    url = url.strip()

    # Validação básica de URL (deve conter scheme e netloc)
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        logger.error("URL inválida: %r", url)
        raise ValueError(f"URL inválida: {url}")

    logger.info("Abrindo site: %s", url)

    try:
        aberto = webbrowser.open(url)

        if not aberto:
            logger.error("Falha ao abrir navegador para: %s", url)
            raise RuntimeError(
                f"Não foi possível abrir o navegador para: {url}"
            )

        logger.info("Site aberto com sucesso: %s", url)

    except RuntimeError:
        raise
    except Exception as exc:
        logger.exception(
            "Erro inesperado ao abrir site '%s': %s", url, exc
        )
        raise RuntimeError(f"Erro ao abrir o site {url}: {exc}") from exc

