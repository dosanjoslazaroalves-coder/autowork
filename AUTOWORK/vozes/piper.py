from __future__ import annotations

from pathlib import Path

from vozes.base import TtsEngine


class PiperTtsEngine(TtsEngine):
    async def synthesize_to_file(self, texto: str, output_path: Path) -> Path:
        raise NotImplementedError(
            "Piper TTS ainda não está implementado. Defina VOICE_ENGINE='edge' em configui.py."
        )
