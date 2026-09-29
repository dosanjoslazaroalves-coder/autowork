from __future__ import annotations

import logging
import queue
import threading
from datetime import datetime
from typing import Any, Callable, Dict, Mapping, Optional

logger = logging.getLogger(__name__)

STATUS_PLANEJADO = "planejado"
STATUS_EXECUTANDO = "executando"
STATUS_CONCLUIDO = "concluido"
STATUS_FALHOU = "falhou"
STATUS_CANCELADO = "cancelado"
STATUS_INTERROMPIDO = "interrompido"
STATUS_IGNORADO = "ignorado"
STATUS_TIMEOUT = "timeout"

ExecutorEtapa = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]


class ExecutorComplexo:
    """Orquestra workflows sequenciais de comandos complexos."""

    def __init__(
        self,
        executor_etapa: Optional[ExecutorEtapa] = None,
        *,
        timeout_padrao: Optional[float] = None,
    ) -> None:
        self._executor_etapa = executor_etapa or _executar_acao_real
        self._timeout_padrao = timeout_padrao
        self._cancelado = threading.Event()

    def cancelar_workflow(self) -> None:
        self._cancelado.set()

    def executar(self, plano: Mapping[str, Any]) -> Dict[str, Any]:
        validacao = self._validar_plano(plano)
        if validacao is not None:
            return validacao

        workflow_id = str(plano.get("id"))
        etapas = [dict(etapa) for etapa in plano.get("etapas", [])]
        contexto: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "comando_original": plano.get("comando_original") or plano.get("descricao", ""),
            "etapa_atual": None,
            "status": STATUS_EXECUTANDO,
            "iniciado_em": datetime.now().isoformat(timespec="seconds"),
            "finalizado_em": None,
            "resultados": [],
            "etapas_concluidas": [],
            "etapas_falhas": [],
            "erro_atual": None,
        }

        logger.info("[WORKFLOW] ID: %s STATUS: %s", workflow_id, STATUS_EXECUTANDO)

        for indice, etapa in enumerate(etapas, start=1):
            if self._cancelado.is_set():
                resultado = _resultado_etapa(
                    etapa,
                    sucesso=False,
                    status=STATUS_CANCELADO,
                    mensagem=None,
                    erro="workflow_cancelado",
                )
                contexto["resultados"].append(resultado)
                contexto["status"] = STATUS_CANCELADO
                break

            contexto["etapa_atual"] = etapa.get("id")
            dependencia_quebrada = self._dependencia_quebrada(etapa, contexto["resultados"])
            if dependencia_quebrada:
                resultado = _resultado_etapa(
                    etapa,
                    sucesso=False,
                    status=STATUS_IGNORADO,
                    mensagem=None,
                    erro=f"dependencia_quebrada:{dependencia_quebrada}",
                )
                contexto["resultados"].append(resultado)
                contexto["etapas_falhas"].append(etapa.get("id"))
                contexto["erro_atual"] = resultado["erro"]
                # Uma dependência quebrada impede somente esta etapa. As
                # etapas seguintes ainda podem ser independentes e precisam
                # ser processadas na ordem original.
                continue

            logger.info(
                "[ETAPA %s/%s] ACAO: %s STATUS: %s",
                indice,
                len(etapas),
                etapa.get("acao"),
                STATUS_EXECUTANDO,
            )
            resultado = self._executar_com_retry(etapa)
            contexto["resultados"].append(resultado)

            if resultado["sucesso"]:
                contexto["etapas_concluidas"].append(etapa.get("id"))
                logger.info("[ETAPA %s/%s] STATUS: %s", indice, len(etapas), STATUS_CONCLUIDO)
                continue

            contexto["etapas_falhas"].append(etapa.get("id"))
            contexto["erro_atual"] = resultado["erro"]
            logger.info("[ETAPA %s/%s] STATUS: %s", indice, len(etapas), resultado["status"])
            # Falhas não interrompem automaticamente as próximas etapas.
            # Dependências reais são avaliadas quando a etapa dependente
            # chegar; ações independentes seguem normalmente.
            continue

        if contexto["status"] == STATUS_EXECUTANDO:
            contexto["status"] = (
                STATUS_CONCLUIDO if len(contexto["etapas_concluidas"]) == len(etapas) else STATUS_FALHOU
            )

        contexto["finalizado_em"] = datetime.now().isoformat(timespec="seconds")
        sucesso = contexto["status"] == STATUS_CONCLUIDO
        logger.info("[WORKFLOW] ID: %s STATUS: %s", workflow_id, contexto["status"])

        return {
            "tipo": "workflow",
            "workflow_id": workflow_id,
            "status": "sucesso" if sucesso else contexto["status"],
            "sucesso": sucesso,
            "confirmado": sucesso,
            "executado": bool(contexto["resultados"]),
            "mensagem": _mensagem_final(contexto, total_etapas=len(etapas)),
            "contexto": contexto,
            "resultados": contexto["resultados"],
            "falar": not sucesso,
        }

    def _executar_com_retry(self, etapa: Mapping[str, Any]) -> Dict[str, Any]:
        max_tentativas = max(1, int(etapa.get("max_tentativas") or 1))
        ultimo_resultado: Optional[Dict[str, Any]] = None

        for tentativa in range(1, max_tentativas + 1):
            if self._cancelado.is_set():
                return _resultado_etapa(
                    etapa,
                    sucesso=False,
                    status=STATUS_CANCELADO,
                    mensagem=None,
                    erro="workflow_cancelado",
                    tentativa=tentativa,
                )

            try:
                bruto = self._executar_uma_tentativa(etapa)
            except Exception as exc:  # uma ação nunca deve abortar o workflow
                bruto = {
                    "sucesso": False,
                    "status": STATUS_FALHOU,
                    "mensagem": None,
                    "erro": str(exc),
                }
            ultimo_resultado = _normalizar_retorno(etapa, bruto, tentativa=tentativa)
            if ultimo_resultado["sucesso"]:
                return ultimo_resultado

        assert ultimo_resultado is not None
        return ultimo_resultado

    def _executar_uma_tentativa(self, etapa: Mapping[str, Any]) -> Mapping[str, Any]:
        timeout = etapa.get("timeout", self._timeout_padrao)
        if timeout in (None, 0):
            return self._executor_etapa(str(etapa.get("acao")), dict(etapa.get("parametros", {})))

        fila: "queue.Queue[Mapping[str, Any]]" = queue.Queue(maxsize=1)

        def alvo() -> None:
            try:
                fila.put(self._executor_etapa(str(etapa.get("acao")), dict(etapa.get("parametros", {}))))
            except Exception as exc:  # pragma: no cover - caminho defensivo
                fila.put({"sucesso": False, "status": STATUS_FALHOU, "erro": str(exc), "mensagem": None})

        thread = threading.Thread(target=alvo, name=f"workflow-etapa-{etapa.get('id')}", daemon=True)
        thread.start()

        try:
            return fila.get(timeout=float(timeout))
        except queue.Empty:
            return {
                "sucesso": False,
                "status": STATUS_TIMEOUT,
                "mensagem": None,
                "erro": f"timeout:{timeout}",
            }

    def _validar_plano(self, plano: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(plano, Mapping):
            return _resultado_plano_invalido("plano_nao_mapeavel")
        if plano.get("tipo") != "comando_complexo":
            return _resultado_plano_invalido("tipo_invalido")
        etapas = plano.get("etapas")
        if not isinstance(etapas, list):
            return _resultado_plano_invalido("etapas_invalidas")
        if not etapas:
            return _resultado_plano_invalido("workflow_vazio")
        for etapa in etapas:
            if not isinstance(etapa, Mapping) or not etapa.get("id") or not etapa.get("acao"):
                return _resultado_plano_invalido("etapa_invalida")
        return None

    @staticmethod
    def _dependencia_quebrada(etapa: Mapping[str, Any], resultados: list[Dict[str, Any]]) -> Optional[Any]:
        por_id = {resultado.get("etapa_id"): resultado for resultado in resultados}
        for dependencia in etapa.get("dependencias", []) or []:
            resultado = por_id.get(dependencia)
            if not resultado or not resultado.get("sucesso"):
                return dependencia
        return None


def executar_workflow(plano: Mapping[str, Any]) -> Dict[str, Any]:
    return ExecutorComplexo().executar(plano)


def _normalizar_retorno(
    etapa: Mapping[str, Any],
    retorno: Mapping[str, Any],
    *,
    tentativa: int,
) -> Dict[str, Any]:
    sucesso = _retorno_sucesso(retorno)
    status = STATUS_CONCLUIDO if sucesso else str(retorno.get("status") or STATUS_FALHOU)
    return _resultado_etapa(
        etapa,
        sucesso=sucesso,
        status=status,
        mensagem=retorno.get("mensagem"),
        erro=retorno.get("erro"),
        tentativa=tentativa,
        retorno=dict(retorno),
    )


def _retorno_sucesso(retorno: Mapping[str, Any]) -> bool:
    if retorno.get("confirmado") is True:
        return True
    if "confirmado" in retorno:
        return False
    return retorno.get("sucesso") is True


def _resultado_etapa(
    etapa: Mapping[str, Any],
    *,
    sucesso: bool,
    status: str,
    mensagem: Optional[Any],
    erro: Optional[Any],
    tentativa: Optional[int] = None,
    retorno: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    resultado = {
        "sucesso": bool(sucesso),
        "status": status,
        "etapa_id": etapa.get("id"),
        "acao": etapa.get("acao"),
        "mensagem": mensagem if isinstance(mensagem, str) and mensagem else None,
        "erro": erro,
        "motivo": None if sucesso else _motivo_falha(mensagem, erro, status),
        "tentativa": tentativa,
        "obrigatoria": etapa.get("obrigatoria", True),
        "parametros": dict(etapa.get("parametros", {})),
    }
    if retorno is not None:
        resultado["retorno"] = retorno
    return resultado


def _resultado_plano_invalido(erro: str) -> Dict[str, Any]:
    return {
        "tipo": "workflow",
        "workflow_id": None,
        "status": STATUS_FALHOU,
        "sucesso": False,
        "confirmado": False,
        "executado": False,
        "mensagem": "Plano de workflow inválido.",
        "erro": erro,
        "contexto": {
            "workflow_id": None,
            "status": STATUS_FALHOU,
            "resultados": [],
            "erro_atual": erro,
        },
        "resultados": [],
        "falar": True,
    }


def _mensagem_final(contexto: Mapping[str, Any], *, total_etapas: int) -> str:
    concluidas = len(contexto.get("etapas_concluidas", []))
    resultados = list(contexto.get("resultados", []))
    if contexto.get("status") == STATUS_CONCLUIDO:
        return "Todas as ações foram concluídas com sucesso."
    if contexto.get("status") == STATUS_CANCELADO:
        return f"Workflow cancelado após {concluidas} de {total_etapas} etapa(s)."

    falhas = [resultado for resultado in resultados if not resultado.get("sucesso")]
    mensagem = f"Concluí o comando. {concluidas} de {total_etapas} ação(ões) foram concluídas."
    if not falhas:
        return mensagem

    detalhes = []
    for falha in falhas:
        etapa = falha.get("etapa_id")
        acao = falha.get("acao") or "ação"
        motivo = falha.get("motivo") or "Não foi possível determinar a causa da falha."
        detalhes.append(f"A etapa {etapa} ({acao}) falhou: {motivo}.")
    return f"{mensagem} " + " ".join(detalhes)


def _motivo_falha(mensagem: Optional[Any], erro: Optional[Any], status: str) -> str:
    """Retorna somente uma causa fornecida pela ação ou pelo executor."""
    if status == STATUS_IGNORADO:
        return "uma dependência anterior não foi concluída"

    candidatos = [valor for valor in (mensagem, erro) if isinstance(valor, str) and valor.strip()]
    genericos = {
        "falha",
        "falhou",
        "erro",
        "falha ao executar ação",
        "falha ao executar acao",
        "erro ao executar ação",
        "erro ao executar acao",
        "falha ao executar ação.",
        "falha ao executar acao.",
    }
    for candidato in candidatos:
        if candidato.strip().lower() not in genericos:
            return candidato.strip()
    return "Não foi possível determinar a causa da falha."


def _executar_acao_real(acao: str, parametros: Mapping[str, Any]) -> Mapping[str, Any]:
    registro = _registro_acoes()
    funcao = registro.get(acao)
    if funcao is None:
        return {
            "sucesso": False,
            "executado": False,
            "confirmado": False,
            "status": "acao_nao_encontrada",
            "mensagem": f"Ação complexa '{acao}' não registrada.",
            "erro": "acao_nao_encontrada",
        }
    return funcao(dict(parametros))


def _registro_acoes() -> Dict[str, Callable[[Mapping[str, Any]], Mapping[str, Any]]]:
    from comd_rapidos.abrir_app import abrir_app
    from comd_rapidos.abrir_site import abrir_site
    from comd_rapidos.atalho_nav import AtalhoNav
    from comd_rapidos.atalhos import Janela

    registro: Dict[str, Callable[..., Mapping[str, Any]]] = {}

    def registrar(nome: str, funcao: Callable[..., Mapping[str, Any]], **_: Any) -> None:
        registro[nome] = funcao

    Janela().registrar_no_executor(registrar)
    AtalhoNav().registrar_no_executor(registrar)

    def chamar_abrir_app(parametros: Mapping[str, Any]) -> Mapping[str, Any]:
        return abrir_app(str(parametros.get("nome") or parametros.get("aplicativo") or ""))

    def chamar_abrir_site(parametros: Mapping[str, Any]) -> Mapping[str, Any]:
        return abrir_site(str(parametros.get("url") or parametros.get("site") or ""))

    adaptado: Dict[str, Callable[[Mapping[str, Any]], Mapping[str, Any]]] = {
        "abrir_aplicativo": chamar_abrir_app,
        "abrir_app": chamar_abrir_app,
        "abrir_site": chamar_abrir_site,
    }

    for nome, funcao in registro.items():
        adaptado[nome] = lambda parametros, fn=funcao: fn()

    return adaptado
