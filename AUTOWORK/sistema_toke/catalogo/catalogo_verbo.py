from typing import Set, Dict

VERBOS_ABRIR: Set[str] = frozenset({
    "abrir", "abra", "abre", "abrindo",
    "executar", "execute", "executa",
    "iniciar", "inicie", "inicia",
    "rodar", "rode", "roda",
    "lançar", "lancar", "lanca", "lance",
    "chamar", "chama", "chame",
})

VERBOS_ABRIR_SITE: Set[str] = frozenset({
    "abrir site", "abra site", "abre site", "abrindo site",
    "executar site", "execute site", "executa site",
    "iniciar site", "inicie site", "inicia site",
    "rodar site", "rode site",
    "acessar", "acessa", "acesse",
    "entrar", "entra", "entre",
})

VERBO_ABRIR_SITE_CANONICO = "abrir site"

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
    "ver",
    "expor", "expoe", "exponha",
})

VERBOS_MAXIMIZAR: Set[str] = frozenset({
    "maximizar", "maximiza", "maximize",
    "ampliar", "amplia", "amplie",
})

VERBOS_RESTAURAR: Set[str] = frozenset({
    "restaurar", "restaura", "restaure",
    "minimizar", "minimiza", "minimize",
    "esconder", "esconde", "esconda",
})

VERBOS_ENCAIXAR: Set[str] = frozenset({
    "encaixar", "encaixa", "encaixe",
})

VERBOS_BLOQUEAR: Set[str] = frozenset({
    "bloquear", "bloqueia", "bloqueie",
    "travar", "trava", "trave",
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
    "avançar", "avança",
})

VERBOS_BUSCAR: Set[str] = frozenset({
    "buscar", "busca", "busque",
    "pesquisar", "pesquisa", "pesquise",
    "localizar", "localiza", "localize",
    "procurar", "procura", "procure",
    "achar", "acha", "ache",
    "encontrar", "encontra", "encontre",
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
    "debugar", "debuga", "debugue",
})

MAPA_VERBOS: Dict[str, str] = {
    "abrir": "abrir", "abra": "abrir", "abre": "abrir", "abrindo": "abrir",
    "abrir site": "abrir site", "abra site": "abrir site", "abre site": "abrir site",
    "acessar": "abrir", "acessa": "abrir", "acesse": "abrir",
    "entrar": "abrir", "entra": "abrir", "entre": "abrir",
    "executar": "abrir", "execute": "abrir", "executa": "abrir",
    "iniciar": "abrir", "inicie": "abrir", "inicia": "abrir",
    "rodar": "abrir", "rode": "abrir", "roda": "abrir",
    "lancar": "abrir", "lanca": "abrir", "lance": "abrir",
    "lançar": "abrir",
    "chamar": "abrir", "chama": "abrir", "chame": "abrir",
    "fechar": "fechar", "fecha": "fechar", "feche": "fechar",
    "encerrar": "encerrar", "encerra": "encerrar", "encerre": "encerrar",
    "sair": "sair", "sai": "sair",
    "alternar": "alternar", "alterna": "alternar", "alterne": "alternar",
    "trocar": "trocar", "troca": "trocar", "troque": "trocar",
    "mudar": "mudar", "muda": "mudar", "mude": "mudar",
    "mostrar": "mostrar", "mostra": "mostrar", "mostre": "mostrar",
    "exibir": "exibir", "exibe": "exibir", "exiba": "exibir",
    "ver": "mostrar",
    "expor": "mostrar", "expoe": "mostrar", "exponha": "mostrar",
    "maximizar": "maximizar", "maximiza": "maximizar", "maximize": "maximizar",
    "ampliar": "ampliar", "amplia": "ampliar", "amplie": "ampliar",
    "restaurar": "restaurar", "restaura": "restaurar", "restaure": "restaurar",
    "minimizar": "minimizar", "minimiza": "minimizar", "minimize": "minimizar",
    "esconder": "minimizar", "esconde": "minimizar", "esconda": "minimizar",
    "encaixar": "encaixar", "encaixa": "encaixar", "encaixe": "encaixar",
    "bloquear": "bloquear", "bloqueia": "bloquear", "bloqueie": "bloquear",
    "travar": "travar", "trava": "travar", "trave": "travar",
    "navegar": "navegar", "navega": "navegar", "navegue": "navegar",
    "ir": "navegar", "vai": "navegar",
    "atualizar": "atualizar", "atualiza": "atualizar", "atualize": "atualizar",
    "recarregar": "atualizar", "recarrega": "atualizar", "recarregue": "atualizar",
    "reabrir": "reabrir", "reabre": "reabrir", "reabra": "reabrir",
    "voltar": "voltar", "volta": "voltar", "volte": "voltar",
    "retornar": "voltar", "retorna": "voltar", "retorne": "voltar",
    "avancar": "avancar", "avanca": "avancar", "avance": "avancar",
    "avançar": "avancar", "avança": "avancar",
    "buscar": "buscar", "busca": "buscar", "busque": "buscar",
    "pesquisar": "buscar", "pesquisa": "buscar", "pesquise": "buscar",
    "localizar": "buscar", "localiza": "buscar", "localize": "buscar",
    "procurar": "buscar", "procura": "buscar", "procure": "buscar",
    "achar": "buscar", "acha": "buscar", "ache": "buscar",
    "encontrar": "buscar", "encontra": "buscar", "encontre": "buscar",
    "salvar": "salvar", "salva": "salvar", "salve": "salvar",
    "imprimir": "imprimir", "imprime": "imprimir", "imprima": "imprimir",
    "aumentar": "aumentar", "aumenta": "aumentar", "aumente": "aumentar",
    "diminuir": "diminuir", "diminui": "diminuir", "diminua": "diminuir",
    "reduzir": "diminuir", "reduz": "diminuir", "reduza": "diminuir",
    "depurar": "depurar", "depura": "depurar", "depure": "depurar",
    "debugar": "depurar", "debuga": "depurar", "debugue": "depurar",
    "inspecionar": "inspecionar", "inspeciona": "inspecionar", "inspecione": "inspecionar",
    "forcar": "forcar", "forca": "forcar", "force": "forcar",
    "forçar": "forcar", "força": "forcar",
}

