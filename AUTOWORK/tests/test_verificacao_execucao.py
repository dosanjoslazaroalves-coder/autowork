import sys
import unittest
from unittest.mock import MagicMock, patch

if "pyautogui" not in sys.modules:
    try:
        import pyautogui
    except ImportError:
        mock_pyautogui = MagicMock()
        sys.modules["pyautogui"] = mock_pyautogui

from sistema_toke.executor import executar, registrar, REGISTRO_ACOES
from sistema_toke.verificador import JanelaInfo, CLASSES_DESKTOP, TITULOS_DESKTOP
from sistema_toke.parser import parse
from interpretador import interpretar
import comd_rapidos.atalhos
from comd_rapidos.atalhos import Janela


class TestVerificadorEstrutura(unittest.TestCase):

    def test_janela_info_dataclass(self):
        info = JanelaInfo(hwnd=12345, titulo="Google Chrome", classe="Chrome_WidgetWin_1", eh_desktop=False)
        self.assertEqual(info.hwnd, 12345)
        self.assertEqual(info.titulo, "Google Chrome")
        self.assertEqual(info.classe, "Chrome_WidgetWin_1")
        self.assertFalse(info.eh_desktop)
        self.assertIn("12345", str(info))

    def test_classes_desktop_reconhecidas(self):
        self.assertIn("Progman", CLASSES_DESKTOP)
        self.assertIn("WorkerW", CLASSES_DESKTOP)
        self.assertIn("Shell_TrayWnd", CLASSES_DESKTOP)


class TestExecutorVerificacao(unittest.TestCase):

    def setUp(self):
        self._backup_registro = dict(REGISTRO_ACOES)

    def tearDown(self):
        REGISTRO_ACOES.clear()
        REGISTRO_ACOES.update(self._backup_registro)

    def test_acao_com_sucesso_confirmado(self):
        registrar("acao_teste_ok", lambda: {
            "sucesso": True,
            "executado": True,
            "confirmado": True,
            "mensagem": "Fechada com sucesso.",
        })
        resultado = executar("acao_teste_ok")
        self.assertEqual(resultado["status"], "sucesso")
        self.assertTrue(resultado["confirmado"])
        self.assertTrue(resultado["executado"])

    def test_acao_com_sucesso_nao_confirmado(self):
        registrar("acao_teste_nao_conf", lambda: {
            "sucesso": True,
            "executado": True,
            "confirmado": False,
            "mensagem": "Enviado, mas sem confirmacao.",
        })
        resultado = executar("acao_teste_nao_conf")
        self.assertEqual(resultado["status"], "nao_confirmado")
        self.assertFalse(resultado["confirmado"])
        self.assertTrue(resultado["executado"])

    def test_acao_com_falha_explicita(self):
        registrar("acao_teste_falha", lambda: {
            "sucesso": False,
            "executado": False,
            "confirmado": False,
            "mensagem": "Nenhuma janela para fechar.",
        })
        resultado = executar("acao_teste_falha")
        self.assertEqual(resultado["status"], "falha")
        self.assertFalse(resultado["confirmado"])
        self.assertFalse(resultado["executado"])

    def test_acao_nao_registrada(self):
        resultado = executar("acao_inexistente_xyz_123")
        self.assertEqual(resultado["status"], "acao_nao_encontrada")
        self.assertFalse(resultado["executado"])
        self.assertFalse(resultado["confirmado"])

    def test_acao_legada_sem_retorno_estruturado(self):
        registrar("acao_legada", lambda: None)
        resultado = executar("acao_legada")
        self.assertEqual(resultado["status"], "contrato_invalido")
        self.assertFalse(resultado["executado"])
        self.assertFalse(resultado["confirmado"])

    def test_acao_que_lanca_excecao(self):
        def acao_com_erro():
            raise RuntimeError("Falha de teste critica")

        registrar("acao_com_erro", acao_com_erro)
        resultado = executar("acao_com_erro")
        self.assertEqual(resultado["status"], "erro_excecao")
        self.assertFalse(resultado["executado"])
        self.assertFalse(resultado["confirmado"])
        self.assertIn("Falha de teste critica", resultado["erro"])


