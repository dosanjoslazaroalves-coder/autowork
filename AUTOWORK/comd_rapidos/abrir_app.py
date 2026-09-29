from __future__ import annotations

import logging
import re
import time

import pyautogui

from sistema_toke.catalogo.catalogo_app import resolver_nome_app
from sistema_toke.contrato import montar

logger = logging.getLogger(__name__)

_RE_NOME_APP_SEGURO = re.compile(r"^[a-zA-Z0-9\s\-_.+áéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ]+$")


def abrir_app(nome: str) -> dict:
    """Abre um aplicativo pelo menu Iniciar e tenta confirmar a janela resultante."""
    if not nome or not nome.strip():
        logger.warning("Abrir app: nome vazio ou nulo.")
        return montar(
            executado=False,
            confirmado=False,
            mensagem="Nome do aplicativo não informado.",
            erro="Nome vazio",
        )

    nome_limpo = resolver_nome_app(nome)
    if nome_limpo is None:
        logger.warning("Abrir app: aplicativo fora do catalogo: %r", nome)
        return montar(
            executado=False,
            confirmado=False,
            mensagem=f"Aplicativo não cadastrado no catálogo: {nome.strip()}",
            erro="Aplicativo não cadastrado",
        )

    if not _RE_NOME_APP_SEGURO.match(nome_limpo) or len(nome_limpo) > 100:
        logger.warning("Abrir app: nome contém caracteres não permitidos: %r", nome)
        return montar(
            executado=False,
            confirmado=False,
            mensagem=f"Nome de aplicativo inválido ou não seguro: {nome}",
            erro="Nome contém caracteres inválidos",
        )

    from sistema_toke.verificador import capturar_janela_ativa, esperar_titulo_compativel

    antes = capturar_janela_ativa()
    hwnd_antes = antes.hwnd if antes else None
    logger.info("Abrindo aplicativo de forma segura: %s", nome_limpo)

    try:
        pyautogui.press("win")
        time.sleep(0.4)
        escrever = getattr(pyautogui, "write", pyautogui.typewrite)
        escrever(nome_limpo)
        time.sleep(0.35)
        pyautogui.press("enter")
    except Exception as exc:
        logger.exception("Erro ao tentar abrir aplicativo '%s': %s", nome_limpo, exc)
        return montar(
            executado=False,
            confirmado=False,
            mensagem=f"Erro ao tentar abrir o aplicativo {nome_limpo}: {exc}",
            erro=str(exc),
        )

    encontrada = esperar_titulo_compativel(
        nome_limpo,
        hwnd_anterior=hwnd_antes,
        timeout_ms=2500,
    )
    if encontrada is not None:
        return montar(
            executado=True,
            confirmado=True,
            mensagem=f"{nome_limpo} aberto.",
            detalhes={"app": nome_limpo, "janela": str(encontrada)},
        )

    return montar(
        executado=True,
        confirmado=False,
        mensagem=(
            f"Pedido para abrir {nome_limpo} enviado, "
            "mas a janela do aplicativo não foi confirmada."
        ),
        detalhes={"app": nome_limpo, "hwnd_antes": hwnd_antes},
    )
