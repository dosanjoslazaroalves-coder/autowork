# Testes

## Configuracao

`pyproject.toml` configura pytest para procurar testes em `tests/` com padrao `test_*.py`.

Comando principal esperado:

```powershell
python -m pytest
```

Alguns arquivos usam `unittest`, mas ainda podem ser descobertos pelo pytest por estarem em `tests/`.

## Testes em `tests/`

| Arquivo | O que verifica |
|---|---|
| `tests/test_captura.py` | Inicializacao e parametros de `ServicoCaptura`, chamada ao `listen` e timeout sem fala |
| `tests/test_estados.py` | Estados essenciais do enum `Estado` |
| `tests/test_fluxo.py` | Integracao `interpretador -> dispatcher` para clima e horario, com APIs reais |
| `tests/test_fluxo_apresentacao.py` | Script de integracao com stubs para comandos, TTS e `fala.processar_comando` |
| `tests/test_integracao_fluxo.py` | Fluxo por `fala.processar_comando`, politica de fala, conversa, clima, localizacao e apresentacao |
| `tests/test_integracao_wake.py` | Wake word + comando `fechar` em um ciclo do orquestrador |
| `tests/test_interpretador.py` | Roteamento deterministico de intencoes e flag `falar` |
| `tests/test_orquestrador.py` | Inicializacao e ciclos sem audio/transcricao |
| `tests/test_reconhecimento.py` | STT, normalizacao e tratamento de erros da Google Speech API |
| `tests/test_tts.py` | Chamada basica de `audio.tts.falar` e texto vazio |
| `tests/test_tudo.py` | Localizacao, datas, horario, diferenca e clima |
| `tests/test_wake_word.py` | Variantes de wake word e limpeza do comando |

## Scripts de teste fora de `tests/`

- `_test_integracao.py`: teste manual do pipeline normalizador/parser/resolvedor/executor com mocks.
- `_test_normalizador.py`: teste manual do normalizador e parser.
- `teste_chat.py`: REPL manual do chatbot.
- `teste_interface.py`: demo manual da interface Textual antiga/experimental.
- `teste_viso.py`: aplicacao manual de visao computacional.
- `modules/voz_teste/teste_voz.py`: teste manual do TTS Kokoro.

## Dependencias externas durante testes

Nem todos os testes sao hermeticos. Alguns podem depender de internet para Nominatim/Open-Meteo/ip-api, chave OpenRouter, Ollama local, dependencias de TTS Kokoro/eSpeak, camera ou dispositivo de audio.

## Observacoes de risco

- `tests/test_tts.py` usa patch em `audio.tts._falar_kokoro` com `create=True`, mas `audio.tts.falar()` importa `modules.voz_teste.falar` dentro da funcao. O patch pode nao impedir o uso do TTS real em ambientes com dependencias instaladas.
- `tests/test_integracao_fluxo.py` afirma no comentario inicial que comando de automacao com sucesso nao fala, mas o teste atual espera uma fala porque usa `fala.processar_comando`, cuja politica fala qualquer mensagem retornada.
- Testes de clima/localizacao podem falhar por rede, rate limit ou indisponibilidade de API.
- `rodar_metricas.py` aparenta conter referencias a simbolos ausentes em `sistema_toke.catalogo`, entao comandos de metricas podem falhar antes de medir o pipeline.

## Componentes com pouca ou nenhuma cobertura observada

- HUD real em `interface/hud.py`.
- `teste_viso.py` e fluxo MediaPipe/OpenCV.
- `setup_dados.py` com download do IBGE.
- Tratamento completo de erros de Ollama em `apresent.py`.
- Empacotamento PyInstaller de `autowork.spec`.
- `configui.py` e `personalidade.py`, que nao aparecem integrados ao fluxo principal.
