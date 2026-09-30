import logging
import requests

from conversa.ollama import OLLAMA_MODEL, OLLAMA_NUM_PREDICT, OLLAMA_TIMEOUT, OLLAMA_URL

logger = logging.getLogger(__name__)

MENSAGEM_APRESENTACAO_FALLBACK = (
    "Olá! Eu sou o AUTOWORK, seu assistente pessoal de automação no Windows. "
    "Posso abrir e fechar aplicativos, gerenciar abas e janelas, consultar previsão do tempo, "
    "informar horas e datas, e auxiliar nas suas tarefas diárias."
)


class Apresentador:

    def __init__(
        self,
        modelo=OLLAMA_MODEL,
        url=OLLAMA_URL,
        timeout: float = OLLAMA_TIMEOUT,
    ):
        self.modelo = modelo
        self.url = url
        self.timeout = timeout

    def apresentar(self, texto):

        prompt = f"""
Você é o AUTOWORK, um assistente inteligente de automação.

Sua tarefa é responder naturalmente ao usuário quando ele quiser
saber quem você é ou quando precisar se apresentar que é um chatbot capaz de abrir 
programas e fechar programas entre outras funçõees com atalhos de desktop e de navegadores,
ver o clima, responder perguntas entre outros.

Regras:
- Fale em português do Brasil.
- Seja natural.
- Seja educado e formal, mas não robótico.
- Não use sempre a mesma estrutura de resposta.
- Varie a forma de se apresentar.
- Explique brevemente quem é o AUTOWORK.
- Responda somente com a fala que será apresentada ao usuário.

Mensagem do usuário:
{texto}
"""

        dados = {
            "model": self.modelo,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"num_predict": OLLAMA_NUM_PREDICT},
        }

        try:
            resposta = requests.post(
                self.url,
                json=dados,
                timeout=self.timeout
            )

            resposta.raise_for_status()

            resposta_aprest = resposta.json()

            texto_resposta = resposta_aprest.get("response", "").strip()
            return texto_resposta if texto_resposta else MENSAGEM_APRESENTACAO_FALLBACK

        except requests.RequestException as erro:
            logger.warning("Ollama não respondeu a tempo para apresentação (%s). Usando apresentação padrão.", erro)
            return MENSAGEM_APRESENTACAO_FALLBACK

        except Exception as erro:
            logger.exception("Erro inesperado no apresentador: %s. Usando apresentação padrão.", erro)
            return MENSAGEM_APRESENTACAO_FALLBACK
