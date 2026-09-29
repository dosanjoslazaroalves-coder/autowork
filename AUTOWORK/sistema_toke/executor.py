from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, Dict, Mapping

from sistema_toke.contrato import interpretar_retorno_acao

logger = logging.getLogger(__name__)


REGISTRO_ACOES: Dict[str, Callable[..., Any]] = {}


def _envelope(
    *,
    acao: str,
    parametros: Mapping[str, Any],
    status: str,
    executado: bool,
    confirmado: bool,
    mensagem: str,
    iniciado: bool,
    erro: Any = None,
    detalhes: Any = None,
) -> Dict[str, Any]:
    return {
        "status": status,
        "iniciado": iniciado,
        "executado": executado,
        "confirmado": confirmado,
        "mensagem": mensagem,
        "acao": acao,
        "parametros": dict(parametros),
        "detalhes": detalhes if isinstance(detalhes, dict) else {},
        "erro": erro,
    }


def registrar(
    nome_acao: str,
    funcao: Callable[..., Any],
    *,
    substituir: bool = False,
) -> None:
    existente = REGISTRO_ACOES.get(nome_acao)
    if existente is not None and existente is not funcao:
        if not substituir:
            logger.warning(
                "Registro: ação '%s' já registrada. Mantendo a função atual.",
                nome_acao,
            )
            return
        logger.warning(
            "Registro: ação '%s' já registrada. Substituindo.", nome_acao
        )

    REGISTRO_ACOES[nome_acao] = funcao
    logger.debug("Registro: ação '%s' registrada com sucesso.", nome_acao)


def registrar_comandos_padrao() -> None:
    from comd_rapidos.abrir_app import abrir_app
    from comd_rapidos.abrir_site import abrir_site
    from comd_rapidos.atalho_nav import AtalhoNav
    from comd_rapidos.atalhos import Janela

    registrar("abrir_app", abrir_app)
    registrar("abrir_site", abrir_site)
    Janela().registrar_no_executor(registrar)
    AtalhoNav().registrar_no_executor(registrar)

    logger.info(
        "Executor: registro padrão inicializado com %d ação(ns).",
        len(REGISTRO_ACOES),
    )


def _chamar_funcao(funcao: Callable[..., Any], parametros: Dict[str, Any]) -> Any:
    try:
        sig = inspect.signature(funcao)
    except (TypeError, ValueError):
        return funcao(**parametros) if parametros else funcao()

    aceita_var_kw = any(
        parametro.kind == inspect.Parameter.VAR_KEYWORD
        for parametro in sig.parameters.values()
    )
    nomes_validos = {
        nome
        for nome, parametro in sig.parameters.items()
        if parametro.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    }

    if aceita_var_kw:
        filtrados = dict(parametros)
    else:
        extras = [nome for nome in parametros if nome not in nomes_validos]
        if extras:
            logger.warning(
                "Executor: ignorando parâmetros fora da assinatura: %s", extras
            )
        filtrados = {
            nome: valor for nome, valor in parametros.items() if nome in nomes_validos
        }

    for nome, parametro in sig.parameters.items():
        if parametro.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if parametro.default is inspect.Parameter.empty and nome not in filtrados:
            raise TypeError(f"parâmetro obrigatório ausente: {nome}")

    return funcao(**filtrados) if filtrados else funcao()


def executar(
    acao: str,
    **parametros: Any,
) -> Dict[str, Any]:
    logger.debug("Executor: recebido acao='%s' parametros=%s", acao, parametros)

    funcao = REGISTRO_ACOES.get(acao)

    if funcao is None:
        logger.warning("Executor: ação '%s' não encontrada no registro.", acao)
        return _envelope(
            acao=acao,
            parametros=parametros,
            status="acao_nao_encontrada",
            iniciado=False,
            executado=False,
            confirmado=False,
            mensagem=f"Ação '{acao}' não está registrada no sistema.",
            erro="Função não registrada",
        )

    try:
        logger.info("Executor: executando '%s'...", acao)
        retorno = _chamar_funcao(funcao, dict(parametros))
    except TypeError as exc:
        logger.warning("Executor: contrato de parâmetros inválido em '%s': %s", acao, exc)
        return _envelope(
            acao=acao,
            parametros=parametros,
            status="contrato_invalido",
            iniciado=False,
            executado=False,
            confirmado=False,
            mensagem=f"Parâmetros inválidos para '{acao}'.",
            erro=str(exc),
        )
    except Exception as exc:
        logger.exception("Executor: erro ao executar '%s': %s", acao, exc)
        return _envelope(
            acao=acao,
            parametros=parametros,
            status="erro_excecao",
            iniciado=True,
            executado=False,
            confirmado=False,
            mensagem=f"Erro ao executar '{acao}': {exc}",
            erro=str(exc),
        )

    interpretado = interpretar_retorno_acao(retorno)
    logger.info(
        "Executor: '%s' finalizada. status='%s' executado=%s confirmado=%s.",
        acao,
        interpretado["status"],
        interpretado["executado"],
        interpretado["confirmado"],
    )
    return _envelope(
        acao=acao,
        parametros=parametros,
        status=interpretado["status"],
        iniciado=True,
        executado=interpretado["executado"],
        confirmado=interpretado["confirmado"],
        mensagem=interpretado["mensagem"],
        erro=interpretado.get("erro"),
        detalhes=interpretado.get("detalhes"),
    )
