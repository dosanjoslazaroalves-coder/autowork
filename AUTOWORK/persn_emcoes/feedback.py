"""Módulo de feedback temporal durante processamento no AUTOWORK.

Emite mensagens curtas e elegantes de espera quando uma operação demora,
evitando a impressão de travamento e garantindo ausência de spam.
"""
from __future__ import annotations

import contextlib
import random
import threading
import time
from typing import Callable, Generator, List, Optional

# Mensagens curtas para o primeiro aviso de espera
_FRASES_PRIMEIRO_AVISO: List[str] = [
    "Um momento.",
    "Estou analisando isso.",
    "Só um instante.",
    "Estou processando sua solicitação.",
    "Um instante, por favor.",
]

# Mensagens para operações excepcionalmente longas
_FRASES_SEGUNDO_AVISO: List[str] = [
    "Só mais um momento, ainda concluindo a análise.",
    "Ainda processando os dados, um instante.",
    "Operação em andamento, quase pronto.",
]


class GerenciadorFeedback:
    """Controla o disparo de falas de espera em background com base no tempo de execução."""

    def __init__(
        self,
        atraso_inicial: float = 2.5,
        intervalo_adicional: float = 6.0,
        max_avisos: int = 2,
    ) -> None:
        """Inicializa o gerenciador.

        Args:
            atraso_inicial: Segundos antes do primeiro aviso (resposta rápida não fala nada).
            intervalo_adicional: Segundos adicionais de espera antes do segundo aviso.
            max_avisos: Número máximo de falas de espera emitidas por operação.
        """
        self.atraso_inicial = atraso_inicial
        self.intervalo_adicional = intervalo_adicional
        self.max_avisos = max_avisos
        self._ultima_frase: Optional[str] = None
        self._evento_parada = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _escolher_frase(self, nivel: int) -> str:
        pool = _FRASES_PRIMEIRO_AVISO if nivel == 1 else _FRASES_SEGUNDO_AVISO
        candidatas = [f for f in pool if f != self._ultima_frase] or pool
        escolhida = random.choice(candidatas)
        self._ultima_frase = escolhida
        return escolhida

    def iniciar(self, callback_fala: Callable[[str], None]) -> None:
        """Inicia o monitoramento temporal em thread secundária."""
        self.parar()
        self._evento_parada.clear()

        def _loop() -> None:
            # 1. Espera atraso inicial
            if self._evento_parada.wait(self.atraso_inicial):
                return  # Terminou rápido, não fala nada

            # Primeiro aviso
            frase1 = self._escolher_frase(nivel=1)
            try:
                callback_fala(frase1)
            except Exception:
                pass

            if self.max_avisos <= 1:
                return

            # 2. Espera intervalo adicional se ainda estiver rodando
            if self._evento_parada.wait(self.intervalo_adicional):
                return

            # Segundo aviso
            frase2 = self._escolher_frase(nivel=2)
            try:
                callback_fala(frase2)
            except Exception:
                pass

        self._thread = threading.Thread(target=_loop, name="autowork-feedback-espera", daemon=True)
        self._thread.start()

    def parar(self) -> None:
        """Cancela o monitoramento caso a operação termine."""
        self._evento_parada.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)
        self._thread = None

    @contextlib.contextmanager
    def monitorar(self, callback_fala: Callable[[str], None]) -> Generator[None, None, None]:
        """Context manager prático para envolver blocos demorados."""
        self.iniciar(callback_fala)
        try:
            yield
        finally:
            self.parar()
