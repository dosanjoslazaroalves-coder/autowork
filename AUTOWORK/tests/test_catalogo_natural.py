"""Frases naturais em pt-BR contra o catálogo de verbos/atalhos."""
import unittest

from interpretador import interpretar
from sistema_toke.parser import parse
from sistema_toke.resolvedor import resolver


def _acao(texto: str) -> str | None:
    intencao = interpretar(texto)
    if not intencao:
        return None
    return intencao.get("acao") if intencao.get("tipo") == "comando" else None


class TestFrasesNaturaisAbrir(unittest.TestCase):
    def test_variacoes_abrir_navegador(self):
        frases = (
            "abrir o navegador",
            "abra o navegador",
            "pode abrir o navegador",
            "quero abrir o navegador",
            "abre o navegador aí",
            "inicie o navegador",
            "executa o navegador",
            "Autowork, abre o Chrome",
        )
        for frase in frases:
            with self.subTest(frase=frase):
                self.assertEqual(_acao(frase), "abrir_app", frase)

    def test_abrir_spotify(self):
        self.assertEqual(_acao("pode abrir o Spotify"), "abrir_app")
        self.assertEqual(interpretar("pode abrir o Spotify")["parametros"]["nome"], "Spotify")

    def test_abrir_pasta_usa_explorador(self):
        self.assertEqual(_acao("abrir pasta"), "abrir_app")
        self.assertEqual(interpretar("abrir pasta")["parametros"]["nome"], "Explorador de Arquivos")


class TestFrasesNaturaisNavegador(unittest.TestCase):
    def test_nova_aba(self):
        for frase in ("abre uma nova aba", "abrir nova aba", "abrir nova guia"):
            with self.subTest(frase=frase):
                self.assertEqual(_acao(frase), "nova_aba", frase)

    def test_fechar_aba(self):
        self.assertEqual(_acao("fecha essa aba"), "fechar_aba")

    def test_voltar_pagina(self):
        self.assertEqual(_acao("volta pra página anterior"), "voltar_pagina")
        self.assertEqual(_acao("voltar pagina"), "voltar_pagina")

    def test_atualizar(self):
        self.assertEqual(_acao("recarrega essa página"), "atualizar_pagina")
        self.assertEqual(_acao("atualiza a página"), "atualizar_pagina")

    def test_devtools_e_inspetor(self):
        frases = (
            "inspecionar a página",
            "inspecione essa página",
            "abrir o inspetor",
            "abre o inspetor",
            "ver os elementos da página",
            "quero ver os elementos dessa página",
            "abrir as ferramentas do desenvolvedor",
            "abre as ferramentas do desenvolvedor",
            "abrir o DevTools",
        )
        for frase in frases:
            with self.subTest(frase=frase):
                self.assertEqual(_acao(frase), "devtools", frase)

    def test_codigo_fonte(self):
        self.assertEqual(_acao("mostra o código dessa página"), "codigo_fonte")

    def test_console(self):
        self.assertEqual(_acao("abrir o console"), "console")

    def test_historico_downloads_favoritos(self):
        self.assertEqual(_acao("abrir o histórico"), "historico")
        self.assertEqual(_acao("abrir downloads"), "downloads")
        self.assertEqual(_acao("abrir os favoritos"), "favoritos")

    def test_buscar_na_pagina(self):
        self.assertEqual(_acao("localizar na página"), "buscar_na_pagina")

    def test_tela_cheia(self):
        self.assertEqual(_acao("abrir tela cheia"), "tela_cheia")


class TestFrasesNaturaisJanelaSistema(unittest.TestCase):
    def test_fechar_janela(self):
        self.assertEqual(_acao("fecha essa janela"), "fechar_janela")
        self.assertEqual(_acao("fechar o Chrome"), "fechar_janela")

    def test_alternar(self):
        self.assertEqual(_acao("troca de janela"), "alternar_janelas")
        self.assertEqual(_acao("trocar de janela"), "alternar_janelas")

    def test_minimizar_maximizar(self):
        self.assertEqual(_acao("minimiza essa janela"), "restaurar_ou_minimizar_janela")
        self.assertEqual(_acao("maximiza essa janela"), "maximizar_janela")

    def test_bloquear(self):
        self.assertEqual(_acao("bloqueia a tela"), "bloquear_tela")
        self.assertEqual(_acao("trava o computador"), "bloquear_tela")

    def test_nao_executa_desligar(self):
        intencao = interpretar("desligar o computador")
        self.assertNotEqual(intencao.get("acao"), "bloquear_tela")
        self.assertNotEqual(intencao.get("tipo"), "comando")

    def test_nao_fecha_alvo_arbitrario(self):
        self.assertIsNone(_acao("fechar a melancia"))

    def test_pedido_interrogativo_vira_comando(self):
        intencao = interpretar("pode abrir o Codex?")
        self.assertEqual(intencao.get("tipo"), "comando")
        self.assertEqual(intencao.get("acao"), "abrir_app")
        self.assertEqual(intencao.get("parametros", {}).get("nome"), "Codex")

    def test_pergunta_sobre_comando_continua_conversa(self):
        intencao = interpretar("você sabe como abrir o Chrome?")
        self.assertEqual(intencao.get("tipo"), "conversa")

    def test_parser_e_resolvedor_devtools(self):
        parsed = parse("abrir o inspetor")
        self.assertIsNotNone(parsed)
        resolvido = resolver(parsed)
        self.assertEqual(resolvido["acao"], "devtools")


if __name__ == "__main__":
    unittest.main()
