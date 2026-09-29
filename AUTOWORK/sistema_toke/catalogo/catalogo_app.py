from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict

MAPA_APPS: Dict[str, str] = {
    "codex": "Codex",
    "openai codex": "Codex",
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "chromium": "Chromium",
    "firefox": "Firefox",
    "mozilla firefox": "Firefox",
    "edge": "Microsoft Edge",
    "microsoft edge": "Microsoft Edge",
    "opera": "Opera",
    "brave": "Brave",
    "browser": "Google Chrome",
    "navegador": "Google Chrome",
    "nav": "Google Chrome",
    "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "vs-code": "Visual Studio Code",
    "visual studio code": "Visual Studio Code",
    "code": "Visual Studio Code",
    "sublime": "Sublime Text",
    "sublime text": "Sublime Text",
    "notepad": "Notepad++",
    "cmd": "Prompt de Comando",
    "prompt": "Prompt de Comando",
    "terminal": "Windows Terminal",
    "powershell": "PowerShell",
    "windows powershell": "PowerShell",
    "explorer": "Explorador de Arquivos",
    "explorador": "Explorador de Arquivos",
    "explorador arquivos": "Explorador de Arquivos",
    "arquivos": "Explorador de Arquivos",
    "spotify": "Spotify",
    "vlc": "VLC media player",
    "vlc media player": "VLC media player",
    "player": "VLC media player",
    "calculadora": "Calculadora",
    "calc": "Calculadora",
    "bloco de notas": "Bloco de notas",
    "bloco notas": "Bloco de notas",
    "notas": "Bloco de notas",
    "calendario": "Calendario",
    "configuracoes": "Configurações",
    "configurações": "Configurações",
    "config": "Configurações",
    "pasta": "Explorador de Arquivos",
    "pastas": "Explorador de Arquivos",
    "painel de controle": "Painel de Controle",
    "controle": "Painel de Controle",
    "discord": "Discord",
    "teams": "Microsoft Teams",
    "microsoft teams": "Microsoft Teams",
    "slack": "Slack",
    "telegram": "Telegram Desktop",
    "whatsapp": "WhatsApp",
    "zoom": "Zoom",
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "outlook": "Microsoft Outlook",
    "onenote": "Microsoft OneNote",
}


@dataclass(frozen=True)
class AppInfo:
    """Metadados extensíveis de um aplicativo reconhecido pelo AUTOWORK."""

    id: str
    nome: str
    aliases: tuple[str, ...]
    categoria: str
    comando: str | None = None
    sistemas: tuple[str, ...] = ("windows",)
    prioridade: int = 100
    metodo: str = "menu_iniciar"


# Aliases de ferramentas técnicas. O mapa legado continua sendo a interface
# consumida pelo parser e pelo resolvedor; esta tabela apenas o amplia.
MAPA_APPS.update({
    "cursor": "Cursor",
    "cursor editor": "Cursor",
    "zed": "Zed",
    "zed editor": "Zed",
    "jetbrains": "JetBrains",
    "jet brains": "JetBrains",
    "jetbrains toolbox": "JetBrains Toolbox",
    "intellij": "IntelliJ IDEA",
    "intellij idea": "IntelliJ IDEA",
    "idea": "IntelliJ IDEA",
    "pycharm": "PyCharm",
    "py charm": "PyCharm",
    "webstorm": "WebStorm",
    "web storm": "WebStorm",
    "android studio": "Android Studio",
    "androidstudio": "Android Studio",
    "eclipse": "Eclipse",
    "eclipse ide": "Eclipse",
    "visual studio": "Visual Studio",
    "vs studio": "Visual Studio",
    "github desktop": "GitHub Desktop",
    "github para desktop": "GitHub Desktop",
    "git": "Git",
    "git bash": "Git Bash",
    "gitbash": "Git Bash",
    "bash do git": "Git Bash",
    "terminal do windows": "Windows Terminal",
    "power shell": "PowerShell",
    "command prompt": "Prompt de Comando",
    "docker desktop": "Docker Desktop",
    "docker": "Docker Desktop",
    "postman": "Postman",
    "insomnia": "Insomnia",
    "dbeaver": "DBeaver",
    "db ever": "DBeaver",
    "mysql workbench": "MySQL Workbench",
    "mysqlworkbench": "MySQL Workbench",
    "workbench mysql": "MySQL Workbench",
    "mongodb compass": "MongoDB Compass",
    "mongo compass": "MongoDB Compass",
    "mongodbcompass": "MongoDB Compass",
    "ollama app": "Ollama",
    "python interpreter": "Python",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "node": "Node.js",
    "anaconda": "Anaconda",
    "anaconda navigator": "Anaconda",
    "figma": "Figma",
    "obsidian": "Obsidian",
})


