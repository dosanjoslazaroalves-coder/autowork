"""Contrato de retorno das ações — evidência, não inferência.

Regras:
    - confirmado=True somente com estado observado.
    - executado=True somente se o efeito colateral foi disparado.
    - sucesso é derivado: True apenas quando confirmado é True.
    - campos obrigatórios ausentes ou tipos inválidos são contrato inválido.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

CAMPOS_BOOL_OBRIGATORIOS = ("executado", "confirmado")


def montar(
    *,
    executado: bool,
    confirmado: bool,
    mensagem: str,
    erro: Optional[str] = None,
    detalhes: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Monta o dicionário interno que o executor interpreta."""
    return {
        "sucesso": bool(confirmado),
        "executado": bool(executado),
        "confirmado": bool(confirmado),
        "mensagem": mensagem,
        "erro": erro,
        "detalhes": detalhes or {},
    }


def _eh_bool_estrito(valor: Any) -> bool:
    return isinstance(valor, bool)


def interpretar_retorno_acao(retorno: Any) -> Dict[str, Any]:
    """Normaliza o retorno bruto da função registrada.

    Não inventa True. Dict incompleto, None, bool cru e tipos estranhos
    viram contrato_invalido — nunca sucesso.
    """
    if not isinstance(retorno, dict):
        return {
            "valido": False,
            "status": "contrato_invalido",
            "executado": False,
            "confirmado": False,
            "mensagem": "A ação não retornou evidência estruturada.",
            "erro": f"retorno_legado:{type(retorno).__name__}",
            "detalhes": {},
        }

    for campo in CAMPOS_BOOL_OBRIGATORIOS:
        if campo not in retorno:
            return {
                "valido": False,
                "status": "contrato_invalido",
                "executado": False,
                "confirmado": False,
                "mensagem": f"A ação omitiu o campo obrigatório '{campo}'.",
                "erro": f"campo_ausente:{campo}",
                "detalhes": dict(retorno.get("detalhes") or {}),
            }
        if not _eh_bool_estrito(retorno[campo]):
            return {
                "valido": False,
                "status": "contrato_invalido",
                "executado": False,
                "confirmado": False,
                "mensagem": f"O campo '{campo}' precisa ser True ou False.",
                "erro": f"campo_invalido:{campo}",
                "detalhes": dict(retorno.get("detalhes") or {}),
            }

    executado = retorno["executado"]
    confirmado = retorno["confirmado"]

    if "sucesso" in retorno and not _eh_bool_estrito(retorno["sucesso"]):
        return {
            "valido": False,
            "status": "contrato_invalido",
            "executado": executado,
            "confirmado": False,
            "mensagem": "O campo 'sucesso' precisa ser True ou False.",
            "erro": "campo_invalido:sucesso",
            "detalhes": dict(retorno.get("detalhes") or {}),
        }

    # Nunca aceitar sucesso declarado sem confirmação observada.
    sucesso = confirmado
    if "sucesso" in retorno and retorno["sucesso"] and not confirmado:
        sucesso = False

    if confirmado:
        status = "sucesso"
    elif executado:
        status = "nao_confirmado"
    else:
        status = "falha"

    mensagem = retorno.get("mensagem")
    if not isinstance(mensagem, str) or not mensagem.strip():
        if status == "sucesso":
            mensagem = "Ação confirmada."
        elif status == "nao_confirmado":
            mensagem = "Comando enviado, mas o efeito não foi confirmado."
        else:
            mensagem = "A ação não foi executada."

    return {
        "valido": True,
        "status": status,
        "sucesso": sucesso,
        "executado": executado,
        "confirmado": confirmado,
        "mensagem": mensagem,
        "erro": retorno.get("erro"),
        "detalhes": dict(retorno.get("detalhes") or {}),
    }