class TestAtalhosFechamentoSemFalsoPositivo(unittest.TestCase):

    @patch("sistema_toke.verificador.capturar_janela_ativa")
    @patch("comd_rapidos.atalhos.pyautogui.hotkey")
    def test_fechar_janela_com_desktop_ativo_nao_envia_alt_f4(self, mock_hotkey, mock_capturar):
        from comd_rapidos.atalhos import Janela
        mock_capturar.return_value = JanelaInfo(hwnd=100, titulo="Program Manager", classe="Progman", eh_desktop=True)

        janela = Janela()
        resultado = janela.fechar_janela()

        mock_hotkey.assert_not_called()
        self.assertFalse(resultado["sucesso"])
        self.assertFalse(resultado["executado"])
        self.assertFalse(resultado["confirmado"])
        self.assertIn("Nenhuma janela de aplicativo", resultado["mensagem"])

    @patch("sistema_toke.verificador.verificar_fechamento_janela", return_value=True)
    @patch("sistema_toke.verificador.capturar_janela_ativa")
    @patch("comd_rapidos.atalhos.pyautogui.hotkey")
    def test_fechar_janela_valida_com_sucesso(self, mock_hotkey, mock_capturar, mock_verificar):
        from comd_rapidos.atalhos import Janela
        mock_capturar.return_value = JanelaInfo(hwnd=200, titulo="Bloco de Notas", classe="Notepad", eh_desktop=False)

        janela = Janela()
        resultado = janela.fechar_janela()

        mock_hotkey.assert_called_once_with("alt", "f4")
        self.assertTrue(resultado["sucesso"])
        self.assertTrue(resultado["executado"])
        self.assertTrue(resultado["confirmado"])


class TestParserPrevencaoFalsosPositivos(unittest.TestCase):

    def test_parser_rejeita_alvo_arbitrario_para_fechar(self):
        intencao = interpretar("fechar a melancia")
        self.assertNotEqual(intencao.get("tipo"), "comando")

    def test_parser_aceita_app_conhecido_com_verbo_fechar(self):
        intencao = interpretar("fechar o Chrome")
        self.assertEqual(intencao.get("tipo"), "comando")
        self.assertEqual(intencao.get("acao"), "fechar_janela")

    def test_parser_aceita_mostrar_area_de_trabalho(self):
        intencao = interpretar("mostrar a área de trabalho")
        self.assertEqual(intencao.get("tipo"), "comando")
        self.assertEqual(intencao.get("acao"), "mostrar_area_de_trabalho")

    def test_parser_aceita_minimizar_as_telas(self):
        intencao = interpretar("minimizar as telas")
        self.assertEqual(intencao.get("tipo"), "comando")
        self.assertEqual(intencao.get("acao"), "mostrar_area_de_trabalho")

    def test_parser_aceita_abrir_site_com_prefixos(self):
        for frase in ("abrir o site do youtube", "abrir site youtube", "abrir youtube", "abrir site github"):
            intencao = interpretar(frase)
            self.assertEqual(intencao.get("tipo"), "comando", f"Falha tipo em: {frase}")
            self.assertEqual(intencao.get("acao"), "abrir_site", f"Falha acao em: {frase}")
            self.assertIn("url", intencao.get("parametros", {}), f"Falha url em: {frase}")


class TestAbrirSiteVerificacao(unittest.TestCase):

    @patch("webbrowser.open", return_value=True)
    def test_abrir_site_retorna_confirmado(self, mock_browser):
        from comd_rapidos.abrir_site import abrir_site
        resultado = abrir_site("https://www.youtube.com")
        self.assertTrue(resultado["sucesso"])
        self.assertTrue(resultado["executado"])
        self.assertTrue(resultado["confirmado"])
        self.assertIn("sucesso", resultado["mensagem"])

    def test_abrir_site_rejeita_esquema_inseguro(self):
        from comd_rapidos.abrir_site import abrir_site
        resultado = abrir_site("file:///C:/Windows/System32/cmd.exe")
        self.assertFalse(resultado["sucesso"])
        self.assertFalse(resultado["executado"])
        self.assertFalse(resultado["confirmado"])
        self.assertIn("não permitida", resultado["mensagem"])


if __name__ == "__main__":
    unittest.main()
