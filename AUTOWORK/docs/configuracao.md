# Configuracao

## Arquivos de configuracao

- `requirements.txt`: dependencias principais. O bloco Kokoro esta comentado, indicando instalacao manual recomendada para TTS experimental.
- `pyproject.toml`: configura Black, Ruff, MyPy e pytest.
- `.gitignore`: ignora `.venv`, `.vscode`, caches Python, WAVs, outputs e `.env`.
- `autowork.spec`: arquivo PyInstaller com entrada `app.py`, dados `modules/dados/*.json` e hidden imports de audio/numericos.
- `.vscode/settings.json`: define `python-envs.defaultEnvManager` como `ms-python.python:system`.

## Variaveis de ambiente

### Chat/OpenRouter

`conversa/chatbot.py` procura a chave nesta ordem:

1. constante `OPENROUTER_API_KEY`, se nao for placeholder;
2. variavel de ambiente `OPENROUTER_API_KEY`;
3. variavel de ambiente `CHAVE_API_CHAT`;
4. arquivo `.env` na raiz;
5. arquivo `.venv/.env`.

Exemplo seguro:

```text
OPENROUTER_API_KEY=sua_chave_aqui
```

Nao versione `.env`; ele ja esta no `.gitignore`.

### Metricas

`metricas.py` usa:

```text
AUTOWORK_PROFILING=1
AUTOWORK_METRICAS_IMPRIMIR=1
AUTOWORK_METRICAS_FALA=1
```

Essas flags ativam ciclo de metricas, impressao de relatorio e fala do relatorio.

## Modelos e URLs

- OpenRouter: `https://openrouter.ai/api/v1`.
- Modelo OpenRouter: `openrouter/free`.
- Ollama local: `http://localhost:11434/api/generate`.
- Modelo Ollama: `qwen2.5:3b`.
- Kokoro: `hexgrad/Kokoro-82M`.
- MediaPipe vision: `MODEL_URL` em `teste_viso.py`, baixado para `hand_landmarker.task`.

## TTS Kokoro/eSpeak

`modules/voz_teste/config.py` define `LANG_CODE = "p"`, `VOICE = "pm_santa"`, `SPEED = 0.85`, `SAMPLE_RATE = 24000` e `ESPEAK_DIR = C:\Program Files\eSpeak NG`. O codigo valida `LANG_CODE == "p"` e exige que a voz esteja em `VOZES_PT_BR`.

## Dados locais

`modules/localizacao/localizacao.py` carrega `modules/dados/aliases.json`, `capitais_internacionais.json` e `municipios_brasil.json`. `setup_dados.py` pode regenerar municipios usando API do IBGE, mas o caminho de saida esta hardcoded para a pasta local do autor.

## Cuidados com credenciais

Nenhuma credencial real deve ser copiada para documentacao ou commits. Use `.env` com placeholders como `OPENROUTER_API_KEY=sua_chave_aqui`.
