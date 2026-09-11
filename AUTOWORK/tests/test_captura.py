from __future__ import annotations
import speech_recognition as sr
from unittest.mock import MagicMock, patch
import pytest
from audio.captura import ServicoCaptura

def test_captura_init() -> None:
    servico = ServicoCaptura()
    assert servico is not None

def test_parametros_recomendados() -> None:
    """Defaults afinados para comandos curtos (relatório de melhorias de voz)."""
    servico = ServicoCaptura()
    r = servico.recognizer
    assert r.pause_threshold == 0.6
    assert r.non_speaking_duration == 0.3
    assert r.phrase_threshold == 0.3
    assert r.dynamic_energy_threshold is True
    assert r.dynamic_energy_adjustment_damping == 0.12
    assert r.dynamic_energy_ratio == 1.3
    assert r.operation_timeout == 8.0
    assert servico.listen_timeout is None
    assert servico.phrase_time_limit == 10.0

def test_non_speaking_maior_que_pause_erro() -> None:
    with pytest.raises(ValueError):
        ServicoCaptura(pause_threshold=0.3, non_speaking_duration=0.5)

@patch('audio.captura.sr.Microphone')
def test_captura_capturar(mock_microphone: MagicMock) -> None:
    servico = ServicoCaptura()

    mock_audio = MagicMock()
    servico.recognizer.listen = MagicMock(return_value=mock_audio)

    audio = servico.capturar()

    assert audio == mock_audio
    servico.recognizer.listen.assert_called_once()

@patch('audio.captura.sr.Microphone')
def test_captura_passa_limites_ao_listen(mock_microphone: MagicMock) -> None:
    servico = ServicoCaptura()
    servico.recognizer.listen = MagicMock(return_value=MagicMock())

    servico.capturar()

    kwargs = servico.recognizer.listen.call_args.kwargs
    assert kwargs == {"timeout": None, "phrase_time_limit": 10.0}

@patch('audio.captura.sr.Microphone')
def test_captura_timeout_retorna_none(mock_microphone: MagicMock) -> None:
    """WaitTimeoutError vira None — o ciclo deve reiniciar sem falhar."""
    servico = ServicoCaptura(listen_timeout=5.0)
    servico.recognizer.listen = MagicMock(side_effect=sr.WaitTimeoutError("timed out"))

    assert servico.capturar() is None
