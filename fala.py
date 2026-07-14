import speech_recognition as sr
import time

import logging
import requests
import json

from voz import Voz


recognizer = sr.Recognizer()

recognizer.energy_threshold = 260
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 2.5
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.5


def cap_audio():
    with sr.Microphone() as microfone:
        print("Pode falar...")
        audio = recognizer.listen(microfone)
        return audio


def trans_audio(audio):
    try:
        texto = recognizer.recognize_google(audio, language="pt-BR")
        return texto.lower()

    except sr.UnknownValueError:
        print("Não consegui entender.")
        return None

    except sr.RequestError:
        print("Erro ao conectar ao serviço do Google.")
        return None


URL = "http://localhost:11434/api/generate"
MODELO = "qwen2.5:3b"


def prompt_ia(texto: str) -> str:

    return f"""
Você é o interpretador de comandos do AUTOWORK.

Sua única função é interpretar a frase do usuário e retornar SOMENTE um JSON válido.

Não escreva explicações.
Não escreva comentários.
Não utilize Markdown.
Não escreva texto antes ou depois do JSON.

O JSON deve ser válido para ser processado diretamente com json.loads() em Python.

Formato obrigatório:

{{
    "acao": "",
    "parametros": {{}},
    "confirmacao": false,
    "confianca": 0.0,
    "fala": ""
}}

Descrição dos campos:

- acao: ação que será executada pelo AUTOWORK.
- parametros: parâmetros necessários para executar a ação.
- confirmacao: true apenas para ações perigosas.
- confianca: número entre 0.0 e 1.0.
- fala: mensagem que será enviada para o módulo voz.py.

Regras para o campo "fala":

- Deve conter apenas a mensagem que o assistente irá falar, com estilo despojado .
- Deve ser curta, natural e profissional.
- Não mencione JSON.
- Não descreva o formato da resposta.
- Não explique seu raciocínio.
- Varie as respostas para não parecer repetitivo.
- A mensagem deve corresponder exatamente à ação identificada.
- Caso a ação exija confirmação, a mensagem deve solicitar essa confirmação.
- Caso o comando não seja compreendido, peça educadamente para o usuário repetir.

Caso não consiga interpretar o comando, retorne:

{{
    "acao": "desconhecida",
    "parametros": {{}},
    "confirmacao": false,
    "confianca": 0.0,
    "fala": "Desculpe, não consegui entender o comando. Pode repetir de outra forma?"
}}

Exemplos

Usuário:
Abra o Chrome

Resposta:

{{
    "acao": "abrir_app",
    "parametros": {{
        "nome": "chrome"
    }},
    "confirmacao": false,
    "confianca": 0.98,
    "fala": "Claro. Abrindo o Google Chrome."
}}

Usuário:
Feche o Chrome

Resposta:

{{
    "acao": "fechar_app",
    "parametros": {{
        "nome": "chrome"
    }},
    "confirmacao": false,
    "confianca": 0.98,
    "fala": "Tudo certo. Fechando o Google Chrome."
}}

Usuário:
Desligue o computador

Resposta:

{{
    "acao": "desligar_pc",
    "parametros": {{}},
    "confirmacao": true,
    "confianca": 0.99,
    "fala": "Essa ação requer confirmação. Deseja realmente desligar o computador?"
}}

Agora interprete a frase abaixo.

Usuário:
{texto}

Resposta:
""" .strip()

comando_fechar = [
    "fechar",
    "encerrar",
    "desligar"
]

while True:


    audio = cap_audio()

    texto = trans_audio(audio)

    if texto is None:
        continue

    print(f"Você disse: {texto}")

    if texto in comando_fechar:
        print("Encerrando...")
        break


    dados = {
        "model": MODELO,
        "prompt": prompt_ia(texto),
        "stream": False,
        "options": {"temperature": 0.0, "top_p": 0.1},
    }

    try:
        resposta_ia = requests.post(URL, json=dados, timeout=60)
        if not resposta_ia.ok:
            print("Erro ao chamar IA local (HTTP):", resposta_ia.status_code)
            print("Detalhes:", resposta_ia.text)
            continue

        payload = resposta_ia.json()
        texto_resposta = (payload.get("response") or "").strip()

        try:
            comando = json.loads(texto_resposta)
            print("Resposta IA (JSON):", comando)
        except json.JSONDecodeError:
            print("Resposta IA (texto não-JSON):", texto_resposta)
            continue

        # Integração com voz.py (falando ação prevista e confirmação pós-execução)
        voz = Voz()

        try:
            fala_para_usuario = (comando.get("fala") or "").strip() if isinstance(comando, dict) else ""
        except Exception:
            fala_para_usuario = ""

        if fala_para_usuario:
            try:
                voz.falar(fala_para_usuario)
            except Exception as e:
                print("Erro ao falar (voz.py):", e)

        try:
            from ia import executar_comando

            confirmacao = executar_comando(comando)
            mensagem_final = ""
            try:
                if isinstance(confirmacao, dict):
                    mensagem_final = (confirmacao.get("mensagem") or "").strip()
            except Exception:
                mensagem_final = ""

            if mensagem_final:
                voz.falar(mensagem_final)
        except Exception as e:
            print("Erro ao executar comando em ia.py:", e)



    except Exception as e:
        print("Erro ao chamar IA local:", e)

    time.sleep(0.5)



