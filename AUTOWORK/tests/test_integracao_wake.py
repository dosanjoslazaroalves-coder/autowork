from __future__ import annotations
from unittest.mock import MagicMock, patch
from core.orquestrador import Orquestrador
from core.estados import Estado

def test_integracao_wake_word_fluxo() -> None:
    mock_captura = MagicMock()
    mock_stt = MagicMock()
    mock_stt.transcrever.return_value = "autowork fechar"
    
    orq = Orquestrador(mock_captura, mock_stt)
    
    # Executa apenas 1 ciclo
    with patch('core.orquestrador.logger'):
        with patch('audio.tts.falar'):
            orq._ciclo()
            
    # Ao ouvir 'autowork fechar', deve ir para o estado ENCERRANDO
    assert orq.estado == Estado.ENCERRANDO
    assert orq._rodando is False
