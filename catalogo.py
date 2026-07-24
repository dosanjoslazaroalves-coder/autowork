from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

"""
catálogo.py — Dados puros de comandos conhecidos.

Responsabilidade única: armazenar comandos, sinônimos e aliases.
Nenhuma lógica. Apenas dados.
"""

# ══════════════════════════════════════════════
# Estrutura de dados para ações do catálogo
# ══════════════════════════════════════════════


@dataclass(frozen=True)
class AcaoInfo:


    nome: str
    sinonimos: List[str] = field(default_factory=list)
    funcao: str = ""
    modulo: str = ""
    parametros: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SiteInfo:
    """Informações de um site no catálogo."""
    nome: str
    url: str
    sinonimos: List[str] = field(default_factory=list)
    categoria: str = ""


# ══════════════════════════════════════════════
# Verbos / gatilhos por categoria
# ══════════════════════════════════════════════

VERBOS_ABRIR: Set[str] = frozenset({
    "abrir", "abra", "abre", "abrindo",
    "executar", "execute", "executa",
    "iniciar", "inicie", "inicia",
    "rodar", "rode",
})

VERBOS_FECHAR: Set[str] = frozenset({
    "fechar", "fecha", "feche",
    "encerrar", "encerra", "encerre",
    "sair", "sai",
})

VERBOS_ALTERNAR: Set[str] = frozenset({
    "alternar", "alterna", "alterne",
    "trocar", "troca", "troque",
    "mudar", "muda", "mude",
})

VERBOS_MOSTRAR: Set[str] = frozenset({
    "mostrar", "mostra", "mostre",
    "exibir", "exibe", "exiba",
})

VERBOS_MAXIMIZAR: Set[str] = frozenset({
    "maximizar", "maximiza", "maximize",
    "ampliar", "amplia", "amplie",
})

VERBOS_RESTAURAR: Set[str] = frozenset({
    "restaurar", "restaura", "restaure",
    "minimizar", "minimiza", "minimize",
})

VERBOS_ENCAIXAR: Set[str] = frozenset({
    "encaixar", "encaixa", "encaixe",
})

VERBOS_BLOQUEAR: Set[str] = frozenset({
    "bloquear", "bloqueia", "bloqueie",
    "travar", "trava",
})

VERBOS_NAVEGAR: Set[str] = frozenset({
    "navegar", "navega", "navegue",
    "ir", "vai",
})

VERBOS_ATUALIZAR: Set[str] = frozenset({
    "atualizar", "atualiza", "atualize",
    "recarregar", "recarrega", "recarregue",
})

VERBOS_REABRIR: Set[str] = frozenset({
    "reabrir", "reabre", "reabra",
})

VERBOS_VOLTAR: Set[str] = frozenset({
    "voltar", "volta", "volte",
    "retornar", "retorna", "retorne",
})

VERBOS_AVANCAR: Set[str] = frozenset({
    "avancar", "avanca", "avance",
})

VERBOS_BUSCAR: Set[str] = frozenset({
    "buscar", "busca", "busque",
    "pesquisar", "pesquisa", "pesquise",
})

VERBOS_SALVAR: Set[str] = frozenset({
    "salvar", "salva", "salve",
})

VERBOS_IMPRIMIR: Set[str] = frozenset({
    "imprimir", "imprime", "imprima",
})

VERBOS_AUMENTAR: Set[str] = frozenset({
    "aumentar", "aumenta", "aumente",
})

VERBOS_DIMINUIR: Set[str] = frozenset({
    "diminuir", "diminui", "diminua",
})

VERBOS_INSPECIONAR: Set[str] = frozenset({
    "inspecionar", "inspeciona", "inspecione",
})

VERBOS_ZOOM: Set[str] = frozenset({
    "ampliar", "amplia", "amplie",
    "reduzir", "reduz", "reduza",
})

VERBOS_DEVTOOLS: Set[str] = frozenset({
    "inspecionar", "inspeciona", "inspecione",
    "depurar", "depura", "depure",
})


