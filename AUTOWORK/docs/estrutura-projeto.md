# Estrutura do projeto

A raiz analisada foi `C:\Users\Marco Antônio\Documents\Chat\AUTOWORK`.

## Pastas relevantes

- `audio/`: servicos de captura, reconhecimento, wake word e TTS.
- `comd_rapidos/`: acoes executaveis locais, incluindo apps, sites, janela e navegador.
- `conversa/`: chatbot baseado em OpenRouter e prompt de sistema.
- `core/`: estado e orquestrador do fluxo.
- `interface/`: saida de terminal e HUD Textual.
- `modules/`: modulos de informacao, dados locais e TTS experimental.
- `modules/dados/`: JSONs usados por localizacao, tempo e clima.
- `modules/voz_teste/`: laboratorio de TTS Kokoro integrado pela fachada `audio.tts`.
- `sistema_toke/`: pipeline deterministico de comandos.
- `sistema_toke/catalogo/`: catalogos de verbos, apps, sites e atalhos.
- `tests/`: testes pytest/unittest do fluxo principal e modulos.
- `.venv/`, `__pycache__/`, `.pytest_cache/`: artefatos gerados; nao foram tratados como codigo-fonte.

## Arquivos de configuracao e suporte

- `requirements.txt`: dependencias principais.
- `pyproject.toml`: configuracao de Black, Ruff, MyPy e pytest.
- `.gitignore`: ignora `.venv`, `.vscode`, caches Python, WAVs, outputs e `.env`.
- `autowork.spec`: especificacao PyInstaller com `app.py` como entrada e JSONs de `modules/dados` como dados empacotados.
- `hand_landmarker.task`: modelo MediaPipe usado por `teste_viso.py`.
- `.vscode/settings.json`: define gerenciador de ambiente Python da extensao.

## Arvore do projeto

```text
AUTOWORK/
├── _test_integracao.py
├── _test_normalizador.py
├── .gitignore
├── .vscode/
│   └── settings.json
├── app.py
├── apresent.py
├── audio/
│   ├── __init__.py
│   ├── captura.py
│   ├── reconhecimento.py
│   ├── tts.py
│   └── wake_word.py
├── autowork.spec
├── comd_rapidos/
│   ├── abrir_app.py
│   ├── abrir_site.py
│   ├── atalho_nav.py
│   └── atalhos.py
├── configui.py
├── conversa/
│   ├── __init__.py
│   ├── chatbot.py
│   └── prompt.py
├── core/
│   ├── __init__.py
│   ├── estados.py
│   └── orquestrador.py
├── dispatcher.py
├── estatisticas.py
├── fala.py
├── hand_landmarker.task
├── interface/
│   ├── __init__.py
│   ├── hud.py
│   └── terminal.py
├── interpretador.py
├── metricas.py
├── modules/
│   ├── __init__.py
│   ├── clima/
│   │   ├── __init__.py
│   │   └── clima.py
│   ├── dados/
│   │   ├── aliases.json
│   │   ├── capitais_internacionais.json
│   │   └── municipios_brasil.json
│   ├── localizacao/
│   │   ├── __init__.py
│   │   └── localizacao.py
│   ├── tempo/
│   │   ├── __init__.py
│   │   ├── datas.py
│   │   └── tempo.py
│   └── voz_teste/
│       ├── __init__.py
│       ├── config.py
│       ├── README.md
│       ├── requirements.txt
│       ├── teste_voz.py
│       └── tts.py
├── personalidade.py
├── pyproject.toml
├── requirements.txt
├── rodar_metricas.py
├── setup_dados.py
├── sistema_toke/
│   ├── catalogo/
│   │   ├── __init__.py
│   │   ├── catalogo_app.py
│   │   ├── catalogo_atalho.py
│   │   ├── catalogo_site.py
│   │   └── catalogo_verbo.py
│   ├── executor.py
│   ├── normalizador.py
│   ├── parser.py
│   └── resolvedor.py
├── teste_chat.py
├── teste_interface.py
├── teste_viso.py
└── tests/
    ├── test_captura.py
    ├── test_estados.py
    ├── test_fluxo.py
    ├── test_fluxo_apresentacao.py
    ├── test_integracao_fluxo.py
    ├── test_integracao_wake.py
    ├── test_interpretador.py
    ├── test_orquestrador.py
    ├── test_reconhecimento.py
    ├── test_tts.py
    ├── test_tudo.py
    └── test_wake_word.py
```
