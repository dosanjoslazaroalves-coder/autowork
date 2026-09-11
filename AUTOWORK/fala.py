"""Módulo de compatibilidade — delega ao novo app.py."""
from __future__ import annotations

# Re-exporta para manter compatibilidade com testes existentes
from app import main  # noqa: F401


def processar_comando(texto: str) -> dict:
    """Compatibilidade: cria orquestrador temporário para processar texto."""
    from core.orquestrador import Orquestrador
    from audio.captura import ServicoCaptura
    from audio.reconhecimento import ServicoReconhecimento

    captura = ServicoCaptura()
    stt = ServicoReconhecimento(captura.recognizer)
    orq = Orquestrador(captura, stt)
    resultado = orq.processar_comando(texto)
    
    from audio.tts import falar
    mensagem = resultado.get("mensagem", "")
    if mensagem:
        falar(mensagem)
        
    return resultado