_METADADOS_APPS = {
    "Visual Studio Code": ("vscode", "desenvolvimento", "code", 100),
    "Cursor": ("cursor", "desenvolvimento", "cursor", 100),
    "Zed": ("zed", "desenvolvimento", "zed", 100),
    "JetBrains": ("jetbrains", "desenvolvimento", None, 80),
    "JetBrains Toolbox": ("jetbrains_toolbox", "desenvolvimento", None, 80),
    "IntelliJ IDEA": ("intellij", "desenvolvimento", None, 100),
    "PyCharm": ("pycharm", "desenvolvimento", "pycharm", 100),
    "WebStorm": ("webstorm", "desenvolvimento", "webstorm", 100),
    "Android Studio": ("android_studio", "desenvolvimento", "studio", 100),
    "Eclipse": ("eclipse", "desenvolvimento", None, 100),
    "Visual Studio": ("visual_studio", "desenvolvimento", "devenv", 100),
    "GitHub Desktop": ("github_desktop", "git", None, 100),
    "Git": ("git", "git", "git", 100),
    "Git Bash": ("git_bash", "git", None, 100),
    "Windows Terminal": ("windows_terminal", "terminal", "wt", 80),
    "PowerShell": ("powershell", "terminal", "powershell", 100),
    "Prompt de Comando": ("cmd", "terminal", "cmd", 100),
    "Docker Desktop": ("docker_desktop", "devops", "docker desktop", 100),
    "Postman": ("postman", "desenvolvimento", "postman", 100),
    "Insomnia": ("insomnia", "desenvolvimento", "insomnia", 100),
    "DBeaver": ("dbeaver", "banco_de_dados", None, 100),
    "MySQL Workbench": ("mysql_workbench", "banco_de_dados", None, 100),
    "MongoDB Compass": ("mongodb_compass", "banco_de_dados", None, 100),
    "Ollama": ("ollama", "inteligencia_artificial", "ollama", 100),
    "Python": ("python", "desenvolvimento", "python", 100),
    "Node.js": ("nodejs", "desenvolvimento", "node", 100),
    "Anaconda": ("anaconda", "desenvolvimento", None, 100),
    "Figma": ("figma", "design", None, 100),
    "Obsidian": ("obsidian", "produtividade", None, 100),
}


def _construir_catalogo_apps() -> tuple[AppInfo, ...]:
    por_nome: dict[str, list[str]] = {}
    for alias, nome in MAPA_APPS.items():
        por_nome.setdefault(nome, []).append(alias)

    catalogo = []
    for nome, aliases in por_nome.items():
        id_app, categoria, comando, prioridade = _METADADOS_APPS.get(
            nome,
            (
                re.sub(
                    r"[^a-z0-9]+",
                    "_",
                    "".join(
                        char
                        for char in unicodedata.normalize("NFD", nome.casefold())
                        if unicodedata.category(char) != "Mn"
                    ),
                ).strip("_"),
                "geral",
                None,
                100,
            ),
        )
        catalogo.append(
            AppInfo(
                id=id_app,
                nome=nome,
                aliases=tuple(sorted(set(aliases))),
                categoria=categoria,
                comando=comando,
                prioridade=prioridade,
            )
        )
    return tuple(catalogo)


CATALOGO_APPS = _construir_catalogo_apps()


def normalizar_nome_app(nome: str) -> str:
    """Normaliza nomes falados sem remover a separacao entre palavras."""
    texto = unicodedata.normalize("NFD", str(nome or ""))
    texto = "".join(char for char in texto if unicodedata.category(char) != "Mn")
    texto = texto.casefold().replace("-", " ")
    return re.sub(r"\s+", " ", texto).strip()


def resolver_app(nome: str) -> AppInfo | None:
    """Resolve um alias para a entrada estruturada do catálogo."""
    chave = normalizar_nome_app(nome)
    if not chave:
        return None

    mapa_normalizado = {
        normalizar_nome_app(alias): canonico
        for alias, canonico in MAPA_APPS.items()
    }
    if chave in mapa_normalizado:
        canonico = mapa_normalizado[chave]
        return next((app for app in CATALOGO_APPS if app.nome == canonico), None)

    canonicos = {
        normalizar_nome_app(canonico): canonico
        for canonico in MAPA_APPS.values()
    }
    canonico = canonicos.get(chave)
    return next((app for app in CATALOGO_APPS if app.nome == canonico), None)


def resolver_nome_app(nome: str) -> str | None:
    """Retorna o nome canônico somente quando o app está no catálogo."""
    app = resolver_app(nome)
    return app.nome if app else None
