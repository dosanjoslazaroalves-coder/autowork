from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
import uuid
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional

try:
    import requests
except ImportError:  # pragma: no cover - dependência opcional em ambientes mínimos
    requests = None

from conversa.ollama import OLLAMA_AUX_TIMEOUT, OLLAMA_MODEL, OLLAMA_NUM_PREDICT, OLLAMA_URL


logger = logging.getLogger(__name__)


STATUS_WORKFLOW_PLANEJADO = "planejado"
STATUS_ETAPA_PENDENTE = "pendente"
OLLAMA_MODELO = OLLAMA_MODEL
OLLAMA_TIMEOUT = OLLAMA_AUX_TIMEOUT

VERBOS_ABRIR = {
    "abra",
    "abre",
    "abrir",
    "inicie",
    "iniciar",
    "execute",
    "executar",
    "rode",
    "rodar",
}

VERBOS_FECHAR = {"feche", "fechar", "fecha", "encerre", "encerrar"}
VERBOS_MINIMIZAR = {"minimize", "minimizar", "minimiza"}

APLICATIVOS: Dict[str, str] = {
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "navegador": "Google Chrome",
    "browser": "Google Chrome",
    "edge": "Microsoft Edge",
    "microsoft edge": "Microsoft Edge",
    "firefox": "Firefox",
    "bloco de notas": "Bloco de notas",
    "bloco notas": "Bloco de notas",
    "notepad": "Bloco de notas",
    "calculadora": "Calculadora",
    "cmd": "Prompt de Comando",
    "prompt": "Prompt de Comando",
    "terminal": "Windows Terminal",
    "powershell": "PowerShell",
    "explorador": "Explorador de Arquivos",
    "explorador de arquivos": "Explorador de Arquivos",
    "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "visual studio code": "Visual Studio Code",
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "outlook": "Microsoft Outlook",
    "spotify": "Spotify",
    "discord": "Discord",
    "whatsapp": "WhatsApp",
}

SITES: Dict[str, str] = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "you tube": "https://www.youtube.com",
    "yt": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "chatgpt": "https://chatgpt.com",
    "chat gpt": "https://chatgpt.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "x": "https://x.com",
    "twitter": "https://x.com",
    "linkedin": "https://www.linkedin.com",
    "netflix": "https://www.netflix.com",
    "spotify web": "https://open.spotify.com",
    "notion": "https://www.notion.so",
}

ATALHOS_SEM_PARAMETROS = {
    "abrir nova aba": "nova_aba",
    "abrir nova guia": "nova_aba",
    "nova aba": "nova_aba",
    "nova guia": "nova_aba",
    "fechar aba": "fechar_aba",
    "feche a aba": "fechar_aba",
    "fechar janela": "fechar_janela",
    "feche a janela": "fechar_janela",
    "mostrar area de trabalho": "mostrar_area_de_trabalho",
    "mostrar a area de trabalho": "mostrar_area_de_trabalho",
    "minimizar todas as janelas": "mostrar_area_de_trabalho",
    "minimize todas as janelas": "mostrar_area_de_trabalho",
    "minimizar tudo": "mostrar_area_de_trabalho",
    "minimize tudo": "mostrar_area_de_trabalho",
    "por ultimo minimize todas as janelas": "mostrar_area_de_trabalho",
}

PADRAO_CONECTORES = re.compile(
    r"\b(?:(?:e\s+)?(?:depois|em\s+seguida|ent[aã]o|ap[oó]s\s+isso|por\s+"
    r"[uú]ltimo|finalmente)|primeiro|segundo|terceiro|quarto|quinto)\b",
    flags=re.IGNORECASE,
)

PADRAO_VERBO_COMANDO = re.compile(
    r"\b(?:abra|abre|abrir|inicie|iniciar|execute|executar|rode|rodar|"
    r"feche|fechar|fecha|minimize|minimizar|minimiza|mostre|mostrar)\b",
    flags=re.IGNORECASE,
)


def detectar_comando_complexo(texto: str) -> bool:
    """Detecta uma sequência, inclusive quando ela precisa do Ollama.

    A detecção continua local e barata. A requisição ao Ollama só acontece
    depois, em ``interpretar_comando_complexo``, quando o parser determinístico
    encontra uma etapa ambígua ou desconhecida.
    """
    if not isinstance(texto, str) or not texto.strip():
        return False

    etapas = _interpretar_etapas(texto)
    if len(etapas) < 2:
        return False

    reconhecidas = [e for e in etapas if e["acao"] != "acao_desconhecida"]
    if len(reconhecidas) >= 2:
        return True

    return bool(
        reconhecidas
        and (PADRAO_CONECTORES.search(texto) or len(etapas) >= 2)
        and PADRAO_VERBO_COMANDO.search(texto)
    )


