"""Serviço textual do núcleo AUTOWORK para consumidores locais.

Esta camada reutiliza o mesmo ``Orquestrador`` usado pelo ``app.py``. Ela não
cria interpretador, executor, conversa ou áudio alternativos; apenas oferece
uma entrada programática para o processamento de texto.
"""

from __future__ import annotations

import logging
import sys
import threading
from typing import Any

from core.estados import Estado

logger = logging.getLogger(__name__)


class _OuvinteApi:
    """Coleta eventos do orquestrador sem depender de HUD ou terminal."""

    def __init__(self) -> None:
        self.estado = Estado.INICIALIZANDO
        self.ultima_transcricao = ""
        self.ultima_resposta: dict[str, Any] = {}
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
            return {
                "state": self.estado.name,
                "last_transcript": self.ultima_transcricao,
                "last_response": dict(self.ultima_resposta),
            }

    def ao_nivel(self, _nivel: float) -> None:
        pass

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

                captura = ServicoCaptura()
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
            **self._ouvinte.snapshot(),
        }

    def processar_comando(self, texto: str) -> dict[str, Any]:
        """Processa texto com o pipeline oficial e reproduz a resposta via TTS."""
        texto_limpo = texto.strip()
        if not texto_limpo:
            raise ValueError("texto não pode ser vazio")

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
                    orquestrador._falar_resposta(mensagem)
                    orquestrador._set_estado(estado_resultado)
                    orquestrador._set_estado(Estado.IDLE)
            else:
                orquestrador._set_estado(Estado.IDLE)
            logger.info("[ServicoApi] resultado status=%s acao=%s estado=%s",
                        resultado.get("status"), resultado.get("acao"), resultado["estado"])
            return resultado

    def _iniciar_tts(self, orquestrador, mensagem: str, estado_resultado: Estado) -> None:
        """Reproduz TTS HTTP sem manter a requisição bloqueada."""
        if self._tts_thread is not None and self._tts_thread.is_alive():
            raise ValueError("A resposta de voz anterior ainda está sendo reproduzida.")

        def reproduzir() -> None:
            try:
                orquestrador._falar_resposta(mensagem)
            except Exception:
                logger.exception("[ServicoApi] Falha no TTS assíncrono.")
            finally:
                with self._lock:
                    self._tts_thread = None
                    orquestrador._set_estado(estado_resultado)
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
