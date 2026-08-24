"""Módulo experimental de Text-to-Speech para o AUTOWORK."""

from .tts import TTSError, falar, gerar_audio, salvar_audio

__all__ = ["TTSError", "falar", "gerar_audio", "salvar_audio"]
