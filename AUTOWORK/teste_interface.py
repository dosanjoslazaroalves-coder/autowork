from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Input, Label
from datetime import datetime
import random


AUTOWORK = r"""
 █████╗ ██╗   ██╗████████╗ ██████╗ ██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝
███████║██║   ██║   ██║   ██║   ██║██║ █╗ ██║██║   ██║██████╔╝█████╔╝
██╔══██║██║   ██║   ██║   ██║   ██║██║███╗██║██║   ██║██╔══██╗██╔═██╗
██║  ██║╚██████╔╝   ██║   ╚██████╔╝╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝  ╚══╝╚══╝  ╚═════╝  ╚═╝  ╚═╝╚═╝  ╚═╝
"""


OCTO_NORMAL = r"""
   ╭──╮
  (◉  ◉)
   ┤<>├
   ┤  ├
   ╰──╯
"""

OCTO_PISCANDO = r"""
   ╭──╮
  (─  ─)
╭──┤<>├──╮
╰──┤  ├──╯
   ╰──╯
"""

OCTO_ESQUERDA = r"""
   ╭──╮
  (●  ◉)
╭──┤<>├──╮
╰──┤  ├──╯
   ╰──╯
"""

OCTO_DIREITA = r"""
   ╭──╮
  (◉  ●)
╭──┤<>├──╮
╰──┤  ├──╯
   ╰──╯
"""

OCTO_PENSANDO = r"""
   ╭──╮
  (•  •)
╭──┤??├──╮
╰──┤  ├──╯
   ╰──╯
"""

OCTO_SUCESSO = r"""
   ╭──╮
  (✓  ✓)
╭──┤<>├──╮
╰──┤  ├──╯
   ╰──╯
"""

OCTO_ERRO = r"""
   ╭──╮
  (×  ×)
╭──┤!!├──╮
╰──┤  ├──╯
   ╰──╯
"""


