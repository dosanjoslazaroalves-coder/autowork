"""Interpretação determinística das intenções de tempo e clima."""

from __future__ import annotations

import re
from typing import Any


_LOCAL = r"(?P<local>.+?)"
_DIAS = {"hoje": 0, "amanhã": 1, "amanha": 1, "ontem": -1}


def _comando(acao: str, parametros: dict[str, Any], confianca: float = 0.95) -> dict[str, Any]:
    return {
        "tipo": "informacao",
        "acao": acao,
        "parametros": parametros,
        "confianca": confianca,
        "fala": "",
    }


def interpretar(texto: str) -> dict[str, Any] | None:
    """Converte uma pergunta em intenção; retorna ``None`` para comandos legados."""
    if not texto or not texto.strip():
        return None
    frase = re.sub(r"[?!.,;:]+", "", " ".join(texto.lower().strip().split()))

    if re.search(r"\b(diferença|diferenca)\b.*\bhorário\b|\bdiferenca de horario\b", frase):
        partes = re.search(r"entre\s+(.+?)\s+e\s+(.+)$", frase)
        return _comando("diferenca_horario", {
            "origem": partes.group(1) if partes else "Brasil",
            "destino": partes.group(2).removeprefix("o ") if partes else "Japão",
        })

    conversao = re.search(r"converta\s+(?P<hora>\d{1,2}(?::\d{2})?)\s+horas?\s+d[aoe]\s+"
                          r"(?P<origem>.+?)\s+para\s+(?P<destino>.+)$", frase)
    if conversao:
        valores = conversao.groupdict()
        valores["destino"] = re.sub(r"^o horário do |^o horario do ", "", valores["destino"])
        return _comando("converter_horario", valores)

    clima = re.search(r"\b(clima|tempo|temperatura|chover|previsão|previsao)\b", frase)
    if clima:
        data = next((chave for chave in _DIAS if re.search(rf"\b{chave}\b", frase)), "hoje")
        local = None
        localizado = re.search(r"\b(?:em|no|na|para)\s+" + _LOCAL + r"(?:\s+(?:hoje|amanhã|amanha))?$", frase)
        if localizado:
            local = localizado.group("local").strip().rstrip("?!.,")
        return _comando("consultar_clima", {"local": local or "São Paulo", "data": data})

    if re.search(r"\b(data|dia)\b", frase):
        relativo = next((valor for chave, valor in _DIAS.items() if re.search(rf"\b{chave}\b", frase)), 0)
        futuro = re.search(r"(?:daqui a|em)\s+(\d+)\s+dias?", frase)
        if futuro:
            relativo = int(futuro.group(1))
        return _comando("consultar_data", {"dias": relativo})

    if re.search(r"\b(hora|horas)\b", frase):
        localizado = re.search(r"\b(?:em|no|na)\s+(.+)$", frase)
        return _comando("consultar_horario", {"local": localizado.group(1).strip() if localizado else "Brasil"})

    return None


interpretar_comando = interpretar