def interpretar_comando_complexo(texto: str) -> Dict[str, Any]:
    etapas = _interpretar_etapas(texto)
    etapas_ia = _interpretar_com_ollama_se_necessario(texto, etapas)
    if etapas_ia:
        etapas = etapas_ia
    workflow_id = f"workflow-{uuid.uuid4().hex[:12]}"
    return {
        "tipo": "comando_complexo",
        "id": workflow_id,
        "status": STATUS_WORKFLOW_PLANEJADO,
        "descricao": texto.strip(),
        "comando_original": texto,
        "criado_em": datetime.now().isoformat(timespec="seconds"),
        "confianca": _confianca_workflow(etapas),
        "etapas": etapas,
        "fala": "",
        "falar": False,
    }


def _interpretar_etapas(texto: str) -> List[Dict[str, Any]]:
    partes = _separar_partes(texto)
    etapas: List[Dict[str, Any]] = []

    for parte in partes:
        interpretada = _interpretar_parte(parte)
        etapa_id = len(etapas) + 1
        etapas.append(
            {
                "id": etapa_id,
                "acao": interpretada["acao"],
                "parametros": interpretada["parametros"],
                # Ordem de execução não implica dependência lógica. Uma
                # dependência só é adicionada quando o plano realmente exige
                # o resultado de uma etapa anterior.
                "dependencias": [],
                "obrigatoria": True,
                "status": STATUS_ETAPA_PENDENTE,
                "confianca": interpretada["confianca"],
                "descricao": parte.strip(),
                "max_tentativas": 1,
                "timeout": None,
                "idempotente": interpretada["idempotente"],
                "erro": interpretada.get("erro"),
            }
        )

    return etapas


def _separar_partes(texto: str) -> List[str]:
    limpo = _limpar_wake_word(texto)
    limpo = re.sub(r"\s+", " ", limpo).strip(" ,.;")

    # Preserve a repeated implicit target list before converting commas into
    # generic separators. Example: "abra o Chrome, o VS Code e o Notepad".
    lista = re.match(
        r"^(?P<verbo>" + "|".join(sorted(VERBOS_ABRIR, key=len, reverse=True))
        + r")\s+(?P<alvos>.+)$",
        limpo,
        flags=re.IGNORECASE,
    )
    if (
        lista
        and "," in lista.group("alvos")
        and not PADRAO_CONECTORES.search(lista.group("alvos"))
        and not PADRAO_VERBO_COMANDO.search(lista.group("alvos"))
    ):
        alvos = re.split(r"\s*,\s*|\s+e\s+", lista.group("alvos"), flags=re.IGNORECASE)
        if len(alvos) >= 2 and all(alvo.strip() for alvo in alvos):
            return [f"{lista.group('verbo')} {alvo.strip()}" for alvo in alvos]

    limpo = re.sub(r"\s*,\s*", " | ", limpo)
    limpo = PADRAO_CONECTORES.sub(" | ", limpo)
    limpo = re.sub(
        r"\s+e\s+(?=(?:abra|abre|abrir|inicie|iniciar|execute|executar|rode|rodar|"
        r"feche|fechar|fecha|minimize|minimizar|minimiza|mostre|mostrar)\b)",
        " | ",
        limpo,
        flags=re.IGNORECASE,
    )

    # Para uma lista nominal sem vírgula preservada (o filtro pode removê-la),
    # expanda o verbo inicial somente quando houver uma conjunção entre alvos.
    if "|" not in limpo:
        lista = re.match(
            r"^(?P<verbo>" + "|".join(sorted(VERBOS_ABRIR, key=len, reverse=True))
            + r")\s+(?P<alvos>.+)$",
            limpo,
            flags=re.IGNORECASE,
        )
        if lista and re.search(r"\s+e\s+", lista.group("alvos"), re.IGNORECASE):
            alvos = re.split(r"\s+e\s+", lista.group("alvos"), flags=re.IGNORECASE)
            if len(alvos) >= 2 and all(alvo.strip() for alvo in alvos):
                return [f"{lista.group('verbo')} {alvo.strip()}" for alvo in alvos]

    partes = [p.strip(" ,.;") for p in limpo.split("|") if p.strip(" ,.;")]
    # Linguagem natural costuma omitir o verbo nas etapas seguintes:
    # "abra Chrome, depois Spotify e depois VS Code". Reaproveite o verbo
    # somente para a lista de abertura; não transforme texto livre em ação.
    if len(partes) >= 2:
        primeiro_tokens = partes[0].split(maxsplit=1)
        if primeiro_tokens and primeiro_tokens[0] in VERBOS_ABRIR:
            verbo = primeiro_tokens[0]
            partes = [partes[0]] + [
                parte if PADRAO_VERBO_COMANDO.search(parte) else f"{verbo} {parte}"
                for parte in partes[1:]
            ]
    return partes


