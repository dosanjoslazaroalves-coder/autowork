"""Módulo de filtragem e saneamento de linguagem para o AUTOWORK.

Responsável por preparar e qualificar o texto recebido do reconhecimento de voz (STT)
antes que ele seja avaliado pelo interpretador de comandos.

Princípios:
    - O filtro não executa comandos nem altera catálogos.
    - Preserva o texto original intacto junto ao texto filtrado.
    - Remove ruídos linguísticos e vícios de fala sem inventar informações.
    - Corrige erros fonéticos conhecidos de Speech-to-Text.
    - Detecta perguntas legítimas e ambiguidades/ruídos desconexos.
    - É 100% determinístico e ultrarrápido (< 1 milissegundo).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class ResultadoFiltro:
    """Estrutura com o resultado do processamento do filtro."""
    texto_original: str
    texto_filtrado: str
    alterado: bool
    confianca: float
    ambiguo: bool
    eh_pergunta: bool

    def to_dict(self) -> Dict[str, Any]:
        """Converte o resultado para dicionário serializável."""
        return {
            "texto_original": self.texto_original,
            "texto_filtrado": self.texto_filtrado,
            "alterado": self.alterado,
            "confianca": self.confianca,
            "ambiguo": self.ambiguo,
            "eh_pergunta": self.eh_pergunta,
        }


# ── Padrões de Wake Word residual no início ───────────────────────
_RE_WAKE_WORD_INICIO = re.compile(
    r"^(?:autowork|auto-work|auto\s*work|work)\b[,:\s]*",
    re.IGNORECASE,
)

# ── Correções fonéticas comuns de transcrição do STT ──────────────
_CORRECOES_STT: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bbloqui(?:m)?\s+de\s+notas?\b", re.IGNORECASE), "bloco de notas"),
    (re.compile(r"\bcrome\b", re.IGNORECASE), "chrome"),
    (re.compile(r"\b(?:gutube|iutube|youtub)\b", re.IGNORECASE), "youtube"),
    (re.compile(r"\bcalculador\b", re.IGNORECASE), "calculadora"),
    (re.compile(r"\bnav\b", re.IGNORECASE), "navegador"),
    (re.compile(r"\bminimiza\s+as\s+tela\b", re.IGNORECASE), "minimizar as telas"),
    (re.compile(r"\bminimiza\s+a\s+tela\b", re.IGNORECASE), "minimizar a tela"),
    (re.compile(r"\bminimiza\s+as\s+janela\b", re.IGNORECASE), "minimizar as janelas"),
    (re.compile(r"\besconde\s+as\s+tela\b", re.IGNORECASE), "esconder as telas"),
    (re.compile(r"\besconde\s+as\s+janela\b", re.IGNORECASE), "esconder as janelas"),
    (re.compile(r"\bvisual\s+(?:esteve|studio)\s+code\b", re.IGNORECASE), "visual studio code"),
    (re.compile(r"\bvisual\s+esteve\b", re.IGNORECASE), "visual studio code"),
    (re.compile(r"\barea\s+de\s+trabalho\b", re.IGNORECASE), "área de trabalho"),
    (re.compile(r"\bdev\s*tools?\b", re.IGNORECASE), "devtools"),
    (re.compile(r"\binpetor\b", re.IGNORECASE), "inspetor"),
    (re.compile(r"\bferamentas?\s+d[oe]\s+desenvolvedor\b", re.IGNORECASE), "ferramentas do desenvolvedor"),
]

# ── Detecção de Perguntas Legítimas ────────────────────────────────
_RE_INTERROGATIVOS_INICIO = re.compile(
    r"^(?:como|por\s*que|porque|qual|quem|quando|onde|quanto|ser[aá]\s+que)\b",
    re.IGNORECASE,
)

_RE_PERGUNTA_CAPACIDADE = re.compile(
    r"\b(?:voc[eê]|vc)\s+(?:sabe|consegue|pode|saberia|poderia)\b"
    r"|\b(?:como\s+(?:eu\s+)?abro|como\s+(?:eu\s+)?fa[cç]o|o\s+que\s+significa|o\s+que\s+[ée]|quem\s+[ée])\b",
    re.IGNORECASE,
)

# ── Preenchimentos e Vícios de Fala no Início (Fillers) ────────────
_RE_FILLERS_INICIO = [
    re.compile(r"^(?:eu\s+)?preciso\s+que\s+voc[eê]\s+", re.IGNORECASE),
    re.compile(r"^preciso\s+que\s+vc\s+", re.IGNORECASE),
    re.compile(r"^(?:eu\s+)?preciso\s+que\s+voc[eê]\s+", re.IGNORECASE),
    re.compile(r"^preciso\s+que\s+vc\s+", re.IGNORECASE),
    re.compile(r"^(?:eu\s+)?(?:gostaria\s+que\s+voc[eê]\s+|queria\s+que\s+voc[eê]\s+|quero\s+que\s+voc[eê]\s+|quero\s+que\s+vc\s+)", re.IGNORECASE),
    re.compile(r"^(?:d[aá]\s+pra\s+voc[eê]\s+|d[aá]\s+pra\s+vc\s+|d[aá]\s+pra\s+)", re.IGNORECASE),
    re.compile(r"^(?:tem\s+como\s+voc[eê]\s+|tem\s+como\s+)", re.IGNORECASE),
    re.compile(r"^(?:faz\s+favor\s+de\s+|faz\s+favor\s+)", re.IGNORECASE),
    re.compile(r"^(?:por\s+favor\s+|favor\s+|por\s+gentileza\s+)", re.IGNORECASE),
]

# ── Ruídos e Marcadores Descartáveis no Fim ou Intermediários ───────
_RE_RUÍDOS_DESCARTE = [
    re.compile(r"\b(?:a[ií]|aqui|tipo\s+assim|tipo|ent[aã]o)\s*$", re.IGNORECASE),
    re.compile(r"\b(?:pra\s+mim)\s*$", re.IGNORECASE),
    re.compile(r"\b(?:a[ií]|aqui)\s+(?=(?:o|a|os|as|um|uma|esse|essa|aquele|aquela|o\s+meu|a\s+minha)\b)", re.IGNORECASE),
]

# ── Ambiguidade e Ruído Desconexo de STT ───────────────────────────
# Palavras desconexas conhecidas ou sequências gramaticalmente caóticas
_RE_INCOERENCIA_STT = re.compile(
    r"\b(?:cira\s+t[aá]|t[aá]\s+coisa|n[aã]o\s+conseguir\s+cria|coisa\s+mais\s+n[aã]o|esse\s+work\s+abrir)\b"
    r"|\b(?:bla\s+bla|xpto|asdf|qwerty)\b",
    re.IGNORECASE,
)


def _detectar_pergunta(texto: str) -> bool:
    """Verifica se a frase possui natureza interrogativa genuína."""
    texto_limpo = texto.strip()
    if texto_limpo.endswith("?"):
        return True
    if _RE_INTERROGATIVOS_INICIO.search(texto_limpo):
        return True
    if _RE_PERGUNTA_CAPACIDADE.search(texto_limpo):
        return True
    return False


def _detectar_ambiguidade(texto: str, eh_pergunta: bool) -> Tuple[bool, float]:
    """Avalia se o texto é ambíguo, incompleto ou desconexo.

    Retorna:
        (ambiguo: bool, confianca: float)
    """
    texto_limpo = texto.strip()
    if not texto_limpo:
        return True, 0.0

    tokens = texto_limpo.split()

    # 1. Padrões claros de ruído incoerente ou transcrição corrompida
    if _RE_INCOERENCIA_STT.search(texto_limpo):
        return True, 0.20

    # 2. Comando vago / incompleto de 1 palavra que requer alvo
    verbos_incompletos = {"abre", "abrir", "abra", "inicia", "iniciar", "inicie", "fecha", "fechar", "feche", "executa", "execute"}
    if len(tokens) == 1 and tokens[0].lower() in verbos_incompletos:
        return True, 0.40

    # 3. Frase com pronomes genéricos sem especificar o alvo ("abre aquele programa aí", "abre aquele")
    if re.search(r"\b(?:aquele\s+programa|aquela\s+coisa|aquele\s+app)\b", texto_limpo, re.IGNORECASE):
        # Se for vago demais e não citar navegador ou algo do catálogo
        if not re.search(r"\b(?:navegador|browser|chrome|pasta|janela|site)\b", texto_limpo, re.IGNORECASE):
            return True, 0.35

    return False, 0.95


def _remover_fillers(texto: str, eh_pergunta: bool) -> str:
    """Remove palavras de preenchimento e vícios de fala."""
    resultado = texto.strip()

    # Se for uma pergunta ("pode abrir o navegador?"), não remove "pode", pois muda o sentido
    if not eh_pergunta:
        # Remove "pode" coloquial inicial se seguido de verbo no infinitivo: "pode fechar o chrome" -> "fechar o chrome"
        resultado = re.sub(
            r"^(?:eu\s+)?(?:pode|queria|quero|preciso|consegue)\s+(?=[a-zà-ú]+(?:r|ir|ar|er)\b)",
            "",
            resultado,
            flags=re.IGNORECASE,
        ).strip()

        # Remove "eu quero que você", "dá pra você", "por favor", etc.
        for padrao in _RE_FILLERS_INICIO:
            resultado = padrao.sub("", resultado).strip()

    # Remove ruídos no final ou intermediários ("aí", "pra mim")
    for padrao in _RE_RUÍDOS_DESCARTE:
        resultado = padrao.sub("", resultado).strip()

    return resultado


def _aplicar_correcoes_stt(texto: str) -> str:
    """Aplica substituições conservadoras para deslizes fonéticos de STT."""
    resultado = texto
    for padrao, substituto in _CORRECOES_STT:
        resultado = padrao.sub(substituto, resultado)
    return resultado


def _normalizar_espacos_e_pontuacao(texto: str) -> str:
    """Remove pontuações desnecessárias preservando interrogação quando presente."""
    # Preserva o '?' se existir
    tem_interrogacao = "?" in texto
    limpo = re.sub(r"[!.,;:]+", "", texto)
    limpo = " ".join(limpo.split())
    if tem_interrogacao and not limpo.endswith("?"):
        limpo += "?"
    return limpo


def filtrar(texto: str) -> ResultadoFiltro:
    """Filtra, higieniza e qualifica o texto recebido da voz/STT.

    Parâmetros:
        texto: Frase original recebida (geralmente após detecção de wake word).

    Retorna:
        ResultadoFiltro contendo texto_original, texto_filtrado, alterado,
        confianca, ambiguo e eh_pergunta.
    """
    if not texto or not texto.strip():
        return ResultadoFiltro(
            texto_original=texto or "",
            texto_filtrado="",
            alterado=False,
            confianca=0.0,
            ambiguo=True,
            eh_pergunta=False,
        )

    texto_original = texto.strip()

    # 1. Remover Wake Word se ainda estiver presente na cabeça da string
    texto_sem_wake = _RE_WAKE_WORD_INICIO.sub("", texto_original).strip()

    # 2. Identificar se é pergunta antes de qualquer alteração que remova contexto
    eh_pergunta = _detectar_pergunta(texto_sem_wake)

    # 3. Detectar ruído severo e incoerência bruta de STT logo de início
    if _RE_INCOERENCIA_STT.search(texto_sem_wake):
        return ResultadoFiltro(
            texto_original=texto_original,
            texto_filtrado=texto_sem_wake,
            alterado=(texto_sem_wake != texto_original),
            confianca=0.20,
            ambiguo=True,
            eh_pergunta=eh_pergunta,
        )

    # 4. Aplicar correções fonéticas conservadoras de STT
    texto_corrigido = _aplicar_correcoes_stt(texto_sem_wake)

    # 5. Remover ruídos de preenchimento e vícios de fala
    texto_sem_fillers = _remover_fillers(texto_corrigido, eh_pergunta)

    # 6. Normalizar espaços e pontuação final
    texto_final = _normalizar_espacos_e_pontuacao(texto_sem_fillers)

    # 7. Avaliar ambiguidade e confiança sobre o texto limpo
    ambiguo, confianca = _detectar_ambiguidade(texto_final, eh_pergunta)

    alterado = (texto_final.lower() != texto_original.lower())

    return ResultadoFiltro(
        texto_original=texto_original,
        texto_filtrado=texto_final,
        alterado=alterado,
        confianca=confianca,
        ambiguo=ambiguo,
        eh_pergunta=eh_pergunta,
    )