class AutoWork(App):

    TITLE = "AUTOWORK"
    SUB_TITLE = "Intelligent Automation System"

    CSS = """

    Screen {
        color: cyan;
    }

    #principal {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    #logo {
        width: 100%;
        height: 9;
        color: cyan;
        content-align: center middle;
    }

    #subtitulo {
        width: 100%;
        height: 2;
        color: gray;
        content-align: center middle;
    }

    #topo {
        width: 100%;
        height: 3;
    }

    #titulo {
        width: 2fr;
    }

    #relogio {
        width: 1fr;
        content-align: right middle;
        color: gray;
    }

    #conteudo {
        width: 100%;
        height: 1fr;
    }

    #robo_panel {
        width: 1fr;
        height: 100%;
        border: solid cyan;
        padding: 1;
    }

    #area_movimento {
        width: 100%;
        height: 15;
        overflow: hidden;
    }

    #robo {
        width: auto;
        height: auto;
        color: cyan;
    }

    #robo_nome {
        width: 100%;
        height: 2;
        content-align: center middle;
    }

    #mensagem {
        width: 100%;
        height: 5;
        content-align: center middle;
    }

    #estado {
        width: 100%;
        height: 2;
        content-align: center middle;
    }

    #direita {
        width: 2fr;
        height: 100%;
        margin-left: 1;
    }

    .painel {
        width: 100%;
        border: solid cyan;
        padding: 1;
        margin-bottom: 1;
    }

    #atividade {
        height: 1fr;
    }

    #entrada {
        width: 100%;
        height: 4;
        margin-top: 1;
        border: solid cyan;
    }

    """

    posicao_x = 0
    direcao = 1
    andando = True
    estado_robo = "NORMAL"
    passos = 0

    def compose(self) -> ComposeResult:

        with Container(id="principal"):

            yield Static(
                AUTOWORK,
                id="logo"
            )

            yield Static(
                "INTELLIGENT AUTOMATION SYSTEM",
                id="subtitulo"
            )

            with Horizontal(id="topo"):

                yield Label(
                    "◈ OCTO CORE  •  ONLINE",
                    id="titulo"
                )

                yield Label(
                    "",
                    id="relogio"
                )

            with Horizontal(id="conteudo"):

                with Vertical(id="robo_panel"):

                    with Container(id="area_movimento"):

                        yield Static(
                            OCTO_NORMAL,
                            id="robo"
                        )

                    yield Label(
                        "O C T O",
                        id="robo_nome"
                    )

                    yield Static(
                        "Sistema pronto.\n"
                        "Aguardando comando...",
                        id="mensagem"
                    )

                    yield Label(
                        "● ONLINE",
                        id="estado"
                    )

                with Vertical(id="direita"):

                    yield Static(
                        """
╔══════════════════════════════════╗
║          SYSTEM STATUS           ║
╚══════════════════════════════════╝

  ● VOICE          ONLINE
  ● INTERPRETER    ONLINE
  ● NORMALIZER     ONLINE
  ● PARSER         ONLINE
  ● CATALOG        ONLINE
  ● EXECUTOR       ONLINE
  ● DEBUGGER       ONLINE
  ● OCTO CORE      ONLINE
""",
                        classes="painel"
                    )

                    yield Static(
                        """
╔══════════════════════════════════╗
║             ACTIVITY             ║
╚══════════════════════════════════╝

  Sistema iniciado.

  OCTO Core carregado.

  > Aguardando comando...
""",
                        id="atividade",
                        classes="painel"
                    )

            yield Input(
                placeholder="> Digite um comando...",
                id="entrada"
            )

    def on_mount(self):

        self.set_interval(
            1,
            self.atualizar_relogio
        )

        self.set_interval(
            0.12,
            self.mover_octo
        )

        self.set_interval(
            0.30,
            self.comportamento_octo
        )

        self.atualizar_relogio()

    def atualizar_relogio(self):

        relogio = self.query_one(
            "#relogio",
            Label
        )

        relogio.update(
            datetime.now().strftime(
                "%d/%m/%Y  %H:%M:%S"
            )
        )

    def mover_octo(self):

        if not self.andando:
            return

        robo = self.query_one(
            "#robo",
            Static
        )

        area = self.query_one(
            "#area_movimento"
        )

        largura = max(
            10,
            area.size.width - 14
        )

        self.posicao_x += self.direcao

        if self.posicao_x >= largura:

            self.posicao_x = largura
            self.direcao = -1

        if self.posicao_x <= 0:

            self.posicao_x = 0
            self.direcao = 1

        robo.styles.margin = (
            0,
            0,
            0,
            self.posicao_x
        )

        self.passos += 1

    def comportamento_octo(self):

        if self.estado_robo != "NORMAL":
            return

        robo = self.query_one(
            "#robo",
            Static
        )

        numero = random.random()

        if numero < 0.06:

            robo.update(
                OCTO_PISCANDO
            )

            self.set_timer(
                0.18,
                lambda: robo.update(
                    OCTO_NORMAL
                )
            )

        elif numero < 0.10:

            robo.update(
                OCTO_ESQUERDA
            )

            self.set_timer(
                0.35,
                lambda: robo.update(
                    OCTO_NORMAL
                )
            )

        elif numero < 0.14:

            robo.update(
                OCTO_DIREITA
            )

            self.set_timer(
                0.35,
                lambda: robo.update(
                    OCTO_NORMAL
                )
            )

    def on_input_submitted(
        self,
        event: Input.Submitted
    ):

        comando = event.value.strip()

        if not comando:
            return

        event.input.value = ""

        self.estado_robo = "PROCESSANDO"
        self.andando = False

        robo = self.query_one(
            "#robo",
            Static
        )

        mensagem = self.query_one(
            "#mensagem",
            Static
        )

        estado = self.query_one(
            "#estado",
            Label
        )

        atividade = self.query_one(
            "#atividade",
            Static
        )

        robo.update(
            OCTO_PENSANDO
        )

        mensagem.update(
            f'Comando recebido:\n"{comando}"'
        )

        estado.update(
            "● PROCESSANDO"
        )

        atividade.update(
            f"""
╔══════════════════════════════════╗
║             ACTIVITY             ║
╚══════════════════════════════════╝

  > Comando:

    {comando}

  > OCTO:
    analisando...

  > Status:
    ● PROCESSANDO
"""
        )

        self.set_timer(
            1,
            lambda: self.finalizar(
                comando
            )
        )

    def finalizar(
        self,
        comando
    ):

        robo = self.query_one(
            "#robo",
            Static
        )

        mensagem = self.query_one(
            "#mensagem",
            Static
        )

        estado = self.query_one(
            "#estado",
            Label
        )

        robo.update(
            OCTO_SUCESSO
        )

        mensagem.update(
            "Tarefa concluída.\n"
            "Tudo funcionando."
        )

        estado.update(
            "● CONCLUÍDO"
        )

        self.estado_robo = "SUCESSO"

        self.set_timer(
            2,
            self.voltar_normal
        )

    def voltar_normal(self):

        robo = self.query_one(
            "#robo",
            Static
        )

        mensagem = self.query_one(
            "#mensagem",
            Static
        )

        estado = self.query_one(
            "#estado",
            Label
        )

        self.estado_robo = "NORMAL"
        self.andando = True

        robo.update(
            OCTO_NORMAL
        )

        mensagem.update(
            "Sistema pronto.\n"
            "Aguardando comando..."
        )

        estado.update(
            "● ONLINE"
        )


if __name__ == "__main__":
    AutoWork().run()