def _interpretar_parte(parte: str) -> Dict[str, Any]:
    texto = _normalizar(parte)
    texto = _remover_prefixos_ordinais(texto)

    for frase, acao in sorted(ATALHOS_SEM_PARAMETROS.items(), key=lambda item: len(item[0]), reverse=True):
        if frase in texto:
            return {
                "acao": acao,
                "parametros": {},
                "confianca": 0.96,
                "idempotente": acao in {"mostrar_area_de_trabalho"},
            }

    tokens = texto.split()
    if not tokens:
        return _desconhecida(parte, "etapa_vazia")

    verbo = tokens[0]
    resto = " ".join(tokens[1:]).strip()

    if verbo in VERBOS_ABRIR:
        alvo = _limpar_alvo_abertura(resto)
        if not alvo:
            return {
                "acao": "abrir",
                "parametros": {},
                "confianca": 0.4,
                "idempotente": True,
                "erro": "parametro_ausente:alvo",
            }
        return _classificar_abertura(alvo)

    if verbo in VERBOS_FECHAR:
        if "aba" in texto:
            return {"acao": "fechar_aba", "parametros": {}, "confianca": 0.92, "idempotente": False}
        if "janela" in texto:
            return {"acao": "fechar_janela", "parametros": {}, "confianca": 0.92, "idempotente": False}
        return _desconhecida(parte, "alvo_de_fechamento_desconhecido")

    if verbo in VERBOS_MINIMIZAR and re.search(r"\b(tudo|janelas?|todas)\b", texto):
        return {
            "acao": "mostrar_area_de_trabalho",
            "parametros": {},
            "confianca": 0.95,
            "idempotente": True,
        }

    if texto.startswith("mostre") or texto.startswith("mostrar"):
        if "area de trabalho" in texto:
            return {
                "acao": "mostrar_area_de_trabalho",
                "parametros": {},
                "confianca": 0.95,
                "idempotente": True,
            }

    return _desconhecida(parte, "acao_desconhecida")


def _classificar_abertura(alvo: str) -> Dict[str, Any]:
    alvo_norm = _normalizar(alvo)
    alvo_site = _remover_prefixo_site(alvo_norm)

    # O catálogo central é a autoridade para aplicativos; este módulo não
    # mantém uma segunda lista de executáveis válidos.
    from sistema_toke.catalogo.catalogo_app import resolver_nome_app
    from sistema_toke.catalogo.catalogo_site import CATALOGO_SITES

    app_catalogado = resolver_nome_app(alvo_norm) or resolver_nome_app(alvo_site)
    if app_catalogado:
        return {
            "acao": "abrir_aplicativo",
            "parametros": {"aplicativo": app_catalogado, "nome": app_catalogado},
            "confianca": 0.97,
            "idempotente": True,
        }

    for chave, site_info in CATALOGO_SITES.items():
        nomes = {chave.lower(), site_info.nome.lower(), *(s.lower() for s in site_info.sinonimos)}
        if alvo_site in nomes or alvo_norm in nomes:
            return {
                "acao": "abrir_site",
                "parametros": {"site": chave, "url": site_info.url},
                "confianca": 0.97,
                "idempotente": True,
            }

    if alvo_norm in APLICATIVOS:
        app = APLICATIVOS[alvo_norm]
        return {
            "acao": "abrir_aplicativo",
            "parametros": {"aplicativo": app, "nome": app},
            "confianca": 0.97,
            "idempotente": True,
        }

    if alvo_site in SITES:
        url = SITES[alvo_site]
        return {
            "acao": "abrir_site",
            "parametros": {"site": alvo_site, "url": url},
            "confianca": 0.97,
            "idempotente": True,
        }

    if _parece_url(alvo_norm):
        url = alvo_norm if alvo_norm.startswith(("http://", "https://")) else f"https://{alvo_norm}"
        return {
            "acao": "abrir_site",
            "parametros": {"site": alvo_norm, "url": url},
            "confianca": 0.84,
            "idempotente": True,
        }

    if re.search(r"\b(site|pagina|web)\b", alvo_norm):
        site = _remover_prefixo_site(alvo_norm)
        if not site:
            return {
                "acao": "abrir_site",
                "parametros": {},
                "confianca": 0.45,
                "idempotente": True,
                "erro": "parametro_ausente:site",
            }
        return {
            "acao": "abrir_site",
            "parametros": {"site": site, "url": f"https://{site}"},
            "confianca": 0.68,
            "idempotente": True,
        }

    return {
        "acao": "abrir_aplicativo",
        "parametros": {"aplicativo": alvo, "nome": alvo},
        "confianca": 0.62,
        "idempotente": True,
    }


