"""Interface HUD do AUTOWORK (Textual) — apresentação, sem lógica de áudio.

A interface não controla módulos: apenas recebe eventos do app.py através
da fachada thread-safe ``HUD`` (set_state, set_audio_level, set_transcript,
set_response) e reflete o estado real do assistente.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from typing import Callable, Deque, Dict, Optional, Tuple

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import RichLog, Static

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mascote — identidade visual do AUTOWORK. O formato é fixo; apenas olhos e
# símbolo central variam conforme o estado.
# ---------------------------------------------------------------------------

_LINHA_TOPO = "                    ╭───╮"
_LINHA_OLHOS = "                   ({olhos})"
_LINHA_SIMBOLO = "                   ┤ {simbolo} ├"
_LINHA_CORPO = "                    ████"
_LINHA_BASE = "                   ╰───╯"


def mascote(olhos: str = "◉   ◉", simbolo: str = "<>") -> str:
    """Renderiza o mascote no formato canônico, trocando olhos e símbolo."""
    return "\n".join(
        [
            _LINHA_TOPO,
            _LINHA_OLHOS.format(olhos=olhos),
            _LINHA_SIMBOLO.format(simbolo=simbolo),
            _LINHA_CORPO,
            _LINHA_CORPO,
            _LINHA_CORPO,
            _LINHA_BASE,
        ]
    )


MASCOTE_PADRAO = mascote()

# Rótulo e estilo Rich de cada estado da interface.
ESTADOS_UI: Dict[str, Tuple[str, str]] = {
    "IDLE": ("● PRONTO", "bold #4d7d95"),
    "LISTENING": ("● ESCUTANDO", "bold #00e5ff"),
    "THINKING": ("● PROCESSANDO", "bold #3f9fff"),
    "SPEAKING": ("● FALANDO", "bold #35e0c0"),
    "ERROR": ("● ERRO", "bold #ff5555"),
}

# Blocos do visualizador de áudio, do silêncio ao pico.
_BLOCOS = "▁▂▃▄▅▆▇█"
_LARGURA_VISUALIZADOR = 46
_COR_MASCOTE = "#35c8e0"


class AppHUD(App):
    """Aplicação Textual do painel AUTOWORK."""

    TITLE = "AUTOWORK"

    BINDINGS = [("q", "quit", "Encerrar")]

    CSS = """
    Screen {
        background: #04070c;
        color: #dfe9ee;
    }
    #cabecalho {
        height: 5;
        background: #060b13;
        border-bottom: round #0e2a3a;
    }
    #titulo {
        width: 1fr;
        padding: 0 2;
        content-align: left middle;
    }
    #relogio {
        width: 24;
        padding: 0 2;
        content-align: right middle;
    }
    #corpo {
        height: 1fr;
    }
    #esquerda {
        width: 1fr;
        padding: 1 2;
    }
    #direita {
        width: 34;
        background: #050910;
        border-left: round #123549;
        padding: 1 1;
    }
    #rotulo_conversa {
        color: #4d7d95;
        text-style: bold;
    }
    #conversa {
        height: 1fr;
        background: transparent;
        border: none;
        padding: 0 1;
    }
    #modulos {
        height: 4;
        color: #4d7d95;
        padding: 0 1;
    }
    #estado {
        height: 3;
        content-align: center middle;
        text-style: bold;
    }
    #mascote {
        height: 1fr;
        content-align: center middle;
    }
    #visualizador {
        height: 3;
        content-align: center middle;
        border-top: round #0e2a3a;
    }
    #rodape {
        height: 1;
        background: #060b13;
        color: #2e4654;
        content-align: right middle;
        padding-right: 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._estado = "IDLE"
        self._tick = 0
        self._ultimo_nivel_em: float = 0.0
        self._niveis: Deque[float] = _deque_zeros(_LARGURA_VISUALIZADOR)
        self._modulos: Dict[str, str] = {
            "MICROFONE": "AGUARDANDO",
            "RECONHECIMENTO": "AGUARDANDO",
            "VOZ": "AGUARDANDO",
        }

    # -- Composição ---------------------------------------------------------

    def compose(self) -> ComposeResult:
        with Horizontal(id="cabecalho"):
            yield Static(self._texto_titulo(), id="titulo")
            yield Static(self._texto_relogio(), id="relogio")
        with Horizontal(id="corpo"):
            with Vertical(id="esquerda"):
                yield Static("SISTEMA DE ASSISTÊNCIA", id="rotulo_conversa")
                yield RichLog(id="conversa", markup=True, wrap=True, highlight=False)
                yield Static(self._texto_modulos(), id="modulos")
            with Vertical(id="direita"):
                yield Static(self._texto_estado(), id="estado")
                yield Static(self._texto_mascote(), id="mascote")
        yield Static(self._texto_visualizador(), id="visualizador")
        yield Static("Q — encerrar o AUTOWORK", id="rodape")

    def on_mount(self) -> None:
        self.set_interval(1.0, self._tick_relogio)
        self.set_interval(0.12, self._tick_visualizador)
        self.set_interval(0.28, self._tick_animacao)
        self._registrar(
            "[b #00e5ff]AUTOWORK[/] iniciado. Diga [i]'Autowork'[/i] seguido do comando."
        )

    # -- Textos renderizados -------------------------------------------------

    @staticmethod
    def _texto_titulo() -> Text:
        texto = Text()
        texto.append("A U T O W O R K\n", style="bold #00e5ff")
        texto.append("INTELLIGENT ASSISTANT", style="#3f6f85")
        return texto

    @staticmethod
    def _texto_relogio(agora: Optional[str] = None) -> Text:
        hora = agora or datetime.now().strftime("%H:%M:%S")
        texto = Text()
        texto.append(hora + "\n", style="bold #dfe9ee")
        texto.append("● ONLINE", style="#35e0c0")
        return texto

    def _texto_estado(self) -> Text:
        rotulo, estilo = ESTADOS_UI.get(self._estado, ESTADOS_UI["IDLE"])
        return Text(rotulo, style=estilo)

    def _texto_mascote(self) -> Text:
        olhos, simbolo = self._variacoes_mascote()
        return Text(mascote(olhos, simbolo), style=_COR_MASCOTE)

    def _variacoes_mascote(self) -> Tuple[str, str]:
        """Olhos/símbolo por estado — o formato do mascote nunca muda."""
        if self._estado == "LISTENING":
            # Animação sutil: piscada ocasional.
            if self._tick % 7 == 6:
                return "─   ─", "<>"
            return "◉   ◉", "<>"
        if self._estado == "THINKING":
            return "•   •", "??"
        if self._estado == "SPEAKING":
            # Pequena oscilação do símbolo central representando a fala.
            return "◉   ◉", "<>" if self._tick % 2 == 0 else "><"
        if self._estado == "ERROR":
            return "×   ×", "!!"
        return "◉   ◉", "<>"

    def _texto_modulos(self) -> Text:
        cor_por_valor = {
            "ONLINE": "#35e0c0",
            "FALANDO": "#00e5ff",
            "ERRO": "#ff5555",
            "AGUARDANDO": "#2e4654",
        }
        texto = Text()
        for nome, valor in self._modulos.items():
            cor = cor_por_valor.get(valor, "#2e4654")
            texto.append(f"{nome:<16}", style="#4d7d95")
            texto.append(f"● {valor}\n", style=cor)
        return texto

    def _texto_visualizador(self) -> Text:
        barra = "".join(
            _BLOCOS[min(7, int(round(nivel * 7)))] for nivel in self._niveis
        )
        return Text(barra, style="#00b8d4")

    # -- Ticks (timers) ------------------------------------------------------

    def _tick_relogio(self) -> None:
        try:
            self.query_one("#relogio", Static).update(self._texto_relogio())
        except Exception:
            logger.debug("Relógio não atualizado.", exc_info=True)

    def _tick_animacao(self) -> None:
        """Atualiza o mascote apenas quando ele realmente se anima."""
        if self._estado not in ("LISTENING", "SPEAKING"):
            return
        self._tick += 1
        self._renderizar_mascote()

    def _tick_visualizador(self) -> None:
        """Decai o visualizador quando não chega nível real novo.

        Não inventa movimento: silêncio real colapsa a barra até a base.
        """
        if self._estado not in ("LISTENING", "SPEAKING"):
            return
        if time.monotonic() - self._ultimo_nivel_em > 0.15:
            self._niveis.append(self._niveis[-1] * 0.55)
            self._renderizar_visualizador()

    # -- Atualizações (chamadas via call_from_thread pela fachada HUD) -------

    def _definir_estado(self, estado: str) -> None:
        if estado == self._estado:
            return
        if estado not in ESTADOS_UI:
            estado = "IDLE"
            if estado == self._estado:
                return
        self._estado = estado
        self._tick = 0
        if estado not in ("LISTENING", "SPEAKING"):
            self._zerar_visualizador()
        try:
            self.query_one("#estado", Static).update(self._texto_estado())
            self._renderizar_mascote()
        except Exception:
            logger.debug("Estado não refletido na interface.", exc_info=True)

    def _receber_nivel(self, nivel: float) -> None:
        self._ultimo_nivel_em = time.monotonic()
        self._niveis.append(max(0.0, min(1.0, nivel)))
        self._renderizar_visualizador()

    def _receber_transcricao(self, texto: str) -> None:
        self._registrar(f"[#4d7d95]Você:[/] {texto}")

    def _receber_resposta(self, mensagem: str) -> None:
        self._registrar(f"[b #00e5ff]AUTOWORK:[/] {mensagem}")

    def _receber_modulo(self, nome: str, valor: str) -> None:
        if nome in self._modulos:
            self._modulos[nome] = valor
        try:
            self.query_one("#modulos", Static).update(self._texto_modulos())
        except Exception:
            logger.debug("Status de módulo não refletido.", exc_info=True)

    def encerrar_interface(self) -> None:
        self.exit()

    # -- Auxiliares -----------------------------------------------------------

    def _registrar(self, linha: str) -> None:
        try:
            self.query_one("#conversa", RichLog).write(linha)
        except Exception:
            logger.debug("Mensagem não exibida (interface ausente).", exc_info=True)

    def _renderizar_mascote(self) -> None:
        try:
            self.query_one("#mascote", Static).update(self._texto_mascote())
        except Exception:
            logger.debug("Mascote não atualizado.", exc_info=True)

    def _renderizar_visualizador(self) -> None:
        try:
            self.query_one("#visualizador", Static).update(self._texto_visualizador())
        except Exception:
            logger.debug("Visualizador não atualizado.", exc_info=True)

    def _zerar_visualizador(self) -> None:
        self._niveis = _deque_zeros(_LARGURA_VISUALIZADOR)
        self._renderizar_visualizador()


