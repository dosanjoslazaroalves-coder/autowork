"""Módulo principal da personalidade e personificação do AUTOWORK.

Centraliza a identidade verbal, geração de respostas contextuais, confirmações,
tratamento de erros amigáveis e coordenação com estados emocionais e temporais.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from persn_emcoes.estado import ControladorEmocional, EstadoEmocional
from persn_emcoes.feedback import GerenciadorFeedback
from persn_emcoes.saudacao import GeradorSaudacao, obter_despedida, obter_saudacao


@dataclass
class ConfiguracaoFala:
    """Parâmetros e características de fala determinados pela personalidade."""

    texto: str
    velocidade: float = 0.85
    voz: str = "pm_santa"
    tom: str = "equilibrado e sóbrio"
    formalidade: str = "elegante"
    naturalidade: str = "alta"
    objetividade: str = "alta"
    cordialidade: str = "cortês"
    intensidade_emocional: str = "neutra"

# Variações para comandos não reconhecidos
_FRASES_NAO_RECONHECIDO: List[str] = [
    "Não reconheci esse comando, senhor.",
    "Não consegui identificar essa instrução.",
    "Instrução não compreendida. Poderia repetir?",
    "Não localizei essa ação nos módulos ativos.",
]

# Variações para confirmações de sucesso discretas
_FRASES_SUCESSO: List[str] = [
    "Operação concluída com sucesso.",
    "Comando executado.",
    "Ação finalizada com êxito.",
    "Pronto, senhor.",
]

# Variações para erros apresentados ao usuário
_FRASES_ERRO_AMIGAVEL: List[str] = [
    "Não foi possível concluir a operação no momento.",
    "Ocorreu uma falha durante o processamento da instrução.",
    "Não consegui finalizar essa tarefa. Verifique as configurações.",
]

_EXATAS_ESTILO: Dict[str, str] = {
    "sistema iniciado": "Inicialização concluída. Todos os sistemas estão operacionais.",
    "abrindo navegador": "Comando confirmado. Inicializando navegador.",
    "erro": "Não foi possível concluir a operação solicitada.",
}

_PadraoBuilder = Tuple[re.Pattern[str], Callable[[re.Match[str]], str]]
_PADROES_ESTILO: Tuple[_PadraoBuilder, ...] = (
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


class Personalidade:
    """Núcleo da identidade verbal e conduta comunicativa do AUTOWORK."""

    def __init__(self, nome_usuario: str = "Marco") -> None:
        self.nome_usuario = nome_usuario
        self.emocao = ControladorEmocional(EstadoEmocional.NEUTRO)
        self.saudador = GeradorSaudacao(nome_usuario=nome_usuario)
        self.feedback = GerenciadorFeedback()

        self._ultima_fala_sucesso: Optional[str] = None
        self._ultima_fala_nao_reconhecido: Optional[str] = None
        self._ultima_fala_erro: Optional[str] = None

    # ── Métodos de Saudação e Despedida ─────────────────────────────

    def saudar(self, momento: Optional[datetime] = None, incluir_data: bool = False) -> str:
        """Produz a saudação inicial do AUTOWORK e ajusta estado para ATENTO."""
        self.emocao.transitar(EstadoEmocional.ATENTO)
        return self.saudador.gerar_saudacao(momento=momento, incluir_data=incluir_data)

    def despedir(self) -> str:
        """Produz a fala de encerramento e ajusta estado para NEUTRO."""
        self.emocao.transitar(EstadoEmocional.NEUTRO)
        return self.saudador.gerar_despedida()

    # ── Mensagens Contextuais ───────────────────────────────────────

    def nao_reconhecido(self) -> str:
        """Mensagem elegante quando o comando não foi compreendido."""
        self.emocao.transitar(EstadoEmocional.ALERTA)
        candidatas = [f for f in _FRASES_NAO_RECONHECIDO if f != self._ultima_fala_nao_reconhecido] or _FRASES_NAO_RECONHECIDO
        escolhida = random.choice(candidatas)
        self._ultima_fala_nao_reconhecido = escolhida
        return escolhida

    def confirmar_conclusao(self, detalhe: Optional[str] = None) -> str:
        """Retorna uma fala polida de sucesso/conclusão."""
        self.emocao.transitar(EstadoEmocional.SATISFEITO)
        if detalhe and detalhe.strip():
            return f"Operação concluída. {detalhe.strip()}"

        candidatas = [f for f in _FRASES_SUCESSO if f != self._ultima_fala_sucesso] or _FRASES_SUCESSO
        escolhida = random.choice(candidatas)
        self._ultima_fala_sucesso = escolhida
        return escolhida

    def erro_amigavel(self, mensagem_original: Optional[str] = None) -> str:
        """Gera uma mensagem de erro compreensiva e elegante sem jargão desnecessário."""
        self.emocao.transitar(EstadoEmocional.ERRO)
        if mensagem_original and len(mensagem_original.split()) < 8 and not mensagem_original.lower().startswith("traceback"):
            return mensagem_original

        candidatas = [f for f in _FRASES_ERRO_AMIGAVEL if f != self._ultima_fala_erro] or _FRASES_ERRO_AMIGAVEL
        escolhida = random.choice(candidatas)
        self._ultima_fala_erro = escolhida
        return escolhida

    # ── Estilização Verbal ──────────────────────────────────────────

    def estilizar(self, texto: str) -> str:
        """Ajusta frases curtas para um tom consistente, polido e tecnológico."""
        limpo = " ".join((texto or "").strip().split())
        if not limpo:
            return limpo

        chave = limpo.lower().rstrip(".")
        if chave in _EXATAS_ESTILO:
            return _EXATAS_ESTILO[chave]

        # Se for resposta longa (ex.: gerada pelo Chatbot/LLM), preserva a integridade original
        if len(limpo.split()) > 14:
            return limpo

        for padrao, builder in _PADROES_ESTILO:
            match = padrao.match(limpo)
            if match:
                return builder(match)

        return limpo

    # ── Integração com Módulo de Fala ───────────────────────────────

    def configurar_fala(
        self,
        texto: str,
        estado: Optional[EstadoEmocional] = None,
    ) -> ConfiguracaoFala:
        """Determina as características e parâmetros acústicos suportados para a fala.

        Modula a velocidade da elocução conforme o estado emocional simulado e
        preserva o tom, formalidade e intensidade nos metadados.
        """
        estado_ativo = estado or self.emocao.atual
        texto_final = self.estilizar(texto)

        mapa_config: Dict[EstadoEmocional, Dict[str, Any]] = {
            EstadoEmocional.NEUTRO: {
                "velocidade": 0.85,
                "tom": "equilibrado e sóbrio",
                "cordialidade": "cortês",
                "intensidade_emocional": "neutra",
            },
            EstadoEmocional.ATENTO: {
                "velocidade": 0.88,
                "tom": "focado e conciso",
                "cordialidade": "pronta",
                "intensidade_emocional": "moderada",
            },
            EstadoEmocional.PROCESSANDO: {
                "velocidade": 0.82,
                "tom": "analítico e calmo",
                "cordialidade": "cortês",
                "intensidade_emocional": "baixa",
            },
            EstadoEmocional.SATISFEITO: {
                "velocidade": 0.86,
                "tom": "prestativo e polido",
                "cordialidade": "calorosa e respeitosa",
                "intensidade_emocional": "moderada",
            },
            EstadoEmocional.ALERTA: {
                "velocidade": 0.92,
                "tom": "vigilante e direto",
                "cordialidade": "sóbria",
                "intensidade_emocional": "alta",
            },
            EstadoEmocional.ERRO: {
                "velocidade": 0.82,
                "tom": "compreensivo e resolutivo",
                "cordialidade": "atenciosa",
                "intensidade_emocional": "contida",
            },
            EstadoEmocional.CONCLUIDO: {
                "velocidade": 0.87,
                "tom": "eficiente e discreto",
                "cordialidade": "cortês",
                "intensidade_emocional": "neutra",
            },
        }

        cfg = mapa_config.get(estado_ativo, mapa_config[EstadoEmocional.NEUTRO])

        return ConfiguracaoFala(
            texto=texto_final,
            velocidade=cfg["velocidade"],
            voz="pm_santa",
            tom=cfg["tom"],
            formalidade="elegante",
            naturalidade="alta",
            objetividade="alta",
            cordialidade=cfg["cordialidade"],
            intensidade_emocional=cfg["intensidade_emocional"],
        )


# Instância global padrão
_PERSONALIDADE_PADRAO = Personalidade()


def estilizar_fala(texto: str) -> str:
    """Função compatível com a interface anterior de estilização."""
    return _PERSONALIDADE_PADRAO.estilizar(texto)
