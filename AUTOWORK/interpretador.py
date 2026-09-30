import json
import re
from typing import Any

from conversa.ollama import OLLAMA_MODEL, OLLAMA_URL

try:
    import requests
except ImportError: 
    requests = None


class InterpretadorComplexo:

    def __init__(self, modelo, url):
        modelo = OLLAMA_MODEL
        url = OLLAMA_URL

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
            "stream": False,
            "think": False,
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


def interpretar(texto: Any) -> dict[str, Any] | None:
    from filtro import filtrar, ResultadoFiltro

    if isinstance(texto, ResultadoFiltro):
        info_filtro = texto
    elif isinstance(texto, str):
        info_filtro = filtrar(texto)
    else:
        return _intencao("desconhecido", {}, tipo="desconhecido", confianca=0.0)

    texto_original = info_filtro.texto_original
    texto_filtrado = info_filtro.texto_filtrado

    if not texto_filtrado or not texto_filtrado.strip():
        return _intencao("desconhecido", {"texto_original": texto_original}, tipo="desconhecido", confianca=0.0)

    # Entrada ambígua / desconexa de STT detectada pelo filtro:
    if info_filtro.ambiguo and info_filtro.confianca <= 0.35:
        return {
            "tipo": "desconhecido",
            "acao": None,
            "intencao": None,
            "parametros": {"texto_original": texto_original},
            "confianca": info_filtro.confianca,
            "fala": "",
            "falar": True,
            "mensagem": "Não consegui compreender o comando, senhor.",
            "texto_original": texto_original,
            "texto_filtrado": texto_filtrado,
        }

    frase = re.sub(r"[?!.,;:]+", "", " ".join(texto_filtrado.lower().split()))

    if not info_filtro.eh_pergunta:
        try:
            from sist_comd_complex import detectar_comando_complexo, interpretar_comando_complexo

            # O filtro remove pontuação para os comandos simples, mas vírgulas
            # são delimitadores semânticos em listas de ações complexas. Use a
            # fala original quando ela contém esse marcador; o parser complexo
            # já remove wake word e normaliza o restante.
            texto_original_sem_wake = re.sub(
                r"^(?:autowork|auto-work|auto\s*work|work)\b[,\s:]*",
                "",
                texto_original,
                flags=re.IGNORECASE,
            ).strip()
            texto_complexo = (
                texto_original
                if "," in texto_original
                and re.match(
                    r"^(?:abra|abre|abrir|inicie|iniciar|execute|executar|rode|rodar|"
                    r"feche|fechar|fecha|minimize|minimizar|minimiza|mostre|mostrar)\b",
                    texto_original_sem_wake,
                    flags=re.IGNORECASE,
                )
                else texto_filtrado
            )
            if detectar_comando_complexo(texto_complexo):
                plano = interpretar_comando_complexo(texto_complexo)
                plano["texto_original"] = texto_original
                plano["texto_filtrado"] = texto_filtrado
                plano["intencao"] = "COMANDO_COMPLEXO"
                return plano
        except Exception as exc:
            import logging

            logging.getLogger(__name__).debug(
                "Falha ao detectar comando complexo: %s", exc
            )

    # Comando só vale quando a FRASE ORIGINAL/FILTRADA começa com verbo do catálogo
    # (ou é um comando fixo). Não usar o texto normalizado aqui: ele remove
    # "você/sabe/como" e transformaria perguntas em comandos.
    from sistema_toke.catalogo.catalogo_verbo import MAPA_VERBOS, PALAVRAS_DESCARTE
    from sistema_toke.normalizador import normalizar
    from sistema_toke.parser import parse
    from sistema_toke.resolvedor import resolver

    frase_comando = re.sub(r"^(por favor|favor)\s+", "", frase).strip()
    tokens_comando = frase_comando.split()
    while tokens_comando and tokens_comando[0] in PALAVRAS_DESCARTE:
        tokens_comando = tokens_comando[1:]
    comeca_com_verbo = bool(tokens_comando) and (
        tokens_comando[0] in MAPA_VERBOS
        or (len(tokens_comando) >= 2 and f"{tokens_comando[0]} {tokens_comando[1]}" in MAPA_VERBOS)
    )

    eh_clima = re.search(r"\b(clima|tempo|temperatura|chover|previsão|previsao)\b", frase)

    # 1. Tentativa deterministica. Perguntas que contem um pedido operacional
    # conhecido ("pode abrir o Codex?") tambem passam pelo parser; perguntas
    # sobre como executar algo continuam sendo conversa.
    comando = parse(texto_filtrado)
    resolvido_previo = resolver(comando) if comando else None
    pedido_operacional = _eh_pedido_operacional(
        frase,
        info_filtro.eh_pergunta,
        comando,
        resolvido_previo,
    )
    if comando and not eh_clima and (comeca_com_verbo or comando.get("pronto") or pedido_operacional):
            # Hora/data são tratadas pelo módulo de tempo, não pelo executor.
            if comando.get("acao") == "informar_hora":
                return _intencao("consultar_horario", {"local": _extrair_local(frase), "texto_original": texto_original}, tipo="hora")
            if comando.get("acao") == "informar_data":
                return _intencao("consultar_data", {"expressao": "hoje", "local": _extrair_local(frase), "texto_original": texto_original}, tipo="hora")

            resolvido = resolvido_previo
            if resolvido:
                params = dict(resolvido.get("parametros", {}))
                return {
                    "tipo": "comando",
                    "acao": resolvido["acao"],
                    "intencao": resolvido["acao"].upper(),
                    "parametros": params,
                    "confianca": 0.99,
                    "fala": "",
                    "falar": False,
                    "texto_original": texto_original,
                    "texto_filtrado": texto_filtrado,
                }

            # Parser determinístico não conseguiu resolver o alvo diretamente.
            # Consulta a IA Local antes de declarar o comando como não resolvido.
            try:
                from sistema_toke.resolvedor_ia import interpretar_com_ia
                intencao_ia = interpretar_com_ia(texto_filtrado)
                if intencao_ia is not None:
                    intencao_ia["texto_original"] = texto_original
                    intencao_ia["texto_filtrado"] = texto_filtrado
                    intencao_ia["intencao"] = intencao_ia.get("acao", "").upper()
                    return intencao_ia
            except Exception as exc:
                import logging
                logging.getLogger(__name__).debug("Falha no fallback do resolvedor IA: %s", exc)

            # Parser reconheceu a ação, mas o alvo não existe (app/site desconhecido).
            return {
                "tipo": "comando",
                "acao": comando.get("acao", ""),
                "intencao": comando.get("acao", "").upper(),
                "parametros": {"alvo": comando.get("alvo"), "texto_original": texto_original},
                "confianca": 0.6,
                "fala": "",
                "falar": False,
                "resolvido": False,
                "texto_original": texto_original,
                "texto_filtrado": texto_filtrado,
            }

    # 2. Clima
    if re.search(r"\b(clima|tempo|temperatura|chover|previsão|previsao)\b", frase):
        data_match = re.search(r"\b(hoje|amanhã|amanha|ontem|daqui a \d+ dias?|daqui a uma semana|próxima \w+(?:-feira)?|proxima \w+(?:-feira)?)\b", frase)
        data = data_match.group(1) if data_match else "hoje"

        frase_sem_data = re.sub(r"\b(hoje|amanhã|amanha|ontem|daqui a \d+ dias?|daqui a uma semana|próxima \w+(?:-feira)?|proxima \w+(?:-feira)?)\b", "", frase).strip()
        local_match = re.search(r"\b(?:em|no|na|para|de)\s+(.+)$", frase_sem_data)
        local = local_match.group(1).strip() if local_match else "São Paulo"

        return _intencao("consultar_clima", {"local": local, "data": data, "texto_original": texto_original}, tipo="clima")

    # 3. Hora / Data (módulo de tempo)
    # Diferença de Horário
    if re.search(r"\b(diferença|diferenca)\b.*\bhorário\b", frase):
        partes = re.search(r"entre\s+(.+?)\s+e\s+(.+)$", frase)
        return _intencao("diferenca_horario", {
            "origem": partes.group(1).strip() if partes else "Brasil",
            "destino": partes.group(2).strip() if partes else "Japão",
            "texto_original": texto_original,
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
            "texto_original": texto_original,
        }, tipo="hora")

    # Consultar Data
    if re.search(r"\b(data|dia)\b", frase):
        expressao_match = re.search(r"\b(hoje|amanhã|amanha|ontem|daqui a \d+ dias?|daqui a uma semana|próxima \w+(?:-feira)?|proxima \w+(?:-feira)?)\b", frase)
        expressao = expressao_match.group(1) if expressao_match else "hoje"

        local_match = re.search(r"\b(?:em|no|na)\s+(.+)$", re.sub(r"\b(hoje|amanhã|amanha|ontem)\b", "", frase))
        local = local_match.group(1).strip() if local_match else "Brasil"

        return _intencao("consultar_data", {"expressao": expressao, "local": local, "texto_original": texto_original}, tipo="hora")

    # Consultar Horário
    if re.search(r"\b(hora|horas|horário|horario)\b", frase):
        return _intencao("consultar_horario", {"local": _extrair_local(frase), "texto_original": texto_original}, tipo="hora")

    # Localização do usuário ("onde estou?") — o módulo não recebe parâmetros.
    if re.search(
        r"\b(onde (eu )?estou|minha localiza(ç|c)(ã|a)o"
        r"|em que (cidade|pa(í|i)s|lugar|estado) (eu )?estou)\b",
        frase,
    ):
        return _intencao("consultar_localizacao", {"texto_original": texto_original}, tipo="informacao")

    # 4. Apresentação do AUTOWORK — apenas pedidos explícitos de apresentação.
    #    Perguntas de identidade/capacidade ("quem é você?", "o que você
    #    pode fazer?") ficam para o chatbot, que conhece o AUTOWORK.
    if re.search(
        r"\b(se apresente?|se apresenta|se apresentar"
        r"|o que (é|e) o (autowork|projeto)"
        r"|(me )?explique o (projeto|autowork)"
        r"|fale sobre o autowork)\b",
        frase,
    ):
        return _intencao("apresentar", {"texto_original": texto_original}, tipo="apresentacao")

    # 5. Fallback com IA Local (Ollama) para comandos em linguagem natural
    #    Acionado somente quando o sistema determinístico não identificou o comando.
    #    Perguntas de conversa ("você sabe...", "o que significa...", "quem é...", etc.)
    #    seguem diretamente para a conversa.
    eh_pergunta_conversa = info_filtro.eh_pergunta or bool(
        re.search(
            r"\b(voc[eê]|vc)\s+(sabe|consegue|pode)\b"
            r"|^(como|o que significa|por que|porque|qual|quem|quando|quanto)\b"
            r"|\b(piada|sentido da vida|me conte|conte|explique|o que [ée])\b",
            frase,
        )
    )

    if not eh_pergunta_conversa:
        try:
            from sistema_toke.resolvedor_ia import interpretar_com_ia
            intencao_ia = interpretar_com_ia(texto_filtrado)
            if intencao_ia is not None:
                intencao_ia["texto_original"] = texto_original
                intencao_ia["texto_filtrado"] = texto_filtrado
                intencao_ia["intencao"] = intencao_ia.get("acao", "").upper()
                return intencao_ia
        except Exception as exc:
            import logging
            logging.getLogger(__name__).debug("Falha no fallback do resolvedor IA: %s", exc)

    # 6. Conversa (fallback para o chatbot)
    return {
        "tipo": "conversa",
        "acao": "chat",
        "intencao": None,
        "parametros": {"texto_original": texto_original, "texto_filtrado": texto_filtrado},
        "confianca": 0.5,
        "fala": "",
        "falar": True,
        "texto_original": texto_original,
        "texto_filtrado": texto_filtrado,
    }


