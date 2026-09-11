from __future__ import annotations
import speech_recognition as sr
from unittest.mock import MagicMock
from audio.reconhecimento import ServicoReconhecimento

def test_reconhecimento_sucesso() -> None:
    mock_recognizer = MagicMock(spec=sr.Recognizer)
    mock_recognizer.recognize_google.return_value = "hello world"
    servico = ServicoReconhecimento(mock_recognizer)

    mock_audio = MagicMock(spec=sr.AudioData)
    texto = servico.transcrever(mock_audio)

    assert texto == "hello world"

def test_reconhecimento_normaliza_texto() -> None:
    mock_recognizer = MagicMock(spec=sr.Recognizer)
    mock_recognizer.recognize_google.return_value = "  Abrir o Chrome  "
    servico = ServicoReconhecimento(mock_recognizer)

    texto = servico.transcrever(MagicMock(spec=sr.AudioData))

    assert texto == "abrir o chrome"
    assert mock_recognizer.recognize_google.call_args.kwargs == {"language": "pt-BR"}

def test_reconhecimento_falha() -> None:
    mock_recognizer = MagicMock(spec=sr.Recognizer)
    mock_recognizer.recognize_google.side_effect = sr.UnknownValueError
    servico = ServicoReconhecimento(mock_recognizer)

    mock_audio = MagicMock(spec=sr.AudioData)
    texto = servico.transcrever(mock_audio)

    assert texto is None

def test_reconhecimento_erro_requisicao() -> None:
    """RequestError (rede/cota) não pode derrubar o assistente."""
    mock_recognizer = MagicMock(spec=sr.Recognizer)
    mock_recognizer.recognize_google.side_effect = sr.RequestError("sem internet")
    servico = ServicoReconhecimento(mock_recognizer)

    assert servico.transcrever(MagicMock(spec=sr.AudioData)) is None

def test_transcrever_sem_audio() -> None:
    """Captura com timeout (None) é ignorada sem chamar o reconhecedor."""
    mock_recognizer = MagicMock(spec=sr.Recognizer)
    servico = ServicoReconhecimento(mock_recognizer)

    assert servico.transcrever(None) is None
    mock_recognizer.recognize_google.assert_not_called()
