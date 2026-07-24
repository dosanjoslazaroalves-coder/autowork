"""
fala.py — Captura de voz e orquestração do pipeline AUTOWORK.

Responsabilidade:
    1. Capturar áudio do microfone
    2. Converter áudio em texto (Speech-to-Text)
    3. Passar o texto para o pipeline (normalizador → parser → executor)
    4. Exibir feedback visual no terminal
"""

from __future__ import annotations

import logging
from datetime import datetime

import speech_recognition as sr

from executor import REGISTRO_ACOES, executar, registrar
from normalizador import normalizar
from parser import parse

logger = logging.getLogger(__name__)

recognizer = sr.Recognizer()
_microfone = sr.Microphone()

# Ajustes para comandos curto
recognizer.energy_threshold = 250
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 3.5
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.4

COMANDO_FECHAR = frozenset({"fechar", "encerrar", "desligar"})


# ══════════════════════════════════════════════
# Funções informativas (executadas localmente)
# ══════════════════════════════════════════════


def _informar_hora() -> None:
    """Exibe a hora atual no terminal."""
    hora_atual = datetime.now().strftime("%H:%M:%S")
    print(f"  Hora atual: {hora_atual}")
    logger.info("Hora informada: %s", hora_atual)


def _informar_data() -> None:
    """Exibe a data atual no terminal."""
    data_atual = datetime.now().strftime("%d/%m/%Y")
    print(f"  Data atual: {data_atual}")
    logger.info("Data informada: %s", data_atual)

def _inicializar_executor() -> None:

    from atalhos import Janela

    janela = Janela()
    janela.registrar_no_executor(registrar)

    # ── Atalhos do navegador (AtalhoNav) ──
    from atalho_nav import AtalhoNav

    atalho_nav = AtalhoNav()
    atalho_nav.registrar_no_executor(registrar)

    # ── Abrir aplicativos ──
    from abrir_app import abrir_app

    registrar("abrir_app", abrir_app)

    # ── Abrir sites ──
    from abrir_site import abrir_site

    registrar("abrir_site", abrir_site)

    # ── Ações informativas locais ──
    registrar("informar_hora", _informar_hora)
    registrar("informar_data", _informar_data)

    logger.info(
        "Executor inicializado com %d ação(ns).",
        len(REGISTRO_ACOES),
    )


def calibrar_microfone() -> None:
    """Calibra o microfone uma única vez."""
    try:
        print("Calibrando microfone...")

        with _microfone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)

        print("Microfone calibrado.")
        logger.info(
            "Microfone calibrado. energy_threshold=%s",
            recognizer.energy_threshold,
        )

    except Exception as exc:
        logger.exception("Erro ao calibrar o microfone: %s", exc)


def capturar_audio() -> sr.AudioData:
    """Captura o áudio do microfone."""
    print("\nPode falar...")

    with _microfone as source:
        return recognizer.listen(source)


def transcrever_audio(audio: sr.AudioData) -> str | None:
    """Converte áudio em texto."""
    try:
        texto = recognizer.recognize_google(
            audio,
            language="pt-BR",
        )

        return texto.lower().strip()

    except sr.UnknownValueError:
        print("Não consegui entender.")
        return None

    except sr.RequestError:
        print("Erro ao conectar ao serviço do Google.")
        return None


def _exibir_banner() -> None:
    """Exibe o banner do AUTOWORK no terminal."""
    print()
    print("=" * 45)
    print("            AUTOWORK")
    print("=" * 45)


def _exibir_resultado(
    texto: str,
    normalizado: str | None,
    comando: dict | None,
    resultado_execucao: dict | None = None,
) -> None:
    """Exibe o resultado detalhado do processamento no terminal.

    Args:
        texto: Texto original capturado.
        normalizado: Texto após normalização.
        comando: Dicionário de comando (ou None se não reconhecido).
        resultado_execucao: Resultado da execução (ou None).
    """
    print()
    print("  ▶ Texto capturado:    %s" % texto)

    if normalizado:
        print("  ▶ Texto normalizado:  %s" % normalizado)

    if comando is None:
        print("  ▶ Parser:             Não reconhecido")
        return

    acao = comando.get("acao", "")
    parametros = comando.get("parametros", {})

    print("  ▶ Ação reconhecida:    %s" % acao)

    if parametros:
        for chave, valor in parametros.items():
            print("  ▶   %s: %s" % (chave, valor))

    if resultado_execucao:
        status = resultado_execucao.get("status", "?")
        print("  ▶ Status:              %s" % status)

        mensagem = resultado_execucao.get("mensagem", "")
        if mensagem:
            print("  ▶ %s" % mensagem)


# ══════════════════════════════════════════════
# Pipeline principal
# ══════════════════════════════════════════════


def processar_comando(texto: str) -> dict:

    _exibir_banner()

    # 1. Normaliza o texto
    normalizado = normalizar(texto)
    logger.debug("Normalizado: %r", normalizado)

    # 2. Parseia o comando
    comando = parse(texto)

    # 3. Se não reconheceu, retorna
    if comando is None:
        logger.debug("Comando não reconhecido pelo parser: %r", normalizado or texto)
        _exibir_resultado(texto, normalizado, None)
        return {"status": "nao_reconhecido", "texto": texto}

    # 4. Executa o comando via executor (registry pattern)
    # Passa apenas a ação e os parâmetros reais, sem metadados
    logger.debug("Executando comando: %s", comando)
    acao = comando["acao"]
    params = comando.get("parametros", {})
    resultado = executar(acao, **params)

    # 5. Exibe resultado
    _exibir_resultado(texto, normalizado, comando, resultado)

    return resultado


def main() -> None:
    """Loop principal do AUTOWORK.

    1. Inicializa o executor (registra todas as ações)
    2. Calibra o microfone
    3. Loop infinito: escuta → transcreve → processa
    """
    # Inicializa o sistema de registro de ações
    _inicializar_executor()

    # Calibra o microfone
    calibrar_microfone()

    print("\nAUTOWORK pronto! Fale um comando.")

    while True:
        # 1. Captura áudio
        audio = capturar_audio()

        # 2. Transcreve áudio → texto
        texto = transcrever_audio(audio)

        if texto is None:
            continue

        # 3. Verifica comando de encerramento
        if texto in COMANDO_FECHAR:
            print("\nEncerrando AUTOWORK...")
            break

        # 4. Processa o comando pelo pipeline completo
        processar_comando(texto)

        print()


if __name__ == "__main__":
    main()
