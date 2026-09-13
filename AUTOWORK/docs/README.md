# AUTOWORK - Documentacao Tecnica

AUTOWORK e um assistente local para computador, escrito em Python, com foco em comandos por voz e texto. O codigo atual combina captura de audio, reconhecimento de fala, deteccao de wake word, interpretacao de intencoes, execucao de comandos locais, consultas informativas, conversa por IA, apresentacao por IA e uma interface HUD em terminal.

## Funcionalidades identificadas

- Execucao por voz via microfone, Google Speech Recognition e wake word.
- Execucao direta de texto com `python app.py --texto "frase"`.
- Loop sem HUD com `python app.py --terminal`.
- Interface HUD em Textual quando `app.py` e iniciado sem argumentos especiais.
- Abertura de aplicativos cadastrados por automacao de teclado com `pyautogui`.
- Abertura de sites cadastrados com `webbrowser`.
- Atalhos de janela e navegador com `pyautogui`.
- Consulta de horario, data, diferenca/conversao de horario, clima e localizacao.
- Conversa via OpenRouter usando o SDK `openai`.
- Apresentacao via Ollama local usando `requests`.
- TTS experimental via Kokoro em `modules/voz_teste`.
- Modulo independente de visao computacional em `teste_viso.py` usando OpenCV e MediaPipe.
- Instrumentacao de metricas em `metricas.py` e `rodar_metricas.py`.

## Tecnologias principais

Python 3.11 e indicado em `pyproject.toml`. As dependencias principais estao em `requirements.txt`: `SpeechRecognition`, `PyAudio`, `textual`, `pyautogui`, `psutil`, `openai`, `requests` e `tzdata`. O modulo experimental de voz possui dependencias proprias em `modules/voz_teste/requirements.txt`.

## Como iniciar

```powershell
python app.py
python app.py --terminal
python app.py --texto "abrir o chrome"
```

O comando padrao inicia a HUD. O modo `--terminal` usa microfone e terminal sem HUD. O modo `--texto` processa uma frase sem microfone nem interface.

## Documentos

- [Arquitetura](arquitetura.md)
- [Estrutura do projeto](estrutura-projeto.md)
- [Fluxo de execucao](fluxo-execucao.md)
- [Modulos Python](modulos.md)
- [Configuracao](configuracao.md)
- [Dependencias](dependencias.md)
- [Testes](testes.md)
- [Guia de desenvolvimento](desenvolvimento.md)

## Limites observados

A documentacao reflete o codigo existente. Quando um modulo aparenta ser experimental, legado, incompleto ou dependente de servico externo, isso e indicado explicitamente.
