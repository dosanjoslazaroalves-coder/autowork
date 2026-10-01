import json
import unittest
from unittest.mock import patch

from interpretador import interpretar
from sistema_toke.resolvedor_ia import interpretar_com_ia


class TestAssistenteSemantico(unittest.TestCase):
    def test_frases_naturais_de_abertura(self):
        casos = (
            "abre o chrome",
            "por favor abre o navegador para mim",
            "eu preciso que você abra o navegador porque quero pesquisar uma documentação",
            "eu queria pesquisar alguma coisa, abre meu navegador aí",
        )
        for texto in casos:
            with self.subTest(texto=texto):
                resultado = interpretar(texto)
                self.assertEqual(resultado["acao"], "abrir_app")
                self.assertEqual(resultado["parametros"]["nome"], "Google Chrome")

    def test_lista_de_aplicativos_sem_repetir_verbo(self):
        resultado = interpretar("abra chrome, depois spotify e depois vscode")
        self.assertEqual(resultado["tipo"], "comando_complexo")
        self.assertEqual(
            [etapa["parametros"]["nome"] for etapa in resultado["etapas"]],
            ["Google Chrome", "Spotify", "Visual Studio Code"],
        )

    def test_clima_com_tempo_relativo(self):
        for texto in (
            "qual o clima de São Paulo?",
            "como vai estar o clima amanhã em São Paulo?",
            "amanhã vai chover em São Paulo?",
        ):
            with self.subTest(texto=texto):
                resultado = interpretar(texto)
                self.assertEqual(resultado["acao"], "consultar_clima")
                self.assertEqual(resultado["parametros"]["local"], "são paulo")

    def test_agendamento_relativo_nao_bloqueia(self):
        resultado = interpretar("abra o spotify daqui a 10 minutos")
        self.assertEqual(resultado["acao"], "abrir_app")
        self.assertEqual(resultado["agendamento"]["atraso_segundos"], 600)

    def test_contexto_resolve_referencia(self):
        resultado = interpretar("fecha ele", contexto={"app_atual": "Visual Studio Code"})
        self.assertEqual(resultado["acao"], "fechar_janela")

    @patch("sistema_toke.resolvedor_ia._chamar_ollama")
    def test_resolvedor_ia_restringe_a_catalogo(self, chamar):
        chamar.return_value = json.dumps({
            "intencao": "abrir_app",
            "alvo": "navegador",
            "confianca": 0.93,
        })
        resultado = interpretar_com_ia("abra aquele editor")
        self.assertEqual(resultado["acao"], "abrir_app")
        self.assertEqual(resultado["parametros"]["nome"], "Google Chrome")


if __name__ == "__main__":
    unittest.main()
