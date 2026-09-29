import unittest
from unittest.mock import patch
from interpretador import interpretar
from dispatcher import dispatch

class TestFluxo(unittest.TestCase):
    def test_clima_hoje(self):
        intencao = interpretar("como está o clima de campinas")
        self.assertIsNotNone(intencao)
        self.assertEqual(intencao["acao"], "consultar_clima")
        self.assertEqual(intencao["parametros"]["local"], "campinas")
        
        resultado = dispatch(intencao)
        self.assertTrue(resultado["sucesso"])
        self.assertIn("temp", resultado["dados"])

    def test_horario_londres(self):
        intencao = interpretar("que horas são em londres")
        self.assertEqual(intencao["acao"], "consultar_horario")
        
        resultado = dispatch(intencao)
        self.assertTrue(resultado["sucesso"])
        self.assertEqual(resultado["dados"]["timezone"], "Europe/London")
        
    def test_diferenca(self):
        intencao = interpretar("qual a diferença de horário entre campinas e londres")
        self.assertEqual(intencao["acao"], "diferenca_horario")
        
        resultado = dispatch(intencao)
        self.assertTrue(resultado["sucesso"])
        self.assertIn("diferenca_horas", resultado["dados"])
        
    def test_clima_amanha_salvador(self):
        intencao = interpretar("vai chover amanhã em salvador")
        self.assertEqual(intencao["acao"], "consultar_clima")
        self.assertEqual(intencao["parametros"]["data"], "amanhã")
        
        resultado = dispatch(intencao)
        self.assertTrue(resultado["sucesso"])

    def test_metadado_da_intencao_nao_e_repassado_ao_modulo(self):
        """O texto original é rastreabilidade, não argumento da função alvo."""
        chamada = {}

        def horario(**parametros):
            chamada.update(parametros)
            return {"sucesso": True, "mensagem": "Agora são 10:00."}

        with patch("dispatcher.consultar_horario", side_effect=horario):
            resultado = dispatch({
                "acao": "consultar_horario",
                "parametros": {"local": "Brasil", "texto_original": "Que horas são?"},
            })

        self.assertTrue(resultado["sucesso"])
        self.assertEqual(chamada, {"local": "Brasil"})

if __name__ == "__main__":
    unittest.main()
