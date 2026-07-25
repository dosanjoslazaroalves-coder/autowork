from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

import requests
from requests.adapters import HTTPAdapter

from metricas import MedidorCiclo

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_PADRAO = "qwen2.5:3b"

# Prompt compacto: mesmas regras, menos tokens por requisição.
_PROMPT_TEMPLATE = """"""

def interpretar_comando():
    pass