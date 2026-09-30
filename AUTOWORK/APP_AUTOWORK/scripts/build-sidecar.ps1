$ErrorActionPreference = "Stop"

$appRoot = Split-Path -Parent $PSScriptRoot
$defaultCorePath = [IO.Path]::GetFullPath((Join-Path $appRoot "..\Chat\AUTOWORK"))
$corePath = if ($env:AUTOWORK_CORE_PATH) { [IO.Path]::GetFullPath($env:AUTOWORK_CORE_PATH) } else { $defaultCorePath }
if (-not (Test-Path -LiteralPath (Join-Path $corePath "core\servico_api.py"))) {
  throw "Núcleo AUTOWORK não encontrado em '$corePath'. Defina AUTOWORK_CORE_PATH."
}

# Always use the requested interpreter or the core environment. A global
# pyinstaller/python must never silently change which dependencies are bundled.
$python = if ($env:PYTHON_EXECUTABLE) { $env:PYTHON_EXECUTABLE } else { Join-Path $corePath ".venv\Scripts\python.exe" }
if (-not (Test-Path -LiteralPath $python)) {
  throw "Python do núcleo não encontrado em '$python'. Defina PYTHON_EXECUTABLE."
}

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
& $python -c "import PyInstaller, fastapi, uvicorn, speech_recognition, pyaudio, psutil, pyautogui, requests, tzdata, kokoro, misaki, torch, numpy, scipy, sounddevice, phonemizer, espeakng_loader; print('Dependências do sidecar verificadas.')"
if ($LASTEXITCODE -ne 0) { throw "Dependências incompletas no ambiente '$python'. Instale os requirements do núcleo e PyInstaller nesse ambiente." }

$dataPath = Join-Path $corePath "modules\dados"
if (-not (Test-Path -LiteralPath (Join-Path $dataPath "paises_capitais.json"))) {
  throw "Recursos do núcleo ausentes: $dataPath"
}

$distPath = Join-Path $appRoot "python"
New-Item -ItemType Directory -Force -Path $distPath | Out-Null
$buildArguments = @(
  "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--console",
  "--name", "autowork-api", "--distpath", $distPath,
  "--workpath", (Join-Path $appRoot ".tmp\autowork-api-build"),
  "--specpath", (Join-Path $appRoot ".tmp\autowork-api-spec"),
  "--paths", $corePath,
  "--paths", $distPath,
  "--add-data", "$dataPath;modules/dados",
  "--collect-data", "tzdata",
  "--collect-data", "speech_recognition",
  "--collect-data", "kokoro",
  "--collect-data", "espeakng_loader",
  "--collect-data", "language_tags",
  "--copy-metadata", "fastapi",
  "--copy-metadata", "uvicorn",
  "--hidden-import", "core.servico_api",
  "--hidden-import", "core.orquestrador",
  "--hidden-import", "audio.captura",
  "--hidden-import", "audio.reconhecimento",
  "--hidden-import", "dispatcher",
  "--hidden-import", "interpretador",
  "--hidden-import", "filtro",
  "--hidden-import", "apresent",
  "--hidden-import", "interface.terminal",
  "--collect-submodules", "uvicorn",
  "--collect-submodules", "core",
  "--collect-submodules", "audio",
  "--collect-submodules", "comd_rapidos",
  "--collect-submodules", "persn_emcoes",
  "--collect-submodules", "sistema_toke",
  "--collect-submodules", "sist_comd_complex",
  "--collect-submodules", "modules.tempo",
  "--collect-submodules", "modules.clima",
  "--collect-submodules", "modules.localizacao",
  "--collect-submodules", "conversa",
  "--collect-submodules", "kokoro",
  "--collect-submodules", "misaki",
  "--collect-submodules", "phonemizer",
  "--collect-submodules", "espeakng_loader",
  (Join-Path $distPath "api.py")
)
& $python @buildArguments
if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar o sidecar FastAPI/Core com PyInstaller." }
if (-not (Test-Path -LiteralPath (Join-Path $distPath "autowork-api.exe"))) {
  throw "PyInstaller não produziu o sidecar esperado."
}
Write-Host "Sidecar criado em $(Join-Path $distPath 'autowork-api.exe')"
