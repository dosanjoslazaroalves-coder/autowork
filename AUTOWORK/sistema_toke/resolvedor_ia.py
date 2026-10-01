"""Resolvedor IA — fallback de interpretação via Ollama local.

Este módulo NÃO executa ações. Ele recebe uma frase em linguagem natural,
consulta o Ollama local e retorna uma intenção estruturada validada contra
o catálogo oficial do AUTOWORK, ou None em caso de falha.

Princípios:
    - A IA interpreta. O AUTOWORK decide. O executor executa.
    - Somente intenções existentes no catálogo oficial são aceitas.
    - Qualquer falha (Ollama desligado, timeout, JSON inválido, intenção
      inexistente) resulta em None — o AUTOWORK segue pelo fluxo normal.
    - Sem memória conversacional. Cada chamada é independente.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from conversa.ollama import OLLAMA_AUX_TIMEOUT, OLLAMA_MODEL, OLLAMA_NUM_PREDICT, OLLAMA_URL

logger = logging.getLogger(__name__)

# ── Configuração padrão (compatível com apresent.py) ─────────────
OLLAMA_MODELO = OLLAMA_MODEL
OLLAMA_TIMEOUT = OLLAMA_AUX_TIMEOUT


# ══════════════════════════════════════════════════════════════════
# Construção dinâmica do prompt a partir dos catálogos reais
# ══════════════════════════════════════════════════════════════════

def _listar_intencoes_atalho() -> List[str]:
    """Retorna os nomes reais das ações do CATALOGO_ATALHOS."""
    from sistema_toke.catalogo.catalogo_atalho import CATALOGO_ATALHOS
    return sorted(CATALOGO_ATALHOS.keys())


def _exemplos_apps(limite: int = 20) -> str:
    """Retorna aliases representativos do MAPA_APPS para o prompt."""
    from sistema_toke.catalogo.catalogo_app import MAPA_APPS
    nomes = sorted(set(MAPA_APPS.values()))[:limite]
    return ", ".join(nomes)


def _exemplos_sites(limite: int = 15) -> str:
    """Retorna nomes representativos do CATALOGO_SITES para o prompt."""
    from sistema_toke.catalogo.catalogo_site import CATALOGO_SITES
    return ", ".join(sorted(CATALOGO_SITES.keys())[:limite])


def _construir_prompt(texto: str) -> str:
    """Monta o system prompt completo com catálogo dinâmico."""
    atalhos = _listar_intencoes_atalho()
    lista_atalhos = "\n".join(f"  - {a}" for a in atalhos)
    apps = _exemplos_apps()
    sites = _exemplos_sites()

    return f"""Você é um classificador de intenções do assistente AUTOWORK.

TAREFA: Analise a frase do usuário e retorne SOMENTE um JSON com a intenção correspondente.

REGRAS ABSOLUTAS:
1. Retorne APENAS JSON válido. Nenhum texto antes ou depois.
2. Use SOMENTE as intenções listadas abaixo. NUNCA invente novas.
3. Frases de cortesia e perguntas operacionais ("poderia abrir...", "você consegue abrir...") continuam sendo comandos; só rejeite perguntas de explicação/conversa.
4. Frases como "minimiza tudo", "esconde as janelas", "quero ver a área de trabalho", "mostra o desktop" significam mostrar_area_de_trabalho.
5. Frases como "minimiza essa janela", "diminui a janela" significam restaurar_ou_minimizar_janela.
6. Frases como "troca de janela", "muda a janela", "vai pra outra janela" significam alternar_janelas.
7. Frases como "fecha isso", "fecha a janela", "fecha essa tela" significam fechar_janela.

INTENÇÕES DE ATALHO DISPONÍVEIS:
{lista_atalhos}

INTENÇÕES ESPECIAIS:
  - abrir_app (abrir um aplicativo — requer campo "alvo")
  - abrir_site (abrir um site — requer campo "alvo")

APLICATIVOS VÁLIDOS (exemplos): {apps}
SITES VÁLIDOS (exemplos): {sites}

FORMATO DE RESPOSTA:

Para atalhos:
{{"intencao": "nome_exato_da_intencao"}}

Para aplicativo:
{{"intencao": "abrir_app", "alvo": "alias do aplicativo", "confianca": 0.0}}