def _deque_zeros(tamanho: int) -> Deque[float]:
    from collections import deque

    return deque([0.0] * tamanho, maxlen=tamanho)


class HUD:
    """Fachada thread-safe entre o app.py (pipeline de áudio) e a interface.

    Métodos podem ser chamados de qualquer thread; as atualizações são
    encaminhadas ao loop do Textual via ``call_from_thread``. Se a interface
    não estiver rodando, as chamadas são ignoradas silenciosamente.
    """

    INTERVALO_MINIMO_NIVEL = 0.045  # segundos entre níveis enviados à UI

    def __init__(self) -> None:
        self._app: Optional[AppHUD] = None
        self._ultimo_nivel_em = 0.0
        self._lock = threading.Lock()

    def set_state(self, estado: str) -> None:
        """Define o estado visível: IDLE, LISTENING, THINKING, SPEAKING, ERROR."""
        self._chamar("_definir_estado", estado)

    def set_audio_level(self, nivel: float) -> None:
        """Nível real de áudio (0..1) para o visualizador."""
        agora = time.monotonic()
        with self._lock:
            if agora - self._ultimo_nivel_em < self.INTERVALO_MINIMO_NIVEL:
                return
            self._ultimo_nivel_em = agora
        self._chamar("_receber_nivel", max(0.0, min(1.0, nivel)))

    def set_transcript(self, texto: str) -> None:
        """Texto reconhecido do usuário."""
        self._chamar("_receber_transcricao", texto)

    def set_response(self, mensagem: str) -> None:
        """Resposta produzida pelo assistente."""
        self._chamar("_receber_resposta", mensagem)

    def set_modulo(self, nome: str, valor: str) -> None:
        """Status de um módulo (MICROFONE, RECONHECIMENTO, VOZ)."""
        self._chamar("_receber_modulo", nome, valor)

    def encerrar(self) -> None:
        """Solicita o fechamento da interface."""
        self._chamar("encerrar_interface")

    def executar(self, trabalho: Callable[[], None]) -> None:
        """Roda ``trabalho`` (pipeline de áudio) em thread própria e a
        interface na thread principal, até o usuário encerrar."""
        app = AppHUD()
        self._app = app
        pipeline = threading.Thread(
            target=trabalho, name="autowork-pipeline", daemon=True
        )
        pipeline.start()
        try:
            app.run()
        finally:
            self._app = None
            pipeline.join(timeout=2.0)

    def _chamar(self, metodo: str, *args) -> None:
        app = self._app
        if app is None:
            return
        try:
            app.call_from_thread(getattr(app, metodo), *args)
        except Exception:
            logger.debug("Interface indisponível para %s.", metodo, exc_info=True)
