"""Fachada TTS — delega ao motor Kokoro em modules.voz_teste."""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

OnNivelCallback = Callable[[float], None]

# Janela do envelope de níveis do TTS, em segundos.
_JANELA_NIVEL = 0.06


def falar(texto: Optional[str]) -> None:
    """Sintetiza e reproduz texto via Kokoro TTS.

    Se o texto for vazio ou None, a chamada é ignorada silenciosamente.
    Erros do motor TTS são logados mas não propagados para evitar
    que falhas de áudio derrubem o loop principal.
    """
    if not texto or not texto.strip():
        logger.debug("TTS: texto vazio, ignorando.")
        return

    from modules.voz_teste import falar as _falar_kokoro

    try:
        _falar_kokoro(texto)
    except Exception as exc:
        logger.error("Falha no TTS: %s", exc)


def _envelope(audio, taxa_amostragem: int) -> List[float]:
    """RMS por janela do áudio gerado, normalizado em 0..1."""
    import numpy as np

    tamanho = max(1, int(taxa_amostragem * _JANELA_NIVEL))
    total = len(audio) // tamanho
    if total == 0:
        return [1.0]
    blocos = np.asarray(audio[: total * tamanho], dtype="float32").reshape(
        total, tamanho
    )
    rms = np.sqrt(np.mean(blocos**2, axis=1))
    pico = float(rms.max())
    if pico <= 0:
        return [0.0] * total
    niveis = rms / pico
    return [float(n) for n in niveis]


def falar_com_niveis(texto: Optional[str], on_nivel: OnNivelCallback) -> None:
    """Reproduz texto via TTS emitindo os níveis reais do áudio sintetizado.

    O envelope é calculado sobre a própria forma de onda gerada pelo Kokoro
    e emitido em janelas sincronizadas com a reprodução. Se a geração ou a
    reprodução falharem, cai para ``falar()`` sem níveis.
    """
    if not texto or not texto.strip():
        logger.debug("TTS: texto vazio, ignorando.")
        return

    try:
        from modules.voz_teste import gerar_audio
        from modules.voz_teste import config as config_tts

        audio = gerar_audio(texto)
        envelope = _envelope(audio, config_tts.SAMPLE_RATE)
    except Exception as exc:
        logger.error("Falha ao gerar TTS com níveis: %s", exc)
        falar(texto)
        return

    try:
        import sounddevice as sd
    except ImportError:
        logger.error("sounddevice indisponível; reproduzindo sem níveis.")
        falar(texto)
        return

    def _emitir() -> None:
        for nivel in envelope:
            try:
                on_nivel(nivel)
            except Exception:
                logger.debug("Erro ao reportar nível do TTS.", exc_info=True)
            time.sleep(_JANELA_NIVEL)
        try:
            on_nivel(0.0)
        except Exception:
            pass

    emissor = threading.Thread(target=_emitir, name="tts-niveis", daemon=True)
    try:
        sd.play(audio, config_tts.SAMPLE_RATE)
        emissor.start()
        sd.wait()
    except Exception as exc:
        logger.error("Falha na reprodução do TTS: %s", exc)
        return
    finally:
        emissor.join(timeout=1.0)
