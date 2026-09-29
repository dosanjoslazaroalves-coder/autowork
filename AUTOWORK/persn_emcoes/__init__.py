"""Camada persn_emcoes — Personalidade e Manifestações Emocionais Simuladas do AUTOWORK.

Responsabilidades:
- Apresentação e personificação verbal do AUTOWORK.
- Saudações contextuais (manhã, tarde, noite, dia da semana).
- Feedbacks de espera durante operações demoradas com controle anti-spam.
- Confirmações de conclusão e mensagens de erro amigáveis.
- Gerenciamento de estado emocional simulado.
- Estilização elegante de mensagens para o usuário.
"""
from __future__ import annotations

from persn_emcoes.estado import ControladorEmocional, EstadoEmocional
from persn_emcoes.feedback import GerenciadorFeedback
from persn_emcoes.personalidade import ConfiguracaoFala, Personalidade, estilizar_fala
from persn_emcoes.saudacao import (
    GeradorSaudacao,
    obter_despedida,
    obter_saudacao,
)

__all__ = [
    "ConfiguracaoFala",
    "ControladorEmocional",
    "EstadoEmocional",
    "GeradorSaudacao",
    "GerenciadorFeedback",
    "Personalidade",
    "estilizar_fala",
    "obter_despedida",
    "obter_saudacao",
]
