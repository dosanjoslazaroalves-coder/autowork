import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from dispatcher import dispatch
from interpretador import interpretar
from modules.localizacao import resolver_localidade, LocalizacaoError
from modules.tempo import consultar_horario


class TestHorarioCapitais(unittest.TestCase):
    AGORA = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)

    CAPITAIS = {
        "Brasil": ("Brasília", "America/Sao_Paulo"),
        "Estados Unidos": ("Washington, D.C.", "America/New_York"),
        "Canadá": ("Ottawa", "America/Toronto"),
        "México": ("Cidade do México", "America/Mexico_City"),
        "Argentina": ("Buenos Aires", "America/Argentina/Buenos_Aires"),
        "Reino Unido": ("Londres", "Europe/London"),
        "França": ("Paris", "Europe/Paris"),
        "Alemanha": ("Berlim", "Europe/Berlin"),
        "Itália": ("Roma", "Europe/Rome"),
        "Espanha": ("Madri", "Europe/Madrid"),
        "Portugal": ("Lisboa", "Europe/Lisbon"),
        "Rússia": ("Moscou", "Europe/Moscow"),
        "China": ("Pequim", "Asia/Shanghai"),
        "Japão": ("Tóquio", "Asia/Tokyo"),
        "Coreia do Sul": ("Seul", "Asia/Seoul"),
        "Índia": ("Nova Délhi", "Asia/Kolkata"),
        "Austrália": ("Canberra", "Australia/Sydney"),
        "Egito": ("Cairo", "Africa/Cairo"),
        "África do Sul": ("Pretória", "Africa/Johannesburg"),
        "Arábia Saudita": ("Riad", "Asia/Riyadh"),
        "Turquia": ("Ancara", "Europe/Istanbul"),
    }

    def test_paises_resolvem_capital_e_fuso(self):
        for pais, (capital, timezone_iana) in self.CAPITAIS.items():
            with self.subTest(pais=pais):
                local = resolver_localidade(pais)
                self.assertEqual(local["nome"], capital)
                self.assertEqual(local["pais"], pais)
                self.assertEqual(local["timezone"], timezone_iana)

    def test_comandos_naturais_por_capital_e_pais(self):
        casos = {
            "Que horas são em Tóquio?": ("Tóquio", "Asia/Tokyo"),
            "Que horas são no Japão?": ("Tóquio", "Asia/Tokyo"),
            "Que horas são na capital do Japão?": ("Tóquio", "Asia/Tokyo"),
            "Qual é o horário de Paris?": ("Paris", "Europe/Paris"),
            "Que horas são na Inglaterra?": ("Londres", "Europe/London"),
            "Que horas são nos Estados Unidos?": ("Washington, D.C.", "America/New_York"),
            "Que horas são na China?": ("Pequim", "Asia/Shanghai"),
            "Que horas são em Nova Délhi?": ("Nova Délhi", "Asia/Kolkata"),
        }

        for texto, (capital, timezone_iana) in casos.items():
            with self.subTest(texto=texto):
                intencao = interpretar(texto)
                resultado = dispatch(intencao)
                self.assertTrue(resultado["sucesso"])
                self.assertEqual(resultado["dados"]["local"]["nome"], capital)
                self.assertEqual(resultado["dados"]["timezone"], timezone_iana)

    def test_calculo_usa_transicao_real_do_zoneinfo(self):
        for local in ("Tóquio", "Londres", "Washington", "Paris", "Brasília"):
            with self.subTest(local=local):
                resolvido = resolver_localidade(local)
                resultado = consultar_horario(local, agora=self.AGORA)
                esperado = self.AGORA.astimezone(ZoneInfo(resolvido["timezone"]))
                self.assertEqual(resultado["dados"]["horario"], esperado.isoformat())

    def test_localidade_desconhecida_nao_inventa_fuso(self):
        with self.assertRaises(LocalizacaoError):
            resolver_localidade("Nárnia")

        resultado = consultar_horario("Nárnia", agora=self.AGORA)
        self.assertFalse(resultado["sucesso"])
        self.assertEqual(resultado["erro"], "localidade_invalida")


if __name__ == "__main__":
    unittest.main()
