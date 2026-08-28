"""Consulta Open-Meteo e geocodificação Nominatim, isoladas neste módulo."""

from __future__ import annotations

import json
from datetime import date, timedelta
from functools import lru_cache
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ClimaError(RuntimeError):
    """Erro controlado ao consultar localização ou previsão."""


def _get(url: str) -> dict:
    try:
        request = Request(url, headers={"User-Agent": "AUTOWORK/1.0"})
        with urlopen(request, timeout=8) as resposta:
            dados = json.load(resposta)
    except Exception as exc:
        raise ClimaError("Não foi possível consultar o clima neste momento.") from exc
    if not isinstance(dados, dict):
        raise ClimaError("Resposta inválida do serviço de clima.")
    return dados


@lru_cache(maxsize=64)
def localizar(local: str) -> tuple[float, float, str]:
    dados = _get("https://nominatim.openstreetmap.org/search?" + urlencode({
        "q": local, "format": "json", "limit": 1,
    }))
    if not dados:
        raise ClimaError("Não consegui localizar essa cidade.")
    try:
        return float(dados[0]["lat"]), float(dados[0]["lon"]), dados[0].get("display_name", local)
    except (KeyError, TypeError, ValueError) as exc:
        raise ClimaError("Resposta inválida do serviço de localização.") from exc


def consultar_clima(local: str, data: str = "hoje") -> str:
    latitude, longitude, nome = localizar(local)
    dias = 1 if data in {"amanhã", "amanha"} else 0
    alvo = date.today() + timedelta(days=dias)
    dados = _get("https://api.open-meteo.com/v1/forecast?" + urlencode({
        "latitude": latitude, "longitude": longitude, "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
        "timezone": "auto", "forecast_days": 2,
    }))
    try:
        if dias == 0:
            temp = dados["current"]["temperature_2m"]
            sensacao = dados["current"]["apparent_temperature"]
            return f"Em {local}, agora faz {temp}°C, sensação de {sensacao}°C."
        indice = dados["daily"]["time"].index(alvo.isoformat())
        chuva = dados["daily"]["precipitation_probability_max"][indice]
        maxima = dados["daily"]["temperature_2m_max"][indice]
        minima = dados["daily"]["temperature_2m_min"][indice]
        return f"Amanhã em {local}: de {minima}°C a {maxima}°C, com {chuva}% de chance de chuva."
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise ClimaError("Resposta inválida do serviço de clima.") from exc
