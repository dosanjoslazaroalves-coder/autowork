"""Testes unitários e de integração para o módulo filtro.py e sua integração com o interpretador."""
from __future__ import annotations

import unittest
from filtro import filtrar, ResultadoFiltro
from interpretador import interpretar


class TestFiltroUnitario(unittest.TestCase):
    """Testa os métodos internos e comportamento isolado do filtro.py."""

    def test_cenario_1_frase_perfeitamente_reconhecida(self):
        """1. Frase perfeitamente reconhecida."""
        entrada = "abrir o chrome"
        res = filtrar(entrada)
        self.assertFalse(res.ambiguo)
        self.assertFalse(res.eh_pergunta)
        self.assertEqual(res.texto_filtrado.lower(), "abrir o chrome")
        self.assertGreaterEqual(res.confianca, 0.90)

    def test_cenario_2_frase_informal(self):
        """2. Frase informal com ruídos como 'aí'."""
        entrada = "abre aquele navegador aí"
        res = filtrar(entrada)
        self.assertFalse(res.ambiguo)
        self.assertEqual(res.texto_filtrado, "abre aquele navegador")
        self.assertTrue(res.alterado)

    def test_cenario_3_frase_com_palavras_extras(self):
        """3. Frase com palavras extras / preenchimento ('eu quero que você')."""
        entrada = "AUTOWORK eu quero que você abra o Google Chrome"
        res = filtrar(entrada)
        self.assertFalse(res.ambiguo)
        self.assertEqual(res.texto_filtrado, "abra o Google Chrome")

    def test_cenario_4_erro_speech_to_text(self):
        """4. Frase com erro de Speech-to-Text fonético ('minimiza as tela')."""
        entrada = "AUTOWORK minimiza as tela"
        res = filtrar(entrada)
        self.assertFalse(res.ambiguo)
        self.assertEqual(res.texto_filtrado, "minimizar as telas")

    def test_cenario_5_frase_incompleta(self):
        """5. Frase incompleta (verbo sem alvo)."""
        entrada = "abrir"
        res = filtrar(entrada)
        self.assertTrue(res.ambiguo)
        self.assertLessEqual(res.confianca, 0.50)

    def test_cenario_6_frase_ambigua_ruido_severo(self):
        """6. Frase ambígua ou desconexa de transcrição corrompida."""
        entrada = "AUTOWORK eu cira tá coisa mais não conseguir cria esse work abrir navegador"
        res = filtrar(entrada)
        self.assertTrue(res.ambiguo)
        self.assertLessEqual(res.confianca, 0.35)

    def test_cenario_7_pergunta_sobre_comando(self):
        """7. Pergunta sobre como executar um comando."""
        entrada = "como eu abro o Chrome?"
        res = filtrar(entrada)
        self.assertTrue(res.eh_pergunta)
        self.assertIn("como", res.texto_filtrado.lower())

    def test_cenario_8_conversa_pergunta_capacidade(self):
        """8. Pergunta sobre capacidades ou conversa."""
        entrada = "você consegue abrir aplicativos?"
        res = filtrar(entrada)
        self.assertTrue(res.eh_pergunta)

    def test_cenario_9_comando_inexistente(self):
        """9. Frase com comando inexistente/arbitrário."""
        entrada = "formate meu computador imediatamente"
        res = filtrar(entrada)
        self.assertFalse(res.ambiguo)
        self.assertIn("formate", res.texto_filtrado.lower())

    def test_cenario_10_app_com_erro_transcricao(self):
        """10. Nome de aplicativo com erro de transcrição de STT ('bloqui de notas')."""
        entrada = "AUTOWORK abre o bloqui de notas"
        res = filtrar(entrada)
        self.assertFalse(res.ambiguo)
        self.assertEqual(res.texto_filtrado, "abre o bloco de notas")


class TestIntegracaoFiltroInterpretador(unittest.TestCase):
    """Testa o fluxo integrado completo: filtro → interpretador → catálogo."""

    def _executar_e_registrar(self, entrada: str) -> dict:
        filtro_res = filtrar(entrada)
        interp_res = interpretar(filtro_res)
        return {
            "entrada": entrada,
            "filtro": filtro_res.texto_filtrado,
            "tipo": interp_res.get("tipo"),
            "intencao": interp_res.get("intencao"),
            "acao": interp_res.get("acao"),
            "parametros": interp_res.get("parametros"),
            "confianca": interp_res.get("confianca"),
        }

    def test_integracao_comando_com_preenchimento(self):
        dados = self._executar_e_registrar("AUTOWORK eu quero que você abra o Google Chrome")
        self.assertEqual(dados["tipo"], "comando")
        self.assertEqual(dados["acao"], "abrir_app")
        self.assertEqual(dados["parametros"]["nome"], "Google Chrome")

    def test_integracao_pergunta_nao_vira_comando(self):
        dados = self._executar_e_registrar("AUTOWORK pode abrir o navegador?")
        self.assertEqual(dados["tipo"], "comando")
        self.assertEqual(dados["acao"], "abrir_app")

    def test_integracao_pedido_natural_preciso_que_voce(self):
        dados = self._executar_e_registrar("AUTOWORK eu preciso que você abra o Codex")
        self.assertEqual(dados["tipo"], "comando")
        self.assertEqual(dados["acao"], "abrir_app")
        self.assertEqual(dados["parametros"]["nome"], "Codex")

    def test_integracao_correcao_stt_bloco_notas(self):
        dados = self._executar_e_registrar("AUTOWORK abre o bloqui de notas")
        self.assertEqual(dados["tipo"], "comando")
        self.assertEqual(dados["acao"], "abrir_app")
        self.assertEqual(dados["parametros"]["nome"], "Bloco de notas")

    def test_integracao_correcao_stt_area_trabalho(self):
        dados = self._executar_e_registrar("AUTOWORK minimiza as tela")
        self.assertEqual(dados["tipo"], "comando")
        self.assertEqual(dados["acao"], "mostrar_area_de_trabalho")

    def test_integracao_ruido_incoerente_rejeitado(self):
        dados = self._executar_e_registrar("AUTOWORK eu cira tá coisa mais não conseguir cria esse work abrir navegador")
        self.assertEqual(dados["tipo"], "desconhecido")
        self.assertIsNone(dados["acao"])

    def test_integracao_variacao_informal(self):
        dados = self._executar_e_registrar("abre aquele navegador aí")
        self.assertEqual(dados["tipo"], "comando")
        self.assertEqual(dados["acao"], "abrir_app")
        self.assertEqual(dados["parametros"]["nome"], "Google Chrome")

    def test_integracao_comando_pode_fechar(self):
        dados = self._executar_e_registrar("pode fechar o Chrome")
        self.assertEqual(dados["tipo"], "comando")
        self.assertEqual(dados["acao"], "fechar_janela")

    def test_integracao_seguranca_comando_inexistente(self):
        dados = self._executar_e_registrar("formate meu computador")
        # NUNCA pode ser comando executado
        self.assertNotEqual(dados["tipo"], "comando")


if __name__ == "__main__":
    unittest.main()
