from __future__ import annotations
from core.estados import Estado

def test_estados_existem() -> None:
    esperados = [
        'INICIALIZANDO', 'IDLE', 'OUVINDO', 'TRANSCREVENDO', 
        'DETECTANDO_WAKE', 'PROCESSANDO', 'EXECUTANDO', 
        'FALANDO', 'SUCESSO', 'ERRO', 'ENCERRANDO'
    ]
    for est in esperados:
        assert hasattr(Estado, est)
