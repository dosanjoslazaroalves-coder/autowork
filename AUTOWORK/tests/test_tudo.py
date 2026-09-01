import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from modules.localizacao import resolver_localidade, LocalizacaoError
from modules.tempo.datas import resolver_data_relativa
from modules.clima import consultar_clima
from modules.tempo import consultar_horario, consultar_data, diferenca_horario

class TestLocalizacao(unittest.TestCase):
    def test_cidade_brasil(self):
        loc = resolver_localidade("Campinas")
        self.assertEqual(loc["nome"], "Campinas")
        self.assertEqual(loc["estado"], "SP")
        self.assertEqual(loc["timezone"], "America/Sao_Paulo")
        
    def test_cidade_exterior(self):
        loc = resolver_localidade("Tóquio")
        self.assertEqual(loc["pais"], "Japão")
        self.assertEqual(loc["timezone"], "Asia/Tokyo")
        
    def test_alias(self):
        loc = resolver_localidade("Tokyo")
        self.assertEqual(loc["nome"], "Tóquio")
        
    def test_cidade_invalida(self):
        with self.assertRaises(LocalizacaoError):
            resolver_localidade("CidadeInexistente1234")

class TestTempoDatas(unittest.TestCase):
    def test_horario(self):
        res = consultar_horario("Japão")
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["dados"]["timezone"], "Asia/Tokyo")
        
    def test_horario_invalido(self):
        res = consultar_horario("Marte")
        self.assertFalse(res["sucesso"])
        
    def test_diferenca(self):
        res = diferenca_horario("São Paulo", "Londres")
        self.assertTrue(res["sucesso"])
        self.assertIn("diferenca_horas", res["dados"])
        
    def test_datas_relativas(self):
        agora = datetime(2023, 10, 10, 12, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
        dt, desc = resolver_data_relativa("amanhã", agora=agora)
        self.assertEqual(dt.day, 11)
        self.assertEqual(desc, "amanhã")

class TestClima(unittest.TestCase):
    def test_clima_cidade(self):
        res = consultar_clima("Campinas", "hoje")
        self.assertTrue(res["sucesso"])
        self.assertIn("temp", res["dados"])
        
    def test_clima_amanha(self):
        res = consultar_clima("Salvador", "amanhã")
        self.assertTrue(res["sucesso"])
        self.assertIn("t_min", res["dados"])
        
    def test_clima_cidade_invalida(self):
        res = consultar_clima("CidadeInexistente1234", "hoje")
        self.assertFalse(res["sucesso"])
        self.assertEqual(res["erro"], "cidade_nao_encontrada")

if __name__ == "__main__":
    unittest.main()
