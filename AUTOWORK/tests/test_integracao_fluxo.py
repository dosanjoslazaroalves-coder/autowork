"""
Teste de integração do fluxo completo AUTOWORK:

    fala.py → interpretador.py → módulo apropriado → resposta → terminal + voz

A voz (fala.falar) é capturada em uma lista e o executor de apps/sites é
simulado, para não abrir janelas reais durante o teste. Clima, apresentação
e conversa usam os módulos reais (precisam de internet / Ollama / chave).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fala


def _limpar_modulo_fala():
    fala.falas_reproduzidas = []
    fala.falar = lambda texto: fala.falas_reproduzidas.append(texto)
    fala.executar = lambda acao, **parametros: {
        "status": "sucesso",
        "acao": acao,
        "mensagem": "Comando '%s' executado (simulado)." % acao,
        "parametros": dict(parametros),
    }


_limpar_modulo_fala()


class TestIntegracaoFluxo(unittest.TestCase):

    def _processar(self, texto):
        fala.falas_reproduzidas.clear()
        resultado = fala.processar_comando(texto)
        return resultado, list(fala.falas_reproduzidas)

    def test_comando_abrir_chrome(self):
        resultado, falas = self._processar("abrir o Chrome")
        self.assertEqual(resultado["status"], "sucesso")
        self.assertEqual(resultado["acao"], "abrir_app")
        self.assertEqual(resultado["parametros"], {"nome": "Google Chrome"})
        self.assertTrue(falas, "resposta do comando não foi enviada para a voz")

    def test_hora(self):
        resultado, falas = self._processar("Que horas são?")
        self.assertEqual(resultado["status"], "sucesso")
        self.assertEqual(resultado["acao"], "consultar_horario")
        self.assertTrue(resultado["mensagem"])
        self.assertEqual(falas, [resultado["mensagem"]])

    def test_clima(self):
        resultado, falas = self._processar("Como está o clima em São Paulo?")
        self.assertEqual(resultado["status"], "sucesso")
        self.assertEqual(resultado["acao"], "consultar_clima")
        self.assertTrue(resultado["mensagem"])
        self.assertEqual(falas, [resultado["mensagem"]])

    def test_apresentacao(self):
        resultado, falas = self._processar("O que é o AUTOWORK?")
        self.assertEqual(resultado["status"], "sucesso")
        self.assertEqual(resultado["acao"], "apresentar")
        self.assertTrue(resultado["mensagem"])
        self.assertEqual(falas, [resultado["mensagem"]])

    def test_conversa_chatbot(self):
        resultado, falas = self._processar("Explique inteligência artificial para mim.")
        self.assertEqual(resultado["acao"], "chat")
        # Sem rede/chave o chatbot responde com a mensagem de falha dele;
        # o fluxo (terminal + voz) precisa funcionar dos dois jeitos.
        self.assertTrue(resultado.get("mensagem"))
        self.assertEqual(falas, [resultado["mensagem"]])

    def test_desconhecido(self):
        resultado, _ = self._processar("   ")
        self.assertEqual(resultado["status"], "nao_reconhecido")


if __name__ == "__main__":
    unittest.main()
