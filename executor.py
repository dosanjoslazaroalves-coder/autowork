from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)  


REGISTRO_ACOES: Dict[str, Callable[..., Any]] = {}


def registrar(nome_acao: str, funcao: Callable[..., Any]) -> None:

    if nome_acao in REGISTRO_ACOES:
        logger.warning(
            "Registro: ação '%s' já registrada. Substituindo.", nome_acao
        )

    REGISTRO_ACOES[nome_acao] = funcao
    logger.debug("Registro: ação '%s' registrada com sucesso.", nome_acao)


def executar(
    acao: str,
    **parametros: Any,
) -> Dict[str, Any]:
   
    logger.debug("Executor: recebido acao='%s' parametros=%s", acao, parametros)

    # 1. Busca a função no registro
    funcao = REGISTRO_ACOES.get(acao)

    if funcao is None:
        logger.warning("Executor: ação '%s' não encontrada no registro.", acao)
        return {
            "status": "acao_nao_encontrada",
            "mensagem": f"Ação '{acao}' não está registrada no sistema.",
            "acao": acao,
            "parametros": dict(parametros),
        }

    # 2. Executa a função
    try:
        logger.info("Executor: executando '%s'...", acao)

        # Chama a função com os parâmetros corretos
        if parametros:
            funcao(**parametros)
        else:
            funcao()

        logger.info("Executor: '%s' concluída com sucesso.", acao)
        return {
            "status": "sucesso",
            "mensagem": f"Comando '{acao}' executado com sucesso.",
            "acao": acao,
            "parametros": dict(parametros),
        }

    except Exception as exc:
        logger.exception("Executor: erro ao executar '%s': %s", acao, exc)
        return {
            "status": "falha",
            "mensagem": f"Erro ao executar '{acao}': {exc}",
            "acao": acao,
            "parametros": dict(parametros),
        }

