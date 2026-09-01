from __future__ import annotations

import logging

import speech_recognition as sr

from sistema_toke.executor import executar, registrar_comandos_padrao
from sistema_toke.normalizador import normalizar
from modules.voz_teste import falar

logger = logging.getLogger(__name__)

recognizer = sr.Recognizer()
_microfone = sr.Microphone()

recognizer.energy_threshold = 150
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 1.7
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.4

COMANDO_FECHAR = frozenset({"fechar", "encerrar", "desligar"})


def _inicializar_executor() -> None:
    registrar_comandos_padrao()


def calibrar_microfone() -> None:

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
    print("\nPode falar...")
    falar("Pode falar...")

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
        falar("Ocorreu um erro ao conectar ao serviço de reconhecimento.")
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

        erro = resultado_execucao.get("erro")
        if erro:
            print("  ▶ Erro:                %s" % erro)

        dados = resultado_execucao.get("dados")
        if dados:
            print(
                "  ▶ Dados extraídos:     "
                "(Estruturados para o Agente IA)"
            )


def processar_comando(texto: str) -> dict:
    from dispatcher import dispatch
    from interpretador import interpretar

    intencao = interpretar(texto)
    tipo = intencao.get("tipo", "desconhecido")

    # Comando específico: o interpretador já passou pelo parser/resolvedor.
    if tipo == "comando":
        normalizado = normalizar(texto)
        logger.debug("Normalizado: %r", normalizado)

        if intencao.get("resolvido") is False:
            logger.debug(
                "Resolvedor não encontrou ação para a intenção: %s",
                intencao,
            )

            resultado = {
                "status": "falha",
                "acao": intencao.get("acao", ""),
                "mensagem": "Não foi possível resolver a ação.",
            }
        else:
            logger.debug("Executando comando: %s", intencao)

            resultado = executar(
                intencao["acao"],
                **intencao.get("parametros", {}),
            )

        _exibir_resultado(texto, normalizado, intencao, resultado)

        mensagem = resultado.get("mensagem", "")

        if mensagem:
            falar(mensagem)

        return resultado

    # Intenção vazia: nada reconhecido.
    if tipo == "desconhecido":
        logger.debug("Intenção não reconhecida: %r", texto)

        _exibir_resultado(texto, None, None)

        falar("Não reconheci esse comando, senhor.")

        return {
            "status": "nao_reconhecido",
            "texto": texto,
        }

    # Clima, hora, apresentação e conversa seguem pelo dispatcher.
    resultado = dispatch(intencao)

    _exibir_resultado(
        texto,
        None,
        intencao,
        resultado,
    )

    mensagem = resultado.get("mensagem", "")

    if mensagem:
        falar(mensagem)

    return resultado


def main() -> None:
    _inicializar_executor()

    calibrar_microfone()

    print("\nAUTOWORK pronto! Fale um comando.")
    falar("AUTOWORK pronto. Fale um comando, Marco .")
    print()

    while True:
        audio = capturar_audio()

        texto = transcrever_audio(audio)

        if texto is None:
            continue

        if texto in COMANDO_FECHAR:
            print("\nEncerrando AUTOWORK...")
            falar("Encerrando AUTOWORK, senhor.")
            break

        processar_comando(texto)

        print()


if __name__ == "__main__":
    main()