import requests


class Apresentador:

    def __init__(
        self,
        modelo="qwen2.5:3b",
        url="http://localhost:11434/api/generate"
    ):
        self.modelo = modelo
        self.url = url

    def apresentar(self, texto):

        prompt = f"""
Você é o AUTOWORK, um assistente inteligente de automação.

Sua tarefa é responder naturalmente ao usuário quando ele quiser
saber quem você é ou quando precisar se apresentar.

Regras:
- Fale em português do Brasil.
- Seja natural.
- Seja educado e formal, mas não robótico.
- Não use sempre a mesma estrutura de resposta.
- Varie a forma de se apresentar.
- Explique brevemente quem é o AUTOWORK.
- Não invente funções que o sistema não possui.
- Responda somente com a fala que será apresentada ao usuário.

Mensagem do usuário:
{texto}
"""

        dados = {
            "model": self.modelo,
            "prompt": prompt,
            "stream": False
        }

        try:
            resposta = requests.post(
                self.url,
                json=dados,
                timeout=60
            )

            resposta.raise_for_status()

            resposta_aprest = resposta.json()

            return resposta_aprest.get("response", "").strip()

        except requests.RequestException as erro:
            print(f"Erro ao comunicar com o Ollama: {erro}")
            return None

        except Exception as erro:
            print(f"Erro inesperado no apresentador: {erro}")
            return None