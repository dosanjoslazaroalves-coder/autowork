
from __future__ import annotations

import logging
from typing import Callable

import pyautogui
import time

logger = logging.getLogger(__name__)


class Janela:


    def __init__(self, pausa: float = 0.3):
        self.logger = logging.getLogger(__name__)
        self.pausa = pausa

    # ── Auto-registro ──────────────────────────

    def registrar_no_executor(self, registrar_fn: Callable) -> None:

        registrar_fn("fechar_janela", self.fechar_janela)
        registrar_fn("alternar_janelas", self.alternar_janelas)
        registrar_fn("mostrar_area_de_trabalho", self.mostrar_area_de_trabalho)
        registrar_fn("maximizar_janela", self.maximizar_janela)
        registrar_fn(
            "restaurar_ou_minimizar_janela",
            self.restaurar_ou_minimizar_janela,
        )
        registrar_fn("mover_janela_esquerda", self.mover_janela_esquerda)
        registrar_fn("mover_janela_direita", self.mover_janela_direita)
        registrar_fn("abrir_visao_de_tarefas", self.abrir_visao_de_tarefas)
        registrar_fn("bloquear_tela", self.bloquear_tela)
        self.logger.info(
            "Janela: todos os métodos registrados no executor."
        )

    # ── Ações ──────────────────────────────────

    def fechar_janela(self) -> None:

        self.logger.info("Fechando janela")
        time.sleep(self.pausa)
        pyautogui.hotkey("alt", "f4")

    def alternar_janelas(self) -> None:

        self.logger.info("Alternando entre janelas")
        time.sleep(self.pausa)
        pyautogui.hotkey("alt", "tab")

    def mostrar_area_de_trabalho(self) -> None:

        self.logger.info("Minimizar janela")
        time.sleep(self.pausa)
        pyautogui.hotkey("win", "d")

    def maximizar_janela(self) -> None:

        self.logger.info("Maximizando janela")
        time.sleep(self.pausa)
        pyautogui.hotkey("win", "up")

    def restaurar_ou_minimizar_janela(self) -> None:

        self.logger.info("Restaurando ou minimizando janela")
        time.sleep(self.pausa)
        pyautogui.hotkey("win", "down")

    def mover_janela_esquerda(self) -> None:

        self.logger.info("Mover janela à esquerda")
        time.sleep(self.pausa)
        pyautogui.hotkey("win", "left")

    def mover_janela_direita(self) -> None:

        self.logger.info("Mover janela à direita")
        time.sleep(self.pausa)
        pyautogui.hotkey("win", "right")

    def abrir_visao_de_tarefas(self) -> None:

        self.logger.info("Abrindo visão de tarefas")
        time.sleep(self.pausa)
        pyautogui.hotkey("win", "tab")

    def bloquear_tela(self) -> None:

        self.logger.info("Bloqueando tela")
        time.sleep(self.pausa)
        pyautogui.hotkey("win", "l")

