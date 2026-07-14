from __future__ import annotations

from typing import Any, Mapping, Optional
import logging

import pyautogui

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    try:
        logger.info(msg)
    except Exception:
        pass


def _validar_json(comando: Any) -> Optional[dict[str, Any]]:
    if not isinstance(comando, Mapping):
        _log("ia.py: comando inválido (não é dict/mapping)")
        return None

    acao = comando.get("acao")
    parametros = comando.get("parametros")

    if not isinstance(acao, str) or not acao.strip():
        _log("ia.py: comando inválido (acao ausente/inválida)")
        return None

    if not isinstance(parametros, Mapping):
        _log("ia.py: comando inválido (parametros ausente/inválido)")
        return None

    return dict(comando)


def _validar_parametros_abrir_app(parametros: Mapping[str, Any]) -> Optional[str]:
    nome = parametros.get("nome")
    if not isinstance(nome, str) or not nome.strip():
        _log("ia.py: abrir_app sem parametros.nome válido")
        return None
    return nome.strip()


def _abrir_app(nome_app: str) -> None:
    # Ativa o menu Iniciar com a tecla Windows.
    pyautogui.press("win")

    # Espera mínima para o menu/pesquisa abrir.
    pyautogui.sleep(0.2)

    # Digita o nome do app e envia.
    pyautogui.typewrite(nome_app)
    pyautogui.press("enter")


def executar_comando(comando: dict) -> dict[str, object]:
    """Executa a automação correspondente ao dicionário recebido.

    Contrato de entrada:
      - dict já interpretado pelo fala.py, com campos:
        {"acao": str, "parametros": dict}

    Contrato de retorno (para integração com voz.py):
      - {"status": str, "mensagem": str, "acao": str, "parametros": dict}

    Observação:
      - Mantém o foco em ser um executor simples para expansão futura.
    """

    try:
        validado = _validar_json(comando)
        if validado is None:
            return {
                "status": "falha",
                "mensagem": "Não foi possível validar o comando.",
                "acao": "",
                "parametros": {},
            }

        acao = str(validado.get("acao")).strip().lower()
        parametros = validado.get("parametros")
        if not isinstance(parametros, Mapping):
            return {
                "status": "falha",
                "mensagem": "Parâmetros inválidos para a ação.",
                "acao": acao,
                "parametros": {},
            }

        if acao == "abrir_app":
            nome_app = _validar_parametros_abrir_app(parametros)
            if nome_app is None:
                return {
                    "status": "falha",
                    "mensagem": "Nome do aplicativo inválido.",
                    "acao": acao,
                    "parametros": {},
                }

            _abrir_app(nome_app)
            _log(f"ia.py: executado abrir_app: {nome_app}")
            return {
                "status": "sucesso",
                "mensagem": f"{nome_app} aberto com sucesso.",
                "acao": acao,
                "parametros": {"nome": nome_app},
            }

        _log(f"ia.py: ação desconhecida: {acao}")
        return {
            "status": "comando_desconhecido",
            "mensagem": "Não conheço essa ação no momento.",
            "acao": acao,
            "parametros": dict(parametros) if isinstance(parametros, Mapping) else {},
        }

    except Exception as exc:
        try:
            _log(f"ia.py: erro ao executar comando: {exc}")
        except Exception:
            pass
        return {
            "status": "falha",
            "mensagem": "Aconteceu um erro ao executar a ação.",
            "acao": "",
            "parametros": {},
        }


