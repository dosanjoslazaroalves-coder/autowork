from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import edge_tts

from vozes.base import TtsEngine


class EdgeTtsEngine(TtsEngine):
    async def synthesize_to_file(self, texto: str, output_path: Path) -> Path:
        kwargs: Dict[str, Any] = {
            "text": texto,
            "voice": self.settings.voice_name,
            "rate": self.settings.rate,
            "pitch": self.settings.pitch,
            "volume": self.settings.volume,
        }
        communicate = edge_tts.Communicate(**kwargs)
        await communicate.save(str(output_path))
        return output_path
