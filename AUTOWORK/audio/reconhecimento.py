"""Serviço de transcrição de áudio para texto (STT)."""
from __future__ import annotations

import logging
import time
from typing import Optional

import speech_recognition as sr

logger = logging.getLogger(__name__)


class ServicoReconhecimento:
    """Transcreve AudioData para texto usando Google Speech API."""

    def __init__(self, recognizer: sr.Recognizer, idioma: str = "pt-BR") -> None:
        self.recognizer = recognizer
        self.idioma = idioma

    def transcrever(self, audio: Optional[sr.AudioData]) -> Optional[str]:
        """Retorna texto normalizado, ou None se não entendeu / sem áudio."""
        if audio is None:
            return None
        t0 = time.perf_counter()
        try:
            texto = self.recognizer.recognize_google(audio, language=self.idioma)
        except sr.UnknownValueError:
            logger.debug("Áudio não compreendido pelo reconhecedor.")
            return None
        except sr.RequestError as exc:
            logger.error("[VOICE] erro no serviço de reconhecimento: %s", exc)
            return None
        resultado = texto.lower().strip()
        logger.info("[VOICE] reconhecimento em %.2fs", time.perf_counter() - t0)
        logger.info('[VOICE] texto: "%s"', resultado)
        return resultado
