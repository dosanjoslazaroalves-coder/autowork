"""Teste de integração do fluxo de voz: apresentação + comandos.

Executa `processar_comando` do fala.py (núcleo) com o executor registrado,
mas substitui as ações reais por stubs para não abrir programas na máquina.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fala  # noqa: E402
from sistema_toke.executor import REGISTRO_ACOES, registrar_comandos_padrao  # noqa: E402


def main() -> None:
    registrar_comandos_padrao()

    executadas: list[tuple[str, dict]] = []
    for nome in list(REGISTRO_ACOES):
        REGISTRO_ACOES[nome] = lambda **kw: executadas.append((nome, kw))

    falas: list[str] = []
    fala.falar = falas.append  # stub do TTS

    casos = [
        "se apresente",
        "quem é você?",
        "o que você faz?",
        "abrir google chrome",
        "abrir bloco de notas",
        "abrir o site do youtube",
        "fazer um café",
    ]

    falhas = 0
    for caso in casos:
        try:
            r = fala.processar_comando(caso)
            status = r.get("status")
            esperado = "sucesso" if "apresent" in caso or "abrir" in caso else None
            ok = status != "acao_nao_encontrada"
            if esperado and status != esperado:
                ok = False
            print("%s %-25s -> %s" % ("OK  " if ok else "FALHA", caso, status))
            falhas += 0 if ok else 1
        except Exception as exc:
            print("FALHA %-25s -> %s: %s" % (caso, type(exc).__name__, exc))
            falhas += 1

    print("\nAções executadas (stub):", executadas)
    print("Total de falhas:", falhas)
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