MAPA_VERBOS: Dict[str, str] = {
    # ── abrir ──
    "abrir": "abrir",
    "abra": "abrir",
    "abre": "abrir",
    "abrindo": "abrir",
    "executar": "abrir",
    "execute": "abrir",
    "executa": "abrir",
    "iniciar": "abrir",
    "inicie": "abrir",
    "inicia": "abrir",
    "rodar": "abrir",
    "rode": "abrir",
    # ── fechar ──
    "fechar": "fechar",
    "fecha": "fechar",
    "feche": "fechar",
    "encerrar": "encerrar",
    "encerra": "encerrar",
    "encerre": "encerrar",
    "sair": "sair",
    "sai": "sair",
    # ── alternar ──
    "alternar": "alternar",
    "alterna": "alternar",
    "alterne": "alternar",
    "trocar": "trocar",
    "troca": "trocar",
    "troque": "trocar",
    "mudar": "mudar",
    "muda": "mudar",
    "mude": "mudar",
    # ── mostrar ──
    "mostrar": "mostrar",
    "mostra": "mostrar",
    "mostre": "mostrar",
    "exibir": "exibir",
    "exibe": "exibir",
    "exiba": "exibir",
    # ── maximizar ──
    "maximizar": "maximizar",
    "maximiza": "maximizar",
    "maximize": "maximizar",
    "ampliar": "ampliar",
    "amplia": "ampliar",
    "amplie": "ampliar",
    # ── restaurar / minimizar ──
    "restaurar": "restaurar",
    "restaura": "restaurar",
    "restaure": "restaurar",
    "minimizar": "minimizar",
    "minimiza": "minimizar",
    "minimize": "minimizar",
    # ── encaixar ──
    "encaixar": "encaixar",
    "encaixa": "encaixar",
    "encaixe": "encaixar",
    # ── bloquear ──
    "bloquear": "bloquear",
    "bloqueia": "bloquear",
    "bloqueie": "bloquear",
    "travar": "travar",
    "trava": "travar",
    # ── navegar ──
    "navegar": "navegar",
    "navega": "navegar",
    "navegue": "navegar",
    "ir": "navegar",
    "vai": "navegar",
    # ── atualizar ──
    "atualizar": "atualizar",
    "atualiza": "atualizar",
    "atualize": "atualizar",
    "recarregar": "atualizar",
    "recarrega": "atualizar",
    "recarregue": "atualizar",
    # ── reabrir ──
    "reabrir": "reabrir",
    "reabre": "reabrir",
    "reabra": "reabrir",
    # ── voltar ──
    "voltar": "voltar",
    "volta": "voltar",
    "volte": "voltar",
    "retornar": "voltar",
    "retorna": "voltar",
    "retorne": "voltar",
    # ── avancar ──
    "avancar": "avancar",
    "avanca": "avancar",
    "avance": "avancar",
    # ── buscar ──
    "buscar": "buscar",
    "busca": "buscar",
    "busque": "buscar",
    "pesquisar": "buscar",
    "pesquisa": "buscar",
    "pesquise": "buscar",
    # ── salvar ──
    "salvar": "salvar",
    "salva": "salvar",
    "salve": "salvar",
    # ── imprimir ──
    "imprimir": "imprimir",
    "imprime": "imprimir",
    "imprima": "imprimir",
    # ── aumentar ──
    "aumentar": "aumentar",
    "aumenta": "aumentar",
    "aumente": "aumentar",
    # ── diminuir ──
    "diminuir": "diminuir",
    "diminui": "diminuir",
    "diminua": "diminuir",
    # ── inspecionar - já registrado acima como duplicata, evitando conflito
    # "inspecionar" mapeado para "inspecionar" (já existe via VERBOS_INSPECIONAR)
    # ── ampliar (zoom) - já mapeado para "ampliar" (maximizar)
    # ── reduzir - novo mapeamento
    "reduzir": "diminuir",
    "reduz": "diminuir",
    "reduza": "diminuir",
    # ── depurar ──
    "depurar": "depurar",
    "depura": "depurar",
    "depure": "depurar",
}


VERBOS_POR_ACAO: Dict[str, Set[str]] = {
    "abrir_app": VERBOS_ABRIR,
    "abrir_site": VERBOS_ABRIR,
    "fechar_janela": VERBOS_FECHAR,
    "alternar_janelas": VERBOS_ALTERNAR,
    "mostrar_area_de_trabalho": VERBOS_MOSTRAR,
    "maximizar_janela": VERBOS_MAXIMIZAR,
    "restaurar_ou_minimizar_janela": VERBOS_RESTAURAR,
    "encaixar_janela_esquerda": VERBOS_ENCAIXAR,
    "encaixar_janela_direita": VERBOS_ENCAIXAR,
    "bloquear_tela": VERBOS_BLOQUEAR,
}

PALAVRAS_DESCARTE: Set[str] = frozenset({
    "o", "a", "os", "as",
    "um", "uma", "uns", "umas",
    "de", "da", "do", "das", "dos",
    "em", "no", "na", "nos", "nas",
    "para", "pra", "por", "per",
    "com", "sem", "sob", "sobre",
    "entre", "apos", "ate", "ate",
    "mim", "me", "te", "se", "si",
    "voce", "voces",
    "ele", "ela", "eles", "elas",
    "lhe", "lhes",
    "meu", "meus", "minha", "minhas",
    "teu", "teus", "tua", "tuas",
    "seu", "seus", "sua", "suas",
    "nosso", "nossa", "nossos", "nossas",
    "favor",
    "consegue", "conseguir", "pode", "poder",
    "quero", "quer", "querer",
    "preciso", "precisa", "precisar",
    "gostaria", "gostar",
    "seria", "sao", "e", "esta",
    "poderia",
    "qual", "quais", "que",
    "como", "quando", "onde",
    "hoje", "agora",
})


PALAVRAS_OBJETO_JANELA: Set[str] = frozenset({
    "janela", "janelas", "tela", "telas",
    "area", "trabalho", "esquerda", "direita",
    "tarefas", "visao",
})


