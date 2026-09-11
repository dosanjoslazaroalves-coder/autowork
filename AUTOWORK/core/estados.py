"""Estados do sistema AUTOWORK."""
from __future__ import annotations

from enum import Enum, auto


class Estado(Enum):
    """Estados possíveis do assistente de voz."""

    INICIALIZANDO = auto()
    IDLE = auto()             # Aguardando wake word
    OUVINDO = auto()          # Capturando áudio do microfone
    TRANSCREVENDO = auto()    # Convertendo áudio em texto
    DETECTANDO_WAKE = auto()  # Verificando wake word
    PROCESSANDO = auto()      # Interpretando comando
    EXECUTANDO = auto()       # Executando ação
    FALANDO = auto()          # TTS em andamento
    SUCESSO = auto()          # Ação concluída com sucesso
    ERRO = auto()             # Ação falhou
    ENCERRANDO = auto()       # Shutdown