def _eh_pedido_operacional(
    frase: str,
    eh_pergunta: bool,
    comando: dict[str, Any] | None,
    resolvido: dict[str, Any] | None,
) -> bool:
    """Distingue pedido operacional em forma de pergunta de conversa."""
    if not comando or not resolvido:
        return False
    if not eh_pergunta:
        return True

    # "voce sabe como abrir..." e "como eu abro..." pedem explicacao.
    if re.search(
        r"^(?:voc[eê]|vc)\s+sabe\b"
        r"|^(?:voc[eê]|vc)\s+(?:consegue|pode)\s+(?:me\s+)?(?:explicar|dizer|ensinar|falar|contar)\b"
        r"|^como\s+(?:eu\s+)?(?:abro|fa[cç]o|posso)\b"
        r"|^(?:o que|qual|quem|por que|porque|quando|onde|quanto)\b",
        frase,
    ):
        return False

    # Formas interrogativas de cortesia sao comandos quando o alvo foi
    # resolvido pelo catalogo: "pode abrir o Codex?".
    return bool(re.search(
        r"^(?:pode|poderia|consegue|ser[aá]\s+que\s+pode|ser[aá]\s+que\s+consegue)\b",
        frase,
    )) or bool(re.search(r"\b(?:abra|abre|abrir|inicie|iniciar|execute|rod[ae]|pesquise|pesquisar)\b", frase))


def _extrair_local(frase: str) -> str:
    local_match = re.search(r"\b(?:em|no|na|nos|nas|de|do|da|dos|das)\s+(.+)$", frase)
    return local_match.group(1).strip() if local_match else "Brasil"


def _intencao(
    acao: str,
    parametros: dict[str, Any],
    tipo: str = "informacao",
    confianca: float = 0.95,
    falar: bool = True,
) -> dict[str, Any]:
    return {"tipo": tipo, "acao": acao, "parametros": parametros,
            "confianca": confianca, "fala": "", "falar": falar}
