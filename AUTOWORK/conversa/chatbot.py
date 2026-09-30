"""Chatbot da conversa normal, atendida pelo Ollama local."""
from __future__ import annotations

import logging
from typing import Any, Optional

import requests

from conversa.historico import HistoricoConversa
from conversa.ollama import OLLAMA_MODEL, OLLAMA_NUM_PREDICT, OLLAMA_TIMEOUT, OLLAMA_URL
from conversa.prompt import SYSTEM_PROMPT

MODEL = OLLAMA_MODEL
MAX_HISTORY = 20
TIMEOUT_SECONDS = OLLAMA_TIMEOUT
MENSAGEM_FALHA = "Não foi possível obter uma resposta da IA."

logger = logging.getLogger("autowork.conversa.normal")


class Chatbot:
    """Cliente de conversa normal via HTTP para o Ollama local.

    A interface pública ``responder``/``enviar`` permanece compatível com o
    chatbot anterior. O histórico é somente em memória e pode ser compartilhado
    com o cliente avançado pelo dispatcher.
    """

    def __init__(
        self,
        model: str = MODEL,
        url: str = OLLAMA_URL,
        max_history: int = MAX_HISTORY,
        timeout: float = TIMEOUT_SECONDS,
        historico: Optional[HistoricoConversa] = None,
    ) -> None:
        self.model = model
        self.url = url
        self.max_history = max_history
        self.timeout = timeout
        self._historico = historico or HistoricoConversa(max_history=max_history)
        if not self._historico.mensagens:
            self.limpar_historico()
        self._ultima_solicitacao_sucesso = False

    def limpar_historico(self) -> None:
        self._historico.limpar(SYSTEM_PROMPT)

    def responder(self, mensagem: str) -> dict[str, Any]:
        """Retorna a resposta no formato estruturado usado pelo dispatcher."""
        conteudo = self.enviar(mensagem)
        return {
            "tipo": "conversa",
            "mensagem": conteudo,
            "sucesso": self._ultima_solicitacao_sucesso,
        }

    def enviar(self, mensagem: str) -> str:
        texto = mensagem.strip()
        self._ultima_solicitacao_sucesso = False
        if not texto:
            return "Envie uma mensagem para conversar."

        self._historico.adicionar("user", texto)
        prompt = self._montar_prompt()
        dados = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"num_predict": OLLAMA_NUM_PREDICT},
        }

        logger.info("[OLLAMA] Iniciando requisição")
        logger.debug(
            "[OLLAMA] Endpoint: %s | Modelo: %s | Timeout: %ss",
            self.url,
            self.model,
            self.timeout,
        )
        try:
            resposta = requests.post(self.url, json=dados, timeout=self.timeout)
            logger.info("[OLLAMA] Status HTTP: %s", resposta.status_code)
            resposta.raise_for_status()
            corpo = resposta.json()
            conteudo = corpo.get("response", "") if isinstance(corpo, dict) else ""
            if not isinstance(conteudo, str):
                conteudo = ""
            conteudo = conteudo.strip()
        except requests.exceptions.ConnectionError:
            logger.error("[OLLAMA][ERRO] Tipo: conexão recusada | Etapa: envio")
            self._desfazer_ultima_mensagem_usuario()
            return "Não foi possível conectar ao Ollama local."
        except requests.exceptions.Timeout:
            logger.error("[OLLAMA][ERRO] Tipo: timeout | Etapa: envio")
            self._desfazer_ultima_mensagem_usuario()
            return "A solicitação excedeu o tempo limite. Tente novamente."
        except requests.exceptions.HTTPError as exc:
            status = getattr(exc.response, "status_code", "desconhecido")
            corpo_erro = _texto_erro_ollama(exc.response)
            if status == 404 and "not found" in corpo_erro.lower():
                logger.error(
                    "[OLLAMA][ERRO] Tipo: modelo não encontrado | Modelo: %s | Etapa: resposta",
                    self.model,
                )
                self._desfazer_ultima_mensagem_usuario()
                return f"O modelo {self.model} não está instalado no Ollama."
            logger.error(
                "[OLLAMA][ERRO] Tipo: HTTP %s | Mensagem: %s | Etapa: resposta",
                status,
                corpo_erro or "sem detalhes",
            )
            self._desfazer_ultima_mensagem_usuario()
            return "O Ollama local está indisponível no momento."
        except requests.exceptions.RequestException:
            logger.error("[OLLAMA][ERRO] Tipo: requisição HTTP | Etapa: envio")
            self._desfazer_ultima_mensagem_usuario()
            return MENSAGEM_FALHA
        except (ValueError, TypeError, AttributeError):
            logger.error("[OLLAMA][ERRO] Tipo: JSON/resposta inválida | Etapa: parsing")
            self._desfazer_ultima_mensagem_usuario()
            return MENSAGEM_FALHA
        except Exception:
            logger.exception("[OLLAMA][ERRO] Tipo: inesperado | Etapa: processamento")
            self._desfazer_ultima_mensagem_usuario()
            return MENSAGEM_FALHA

        if not conteudo:
            logger.error("[OLLAMA][ERRO] Tipo: resposta vazia | Etapa: parsing")
            self._desfazer_ultima_mensagem_usuario()
            return MENSAGEM_FALHA

        self._historico.adicionar("assistant", conteudo)
        self._ultima_solicitacao_sucesso = True
        logger.info("[OLLAMA] Resposta recebida")
        return conteudo

    def _montar_prompt(self) -> str:
        partes = []
        for mensagem in self._historico.mensagens:
            role = mensagem["role"]
            content = mensagem["content"]
            if role == "system":
                partes.append(f"Instruções do sistema:\n{content}")
            elif role == "user":
                partes.append(f"Usuário: {content}")
            else:
                partes.append(f"AUTOWORK: {content}")
        return "\n\n".join(partes) + "\n\nAUTOWORK:"

    def _desfazer_ultima_mensagem_usuario(self) -> None:
        self._historico.remover_ultima_mensagem_usuario()


def _texto_erro_ollama(resposta: Any) -> str:
    try:
        corpo = resposta.json()
        if isinstance(corpo, dict):
            return str(corpo.get("error", ""))
    except (ValueError, TypeError, AttributeError):
        pass
    return str(getattr(resposta, "text", ""))[:300]
