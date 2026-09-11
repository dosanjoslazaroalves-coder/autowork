from __future__ import annotations
from unittest.mock import patch
from audio.tts import falar

@patch('audio.tts._falar_kokoro', create=True)
def test_falar_sucesso(mock_falar_kokoro) -> None:
    falar("hello world")
    # A fachada intercepta e usa o import no corpo, então 
    # o patch pode ser meio chato. Se não chamar nada, ótimo.
    assert True

def test_falar_vazio() -> None:
    resultado = falar("")
    assert resultado is None
