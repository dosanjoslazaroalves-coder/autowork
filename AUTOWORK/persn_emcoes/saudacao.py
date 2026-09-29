"""Módulo de saudações e despedidas personalizadas do AUTOWORK.

Responsável por consultar o horário e dia da semana e compor saudações
contextualizadas, elegantes e variadas para evitar monotonia.
"""
from __future__ import annotations

import random
from datetime import datetime
from typing import List, Optional, Tuple

_DIAS_SEMANA_PT: Tuple[str, ...] = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)

_NOME_PADRAO = "Marco"

# Templates de saudação organizados por período do dia.
# Marcadores disponíveis: {nome}, {dia_semana}, {data}
_MODELOS_MANHA: List[str] = [
    "Bom dia, {nome}. Hoje é {dia_semana}. O AUTOWORK está online e pronto para suas instruções.",
    "Bom dia, {nome}. Sistemas inicializados nesta {dia_semana}. O AUTOWORK está à sua disposição.",
    "Bom dia, {nome}. Hoje é {dia_semana}. Tudo pronto para começarmos as atividades.",
    "Bom dia, {nome}. AUTOWORK online nesta {dia_semana}. Aguardo seu comando.",
]

_MODELOS_TARDE: List[str] = [
    "Boa tarde, {nome}. O AUTOWORK está online e pronto para suas instruções.",
    "Boa tarde, {nome}. Sistemas operacionais nesta {dia_semana}. Em que posso ajudar?",
    "Boa tarde, {nome}. Assistente AUTOWORK ativo e aguardando suas diretrizes.",
    "Boa tarde, {nome}. Todos os módulos sincronizados nesta {dia_semana}. Pronto para continuar.",
]

_MODELOS_NOITE: List[str] = [
    "Boa noite, {nome}. Sistemas inicializados nesta {dia_semana}. Estou pronto.",
    "Boa noite, {nome}. AUTOWORK online e pronto para suas tarefas.",
    "Boa noite, {nome}. Tudo operacional nesta {dia_semana}. Aguardo suas instruções.",
    "Boa noite, {nome}. Módulos prontos. À sua disposição.",
]

_MODELOS_DESPEDIDA: List[str] = [
    "Encerrando o AUTOWORK, {nome}. Até logo.",
    "Desligando os sistemas, {nome}. Tenha um ótimo descanso.",
    "AUTOWORK finalizado. Estarei disponível quando precisar.",
    "Encerrando operações, {nome}. Até a próxima.",
]


class GeradorSaudacao:
    """Gera saudações e despedidas inteligentes com alternância de variações."""

    def __init__(self, nome_usuario: str = _NOME_PADRAO) -> None:
        self.nome_usuario = nome_usuario
        self._ultima_saudacao: Optional[str] = None
        self._ultima_despedida: Optional[str] = None

    @staticmethod
    def identificar_periodo(hora: int) -> str:
        """Determina o período ('manha', 'tarde', 'noite') a partir da hora (0-23)."""
        if 5 <= hora < 12:
            return "manha"
        if 12 <= hora < 18:
            return "tarde"
        return "noite"

    @staticmethod
    def obter_dia_semana(momento: Optional[datetime] = None) -> str:
        """Retorna o nome do dia da semana em português."""
        dt = momento or datetime.now()
        return _DIAS_SEMANA_PT[dt.weekday()]

    def gerar_saudacao(
        self,
        momento: Optional[datetime] = None,
        incluir_data: bool = False,
    ) -> str:
        """Gera uma saudação de inicialização baseada no horário e no dia.

        Args:
            momento: Datetime opcional para testes ou simulações. Se omitido, usa datetime.now().
            incluir_data: Se True, anexa a data formatada no final.

        Returns:
            String com a saudação personalizada e elegante.
        """
        dt = momento or datetime.now()
        periodo = self.identificar_periodo(dt.hour)
        dia_semana = self.obter_dia_semana(dt)
        data_formatada = dt.strftime("%d/%m/%Y")

        if periodo == "manha":
            opcoes = _MODELOS_MANHA
        elif periodo == "tarde":
            opcoes = _MODELOS_TARDE
        else:
            opcoes = _MODELOS_NOITE

        # Evita repetir imediatamente a mesma variação anterior
        candidatos = [op for op in opcoes if op != self._ultima_saudacao] or opcoes
        escolhido = random.choice(candidatos)
        self._ultima_saudacao = escolhido

        saudacao = escolhido.format(
            nome=self.nome_usuario,
            dia_semana=dia_semana,
            data=data_formatada,
        )

        if incluir_data and "{data}" not in escolhido:
            saudacao = f"{saudacao} Data de hoje: {data_formatada}."

        return saudacao

    def gerar_despedida(self) -> str:
        """Gera uma frase elegante de encerramento."""
        candidatos = [op for op in _MODELOS_DESPEDIDA if op != self._ultima_despedida] or _MODELOS_DESPEDIDA
        escolhido = random.choice(candidatos)
        self._ultima_despedida = escolhido
        return escolhido.format(nome=self.nome_usuario)


_INSTANCIA_GLOBAL = GeradorSaudacao()


def obter_saudacao(
    momento: Optional[datetime] = None,
    incluir_data: bool = False,
    nome: Optional[str] = None,
) -> str:
    """Função utilitária direta para obter saudação formatada."""
    gerador = _INSTANCIA_GLOBAL if nome is None else GeradorSaudacao(nome)
    return gerador.gerar_saudacao(momento=momento, incluir_data=incluir_data)


def obter_despedida(nome: Optional[str] = None) -> str:
    """Função utilitária direta para obter frase de encerramento."""
    gerador = _INSTANCIA_GLOBAL if nome is None else GeradorSaudacao(nome)
    return gerador.gerar_despedida()
