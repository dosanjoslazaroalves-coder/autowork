"""Roteia intenções informativas para seus módulos responsáveis."""

from __future__ import annotations

from typing import Any

from modules.clima import consultar_clima
from modules.tempo import consultar_data, consultar_horario, converter_horario, diferenca_horario


def dispatch(comando: dict[str, Any]) -> dict[str, Any]:
    acao = comando.get("acao")
    parametros = comando.get("parametros", {})
    try:
        if acao == "consultar_data":
            resposta = consultar_data(**parametros)
        elif acao == "consultar_horario":
            resposta = consultar_horario(**parametros)
        elif acao == "converter_horario":
            resposta = converter_horario(**parametros)
        elif acao == "diferenca_horario":
            resposta = diferenca_horario(**parametros)
        elif acao == "consultar_clima":
            resposta = consultar_clima(**parametros)
        else:
            return {"status": "acao_nao_encontrada", "mensagem": f"Ação '{acao}' não é informativa."}
        return {"status": "sucesso", "mensagem": resposta, "acao": acao, "parametros": parametros}
    except (ValueError, RuntimeError) as exc:
        return {"status": "falha", "mensagem": str(exc), "acao": acao, "parametros": parametros}


dispatch_intencao = dispatch
