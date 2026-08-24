# Módulo experimental de voz (`voz_teste`)

Área isolada para desenvolver, testar e corrigir Text-to-Speech (TTS) antes de uma futura integração ao AUTOWORK.

## Objetivo

Validar de forma independente:

1. carregamento do motor TTS (Kokoro);
2. inicialização do pipeline;
3. conversão de texto em áudio (PT-BR);
4. reprodução no dispositivo padrão do Windows;
5. tratamento de erros com diagnóstico claro.

## Estrutura

```text
modules/
└── voz_teste/
    ├── __init__.py      # exporta falar, gerar_audio, salvar_audio
    ├── config.py        # voz, idioma, velocidade, caminhos
    ├── tts.py           # implementação Kokoro + eSpeak NG
    ├── teste_voz.py     # teste executável
    ├── requirements.txt # dependências só deste módulo
    ├── README.md
    └── output/          # criada automaticamente ao salvar áudio
```

## Dependências

### Python

- Python 3.11 recomendado

### Pacotes Python

Instale somente o necessário para este módulo:

```powershell
python -m pip install -r modules/voz_teste/requirements.txt
```

### eSpeak NG (Windows)

O Kokoro usa o Misaki/Phonemizer com eSpeak NG para fonemização em português.

Instale o eSpeak NG para Windows e confirme:

```text
C:\Program Files\eSpeak NG\libespeak-ng.dll
C:\Program Files\eSpeak NG\espeak-ng-data
```

Se o caminho for diferente, ajuste `ESPEAK_DIR` em `config.py`.

## Como executar o teste

Na raiz do AUTOWORK:

```powershell
python modules/voz_teste/teste_voz.py
```

Ou:

```powershell
python -m modules.voz_teste.teste_voz
```

Saída esperada:

```text
Inicializando TTS...
Modelo carregado.
Gerando áudio...
Áudio gerado.
Reproduzindo áudio...
Teste concluído.
```

## Uso programático

```python
from modules.voz_teste import falar, gerar_audio, salvar_audio

falar("Olá, este é um teste de voz do AUTOWORK.")

audio = gerar_audio("Teste de síntese.")
salvar_audio("Salvar em arquivo.", "modules/voz_teste/output/teste.wav")
```

## Configuração

Edite `config.py`:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `LANG_CODE` | `"p"` | Código Kokoro para PT-BR |
| `VOICE` | `"pf_dora"` | Voz feminina brasileira |
| `SPEED` | `1.0` | Velocidade da fala |
| `SAMPLE_RATE` | `24000` | Taxa de amostragem |
| `ESPEAK_DIR` | `C:\Program Files\eSpeak NG` | Instalação do eSpeak NG |

## Possíveis erros

### `language "pt-br" is not supported by the espeak backend`

**Causa:** o Misaki sobrescreve o `EspeakWrapper` com o `espeakng_loader` embutido, que no Windows não lista a voz `pt-br`.

**Correção no módulo:** `tts.py` reaplica os caminhos do eSpeak NG nativo após importar o Kokoro.

### `DLL do eSpeak NG não encontrada`

**Causa:** eSpeak NG não instalado ou caminho incorreto em `config.py`.

### `Pacote kokoro não encontrado`

**Causa:** dependências não instaladas.

**Correção:** `python -m pip install -r modules/voz_teste/requirements.txt`

### Falha na reprodução de áudio

**Causa:** dispositivo de saída indisponível ou driver de áudio.

**Correção:** verifique o dispositivo padrão do Windows e reinstale `sounddevice`.

## Integração futura com o AUTOWORK

Este módulo **não altera** arquivos existentes do AUTOWORK.

Para integrar depois:

1. validar `falar()` neste módulo isolado;
2. criar um adaptador em `voz.py` ou `vozes/` que importe `modules.voz_teste.falar`;
3. manter `config.py` como fonte de configuração do TTS;
4. não misturar dependências do módulo com o restante até a integração ser aprovada.

## Isolamento

- Não importa `executor`, `fala`, `main` nem outros módulos do AUTOWORK.
- Não modifica o fluxo principal do projeto.
- Toda correção deve ocorrer dentro de `modules/voz_teste/`.
