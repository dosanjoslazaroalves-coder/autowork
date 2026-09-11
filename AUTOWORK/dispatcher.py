
from __future__ import annotations
from typing import Any
from modules.clima import consultar_clima
from modules.localizacao import localizar_usuario
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
        import logging
        logging.getLogger(__name__).error(f"Erro no módulo de apresentação: {exc}")

    if not resposta:
        return {
            "status": "falha",
            "acao": "apresentar",
            "tipo": "erro",
            "falar": True,
            "mensagem": "Não consegui gerar a apresentação.",
        }

    return {
        "status": "sucesso",
        "acao": "apresentar",
        "tipo": "informacao",
        "falar": True,
        "mensagem": resposta,
    }


def _conversar(mensagem: str) -> dict[str, Any]:
    try:
        resposta = _obter_chatbot().responder(mensagem)
    except Exception as exc:
        resposta = {"tipo": "conversa", "mensagem": "", "sucesso": False}
        import logging
        logging.getLogger(__name__).error(f"Erro no módulo de conversa: {exc}")

    if not resposta.get("mensagem"):
        return {
            "status": "falha",
            "acao": "chat",
            "tipo": "erro",
            "falar": True,
            "mensagem": "Não foi possível obter uma resposta da IA.",
        }

    sucesso = bool(resposta.get("sucesso"))
    return {
        "status": "sucesso" if sucesso else "falha",
        "acao": "chat",
        "tipo": "conversa" if sucesso else "erro",
        "falar": True,
        "mensagem": resposta["mensagem"],
    }


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
        "consultar_localizacao": localizar_usuario,
    }

    if acao not in funcoes:
        return {
            "status": "acao_nao_encontrada",
            "mensagem": f"Ação '{acao}' não é informativa.",
            "sucesso": False,
            "acao": acao,
            "tipo": "erro",
            "falar": False,
            "erro": "acao_invalida"
        }

    try:
        resultado = funcoes[acao](**parametros)

        sucesso = bool(resultado.get("sucesso"))
        resultado["status"] = "sucesso" if sucesso else "falha"
        resultado["tipo"] = "informacao" if sucesso else "erro"
        resultado["falar"] = True
        resultado["parametros"] = parametros

        return resultado
    except Exception as exc:
        # Detalhe técnico fica no campo "erro" (terminal/log); a mensagem
        # falada é curta e amigável.
        return {
            "status": "falha",
            "sucesso": False,
            "acao": acao,
            "tipo": "erro",
            "falar": True,
            "parametros": parametros,
            "mensagem": "Não consegui obter as informações.",
            "erro": f"excecao_nao_tratada: {exc}",
            "dados": None
        }
