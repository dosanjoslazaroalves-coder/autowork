from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class MedidorCiclo:
    """Acumula tempos por etapa de um ciclo de comando."""

    _inicios: Dict[str, float] = field(default_factory=dict)
    tempos: Dict[str, float] = field(default_factory=dict)

    def iniciar(self, etapa: str) -> None:
        self._inicios[etapa] = time.perf_counter()

    def parar(self, etapa: str) -> float:
        inicio = self._inicios.pop(etapa, None)
        if inicio is None:
            return 0.0
        duracao = time.perf_counter() - inicio
        self.tempos[etapa] = self.tempos.get(etapa, 0.0) + duracao
        return duracao

    def registrar(self, etapa: str, duracao: float) -> None:
        if duracao < 0:
            return
        self.tempos[etapa] = self.tempos.get(etapa, 0.0) + duracao

    def total(self) -> float:
        return sum(self.tempos.values())

    def relatorio(self, titulo: str = "Métricas do ciclo") -> str:
        rotulos = {
            "captura": "Captura",
            "google": "Google Speech",
            "ollama": "Ollama",
            "json": "JSON",
            "execucao": "Execução",
            "tts": "TTS",
        }
        ordem = ("captura", "google", "ollama", "json", "execucao", "tts")
        linhas = [titulo, ""]
        for chave in ordem:
            if chave in self.tempos:
                nome = rotulos.get(chave, chave)
                linhas.append(f"{nome:.<18}{self.tempos[chave]:.2f} s")
        linhas.append("")
        linhas.append(f"{'TOTAL':.<18}{self.total():.2f} s")
        return "\n".join(linhas)

    def imprimir(self, titulo: str = "Métricas do ciclo") -> None:
        print(self.relatorio(titulo))


class Cronometro:
    """Context manager simples para medir um bloco de código."""

    def __init__(self, medidor: MedidorCiclo, etapa: str) -> None:
        self._medidor = medidor
        self._etapa = etapa
        self.duracao: float = 0.0

    def __enter__(self) -> "Cronometro":
        self._medidor.iniciar(self._etapa)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.duracao = self._medidor.parar(self._etapa)


def medir(func):
    """Decorator que retorna (resultado, duracao_em_segundos)."""

    def wrapper(*args, **kwargs):
        inicio = time.perf_counter()
        resultado = func(*args, **kwargs)
        return resultado, time.perf_counter() - inicio

    return wrapper
