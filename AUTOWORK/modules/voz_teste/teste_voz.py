"""Teste executável do módulo experimental de voz."""

from __future__ import annotations

import sys
from pathlib import Path


def _garantir_import() -> None:
  """Permite executar o teste a partir da raiz do AUTOWORK."""

  raiz = Path(__file__).resolve().parents[2]
  if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))


def main() -> int:
  _garantir_import()

  from modules.voz_teste import TTSError, gerar_audio
  from modules.voz_teste.tts import _get_pipeline, _get_sounddevice
  from modules.voz_teste import config

  frase = "Olá. Este é um teste de voz do AUTOWORK."

  print("Inicializando TTS...")
  try:
    _get_pipeline()
  except TTSError as exc:
    print(str(exc))
    return 1
  except Exception as exc:
    print(
      "\n".join(
        [
          "ETAPA: inicialização",
          f"ERRO: {exc}",
          f"Tipo: {type(exc).__name__}",
          "Causa provável: falha inesperada ao carregar o motor TTS.",
          "Arquivo/configuração: modules/voz_teste/tts.py",
          "Como corrigir: verifique dependências em modules/voz_teste/requirements.txt",
        ]
      )
    )
    return 1

  print("Modelo carregado.")
  print("Gerando áudio...")

  try:
    audio = gerar_audio(frase)
    print("Áudio gerado.")
    print("Reproduzindo áudio...")
    sd = _get_sounddevice()
    sd.play(audio, config.SAMPLE_RATE)
    sd.wait()
  except TTSError as exc:
    print(str(exc))
    return 1
  except Exception as exc:
    print(
      "\n".join(
        [
          "ETAPA: teste de voz",
          f"ERRO: {exc}",
          f"Tipo: {type(exc).__name__}",
          "Causa provável: falha inesperada durante geração ou reprodução.",
          "Arquivo/configuração: modules/voz_teste/teste_voz.py",
          "Como corrigir: execute novamente com diagnóstico detalhado em modules/voz_teste/README.md",
        ]
      )
    )
    return 1

  print("Teste concluído.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
