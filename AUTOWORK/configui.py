from __future__ import annotations

from typing import Dict, TypedDict


class VoiceProfileConfig(TypedDict):
    voice_name: str
    rate: str
    pitch: str
    volume: str


# Motor ativo: "edge" | "piper" | "kokoro"
VOICE_ENGINE = "edge"

# Perfis: "jarvis" | "normal" | "alerta"
VOICE_PROFILE = "jarvis"

VOICE_PROFILES: Dict[str, VoiceProfileConfig] = {
    "jarvis": {
        "voice_name": "pt-BR-AntonioNeural",
        "rate": "-15%",
        "pitch": "-10Hz",
        "volume": "+0%",
    },
    "normal": {
        "voice_name": "pt-BR-AntonioNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "volume": "+0%",
    },
    "alerta": {
        "voice_name": "pt-BR-AntonioNeural",
        "rate": "+10%",
        "pitch": "-5Hz",
        "volume": "+0%",
    },
}


def get_active_voice_config() -> VoiceProfileConfig:
    perfil = VOICE_PROFILES.get(VOICE_PROFILE) or VOICE_PROFILES["normal"]
    return {
        "voice_name": perfil["voice_name"],
        "rate": perfil["rate"],
        "pitch": perfil["pitch"],
        "volume": perfil["volume"],
    }


# Atalhos legados / override opcional (None = usar perfil)
VOICE_NAME = None
VOICE_RATE = None
VOICE_PITCH = None
VOICE_VOLUME = None


def resolve_voice_settings() -> VoiceProfileConfig:
    base = get_active_voice_config()
    return {
        "voice_name": VOICE_NAME or base["voice_name"],
        "rate": VOICE_RATE or base["rate"],
        "pitch": VOICE_PITCH or base["pitch"],
        "volume": VOICE_VOLUME or base["volume"],
    }
