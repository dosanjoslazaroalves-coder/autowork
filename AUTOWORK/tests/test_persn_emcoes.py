"""Testes unitários e de integração para a camada persn_emcoes do AUTOWORK."""
from __future__ import annotations

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from core.estados import Estado
from core.orquestrador import Orquestrador
from persn_emcoes.estado import ControladorEmocional, EstadoEmocional
from persn_emcoes.feedback import GerenciadorFeedback
from persn_emcoes.personalidade import Personalidade
from persn_emcoes.saudacao import GeradorSaudacao, obter_despedida, obter_saudacao


# ── 1. Saudação pela manhã ──────────────────────────────────────────
def test_saudacao_manha() -> None:
    saudador = GeradorSaudacao(nome_usuario="Marco")
    dt_manha = datetime(2026, 9, 24, 9, 30)  # Quinta-feira às 09:30
    mensagem = saudador.gerar_saudacao(momento=dt_manha)

    assert "Bom dia" in mensagem
    assert "Marco" in mensagem
    assert "quinta-feira" in mensagem or "AUTOWORK" in mensagem


# ── 2. Saudação à tarde ─────────────────────────────────────────────
def test_saudacao_tarde() -> None:
    saudador = GeradorSaudacao(nome_usuario="Marco")
    dt_tarde = datetime(2026, 9, 24, 15, 0)  # 15:00
    mensagem = saudador.gerar_saudacao(momento=dt_tarde)

    assert "Boa tarde" in mensagem
    assert "Marco" in mensagem


# ── 3. Saudação à noite ─────────────────────────────────────────────
def test_saudacao_noite() -> None:
    saudador = GeradorSaudacao(nome_usuario="Marco")
    dt_noite = datetime(2026, 9, 24, 21, 45)  # 21:45
    mensagem = saudador.gerar_saudacao(momento=dt_noite)

    assert "Boa noite" in mensagem
    assert "Marco" in mensagem


# ── 4. Identificação correta do dia da semana ───────────────────────
@pytest.mark.parametrize(
    ("ano", "mes", "dia", "dia_esperado"),
    [
        (2026, 9, 21, "segunda-feira"),
        (2026, 9, 22, "terça-feira"),
        (2026, 9, 23, "quarta-feira"),
        (2026, 9, 24, "quinta-feira"),
        (2026, 9, 25, "sexta-feira"),
        (2026, 9, 26, "sábado"),
        (2026, 9, 27, "domingo"),
    ],
)
def test_identificacao_dia_da_semana(ano: int, mes: int, dia: int, dia_esperado: str) -> None:
    dt = datetime(ano, mes, dia, 10, 0)
    dia_obtido = GeradorSaudacao.obter_dia_semana(dt)
    assert dia_obtido == dia_esperado


# ── 5. Variação das mensagens ───────────────────────────────────────
def test_variacao_mensagens() -> None:
    saudador = GeradorSaudacao(nome_usuario="Marco")
    dt = datetime(2026, 9, 24, 10, 0)

    # Executa sucessivas saudações para verificar alternância
    saudacoes = [saudador.gerar_saudacao(momento=dt) for _ in range(5)]
    # Verifica que não repetiu a mesma frase consecutivamente
    for i in range(len(saudacoes) - 1):
        assert saudacoes[i] != saudacoes[i + 1]

    # Verifica despedidas também
    despedidas = [saudador.gerar_despedida() for _ in range(5)]
    for i in range(len(despedidas) - 1):
        assert despedidas[i] != despedidas[i + 1]


# ── 6. Feedback após demora ─────────────────────────────────────────
def test_feedback_apos_demora() -> None:
    feedback = GerenciadorFeedback(atraso_inicial=0.05, intervalo_adicional=0.1)
    falas_coletadas = []

    def ao_falar(msg: str) -> None:
        falas_coletadas.append(msg)

    with feedback.monitorar(ao_falar):
        # Simula processamento demorado
        time.sleep(0.08)

    assert len(falas_coletadas) >= 1
    palavras_esperadas = ("analisando", "momento", "instante", "processando")
    assert any(any(p in f.lower() for p in palavras_esperadas) for f in falas_coletadas)


# ── 7. Controle para evitar mensagens repetidas e resposta rápida ──
def test_feedback_controle_resposta_rapida_e_repeticao() -> None:
    feedback = GerenciadorFeedback(atraso_inicial=0.2)
    falas_coletadas = []

    # Resposta rápida (< atraso_inicial): não deve falar nada
    with feedback.monitorar(lambda msg: falas_coletadas.append(msg)):
        time.sleep(0.01)

    assert len(falas_coletadas) == 0

    # Rotação de frases sem repetição consecutiva
    frase1 = feedback._escolher_frase(nivel=1)
    frase2 = feedback._escolher_frase(nivel=1)
    assert frase1 != frase2


