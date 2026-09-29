"""Módulo de gerenciamento de estado emocional simulado do AUTOWORK.

Este módulo implementa uma simulação comportamental para tornar as interações
mais naturais e fluidas. O assistente não possui e não afirma possuir emoções
reais; trata-se exclusivamente de um modelo de tom e conduta comunicativa.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional


class EstadoEmocional(str, Enum):
    """Estados emocionais simulados disponíveis para orientar o comportamento verbal."""

    NEUTRO = "neutro"
    ATENTO = "atento"
    PROCESSANDO = "processando"
    SATISFEITO = "satisfeito"
    ALERTA = "alerta"
    ERRO = "erro"
    CONCLUIDO = "concluido"


class ControladorEmocional:
    """Gerencia o ciclo e transições do estado emocional simulado."""

    # Descrições de postura verbal associadas a cada estado
    _POSTURAS: Dict[EstadoEmocional, str] = {
        EstadoEmocional.NEUTRO: "Equilibrado, sóbrio e receptivo.",
        EstadoEmocional.ATENTO: "Pronto para instrução, conciso e focado.",
        EstadoEmocional.PROCESSANDO: "Analítico, calmo e seguro.",
        EstadoEmocional.SATISFEITO: "Polido, prestativo e confiante.",
        EstadoEmocional.ALERTA: "Vigilante, cauteloso e direto.",
        EstadoEmocional.ERRO: "Compreensivo, resolutivo e não-alarmista.",
        EstadoEmocional.CONCLUIDO: "Eficiente, pontual e discreto.",
    }

    def __init__(self, estado_inicial: EstadoEmocional = EstadoEmocional.NEUTRO) -> None:
        self._estado_atual = estado_inicial
        self._historico: List[EstadoEmocional] = [estado_inicial]

    @property
    def atual(self) -> EstadoEmocional:
        """Retorna o estado emocional simulado atual."""
        return self._estado_atual

    @property
    def postura_verbal(self) -> str:
        """Retorna uma breve descrição da postura verbal correspondente ao estado."""
        return self._POSTURAS.get(self._estado_atual, "Objetivo e cortês.")

    def transitar(self, novo_estado: EstadoEmocional) -> EstadoEmocional:
        """Altera o estado emocional simulado atual e registra no histórico recente.

        Args:
            novo_estado: O novo EstadoEmocional a ser adotado.

        Returns:
            O EstadoEmocional atualizado.
        """
        if not isinstance(novo_estado, EstadoEmocional):
            try:
                novo_estado = EstadoEmocional(str(novo_estado).lower())
            except ValueError:
                novo_estado = EstadoEmocional.NEUTRO

        self._estado_atual = novo_estado
        self._historico.append(novo_estado)
        if len(self._historico) > 50:
            self._historico.pop(0)

        return self._estado_atual

    def resetar(self) -> None:
        """Restaura o estado emocional simulado para o padrão NEUTRO."""
        self.transitar(EstadoEmocional.NEUTRO)
