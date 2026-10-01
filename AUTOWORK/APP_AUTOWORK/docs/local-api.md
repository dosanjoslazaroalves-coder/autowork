# Integração local Electron → FastAPI → núcleo real

## Arquitetura

O FastAPI funciona como ponte local em `127.0.0.1:47100`. Não cria servidor
remoto, autenticação, conta ou banco de dados. `AUTOWORK_API_HOST` aceita apenas
endereços de loopback e `AUTOWORK_API_PORT` permite uma porta local alternativa.

- `python/api.py`: validação HTTP e inicialização do Uvicorn.
- `python/service.py`: carrega `core.servico_api` do núcleo original em
  desenvolvimento e dos módulos embutidos quando congelado pelo PyInstaller.
- `core/servico_api.py`: fachada sobre o `Orquestrador` real, com o mesmo
  interpretador, parser, resolvedor, dispatcher e executor de `app.py`.
- `src/main.ts`: dono do processo da API que iniciar e cliente HTTP local.
- `src/preload.ts`: contrato IPC restrito, sem Node.js no renderer.
- `src/renderer/renderer.ts`: representa conexão/estados e envia texto.
- `python/autowork.py`: transporte JSONL legado sobre o mesmo serviço.

O desktop não mantém catálogo, regras de comandos ou inteligência próprios.
O núcleo continua responsável pelos estados e pelo resultado dos comandos.

## Ambiente de desenvolvimento

O núcleo é encontrado em `../Chat/AUTOWORK`. Defina `AUTOWORK_CORE_PATH` quando
o checkout estiver em outro local. Os scripts de API/teste/build escolhem o
Python de `.venv/Scripts/python.exe`; `PYTHON_EXECUTABLE` pode selecionar outro
ambiente explicitamente. Não presumem que um Python global tenha dependências.

```powershell
pnpm start:api
```

Em outro terminal, use JSON codificado em UTF-8 para preservar acentos também
em versões antigas do PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:47100/health
Invoke-RestMethod http://127.0.0.1:47100/api/status
$body = [Text.Encoding]::UTF8.GetBytes('{"texto":"que horas são"}')
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:47100/api/command -ContentType 'application/json; charset=utf-8' -Body $body
```

O `/health` confirma transporte. `/api/status` mostra a identidade, o estado e
eventuais falhas do núcleo. `/api/command` retorna o resultado real e usa o
mesmo TTS Kokoro do fluxo principal, publicando `FALANDO` no `/api/status`
durante a reprodução antes de voltar a `IDLE`. Comandos de horário local e data
permitem verificar o núcleo sem depender de rede ou
ações que alterem aplicativos do usuário. Comandos que passam pelo Ollama
exigem o modelo/serviço definido no núcleo; isso é uma dependência funcional
existente, não um requisito de instalação manual de Python.

`POST /api/voice/start` inicia, em uma única thread, o mesmo ciclo de captura,
STT, interpretação, execução e TTS usado por `app.py --terminal`. A transcrição
real fica em `last_transcript`, enquanto `state`, `last_response`,
`voice_running` e `audio_level` permitem que a HUD reflita o estado do núcleo.
`POST /api/voice/stop` solicita o encerramento da escuta; o timeout curto da
ponte permite parar a captura sem deixar a janela bloqueada.

## Terminal e UTF-8

`app.py --texto` continua disponível no projeto original, além das opções de
voz/terminal já existentes. Saída UTF-8 é configurada nos processos Python e
decodificada como UTF-8 no Electron. Caminhos são tratados com APIs de arquivos
e argumentos separados, preservando espaços e acentos como em `Marco Antônio`.

## Testes

```powershell
pnpm run test:api
pnpm run typecheck
pnpm start
```

O teste HTTP usa `ServicoApi`/`Orquestrador` reais. No Electron, confirme conexão,
envie `que horas são` e um segundo comando suportado, confira a resposta e o
estado, feche a janela e verifique que os processos criados por ela encerraram.
Uma API iniciada manualmente e reutilizada pelo Electron deve continuar ativa.

Teste falhas também: API indisponível, porta ocupada por serviço incompatível e
núcleo que falha na inicialização devem produzir diagnóstico, sem congelar a
janela nem iniciar sucessivas cópias da API na mesma porta.

## Sidecar e distribuição

```powershell
pnpm run build:sidecar
```

O script `scripts/build-sidecar.ps1` usa caminhos absolutos, verifica imports e
compila `python/api.py` como `python/autowork-api.exe` com PyInstaller `onefile`.
Inclui os pacotes do núcleo e imports dinâmicos, recursos `modules/dados`,
`tzdata`, dados de SpeechRecognition e metadados FastAPI/Uvicorn. O núcleo não
é duplicado em uma segunda árvore de fontes: os módulos do projeto original
entram no arquivo distribuível. Recursos são lidos relativamente a `__file__`
no diretório de extração gerenciado pelo PyInstaller.

Execute o sidecar com diretório de trabalho fora dos dois projetos e com as
variáveis de caminho de desenvolvimento removidas. Teste os três endpoints,
comandos de horário/data e uma capital para verificar os JSON/fusos empacotados.
Esse teste precisa passar antes da distribuição:

```powershell
pnpm run dist:dir
pnpm run dist
```

O electron-builder inclui somente o executável em
`resources/autowork/autowork-api.exe`. Os scripts conferem sua existência e
tamanho depois do build. O instalador NSIS é copiado da pasta `release` para
a raiz com o nome `AUTOWORK-Setup-0.3.1.exe`, mantendo o original.

Após instalar, confira fisicamente o atalho `AUTOWORK` na Área de Trabalho e
seu destino `AUTOWORK.exe`; abra pelo atalho, envie comandos e feche o app.
As opções NSIS usam as pastas conhecidas do Windows, incluindo redirecionamento
da Área de Trabalho. Registre resultados de instalação/atalho separadamente
dos resultados de compilação.

## Voz e serviços opcionais

O canal HTTP textual não inicializa microfone, mas reproduz as respostas
faladas pelo mesmo TTS Kokoro do núcleo. O modo original `app.py` preserva voz,
TTS e debug, com suas dependências Kokoro/modelos/eSpeak descritas no núcleo.
O instalador textual não redistribui
esses modelos nem o servidor Ollama. Falhas desses serviços devem ser mostradas
pelo núcleo; não há substituição por respostas fictícias.