def _limpar_wake_word(texto: str) -> str:
    return re.sub(r"^\s*(autowork|auto work|alto work)[, ]+", "", texto.strip(), flags=re.IGNORECASE)


def _normalizar(texto: str) -> str:
    texto = texto.strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    texto = re.sub(r"[?!;:]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip(" .,")


def _remover_prefixos_ordinais(texto: str) -> str:
    return re.sub(
        r"^(?:por favor|favor|primeiro|segundo|terceiro|quarto|quinto|por ultimo|finalmente)\s+",
        "",
        texto,
    ).strip()


def _limpar_alvo_abertura(resto: str) -> str:
    alvo = re.sub(r"^(?:o|a|os|as|um|uma)\s+", "", resto.strip())
    alvo = re.sub(r"^(?:aplicativo|app|programa)\s+(?:d[eo]\s+|da\s+|do\s+)?", "", alvo)
    return alvo.strip()


def _remover_prefixo_site(alvo: str) -> str:
    return re.sub(
        r"^(?:o\s+|a\s+)?(?:site|pagina|web)\s+(?:d[eo]\s+|da\s+|do\s+)?",
        "",
        alvo,
    ).strip()


def _parece_url(alvo: str) -> bool:
    return bool(
        alvo.startswith(("http://", "https://", "www."))
        or re.search(r"\.(?:com|com\.br|org|net|io|dev|app|tv|ai|me)\b", alvo)
    )


def _desconhecida(parte: str, erro: str) -> Dict[str, Any]:
    return {
        "acao": "acao_desconhecida",
        "parametros": {"texto": parte.strip()},
        "confianca": 0.0,
        "idempotente": False,
        "erro": erro,
    }


def _confianca_workflow(etapas: List[Dict[str, Any]]) -> float:
    if not etapas:
        return 0.0
    return round(sum(float(e.get("confianca", 0.0)) for e in etapas) / len(etapas), 2)


def _interpretar_com_ollama_se_necessario(
    texto: str, etapas_deterministicas: List[Dict[str, Any]]
) -> Optional[List[Dict[str, Any]]]:
    """Usa o Ollama apenas quando a interpretação local não é suficiente.

    O comportamento determinístico continua sendo a primeira opção. A IA não
    executa nada: ela propõe uma sequência que é validada contra os catálogos
    locais antes de ser aceita. Se o Ollama estiver indisponível ou responder
    algo inválido, o parser local permanece como fallback.
    """
    politica = os.getenv("AUTOWORK_COMPLEX_USE_OLLAMA", "auto").strip().lower()
    if politica == "never":
        return None
    precisa_ia = any(
        etapa.get("acao") == "acao_desconhecida" or etapa.get("erro")
        for etapa in etapas_deterministicas
    )
    if politica != "always" and not precisa_ia:
        return None
    return _interpretar_sequencia_com_ollama(texto)


def _interpretar_sequencia_com_ollama(texto: str) -> Optional[List[Dict[str, Any]]]:
    if requests is None:
        logger.debug("Comandos complexos: requests não está instalado.")
        return None

    prompt = _prompt_sequencia(texto)
    try:
        resposta = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODELO,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "think": False,
                "options": {"num_predict": OLLAMA_NUM_PREDICT},
            },
            timeout=OLLAMA_TIMEOUT,
        )
        resposta.raise_for_status()
        corpo = resposta.json()
        bruto = corpo.get("response", corpo) if isinstance(corpo, Mapping) else corpo
        dados = bruto if isinstance(bruto, Mapping) else _extrair_json(str(bruto))
        return _validar_sequencia_ia(dados)
    except (requests.exceptions.RequestException, ValueError, TypeError, json.JSONDecodeError):
        logger.debug("Comandos complexos: Ollama indisponível ou resposta inválida.", exc_info=True)
        return None
    except Exception:
        logger.debug("Comandos complexos: falha inesperada no Ollama.", exc_info=True)
        return None


