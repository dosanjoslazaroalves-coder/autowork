import time
import unittest
from unittest.mock import MagicMock, patch

from interpretador import interpretar
from sist_comd_complex.executor_complexo import ExecutorComplexo
from sist_comd_complex.interpretador_complex import (
    detectar_comando_complexo,
    interpretar_comando_complexo,
)


class TestInterpretadorComplexo(unittest.TestCase):
    def test_comando_simples_nao_e_complexo(self):
        self.assertFalse(detectar_comando_complexo("Abra o navegador Google Chrome."))
        intencao = interpretar("Abra o Chrome.")
        self.assertEqual(intencao["tipo"], "comando")

    def test_comando_complexo_com_duas_etapas(self):
        plano = interpretar("Abra o Chrome, depois abra o bloco de notas.")
        self.assertEqual(plano["tipo"], "comando_complexo")
        self.assertEqual(len(plano["etapas"]), 2)
        self.assertEqual(plano["etapas"][0]["acao"], "abrir_aplicativo")
        self.assertEqual(plano["etapas"][1]["dependencias"], [])

    def test_comando_complexo_com_cinco_etapas(self):
        plano = interpretar_comando_complexo(
            "Abra o Chrome, depois abra o YouTube, em seguida abra o bloco de notas, "
            "depois abra o GitHub e por último minimize todas as janelas."
        )
        self.assertEqual(len(plano["etapas"]), 5)
        self.assertEqual(plano["etapas"][1]["acao"], "abrir_site")
        self.assertEqual(plano["etapas"][3]["acao"], "abrir_site")
        self.assertEqual(plano["etapas"][-1]["acao"], "mostrar_area_de_trabalho")

    def test_conector_depois(self):
        self.assertTrue(detectar_comando_complexo("Abra o Chrome depois abra o YouTube"))

    def test_conector_em_seguida(self):
        self.assertTrue(detectar_comando_complexo("Abra o Chrome em seguida abra o YouTube"))

    def test_multiplas_acoes_com_e_antes_de_verbo(self):
        plano = interpretar_comando_complexo("Abra o Chrome e abra o YouTube")
        self.assertEqual([e["acao"] for e in plano["etapas"]], ["abrir_aplicativo", "abrir_site"])

    def test_comando_real_com_chrome_e_vs_code_entrega_duas_etapas(self):
        plano = interpretar("Abra o Chrome e abra o VS Code.")
        self.assertEqual(plano["tipo"], "comando_complexo")
        self.assertEqual(
            [etapa["parametros"]["nome"] for etapa in plano["etapas"]],
            ["Google Chrome", "Visual Studio Code"],
        )

    def test_lista_nominal_com_tres_aplicativos(self):
        plano = interpretar("Abra o Chrome, o VS Code e o Bloco de Notas.")
        self.assertEqual(
            [etapa["parametros"]["nome"] for etapa in plano["etapas"]],
            ["Google Chrome", "Visual Studio Code", "Bloco de notas"],
        )

    def test_parametro_ausente(self):
        plano = interpretar_comando_complexo("Abra, depois abra o Chrome")
        self.assertEqual(plano["etapas"][0]["acao"], "abrir")
        self.assertEqual(plano["etapas"][0]["erro"], "parametro_ausente:alvo")

    def test_acao_desconhecida(self):
        plano = interpretar_comando_complexo("Dance, depois abra o Chrome")
        self.assertEqual(plano["etapas"][0]["acao"], "acao_desconhecida")


