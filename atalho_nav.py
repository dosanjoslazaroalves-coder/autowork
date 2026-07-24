
from __future__ import annotations

import logging
from typing import Callable

import pyautogui
import time

logger = logging.getLogger(__name__)


class AtalhoNav:

    def __init__(self, pausa: float = 0.3) -> None:
        self.logger = logging.getLogger(__name__)
        self.pausa = pausa

    # ── Auto-registro ──────────────────────────

    def registrar_no_executor(self, registrar_fn: Callable) -> None:
        """Registra todos os métodos no executor (Registry Pattern)."""
        # Abas
        registrar_fn("nova_aba", self.nova_aba)
        registrar_fn("fechar_aba", self.fechar_aba)
        registrar_fn("reabrir_aba", self.reabrir_aba)
        registrar_fn("proxima_aba", self.proxima_aba)
        registrar_fn("aba_anterior", self.aba_anterior)

        # Página
        registrar_fn("atualizar_pagina", self.atualizar_pagina)
        registrar_fn("atualizacao_forcada", self.atualizacao_forcada)
        registrar_fn("barra_endereco", self.barra_endereco)
        registrar_fn("voltar_pagina", self.voltar_pagina)
        registrar_fn("avancar_pagina", self.avancar_pagina)
        registrar_fn("pagina_inicial", self.pagina_inicial)

        # Navegação interna
        registrar_fn("historico", self.historico)
        registrar_fn("downloads", self.downloads)
        registrar_fn("favoritos", self.favoritos)
        registrar_fn("buscar_na_pagina", self.buscar_na_pagina)

        # Janelas
        registrar_fn("janela_anonima", self.janela_anonima)
        registrar_fn("nova_janela", self.nova_janela)
        registrar_fn("fechar_janela_nav", self.fechar_janela_nav)

        # Ações de página
        registrar_fn("salvar_pagina", self.salvar_pagina)
        registrar_fn("imprimir_pagina", self.imprimir_pagina)

        # Zoom
        registrar_fn("zoom_mais", self.zoom_mais)
        registrar_fn("zoom_menos", self.zoom_menos)
        registrar_fn("zoom_padrao", self.zoom_padrao)

        # DevTools / Inspecionar
        registrar_fn("devtools", self.devtools)
        registrar_fn("inspecionar_elemento", self.inspecionar_elemento)

        self.logger.info(
            "AtalhoNav: todos os métodos registrados no executor."
        )

    # ══════════════════════════════════════════════
    # Abas
    # ══════════════════════════════════════════════

    def nova_aba(self) -> None:
        """Abre uma nova aba (Ctrl + T)."""
        self.logger.info("Nova aba")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "t")

    def fechar_aba(self) -> None:
        """Fecha a aba atual (Ctrl + W)."""
        self.logger.info("Fechando aba")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "w")

    def reabrir_aba(self) -> None:
        """Reabre a última aba fechada (Ctrl + Shift + T)."""
        self.logger.info("Reabrindo aba")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "shift", "t")

    def proxima_aba(self) -> None:
        """Vai para a próxima aba (Ctrl + Tab)."""
        self.logger.info("Próxima aba")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "tab")

    def aba_anterior(self) -> None:
        """Vai para a aba anterior (Ctrl + Shift + Tab)."""
        self.logger.info("Aba anterior")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "shift", "tab")

    # ══════════════════════════════════════════════
    # Página
    # ══════════════════════════════════════════════

    def atualizar_pagina(self) -> None:
        """Atualiza a página atual (F5)."""
        self.logger.info("Atualizando página")
        time.sleep(self.pausa)
        pyautogui.press("f5")

    def atualizacao_forcada(self) -> None:
        """Atualização forçada (Ctrl + F5)."""
        self.logger.info("Atualização forçada")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "f5")

    def barra_endereco(self) -> None:
        """Foca na barra de endereço (Ctrl + L)."""
        self.logger.info("Barra de endereço")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "l")

    def voltar_pagina(self) -> None:
        """Volta para a página anterior (Alt + ←)."""
        self.logger.info("Voltando página")
        time.sleep(self.pausa)
        pyautogui.hotkey("alt", "left")

    def avancar_pagina(self) -> None:
        """Avança para a próxima página (Alt + →)."""
        self.logger.info("Avançando página")
        time.sleep(self.pausa)
        pyautogui.hotkey("alt", "right")

    def pagina_inicial(self) -> None:
        """Vai para a página inicial (Alt + Home)."""
        self.logger.info("Página inicial")
        time.sleep(self.pausa)
        pyautogui.hotkey("alt", "home")

    # ══════════════════════════════════════════════
    # Navegação interna do navegador
    # ══════════════════════════════════════════════

    def historico(self) -> None:
        """Abre o histórico (Ctrl + H)."""
        self.logger.info("Abrindo histórico")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "h")

    def downloads(self) -> None:
        """Abre a página de downloads (Ctrl + J)."""
        self.logger.info("Abrindo downloads")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "j")

    def favoritos(self) -> None:
        """Adiciona aos favoritos (Ctrl + D)."""
        self.logger.info("Adicionando favoritos")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "d")

    def buscar_na_pagina(self) -> None:
        """Abre a busca na página (Ctrl + F)."""
        self.logger.info("Buscando na página")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "f")

    # ══════════════════════════════════════════════
    # Janelas do navegador
    # ══════════════════════════════════════════════

    def janela_anonima(self) -> None:
        """Abre uma janela anônima/privada (Ctrl + Shift + N)."""
        self.logger.info("Janela anônima")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "shift", "n")

    def nova_janela(self) -> None:
        """Abre uma nova janela (Ctrl + N)."""
        self.logger.info("Nova janela")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "n")

    def fechar_janela_nav(self) -> None:
        """Fecha a janela atual do navegador (Ctrl + Shift + W)."""
        self.logger.info("Fechando janela do navegador")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "shift", "w")

    # ══════════════════════════════════════════════
    # Ações de página
    # ══════════════════════════════════════════════

    def salvar_pagina(self) -> None:
        """Salva a página atual (Ctrl + S)."""
        self.logger.info("Salvando página")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "s")

    def imprimir_pagina(self) -> None:
        """Abre a impressão da página (Ctrl + P)."""
        self.logger.info("Imprimindo página")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "p")

    # ══════════════════════════════════════════════
    # Zoom
    # ══════════════════════════════════════════════

    def zoom_mais(self) -> None:
        """Aumenta o zoom (Ctrl + '+')."""
        self.logger.info("Aumentando zoom")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "+")

    def zoom_menos(self) -> None:
        """Diminui o zoom (Ctrl + '-')."""
        self.logger.info("Diminuindo zoom")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "-")

    def zoom_padrao(self) -> None:
        """Reseta o zoom para o padrão (Ctrl + '0')."""
        self.logger.info("Zoom padrão")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "0")

    # ══════════════════════════════════════════════
    # DevTools / Inspecionar
    # ══════════════════════════════════════════════

    def devtools(self) -> None:
        """Abre as ferramentas do desenvolvedor (F12)."""
        self.logger.info("Abrindo DevTools")
        time.sleep(self.pausa)
        pyautogui.press("f12")

    def inspecionar_elemento(self) -> None:
        """Abre o inspetor de elementos (Ctrl + Shift + C)."""
        self.logger.info("Inspecionando elemento")
        time.sleep(self.pausa)
        pyautogui.hotkey("ctrl", "shift", "c")

