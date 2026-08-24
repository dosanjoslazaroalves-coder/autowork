from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    OpenAI,
    RateLimitError,
)

from conversa.prompt import SYSTEM_PROMPT

# Coloque a chave da API do OpenRouter aqui (começa com sk-or-v1-).
# Se deixar SUA_CHAVE_AQUI, o programa tenta OPENROUTER_API_KEY ou CHAVE_API_CHAT.
OPENROUTER_API_KEY = "SUA_CHAVE_AQUI"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "openrouter/free"
MAX_HISTORY = 20
TIMEOUT_SECONDS = 45.0
MENSAGEM_FALHA = "Não foi possível obter uma resposta da IA."

logger = logging.getLogger("autowork.conversa")

_RAIZ = Path(__file__).resolve().parents[1]
_ARQUIVOS_ENV = (_RAIZ / ".env", _RAIZ / ".venv" / ".env")


def _ler_arquivo_env(caminho: Path) -> dict[str, str]:
    valores: dict[str, str] = {}
    if not caminho.is_file():
        return valores
    try:
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            texto = linha.strip()
            if not texto or texto.startswith("#") or "=" not in texto:
                continue
            nome, valor = texto.split("=", 1)
            valores[nome.strip()] = valor.strip().strip('"').strip("'")
    except OSError:
        logger.warning("Não foi possível ler arquivo de chave.")
    return valores


def carregar_api_key() -> str:
    if OPENROUTER_API_KEY.strip() and OPENROUTER_API_KEY.strip() != "SUA_CHAVE_AQUI":
        return OPENROUTER_API_KEY.strip()

    for nome in ("OPENROUTER_API_KEY", "CHAVE_API_CHAT"):
        valor = os.environ.get(nome, "").strip()
        if valor:
            return valor

    for caminho in _ARQUIVOS_ENV:
        env = _ler_arquivo_env(caminho)
        for nome in ("OPENROUTER_API_KEY", "CHAVE_API_CHAT"):
            valor = env.get(nome, "").strip()
            if valor:
                return valor

    return ""


class Chatbot:
    """Camada de conversa: OpenRouter, histórico temporário e resposta textual."""

    def __init__(
        self,
        api_key: str = "",
        model: str = MODEL,
        max_history: int = MAX_HISTORY,
        timeout: float = TIMEOUT_SECONDS,
    ) -> None:
        self.model = model
        self.max_history = max_history
        self._api_key = (api_key or carregar_api_key()).strip()
        self._client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=self._api_key or "missing",
            timeout=timeout,
            default_headers={
                "HTTP-Referer": "https://autowork.local",
                "X-Title": "AUTOWORK",
            },
        )
        self._historico: list[dict[str, str]] = []
        self.limpar_historico()

    def limpar_historico(self) -> None:
        self._historico = [{"role": "system", "content": SYSTEM_PROMPT}]

    def enviar(self, mensagem: str) -> str:
        texto = mensagem.strip()
        if not texto:
            return "Envie uma mensagem para conversar."

        if not self._api_key or self._api_key == "SUA_CHAVE_AQUI":
            logger.warning("Chamada bloqueada: API key não configurada.")
            return (
                "Falta a chave da API do OpenRouter. "
                "Cole em OPENROUTER_API_KEY em conversa/chatbot.py "
                "ou em CHAVE_API_CHAT."
            )

        self._historico.append({"role": "user", "content": texto})
        self._trim_historico()

        try:
            resposta = self._client.chat.completions.create(
                model=self.model,
                messages=self._historico,
            )
        except AuthenticationError:
            logger.warning("Falha na API OpenRouter: chave inválida.")
            self._desfazer_ultima_mensagem_usuario()
            return "A chave da API é inválida. Verifique OPENROUTER_API_KEY."
        except APITimeoutError:
            logger.warning("Falha na API OpenRouter: timeout.")
            self._desfazer_ultima_mensagem_usuario()
            return "A solicitação excedeu o tempo limite. Tente novamente."
        except APIConnectionError:
            logger.warning("Falha na API OpenRouter: conexão.")
            self._desfazer_ultima_mensagem_usuario()
            return "Não foi possível conectar à API. Verifique sua internet."
        except RateLimitError:
            logger.warning("Falha na API OpenRouter: 429.")
            self._desfazer_ultima_mensagem_usuario()
            return "Muitas solicitações no momento. Aguarde e tente novamente."
        except NotFoundError:
            logger.warning("Falha na API OpenRouter: modelo indisponível.")
            self._desfazer_ultima_mensagem_usuario()
            return "O modelo configurado não está disponível no momento."
        except APIStatusError as exc:
            logger.warning(
                "Falha na API OpenRouter: HTTP %s.",
                getattr(exc, "status_code", "desconhecido"),
            )
            self._desfazer_ultima_mensagem_usuario()
            return self._mensagem_http(exc)
        except Exception:
            logger.exception("Erro inesperado ao consultar a API OpenRouter.")
            self._desfazer_ultima_mensagem_usuario()
            return MENSAGEM_FALHA

        conteudo = self._extrair_conteudo(resposta)
        if not conteudo:
            logger.warning("Falha na API OpenRouter: resposta vazia.")
            self._desfazer_ultima_mensagem_usuario()
            return MENSAGEM_FALHA

        self._historico.append({"role": "assistant", "content": conteudo})
        self._trim_historico()
        return conteudo

    def _trim_historico(self) -> None:
        sistema = self._historico[0]
        recentes = self._historico[1:]
        if len(recentes) > self.max_history:
            recentes = recentes[-self.max_history :]
        self._historico = [sistema, *recentes]

    def _desfazer_ultima_mensagem_usuario(self) -> None:
        if len(self._historico) > 1 and self._historico[-1]["role"] == "user":
            self._historico.pop()

    def _mensagem_http(self, exc: APIStatusError) -> str:
        status = getattr(exc, "status_code", None)
        if status == 400:
            return "O modelo configurado não está disponível ou a solicitação é inválida."
        if status == 401:
            return "A chave da API é inválida. Verifique OPENROUTER_API_KEY."
        if status == 404:
            return "O modelo configurado não está disponível no momento."
        if status == 429:
            return "Muitas solicitações no momento. Aguarde e tente novamente."
        if isinstance(status, int) and status >= 500:
            return "O serviço da IA está indisponível no momento. Tente novamente."
        return MENSAGEM_FALHA

    def _extrair_conteudo(self, resposta: Any) -> str:
        try:
            choices = getattr(resposta, "choices", None) or []
            if not choices:
                return ""
            message = getattr(choices[0], "message", None)
            content = getattr(message, "content", None)
            if isinstance(content, str):
                return content.strip()
            return ""
        except Exception:
            logger.warning("Não foi possível ler o conteúdo da resposta.")
            return ""
