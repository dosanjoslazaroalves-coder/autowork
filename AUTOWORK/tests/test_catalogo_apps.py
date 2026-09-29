import unittest

from interpretador import interpretar
from sistema_toke.catalogo.catalogo_app import CATALOGO_APPS, resolver_app, resolver_nome_app
from sistema_toke.parser import parse
from sistema_toke.resolvedor import resolver


class TestCatalogoApps(unittest.TestCase):
    def test_catalogo_estruturado_tem_metadados(self):
        vscode = resolver_app("VS Code")
        self.assertIsNotNone(vscode)
        self.assertEqual(vscode.id, "vscode")
        self.assertEqual(vscode.categoria, "desenvolvimento")
        self.assertEqual(vscode.comando, "code")
        self.assertGreaterEqual(len(CATALOGO_APPS), 50)

    def test_aliases_tecnicos(self):
        esperados = {
            "vscode": "Visual Studio Code",
            "visual studio code": "Visual Studio Code",
            "cursor editor": "Cursor",
            "codex": "Codex",
            "power shell": "PowerShell",
            "gitbash": "Git Bash",
            "mongo compass": "MongoDB Compass",
            "node js": "Node.js",
        }
        for alias, esperado in esperados.items():
            with self.subTest(alias=alias):
                self.assertEqual(resolver_nome_app(alias), esperado)

    def test_aplicativo_inexistente_nao_resolve(self):
        self.assertIsNone(resolver_app("aplicativo fantasma xyz"))
        intencao = interpretar("abrir aplicativo fantasma xyz")
        self.assertNotEqual(intencao.get("acao"), "abrir_app")

    def test_github_site_e_github_desktop_sao_diferentes(self):
        site = resolver(parse("abrir github"))
        app = resolver(parse("abrir github desktop"))
        self.assertEqual(site["acao"], "abrir_site")
        self.assertEqual(app["acao"], "abrir_app")
        self.assertEqual(app["parametros"]["nome"], "GitHub Desktop")

    def test_marcador_site_tem_prioridade_sobre_alias_de_app(self):
        site = resolver(parse("abrir site docker"))
        self.assertEqual(site["acao"], "abrir_site")

    def test_ferramentas_tecnicas_resolvem_como_apps(self):
        for frase, nome in (
            ("abrir cursor", "Cursor"),
            ("abrir codex", "Codex"),
            ("abrir terminal", "Windows Terminal"),
            ("abrir docker", "Docker Desktop"),
            ("abrir ollama", "Ollama"),
        ):
            with self.subTest(frase=frase):
                intencao = interpretar(frase)
                self.assertEqual(intencao["tipo"], "comando")
                self.assertEqual(intencao["acao"], "abrir_app")
                self.assertEqual(intencao["parametros"]["nome"], nome)


if __name__ == "__main__":
    unittest.main()
