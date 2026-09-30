"""Estado temporário do modo de conversa avançada."""
from __future__ import annotations

import time
from collections.abc import Callable
from typing import Optional


DURACAO_MODO_AVANCADO_SEGUNDOS = 3 * 60


class ModoConversaAvancada:
    """Controla uma única janela de expiração, sem timer em background."""

    def __init__(
        self,
        duracao_segundos: float = DURACAO_MODO_AVANCADO_SEGUNDOS,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        self.duracao_segundos = float(duracao_segundos)
        self._relogio = relogio
        self._expira_em: Optional[float] = None

    @property
    def ativo(self) -> bool:
        """Indica se a janela ainda está válida e expira-a quando necessário."""
        if self._expira_em is None:
            return False
        if self._relogio() >= self._expira_em:
            self._expira_em = None
            return False
        return True

    @property
    def expira_em(self) -> Optional[float]:
        """Instante monotônico da expiração, ou None quando inativo."""
        if not self.ativo:
            return None
        return self._expira_em

    def ativar(self) -> None:
        """Ativa ou renova a janela completa de três minutos."""
        self._expira_em = self._relogio() + self.duracao_segundos

    def desativar(self) -> None:
        """Desativa o modo imediatamente."""
        self._expira_em = None


_MODO_CONVERSA_AVANCADA = ModoConversaAvancada()


def obter_modo_conversa_avancada() -> ModoConversaAvancada:
    """Retorna o estado compartilhado pelo fluxo principal do AUTOWORK."""
    return _MODO_CONVERSA_AVANCADA

