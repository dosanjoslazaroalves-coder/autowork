"""Configurações exclusivas do módulo experimental de TTS."""

from __future__ import annotations

from pathlib import Path

# Motor TTS
ENGINE = "kokoro"
MODEL_REPO = "hexgrad/Kokoro-82M"

# Português brasileiro (Kokoro lang_code "p" -> espeak "pt-br")
LANG_CODE = "p"
VOICE = "pm_santa"
SPEED = 0.85
SAMPLE_RATE = 24000

# Vozes PT-BR suportadas pelo Kokoro
VOZES_PT_BR = ("pf_dora","bm_george", "pm_santa")

# eSpeak NG nativo (Windows)
ESPEAK_DIR = Path(r"C:\Program Files\eSpeak NG")
ESPEAK_LIBRARY = ESPEAK_DIR / "libespeak-ng.dll"
ESPEAK_DATA = ESPEAK_DIR / "espeak-ng-data"

# Saída de áudio gerado pelo módulo
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
