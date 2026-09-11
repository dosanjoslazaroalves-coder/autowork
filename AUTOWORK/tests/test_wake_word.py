from __future__ import annotations
import pytest
from audio.wake_word import detectar

@pytest.mark.parametrize("texto, esperado_bool, esperado_str", [
    ("autowork comando", True, "comando"),
    ("hello autowork oi", True, "hello oi"),
    ("autowork please", True, "please"),
    ("auto work teste", True, "teste"),
    ("hello world", False, ""),
    ("", False, ""),
    ("AUTOWORK", True, ""),
])
def test_detectar_wake_word(texto: str, esperado_bool: bool, esperado_str: str) -> None:
    resultado_bool, resultado_str = detectar(texto)
    assert resultado_bool == esperado_bool
    assert resultado_str == esperado_str