VERBOS_POR_ACAO: Dict[str, Set[str]] = {
    "abrir_app": VERBOS_ABRIR,
    "abrir_site": VERBOS_ABRIR_SITE,
    "fechar_janela": VERBOS_FECHAR,
    "alternar_janelas": VERBOS_ALTERNAR,
    "mostrar_area_de_trabalho": VERBOS_MOSTRAR,
    "maximizar_janela": VERBOS_MAXIMIZAR,
    "restaurar_ou_minimizar_janela": VERBOS_RESTAURAR,
    "encaixar_janela_esquerda": VERBOS_ENCAIXAR,
    "encaixar_janela_direita": VERBOS_ENCAIXAR,
    "bloquear_tela": VERBOS_BLOQUEAR,
}

# Palavras que não entram no objeto e também podem prefixar um comando
# ("quero abrir", "me mostra"). Não incluir "sabe": "você sabe abrir..."
# deve continuar como conversa, não como comando.
PALAVRAS_DESCARTE: Set[str] = frozenset({
    "","o", "a", "os", "as", "um", "uma", "uns", "umas",
    "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas",
    "para", "pra", "pro", "por", "per", "com", "sem", "sob", "sobre",
    "entre", "apos", "ate", "até", "mim", "me", "te", "se", "si",
    "voce", "você", "voces", "vocês", "vc", "ele", "ela", "eles", "elas", "lhe", "lhes",
    "meu", "meus", "minha", "minhas", "teu", "teus", "tua", "tuas",
    "seu", "seus", "sua", "suas", "nosso", "nossa", "nossos", "nossas",
    "esse", "essa", "esses", "essas", "este", "esta", "estes", "estas",
    "aquele", "aquela", "aqueles", "aquelas",
    "ai", "aí", "la", "lá", "ali", "aqui",
    "favor", "consegue", "conseguir", "pode", "poder", "podia", "poderia",
    "quero", "quer", "querer", "queria", "preciso", "precisa", "precisar",
    "gostaria", "gostar", "seria", "sao", "são", "e", "é", "esta", "está",
    "qual", "quais", "que", "como", "quando", "onde", "hoje", "agora",
    "so", "só", "bem", "dai", "daí",
})
