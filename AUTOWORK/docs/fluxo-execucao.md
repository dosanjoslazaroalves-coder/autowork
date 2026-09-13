# Fluxo de execucao

## Inicializacao por `app.py`

```text
main()
  -> _analisar_argumentos()
  -> _configurar_logging()
  -> modo --texto, --terminal ou HUD
```

No modo padrao, `app.py` cria `PonteInterface`, constroi `Orquestrador` e inicia `interface.hud.HUD`. A HUD roda na thread principal; o pipeline de audio roda em thread separada criada por `HUD.executar()`.

## Loop de voz real

```text
Inicializacao
  -> ServicoCaptura.calibrar()
  -> Estado.IDLE
  -> Estado.OUVINDO
  -> captura de audio
  -> Estado.TRANSCREVENDO
  -> recognize_google(language="pt-BR")
  -> Estado.DETECTANDO_WAKE
  -> detectar wake word
  -> Estado.PROCESSANDO
  -> interpretador.interpretar()
  -> comando local ou dispatcher
  -> resultado estruturado
  -> TTS se politica permitir
  -> Estado.SUCESSO ou Estado.ERRO
  -> Estado.IDLE
```

## Caminhos alternativos

- Sem fala capturada: `ServicoCaptura.capturar()` retorna `None` em `WaitTimeoutError`; o orquestrador volta para `Estado.IDLE` sem STT e sem fala.
- Fala nao compreendida/falha de STT: `ServicoReconhecimento.transcrever()` retorna `None` para `UnknownValueError`, `RequestError` ou audio ausente; o ciclo volta para `IDLE`.
- Sem wake word: `audio.wake_word.detectar()` retorna `(False, "")`; a frase e ignorada.
- Encerramento: depois de remover a wake word, comandos exatamente `fechar`, `encerrar` ou `desligar` falam uma mensagem de encerramento, mudam para `Estado.ENCERRANDO` e param o loop.
- Comando local reconhecido: `interpretador -> parser -> resolvedor -> executor -> comd_rapidos`.
- Comando local nao resolvido: o interpretador retorna `resolvido=False`; o orquestrador devolve `status="falha"` com mensagem curta.
- Clima/hora/data/localizacao: o interpretador classifica por regex e `dispatcher.dispatch()` chama `modules.tempo`, `modules.clima` ou `modules.localizacao`.
- Apresentacao: `dispatcher._apresentar()` usa `apresent.Apresentador` e Ollama local.
- Conversa: fallback do interpretador para `acao="chat"`; `dispatcher._conversar()` usa `conversa.chatbot.Chatbot` e OpenRouter.

## Wake word real

A docstring fala em AUTOWORK, mas a constante em `audio/wake_word.py` e `WAKE_WORD = "work"`, com variantes `work`, `auto-work` e `auto`. A funcao remove essas variantes e retorna o comando limpo.

## Texto unico

`python app.py --texto "..."` constroi o mesmo orquestrador e chama `processar_comando(texto)`. Nao usa wake word, microfone ou HUD. Se o resultado deve ser falado, chama `audio.tts.falar()`.

## Scripts independentes

- `teste_chat.py`: REPL textual para `Chatbot`.
- `teste_interface.py`: demo independente da interface Textual antiga/experimental.
- `teste_viso.py`: aplicacao OpenCV/MediaPipe para camera, maos, pinch e formas; nao e chamada por `app.py`.
- `rodar_metricas.py`: executa pipeline de comando sob medicao; usa mocks por padrao para evitar acoes reais.
