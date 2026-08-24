import ollama
import json
import requests


class InterpretadorComplexo:

    def __init__(self, modelo, url):
        modelo = "qwen2.5:3b"
        url = "http://localhost:11434/api/generate"

        self.modelo = modelo
        self.url = url

    def interpretar(self, texto):

        prompt = f"""
        Você é o Interpretador de Comandos e Chatbot do AUTOWORK.

        Objetivo:
        Diferenciar comandos normais de conversas e assim enviar para os módulos
        citados: normalizador.py e chatbot.py.

        Regras:
        - Retorne somente JSON válido.
        - Não escreva texto fora do JSON.
        - Use somente os comandos fornecidos.
        - Nunca invente comandos.
        - Se não souber identificar, use tipo "desconhecido".
        - Não execute comandos.
        - Responda em português.

        Formato obrigatório:

        {{
            "tipo": "comando | conversa | desconhecido",
            "acao": "",
            "parametros": {{}},
            "confianca": 0.0,
            "fala": ""
        }}

        Comandos disponíveis:

        Exemplo de comando:

        Usuário: usa palavras com (faça, abra, inicie ou fecha...)

        Resposta:

        {{
            "tipo": "comando",
            "acao": "normalizado.py",
            "parametros": {{
                "texto_original": "{texto}"
            }},
            "confianca": 0.99,
            "fala": "Abrindo o Chrome."
        }}

        Exemplo de conversa:

        Usuário:

        "Você sabe como abrir o Chrome?"

        Resposta:

        {{
            "tipo": "conversa",
            "acao": "chatbot.py",
            "parametros": {{}},
            "confianca": 0.97,
            "fala": "Sim. Posso explicar como abrir o Chrome."
        }}

        Mensagem do usuário: {texto}
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

            resultado = resposta.json()

            return resultado

        except requests.exceptions.ConnectionError:
            print("Erro: não foi possível conectar ao Ollama.")

        except requests.exceptions.Timeout:
            print("Erro: o Ollama demorou muito para responder.")

        except requests.exceptions.HTTPError as erro:
            print(f"Erro HTTP: {erro}")

        except requests.exceptions.RequestException as erro:
            print(f"Erro na requisição: {erro}")

        except json.JSONDecodeError:
            print("Erro: a resposta do Ollama não é um JSON válido.")

        except Exception as erro:
            print(f"Erro inesperado: {erro}")