Para site:
{{"intencao": "abrir_site", "alvo": "nome do site", "confianca": 0.0}}

Se não for comando:
{{"intencao": "DESCONHECIDO"}}

EXEMPLOS:
"minimize tudo" → {{"intencao": "mostrar_area_de_trabalho"}}
"esconde as janelas" → {{"intencao": "mostrar_area_de_trabalho"}}
"quero ver a área de trabalho" → {{"intencao": "mostrar_area_de_trabalho"}}
"abre o navegador" → {{"intencao": "abrir_app", "alvo": "navegador"}}
"fecha essa janela" → {{"intencao": "fechar_janela"}}
"troque de janela" → {{"intencao": "alternar_janelas"}}
"abre o youtube" → {{"intencao": "abrir_site", "alvo": "youtube"}}
"bloqueia o computador" → {{"intencao": "bloquear_tela"}}
"o que é inteligência artificial?" → {{"intencao": "DESCONHECIDO"}}
"quem é você?" → {{"intencao": "DESCONHECIDO"}}
"o que significa minimizar?" → {{"intencao": "DESCONHECIDO"}}

Frase do usuário: "{texto}"
"""


# ══════════════════════════════════════════════════════════════════
# Comunicação com Ollama
# ══════════════════════════════════════════════════════════════════

# Aliases canônicos comuns mapeados para as ações oficiais do CATALOGO_ATALHOS
MAPA_ALIASES_INTENCOES: Dict[str, str] = {
    "mostrar_area_trabalho": "mostrar_area_de_trabalho",
    "mostrar_area_de_trabalho": "mostrar_area_de_trabalho",
    "area_de_trabalho": "mostrar_area_de_trabalho",
    "area_trabalho": "mostrar_area_de_trabalho",
    "minimizar_tudo": "mostrar_area_de_trabalho",
    "minimizar_todas_as_janelas": "mostrar_area_de_trabalho",
    "minimizar_as_janelas": "mostrar_area_de_trabalho",
    "esconder_janelas": "mostrar_area_de_trabalho",
    "esconder_as_janelas": "mostrar_area_de_trabalho",
    "alternar_janela": "alternar_janelas",
    "alternar_janelas": "alternar_janelas",
    "trocar_janela": "alternar_janelas",
    "trocar_de_janela": "alternar_janelas",
    "fechar_janela": "fechar_janela",
    "maximizar_janela": "maximizar_janela",
    "restaurar_ou_minimizar_janela": "restaurar_ou_minimizar_janela",
    "minimizar_janela": "restaurar_ou_minimizar_janela",
    "bloquear_tela": "bloquear_tela",
    "devtools": "devtools",
    "dev_tools": "devtools",
    "inspetor": "devtools",
    "inspecionar": "devtools",
    "codigo_fonte": "codigo_fonte",
    "console": "console",
    "tela_cheia": "tela_cheia",
    "nova_aba": "nova_aba",
    "fechar_aba": "fechar_aba",
    "voltar_pagina": "voltar_pagina",
}


def _chamar_ollama(
    prompt: str,
    url: str = OLLAMA_URL,
    modelo: str = OLLAMA_MODELO,
    timeout: float = OLLAMA_TIMEOUT,
) -> Optional[str]:
    """Faz a requisição HTTP ao Ollama e retorna o texto da resposta.

    Retorna None em qualquer falha (conexão, timeout, HTTP, parse).
    Nunca levanta exceção para o chamador.
    """
    try:
        import requests
    except ImportError:
        logger.warning("Resolvedor IA: 'requests' não instalado.")
        return None

    # O parâmetro permanece por compatibilidade, mas o projeto usa somente
    # qwen3:8b e não faz fallback silencioso para outro modelo.
    modelo = OLLAMA_MODEL
    dados = {
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "think": False,
        "options": {"num_predict": OLLAMA_NUM_PREDICT},
    }

    inicio = time.perf_counter()
    try:
        resposta = requests.post(url, json=dados, timeout=timeout)
        if resposta.status_code == 404 and "not found" in resposta.text.lower():
            logger.error("[OLLAMA][ERRO] Modelo %s não encontrado no resolvedor IA.", modelo)
            return None

        resposta.raise_for_status()
        corpo = resposta.json()
        if not isinstance(corpo, dict) or not isinstance(corpo.get("response"), str):
            logger.error("[OLLAMA][ERRO] Resposta inválida no resolvedor IA.")
            return None
        retorno = corpo["response"]
        logger.info(
            "[PERF] resolvedor_ia Ollama modelo=%s em %.1f ms",
            modelo,
            (time.perf_counter() - inicio) * 1000,
        )
        return retorno
    except requests.exceptions.ConnectionError:
        logger.error("[OLLAMA][ERRO] Ollama indisponível no resolvedor IA.")
        return None
    except requests.exceptions.Timeout:
        logger.error("[OLLAMA][ERRO] Timeout no resolvedor IA (%ss).", timeout)
        return None
    except requests.exceptions.HTTPError as exc:
        status = getattr(exc.response, "status_code", "?")
        logger.error("[OLLAMA][ERRO] HTTP %s no resolvedor IA.", status)
        return None
    except requests.exceptions.RequestException as exc:
        logger.error("[OLLAMA][ERRO] Requisição no resolvedor IA: %s", exc)
        return None
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        logger.error("[OLLAMA][ERRO] JSON inválido no resolvedor IA.")
        return None
    except Exception:
        logger.exception("[OLLAMA][ERRO] Falha inesperada no resolvedor IA.")
        return None


# ══════════════════════════════════════════════════════════════════
# Extração e Validação
# ══════════════════════════════════════════════════════════════════

def _extrair_json(texto: str) -> Optional[Dict[str, Any]]:
    """Extrai o primeiro objeto JSON de uma string.

    Lida com respostas limpas, markdown code blocks e texto extra.
    """
    if not texto:
        return None

    texto = texto.strip()

    # Tentativa 1: parse direto
    try:
        resultado = json.loads(texto)
        if isinstance(resultado, dict):
            return resultado
    except json.JSONDecodeError:
        pass

    # Tentativa 2: extrair primeiro {...} da string
    # Procura um objeto balanceado para aceitar campos aninhados sem usar
    # eval/exec e sem truncar a resposta do modelo no primeiro bloco.
    inicio = texto.find("{")
    if inicio >= 0:
        nivel = 0
        em_string = False
        escape = False
        for indice in range(inicio, len(texto)):
            caractere = texto[indice]
            if em_string:
                if escape:
                    escape = False
                elif caractere == "\\":
                    escape = True
                elif caractere == '"':
                    em_string = False
                continue
            if caractere == '"':
                em_string = True
            elif caractere == "{":
                nivel += 1
            elif caractere == "}":
                nivel -= 1
                if nivel == 0:
                    try:
                        resultado = json.loads(texto[inicio : indice + 1])
                        return resultado if isinstance(resultado, dict) else None
                    except json.JSONDecodeError:
                        break

    return None


def _validar_intencao(dados: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Valida a intenção retornada pela IA contra os catálogos oficiais.

    Retorna um dicionário pronto para o interpretador ou None se inválido.
    A IA NUNCA executa ações — esta função apenas converte a resposta em
    uma estrutura que o executor existente pode processar de forma segura.
    """
    from sistema_toke.catalogo.catalogo_atalho import CATALOGO_ATALHOS
    from sistema_toke.catalogo.catalogo_app import MAPA_APPS, resolver_nome_app
    from sistema_toke.catalogo.catalogo_site import CATALOGO_SITES

    intencao_raw = dados.get("intencao") or dados.get("acao") or ""
    if not isinstance(intencao_raw, str):
        return None

    intencao = intencao_raw.strip().lower().replace("-", "_")

    if not intencao or intencao == "desconhecido":
        return None

    # Aplica mapeamento canônico de aliases se aplicável
    if intencao in MAPA_ALIASES_INTENCOES:
        intencao = MAPA_ALIASES_INTENCOES[intencao]

    # ── 1. Atalhos do sistema e navegador ─────────────────────────
    if intencao in CATALOGO_ATALHOS:
        logger.info(
            "Resolvedor IA: intenção '%s' validada (atalho).", intencao
        )
        return {
            "tipo": "comando",
            "acao": intencao,
            "parametros": {},
            "confianca": 0.85,
            "fala": "",
            "falar": False,
        }

    # ── 2. Abrir aplicativo ───────────────────────────────────────
    if intencao in {"abrir_app", "abrir_aplicativo"}:
        entidades = dados.get("entidades") if isinstance(dados.get("entidades"), dict) else {}
        alvo = (dados.get("alvo") or dados.get("aplicativo") or entidades.get("aplicativo") or "")
        alvo = str(alvo).strip().lower()
        if not alvo:
            logger.debug("Resolvedor IA: abrir_app sem alvo.")
            return None

        nome_real = resolver_nome_app(alvo)
        if nome_real:
            logger.info(
                "Resolvedor IA: abrir_app '%s' → '%s'.", alvo, nome_real
            )
            return {
                "tipo": "comando",
                "acao": "abrir_app",
                "parametros": {"nome": nome_real},
                "entidades": {"aplicativo": nome_real},
                "confianca": _confianca_modelo(dados),
                "precisa_confirmacao": _confianca_modelo(dados) < 0.85,
                "fala": "",
                "falar": False,
            }
        logger.debug(
            "Resolvedor IA: alvo '%s' não encontrado em MAPA_APPS.", alvo
        )
        return None

    # ── 3. Abrir site ─────────────────────────────────────────────
    if intencao == "abrir_site":
        entidades = dados.get("entidades") if isinstance(dados.get("entidades"), dict) else {}
        alvo = (dados.get("alvo") or dados.get("site") or entidades.get("site") or "")
        alvo = str(alvo).strip().lower()
        if not alvo:
            logger.debug("Resolvedor IA: abrir_site sem alvo.")
            return None

        for _chave, site_info in CATALOGO_SITES.items():
            nomes_validos = [site_info.nome.lower()] + [
                s.lower() for s in site_info.sinonimos
            ]
            if alvo in nomes_validos:
                logger.info(
                    "Resolvedor IA: abrir_site '%s' → '%s'.",
                    alvo,
                    site_info.url,
                )
                return {
                    "tipo": "comando",
                    "acao": "abrir_site",
                    "parametros": {"url": site_info.url},
                    "entidades": {"site": site_info.nome},
                    "confianca": _confianca_modelo(dados),
                    "precisa_confirmacao": _confianca_modelo(dados) < 0.85,
                    "fala": "",
                    "falar": False,
                }

        logger.debug(
            "Resolvedor IA: alvo '%s' não encontrado em CATALOGO_SITES.", alvo
        )
        return None

    # ── 4. Intenção não reconhecida — rejeitar ────────────────────
    logger.debug(
        "Resolvedor IA: intenção '%s' NÃO existe no catálogo. Rejeitada.",
        intencao,
    )
    return None


