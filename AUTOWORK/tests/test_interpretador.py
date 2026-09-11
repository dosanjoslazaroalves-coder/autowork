"""Testes unitários do interpretador (roteador central de intenções)."""

import unittest

from interpretador import interpretar


class TestRoteamento(unittest.TestCase):

    def _tipo_acao(self, texto):
        intencao = interpretar(texto)
        self.assertIsNotNone(intencao, texto)
        return intencao.get("tipo"), intencao.get("acao")

    def test_estrutura_consistente(self):
        for texto in ("abrir o chrome", "que horas são", "conte uma piada"):
            intencao = interpretar(texto)
            for chave in ("tipo", "acao", "parametros", "confianca", "fala", "falar"):
                self.assertIn(chave, intencao, texto)

    def test_comandos(self):
        casos = {
            "abrir o Chrome": "abrir_app",
            "abra o bloco de notas": "abrir_app",
            "abrir nova aba": "nova_aba",
            "por favor abra o chrome": "abrir_app",
            "fechar a janela": "fechar_janela",
        }
        for texto, acao in casos.items():
            tipo, obtido = self._tipo_acao(texto)
            self.assertEqual(tipo, "comando", texto)
            self.assertEqual(obtido, acao, texto)

    def test_comando_resolvido_com_parametros(self):
        intencao = interpretar("abrir o Chrome")
        self.assertEqual(intencao["parametros"], {"nome": "Google Chrome"})

    def test_pergunta_sobre_comando_vai_para_conversa(self):
        tipo, acao = self._tipo_acao("você sabe como abrir o chrome?")
        self.assertEqual(tipo, "conversa")
        self.assertEqual(acao, "chat")

    def test_hora(self):
        casos = {
            "que horas são?": "consultar_horario",
            "qual é o horário agora?": "consultar_horario",
            "me diga a hora": "consultar_horario",
            "que dia é hoje?": "consultar_data",
            "qual a diferença de horário entre Brasil e Japão?": "diferenca_horario",
            "converta 10 horas do Brasil para o Japão": "converter_horario",
        }
        for texto, acao in casos.items():
            tipo, obtido = self._tipo_acao(texto)
            self.assertEqual(tipo, "hora", texto)
            self.assertEqual(obtido, acao, texto)

    def test_hora_com_local(self):
        intencao = interpretar("que horas são em Tóquio?")
        self.assertEqual(intencao["tipo"], "hora")
        self.assertEqual(intencao["parametros"]["local"], "tóquio")

    def test_clima(self):
        casos = (
            "como está o clima?",
            "qual a temperatura em São Paulo?",
            "vai chover hoje em Recife?",
        )
        for texto in casos:
            tipo, acao = self._tipo_acao(texto)
            self.assertEqual(tipo, "clima", texto)
            self.assertEqual(acao, "consultar_clima", texto)

    def test_clima_extrai_local_e_data(self):
        intencao = interpretar("vai chover amanhã em Recife?")
        self.assertEqual(intencao["parametros"]["local"], "recife")
        self.assertEqual(intencao["parametros"]["data"], "amanhã")

    def test_localizacao(self):
        casos = (
            "onde estou?",
            "qual é a minha localização?",
            "em que cidade eu estou?",
        )
        for texto in casos:
            tipo, acao = self._tipo_acao(texto)
            self.assertEqual(tipo, "informacao", texto)
            self.assertEqual(acao, "consultar_localizacao", texto)

    def test_apresentacao(self):
        casos = (
            "se apresente",
            "se apresentar",
            "o que é o AUTOWORK?",
            "me explique o projeto",
            "fale sobre o autowork",
        )
        for texto in casos:
            tipo, acao = self._tipo_acao(texto)
            self.assertEqual(tipo, "apresentacao", texto)
            self.assertEqual(acao, "apresentar", texto)

    def test_conversa(self):
        casos = (
            "explique inteligência artificial para mim",
            "conte uma piada",
            "qual o sentido da vida",
            "quem é você?",
            "o que você consegue fazer?",
            "o que você pode fazer?",
        )
        for texto in casos:
            tipo, acao = self._tipo_acao(texto)
            self.assertEqual(tipo, "conversa", texto)
            self.assertEqual(acao, "chat", texto)

    def test_conversa_encaminha_texto_original(self):
        texto = "explique inteligência artificial para mim"
        intencao = interpretar(texto)
        self.assertEqual(intencao["parametros"]["texto_original"], texto)

    def test_desconhecido(self):
        intencao = interpretar("   ")
        self.assertEqual(intencao["tipo"], "desconhecido")

    def test_comando_nao_deve_ser_falado(self):
        intencao = interpretar("abrir o Chrome")
        self.assertFalse(intencao.get("falar"))

    def test_respostas_informativas_devem_ser_faladas(self):
        casos = (
            "que horas são?",
            "como está o clima?",
            "onde estou?",
            "se apresente",
            "conte uma piada",
        )
        for texto in casos:
            intencao = interpretar(texto)
            self.assertTrue(intencao.get("falar"), texto)


if __name__ == "__main__":
    unittest.main()
