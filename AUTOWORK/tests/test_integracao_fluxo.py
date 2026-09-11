"""
Teste de integração do fluxo completo AUTOWORK:

    fala.py → interpretador.py → dispatcher → módulo → resultado → terminal + TTS

A voz (fala.falar) é capturada em uma lista e o executor de apps/sites é
simulado, para não abrir janelas reais durante o teste. Clima, localização,
apresentação e conversa usam os módulos reais (precisam de internet /
Ollama / chave da API).

Política de voz validada aqui:
    - comando de automação com sucesso: NÃO fala;
    - comando com falha: fala apenas um aviso curto;
    - conversa / informação / erro: fala exatamente UMA vez.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fala


import audio.tts
import sistema_toke.executor

def _limpar_modulo_fala():
    fala.falas_reproduzidas = []
    audio.tts.falar = lambda texto: fala.falas_reproduzidas.append(texto)
    sistema_toke.executor.executar = lambda acao, **parametros: {
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

    # Teste 1: comando executa, aparece no terminal e fala a mensagem de sucesso
    def test_comando_abrir_chrome_nao_fala(self):
        resultado, falas = self._processar("abrir o Chrome")
        self.assertEqual(resultado["status"], "sucesso")
        self.assertEqual(resultado["acao"], "abrir_app")
        self.assertEqual(resultado["parametros"], {"nome": "Google Chrome"})
        self.assertEqual(falas, ["Comando 'abrir_app' executado (simulado)."])

    # Comando com falha: fala a mensagem de erro retornada pelo executor
    def test_comando_falho_fala_aviso_curto(self):
        original = sistema_toke.executor.executar
        sistema_toke.executor.executar = lambda acao, **p: {
            "status": "falha", "acao": acao, "mensagem": "boom", "erro": "FileNotFoundError..."
        }
        try:
            resultado, falas = self._processar("abrir o Chrome")
        finally:
            sistema_toke.executor.executar = original
        self.assertEqual(resultado["status"], "falha")
        self.assertEqual(falas, ["boom"])

    # Teste 2: hora no terminal + voz (uma vez).
    def test_hora(self):
        resultado, falas = self._processar("Que horas são?")
        self.assertEqual(resultado["status"], "sucesso")
        self.assertEqual(resultado["acao"], "consultar_horario")
        self.assertEqual(resultado["tipo"], "informacao")
        self.assertTrue(resultado["mensagem"])
        self.assertEqual(falas, [resultado["mensagem"]])

    # Teste 3: clima no terminal + voz (uma vez).
    def test_clima(self):
        resultado, falas = self._processar("Como está o clima em São Paulo?")
        self.assertEqual(resultado["status"], "sucesso")
        self.assertEqual(resultado["acao"], "consultar_clima")
        self.assertEqual(resultado["tipo"], "informacao")
        self.assertTrue(resultado["mensagem"])
        self.assertEqual(falas, [resultado["mensagem"]])

    # Localização: no terminal + voz (uma vez).
    def test_localizacao(self):
        resultado, falas = self._processar("onde estou?")
        self.assertEqual(resultado["acao"], "consultar_localizacao")
        self.assertEqual(resultado["status"], "sucesso")
        self.assertEqual(resultado["tipo"], "informacao")
        self.assertIn("Você está em", resultado["mensagem"])
        self.assertEqual(falas, [resultado["mensagem"]])

    # Teste 4: apresentação no terminal + voz (uma vez).
    def test_apresentacao(self):
        resultado, falas = self._processar("se apresente")
        self.assertEqual(resultado["status"], "sucesso")
        self.assertEqual(resultado["acao"], "apresentar")
        self.assertEqual(resultado["tipo"], "informacao")
        self.assertTrue(resultado["mensagem"])
        self.assertEqual(falas, [resultado["mensagem"]])

    # Teste 5: "Quem é você?" vai para o chatbot, terminal + voz.
    def test_conversa_chatbot_quem_e_voce(self):
        resultado, falas = self._processar("Quem é você?")
        self.assertEqual(resultado["acao"], "chat")
        self.assertTrue(resultado.get("mensagem"))
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

    # Teste 6: nenhuma resposta é reproduzida duas vezes.
    def test_nenhuma_fala_duplicada(self):
        casos = (
            "abrir o Chrome",
            "Que horas são?",
            "Como está o clima em São Paulo?",
            "onde estou?",
            "se apresente",
            "conte uma piada",
        )
        for texto in casos:
            _, falas = self._processar(texto)
            duplicadas = set(f for f in falas if falas.count(f) > 1)
            self.assertFalse(duplicadas, "%s falou duas vezes: %s" % (texto, duplicadas))
            self.assertLessEqual(len(falas), 1, "%s falou %d vezes" % (texto, len(falas)))


if __name__ == "__main__":
    unittest.main()
