import json
import re
from typing import Any

try:
    import requests
except ImportError: 
    requests = None


class InterpretadorComplexo:

    def __init__(self, modelo, url):
        modelo = "qwen2.5:3b"
        url = "http://localhost:11434/api/generate"

        self.modelo = modelo
        self.url = url

    def interpretar(self, texto):
        if requests is None:
            raise RuntimeError("A dependência requests é necessária para o interpretador Ollama.")

        prompt = f"""
        Você é o Interpretador de Comandos e Chatbot do AUTOWORK.

        Objetivo:
        Diferenciar comandos normais de conversas ou de perguntas de apresentação do projeto e assim enviar para os módulos
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
            "tipo": "comando | conversa | apresentação |  desconhecido ",
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
        Exemplo de pergunta de apresentação:

        Usuário:

        "Quem você?"

        Resposta:

        {{
            "tipo": "apresentação",
            "acao": "chatbot.py",
            "parametros": {{}},
            "confianca": 0.97,
            "fala": "Eu sou um assistente."
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


def interpretar(texto: str) -> dict[str, Any] | None:

    if not texto or not texto.strip():
        return _intencao("desconhecido", {}, tipo="desconhecido", confianca=0.0)

    frase = re.sub(r"[?!.,;:]+", "", " ".join(texto.lower().split()))

    # Comando só vale quando a FRASE ORIGINAL começa com verbo do catálogo
    # (ou é um comando fixo). Não usar o texto normalizado aqui: ele remove
    # "você/sabe/como" e transformaria perguntas em comandos.
    from sistema_toke.catalogo.catalogo_verbo import MAPA_VERBOS
    from sistema_toke.normalizador import normalizar
    from sistema_toke.parser import parse
    from sistema_toke.resolvedor import resolver

    frase_comando = re.sub(r"^(por favor|favor)\s+", "", frase).strip()
    tokens_comando = frase_comando.split()
    comeca_com_verbo = bool(tokens_comando) and (
        tokens_comando[0] in MAPA_VERBOS
        or (len(tokens_comando) >= 2 and f"{tokens_comando[0]} {tokens_comando[1]}" in MAPA_VERBOS)
    )

    eh_clima = re.search(r"\b(clima|tempo|temperatura|chover|previsão|previsao)\b", frase)

    comando = parse(texto)
    if comando and not eh_clima and (comeca_com_verbo or comando.get("pronto")):
        # Hora/data são tratadas pelo módulo de tempo, não pelo executor.
        if comando.get("acao") == "informar_hora":
            return _intencao("consultar_horario", {"local": _extrair_local(frase)}, tipo="hora")
        if comando.get("acao") == "informar_data":
            return _intencao("consultar_data", {"expressao": "hoje", "local": _extrair_local(frase)}, tipo="hora")

        resolvido = resolver(comando)
        if resolvido:
            return {
                "tipo": "comando",
                "acao": resolvido["acao"],
                "parametros": dict(resolvido.get("parametros", {})),
                "confianca": 0.99,
                "fala": "",
            }

        # Parser reconheceu a ação, mas o alvo não existe (app/site desconhecido).
        return {
            "tipo": "comando",
            "acao": comando.get("acao", ""),
            "parametros": {"alvo": comando.get("alvo"), "texto_original": texto},
            "confianca": 0.6,
            "fala": "",
            "resolvido": False,
        }

    # 2. Clima
    if re.search(r"\b(clima|tempo|temperatura|chover|previsão|previsao)\b", frase):
        data_match = re.search(r"\b(hoje|amanhã|amanha|ontem|daqui a \d+ dias?|daqui a uma semana|próxima \w+(?:-feira)?|proxima \w+(?:-feira)?)\b", frase)
        data = data_match.group(1) if data_match else "hoje"

        frase_sem_data = re.sub(r"\b(hoje|amanhã|amanha|ontem|daqui a \d+ dias?|daqui a uma semana|próxima \w+(?:-feira)?|proxima \w+(?:-feira)?)\b", "", frase).strip()
        local_match = re.search(r"\b(?:em|no|na|para|de)\s+(.+)$", frase_sem_data)
        local = local_match.group(1).strip() if local_match else "São Paulo"

        return _intencao("consultar_clima", {"local": local, "data": data}, tipo="clima")

    # 3. Hora / Data (módulo de tempo)
    # Diferença de Horário
    if re.search(r"\b(diferença|diferenca)\b.*\bhorário\b", frase):
        partes = re.search(r"entre\s+(.+?)\s+e\s+(.+)$", frase)
        return _intencao("diferenca_horario", {
            "origem": partes.group(1).strip() if partes else "Brasil",
            "destino": partes.group(2).strip() if partes else "Japão",
        }, tipo="hora")

    # Conversão de Horário
    conversao = re.search(
        r"converta\s+(\d{1,2}(?::\d{2})?)\s+horas?\s+d[aoe]\s+(.+?)\s+para\s+(.+)$",
        frase,
    )
    if conversao:
        destino = re.sub(r"^o horário do |^o horario do |^as ", "", conversao.group(3))
        return _intencao("converter_horario", {
            "hora": conversao.group(1), "origem": conversao.group(2).strip(), "destino": destino.strip(),
        }, tipo="hora")

    # Consultar Data
    if re.search(r"\b(data|dia)\b", frase):
        expressao_match = re.search(r"\b(hoje|amanhã|amanha|ontem|daqui a \d+ dias?|daqui a uma semana|próxima \w+(?:-feira)?|proxima \w+(?:-feira)?)\b", frase)
        expressao = expressao_match.group(1) if expressao_match else "hoje"

        local_match = re.search(r"\b(?:em|no|na)\s+(.+)$", re.sub(r"\b(hoje|amanhã|amanha|ontem)\b", "", frase))
        local = local_match.group(1).strip() if local_match else "Brasil"

        return _intencao("consultar_data", {"expressao": expressao, "local": local}, tipo="hora")

    # Consultar Horário
    if re.search(r"\b(hora|horas|horário|horario)\b", frase):
        return _intencao("consultar_horario", {"local": _extrair_local(frase)}, tipo="hora")

    # 4. Apresentação do AUTOWORK (limitada ao projeto, para não capturar
    #    pedidos genéricos de explicação, que vão para o chatbot)
    if re.search(
        r"\b(se apresente?|se apresenta|quem (é|e) (você|voce)"
        r"|o que (é|e) o (autowork|projeto)"
        r"|o que (você |voce )?(faz|consegue fazer)"
        r"|(me )?explique o (projeto|autowork)"
        r"|fale sobre o autowork)\b",
        frase,
    ):
        return _intencao("apresentar", {"texto_original": texto}, tipo="apresentacao")

    # 5. Conversa (fallback para o chatbot)
    return {
        "tipo": "conversa",
        "acao": "chat",
        "parametros": {"texto_original": texto},
        "confianca": 0.5,
        "fala": "",
    }


def _extrair_local(frase: str) -> str:
    local_match = re.search(r"\b(?:em|no|na)\s+(.+)$", frase)
    return local_match.group(1).strip() if local_match else "Brasil"


def _intencao(
    acao: str,
    parametros: dict[str, Any],
    tipo: str = "informacao",
    confianca: float = 0.95,
) -> dict[str, Any]:
    return {"tipo": tipo, "acao": acao, "parametros": parametros,
            "confianca": confianca, "fala": ""}
