"""Integração isolada com Nominatim e Open-Meteo."""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta, datetime
from http.client import HTTPResponse
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from modules.localizacao import resolver_localidade, LocalizacaoError
from modules.tempo.datas import resolver_data_relativa

logger = logging.getLogger(__name__)

class ClimaError(RuntimeError):
    pass

def _get(url: str) -> dict | list:
    """Faz GET e retorna o JSON deserializado (dict ou list)."""
    logger.debug("API request — URL: %s", url)
    try:
        req = Request(url, headers={"User-Agent": "AUTOWORK/1.0"})
        with urlopen(req, timeout=8) as resposta:  
            codigo = resposta.status
            corpo = resposta.read()
    except HTTPError as exc:
        logger.error("Erro HTTP %s — URL: %s", exc.code, url)
        raise ClimaError(f"Erro HTTP {exc.code} ao consultar o serviço.") from exc
    except URLError as exc:
        logger.error("Erro de conexão — %s — URL: %s", exc.reason, url)
        raise ClimaError("Erro de conexão com o serviço de clima.") from exc
    except TimeoutError as exc:
        logger.error("Timeout — URL: %s", url)
        raise ClimaError("O serviço de clima demorou muito para responder.") from exc
    except Exception as exc:
        logger.error("Erro inesperado — %s: %s — URL: %s", type(exc).__name__, exc, url)
        raise ClimaError("Não foi possível consultar o clima neste momento.") from exc

    try:
        dados = json.loads(corpo)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("JSON inválido na resposta — URL: %s", url)
        raise ClimaError("Resposta com JSON inválido do serviço de clima.") from exc

    if not isinstance(dados, (dict, list)):
        raise ClimaError("Resposta inválida do serviço de clima.")

    return dados

# Mapeamento do código WMO
_WMO_CODES = {
    0: "céu limpo", 1: "predominantemente limpo", 2: "parcialmente nublado", 3: "nublado",
    45: "névoa", 48: "névoa com geada",
    51: "chuvisco leve", 53: "chuvisco moderado", 55: "chuvisco forte",
    61: "chuva leve", 63: "chuva moderada", 65: "chuva forte",
    71: "neve leve", 73: "neve moderada", 75: "neve forte",
    80: "pancadas de chuva leves", 81: "pancadas de chuva moderadas", 82: "pancadas de chuva fortes",
    95: "tempestade", 96: "tempestade com granizo leve", 99: "tempestade com granizo forte"
}

def consultar_clima(local: str = "São Paulo", data: str = "hoje") -> dict:
    try:
        loc = resolver_localidade(local)
        lat = loc["latitude"]
        lon = loc["longitude"]
        tz = loc["timezone"]
        nome_local = loc["nome"]
        
        if not lat or not lon:
            raise ClimaError("Coordenadas geográficas não encontradas para o local.")
            
        data_alvo, desc_data = resolver_data_relativa(data, timezone=tz)
        
        hoje_tz = datetime.now().astimezone(__import__("zoneinfo").ZoneInfo(tz)).date()
        dias_diff = (data_alvo.date() - hoje_tz).days
        
        if dias_diff < 0:
            raise ClimaError("Não é possível consultar o clima no passado.")
        if dias_diff > 7:
            raise ClimaError("A previsão do tempo só alcança até 7 dias.")
            
        dados = _get("https://api.open-meteo.com/v1/forecast?" + urlencode({
            "latitude": lat, "longitude": lon, 
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,precipitation,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
            "timezone": "auto", "forecast_days": max(dias_diff + 1, 2)
        }))
        
        if not isinstance(dados, dict):
            raise ClimaError("Resposta inesperada da API de clima.")
            
        if dias_diff == 0:
            atual = dados["current"]
            temp = atual['temperature_2m']
            sensacao = atual['apparent_temperature']
            umidade = atual['relative_humidity_2m']
            wmo = atual.get('weather_code', 0)
            condicao = _WMO_CODES.get(wmo, "condição desconhecida")
            
            mensagem = f"Hoje em {nome_local}, o clima é de {condicao}, com temperatura de {temp}°C, sensação térmica de {sensacao}°C e umidade de {umidade}%."
            return {
                "sucesso": True,
                "acao": "consultar_clima",
                "dados": {"temp": temp, "sensacao": sensacao, "umidade": umidade, "condicao": condicao, "local": loc},
                "mensagem": mensagem,
                "erro": None
            }
        else:
            try:
                indice = dias_diff
                t_min = dados['daily']['temperature_2m_min'][indice]
                t_max = dados['daily']['temperature_2m_max'][indice]
                chuva_prob = dados['daily']['precipitation_probability_max'][indice]
                wmo = dados['daily']['weather_code'][indice]
                condicao = _WMO_CODES.get(wmo, "condição desconhecida")
                
                mensagem = f"A previsão para {desc_data} em {nome_local} é de {condicao}, com mínima de {t_min}°C, máxima de {t_max}°C e {chuva_prob}% de chance de chuva."
                return {
                    "sucesso": True,
                    "acao": "consultar_clima",
                    "dados": {"t_min": t_min, "t_max": t_max, "chuva_prob": chuva_prob, "condicao": condicao, "local": loc},
                    "mensagem": mensagem,
                    "erro": None
                }
            except (KeyError, IndexError) as exc:
                raise ClimaError("Dados da previsão não estão disponíveis para essa data.") from exc
                
    except LocalizacaoError as e:
        return {
            "sucesso": False,
            "acao": "consultar_clima",
            "dados": None,
            "mensagem": str(e),
            "erro": "cidade_nao_encontrada"
        }
    except ClimaError as e:
        return {
            "sucesso": False,
            "acao": "consultar_clima",
            "dados": None,
            "mensagem": str(e),
            "erro": "api_indisponivel"
        }
    except Exception as e:
        logger.exception("Erro não tratado ao consultar clima")
        return {
            "sucesso": False,
            "acao": "consultar_clima",
            "dados": None,
            "mensagem": "Ocorreu um erro inesperado ao consultar o clima.",
            "erro": "erro_inesperado"
        }
