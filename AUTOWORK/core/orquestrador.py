"""Orquestrador — coordena o fluxo de voz completo do AUTOWORK."""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from core.estados import Estado

logger = logging.getLogger(__name__)

# Callbacks typealias
OnEstadoCallback = Callable[[Estado], None]

COMANDO_FECHAR = frozenset({"fechar", "encerrar", "desligar"})

# Status que merecem resposta por voz mesmo sem a flag "falar" explícita.
STATUS_FALAVEIS = frozenset({"falha", "nao_reconhecido", "acao_nao_encontrada"})


class Orquestrador:
    """Pipeline central: captura → transcrição → wake word → execução → TTS.

    Opcionalmente notifica um ``ouvinte`` (interface) com eventos de estado,
    transcrição, resposta e nível de áudio. O ouvinte é duck-typed: métodos
    ausentes são simplesmente ignorados.
    """

    def __init__(
        self,
        servico_captura,       # audio.captura.ServicoCaptura
        servico_stt,           # audio.reconhecimento.ServicoReconhecimento
        on_estado: Optional[OnEstadoCallback] = None,
        ouvinte: Optional[Any] = None,
    ) -> None:
        from sistema_toke.executor import registrar_comandos_padrao
        registrar_comandos_padrao()

        self._captura = servico_captura
        self._stt = servico_stt
        self._estado = Estado.INICIALIZANDO
        self._on_estado = on_estado or (lambda e: None)
        self._ouvinte = ouvinte
        self._rodando = False

    @property
    def estado(self) -> Estado:
        """Estado atual do sistema."""
        return self._estado

    def _set_estado(self, novo: Estado) -> None:
        """Atualiza estado e notifica callback e ouvinte."""
        self._estado = novo
        self._on_estado(novo)
        self._notificar_ouvinte("ao_estado", novo)
        logger.debug("Estado → %s", novo.name)

    def _notificar_ouvinte(self, metodo: str, *args: Any) -> None:
        """Encaminha um evento ao ouvinte sem nunca quebrar o pipeline."""
        if self._ouvinte is None:
            return
        acao = getattr(self._ouvinte, metodo, None)
        if acao is None:
            return
        try:
            acao(*args)
        except Exception:
            logger.debug("Ouvinte falhou em %s.", metodo, exc_info=True)

    def _tem_ouvinte(self, metodo: str) -> bool:
        return self._ouvinte is not None and hasattr(self._ouvinte, metodo)

    def inicializar(self) -> None:
        """Calibra microfone e prepara o sistema."""
        self._set_estado(Estado.INICIALIZANDO)
        self._captura.calibrar()
        self._set_estado(Estado.IDLE)

    def executar_loop(self) -> None:
        """Loop principal do assistente."""
        from audio.tts import falar
        from interface.terminal import mostrar_status, mostrar_banner

        mostrar_banner()
        falar("AUTOWORK pronto. Fale um comando.")
        mostrar_status("AUTOWORK pronto! Diga 'Autowork' seguido do comando.")

        self._rodando = True
        while self._rodando:
            self._ciclo()

    def _capturar_com_ou_sem_niveis(self):
        """Captura áudio, emitindo níveis reais se o ouvinte os consumir."""
        if self._tem_ouvinte("ao_nivel") and hasattr(
            self._captura, "capturar_com_niveis"
        ):
            return self._captura.capturar_com_niveis(self._ao_nivel_microfone)
        return self._captura.capturar()

    def _ao_nivel_microfone(self, rms: float) -> None:
        """Repassa o RMS bruto do microfone ao ouvinte (sem normalização)."""
        self._notificar_ouvinte("ao_nivel", rms)

    def _falar_resposta(self, mensagem: str) -> None:
        """Fala a mensagem emitindo níveis reais quando a interface os usa."""
        import audio.tts as tts

        if self._tem_ouvinte("ao_nivel") and hasattr(tts, "falar_com_niveis"):
            tts.falar_com_niveis(mensagem, self._ao_nivel_tts)
        else:
            tts.falar(mensagem)

    def _ao_nivel_tts(self, nivel: float) -> None:
        self._notificar_ouvinte("ao_nivel", nivel)

    @staticmethod
    def _deve_falar(resultado: Dict[str, Any]) -> bool:
        """Política de voz: respostas informativas falam; confirmações de
        comando de sucesso não (evita repetição excessiva)."""
        if "falar" in resultado:
            return bool(resultado["falar"])
        return resultado.get("status") in STATUS_FALAVEIS

    def _ciclo(self) -> None:
        """Um ciclo completo: ouvir → transcrever → detectar wake → processar."""
        from audio import wake_word
        from interface.terminal import mostrar_status

        # 1. Captura (None = ninguém falou no tempo limite da escuta)
        self._set_estado(Estado.OUVINDO)
        audio = self._capturar_com_ou_sem_niveis()
        if audio is None:
            self._set_estado(Estado.IDLE)
            return

        # 2. Transcrição
        self._set_estado(Estado.TRANSCREVENDO)
        texto = self._stt.transcrever(audio)
        if texto is None:
            self._set_estado(Estado.IDLE)
            return  # Silêncio — NÃO fala "não entendi"

        self._notificar_ouvinte("ao_transcricao", texto)

        # 3. Wake word
        self._set_estado(Estado.DETECTANDO_WAKE)
        detectado, comando = wake_word.detectar(texto)
        if not detectado:
            logger.debug("Ignorando (sem wake word): %r", texto)
            self._set_estado(Estado.IDLE)
            return

        # 4. Comando de encerramento
        if comando in COMANDO_FECHAR:
            mostrar_status("Encerrando AUTOWORK...")
            self._set_estado(Estado.FALANDO)
            self._falar_resposta("Encerrando AUTOWORK, senhor.")
            self._set_estado(Estado.ENCERRANDO)
            self._rodando = False
            return

        # 5. Processamento
        self._set_estado(Estado.PROCESSANDO)
        resultado = self.processar_comando(comando)
        self._notificar_ouvinte("ao_resposta", resultado)

        # 6. TTS da resposta
        mensagem = resultado.get("mensagem", "")
        if mensagem and self._deve_falar(resultado):
            self._set_estado(Estado.FALANDO)
            self._falar_resposta(mensagem)

        # 7. Estado final
        status = resultado.get("status", "")
        if status == "sucesso":
            self._set_estado(Estado.SUCESSO)
        elif status == "falha":
            self._set_estado(Estado.ERRO)
        self._set_estado(Estado.IDLE)

    def processar_comando(self, texto: str) -> Dict[str, Any]:
        """Interpreta e executa um comando de texto (sem áudio).

        Este método pode ser chamado diretamente para testes,
        sem depender de captura de áudio real.
        """
        from dispatcher import dispatch
        from interpretador import interpretar
        from sistema_toke.executor import executar
        from sistema_toke.normalizador import normalizar
        from interface.terminal import mostrar_resultado

        intencao = interpretar(texto)
        tipo = intencao.get("tipo", "desconhecido")

        # Comando específico: o interpretador já passou pelo parser/resolvedor.
        if tipo == "comando":
            normalizado = normalizar(texto)
            logger.debug("Normalizado: %r", normalizado)

            if intencao.get("resolvido") is False:
                logger.debug(
                    "Resolvedor não encontrou ação para a intenção: %s",
                    intencao,
                )
                resultado = {
                    "status": "falha",
                    "acao": intencao.get("acao", ""),
                    "mensagem": "Não foi possível resolver a ação.",
                }
            else:
                logger.debug("Executando comando: %s", intencao)
                self._set_estado(Estado.EXECUTANDO)
                resultado = executar(
                    intencao["acao"],
                    **intencao.get("parametros", {}),
                )

            mostrar_resultado(texto, normalizado, intencao, resultado)

            return resultado

        # Intenção vazia: nada reconhecido.
        if tipo == "desconhecido":
            logger.debug("Intenção não reconhecida: %r", texto)
            mostrar_resultado(texto, None, None)
            return {
                "status": "nao_reconhecido",
                "texto": texto,
                "mensagem": "Não reconheci esse comando, senhor.",
            }

        # Clima, hora, apresentação e conversa seguem pelo dispatcher.
        self._set_estado(Estado.EXECUTANDO)
        resultado = dispatch(intencao)
        mostrar_resultado(texto, None, intencao, resultado)

        return resultado

    def parar(self) -> None:
        """Sinaliza encerramento do loop."""
        self._rodando = False
