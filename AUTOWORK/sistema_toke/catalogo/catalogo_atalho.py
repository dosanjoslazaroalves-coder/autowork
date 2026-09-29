from typing import Dict, List, TypedDict

class AtalhoInfo(TypedDict):
    nome: str
    sinonimos: List[str]
    categoria: str

# Palavras que descrevem o verbo, não o alvo. O parser ignora estas
# ao pontuar um objeto contra o catálogo (evita "abrir" casar com qualquer atalho).
SINONIMOS_GENERICOS: List[str] = [
    "abrir", "fechar", "encerrar", "sair",
    "mostrar", "exibir", "ver",
    "alternar", "trocar", "mudar",
    "navegar", "ir", "vai",
    "iniciar", "executar", "rodar",
    "nova", "novo",
    "mais", "menos",
]

CATALOGO_ATALHOS: Dict[str, AtalhoInfo] = {
    # ── Janela (Windows) ──
    # Alt+F4 fecha a janela em primeiro plano.
    "fechar_janela": {
        "nome": "fechar_janela",
        "sinonimos": [
            "fechar", "encerrar", "sair",
            "janela", "tela", "app", "aplicativo", "programa",
            "essa janela", "esta janela", "essa tela",
        ],
        "categoria": "janela",
    },
    # Alt+Tab alterna a janela em primeiro plano.
    "alternar_janelas": {
        "nome": "alternar_janelas",
        "sinonimos": [
            "alternar", "trocar", "mudar",
            "janela", "janelas", "aplicativo", "app",
            "outra janela", "proxima janela", "próxima janela",
            "de janela", "trocar janela", "troca de janela",
        ],
        "categoria": "janela",
    },
    # Win+D mostra/oculta a área de trabalho.
    "mostrar_area_de_trabalho": {
        "nome": "mostrar_area_de_trabalho",
        "sinonimos": [
            "mostrar", "exibir",
            "area", "área", "trabalho",
            "area de trabalho", "área de trabalho",
            "desktop", "mesa",
        ],
        "categoria": "janela",
    },
    # Win+Up maximiza a janela ativa.
    "maximizar_janela": {
        "nome": "maximizar_janela",
        "sinonimos": [
            "maximizar", "ampliar",
            "janela",
            "tela cheia janela", "janela maximizada",
            "maximiza janela", "maximize janela",
        ],
        "categoria": "janela",
    },
    # Win+Down restaura (se maximizada) ou minimiza a janela ativa.
    "restaurar_ou_minimizar_janela": {
        "nome": "restaurar_ou_minimizar_janela",
        "sinonimos": [
            "restaurar", "minimizar",
            "janela", "janelas", "tela", "telas", "tudo",
            "essa janela", "esta janela",
        ],
        "categoria": "janela",
    },
    # Win+Left encaixa à esquerda.
    "mover_janela_esquerda": {
        "nome": "mover_janela_esquerda",
        "sinonimos": [
            "mover", "encaixar",
            "esquerda", "lado esquerdo", "janela esquerda",
        ],
        "categoria": "janela",
    },
    # Win+Right encaixa à direita.
    "mover_janela_direita": {
        "nome": "mover_janela_direita",
        "sinonimos": [
            "mover", "encaixar",
            "direita", "lado direito", "janela direita",
        ],
        "categoria": "janela",
    },
    # Win+Tab abre a Visão de Tarefas.
    "abrir_visao_de_tarefas": {
        "nome": "abrir_visao_de_tarefas",
        "sinonimos": [
            "tarefas", "visao de tarefas", "visão de tarefas",
            "visao tarefas", "multitarefa",
        ],
        "categoria": "janela",
    },
    # LockWorkStation / equivalente a Win+L. Não confundir com desligar.
    "bloquear_tela": {
        "nome": "bloquear_tela",
        "sinonimos": [
            "bloquear", "travar",
            "tela", "pc", "computador", "maquina", "máquina",
            "sessao", "sessão", "windows",
            "bloquear tela", "trava tela", "bloquear computador",
        ],
        "categoria": "janela",
    },

    # ── Navegador (atalhos Chromium/Edge/Chrome; Firefox equivalente salvo nota) ──
    # Ctrl+T
    "nova_aba": {
        "nome": "nova_aba",
        "sinonimos": [
            "nova", "abrir", "guia", "aba",
            "nova aba", "nova guia", "outra aba", "aba nova",
            "tab",
        ],
        "categoria": "navegador",
    },
    # Ctrl+W
    "fechar_aba": {
        "nome": "fechar_aba",
        "sinonimos": [
            "fechar", "aba", "guia", "tab",
            "essa aba", "esta aba", "aba atual",
        ],
        "categoria": "navegador",
    },
    # Ctrl+Shift+T
    "reabrir_aba": {
        "nome": "reabrir_aba",
        "sinonimos": [
            "reabrir", "aba fechada", "guia fechada",
            "ultima aba", "última aba", "aba anterior fechada",
        ],
        "categoria": "navegador",
    },
    # Ctrl+Tab
    "proxima_aba": {
        "nome": "proxima_aba",
        "sinonimos": [
            "proxima", "próxima", "proximo", "próximo",
            "proxima aba", "próxima aba", "proxima guia",
            "aba seguinte",
        ],
        "categoria": "navegador",
    },
    # Ctrl+Shift+Tab
    "aba_anterior": {
        "nome": "aba_anterior",
        "sinonimos": [
            "aba anterior", "guia anterior",
            "aba", "guia",
        ],
        "categoria": "navegador",
    },
    # F5
    "atualizar_pagina": {
        "nome": "atualizar_pagina",
        "sinonimos": [
            "atualizar", "recarregar",
            "pagina", "página", "site",
            "essa pagina", "esta pagina", "essa página",
        ],
        "categoria": "navegador",
    },
    # Ctrl+F5 (hard refresh; comum no Chromium)
    "atualizacao_forcada": {
        "nome": "atualizacao_forcada",
        "sinonimos": [
            "forcada", "forçada", "forcado", "forçado",
            "forcar", "forçar",
            "atualizacao forcada", "atualização forçada",
            "recarregar forcado", "hard refresh",
        ],
        "categoria": "navegador",
    },
    # Ctrl+L
    "barra_endereco": {
        "nome": "barra_endereco",
        "sinonimos": [
            "endereco", "endereço", "url",
            "barra endereco", "barra de endereco", "barra de endereço",
            "caixa de pesquisa",
        ],
        "categoria": "navegador",
    },
    # Alt+Left
    "voltar_pagina": {
        "nome": "voltar_pagina",
        "sinonimos": [
            "voltar", "retornar",
            "pagina", "página",
            "pagina anterior", "página anterior",
            "site anterior", "voltar pagina",
        ],
        "categoria": "navegador",
    },
    # Alt+Right
    "avancar_pagina": {
        "nome": "avancar_pagina",
        "sinonimos": [
            "avancar", "avançar",
            "pagina", "página",
            "proxima pagina", "próxima página",
            "avancar pagina",
        ],
        "categoria": "navegador",
    },
    # Alt+Home
    "pagina_inicial": {
        "nome": "pagina_inicial",
        "sinonimos": [
            "inicial", "home",
            "pagina inicial", "página inicial",
            "inicio", "início",
        ],
        "categoria": "navegador",
    },
    # Ctrl+H
    "historico": {
        "nome": "historico",
        "sinonimos": [
            "historico", "histórico",
            "historico de navegacao", "histórico de navegação",
        ],
        "categoria": "navegador",
    },
    # Ctrl+J
    "downloads": {
        "nome": "downloads",
        "sinonimos": [
            "download", "downloads",
            "baixados", "downloads do navegador",
        ],
        "categoria": "navegador",
    },
    # Ctrl+D adiciona/abre o diálogo de favorito da página atual (Chromium).
    "favoritos": {
        "nome": "favoritos",
        "sinonimos": [
            "favorito", "favoritos", "marcadores",
            "bookmarks", "estrelinha",
        ],
        "categoria": "navegador",
    },
    # Ctrl+F
    "buscar_na_pagina": {
        "nome": "buscar_na_pagina",
        "sinonimos": [
            "buscar", "pesquisar", "localizar",
            "na pagina", "na página",
            "nessa pagina", "nesta pagina",
            "localizar na pagina", "buscar na pagina",
            "achar na pagina",
        ],
        "categoria": "navegador",
    },
    # Ctrl+Shift+N no Chromium; Firefox usa Ctrl+Shift+P.
    "janela_anonima": {
        "nome": "janela_anonima",
        "sinonimos": [
            "anonima", "anônima", "anonimo", "anônimo",
            "privada", "privado", "incognito", "incógnito",
            "janela anonima", "janela privada", "modo privado",
        ],
        "categoria": "navegador",
    },
    # Ctrl+N
    "nova_janela": {
        "nome": "nova_janela",
        "sinonimos": [
            "nova janela", "outra janela navegador",
        ],
        "categoria": "navegador",
    },
    # Ctrl+Shift+W fecha a janela do navegador (não a aba).
    "fechar_janela_nav": {
        "nome": "fechar_janela_nav",
        "sinonimos": [
            "janela navegador", "fechar janela navegador",
        ],
        "categoria": "navegador",
    },
    # Ctrl+S
    "salvar_pagina": {
        "nome": "salvar_pagina",
        "sinonimos": [
            "salvar", "salvar pagina", "salvar página",
        ],
        "categoria": "navegador",
    },
    # Ctrl+P
    "imprimir_pagina": {
        "nome": "imprimir_pagina",
        "sinonimos": [
            "imprimir", "imprimir pagina", "imprimir página",
        ],
        "categoria": "navegador",
    },
    # Ctrl++
    "zoom_mais": {
        "nome": "zoom_mais",
        "sinonimos": [
            "aumentar", "ampliar", "mais",
            "zoom", "aumentar zoom", "zoom mais",
        ],
        "categoria": "navegador",
    },
    # Ctrl+-
    "zoom_menos": {
        "nome": "zoom_menos",
        "sinonimos": [
            "diminuir", "menos", "reduzir",
            "zoom", "diminuir zoom", "zoom menos",
        ],
        "categoria": "navegador",
    },
    # Ctrl+0
    "zoom_padrao": {
        "nome": "zoom_padrao",
        "sinonimos": [
            "padrao", "padrão", "normal", "reseta", "resetar",
            "zoom padrao", "zoom padrão", "zoom normal",
        ],
        "categoria": "navegador",
    },
    # F12 (ou Ctrl+Shift+I). Intenção canônica de DevTools/inspetor.
    "devtools": {
        "nome": "devtools",
        "sinonimos": [
            "devtools", "dev tools", "devtool",
            "depurar", "debug", "debugar",
            "inspetor", "inspector", "inspecionar",
            "ferramentas", "desenvolvedor", "desenvolvedores",
            "ferramentas desenvolvedor", "ferramentas do desenvolvedor",
            "elementos", "elemento",
            "console desenvolvedor",
        ],
        "categoria": "navegador",
    },
    # Ctrl+Shift+C — modo de inspecionar elemento (picker).
    "inspecionar_elemento": {
        "nome": "inspecionar_elemento",
        "sinonimos": [
            "inspecionar elemento", "picker",
            "selecionar elemento",
        ],
        "categoria": "navegador",
    },
    # F11 tela cheia no navegador.
    "tela_cheia": {
        "nome": "tela_cheia",
        "sinonimos": [
            "tela cheia", "fullscreen", "full screen",
            "tela inteira", "modo tela cheia",
        ],
        "categoria": "navegador",
    },
    # Ctrl+U código-fonte da página.
    "codigo_fonte": {
        "nome": "codigo_fonte",
        "sinonimos": [
            "codigo", "código", "fonte",
            "codigo fonte", "código-fonte", "codigo-fonte",
            "source", "view source",
            "codigo da pagina", "código da página",
            "codigo pagina",
        ],
        "categoria": "navegador",
    },
    # Ctrl+Shift+J no Chromium/Edge. Firefox: Ctrl+Shift+K.
    "console": {
        "nome": "console",
        "sinonimos": [
            "console", "console do navegador",
            "javascript console", "js console",
        ],
        "categoria": "navegador",
    },
}
