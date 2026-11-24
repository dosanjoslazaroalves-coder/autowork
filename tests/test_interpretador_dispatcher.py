from unittest.mock import patch

from dispatcher import dispatch
from interpretador import interpretar
from modules.clima.clima import ClimaError, localizar


def test_fluxo_horario():
    comando = interpretar("Que horas são no Japão?")
    assert comando["acao"] == "consultar_horario"
    with patch("dispatcher.consultar_horario", return_value="Agora são 04:32 em Japão."):
        resultado = dispatch(comando)
    assert resultado["status"] == "sucesso"
    assert "04:32" in resultado["mensagem"]


def test_interpretacao_clima_amanha():
    comando = interpretar("Vai chover amanhã em São Paulo?")
    assert comando == {
        "tipo": "informacao",
        "acao": "consultar_clima",
        "parametros": {"local": "são paulo", "data": "amanhã"},
        "confianca": 0.95,
        "fala": "",
    }


def test_erro_de_fuso_controlado():
    resultado = dispatch(interpretar("Que horas são em Marte?"))
    assert resultado["status"] == "falha"
    assert "Fuso horário desconhecido" in resultado["mensagem"]


def test_cidade_invalida():
    with patch("modules.clima.clima._get", return_value=[]):
        try:
            localizar("Cidade inexistente")
        except ClimaError as erro:
            assert str(erro) == "Não consegui localizar essa cidade."
        else:
            raise AssertionError("localização inválida deveria falhar")