def _prompt_sequencia(texto: str) -> str:
    from sistema_toke.catalogo.catalogo_atalho import CATALOGO_ATALHOS

    acoes = ["abrir_aplicativo", "abrir_site"] + sorted(CATALOGO_ATALHOS)
    lista_acoes = ", ".join(acoes)
    return f"""Você interpreta sequências de comandos do AUTOWORK.
Retorne SOMENTE JSON válido no formato:
{{"etapas": [{{"acao": "...", "parametros": {{}}, "dependencias": []}}]}}

Regras obrigatórias:
- Preserve exatamente a ordem em que as ações aparecem.
- Use somente estas ações: {lista_acoes}.
- Para abrir aplicativo use acao=abrir_aplicativo e informe nome ou aplicativo.
- Para abrir site use acao=abrir_site e informe site ou url.
- Não invente aplicativos, sites ou ações. Se não conseguir identificar uma
  etapa, não a inclua e retorne um plano inválido para que o sistema local use
  o fallback.
- Dependencias deve conter somente etapas anteriores cujo resultado seja
  realmente necessário; ordem sozinha não é dependência.

Comando do usuário: {texto}
"""


def _extrair_json(texto: str) -> Optional[Dict[str, Any]]:
    texto = texto.strip()
    try:
        dados = json.loads(texto)
        return dados if isinstance(dados, dict) else None
    except json.JSONDecodeError:
        inicio, fim = texto.find("{"), texto.rfind("}")
        if inicio < 0 or fim <= inicio:
            return None
        try:
            dados = json.loads(texto[inicio : fim + 1])
        except json.JSONDecodeError:
            return None
        return dados if isinstance(dados, dict) else None


def _validar_sequencia_ia(dados: Optional[Mapping[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    if not isinstance(dados, Mapping) or not isinstance(dados.get("etapas"), list):
        return None
    itens = dados["etapas"]
    if len(itens) < 2:
        return None

    from sistema_toke.catalogo.catalogo_atalho import CATALOGO_ATALHOS

    acoes_validas = {"abrir_aplicativo", "abrir_app", "abrir_site", *CATALOGO_ATALHOS}
    etapas: List[Dict[str, Any]] = []
    for indice, item in enumerate(itens, start=1):
        if not isinstance(item, Mapping):
            return None
        acao = str(item.get("acao") or "").strip().lower()
        if acao not in acoes_validas:
            return None
        parametros = item.get("parametros")
        if not isinstance(parametros, Mapping):
            parametros = {}
        parametros = dict(parametros)

        if acao in {"abrir_aplicativo", "abrir_app", "abrir_site"}:
            alvo = parametros.get("nome") or parametros.get("aplicativo") or parametros.get("alvo")
            if acao == "abrir_site":
                alvo = parametros.get("url") or parametros.get("site") or alvo
            if not isinstance(alvo, str) or not alvo.strip():
                return None
            if acao in {"abrir_aplicativo", "abrir_app"}:
                from sistema_toke.catalogo.catalogo_app import resolver_nome_app

                if resolver_nome_app(alvo.strip()) is None:
                    return None
            classificado = _classificar_abertura(alvo.strip())
            if acao in {"abrir_aplicativo", "abrir_app"} and classificado["acao"] != "abrir_aplicativo":
                return None
            if acao == "abrir_site" and classificado["acao"] != "abrir_site":
                return None
            acao = classificado["acao"]
            parametros = classificado["parametros"]

        dependencias = item.get("dependencias", [])
        if dependencias is None:
            dependencias = []
        if not isinstance(dependencias, list) or any(
            type(dep) is not int or dep < 1 or dep >= indice for dep in dependencias
        ):
            return None

        etapas.append(
            {
                "id": indice,
                "acao": acao,
                "parametros": parametros,
                "dependencias": list(dict.fromkeys(dependencias)),
                "obrigatoria": bool(item.get("obrigatoria", True)),
                "status": STATUS_ETAPA_PENDENTE,
                "confianca": 0.8,
                "descricao": str(item.get("descricao") or acao),
                "max_tentativas": 1,
                "timeout": None,
                "idempotente": acao in {"abrir_aplicativo", "abrir_site", "mostrar_area_de_trabalho"},
                "erro": None,
            }
        )
    return etapas
