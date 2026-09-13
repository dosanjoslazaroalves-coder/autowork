# Dependencias

## Dependencias principais de `requirements.txt`

| Dependencia | Finalidade | Onde aparece | Obrigatoriedade observada |
|---|---|---|---|
| `SpeechRecognition` | Captura/STT via `Recognizer`, `Microphone`, `AudioData` e Google Speech | `audio/captura.py`, `audio/reconhecimento.py`, testes | Obrigatoria para fluxo de voz |
| `PyAudio` | Backend de microfone para `SpeechRecognition.Microphone` | requisito indireto da captura | Obrigatoria para microfone local |
| `textual` | HUD no terminal | `interface/hud.py`, `teste_interface.py` | Obrigatoria para modo HUD |
| `pyautogui` | Atalhos e abertura de apps | `comd_rapidos/*` | Obrigatoria para comandos locais reais |
| `psutil` | RSS/CPU em metricas | `metricas.py` | Opcional; codigo trata ausencia |
| `openai` | Cliente OpenRouter | `conversa/chatbot.py` | Obrigatoria para conversa por IA |
| `requests` | HTTP para Ollama e IBGE | `apresent.py`, `interpretador.py`, `setup_dados.py` | Obrigatoria para apresentacao/setup; opcional em `InterpretadorComplexo` ate ser usado |
| `tzdata` | Base IANA de timezone em ambientes que precisem | `modules/tempo` via `zoneinfo` | Recomendado para fusos |

## Dependencias comentadas no `requirements.txt`

O arquivo principal lista como instalacao manual recomendada: `kokoro`, `torch`, `sounddevice`, `numpy`, `scipy`, `misaki`, `phonemizer-fork`, `espeakng-loader`. Elas sao exigidas pelo modulo experimental `modules/voz_teste` e parcialmente por `audio.tts.falar_com_niveis`.

## Dependencias de `modules/voz_teste/requirements.txt`

| Dependencia | Finalidade |
|---|---|
| `kokoro` | Motor de TTS |
| `misaki` | Fonemizacao usada pelo Kokoro |
| `phonemizer-fork` | Integracao com eSpeak |
| `espeakng-loader` | Suporte eSpeak NG |
| `torch` | Runtime do modelo |
| `sounddevice` | Reproducao de audio |
| `numpy` | Arrays e processamento de audio |
| `scipy` | Escrita de WAV em `salvar_audio` |

## Dependencias importadas mas ausentes do `requirements.txt` principal

- `cv2`/OpenCV e `mediapipe`: usados por `teste_viso.py`.
- `rich`: usado por `interface/hud.py`, normalmente instalado como dependencia de `textual`, mas nao listado diretamente.
- `pytest`: usado em testes, mas nao listado em `requirements.txt`.

## Servicos externos

| Servico | Uso | Modulo |
|---|---|---|
| Google Speech Recognition | STT via `recognize_google` | `audio/reconhecimento.py` |
| OpenRouter | conversa por IA via API compativel com OpenAI | `conversa/chatbot.py` |
| Ollama local | apresentacao e `InterpretadorComplexo` | `apresent.py`, `interpretador.py` |
| ip-api.com | localizacao aproximada por IP | `modules/localizacao/localizacao.py` |
| Nominatim/OpenStreetMap | geocodificacao de municipios brasileiros | `modules/localizacao/localizacao.py` |
| Open-Meteo | clima atual e previsao | `modules/clima/clima.py` |
| IBGE | geracao da base de municipios | `setup_dados.py` |
| Hugging Face Hub | download/carregamento do modelo Kokoro | `modules/voz_teste/tts.py` |
| Google Cloud Storage | download do modelo MediaPipe | `teste_viso.py` |
