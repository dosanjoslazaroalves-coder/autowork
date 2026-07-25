from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VoiceSettings:
    voice_name: str
    rate: str = "+0%"
    pitch: str = "+0Hz"
    volume: str = "+0%"


class TtsEngine(ABC):
    """Contrato comum para Edge, Piper, Kokoro, etc."""

    def __init__(self, settings: VoiceSettings) -> None:
        self.settings = settings

    @abstractmethod
    async def synthesize_to_file(self, texto: str, output_path: Path) -> Path:
        raise NotImplementedError

    def update_settings(self, settings: VoiceSettings) -> None:
        self.settings = settings
