"""Datas e horários usando a base IANA de fusos horários."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


_FUSOS = {
    "brasil": "America/Sao_Paulo", "são paulo": "America/Sao_Paulo", "sao paulo": "America/Sao_Paulo",
    "rio de janeiro": "America/Sao_Paulo", "japão": "Asia/Tokyo", "japao": "Asia/Tokyo",
    "tóquio": "Asia/Tokyo", "toquio": "Asia/Tokyo", "londres": "Europe/London",
    "nova york": "America/New_York", "portugal": "Europe/Lisbon",
}
_DIAS = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo")


def resolver_fuso(local: str) -> str:
    valor = " ".join(local.lower().strip().split())
    fuso = _FUSOS.get(valor, local if "/" in local else None)
    if not fuso:
        raise ValueError(f"Fuso horário desconhecido: {local}")
    try:
        ZoneInfo(fuso)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Fuso horário desconhecido: {local}") from exc
    return fuso


def consultar_data(dias: int = 0, agora: datetime | None = None) -> str:
    data = (agora or datetime.now()).date() + timedelta(days=int(dias))
    return f"{_DIAS[data.weekday()]}, {data.strftime('%d/%m/%Y')}"


def consultar_horario(local: str = "Brasil", agora: datetime | None = None) -> str:
    fuso = resolver_fuso(local)
    momento = (agora or datetime.now()).astimezone(ZoneInfo(fuso))
    return f"Agora são {momento:%H:%M} em {local.title()}."


def converter_horario(hora: str, origem: str, destino: str, data: datetime | None = None) -> str:
    try:
        base = datetime.strptime(hora, "%H:%M" if ":" in hora else "%H")
    except ValueError as exc:
        raise ValueError(f"Horário inválido: {hora}") from exc
    instante = base.replace(tzinfo=ZoneInfo(resolver_fuso(origem)))
    convertido = instante.astimezone(ZoneInfo(resolver_fuso(destino)))
    return f"{convertido:%H:%M} em {destino.title()}."


def diferenca_horario(origem: str, destino: str, agora: datetime | None = None) -> str:
    primeiro = (agora or datetime.now()).astimezone(ZoneInfo(resolver_fuso(origem)))
    segundo = primeiro.astimezone(ZoneInfo(resolver_fuso(destino)))
    horas = (segundo.utcoffset() - primeiro.utcoffset()).total_seconds() / 3600
    return f"A diferença de horário é de {abs(horas):g} hora(s)."
