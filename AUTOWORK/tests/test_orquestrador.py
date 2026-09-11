from __future__ import annotations
from unittest.mock import MagicMock
from core.orquestrador import Orquestrador
from core.estados import Estado

def test_orquestrador_init() -> None:
    mock_captura = MagicMock()
    mock_stt = MagicMock()

    orq = Orquestrador(mock_captura, mock_stt)
    assert orq is not None
    assert orq.estado == Estado.INICIALIZANDO

def test_ciclo_sem_fala_volta_para_idle() -> None:
    """Captura com timeout (None) reinicia o ciclo sem transcrever nem falar."""
    mock_captura = MagicMock()
    mock_captura.capturar.return_value = None
    mock_stt = MagicMock()

    orq = Orquestrador(mock_captura, mock_stt)
    orq._ciclo()

    mock_stt.transcrever.assert_not_called()
    assert orq.estado == Estado.IDLE

def test_ciclo_transcricao_vazia_nao_fala() -> None:
    """Texto None (não entendeu) reinicia o ciclo sem resposta de voz."""
    mock_captura = MagicMock()
    mock_captura.capturar.return_value = MagicMock()
    mock_stt = MagicMock()
    mock_stt.transcrever.return_value = None

    orq = Orquestrador(mock_captura, mock_stt)
    orq._ciclo()

    assert orq.estado == Estado.IDLE
    mock_captura.capturar.assert_called_once()
