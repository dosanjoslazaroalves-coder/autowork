from __future__ import annotations

import logging
from typing import Callable

import ctypes
import pyautogui
import time

from sistema_toke.contrato import montar

logger = logging.getLogger(__name__)


class Janela:

    def __init__(self, pausa: float = 0.3):
        self.logger = logging.getLogger(__name__)
        self.pausa = pausa

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
        registrar_fn("mover_janela_lado_esquerdo", self.mover_janela_esquerda)
        registrar_fn("mover_janela_lado_direito", self.mover_janela_direita)
        registrar_fn("encaixar_janela_esquerda", self.mover_janela_esquerda)
        registrar_fn("encaixar_janela_direita", self.mover_janela_direita)
        registrar_fn("abrir_visao_de_tarefas", self.abrir_visao_de_tarefas)
        registrar_fn("bloquear_tela", self.bloquear_tela)
        self.logger.info("Janela: todos os métodos registrados no executor.")

    def _sem_app_ativo(self, janela) -> dict:
        return montar(
            executado=False,
            confirmado=False,
            mensagem="Nenhuma janela de aplicativo aberta para este comando.",
            detalhes={"janela": str(janela)},
        )

    def fechar_janela(self) -> dict:
        from sistema_toke.verificador import capturar_janela_ativa, verificar_fechamento_janela

        janela = capturar_janela_ativa()
        if janela is None or janela.eh_desktop:
            self.logger.warning("Janela: nenhuma janela de aplicativo ativa para fechar.")
            return montar(
                executado=False,
                confirmado=False,
                mensagem="Nenhuma janela de aplicativo aberta para fechar.",
                detalhes={"janela": str(janela)},
            )

        nome_janela = janela.titulo or janela.classe or "janela"
        self.logger.info("Fechando janela ativa: %s (hwnd=%d)", nome_janela, janela.hwnd)
        time.sleep(self.pausa)
        pyautogui.hotkey("alt", "f4")

        fechou = verificar_fechamento_janela(janela.hwnd, timeout_ms=800)
        if fechou is True:
            return montar(
                executado=True,
                confirmado=True,
                mensagem=f"Janela '{nome_janela}' fechada com sucesso.",
                detalhes={"hwnd": janela.hwnd, "titulo": janela.titulo},
            )

        motivo = "ainda existe" if fechou is False else "não foi possível observar o sistema"
        return montar(
            executado=True,
            confirmado=False,
            mensagem=(
                f"Comando enviado, mas o fechamento da janela '{nome_janela}' "
                f"não foi confirmado ({motivo})."
            ),
            detalhes={"hwnd": janela.hwnd, "titulo": janela.titulo, "fechou": fechou},
        )

    def alternar_janelas(self) -> dict:
        from sistema_toke.verificador import capturar_janela_ativa, esperar_foreground_diferente

        antes = capturar_janela_ativa()
        if antes is None:
            return montar(
                executado=False,
                confirmado=False,
                mensagem="Não foi possível observar a janela ativa.",
            )

        time.sleep(self.pausa)
        pyautogui.hotkey("alt", "tab")
        mudou = esperar_foreground_diferente(antes.hwnd, timeout_ms=700)
        return montar(
            executado=True,
            confirmado=mudou is True,
            mensagem=(
                "Janelas alternadas com sucesso."
                if mudou is True
                else "Atalho enviado, mas a janela em primeiro plano não mudou."
            ),
            detalhes={"hwnd_antes": antes.hwnd, "mudou": mudou},
        )

    def mostrar_area_de_trabalho(self) -> dict:
        from sistema_toke.verificador import capturar_janela_ativa, esperar_desktop_ativo

        antes = capturar_janela_ativa()
        if antes is not None and antes.eh_desktop:
            return montar(
                executado=False,
                confirmado=True,
                mensagem="A área de trabalho já estava visível.",
                detalhes={"janela": str(antes)},
            )

        time.sleep(self.pausa)
        pyautogui.hotkey("win", "d")
        desktop = esperar_desktop_ativo(timeout_ms=800)
        return montar(
            executado=True,
            confirmado=desktop is True,
            mensagem=(
                "Área de trabalho exibida com sucesso."
                if desktop is True
                else "Atalho enviado, mas a área de trabalho não foi confirmada."
            ),
            detalhes={"desktop": desktop},
        )

    def maximizar_janela(self) -> dict:
        from sistema_toke.verificador import capturar_janela_ativa, consultar_janela

        antes = capturar_janela_ativa()
        if antes is None or antes.eh_desktop:
            return self._sem_app_ativo(antes)
        if antes.maximizada:
            return montar(
                executado=False,
                confirmado=True,
                mensagem="A janela já estava maximizada.",
                detalhes={"hwnd": antes.hwnd},
            )

        time.sleep(self.pausa)
        pyautogui.hotkey("win", "up")
        time.sleep(0.25)
        depois = consultar_janela(antes.hwnd) or capturar_janela_ativa()
        confirmado = bool(depois and depois.hwnd == antes.hwnd and depois.maximizada)
        return montar(
            executado=True,
            confirmado=confirmado,
            mensagem=(
                "Janela maximizada com sucesso."
                if confirmado
                else "Atalho enviado, mas a maximização não foi confirmada."
            ),
            detalhes={"hwnd": antes.hwnd, "depois": str(depois)},
        )

    def restaurar_ou_minimizar_janela(self) -> dict:
        from sistema_toke.verificador import capturar_janela_ativa, consultar_janela

        antes = capturar_janela_ativa()
        if antes is None or antes.eh_desktop:
            return self._sem_app_ativo(antes)

        time.sleep(self.pausa)
        pyautogui.hotkey("win", "down")
        time.sleep(0.25)
        depois = consultar_janela(antes.hwnd)
        confirmado = False
        if depois is None:
            # minimizada pode sair do foreground; IsIconic ainda vale se o HWND existe
            pass
        else:
            confirmado = (
                depois.minimizada
                or depois.rect != antes.rect
                or (antes.maximizada and not depois.maximizada)
            )
        if not confirmado:
            ativa = capturar_janela_ativa()
            confirmado = bool(ativa and ativa.hwnd != antes.hwnd)

        return montar(
            executado=True,
            confirmado=bool(confirmado),
            mensagem=(
                "Janela restaurada ou minimizada com sucesso."
                if confirmado
                else "Atalho enviado, mas o estado da janela não mudou de forma observável."
            ),
            detalhes={"hwnd": antes.hwnd},
        )

    def mover_janela_esquerda(self) -> dict:
        return self._mover_snap("left", "esquerda")

    def mover_janela_direita(self) -> dict:
        return self._mover_snap("right", "direita")

    def _mover_snap(self, tecla: str, lado: str) -> dict:
        from sistema_toke.verificador import capturar_janela_ativa, consultar_janela

        antes = capturar_janela_ativa()
        if antes is None or antes.eh_desktop:
            return self._sem_app_ativo(antes)

        rect_antes = antes.rect
        time.sleep(self.pausa)
        pyautogui.hotkey("win", tecla)
        time.sleep(0.25)
        depois = consultar_janela(antes.hwnd) or capturar_janela_ativa()
        confirmado = False
        if depois is not None and depois.rect and rect_antes:
            if lado == "esquerda":
                confirmado = depois.rect[0] < rect_antes[0] or depois.rect != rect_antes
            else:
                confirmado = depois.rect[0] > rect_antes[0] or depois.rect != rect_antes
        elif depois is not None:
            confirmado = depois.rect != rect_antes

        return montar(
            executado=True,
            confirmado=bool(confirmado),
            mensagem=(
                f"Janela movida para a {lado}."
                if confirmado
                else f"Atalho enviado, mas o encaixe à {lado} não foi confirmado."
            ),
            detalhes={"hwnd": antes.hwnd, "rect_antes": rect_antes, "depois": str(depois)},
        )

    def abrir_visao_de_tarefas(self) -> dict:
        from sistema_toke.verificador import capturar_janela_ativa, esperar_foreground_diferente

        antes = capturar_janela_ativa()
        time.sleep(self.pausa)
        pyautogui.hotkey("win", "tab")
        if antes is None:
            return montar(
                executado=True,
                confirmado=False,
                mensagem="Atalho da visão de tarefas enviado, sem janela anterior observável.",
            )
        mudou = esperar_foreground_diferente(antes.hwnd, timeout_ms=800)
        depois = capturar_janela_ativa()
        classe = (depois.classe if depois else "") or ""
        confirmado = mudou is True or "Multitasking" in classe or "Flip3D" in classe
        return montar(
            executado=True,
            confirmado=bool(confirmado),
            mensagem=(
                "Visão de tarefas aberta."
                if confirmado
                else "Atalho enviado, mas a visão de tarefas não foi confirmada."
            ),
            detalhes={"classe_depois": classe, "mudou": mudou},
        )

    def bloquear_tela(self) -> dict:
        time.sleep(self.pausa)
        ctypes.windll.user32.LockWorkStation()
        return montar(
            executado=True,
            confirmado=False,
            mensagem="Comando de bloqueio enviado. O bloqueio da sessão não pode ser confirmado daqui.",
        )
