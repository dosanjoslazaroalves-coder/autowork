
from __future__ import annotations

import logging

import pyautogui

logger = logging.getLogger(__name__)


def abrir_app(nome: str) -> None:
    
    logger.info("Abrindo aplicativo: %s", nome)

    pyautogui.press("win")
    pyautogui.sleep(0.2)
    pyautogui.typewrite(nome)
    pyautogui.press("enter")

    logger.info("Aplicativo '%s' aberto com sucesso.", nome)

