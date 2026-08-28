from datetime import datetime
from zoneinfo import ZoneInfo

from modules.tempo.tempo import consultar_data, consultar_horario, converter_horario, diferenca_horario


def test_consultar_data_relativa():
    agora = datetime(2026, 8, 28, 12, tzinfo=ZoneInfo("America/Sao_Paulo"))
    assert consultar_data(1, agora) == "sábado, 29/08/2026"


def test_consultar_horario_e_conversao():
    agora = datetime(2026, 1, 1, 12, tzinfo=ZoneInfo("America/Sao_Paulo"))
    assert "12:00" in consultar_horario("Brasil", agora)
    assert converter_horario("15", "Brasil", "Japão") == "03:00 em Japão."


def test_diferenca_de_fuso():
    agora = datetime(2026, 8, 28, 12, tzinfo=ZoneInfo("America/Sao_Paulo"))
    assert "12 hora(s)" in diferenca_horario("Brasil", "Japão", agora)
