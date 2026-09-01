"""Operações de datas e fusos com a base IANA, retornando o padrão de sistema."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from modules.localizacao import resolver_localidade, LocalizacaoError
from modules.tempo.datas import resolver_data_relativa

_DIAS = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo")

def _resolver_tz(local: str) -> str:
    try:
        loc = resolver_localidade(local)
        return loc["timezone"]
    except LocalizacaoError:
        # Tenta interpretar como timezone direto (ex: "America/Sao_Paulo")
        try:
            ZoneInfo(local)
            return local
        except ZoneInfoNotFoundError:
            raise ValueError(f"Fuso horário desconhecido ou localidade não encontrada: {local}")

def consultar_data(expressao: str = "hoje", local: str = "Brasil", agora: datetime | None = None) -> dict:
    try:
        tz = _resolver_tz(local)
        data_alvo, desc = resolver_data_relativa(expressao, timezone=tz, agora=agora)
        
        dia_sem = _DIAS[data_alvo.weekday()]
        mensagem = f"A data {desc} em {local.title()} é {dia_sem}, {data_alvo:%d/%m/%Y}."
        if desc == "hoje":
            mensagem = f"Hoje é {dia_sem}, {data_alvo:%d/%m/%Y}."
            
        return {
            "sucesso": True,
            "acao": "consultar_data",
            "dados": {"data": data_alvo.isoformat(), "dia_semana": dia_sem, "descricao": desc},
            "mensagem": mensagem,
            "erro": None
        }
    except Exception as e:
        return {
            "sucesso": False,
            "acao": "consultar_data",
            "dados": None,
            "mensagem": str(e),
            "erro": "erro_data"
        }

def consultar_horario(local: str = "Brasil", agora: datetime | None = None) -> dict:
    try:
        loc = resolver_localidade(local)
        tz = loc["timezone"]
        nome = loc["nome"]
        
        momento = (agora or datetime.now()).astimezone(ZoneInfo(tz))
        
        return {
            "sucesso": True,
            "acao": "consultar_horario",
            "dados": {"horario": momento.isoformat(), "timezone": tz, "local": loc},
            "mensagem": f"Agora são {momento:%H:%M} em {nome}.",
            "erro": None
        }
    except LocalizacaoError as e:
        return {
            "sucesso": False,
            "acao": "consultar_horario",
            "dados": None,
            "mensagem": str(e),
            "erro": "localidade_invalida"
        }
    except Exception as e:
        return {
            "sucesso": False,
            "acao": "consultar_horario",
            "dados": None,
            "mensagem": "Ocorreu um erro ao consultar o horário.",
            "erro": "erro_inesperado"
        }

def converter_horario(hora: str, origem: str, destino: str) -> dict:
    try:
        base = datetime.strptime(hora, "%H:%M" if ":" in hora else "%H")
    except ValueError:
        return {
            "sucesso": False,
            "acao": "converter_horario",
            "dados": None,
            "mensagem": f"Formato de horário inválido: {hora}. Use HH:MM.",
            "erro": "formato_invalido"
        }
        
    try:
        tz_origem = _resolver_tz(origem)
        tz_destino = _resolver_tz(destino)
        
        convertido = base.replace(tzinfo=ZoneInfo(tz_origem)).astimezone(ZoneInfo(tz_destino))
        
        return {
            "sucesso": True,
            "acao": "converter_horario",
            "dados": {"origem": hora, "convertido": convertido.strftime("%H:%M")},
            "mensagem": f"{hora} em {origem.title()} corresponde a {convertido:%H:%M} em {destino.title()}.",
            "erro": None
        }
    except Exception as e:
        return {
            "sucesso": False,
            "acao": "converter_horario",
            "dados": None,
            "mensagem": str(e),
            "erro": "erro_conversao"
        }

def diferenca_horario(origem: str, destino: str, agora: datetime | None = None) -> dict:
    try:
        tz_origem = _resolver_tz(origem)
        tz_destino = _resolver_tz(destino)
        
        primeiro = (agora or datetime.now()).astimezone(ZoneInfo(tz_origem))
        segundo = primeiro.astimezone(ZoneInfo(tz_destino))
        
        horas = abs((segundo.utcoffset() - primeiro.utcoffset()).total_seconds() / 3600)
        
        return {
            "sucesso": True,
            "acao": "diferenca_horario",
            "dados": {"diferenca_horas": horas},
            "mensagem": f"A diferença de horário entre {origem.title()} e {destino.title()} é de {horas:g} hora(s).",
            "erro": None
        }
    except Exception as e:
        return {
            "sucesso": False,
            "acao": "diferenca_horario",
            "dados": None,
            "mensagem": str(e),
            "erro": "erro_diferenca"
        }
