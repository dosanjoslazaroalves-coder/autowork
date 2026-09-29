"""Testes do modo de escuta REPOUSO / ATIVO do microfone.

Valida que:
- A wake word "work" ativa uma janela de 3 minutos.
- Durante a janela, comandos são aceitos sem wake word.
- Após expirar, volta a exigir wake word.
- Falhas de reconhecimento não encerram o modo ativo.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from audio.wake_word import detectar as _detectar_real
from core.estados import Estado
from core.orquestrador import Orquestrador


# ── Fixtures ────────────────────────────────────────────────────────


def _criar_orquestrador() -> Orquestrador:
    """Cria um Orquestrador com captura e STT mockados."""
    captura = MagicMock()
    captura.capturar.return_value = MagicMock()  # áudio dummy
    stt = MagicMock()
    return Orquestrador(captura, stt)


def _rodar_ciclo(orq: Orquestrador, texto_transcrito: str) -> None:
    """Executa um _ciclo() simulando o texto transcrito pelo STT."""
    orq._captura.capturar.return_value = MagicMock()
    orq._stt.transcrever.return_value = texto_transcrito
    with patch("audio.wake_word.detectar", side_effect=_detectar_real), \
         patch("interface.terminal.mostrar_status"), \
         patch("audio.tts.falar"), \
         patch.object(orq, "processar_comando",
                      return_value={"status": "sucesso", "confirmado": True, "mensagem": ""}):
        orq._ciclo()


def _rodar_ciclo_com_proc(orq: Orquestrador, texto_transcrito: str):
    """Executa um _ciclo() e retorna o mock de processar_comando para asserts."""
    orq._captura.capturar.return_value = MagicMock()
    orq._stt.transcrever.return_value = texto_transcrito
    with patch("audio.wake_word.detectar", side_effect=_detectar_real), \
         patch("interface.terminal.mostrar_status"), \
         patch("audio.tts.falar"), \
         patch.object(orq, "processar_comando",
                      return_value={"status": "sucesso", "confirmado": True, "mensagem": ""}) as mock_proc:
        orq._ciclo()
        return mock_proc


# ── Teste 1 — Ativação ──────────────────────────────────────────────


def test_ativacao_com_work():
    """Dizer 'work' deve ativar o MODO ATIVO."""
    orq = _criar_orquestrador()
    assert orq._modo_ativo is False

    _rodar_ciclo(orq, "work")

    assert orq._modo_ativo is True
    assert orq._ativo_ate > 0


# ── Teste 2 — Primeiro comando ──────────────────────────────────────


def test_primeiro_comando_apos_work():
    """'work abrir chrome' deve ativar + processar e permanecer ATIVO."""
    orq = _criar_orquestrador()

    mock_proc = _rodar_ciclo_com_proc(orq, "work abrir chrome")

    mock_proc.assert_called_once_with("abrir chrome")
    assert orq._modo_ativo is True


# ── Teste 3 — Segundo comando sem "work" ────────────────────────────


def test_segundo_comando_sem_work():
    """Após ativação, um comando sem wake word deve ser processado."""
    orq = _criar_orquestrador()

    # Passo 1: ativar com "work"
    _rodar_ciclo(orq, "work")
    assert orq._modo_ativo is True

    # Passo 2: comando sem wake word
    mock_proc = _rodar_ciclo_com_proc(orq, "abrir bloco de notas")

    mock_proc.assert_called_once_with("abrir bloco de notas")
    assert orq._modo_ativo is True


# ── Teste 4 — Vários comandos consecutivos ──────────────────────────


def test_varios_comandos_consecutivos():
    """Múltiplos comandos sem repetir 'work' devem todos ser processados."""
    orq = _criar_orquestrador()

    # Ativar
    _rodar_ciclo(orq, "work")

    comandos = ["abrir chrome", "abrir bloco de notas", "abrir youtube"]
    for cmd in comandos:
        mock_proc = _rodar_ciclo_com_proc(orq, cmd)
        mock_proc.assert_called_once_with(cmd)

    assert orq._modo_ativo is True


# ── Teste 5 — Expiração ─────────────────────────────────────────────


def test_expiracao_apos_180_segundos():
    """Após 180s a janela deve expirar e _verificar_janela_ativa retornar False."""
    orq = _criar_orquestrador()

    # Ativar
    _rodar_ciclo(orq, "work")
    assert orq._modo_ativo is True

    # Simular expiração (timestamp no passado)
    orq._ativo_ate = 0.0

    assert orq._verificar_janela_ativa() is False
    assert orq._modo_ativo is False


# ── Teste 6 — Comando após expiração ────────────────────────────────


def test_comando_ignorado_apos_expiracao():
    """Comando sem wake word em REPOUSO deve ser ignorado (não processado)."""
    orq = _criar_orquestrador()

    # Ativar e depois expirar
    _rodar_ciclo(orq, "work")
    orq._modo_ativo = False
    orq._ativo_ate = 0.0

    mock_proc = _rodar_ciclo_com_proc(orq, "abrir chrome")

    mock_proc.assert_not_called()
    assert orq.estado == Estado.IDLE


# ── Teste 7 — Nova ativação ─────────────────────────────────────────


def test_nova_ativacao_apos_repouso():
    """Após expirar, dizer 'work' novamente deve reativar o MODO ATIVO."""
    orq = _criar_orquestrador()

    # Ativar e expirar
    _rodar_ciclo(orq, "work")
    orq._modo_ativo = False
    orq._ativo_ate = 0.0
    assert orq._modo_ativo is False

    # Nova ativação
    _rodar_ciclo(orq, "work")
    assert orq._modo_ativo is True
    assert orq._ativo_ate > 0


# ── Teste 8 — Falha de reconhecimento ───────────────────────────────


def test_falha_reconhecimento_nao_encerra_modo_ativo():
    """Transcrição None (não entendeu) não deve encerrar o MODO ATIVO."""
    orq = _criar_orquestrador()

    # Ativar
    _rodar_ciclo(orq, "work")
    assert orq._modo_ativo is True
    ativo_ate_antes = orq._ativo_ate

    # Simular falha de reconhecimento (transcrição None)
    orq._captura.capturar.return_value = MagicMock()
    orq._stt.transcrever.return_value = None
    orq._ciclo()

    # Modo ativo deve continuar
    assert orq._modo_ativo is True
    assert orq._ativo_ate == ativo_ate_antes


# ── Teste extra — Renovação de janela ────────────────────────────────


def test_work_durante_ativo_renova_janela():
    """Dizer 'work' durante MODO ATIVO deve renovar (não duplicar) a janela."""
    import time

    orq = _criar_orquestrador()

    # Ativar
    _rodar_ciclo(orq, "work")

    # Simular passagem parcial de tempo (restam 10s)
    orq._ativo_ate = time.monotonic() + 10

    _rodar_ciclo(orq, "work")
    assert orq._modo_ativo is True
    # A nova janela deve ser maior que os 10s restantes
    assert orq._ativo_ate > time.monotonic() + 10
