"""Serviço de captura e calibração de áudio via SpeechRecognition."""
from __future__ import annotations

import logging
import math
import struct
import time
from typing import Callable, Optional

import speech_recognition as sr

logger = logging.getLogger(__name__)

# Callback chamado com o RMS (amplitude bruta) de cada bloco lido do microfone.
OnNivelCallback = Callable[[float], None]


def _rms(dados: bytes) -> float:
    """Calcula o RMS de um bloco PCM 16 bits little-endian."""
    total = len(dados) // 2
    if total == 0:
        return 0.0
    amostras = struct.unpack(f"<{total}h", dados[: total * 2])
    soma = sum(a * a for a in amostras)
    return math.sqrt(soma / total)


class _StreamComNiveis:
    """Proxy do stream do microfone que mede o nível de cada bloco lido."""

    def __init__(self, stream, on_nivel: OnNivelCallback) -> None:
        self._stream = stream
        self._on_nivel = on_nivel

    def read(self, num_frames: int) -> bytes:
        dados = self._stream.read(num_frames)
        try:
            self._on_nivel(_rms(dados))
        except Exception:
            logger.debug("Erro ao reportar nível de áudio.", exc_info=True)
        return dados


class _FonteComNiveis(sr.AudioSource):
    """Envolve um AudioSource interceptando o stream para medição de nível.

    Mantém o comportamento de ``listen()`` intacto: os mesmos blocos são
    lidos e devolvidos ao Recognizer, que continua dono da detecção de fala.
    """

    def __init__(self, fonte: sr.AudioSource, on_nivel: OnNivelCallback) -> None:
        self._fonte = fonte
        self._on_nivel = on_nivel
        self.SAMPLE_RATE = fonte.SAMPLE_RATE
        self.SAMPLE_WIDTH = fonte.SAMPLE_WIDTH
        self.CHUNK = fonte.CHUNK
        self.stream = None

    def __enter__(self) -> "_FonteComNiveis":
        self._fonte.__enter__()
        self.stream = _StreamComNiveis(self._fonte.stream, self._on_nivel)
        return self

    def __exit__(self, *exc_info) -> bool:
        self.stream = None
        return self._fonte.__exit__(*exc_info)


class _MedidorFala:
    """Marca os instantes de início da fala usando os mesmos limiares do Recognizer.

    Compara o RMS de cada bloco com ``energy_threshold`` corrente — a mesma
    condição que o ``listen()`` usa —, permitindo registrar a espera até o
    usuário começar a falar sem alterar a detecção da biblioteca.
    """

    def __init__(self, recognizer: sr.Recognizer) -> None:
        self._recognizer = recognizer
        self._t0 = time.perf_counter()
        self.inicio: Optional[float] = None

    def bloco(self, rms: float) -> None:
        if self.inicio is None and rms > self._recognizer.energy_threshold:
            self.inicio = time.perf_counter()


class ServicoCaptura:
    """Gerencia microfone e captura de áudio com lazy init.

    Parâmetros do Recognizer afinados para comandos curtos de voz em pt-BR:
    fim de frase detectado rapidamente (baixa latência) sem cortar falas
    pausadas, com limiar de energia calibrado no startup e auto-ajustável.
    """

    def __init__(
        self,
        energy_threshold: int = 300,
        dynamic_energy_threshold: bool = True,
        dynamic_energy_adjustment_damping: float = 0.12,
        dynamic_energy_ratio: float = 1.3,
        pause_threshold: float = 0.6,
        phrase_threshold: float = 0.3,
        non_speaking_duration: float = 0.3,
        operation_timeout: Optional[float] = 8.0,
        listen_timeout: Optional[float] = None,
        phrase_time_limit: Optional[float] = 10.0,
    ) -> None:
        if non_speaking_duration > pause_threshold:
            raise ValueError(
                "non_speaking_duration deve ser <= pause_threshold "
                "(exigência do Recognizer.listen)."
            )
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.dynamic_energy_threshold = dynamic_energy_threshold
        self.recognizer.dynamic_energy_adjustment_damping = (
            dynamic_energy_adjustment_damping
        )
        self.recognizer.dynamic_energy_ratio = dynamic_energy_ratio
        self.recognizer.pause_threshold = pause_threshold
        self.recognizer.phrase_threshold = phrase_threshold
        self.recognizer.non_speaking_duration = non_speaking_duration
        # Timeout HTTP das chamadas recognize_* (rede lenta não trava o assistente).
        self.recognizer.operation_timeout = operation_timeout
        self.listen_timeout = listen_timeout
        self.phrase_time_limit = phrase_time_limit
        self._microfone: Optional[sr.Microphone] = None

    def _obter_microfone(self) -> sr.Microphone:
        if self._microfone is None:
            self._microfone = sr.Microphone()
        return self._microfone

    def calibrar(self, duration: float = 1.0) -> None:
        """Ajusta energy_threshold com base no ruído ambiente.

        Deve ser chamado uma única vez no startup, com o ambiente em silêncio;
        depois disso o ``dynamic_energy_threshold`` cuida das variações.
        """
        try:
            t0 = time.perf_counter()
            with self._obter_microfone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            logger.info(
                "[VOICE] calibração em %.2fs → energy_threshold=%.0f",
                time.perf_counter() - t0,
                self.recognizer.energy_threshold,
            )
        except OSError as exc:
            logger.error("Erro ao calibrar microfone: %s", exc)
            raise

    def capturar(self) -> Optional[sr.AudioData]:
        """Bloqueia até capturar áudio do microfone.

        Retorna ``None`` se ``listen_timeout`` expirar sem fala.
        """
        return self._capturar(None)

    def capturar_com_niveis(self, on_nivel: OnNivelCallback) -> Optional[sr.AudioData]:
        """Como ``capturar()``, mas reporta o RMS de cada bloco via callback.

        O callback roda na mesma thread da captura e deve ser rápido
        (apenas encaminhar o nível para a interface).
        """
        return self._capturar(on_nivel)

    def _capturar(self, on_nivel: Optional[OnNivelCallback]) -> Optional[sr.AudioData]:
        medidor = _MedidorFala(self.recognizer)

        def ao_bloco(rms: float) -> None:
            medidor.bloco(rms)
            if on_nivel is not None:
                on_nivel(rms)

        t0 = time.perf_counter()
        try:
            with _FonteComNiveis(self._obter_microfone(), ao_bloco) as fonte:
                audio = self.recognizer.listen(
                    fonte,
                    timeout=self.listen_timeout,
                    phrase_time_limit=self.phrase_time_limit,
                )
        except sr.WaitTimeoutError:
            logger.info(
                "[VOICE] nenhuma fala em %.1fs de escuta — reiniciando ciclo.",
                self.listen_timeout,
            )
            return None

        total = time.perf_counter() - t0
        if medidor.inicio is not None:
            espera = medidor.inicio - t0
            logger.info("[VOICE] início da fala detectado após %.2fs", espera)
            logger.info(
                "[VOICE] fim da fala detectado — fala ≈ %.2fs (captura %.2fs)",
                total - espera,
                total,
            )
        else:
            logger.debug("[VOICE] captura de %.2fs sem fala marcada.", total)
        return audio
