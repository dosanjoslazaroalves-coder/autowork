"""Testes unitários e de integração para o Resolvedor IA Local (Ollama)."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from interpretador import interpretar
from sistema_toke.resolvedor_ia import (
    _chamar_ollama,
    _extrair_json,
    _validar_intencao,
    interpretar_com_ia,
)


class TestValidacaoIntencao(unittest.TestCase):
    """Testa a validação estrita em Python contra os catálogos oficiais."""

    def test_atalho_oficial(self):
        dados = {"intencao": "mostrar_area_de_trabalho"}
        res = _validar_intencao(dados)
        self.assertIsNotNone(res)
        self.assertEqual(res["tipo"], "comando")
        self.assertEqual(res["acao"], "mostrar_area_de_trabalho")

    def test_atalho_com_maiusculas_e_alias(self):
        # Exemplo fornecido no enunciado: "MOSTRAR_AREA_TRABALHO"
        dados = {"intencao": "MOSTRAR_AREA_TRABALHO"}
        res = _validar_intencao(dados)
        self.assertIsNotNone(res)
        self.assertEqual(res["acao"], "mostrar_area_de_trabalho")

    def test_outros_atalhos(self):
        casos = [
            ("fechar_janela", "fechar_janela"),
            ("FECHAR_JANELA", "fechar_janela"),
            ("alternar_janelas", "alternar_janelas"),
            ("TROCAR_JANELA", "alternar_janelas"),
            ("bloquear_tela", "bloquear_tela"),
            ("minimizar_tudo", "mostrar_area_de_trabalho"),
            ("restaurar_ou_minimizar_janela", "restaurar_ou_minimizar_janela"),
        ]
        for entrada, esperado in casos:
            res = _validar_intencao({"intencao": entrada})
            self.assertIsNotNone(res, f"Falha para {entrada}")
            self.assertEqual(res["acao"], esperado)

    def test_abrir_app_valido(self):
        dados = {"intencao": "abrir_app", "alvo": "chrome"}
        res = _validar_intencao(dados)
        self.assertIsNotNone(res)
        self.assertEqual(res["tipo"], "comando")
        self.assertEqual(res["acao"], "abrir_app")
        self.assertEqual(res["parametros"], {"nome": "Google Chrome"})

    def test_abrir_app_alias_navegador(self):
        dados = {"intencao": "abrir_app", "alvo": "navegador"}
        res = _validar_intencao(dados)
        self.assertIsNotNone(res)
        self.assertEqual(res["parametros"], {"nome": "Google Chrome"})

    def test_abrir_app_inexistente_rejeita(self):
        # Aplicativo inexistente NUNCA pode ser executado
        dados = {"intencao": "abrir_app", "alvo": "app_fantasma_xyz"}
        res = _validar_intencao(dados)
        self.assertIsNone(res)

    def test_abrir_site_valido(self):
        dados = {"intencao": "abrir_site", "alvo": "youtube"}
        res = _validar_intencao(dados)
        self.assertIsNotNone(res)
        self.assertEqual(res["tipo"], "comando")
        self.assertEqual(res["acao"], "abrir_site")
        self.assertEqual(res["parametros"], {"url": "https://www.youtube.com"})

    def test_abrir_site_inexistente_rejeita(self):
        dados = {"intencao": "abrir_site", "alvo": "site_desconhecido_123"}
        res = _validar_intencao(dados)
        self.assertIsNone(res)

    def test_seguranca_rejeita_intencao_inexistente(self):
        # A IA nunca pode inventar comandos fora do catálogo
        comandos_invalidos = [
            {"intencao": "FORMATAR_COMPUTADOR"},
            {"intencao": "DELETAR_ARQUIVOS"},
            {"intencao": "EXECUTE_CMD"},
            {"intencao": "DESCONHECIDO"},
            {"intencao": "desconhecido"},
            {"intencao": ""},
            {},
        ]
        for caso in comandos_invalidos:
            self.assertIsNone(
                _validar_intencao(caso),
                f"Deveria ter rejeitado: {caso}",
            )


class TestExtrairJson(unittest.TestCase):
    """Testa o extrator tolerante de JSON."""

    def test_json_puro(self):
        res = _extrair_json('{"intencao": "fechar_janela"}')
        self.assertEqual(res, {"intencao": "fechar_janela"})

    def test_json_com_markdown(self):
        bloco = '```json\n{"intencao": "mostrar_area_de_trabalho"}\n```'
        res = _extrair_json(bloco)
        self.assertEqual(res, {"intencao": "mostrar_area_de_trabalho"})

    def test_json_com_texto_em_volta(self):
        texto = 'Aqui está o resultado: {"intencao": "alternar_janelas"} espero ter ajudado.'
        res = _extrair_json(texto)
        self.assertEqual(res, {"intencao": "alternar_janelas"})

    def test_texto_sem_json(self):
        self.assertIsNone(_extrair_json("Não consegui entender a frase."))
        self.assertIsNone(_extrair_json(""))


class TestResilienciaFalhasOllama(unittest.TestCase):
    """Testa se o AUTOWORK continua operando quando o Ollama falha."""

    @patch("requests.post")
    def test_ollama_desligado_connection_error(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        res = interpretar_com_ia("esconde as janelas")
        self.assertIsNone(res)

    @patch("requests.post")
    def test_ollama_timeout(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Read timed out")

        res = interpretar_com_ia("esconde as janelas")
        self.assertIsNone(res)

    @patch("requests.post")
    def test_ollama_http_error(self, mock_post):
        import requests
        resp_mock = MagicMock()
        resp_mock.status_code = 500
        mock_post.side_effect = requests.exceptions.HTTPError(response=resp_mock)

        res = interpretar_com_ia("esconde as janelas")
        self.assertIsNone(res)

    @patch("requests.post")
    def test_resposta_nao_json(self, mock_post):
        resp_mock = MagicMock()
        resp_mock.status_code = 200
        resp_mock.json.return_value = {"response": "desculpe, não sei o que fazer"}
        mock_post.return_value = resp_mock

        res = interpretar_com_ia("esconde as janelas")
        self.assertIsNone(res)


class TestIntegracaoPipelineComandos(unittest.TestCase):
    """Testa o pipeline completo através de interpretador.interpretar()."""

    def test_comandos_antigos_continuam_deterministicos(self):
        # Esses comandos são resolvidos pelo sistema determinístico original
        casos = {
            "mostrar a área de trabalho": "mostrar_area_de_trabalho",
            "abre o Google Chrome": "abrir_app",
            "abre o navegador": "abrir_app",
        }
        for frase, acao_esperada in casos.items():
            res = interpretar(frase)
            self.assertIsNotNone(res)
            self.assertEqual(res.get("tipo"), "comando", f"Falha para {frase}")
            self.assertEqual(res.get("acao"), acao_esperada)

    def test_frases_nao_comando_vao_para_conversa(self):
        # Perguntas e conversas NUNCA devem virar comandos
        perguntas = [
            "o que é inteligência artificial?",
            "o que significa minimizar uma janela?",
            "você sabe como abrir o chrome?",
            "quem é você?",
            "conte uma piada",
        ]
        for p in perguntas:
            res = interpretar(p)
            self.assertEqual(res.get("tipo"), "conversa", f"Falha para {p}")
            self.assertEqual(res.get("acao"), "chat")

    def test_variacoes_semanticas_com_ia_ou_mock(self):
        # Testa a integração com fallback IA
        variacoes = [
            "esconde as janelas",
            "minimize todas as janelas",
            "quero ver a área de trabalho",
            "feche essa janela",
            "troque de janela",
        ]
        for frase in variacoes:
            res = interpretar(frase)
            self.assertIsNotNone(res)
            # Se o Ollama estiver ativo, deve ser comando; se inativo, fallback para conversa
            self.assertIn(res.get("tipo"), ("comando", "conversa"))
            if res.get("tipo") == "comando":
                self.assertIn(
                    res.get("acao"),
                    ("mostrar_area_de_trabalho", "fechar_janela", "alternar_janelas", "restaurar_ou_minimizar_janela"),
                )


if __name__ == "__main__":
    unittest.main()
