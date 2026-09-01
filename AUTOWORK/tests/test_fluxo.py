import unittest
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

if __name__ == "__main__":
    unittest.main()
