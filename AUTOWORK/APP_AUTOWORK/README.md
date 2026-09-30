# AUTOWORK Desktop 0.3.0

Interface Windows em Electron e TypeScript para o núcleo Python existente do
AUTOWORK. ORB, partículas, HUD, temas e controles continuam na interface;
comandos de texto e status usam a integração real.

```text
renderer → preload/IPC → Electron → FastAPI em 127.0.0.1:47100
         → AutoworkService → core.servico_api.ServicoApi
         → Orquestrador → interpretador/parser/resolvedor/dispatcher/executor
```

O renderer não interpreta comandos. `app.py` permanece como entrada de terminal,
voz e depuração, usando o mesmo núcleo. O canal de texto do desktop não inicia
microfone nem TTS; controles visuais de voz não substituem o fluxo de voz do
núcleo. As funções que usam Ollama continuam dependendo do serviço/modelo
configurado no núcleo; nenhuma resposta é simulada quando ele está indisponível.

## Desenvolvimento

Requisitos de desenvolvimento: Windows, Node.js, pnpm e o ambiente Python do
núcleo em `../Chat/AUTOWORK/.venv`. Para outros locais, defina
`AUTOWORK_CORE_PATH` e, se necessário, `PYTHON_EXECUTABLE`.

```powershell
pnpm install --frozen-lockfile
& '..\Chat\AUTOWORK\.venv\Scripts\python.exe' -m pip install -r '..\Chat\AUTOWORK\requirements.txt'
& '..\Chat\AUTOWORK\.venv\Scripts\python.exe' -m pip install -r python/requirements.txt pyinstaller pytest httpx
pnpm run typecheck
pnpm run test:api
pnpm start
```

O Electron inicia a API automaticamente, ou reutiliza uma API AUTOWORK local
compatível. `pnpm start:api` inicia somente a ponte usando o Python do núcleo.
Os três endpoints são `GET /health`, `GET /api/status` e `POST /api/command`
com corpo `{ "texto": "que horas são" }`.

Para continuar no terminal:

```powershell
Set-Location '..\Chat\AUTOWORK'
& '.\.venv\Scripts\python.exe' app.py --texto
```

Esse caminho mantém os logs e o pipeline original. Dependências de voz/TTS
opcionais continuam documentadas no núcleo e não são exigidas para comandos de
texto do desktop.

## Build e instalador Windows

```powershell
pnpm run build:sidecar
pnpm run typecheck
pnpm run dist:dir
pnpm run dist
```

`build:sidecar` usa o `.venv` do núcleo ou `PYTHON_EXECUTABLE` explicitamente
selecionado. O PyInstaller produz `python/autowork-api.exe`, incluindo o runtime
Python, a ponte FastAPI, o núcleo importado diretamente do projeto original,
dados de localidades e fusos horários. Não é necessário Python global, pip ou
venv na máquina do usuário final.

`dist:dir` gera `release/win-unpacked`. `dist` gera o instalador NSIS
`release/AUTOWORK-Setup-0.3.0.exe` e copia o mesmo arquivo para a raiz do projeto:

```text
APP_AUTOWORK/AUTOWORK-Setup-0.3.0.exe
```

O executável portátil já suportado pelo projeto também continua sendo gerado
em `release/AUTOWORK-Portable-0.3.0.exe`.

Os scripts de distribuição falham se o sidecar estiver ausente e conferem sua
inclusão em `resources/autowork/autowork-api.exe`. A versão instalada não usa o
checkout Python de desenvolvimento.

O instalador assistido instala `AUTOWORK.exe`, cria o atalho `AUTOWORK` na Área
de Trabalho pelo mecanismo padrão NSIS e uma entrada no Menu Iniciar. A opção
de criação da Área de Trabalho é `always`, incluindo atualização. O nome e o
ícone do atalho correspondem ao aplicativo instalado. Não há caminho de Área
de Trabalho específico de usuário.

O ícone oficial existente `build/icon.svg` é renderizado pelo Electron em seis
tamanhos (16 a 256 pixels) durante o build, produzindo `build/icon.ico` e o
recurso de janela `dist/icon.ico`. O desenho original é preservado.

## Validação e limites

Consulte [docs/local-api.md](docs/local-api.md) para testes HTTP, UTF-8, processo
local e validação do sidecar. Um build concluído não comprova instalação nem
atalho: essas verificações precisam ser executadas e registradas no relatório
da entrega. O instalador local não possui assinatura digital de distribuição.

O workflow de CI existente precisa receber acesso ao repositório/checkout real
do núcleo, além de instalar seus requirements, antes de produzir este sidecar.
O processo de build local acima usa os dois projetos existentes.