class TestExecutorComplexo(unittest.TestCase):
    def _plano(self, etapas):
        return {
            "tipo": "comando_complexo",
            "id": "workflow-teste",
            "status": "planejado",
            "descricao": "teste",
            "etapas": etapas,
        }

    def _etapa(self, etapa_id, acao="acao_ok", obrigatoria=True, dependencias=None, **extras):
        etapa = {
            "id": etapa_id,
            "acao": acao,
            "parametros": {},
            "dependencias": dependencias if dependencias is not None else [],
            "obrigatoria": obrigatoria,
            "status": "pendente",
            "max_tentativas": 1,
            "timeout": None,
        }
        etapa.update(extras)
        return etapa

    def test_falha_na_primeira_etapa_nao_interrompe(self):
        executor = ExecutorComplexo(lambda acao, params: {"sucesso": False, "erro": "falhou"})
        resultado = executor.executar(self._plano([self._etapa(1), self._etapa(2)]))
        self.assertFalse(resultado["sucesso"])
        self.assertEqual(len(resultado["resultados"]), 2)

    def test_falha_no_meio_continua_preservando_resultados(self):
        def fake(acao, params):
            return {"sucesso": acao != "falha", "mensagem": acao}

        etapas = [self._etapa(1), self._etapa(2, "falha"), self._etapa(3)]
        resultado = ExecutorComplexo(fake).executar(self._plano(etapas))
        self.assertEqual(resultado["contexto"]["etapas_concluidas"], [1, 3])
        self.assertEqual(resultado["contexto"]["etapas_falhas"], [2])

    def test_plano_interpretado_executa_todas_as_etapas_em_ordem(self):
        plano = interpretar("Abra o Chrome e abra o VS Code.")
        chamadas = []

        def fake(acao, parametros):
            chamadas.append((acao, parametros["nome"]))
            return {"sucesso": True, "confirmado": True}

        resultado = ExecutorComplexo(fake).executar(plano)
        self.assertEqual(
            chamadas,
            [
                ("abrir_aplicativo", "Google Chrome"),
                ("abrir_aplicativo", "Visual Studio Code"),
            ],
        )
        self.assertEqual(len(resultado["resultados"]), 2)
        self.assertEqual(resultado["mensagem"], "Todas as ações foram concluídas com sucesso.")

    def test_falha_na_ultima_etapa(self):
        def fake(acao, params):
            return {"sucesso": acao != "falha"}

        etapas = [self._etapa(1), self._etapa(2), self._etapa(3, "falha")]
        resultado = ExecutorComplexo(fake).executar(self._plano(etapas))
        self.assertFalse(resultado["sucesso"])
        self.assertEqual(len(resultado["resultados"]), 3)

    def test_dependencia_quebrada(self):
        def fake(acao, params):
            return {"sucesso": False, "erro": "falha_controlada"}

        etapas = [
            self._etapa(1, obrigatoria=False),
            self._etapa(2, dependencias=[1]),
            self._etapa(3, dependencias=[]),
        ]
        resultado = ExecutorComplexo(fake).executar(self._plano(etapas))
        self.assertEqual(resultado["resultados"][1]["status"], "ignorado")
        self.assertEqual(resultado["resultados"][1]["erro"], "dependencia_quebrada:1")
        self.assertEqual(len(resultado["resultados"]), 3)

    def test_motivo_desconhecido_nao_e_inventado(self):
        def sem_causa(acao, params):
            return {"sucesso": False}

        resultado = ExecutorComplexo(sem_causa).executar(
            self._plano([self._etapa(1), self._etapa(2)])
        )
        self.assertEqual(
            resultado["resultados"][0]["motivo"],
            "Não foi possível determinar a causa da falha.",
        )
        self.assertEqual(len(resultado["resultados"]), 2)

    @patch("sist_comd_complex.interpretador_complex.requests")
    def test_ollama_interpreta_sequencia_ambigua(self, mock_requests):
        resposta = MagicMock()
        resposta.json.return_value = {
            "response": (
                '{"etapas": ['
                '{"acao":"abrir_aplicativo","parametros":{"nome":"Chrome"}},'
                '{"acao":"abrir_site","parametros":{"site":"github"}}'
                ']}'
            )
        }
        mock_requests.post.return_value = resposta

        plano = interpretar_comando_complexo("quero abrir o Chrome e abrir o GitHub")

        self.assertEqual(
            [etapa["acao"] for etapa in plano["etapas"]],
            ["abrir_aplicativo", "abrir_site"],
        )
        self.assertEqual(plano["etapas"][0]["dependencias"], [])
        mock_requests.post.assert_called_once()

    def test_timeout(self):
        def lento(acao, params):
            time.sleep(0.2)
            return {"sucesso": True}

        etapa = self._etapa(1, timeout=0.01)
        resultado = ExecutorComplexo(lento).executar(self._plano([etapa]))
        self.assertEqual(resultado["resultados"][0]["status"], "timeout")

    def test_cancelamento(self):
        executor = ExecutorComplexo(lambda acao, params: {"sucesso": True})
        executor.cancelar_workflow()
        resultado = executor.executar(self._plano([self._etapa(1), self._etapa(2)]))
        self.assertEqual(resultado["status"], "cancelado")
        self.assertEqual(resultado["resultados"][0]["status"], "cancelado")

    def test_workflow_vazio(self):
        resultado = ExecutorComplexo(lambda acao, params: {"sucesso": True}).executar(
            self._plano([])
        )
        self.assertEqual(resultado["erro"], "workflow_vazio")

    def test_plano_invalido(self):
        resultado = ExecutorComplexo(lambda acao, params: {"sucesso": True}).executar(
            {"tipo": "outro"}
        )
        self.assertEqual(resultado["erro"], "tipo_invalido")

    def test_execucao_parcial_com_etapa_opcional(self):
        def fake(acao, params):
            return {"sucesso": acao != "opcional_falha"}

        etapas = [
            self._etapa(1),
            self._etapa(2, "opcional_falha", obrigatoria=False),
            self._etapa(3, dependencias=[]),
        ]
        resultado = ExecutorComplexo(fake).executar(self._plano(etapas))
        self.assertEqual(resultado["contexto"]["etapas_concluidas"], [1, 3])
        self.assertEqual(resultado["contexto"]["etapas_falhas"], [2])

    def test_retry(self):
        chamadas = {"total": 0}

        def instavel(acao, params):
            chamadas["total"] += 1
            return {"sucesso": chamadas["total"] == 2}

        etapa = self._etapa(1, max_tentativas=2)
        resultado = ExecutorComplexo(instavel).executar(self._plano([etapa]))
        self.assertTrue(resultado["sucesso"])
        self.assertEqual(chamadas["total"], 2)


if __name__ == "__main__":
    unittest.main()
