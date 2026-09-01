import logging
import sys

from conversa.chatbot import Chatbot

AJUDA = """Comandos:
  /ajuda   Mostra esta ajuda
  /limpar  Apaga o histórico da conversa
  /sair    Encerra o programa
"""


def configurar_logs() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )


def imprimir_cabecalho() -> None:
    print("========================================")
    print("          AUTOWORK CHATBOT")
    print("========================================")
    print()
    print("Digite sua mensagem.")
    print("Use /ajuda para comandos.")
    print()


def main() -> None:
    configurar_logs()
    chatbot = Chatbot()
    imprimir_cabecalho()

    while True:
        try:
            entrada = str(input("Você: ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("AUTOWORK: Até logo.")
            break

        if not entrada:
            continue

        comando = entrada.lower()
        if comando == "/sair":
            print("AUTOWORK: Até logo.")
            break
        if comando == "/limpar":
            chatbot.limpar_historico()
            print("AUTOWORK: Histórico limpo.")
            print()
            continue
        if comando == "/ajuda":
            print(AJUDA)
            continue

        resposta = chatbot.enviar(entrada)
        print(f"AUTOWORK: {resposta}")
        print()


if __name__ == "__main__":
    main()
