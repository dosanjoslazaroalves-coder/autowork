"""Serviço textual do núcleo AUTOWORK para consumidores locais.

Esta camada reutiliza o mesmo ``Orquestrador`` usado pelo ``app.py``. Ela não
cria interpretador, executor, conversa ou áudio alternativos; apenas oferece
uma entrada programática para o processamento de texto.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from typing import Any

from core.estados import Estado

logger = logging.getLogger(__name__)


class _OuvinteApi:
    """Coleta eventos do orquestrador sem depender de HUD ou terminal."""

    def __init__(self) -> None:
        self.estado = Estado.INICIALIZANDO
        self.ultima_transcricao = ""
        self.ultima_resposta: dict[str, Any] = {}
        self.nivel_audio = 0.0
        self._nivel_audio_at = 0.0
        self._lock = threading.RLock()

    def ao_estado(self, estado: Estado) -> None:
        with self._lock:
            self.estado = estado

    def ao_transcricao(self, texto: str) -> None:
        with self._lock:
            self.ultima_transcricao = texto

    def ao_resposta(self, resultado: dict[str, Any]) -> None:
        with self._lock:
            self.ultima_resposta = dict(resultado)

    def snapshot(self) -> dict[str, Any]:
        """Lê os eventos já publicados sem esperar o comando terminar."""
        with self._lock:
            # A HUD consulta o status a cada ~400 ms; mantenha o último nível
            # por uma janela curta para não apagar a reação entre duas leituras.
            nivel = self.nivel_audio if time.monotonic() - self._nivel_audio_at <= 1.0 else 0.0
            return {
                "state": self.estado.name,
                "last_transcript": self.ultima_transcricao,
                "last_response": dict(self.ultima_resposta),
                "audio_level": nivel,
            }

    def ao_nivel(self, nivel: float) -> None:
        with self._lock:
            self.nivel_audio = max(0.0, min(1.0, float(nivel)))
            self._nivel_audio_at = time.monotonic()

    def ao_status(self, _nome: str, _valor: str) -> None:
        pass


class ServicoApi:
    """Fachada do núcleo para a ponte local HTTP."""

    _STATUS_ERRO = frozenset(
        {
            "falha",
            "nao_confirmado",
            "acao_nao_encontrada",
            "contrato_invalido",
            "erro_excecao",
            "erro_stt",
            "erro_tts",
            "erro_voz",
        }
    )

    def __init__(self, *, tts_enabled: bool = True, tts_async: bool = False) -> None:
        self._configurar_saida()
        self._orquestrador = None
        self._ouvinte = _OuvinteApi()
        self._lock = threading.RLock()
        self._lock_inicializacao = threading.RLock()
        self._tts_enabled = tts_enabled
        self._tts_async = tts_async
        self._tts_thread: threading.Thread | None = None
        self._voice_thread: threading.Thread | None = None
        self._voice_stop = threading.Event()
        self._voice_lock = threading.RLock()

    @staticmethod
    def _configurar_saida() -> None:
        """Mantém os mesmos caracteres UTF-8 do ``app.py`` no processo HTTP."""
        for stream in (sys.stdout, sys.stderr):
            try:
                if hasattr(stream, "reconfigure"):
                    stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                logger.debug("Não foi possível configurar saída UTF-8.", exc_info=True)

    def _obter_orquestrador(self):
        with self._lock_inicializacao:
            if self._orquestrador is None:
                from audio.captura import ServicoCaptura
                from audio.reconhecimento import ServicoReconhecimento
                from core.orquestrador import Orquestrador

                # A ponte desktop precisa conseguir parar a escuta sem matar o
                # processo; o terminal preserva seu timeout padrão (None).
                captura = ServicoCaptura(listen_timeout=1.0)
                reconhecimento = ServicoReconhecimento(captura.recognizer)
                orquestrador = Orquestrador(
                    captura,
                    reconhecimento,
                    ouvinte=self._ouvinte,
                )
                # A entrada textual está pronta sem calibrar/abrir o microfone.
                orquestrador._set_estado(Estado.IDLE)
                self._orquestrador = orquestrador
            return self._orquestrador

    def status(self) -> dict[str, Any]:
        orquestrador = self._obter_orquestrador()
        return {
            "core": "online",
            "ready": True,
            "audio_initialized": getattr(orquestrador._captura, "_microfone", None)
            is not None,
            "active_task": orquestrador.gerenciador_tarefas.snapshot(),
            "scheduled": orquestrador.agendador.listar(),
            "queue_size": orquestrador.fila_execucao.tamanho(),
            "context": orquestrador.contexto_execucao.snapshot(),
            "voice_running": self.voice_running,
            **self._ouvinte.snapshot(),
        }

    @property
    def voice_running(self) -> bool:
        thread = self._voice_thread
        return bool(thread and thread.is_alive())

    def start_voice(self) -> dict[str, Any]:
        """Inicia a escuta real em uma única thread, usando o pipeline oficial."""
        with self._voice_lock:
            if self.voice_running:
                return self.status()

            orquestrador = self._obter_orquestrador()
            self._orquestrador = orquestrador
            self._voice_stop.clear()

            def executar_voz() -> None:
                try:
                    orquestrador.inicializar()
                    if not self._voice_stop.is_set():
                        orquestrador.executar_loop()
                except Exception as exc:
                    logger.exception("[ServicoApi] Falha no ciclo de voz da HUD.")
                    self._ouvinte.ao_resposta({
                        "status": "erro_voz",
                        "mensagem": f"Falha no ciclo de voz: {exc}",
                        "falar": False,
                    })
                    orquestrador._set_estado(Estado.ERRO)
                finally:
                    if orquestrador.estado not in (Estado.ERRO, Estado.ENCERRANDO):
                        orquestrador._set_estado(Estado.IDLE)

            self._voice_thread = threading.Thread(
                target=executar_voz,
                name="autowork-voice-loop",
                daemon=True,
            )
            self._voice_thread.start()
            return self.status()

    def stop_voice(self) -> dict[str, Any]:
        """Solicita o fim da escuta sem criar uma segunda implementação de áudio."""
        with self._voice_lock:
            self._voice_stop.set()
            orquestrador = self._orquestrador
            thread = self._voice_thread
            if orquestrador is not None:
                orquestrador.parar()
            if thread and thread.is_alive() and thread is not threading.current_thread():
                thread.join(timeout=2.5)
            if thread and not thread.is_alive():
                self._voice_thread = None
            if orquestrador is not None and orquestrador.estado not in (Estado.ERRO, Estado.ENCERRANDO):
                orquestrador._set_estado(Estado.IDLE)
            return self.status()

    def processar_comando(self, texto: str) -> dict[str, Any]:
        """Processa texto com o pipeline oficial e reproduz a resposta via TTS."""
        texto_limpo = texto.strip()
        if not texto_limpo:
            raise ValueError("texto não pode ser vazio")

        inicio = time.perf_counter()
        logger.info("[ServicoApi] processando comando textual: %r", texto_limpo)
        with self._lock:
            orquestrador = self._obter_orquestrador()
            from core.orquestrador import Orquestrador
            # Reproduz o envelope de estados do ciclo textual sem iniciar áudio.
            orquestrador._notificar_ouvinte("ao_transcricao", texto_limpo)
            orquestrador._set_estado(Estado.PROCESSANDO)
            try:
                resultado = dict(orquestrador.processar_comando(texto_limpo))
            except Exception:
                logger.exception("[ServicoApi] Erro ao processar comando textual no núcleo AUTOWORK.")
                orquestrador._notificar_ouvinte("ao_resposta", {
                    "status": "erro_excecao",
                    "estado": Estado.ERRO.name,
                    "mensagem": "Erro interno do AUTOWORK. Consulte os logs.",
                })
                orquestrador._set_estado(Estado.ERRO)
                raise

            estado_resultado = self._estado_do_resultado(resultado)
            resultado["estado"] = estado_resultado.name
            orquestrador._notificar_ouvinte("ao_resposta", resultado)
            orquestrador._set_estado(estado_resultado)

            mensagem = resultado.get("mensagem", "")
            if self._tts_enabled and mensagem and Orquestrador._deve_falar(resultado):
                # Reutiliza a política, personalidade e motor de voz do fluxo
                # de microfone do Orquestrador.
                orquestrador._set_estado(Estado.FALANDO)
                if self._tts_async:
                    self._iniciar_tts(orquestrador, mensagem, estado_resultado)
                else:
                    tts_ok = orquestrador._falar_resposta(mensagem)
                    orquestrador._set_estado(estado_resultado if tts_ok else Estado.ERRO)
                    orquestrador._set_estado(Estado.IDLE)
            else:
                orquestrador._set_estado(Estado.IDLE)
            logger.info("[ServicoApi] resultado status=%s acao=%s estado=%s",
                        resultado.get("status"), resultado.get("acao"), resultado["estado"])
            logger.info("[PERF] API comando total em %.1f ms", (time.perf_counter() - inicio) * 1000)
            return resultado

    def _iniciar_tts(self, orquestrador, mensagem: str, estado_resultado: Estado) -> None:
        """Reproduz TTS HTTP sem manter a requisição bloqueada."""
        if self._tts_thread is not None and self._tts_thread.is_alive():
            raise ValueError("A resposta de voz anterior ainda está sendo reproduzida.")

        def reproduzir() -> None:
            try:
                tts_ok = orquestrador._falar_resposta(mensagem)
                if not tts_ok:
                    orquestrador._notificar_ouvinte("ao_resposta", {
                        "status": "erro_tts",
                        "mensagem": "Falha ao reproduzir a resposta de voz.",
                        "falar": False,
                    })
            except Exception:
                logger.exception("[ServicoApi] Falha no TTS assíncrono.")
                tts_ok = False
            finally:
                with self._lock:
                    self._tts_thread = None
                    orquestrador._set_estado(estado_resultado if tts_ok else Estado.ERRO)
                    orquestrador._set_estado(Estado.IDLE)

        self._tts_thread = threading.Thread(
            target=reproduzir,
            name="autowork-tts-api",
            daemon=True,
        )
        self._tts_thread.start()

    def _estado_do_resultado(self, resultado: dict[str, Any]) -> Estado:
        status = resultado.get("status")
        if status == "sucesso":
            return Estado.SUCESSO
        if status in self._STATUS_ERRO:
            return Estado.ERRO
        return Estado.IDLE
