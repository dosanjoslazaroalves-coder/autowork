import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

_DIAS_SEMANA = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo")

def resolver_data_relativa(expressao: str, timezone: str = "America/Sao_Paulo", agora: datetime = None) -> tuple[datetime, str]:
    """
    Resolve uma expressão temporal ("hoje", "amanhã", "daqui a 3 dias")
    para um datetime exato, no timezone especificado.
    Retorna (data_alvo, descricao).
    """
    if not expressao:
        expressao = "hoje"
        
    expr = expressao.lower().strip()
    
    tz = ZoneInfo(timezone)
    base = (agora or datetime.now()).astimezone(tz)
    data_alvo = base
    descricao = ""
    
    if expr == "hoje":
        descricao = "hoje"
    elif expr in {"amanhã", "amanha"}:
        data_alvo = base + timedelta(days=1)
        descricao = "amanhã"
    elif expr == "ontem":
        data_alvo = base - timedelta(days=1)
        descricao = "ontem"
    elif "semana" in expr and "daqui a" in expr:
        data_alvo = base + timedelta(days=7)
        descricao = "daqui a uma semana"
    else:
        # Tenta "daqui a N dias"
        match = re.search(r"daqui a\s+(\d+)\s+dias?", expr)
        if match:
            dias = int(match.group(1))
            data_alvo = base + timedelta(days=dias)
            descricao = f"daqui a {dias} dias"
        else:
            # Tenta "próxima segunda-feira", etc
            for i, dia_str in enumerate(_DIAS_SEMANA):
                # match se bater apenas parte, ex "segunda"
                dia_curto = dia_str.split("-")[0]
                if dia_curto in expr or dia_str in expr:
                    dias_ate = (i - base.weekday()) % 7
                    if dias_ate == 0:
                        dias_ate = 7 # Próxima = próxima semana se já for hoje
                    data_alvo = base + timedelta(days=dias_ate)
                    descricao = f"na próxima {dia_str}"
                    break
            else:
                # Default para hoje se não reconhecer
                descricao = "hoje"
                
    return data_alvo, descricao
