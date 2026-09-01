from typing import Dict, List, TypedDict

class AtalhoInfo(TypedDict):
    nome: str
    sinonimos: List[str]
    categoria: str

CATALOGO_ATALHOS: Dict[str, AtalhoInfo] = {
    # ── Janela ──
    "fechar_janela": {"nome": "fechar_janela", "sinonimos": ["fechar", "encerrar", "sair"], "categoria": "janela"},
    "alternar_janelas": {"nome": "alternar_janelas", "sinonimos": ["alternar", "trocar", "mudar"], "categoria": "janela"},
    "mostrar_area_de_trabalho": {"nome": "mostrar_area_de_trabalho", "sinonimos": ["mostrar", "exibir"], "categoria": "janela"},
    "maximizar_janela": {"nome": "maximizar_janela", "sinonimos": ["maximizar", "ampliar"], "categoria": "janela"},
    "restaurar_ou_minimizar_janela": {"nome": "restaurar_ou_minimizar_janela", "sinonimos": ["restaurar", "minimizar"], "categoria": "janela"},
    "encaixar_janela_esquerda": {"nome": "encaixar_janela_esquerda", "sinonimos": ["encaixar"], "categoria": "janela"},
    "encaixar_janela_direita": {"nome": "encaixar_janela_direita", "sinonimos": ["encaixar"], "categoria": "janela"},
    "abrir_visao_de_tarefas": {"nome": "abrir_visao_de_tarefas", "sinonimos": ["tarefas"], "categoria": "janela"},
    "bloquear_tela": {"nome": "bloquear_tela", "sinonimos": ["bloquear", "travar"], "categoria": "janela"},
    
    # ── Navegador ──
    "nova_aba": {"nome": "nova_aba", "sinonimos": ["nova", "abrir", "guia"], "categoria": "navegador"},
    "fechar_aba": {"nome": "fechar_aba", "sinonimos": ["fechar"], "categoria": "navegador"},
    "reabrir_aba": {"nome": "reabrir_aba", "sinonimos": ["reabrir"], "categoria": "navegador"},
    "proxima_aba": {"nome": "proxima_aba", "sinonimos": ["proxima", "proximo", "navegar"], "categoria": "navegador"},
    "aba_anterior": {"nome": "aba_anterior", "sinonimos": ["anterior", "voltar"], "categoria": "navegador"},
    "atualizar_pagina": {"nome": "atualizar_pagina", "sinonimos": ["atualizar", "recarregar"], "categoria": "navegador"},
    "atualizacao_forcada": {"nome": "atualizacao_forcada", "sinonimos": ["forcada", "forcar"], "categoria": "navegador"},
    "barra_endereco": {"nome": "barra_endereco", "sinonimos": ["endereco", "url"], "categoria": "navegador"},
    "voltar_pagina": {"nome": "voltar_pagina", "sinonimos": ["voltar", "retornar"], "categoria": "navegador"},
    "avancar_pagina": {"nome": "avancar_pagina", "sinonimos": ["avancar"], "categoria": "navegador"},
    "pagina_inicial": {"nome": "pagina_inicial", "sinonimos": ["inicial", "home"], "categoria": "navegador"},
    "historico": {"nome": "historico", "sinonimos": ["historico"], "categoria": "navegador"},
    "downloads": {"nome": "downloads", "sinonimos": ["download", "downloads"], "categoria": "navegador"},
    "favoritos": {"nome": "favoritos", "sinonimos": ["favorito", "favoritos", "marcadores"], "categoria": "navegador"},
    "buscar_na_pagina": {"nome": "buscar_na_pagina", "sinonimos": ["buscar", "pesquisar"], "categoria": "navegador"},
    "janela_anonima": {"nome": "janela_anonima", "sinonimos": ["anonima", "anonimo", "privada"], "categoria": "navegador"},
    "nova_janela": {"nome": "nova_janela", "sinonimos": ["nova"], "categoria": "navegador"},
    "fechar_janela_nav": {"nome": "fechar_janela_nav", "sinonimos": ["fechar"], "categoria": "navegador"},
    "salvar_pagina": {"nome": "salvar_pagina", "sinonimos": ["salvar"], "categoria": "navegador"},
    "imprimir_pagina": {"nome": "imprimir_pagina", "sinonimos": ["imprimir"], "categoria": "navegador"},
    "zoom_mais": {"nome": "zoom_mais", "sinonimos": ["aumentar", "ampliar", "mais"], "categoria": "navegador"},
    "zoom_menos": {"nome": "zoom_menos", "sinonimos": ["diminuir", "menos", "reduzir"], "categoria": "navegador"},
    "zoom_padrao": {"nome": "zoom_padrao", "sinonimos": ["padrao", "normal", "reseta"], "categoria": "navegador"},
    "devtools": {"nome": "devtools", "sinonimos": ["devtools", "depurar"], "categoria": "navegador"},
    "inspecionar_elemento": {"nome": "inspecionar_elemento", "sinonimos": ["inspecionar", "inspecione", "elemento"], "categoria": "navegador"},
}
