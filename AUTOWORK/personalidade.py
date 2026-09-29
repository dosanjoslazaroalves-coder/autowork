"""Módulo raiz legado para compatibilidade de personalidade.

Delega à nova camada oficial 'persn_emcoes'.
"""
from __future__ import annotations

from persn_emcoes.personalidade import Personalidade, estilizar_fala

__all__ = ["Personalidade", "estilizar_fala"]
