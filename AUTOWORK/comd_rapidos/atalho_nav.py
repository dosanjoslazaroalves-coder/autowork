from __future__ import annotations

import logging
from typing import Callable, Tuple

import pyautogui
import time

from sistema_toke.contrato import montar

logger = logging.getLogger(__name__)


class AtalhoNav:

    def __init__(self, pausa: float = 0.3) -> None:
        self.logger = logging.getLogger(__name__)
        self.pausa = pausa

    def registrar_no_executor(self, registrar_fn: Callable) -> None:
        pares = {
            "nova_aba": self.nova_aba,
            "fechar_aba": self.fechar_aba,
            "reabrir_aba": self.reabrir_aba,
            "proxima_aba": self.proxima_aba,
            "aba_anterior": self.aba_anterior,
            "atualizar_pagina": self.atualizar_pagina,
            "atualizacao_forcada": self.atualizacao_forcada,
            "barra_endereco": self.barra_endereco,
            "voltar_pagina": self.voltar_pagina,
            "avancar_pagina": self.avancar_pagina,
            "pagina_inicial": self.pagina_inicial,
            "historico": self.historico,
            "downloads": self.downloads,
            "favoritos": self.favoritos,
            "buscar_na_pagina": self.buscar_na_pagina,
            "janela_anonima": self.janela_anonima,
            "nova_janela": self.nova_janela,
            "fechar_janela_nav": self.fechar_janela_nav,
            "salvar_pagina": self.salvar_pagina,
            "imprimir_pagina": self.imprimir_pagina,
            "zoom_mais": self.zoom_mais,
            "zoom_menos": self.zoom_menos,
            "zoom_padrao": self.zoom_padrao,
            "devtools": self.devtools,
            "inspecionar_elemento": self.inspecionar_elemento,
            "tela_cheia": self.tela_cheia,
            "codigo_fonte": self.codigo_fonte,
            "console": self.console,
        }
        for nome, metodo in pares.items():
            registrar_fn(nome, metodo)
        self.logger.info("AtalhoNav: todos os métodos registrados no executor.")

    def _enviar(self, teclas: Tuple[str, ...], descricao: str) -> dict:
        from sistema_toke.verificador import capturar_janela_ativa, janela_parece_navegador

        janela = capturar_janela_ativa()
        if not janela_parece_navegador(janela):
            self.logger.warning(
                "AtalhoNav: recusando '%s' — primeiro plano não é navegador (%s).",
                descricao,
                janela,
            )
            return montar(
                executado=False,
                confirmado=False,
                mensagem="Nenhum navegador em primeiro plano para este atalho.",
                detalhes={"janela": str(janela), "teclas": teclas},
            )

        self.logger.info("%s (foco em %s)", descricao, janela)
        time.sleep(self.pausa)
        if len(teclas) == 1:
            pyautogui.press(teclas[0])
        else:
            pyautogui.hotkey(*teclas)

        return montar(
            executado=True,
            confirmado=False,
            mensagem=(
                f"{descricao} enviado ao navegador. "
                "O efeito visual não foi confirmado."
            ),
            detalhes={"janela": str(janela), "teclas": teclas},
        )

    def nova_aba(self) -> dict:
        return self._enviar(("ctrl", "t"), "Nova aba")

    def fechar_aba(self) -> dict:
        return self._enviar(("ctrl", "w"), "Fechar aba")

    def reabrir_aba(self) -> dict:
        return self._enviar(("ctrl", "shift", "t"), "Reabrir aba")

    def proxima_aba(self) -> dict:
        return self._enviar(("ctrl", "tab"), "Próxima aba")

    def aba_anterior(self) -> dict:
        return self._enviar(("ctrl", "shift", "tab"), "Aba anterior")

    def atualizar_pagina(self) -> dict:
        return self._enviar(("f5",), "Atualizar página")

    def atualizacao_forcada(self) -> dict:
        return self._enviar(("ctrl", "f5"), "Atualização forçada")

    def barra_endereco(self) -> dict:
        return self._enviar(("ctrl", "l"), "Barra de endereço")

    def voltar_pagina(self) -> dict:
        return self._enviar(("alt", "left"), "Voltar página")

    def avancar_pagina(self) -> dict:
        return self._enviar(("alt", "right"), "Avançar página")

    def pagina_inicial(self) -> dict:
        return self._enviar(("alt", "home"), "Página inicial")

    def historico(self) -> dict:
        return self._enviar(("ctrl", "h"), "Histórico")

    def downloads(self) -> dict:
        return self._enviar(("ctrl", "j"), "Downloads")

    def favoritos(self) -> dict:
        return self._enviar(("ctrl", "d"), "Favoritos")

    def buscar_na_pagina(self) -> dict:
        return self._enviar(("ctrl", "f"), "Buscar na página")

    def janela_anonima(self) -> dict:
        return self._enviar(("ctrl", "shift", "n"), "Janela anônima")

    def nova_janela(self) -> dict:
        return self._enviar(("ctrl", "n"), "Nova janela")

    def fechar_janela_nav(self) -> dict:
        return self._enviar(("ctrl", "shift", "w"), "Fechar janela do navegador")

    def salvar_pagina(self) -> dict:
        return self._enviar(("ctrl", "s"), "Salvar página")

    def imprimir_pagina(self) -> dict:
        return self._enviar(("ctrl", "p"), "Imprimir página")

    def zoom_mais(self) -> dict:
        return self._enviar(("ctrl", "+"), "Aumentar zoom")

    def zoom_menos(self) -> dict:
        return self._enviar(("ctrl", "-"), "Diminuir zoom")

    def zoom_padrao(self) -> dict:
        return self._enviar(("ctrl", "0"), "Zoom padrão")

    def devtools(self) -> dict:
        return self._enviar(("f12",), "DevTools")

    def inspecionar_elemento(self) -> dict:
        return self._enviar(("ctrl", "shift", "c"), "Inspecionar elemento")

    def tela_cheia(self) -> dict:
        return self._enviar(("f11",), "Tela cheia")

    def codigo_fonte(self) -> dict:
        return self._enviar(("ctrl", "u"), "Código-fonte")

    def console(self) -> dict:
        # Chromium/Edge/Chrome: Ctrl+Shift+J. Firefox usa Ctrl+Shift+K.
        return self._enviar(("ctrl", "shift", "j"), "Console")
