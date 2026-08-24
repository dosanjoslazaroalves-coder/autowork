

from __future__ import annotations

import logging
from datetime import datetime

import speech_recognition as sr

from sistema_toke.executor import REGISTRO_ACOES, executar, registrar
from sistema_toke.normalizador import normalizar
from sistema_toke.parser import parse
from modules.voz_teste  import falar
from metricas import (
    envolver_falar,
    etapa,
    finalizar_ciclo_comando,
    iniciar_ciclo_comando,
    painel_memoria,
    profiling_ativo,
    publicar_relatorio,
    texto_para_fala,
    falar_relatorio_ativo,
)

logger = logging.getLogger(__name__)

recognizer = sr.Recognizer()
_microfone = sr.Microphone()

# TTS continua em modules.voz_teste; metricas só cronometra quando o profiling está ligado.
if profiling_ativo():
    falar = envolver_falar(falar)

# Ajustes para comandos curto
recognizer.energy_threshold = 200
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 1.7
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.4

COMANDO_FECHAR = frozenset({"fechar", "encerrar", "desligar"})


def _informar_hora() -> None:

    hora_atual = datetime.now().strftime("%H:%M:%S")
    print(f"  Hora atual: {hora_atual}")
    falar(f"  Hora atual: {hora_atual}")
    logger.info("Hora informada: %s", hora_atual)


def _informar_data() -> None:

    data_atual = datetime.now().strftime("%d/%m/%Y")
    print(f"  Data atual: {data_atual}")
    falar(f"  Data atual: {data_atual}")
    logger.info("Data informada: %s", data_atual)

def _inicializar_executor() -> None:

    from comd_rapidos.atalhos import Janela

    janela = Janela()
    janela.registrar_no_executor(registrar)

    from comd_rapidos.atalho_nav import AtalhoNav

    atalho_nav = AtalhoNav()
    atalho_nav.registrar_no_executor(registrar)

    from comd_rapidos.abrir_app import abrir_app

    registrar("abrir_app", abrir_app)

    from comd_rapidos.abrir_site import abrir_site

    registrar("abrir_site", abrir_site)

    registrar("informar_hora", _informar_hora)
    registrar("informar_data", _informar_data)

    logger.info(
        "Executor inicializado com %d ação(ns).",
        len(REGISTRO_ACOES),
    )


def calibrar_microfone() -> None:

    try:
        print("Calibrando microfone...")
        falar("Calibrando microfone senhor ")

        with _microfone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Microfone calibrado.")
        falar("Microfone calibrado senhor ")
        logger.info(
            "Microfone calibrado. energy_threshold=%s",
            recognizer.energy_threshold,
        )

    except Exception as exc:
        logger.exception("Erro ao calibrar o microfone: %s", exc)


def capturar_audio() -> sr.AudioData:
    print("\nPode falar...")
    falar("\nPode falar...")

    with _microfone as source:
        return recognizer.listen(source)


def transcrever_audio(audio: sr.AudioData) -> str | None:

    try:
        texto = recognizer.recognize_google(
            audio,
            language="pt-BR",
        )

        return texto.lower().strip()

    except sr.UnknownValueError:
        print("Não consegui entender.")
        falar("Não consegui entender, pode repetir senhor.")
        return None

    except sr.RequestError:
        print("Erro ao conectar ao serviço do Google.")
        return None


def _exibir_banner() -> None:

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


def _exibir_e_falar_memoria() -> None:
    """Mostra e narra RAM coletada em metricas.py. Não mede aqui."""
    bloco = painel_memoria.texto_terminal_comando()
    if bloco:
        print()
        print(bloco)
    texto_memoria = painel_memoria.texto_fala_comando()
    falar(texto_memoria)


def processar_comando(texto: str) -> dict:

    _exibir_banner()
    ciclo = iniciar_ciclo_comando()
    medidor = ciclo.etapas if ciclo is not None else None
    painel_memoria.marcar_antes_comando()

    with etapa(medidor, "normalizador"):
        normalizado = normalizar(texto)
    logger.debug("Normalizado: %r", normalizado)

    with etapa(medidor, "parser"):
        comando = parse(texto)

    if comando is None:
        logger.debug("Comando não reconhecido pelo parser: %r", normalizado or texto)
        with etapa(medidor, "resposta"):
            _exibir_resultado(texto, normalizado, None)
        painel_memoria.marcar_depois_comando()
        _exibir_e_falar_memoria()
        _encerrar_metricas_ciclo()
        return {"status": "nao_reconhecido", "texto": texto}

    logger.debug("Executando comando: %s", comando)
    acao = comando["acao"]
    params = comando.get("parametros", {})
    with etapa(medidor, "executor"):
        resultado = executar(acao, **params)

    with etapa(medidor, "resposta"):
        _exibir_resultado(texto, normalizado, comando, resultado)

    painel_memoria.marcar_depois_comando()
    _exibir_e_falar_memoria()
    _encerrar_metricas_ciclo()
    return resultado


def _encerrar_metricas_ciclo() -> None:
    relatorio = finalizar_ciclo_comando()
    if relatorio is None:
        return
    publicar_relatorio(relatorio)
    if falar_relatorio_ativo():
        # Narração depois da coleta, para não entrar no tempo do comando.
        falar(texto_para_fala(relatorio))


def main() -> None:
    painel_memoria.marcar_inicio_processo()

    _inicializar_executor()
    painel_memoria.ler()

    calibrar_microfone()
    print("\nAUTOWORK pronto! Fale um comando.")
    falar("\nAUTOWORK pronto! Fale um comando.")
    print()
    print(painel_memoria.texto_terminal_inicio())
    falar(painel_memoria.texto_fala_inicio())

    while True:

        audio = capturar_audio()

        texto = transcrever_audio(audio)

        if texto is None:
            continue

        if texto in COMANDO_FECHAR:
            print("\nEncerrando AUTOWORK...")
            break

        processar_comando(texto)

        print()


if __name__ == "__main__":
    main()
