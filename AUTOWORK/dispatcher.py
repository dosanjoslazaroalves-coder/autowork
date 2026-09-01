
from __future__ import annotations
from typing import Any
from modules.clima import consultar_clima
from modules.tempo import consultar_data, consultar_horario, converter_horario, diferenca_horario

_apresentador = None
_chatbot = None


def _obter_apresentador():
    global _apresentador
    if _apresentador is None:
        from apresent import Apresentador
        _apresentador = Apresentador()
    return _apresentador


def _obter_chatbot():
    global _chatbot
    if _chatbot is None:
        from conversa.chatbot import Chatbot
        _chatbot = Chatbot()
    return _chatbot


def _apresentar(texto_original: str) -> dict[str, Any]:
    try:
        resposta = _obter_apresentador().apresentar(texto_original)
    except Exception as exc:
        resposta = None
        print(f"Erro no módulo de apresentação: {exc}")

    if not resposta:
        return {
            "status": "falha",
            "acao": "apresentar",
            "mensagem": "Não consegui gerar a apresentação, senhor.",
        }

    return {"status": "sucesso", "acao": "apresentar", "mensagem": resposta}


def _conversar(mensagem: str) -> dict[str, Any]:
    try:
        resposta = _obter_chatbot().enviar(mensagem)
    except Exception as exc:
        resposta = ""
        print(f"Erro no módulo de conversa: {exc}")

    if not resposta:
        return {
            "status": "falha",
            "acao": "chat",
            "mensagem": "Não foi possível obter uma resposta da IA.",
        }

    return {"status": "sucesso", "acao": "chat", "mensagem": resposta}


def dispatch(comando: dict[str, Any]) -> dict[str, Any]:
    acao = comando.get("acao")
    parametros = comando.get("parametros", {})

    if acao == "apresentar":
        resultado = _apresentar(parametros.get("texto_original", "") or str(parametros))
        resultado["parametros"] = parametros
        return resultado

    if acao == "chat":
        resultado = _conversar(parametros.get("texto_original", "") or str(parametros))
        resultado["parametros"] = parametros
        return resultado

    funcoes = {
        "consultar_data": consultar_data,
        "consultar_horario": consultar_horario,
        "converter_horario": converter_horario,
        "diferenca_horario": diferenca_horario,
        "consultar_clima": consultar_clima,
    }

    if acao not in funcoes:
        return {
            "status": "acao_nao_encontrada",
            "mensagem": f"Ação '{acao}' não é informativa.",
            "sucesso": False,
            "acao": acao,
            "erro": "acao_invalida"
        }

    try:
        resultado = funcoes[acao](**parametros)

        resultado["status"] = "sucesso" if resultado.get("sucesso") else "falha"
        resultado["parametros"] = parametros

        return resultado
    except Exception as exc:
        return {
            "status": "falha",
            "sucesso": False,
            "acao": acao,
            "parametros": parametros,
            "mensagem": f"Ocorreu um erro interno: {str(exc)}",
            "erro": "excecao_nao_tratada",
            "dados": None
        }