# ── 8. Estado emocional simulado ───────────────────────────────────
def test_estado_emocional() -> None:
    controlador = ControladorEmocional(EstadoEmocional.NEUTRO)
    assert controlador.atual == EstadoEmocional.NEUTRO

    controlador.transitar(EstadoEmocional.ATENTO)
    assert controlador.atual == EstadoEmocional.ATENTO
    assert "Pronto" in controlador.postura_verbal

    controlador.transitar(EstadoEmocional.PROCESSANDO)
    assert controlador.atual == EstadoEmocional.PROCESSANDO

    controlador.transitar(EstadoEmocional.SATISFEITO)
    assert controlador.atual == EstadoEmocional.SATISFEITO

    controlador.transitar(EstadoEmocional.ERRO)
    assert controlador.atual == EstadoEmocional.ERRO

    controlador.resetar()
    assert controlador.atual == EstadoEmocional.NEUTRO


# ── 9. Integração com mecanismo de apresentação / TTS ──────────────
def test_integracao_apresentacao_e_tts() -> None:
    mock_captura = MagicMock()
    mock_stt = MagicMock()
    mock_ouvinte = MagicMock(spec=["ao_resposta", "ao_estado", "ao_transcricao", "ao_status"])

    persn = Personalidade(nome_usuario="Marco")
    orq = Orquestrador(mock_captura, mock_stt, ouvinte=mock_ouvinte, personalidade=persn)

    # Testa callback de feedback emitindo para a interface e TTS
    with patch("audio.tts.falar") as mock_falar, patch("audio.tts.falar_com_niveis") as mock_niveis:
        orq._ao_feedback_espera("Um momento, por favor.")
        mock_ouvinte.ao_resposta.assert_called_with({"mensagem": "Um momento, por favor."})
        assert mock_falar.called or mock_niveis.called


# ── 10. Inicialização do AUTOWORK ───────────────────────────────────
def test_inicializacao_autowork() -> None:
    mock_captura = MagicMock()
    mock_stt = MagicMock()
    mock_ouvinte = MagicMock(spec=["ao_resposta", "ao_estado", "ao_transcricao", "ao_status"])

    persn = Personalidade(nome_usuario="Marco")
    orq = Orquestrador(mock_captura, mock_stt, ouvinte=mock_ouvinte, personalidade=persn)

    with patch.object(orq, "_ciclo", side_effect=lambda: orq.parar()), \
         patch("audio.tts.falar") as mock_falar, \
         patch("audio.tts.falar_com_niveis") as mock_niveis:
        orq.executar_loop()

        # Verifica que a saudação foi emitida
        mock_ouvinte.ao_resposta.assert_called()
        args = mock_ouvinte.ao_resposta.call_args[0][0]
        assert "mensagem" in args
        assert "Marco" in args["mensagem"]
        assert mock_falar.called or mock_niveis.called


# ── 11. Influência da Personalidade nos Parâmetros de Fala ───────────
def test_personalidade_configura_fala_e_caracteristicas() -> None:
    persn = Personalidade(nome_usuario="Marco")

    # Estado neutro
    persn.emocao.transitar(EstadoEmocional.NEUTRO)
    fala_neutra = persn.configurar_fala("Texto de teste.")
    assert fala_neutra.velocidade == 0.85
    assert fala_neutra.voz == "pm_santa"
    assert fala_neutra.tom == "equilibrado e sóbrio"
    assert fala_neutra.formalidade == "elegante"

    # Estado alerta (fala mais rápida e direta)
    persn.emocao.transitar(EstadoEmocional.ALERTA)
    fala_alerta = persn.configurar_fala("Aviso importante.")
    assert fala_alerta.velocidade == 0.92
    assert fala_alerta.intensidade_emocional == "alta"

    # Estado processando (fala mais calma e compassada)
    persn.emocao.transitar(EstadoEmocional.PROCESSANDO)
    fala_proc = persn.configurar_fala("Estou analisando.")
    assert fala_proc.velocidade == 0.82
    assert fala_proc.intensidade_emocional == "baixa"


# ── 12. Repasse dos Parâmetros de Personalidade ao TTS ──────────────
def test_orquestrador_repassa_parametros_personalidade_ao_tts() -> None:
    mock_captura = MagicMock()
    mock_stt = MagicMock()
    mock_ouvinte = MagicMock(spec=["ao_resposta"])

    persn = Personalidade(nome_usuario="Marco")
    persn.emocao.transitar(EstadoEmocional.ALERTA)
    orq = Orquestrador(mock_captura, mock_stt, ouvinte=mock_ouvinte, personalidade=persn)

    with patch("audio.tts.falar") as mock_falar:
        orq._falar_resposta("Atenção, verifique a janela.")

        mock_falar.assert_called_once()
        args, kwargs = mock_falar.call_args
        assert kwargs.get("speed") == 0.92
        assert kwargs.get("voice") == "pm_santa"