def _confianca_modelo(dados: Dict[str, Any]) -> float:
    try:
        valor = float(dados.get("confianca", 0.85))
    except (TypeError, ValueError):
        valor = 0.0
    return max(0.0, min(1.0, valor))


# ══════════════════════════════════════════════════════════════════
# Interface pública
# ══════════════════════════════════════════════════════════════════

def interpretar_com_ia(
    texto: str,
    url: str = OLLAMA_URL,
    modelo: str = OLLAMA_MODELO,
    timeout: float = OLLAMA_TIMEOUT,
) -> Optional[Dict[str, Any]]:
    """Interpreta uma frase via IA local (Ollama) como fallback.

    Retorna um dicionário de intenção validado contra o catálogo oficial
    do AUTOWORK, ou None se a IA não conseguir interpretar, estiver
    indisponível, ou a intenção não for válida.

    Esta função NUNCA executa ações. Ela apenas interpreta e valida.
    """
    if not texto or not texto.strip():
        return None

    logger.debug("Resolvedor IA: consultando para: %r", texto)

    prompt = _construir_prompt(texto)
    resposta_texto = _chamar_ollama(
        prompt, url=url, modelo=modelo, timeout=timeout
    )

    if resposta_texto is None:
        logger.debug("Resolvedor IA: sem resposta do Ollama.")
        return None

    dados = _extrair_json(resposta_texto)
    if dados is None:
        logger.debug(
            "Resolvedor IA: JSON inválido na resposta: %r",
            resposta_texto[:200],
        )
        return None

    resultado = _validar_intencao(dados)
    if resultado is None:
        logger.debug("Resolvedor IA: intenção não validada: %s", dados)

    return resultado
