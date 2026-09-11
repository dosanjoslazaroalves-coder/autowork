"""Detecção de palavra-chave (wake word) 'AUTOWORK'."""
from __future__ import annotations

import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

WAKE_WORD = "auto"
# Variantes comuns de transcrição incorreta pelo Google STT
_VARIANTES = frozenset({"autowork", "auto work", "auto-work", "auto"})


def detectar(texto: Optional[str]) -> Tuple[bool, str]:
    """Verifica se wake word está presente no texto.

    Returns:
        (detectado, comando_limpo): bool indicando detecção e
        texto com a wake word removida.
    """
    if texto is None:
        return False, ""

    texto_lower = texto.lower().strip()

    for variante in _VARIANTES:
        if variante in texto_lower:
            # Remove todas as variantes do texto
            padrao = r"\b(?:" + "|".join(re.escape(v) for v in _VARIANTES) + r")\b"
            comando = re.sub(padrao, "", texto_lower)
            # Também tenta sem word-boundary para variantes com hífen
            for v in _VARIANTES:
                comando = comando.replace(v, "")
            comando = re.sub(r"\s+", " ", comando).strip(" ,.")
            logger.info("Wake word detectada. Comando extraído: %r", comando)
            return True, comando

    return False, ""