PALAVRAS_OBJETO_NAVEGADOR: Set[str] = frozenset({
    "aba", "abas", "guia", "guias",
    "pagina", "paginas",
    "navegador", "browser",
    "zoom",
    "endereco", "enderecos",
    "historico",
    "download", "downloads",
    "favorito", "favoritos", "marcadores",
    "devtools", "ferramentas",
    "elemento", "elementos",
    "anonimo", "anonima", "privada",
    "inicial",
})


CATALOGO_ACOES: Dict[str, AcaoInfo] = {
    "fechar_janela": AcaoInfo(
        nome="fechar_janela",
        sinonimos=["fechar", "encerrar", "sair"],
        funcao="fechar_janela",
        modulo="Janela",
        parametros=[],
    ),
    "alternar_janelas": AcaoInfo(
        nome="alternar_janelas",
        sinonimos=["alternar", "trocar", "mudar"],
        funcao="alternar_janelas",
        modulo="Janela",
        parametros=[],
    ),
    "mostrar_area_de_trabalho": AcaoInfo(
        nome="mostrar_area_de_trabalho",
        sinonimos=["mostrar", "exibir"],
        funcao="mostrar_area_de_trabalho",
        modulo="Janela",
        parametros=[],
    ),
    "maximizar_janela": AcaoInfo(
        nome="maximizar_janela",
        sinonimos=["maximizar", "ampliar"],
        funcao="maximizar_janela",
        modulo="Janela",
        parametros=[],
    ),
    "restaurar_ou_minimizar_janela": AcaoInfo(
        nome="restaurar_ou_minimizar_janela",
        sinonimos=["restaurar", "minimizar"],
        funcao="restaurar_ou_minimizar_janela",
        modulo="Janela",
        parametros=[],
    ),
    "encaixar_janela_esquerda": AcaoInfo(
        nome="encaixar_janela_esquerda",
        sinonimos=["encaixar"],
        funcao="encaixar_janela_esquerda",
        modulo="Janela",
        parametros=[],
    ),
    "encaixar_janela_direita": AcaoInfo(
        nome="encaixar_janela_direita",
        sinonimos=["encaixar"],
        funcao="encaixar_janela_direita",
        modulo="Janela",
        parametros=[],
    ),
    "abrir_visao_de_tarefas": AcaoInfo(
        nome="abrir_visao_de_tarefas",
        sinonimos=["tarefas"],
        funcao="abrir_visao_de_tarefas",
        modulo="Janela",
        parametros=[],
    ),
    "bloquear_tela": AcaoInfo(
        nome="bloquear_tela",
        sinonimos=["bloquear", "travar"],
        funcao="bloquear_tela",
        modulo="Janela",
        parametros=[],
    ),
    # ── Ações de app ──
    "abrir_app": AcaoInfo(
        nome="abrir_app",
        sinonimos=["abrir", "executar", "iniciar", "rodar"],
        funcao="abrir_app",
        modulo="abrir_app",
        parametros=["nome"],
    ),
    # ── Ações de site ──
    "abrir_site": AcaoInfo(
        nome="abrir_site",
        sinonimos=["abrir", "executar", "iniciar", "rodar"],
        funcao="abrir_site",
        modulo="abrir_site",
        parametros=["url"],
    ),
    # ── Ações informativas ──
    "informar_hora": AcaoInfo(
        nome="informar_hora",
        sinonimos=["hora", "horas", "horario"],
        funcao="informar_hora",
        modulo="__info__",
        parametros=[],
    ),
    "informar_data": AcaoInfo(
        nome="informar_data",
        sinonimos=["data", "dia"],
        funcao="informar_data",
        modulo="__info__",
        parametros=[],
    ),
    # ── Ações do navegador (AtalhoNav) ──
    "nova_aba": AcaoInfo(
        nome="nova_aba",
        sinonimos=["nova", "abrir", "guia"],
        funcao="nova_aba",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "fechar_aba": AcaoInfo(
        nome="fechar_aba",
        sinonimos=["fechar"],
        funcao="fechar_aba",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "reabrir_aba": AcaoInfo(
        nome="reabrir_aba",
        sinonimos=["reabrir"],
        funcao="reabrir_aba",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "proxima_aba": AcaoInfo(
        nome="proxima_aba",
        sinonimos=["proxima", "proximo", "navegar"],
        funcao="proxima_aba",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "aba_anterior": AcaoInfo(
        nome="aba_anterior",
        sinonimos=["anterior", "voltar"],
        funcao="aba_anterior",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "atualizar_pagina": AcaoInfo(
        nome="atualizar_pagina",
        sinonimos=["atualizar", "recarregar"],
        funcao="atualizar_pagina",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "atualizacao_forcada": AcaoInfo(
        nome="atualizacao_forcada",
        sinonimos=["forcada", "forcar"],
        funcao="atualizacao_forcada",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "barra_endereco": AcaoInfo(
        nome="barra_endereco",
        sinonimos=["endereco", "url"],
        funcao="barra_endereco",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "voltar_pagina": AcaoInfo(
        nome="voltar_pagina",
        sinonimos=["voltar", "retornar"],
        funcao="voltar_pagina",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "avancar_pagina": AcaoInfo(
        nome="avancar_pagina",
        sinonimos=["avancar"],
        funcao="avancar_pagina",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "pagina_inicial": AcaoInfo(
        nome="pagina_inicial",
        sinonimos=["inicial", "home"],
        funcao="pagina_inicial",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "historico": AcaoInfo(
        nome="historico",
        sinonimos=["historico"],
        funcao="historico",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "downloads": AcaoInfo(
        nome="downloads",
        sinonimos=["download", "downloads"],
        funcao="downloads",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "favoritos": AcaoInfo(
        nome="favoritos",
        sinonimos=["favorito", "favoritos", "marcadores"],
        funcao="favoritos",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "buscar_na_pagina": AcaoInfo(
        nome="buscar_na_pagina",
        sinonimos=["buscar", "pesquisar"],
        funcao="buscar_na_pagina",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "janela_anonima": AcaoInfo(
        nome="janela_anonima",
        sinonimos=["anonima", "anonimo", "privada"],
        funcao="janela_anonima",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "nova_janela": AcaoInfo(
        nome="nova_janela",
        sinonimos=["nova"],
        funcao="nova_janela",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "fechar_janela_nav": AcaoInfo(
        nome="fechar_janela_nav",
        sinonimos=["fechar"],
        funcao="fechar_janela_nav",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "salvar_pagina": AcaoInfo(
        nome="salvar_pagina",
        sinonimos=["salvar"],
        funcao="salvar_pagina",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "imprimir_pagina": AcaoInfo(
        nome="imprimir_pagina",
        sinonimos=["imprimir"],
        funcao="imprimir_pagina",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "zoom_mais": AcaoInfo(
        nome="zoom_mais",
        sinonimos=["aumentar", "ampliar", "mais"],
        funcao="zoom_mais",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "zoom_menos": AcaoInfo(
        nome="zoom_menos",
        sinonimos=["diminuir", "menos", "reduzir"],
        funcao="zoom_menos",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "zoom_padrao": AcaoInfo(
        nome="zoom_padrao",
        sinonimos=["padrao", "normal", "reseta"],
        funcao="zoom_padrao",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "devtools": AcaoInfo(
        nome="devtools",
        sinonimos=["devtools", "depurar"],
        funcao="devtools",
        modulo="AtalhoNav",
        parametros=[],
    ),
    "inspecionar_elemento": AcaoInfo(
        nome="inspecionar_elemento",
        sinonimos=["inspecionar", "elemento"],
        funcao="inspecionar_elemento",
        modulo="AtalhoNav",
        parametros=[],
    ),
}


def _construir_mapa_token_acoes() -> Dict[str, List[str]]:
    """Constrói mapa de primeiro token → ações possíveis."""
    mapa: Dict[str, List[str]] = {}
    for acao_nome, acao_info in CATALOGO_ACOES.items():
        for sinonimo in acao_info.sinonimos:
            if sinonimo not in mapa:
                mapa[sinonimo] = []
            mapa[sinonimo].append(acao_nome)
    return mapa


MAPA_TOKEN_PARA_ACOES: Dict[str, List[str]] = _construir_mapa_token_acoes()


MAPA_APPS: Dict[str, str] = {
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
    "notas": "Bloco de notas",
    "calendario": "Calendario",
    "configuracoes": "Configurações",
    "config": "Configurações",
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


COMANDOS_FIXOS: Dict[str, dict] = {
    "hora": {"acao": "informar_hora", "parametros": {}},
    "horas": {"acao": "informar_hora", "parametros": {}},
    "data": {"acao": "informar_data", "parametros": {}},
    "dia": {"acao": "informar_data", "parametros": {}},
    # ── Navegador (AtalhoNav) ──
    "abrir nova aba": {"acao": "nova_aba", "parametros": {}},
    "abrir nova guia": {"acao": "nova_aba", "parametros": {}},
    "aba anterior": {"acao": "aba_anterior", "parametros": {}},
    "barra endereco": {"acao": "barra_endereco", "parametros": {}},
    "pagina inicial": {"acao": "pagina_inicial", "parametros": {}},
    "janela anonima": {"acao": "janela_anonima", "parametros": {}},
    "zoom padrao": {"acao": "zoom_padrao", "parametros": {}},
    "abrir devtools": {"acao": "devtools", "parametros": {}},
}

CATALOGO_SITES: Dict[str, SiteInfo] = {
    # ── Pesquisa ──
    "google": SiteInfo(
        nome="google",
        url="https://www.google.com",
        sinonimos=["google", "googlar"],
        categoria="pesquisa",
    ),
    "bing": SiteInfo(
        nome="bing",
        url="https://www.bing.com",
        sinonimos=["bing"],
        categoria="pesquisa",
    ),
    "duckduckgo": SiteInfo(
        nome="duckduckgo",
        url="https://duckduckgo.com",
        sinonimos=["duckduckgo"],
        categoria="pesquisa",
    ),
    "yahoo": SiteInfo(
        nome="yahoo",
        url="https://www.yahoo.com",
        sinonimos=["yahoo"],
        categoria="pesquisa",
    ),
    "ecosia": SiteInfo(
        nome="ecosia",
        url="https://www.ecosia.org",
        sinonimos=["ecosia"],
        categoria="pesquisa",
    ),
    # ── Inteligência Artificial ──
    "chatgpt": SiteInfo(
        nome="chatgpt",
        url="https://chatgpt.com",
        sinonimos=["chatgpt", "chat gpt", "gpt", "openai chat"],
        categoria="inteligencia_artificial",
    ),
    "claude": SiteInfo(
        nome="claude",
        url="https://claude.ai",
        sinonimos=["claude", "claude ai", "anthropic"],
        categoria="inteligencia_artificial",
    ),
    "gemini": SiteInfo(
        nome="gemini",
        url="https://gemini.google.com",
        sinonimos=["gemini", "google gemini", "bard"],
        categoria="inteligencia_artificial",
    ),
    "copilot": SiteInfo(
        nome="copilot",
        url="https://copilot.microsoft.com",
        sinonimos=["copilot", "microsoft copilot"],
        categoria="inteligencia_artificial",
    ),
    "perplexity": SiteInfo(
        nome="perplexity",
        url="https://www.perplexity.ai",
        sinonimos=["perplexity", "perplexity ai"],
        categoria="inteligencia_artificial",
    ),
    "poe": SiteInfo(
        nome="poe",
        url="https://poe.com",
        sinonimos=["poe"],
        categoria="inteligencia_artificial",
    ),
    "huggingface": SiteInfo(
        nome="huggingface",
        url="https://huggingface.co",
        sinonimos=["huggingface", "hugging face", "hf"],
        categoria="inteligencia_artificial",
    ),
    "ollama": SiteInfo(
        nome="ollama",
        url="https://ollama.ai",
        sinonimos=["ollama"],
        categoria="inteligencia_artificial",
    ),
    "openrouter": SiteInfo(
        nome="openrouter",
        url="https://openrouter.ai",
        sinonimos=["openrouter", "open router"],
        categoria="inteligencia_artificial",
    ),
    # ── Programação ──
    "github": SiteInfo(
        nome="github",
        url="https://github.com",
        sinonimos=["github", "git hub"],
        categoria="programacao",
    ),
    "gitlab": SiteInfo(
        nome="gitlab",
        url="https://gitlab.com",
        sinonimos=["gitlab", "git lab"],
        categoria="programacao",
    ),
    "bitbucket": SiteInfo(
        nome="bitbucket",
        url="https://bitbucket.org",
        sinonimos=["bitbucket", "bit bucket"],
        categoria="programacao",
    ),
    "stackoverflow": SiteInfo(
        nome="stackoverflow",
        url="https://stackoverflow.com",
        sinonimos=["stackoverflow", "stack overflow", "so"],
        categoria="programacao",
    ),
    "python": SiteInfo(
        nome="python",
        url="https://www.python.org",
        sinonimos=["python", "python org"],
        categoria="programacao",
    ),
    "pypi": SiteInfo(
        nome="pypi",
        url="https://pypi.org",
        sinonimos=["pypi", "pip"],
        categoria="programacao",
    ),
    "dockerhub": SiteInfo(
        nome="dockerhub",
        url="https://hub.docker.com",
        sinonimos=["dockerhub", "docker hub", "docker"],
        categoria="programacao",
    ),
    "npm": SiteInfo(
        nome="npm",
        url="https://www.npmjs.com",
        sinonimos=["npm", "npmjs"],
        categoria="programacao",
    ),
    "vscodemarketplace": SiteInfo(
        nome="vscodemarketplace",
        url="https://marketplace.visualstudio.com",
        sinonimos=["vscode marketplace", "visual studio marketplace", "extensions vscode"],
        categoria="programacao",
    ),
    "jetbrains": SiteInfo(
        nome="jetbrains",
        url="https://www.jetbrains.com",
        sinonimos=["jetbrains", "jet brains", "intellij"],
        categoria="programacao",
    ),
    # ── Google ──
    "gmail": SiteInfo(
        nome="gmail",
        url="https://mail.google.com",
        sinonimos=["gmail", "google mail", "email google", "correio google"],
        categoria="google",
    ),
    "googledrive": SiteInfo(
        nome="googledrive",
        url="https://drive.google.com",
        sinonimos=["google drive", "drive google", "google drive"],
        categoria="google",
    ),
    "googledocs": SiteInfo(
        nome="googledocs",
        url="https://docs.google.com",
        sinonimos=["google docs", "docs google", "documentos google"],
        categoria="google",
    ),
    "googlesheets": SiteInfo(
        nome="googlesheets",
        url="https://sheets.google.com",
        sinonimos=["google sheets", "sheets google", "planilhas google"],
        categoria="google",
    ),
    "googleslides": SiteInfo(
        nome="googleslides",
        url="https://slides.google.com",
        sinonimos=["google slides", "slides google", "apresentacoes google"],
        categoria="google",
    ),
    "googleforms": SiteInfo(
        nome="googleforms",
        url="https://forms.google.com",
        sinonimos=["google forms", "forms google", "formularios google"],
        categoria="google",
    ),
    "googlemeet": SiteInfo(
        nome="googlemeet",
        url="https://meet.google.com",
        sinonimos=["google meet", "meet google", "google meetings"],
        categoria="google",
    ),
    "googleagenda": SiteInfo(
        nome="googleagenda",
        url="https://calendar.google.com",
        sinonimos=["google agenda", "google calendar", "calendar google", "agenda google"],
        categoria="google",
    ),
    "googlemaps": SiteInfo(
        nome="googlemaps",
        url="https://maps.google.com",
        sinonimos=["google maps", "maps google", "mapas google"],
        categoria="google",
    ),
    "googletradutor": SiteInfo(
        nome="googletradutor",
        url="https://translate.google.com",
        sinonimos=["google tradutor", "translate google", "google translate", "tradutor google"],
        categoria="google",
    ),
    "googlefotos": SiteInfo(
        nome="googlefotos",
        url="https://photos.google.com",
        sinonimos=["google fotos", "photos google", "google photos", "fotos google"],
        categoria="google",
    ),
    "googlekeep": SiteInfo(
        nome="googlekeep",
        url="https://keep.google.com",
        sinonimos=["google keep", "keep google", "google notas"],
        categoria="google",
    ),
    # ── Microsoft ──
    "outlook": SiteInfo(
        nome="outlook",
        url="https://outlook.live.com",
        sinonimos=["outlook", "outlook live", "hotmail", "email microsoft"],
        categoria="microsoft",
    ),
    "onedrive": SiteInfo(
        nome="onedrive",
        url="https://onedrive.live.com",
        sinonimos=["onedrive", "one drive", "microsoft onedrive"],
        categoria="microsoft",
    ),
    "teams": SiteInfo(
        nome="teams",
        url="https://teams.microsoft.com",
        sinonimos=["teams", "microsoft teams", "teams microsoft"],
        categoria="microsoft",
    ),
    "microsoft365": SiteInfo(
        nome="microsoft365",
        url="https://www.office.com",
        sinonimos=["microsoft 365", "office 365", "office", "microsoft office"],
        categoria="microsoft",
    ),
    "azure": SiteInfo(
        nome="azure",
        url="https://portal.azure.com",
        sinonimos=["azure", "microsoft azure", "azure portal"],
        categoria="microsoft",
    ),
    "powerbi": SiteInfo(
        nome="powerbi",
        url="https://app.powerbi.com",
        sinonimos=["power bi", "powerbi", "microsoft power bi"],
        categoria="microsoft",
    ),
    # ── Trabalho ──
    "notion": SiteInfo(
        nome="notion",
        url="https://www.notion.so",
        sinonimos=["notion"],
        categoria="trabalho",
    ),
    "trello": SiteInfo(
        nome="trello",
        url="https://trello.com",
        sinonimos=["trello"],
        categoria="trabalho",
    ),
    "jira": SiteInfo(
        nome="jira",
        url="https://www.atlassian.com/software/jira",
        sinonimos=["jira", "jira software"],
        categoria="trabalho",
    ),
    "confluence": SiteInfo(
        nome="confluence",
        url="https://www.atlassian.com/software/confluence",
        sinonimos=["confluence"],
        categoria="trabalho",
    ),
    "slack": SiteInfo(
        nome="slack",
        url="https://slack.com",
        sinonimos=["slack"],
        categoria="trabalho",
    ),
    "zoom": SiteInfo(
        nome="zoom",
        url="https://zoom.us",
        sinonimos=["zoom"],
        categoria="trabalho",
    ),
    "canva": SiteInfo(
        nome="canva",
        url="https://www.canva.com",
        sinonimos=["canva"],
        categoria="trabalho",
    ),
    "figma": SiteInfo(
        nome="figma",
        url="https://www.figma.com",
        sinonimos=["figma"],
        categoria="trabalho",
    ),
    "miro": SiteInfo(
        nome="miro",
        url="https://miro.com",
        sinonimos=["miro", "miro board", "realtime board"],
        categoria="trabalho",
    ),
    "clickup": SiteInfo(
        nome="clickup",
        url="https://clickup.com",
        sinonimos=["clickup", "click up"],
        categoria="trabalho",
    ),
    "monday": SiteInfo(
        nome="monday",
        url="https://monday.com",
        sinonimos=["monday", "monday.com", "monday dot com"],
        categoria="trabalho",
    ),
    "asana": SiteInfo(
        nome="asana",
        url="https://asana.com",
        sinonimos=["asana"],
        categoria="trabalho",
    ),
    # ── Redes Sociais ──
    "youtube": SiteInfo(
        nome="youtube",
        url="https://www.youtube.com",
        sinonimos=["youtube", "you tube", "yt"],
        categoria="redes_sociais",
    ),
    "facebook": SiteInfo(
        nome="facebook",
        url="https://www.facebook.com",
        sinonimos=["facebook", "face", "fb", "face book"],
        categoria="redes_sociais",
    ),
    "instagram": SiteInfo(
        nome="instagram",
        url="https://www.instagram.com",
        sinonimos=["instagram", "insta", "ig"],
        categoria="redes_sociais",
    ),
    "threads": SiteInfo(
        nome="threads",
        url="https://www.threads.net",
        sinonimos=["threads", "threads net"],
        categoria="redes_sociais",
    ),
    "x": SiteInfo(
        nome="x",
        url="https://x.com",
        sinonimos=["x", "twitter"],
        categoria="redes_sociais",
    ),
    "tiktok": SiteInfo(
        nome="tiktok",
        url="https://www.tiktok.com",
        sinonimos=["tiktok", "tik tok", "tt"],
        categoria="redes_sociais",
    ),
    "linkedin": SiteInfo(
        nome="linkedin",
        url="https://www.linkedin.com",
        sinonimos=["linkedin", "linked in", "in"],
        categoria="redes_sociais",
    ),
    "reddit": SiteInfo(
        nome="reddit",
        url="https://www.reddit.com",
        sinonimos=["reddit", "redd"],
        categoria="redes_sociais",
    ),
    "discord": SiteInfo(
        nome="discord",
        url="https://discord.com",
        sinonimos=["discord"],
        categoria="redes_sociais",
    ),
    "pinterest": SiteInfo(
        nome="pinterest",
        url="https://www.pinterest.com",
        sinonimos=["pinterest", "pins"],
        categoria="redes_sociais",
    ),
    # ── Streaming ──
    "netflix": SiteInfo(
        nome="netflix",
        url="https://www.netflix.com",
        sinonimos=["netflix", "net flex", "netflix.com"],
        categoria="streaming",
    ),
    "primevideo": SiteInfo(
        nome="primevideo",
        url="https://www.primevideo.com",
        sinonimos=["prime video", "primevideo", "amazon prime video", "amazon prime"],
        categoria="streaming",
    ),
    "disneyplus": SiteInfo(
        nome="disneyplus",
        url="https://www.disneyplus.com",
        sinonimos=["disney plus", "disneyplus", "disney+"],
        categoria="streaming",
    ),
    "max": SiteInfo(
        nome="max",
        url="https://www.max.com",
        sinonimos=["max", "hbo max", "hbomax"],
        categoria="streaming",
    ),
    "crunchyroll": SiteInfo(
        nome="crunchyroll",
        url="https://www.crunchyroll.com",
        sinonimos=["crunchyroll", "crunchy roll"],
        categoria="streaming",
    ),
    "spotify": SiteInfo(
        nome="spotify",
        url="https://open.spotify.com",
        sinonimos=["spotify", "spotify web", "spotify player"],
        categoria="streaming",
    ),
    "deezer": SiteInfo(
        nome="deezer",
        url="https://www.deezer.com",
        sinonimos=["deezer"],
        categoria="streaming",
    ),
    "twitch": SiteInfo(
        nome="twitch",
        url="https://www.twitch.tv",
        sinonimos=["twitch", "twitch tv", "twitch.tv"],
        categoria="streaming",
    ),
    # ── Compras ──
    "amazon": SiteInfo(
        nome="amazon",
        url="https://www.amazon.com.br",
        sinonimos=["amazon", "amazon brasil"],
        categoria="compras",
    ),
    "mercadolivre": SiteInfo(
        nome="mercadolivre",
        url="https://www.mercadolivre.com.br",
        sinonimos=["mercado livre", "mercadolivre", "ml"],
        categoria="compras",
    ),
    "shopee": SiteInfo(
        nome="shopee",
        url="https://shopee.com.br",
        sinonimos=["shopee", "shoppe"],
        categoria="compras",
    ),
    "aliexpress": SiteInfo(
        nome="aliexpress",
        url="https://www.aliexpress.com",
        sinonimos=["aliexpress", "ali express", "aliex"],
        categoria="compras",
    ),
    "magazineluiza": SiteInfo(
        nome="magazineluiza",
        url="https://www.magazineluiza.com.br",
        sinonimos=["magazine luiza", "magazineluiza", "magalu"],
        categoria="compras",
    ),
    "kabum": SiteInfo(
        nome="kabum",
        url="https://www.kabum.com.br",
        sinonimos=["kabum", "ka bumm", "ka bu m"],
        categoria="compras",
    ),
    "casasbahia": SiteInfo(
        nome="casasbahia",
        url="https://www.casasbahia.com.br",
        sinonimos=["casas bahia", "casasbahia"],
        categoria="compras",
    ),
    # ── Bancos ──
    "nubank": SiteInfo(
        nome="nubank",
        url="https://nubank.com.br",
        sinonimos=["nubank", "nu bank", "nu"],
        categoria="bancos",
    ),
    "bancodobrasil": SiteInfo(
        nome="bancodobrasil",
        url="https://www.bb.com.br",
        sinonimos=["banco do brasil", "bancodobrasil", "bb", "banco brasil"],
        categoria="bancos",
    ),
    "caixa": SiteInfo(
        nome="caixa",
        url="https://www.caixa.gov.br",
        sinonimos=["caixa", "caixa economica", "cef"],
        categoria="bancos",
    ),
    "itau": SiteInfo(
        nome="itau",
        url="https://www.itau.com.br",
        sinonimos=["itau", "itau", "banco itau"],
        categoria="bancos",
    ),
    "bradesco": SiteInfo(
        nome="bradesco",
        url="https://www.bradesco.com.br",
        sinonimos=["bradesco", "banco bradesco"],
        categoria="bancos",
    ),
    "santander": SiteInfo(
        nome="santander",
        url="https://www.santander.com.br",
        sinonimos=["santander", "banco santander"],
        categoria="bancos",
    ),
    "inter": SiteInfo(
        nome="inter",
        url="https://www.bancointer.com.br",
        sinonimos=["inter", "banco inter", "bancointer"],
        categoria="bancos",
    ),
    "c6bank": SiteInfo(
        nome="c6bank",
        url="https://www.c6bank.com.br",
        sinonimos=["c6 bank", "c6bank", "c6"],
        categoria="bancos",
    ),
    "picpay": SiteInfo(
        nome="picpay",
        url="https://picpay.com.br",
        sinonimos=["picpay", "pic pay"],
        categoria="bancos",
    ),
    # ── Educação ──
    "coursera": SiteInfo(
        nome="coursera",
        url="https://www.coursera.org",
        sinonimos=["coursera"],
        categoria="educacao",
    ),
    "udemy": SiteInfo(
        nome="udemy",
        url="https://www.udemy.com",
        sinonimos=["udemy"],
        categoria="educacao",
    ),
    "alura": SiteInfo(
        nome="alura",
        url="https://www.alura.com.br",
        sinonimos=["alura", "alura cursos", "alura online"],
        categoria="educacao",
    ),
    "khanacademy": SiteInfo(
        nome="khanacademy",
        url="https://www.khanacademy.org",
        sinonimos=["khan academy", "khanacademy"],
        categoria="educacao",
    ),
    "edx": SiteInfo(
        nome="edx",
        url="https://www.edx.org",
        sinonimos=["edx", "edx org"],
        categoria="educacao",
    ),
    "duolingo": SiteInfo(
        nome="duolingo",
        url="https://www.duolingo.com",
        sinonimos=["duolingo", "duo lingo"],
        categoria="educacao",
    ),
    "w3schools": SiteInfo(
        nome="w3schools",
        url="https://www.w3schools.com",
        sinonimos=["w3schools", "w3 schools", "w3"],
        categoria="educacao",
    ),
    "mdnwebdocs": SiteInfo(
        nome="mdnwebdocs",
        url="https://developer.mozilla.org",
        sinonimos=["mdn", "mdn web docs", "mozilla developer", "developer mozilla"],
        categoria="educacao",
    ),
    # ── Notícias ──
    "g1": SiteInfo(
        nome="g1",
        url="https://g1.globo.com",
        sinonimos=["g1", "globo g1", "g1 globo"],
        categoria="noticias",
    ),
    "uol": SiteInfo(
        nome="uol",
        url="https://www.uol.com.br",
        sinonimos=["uol", "universo online"],
        categoria="noticias",
    ),
    "cnnbrasil": SiteInfo(
        nome="cnnbrasil",
        url="https://www.cnnbrasil.com.br",
        sinonimos=["cnn brasil", "cnnbrasil", "cnn"],
        categoria="noticias",
    ),
    "bbc": SiteInfo(
        nome="bbc",
        url="https://www.bbc.com",
        sinonimos=["bbc", "bbc news", "bbc news brasil"],
        categoria="noticias",
    ),
    "reuters": SiteInfo(
        nome="reuters",
        url="https://www.reuters.com",
        sinonimos=["reuters", "reuters news"],
        categoria="noticias",
    ),
    "folhadespaulo": SiteInfo(
        nome="folhadespaulo",
        url="https://www.folha.uol.com.br",
        sinonimos=["folha de sao paulo", "folha", "folhadespaulo", "folha de s.paulo"],
        categoria="noticias",
    ),
    "estadao": SiteInfo(
        nome="estadao",
        url="https://www.estadao.com.br",
        sinonimos=["estadao", "estadão", "o estado de sao paulo"],
        categoria="noticias",
    ),
}


def _construir_mapa_sites() -> Dict[str, str]:
    mapa: Dict[str, str] = {}
    for site_nome, site_info in CATALOGO_SITES.items():
 
        mapa[site_nome] = site_nome
        for sinonimo in site_info.sinonimos:
            mapa[sinonimo] = site_nome
    return mapa


MAPA_SITES: Dict[str, str] = _construir_mapa_sites()
