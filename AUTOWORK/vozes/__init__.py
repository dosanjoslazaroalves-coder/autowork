from __future__ import annotations

from configui import VOICE_ENGINE, resolve_voice_settings
from vozes.base import TtsEngine, VoiceSettings
from vozes.edge import EdgeTtsEngine
from vozes.kokoro import KokoroTtsEngine
from vozes.piper import PiperTtsEngine


def build_voice_settings() -> VoiceSettings:
    cfg = resolve_voice_settings()
    return VoiceSettings(
        voice_name=cfg["voice_name"],
        rate=cfg["rate"],
        pitch=cfg["pitch"],
        volume=cfg["volume"],
    )


def get_engine(engine_name: str | None = None) -> TtsEngine:
    name = (engine_name or VOICE_ENGINE or "edge").strip().lower()
    settings = build_voice_settings()

    if name == "edge":
        return EdgeTtsEngine(settings)
    if name == "piper":
        return PiperTtsEngine(settings)
    if name == "kokoro":
        return KokoroTtsEngine(settings)

    raise ValueError(f"Motor TTS desconhecido: {name!r}")
