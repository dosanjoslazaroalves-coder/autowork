"""Configuração única do Ollama usado pelo AUTOWORK."""
from __future__ import annotations

import os

OLLAMA_URL = os.getenv("AUTOWORK_OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = "qwen3:8b"
OLLAMA_TIMEOUT = float(os.getenv("AUTOWORK_OLLAMA_TIMEOUT", "120"))
OLLAMA_NUM_PREDICT = int(os.getenv("AUTOWORK_OLLAMA_NUM_PREDICT", "512"))
OLLAMA_AUX_TIMEOUT = float(os.getenv("AUTOWORK_OLLAMA_AUX_TIMEOUT", "5"))

