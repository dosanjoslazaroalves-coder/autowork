from __future__ import annotations

import re
from typing import Callable, Dict, Tuple


_EXATAS: Dict[str, str] = {
    "sistema iniciado": "Inicialização concluída. Todos os sistemas estão operacionais.",
    "abrindo navegador": "Comando confirmado. Inicializando navegador.",
    "erro": "Não foi possível concluir a operação solicitada.",
}

_PadraoBuilder = Tuple[re.Pattern[str], Callable[[re.Match[str]], str]]
_PADROES: Tuple[_PadraoBuilder, ...] = (
    (
        re.compile(r"^abrindo\s+(.+)$", re.I),
        lambda m: f"Comando confirmado. Inicializando {m.group(1).strip()}.",
    ),
    (
        re.compile(r"^(.+)\s+aberto com sucesso\.?$", re.I),
        lambda m: f"Operação concluída. {m.group(1).strip()} está disponível.",
    ),
    (
        re.compile(r"^não conheço essa ação.*$", re.I),
        lambda _: "Ação não reconhecida nos módulos atuais.",
    ),
)


def estilizar_fala(texto: str) -> str:
    """Ajusta frases curtas para tom premium. Não reescreve prosa longa da IA."""
    limpo = " ".join((texto or "").strip().split())
    if not limpo:
        return limpo

    chave = limpo.lower().rstrip(".")
    if chave in _EXATAS:
        return _EXATAS[chave]

    if len(limpo.split()) > 12:
        return limpo

    for padrao, builder in _PADROES:
        match = padrao.match(limpo)
        if match:
            return builder(match)

    return limpo
