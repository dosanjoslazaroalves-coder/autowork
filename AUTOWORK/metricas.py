"""
Camada de observabilidade do AUTOWORK.

Não controla o fluxo do assistente. Coleta tempo, RAM do processo (OS),
alocações Python (opcional) e CPU. A fala consome apenas o texto já formatado.

Ativação:
    AUTOWORK_PROFILING=1
    AUTOWORK_METRICAS_IMPRIMIR=1
    AUTOWORK_METRICAS_FALA=1

Profiling pesado (tracemalloc, cProfile) só entra pelos modos do
rodar_metricas.py — nunca no caminho normal de um comando.
"""

from __future__ import annotations

import os
import statistics
import threading
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# ── Flag leve (checagem de env; custo desprezível) ───────────────────────────

_TRUTHY = {"1", "true", "yes", "on", "sim"}


def _env_ligado(nome: str) -> bool:
    return os.environ.get(nome, "").strip().lower() in _TRUTHY


def profiling_ativo() -> bool:
    return _env_ligado("AUTOWORK_PROFILING")


def imprimir_relatorio_ativo() -> bool:
    return _env_ligado("AUTOWORK_METRICAS_IMPRIMIR")


def falar_relatorio_ativo() -> bool:
    return _env_ligado("AUTOWORK_METRICAS_FALA")


# ── Conversões ────────────────────────────────────────────────────────────────

_BYTES_POR_MB = 1024.0 * 1024.0


def bytes_para_mb(n: int | float) -> float:
    return float(n) / _BYTES_POR_MB


def formatar_mb(n_bytes: int | float, casas: int = 1) -> str:
    return f"{bytes_para_mb(n_bytes):.{casas}f} MB"


def formatar_segundos(s: float, casas: int = 3) -> str:
    return f"{s:.{casas}f} s"


def formatar_numero_fala(valor: float, casas: int = 2) -> str:
    texto = f"{valor:.{casas}f}"
    return texto.replace(".", ",")


# ── psutil (RAM do processo ≠ heap Python) ───────────────────────────────────

_psutil = None
_psutil_erro: Optional[str] = None

try:
    import psutil as _psutil  # type: ignore
except ImportError:
    _psutil_erro = (
        "psutil não instalado. RAM/CPU do processo ficarão indisponíveis. "
        "Instale com: pip install psutil"
    )


def psutil_disponivel() -> bool:
    return _psutil is not None


def aviso_psutil() -> Optional[str]:
    return _psutil_erro


class ObservadorProcesso:
    """
    Observa o processo no nível do SO.

    RAM: Process.memory_info().rss (resident set — páginas na RAM física).
    Isso NÃO é o mesmo que tracemalloc (alocações rastreadas pelo alocador
    do Python).

    CPU: cpu_percent(interval=None) exige duas amostras. A primeira leitura
    de um Process() é 0.0 e deve ser descartada (documentação do psutil).
    """

    def __init__(self) -> None:
        self._proc = None
        self._prime = False
        if _psutil is None:
            return
        self._proc = _psutil.Process(os.getpid())
        self._proc.cpu_percent(interval=None)
        _psutil.cpu_percent(interval=None)
        self._prime = True

    def rss_bytes(self) -> Optional[int]:
        if self._proc is None:
            return None
        return int(self._proc.memory_info().rss)

    def cpu_processo_percent(self) -> Optional[float]:
        if self._proc is None:
            return None
        valor = float(self._proc.cpu_percent(interval=None))
        if not self._prime:
            return None
        return valor

    def cpu_sistema_percent(self) -> Optional[float]:
        if _psutil is None:
            return None
        return float(_psutil.cpu_percent(interval=None))


_observador_global: Optional[ObservadorProcesso] = None


def observador() -> ObservadorProcesso:
    global _observador_global
    if _observador_global is None:
        _observador_global = ObservadorProcesso()
    return _observador_global


# ── Amostragem de CPU (não bloqueia o teste de velocidade) ───────────────────

class AmostradorCPU:
    """
    Thread que amostra CPU a cada intervalo (padrão 0,1 s).

    Não usa cpu_percent(interval=1): isso bloquearia 1 s e distorceria
    o teste de velocidade.
    A primeira amostra após o prime ainda pode ser 0.0 — é ignorada.
    """

    def __init__(self, intervalo: float = 0.1) -> None:
        self.intervalo = intervalo
        self.amostras_processo: List[float] = []
        self.amostras_sistema: List[float] = []
        self._parar = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._obs = observador()

    def iniciar(self) -> None:
        if not psutil_disponivel():
            return
        self._obs.cpu_processo_percent()
        self._obs.cpu_sistema_percent()
        self._parar.clear()
        self._thread = threading.Thread(target=self._loop, name="cpu-metricas", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        primeira = True
        while not self._parar.wait(self.intervalo):
            p = self._obs.cpu_processo_percent()
            s = self._obs.cpu_sistema_percent()
            if primeira:
                primeira = False
                continue
            if p is not None:
                self.amostras_processo.append(p)
            if s is not None:
                self.amostras_sistema.append(s)

    def parar(self) -> None:
        self._parar.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def resumo(self) -> Dict[str, Optional[float]]:
        def _stats(xs: List[float]) -> Tuple[Optional[float], Optional[float]]:
            if not xs:
                return None, None
            return sum(xs) / len(xs), max(xs)

        med_p, pico_p = _stats(self.amostras_processo)
        med_s, pico_s = _stats(self.amostras_sistema)
        return {
            "processo_media": med_p,
            "processo_pico": pico_p,
            "sistema_media": med_s,
            "sistema_pico": pico_s,
            "n_amostras": float(len(self.amostras_processo)),
        }


# ── RAM ───────────────────────────────────────────────────────────────────────

@dataclass
class SnapshotRAM:
    rotulo: str
    rss_bytes: Optional[int]
    tracemalloc_atual: Optional[int] = None
    tracemalloc_pico: Optional[int] = None


class RegistroRAM:
    def __init__(self) -> None:
        self.snapshots: List[SnapshotRAM] = []
        self.pico_rss: Optional[int] = None

    def capturar(self, rotulo: str) -> SnapshotRAM:
        rss = observador().rss_bytes()
        tm_atual = tm_pico = None
        if tracemalloc.is_tracing():
            atual, pico = tracemalloc.get_traced_memory()
            tm_atual, tm_pico = int(atual), int(pico)
        snap = SnapshotRAM(rotulo, rss, tm_atual, tm_pico)
        self.snapshots.append(snap)
        if rss is not None:
            self.pico_rss = rss if self.pico_rss is None else max(self.pico_rss, rss)
        return snap

    def por_rotulo(self, rotulo: str) -> Optional[SnapshotRAM]:
        for s in reversed(self.snapshots):
            if s.rotulo == rotulo:
                return s
        return None

    def delta(self, de: str, para: str) -> Optional[int]:
        a = self.por_rotulo(de)
        b = self.por_rotulo(para)
        if a is None or b is None or a.rss_bytes is None or b.rss_bytes is None:
            return None
        return b.rss_bytes - a.rss_bytes


# ── Tempo (perf_counter_ns) ───────────────────────────────────────────────────

def agora_ns() -> int:
    return time.perf_counter_ns()


def ns_para_s(ns: int) -> float:
    return ns / 1_000_000_000.0


class MedidorEtapas:
    """Tempos de parede independentes por etapa (clock monotonic de alta resolução)."""

    def __init__(self) -> None:
        self._inicios: Dict[str, int] = {}
        self.tempos_s: Dict[str, float] = {}
        self.inicio_total_ns: Optional[int] = None
        self.fim_total_ns: Optional[int] = None

    def iniciar_total(self) -> None:
        self.inicio_total_ns = agora_ns()

    def parar_total(self) -> float:
        self.fim_total_ns = agora_ns()
        return self.total_s()

    def iniciar(self, etapa: str) -> None:
        self._inicios[etapa] = agora_ns()

    def parar(self, etapa: str) -> float:
        inicio = self._inicios.pop(etapa, None)
        if inicio is None:
            return 0.0
        duracao = ns_para_s(agora_ns() - inicio)
        self.tempos_s[etapa] = self.tempos_s.get(etapa, 0.0) + duracao
        return duracao

    def registrar(self, etapa: str, duracao_s: float) -> None:
        if duracao_s < 0:
            return
        self.tempos_s[etapa] = self.tempos_s.get(etapa, 0.0) + duracao_s

    def total_s(self) -> float:
        if self.inicio_total_ns is None or self.fim_total_ns is None:
            return sum(self.tempos_s.values())
        return ns_para_s(self.fim_total_ns - self.inicio_total_ns)


class etapa:
    """Context manager: with etapa(medidor, 'parser'): ..."""

    def __init__(self, medidor: Optional[MedidorEtapas], nome: str) -> None:
        self._medidor = medidor
        self._nome = nome
        self.duracao: float = 0.0

    def __enter__(self) -> "etapa":
        if self._medidor is not None:
            self._medidor.iniciar(self._nome)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._medidor is not None:
            self.duracao = self._medidor.parar(self._nome)


# ── tracemalloc (opcional) ────────────────────────────────────────────────────

@dataclass
class ResumoTracemalloc:
    atual_bytes: int
    pico_bytes: int
    top_alocacoes: List[str]
    diff_linhas: List[str] = field(default_factory=list)


class SessaoTracemalloc:
    def __init__(self, nframe: int = 10) -> None:
        self.nframe = nframe
        self._snap_inicial = None
        self.ativa = False

    def iniciar(self) -> None:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        tracemalloc.start(self.nframe)
        self._snap_inicial = tracemalloc.take_snapshot()
        self.ativa = True

    def parar_e_resumo(self, limite: int = 15) -> Optional[ResumoTracemalloc]:
        if not self.ativa:
            return None
        atual, pico = tracemalloc.get_traced_memory()
        snap = tracemalloc.take_snapshot()
        stats = snap.statistics("lineno")
        top: List[str] = []
        for st in stats[:limite]:
            top.append(
                f"{st.traceback} | {formatar_mb(st.size)} | {st.count} bloco(s)"
            )
        diff: List[str] = []
        if self._snap_inicial is not None:
            for st in snap.compare_to(self._snap_inicial, "lineno")[:limite]:
                diff.append(
                    f"{st.traceback} | size_diff={formatar_mb(st.size_diff)} "
                    f"count_diff={st.count_diff}"
                )
        tracemalloc.stop()
        self.ativa = False
        return ResumoTracemalloc(int(atual), int(pico), top, diff)


# ── Gargalo ───────────────────────────────────────────────────────────────────

ROTULOS_ETAPA = {
    "inicializacao": "Inicialização",
    "catalogo": "Catálogo",
    "mapas_derivados": "Mapas derivados",
    "imports": "Imports do pipeline",
    "normalizador": "Normalizador",
    "parser": "Parser",
    "interpretador": "Interpretador",
    "executor": "Executor",
    "resposta": "Geração da resposta",
    "fala": "Fala / TTS",
    "captura": "Captura de áudio",
    "transcricao": "Transcrição",
}


def classificar_gargalo(
    tempos: Dict[str, float],
    total_s: float,
) -> Tuple[Optional[str], Optional[float], str]:
    """
    Gargalo = etapa com maior tempo de parede, se representar fatia relevante.
    Muitas chamadas ≠ gargalo. Tempo total e tempo por chamada importam no cProfile.
    """
    candidatos = {k: v for k, v in tempos.items() if v > 0}
    if not candidatos or total_s <= 0:
        return None, None, "Sem dados suficientes para classificar gargalo."

    nome = max(candidatos, key=lambda k: candidatos[k])
    valor = candidatos[nome]
    pct = 100.0 * valor / total_s
    rotulo = ROTULOS_ETAPA.get(nome, nome)

    if pct < 20.0:
        texto = (
            f"Nenhum gargalo dominante. A etapa mais lenta foi {rotulo} "
            f"({formatar_segundos(valor)}, {pct:.1f}% do tempo total)."
        )
    else:
        texto = f"{rotulo} — {pct:.1f}% do tempo total"
    return nome, pct, texto


# ── Relatório ─────────────────────────────────────────────────────────────────

@dataclass
class Relatorio:
    tempos: Dict[str, float]
    total_s: float
    ram: RegistroRAM
    cpu: Dict[str, Optional[float]] = field(default_factory=dict)
    tracemalloc: Optional[ResumoTracemalloc] = None
    notas: List[str] = field(default_factory=list)
    metadados: Dict[str, Any] = field(default_factory=dict)
    cprofile_texto: Optional[str] = None

    def gargalo(self) -> Tuple[Optional[str], Optional[float], str]:
        return classificar_gargalo(self.tempos, self.total_s)

    def texto_terminal(self) -> str:
        linhas = [
            "========== AUTOWORK PROFILING ==========",
            "",
            f"Tempo total: {formatar_segundos(self.total_s)}",
            "",
            "RAM do processo (RSS, sistema operacional):",
        ]
        ini = self.ram.por_rotulo("inicial")
        fim = self.ram.por_rotulo("final")
        if ini and ini.rss_bytes is not None:
            linhas.append(f"  Inicial: {formatar_mb(ini.rss_bytes)}")
        if fim and fim.rss_bytes is not None:
            linhas.append(f"  Final:   {formatar_mb(fim.rss_bytes)}")
        if ini and fim and ini.rss_bytes is not None and fim.rss_bytes is not None:
            delta = fim.rss_bytes - ini.rss_bytes
            sinal = "+" if delta >= 0 else ""
            pct = (100.0 * delta / ini.rss_bytes) if ini.rss_bytes else 0.0
            linhas.append(f"  Variação: {sinal}{formatar_mb(delta)} ({sinal}{pct:.1f}%)")
        if self.ram.pico_rss is not None:
            linhas.append(f"  Pico:    {formatar_mb(self.ram.pico_rss)}")

        pares = [
            ("após_imports", "Após imports base"),
            ("após_catalogo", "Após carregar catálogo"),
            ("após_mapas", "Após mapas derivados"),
            ("antes_comando", "Antes do comando"),
            ("depois_comando", "Depois do comando"),
        ]
        for chave, rotulo in pares:
            snap = self.ram.por_rotulo(chave)
            if snap and snap.rss_bytes is not None:
                linhas.append(f"  {rotulo}: {formatar_mb(snap.rss_bytes)}")

        if not psutil_disponivel():
            linhas.append("  (psutil ausente — RSS não medido)")

        linhas.append("")
        linhas.append("CPU (psutil; primeira amostra 0.0 descartada):")
        if self.cpu.get("processo_media") is not None:
            linhas.append(f"  Processo média: {self.cpu['processo_media']:.1f}%")
            linhas.append(f"  Processo pico:  {self.cpu['processo_pico']:.1f}%")
        else:
            linhas.append("  Processo: sem amostras (intervalo curto ou psutil ausente)")
        if self.cpu.get("sistema_media") is not None:
            linhas.append(f"  Sistema média:  {self.cpu['sistema_media']:.1f}%")
            linhas.append(f"  Sistema pico:   {self.cpu['sistema_pico']:.1f}%")
        if self.cpu.get("n_amostras"):
            linhas.append(f"  Amostras:       {int(self.cpu['n_amostras'])}")

        linhas.append("")
        linhas.append("ETAPAS:")
        ordem = (
            "inicializacao",
            "imports",
            "catalogo",
            "mapas_derivados",
            "normalizador",
            "parser",
            "interpretador",
            "executor",
            "resposta",
            "fala",
            "captura",
            "transcricao",
        )
        vistos = set()
        for chave in ordem:
            if chave in self.tempos:
                nome = ROTULOS_ETAPA.get(chave, chave)
                linhas.append(f"  {nome:.<22} {formatar_segundos(self.tempos[chave])}")
                vistos.add(chave)
        for chave, valor in self.tempos.items():
            if chave not in vistos:
                nome = ROTULOS_ETAPA.get(chave, chave)
                linhas.append(f"  {nome:.<22} {formatar_segundos(valor)}")

        _, _, texto_g = self.gargalo()
        linhas.append("")
        linhas.append("GARGALO (com base nestas medições):")
        linhas.append(f"  {texto_g}")

        if self.notas:
            linhas.append("")
            linhas.append("NOTAS:")
            for n in self.notas:
                linhas.append(f"  - {n}")

        if self.tracemalloc:
            linhas.append("")
            linhas.append("TRACEMALLOC (alocações do alocador Python, não RSS):")
            linhas.append(f"  Atual: {formatar_mb(self.tracemalloc.atual_bytes)}")
            linhas.append(f"  Pico:  {formatar_mb(self.tracemalloc.pico_bytes)}")
            linhas.append("  Principais alocações:")
            for linha in self.tracemalloc.top_alocacoes[:12]:
                linhas.append(f"    {linha}")
            if self.tracemalloc.diff_linhas:
                linhas.append("  Diff vs snapshot inicial:")
                for linha in self.tracemalloc.diff_linhas[:12]:
                    linhas.append(f"    {linha}")

        if self.cprofile_texto:
            linhas.append("")
            linhas.append("CPROFILE / PSTATS (ordenar por tempo interno, não só ncalls):")
            linhas.append(self.cprofile_texto)

        linhas.append("")
        linhas.append("==========================================")
        return "\n".join(linhas)

    def texto_fala(self) -> str:
        """Texto para o TTS. Não mede nada — só narra o relatório já coletado."""
        partes = ["Diagnóstico concluído."]
        partes.append(
            f"O sistema levou {formatar_numero_fala(self.total_s, 2)} segundos."
        )
        nome, pct, _ = self.gargalo()
        if nome and pct is not None:
            rotulo = ROTULOS_ETAPA.get(nome, nome)
            if pct >= 20.0:
                partes.append(f"A etapa mais demorada foi {rotulo.lower()}.")
            else:
                partes.append("Não houve um gargalo dominante nesta execução.")
        ini = self.ram.por_rotulo("inicial")
        fim = self.ram.por_rotulo("final")
        if ini and fim and ini.rss_bytes is not None and fim.rss_bytes is not None:
            delta = fim.rss_bytes - ini.rss_bytes
            partes.append(
                "O consumo de memória do processo "
                f"{'aumentou' if delta >= 0 else 'diminuiu'} "
                f"{formatar_numero_fala(abs(bytes_para_mb(delta)), 1)} megabytes."
            )
        return " ".join(partes)


def texto_para_fala(relatorio: Relatorio) -> str:
    return relatorio.texto_fala()


# ── Comparação de execuções ───────────────────────────────────────────────────

@dataclass
class ResumoComparacao:
    n: int
    media: float
    minimo: float
    maximo: float
    desvio: Optional[float]
    etapas_media: Dict[str, float]


def comparar_totais(amostras: Sequence[Relatorio]) -> Optional[ResumoComparacao]:
    if not amostras:
        return None
    totais = [r.total_s for r in amostras]
    chaves: set[str] = set()
    for r in amostras:
        chaves.update(r.tempos)
    etapas_media = {
        k: sum(r.tempos.get(k, 0.0) for r in amostras) / len(amostras)
        for k in sorted(chaves)
    }
    desvio = statistics.stdev(totais) if len(totais) >= 2 else None
    return ResumoComparacao(
        n=len(totais),
        media=sum(totais) / len(totais),
        minimo=min(totais),
        maximo=max(totais),
        desvio=desvio,
        etapas_media=etapas_media,
    )


def texto_comparacao(resumo: ResumoComparacao, titulo: str = "COMPARAÇÃO") -> str:
    linhas = [
        f"========== {titulo} ==========",
        f"Execuções: {resumo.n}",
        f"Média:     {formatar_segundos(resumo.media)}",
        f"Mínimo:    {formatar_segundos(resumo.minimo)}",
        f"Máximo:    {formatar_segundos(resumo.maximo)}",
    ]
    if resumo.desvio is not None:
        linhas.append(f"Desvio:    {formatar_segundos(resumo.desvio)}")
    linhas.append("Médias por etapa:")
    for k, v in resumo.etapas_media.items():
        nome = ROTULOS_ETAPA.get(k, k)
        linhas.append(f"  {nome:.<22} {formatar_segundos(v)}")
    linhas.append("==========================================")
    return "\n".join(linhas)


# ── Ciclo usado por fala.py ───────────────────────────────────────────────────

_ciclo_atual: Optional["CicloComando"] = None


class CicloComando:
    def __init__(self) -> None:
        self.etapas = MedidorEtapas()
        self.ram = RegistroRAM()
        self.cpu_amostrador: Optional[AmostradorCPU] = None
        self.notas: List[str] = []

    def iniciar(self, amostrar_cpu: bool = False) -> None:
        self.etapas.iniciar_total()
        self.ram.capturar("antes_comando")
        if amostrar_cpu and psutil_disponivel():
            self.cpu_amostrador = AmostradorCPU()
            self.cpu_amostrador.iniciar()

    def finalizar(self) -> Relatorio:
        self.etapas.parar_total()
        self.ram.capturar("depois_comando")
        self.ram.capturar("final")
        cpu: Dict[str, Optional[float]] = {}
        if self.cpu_amostrador is not None:
            self.cpu_amostrador.parar()
            cpu = self.cpu_amostrador.resumo()
        ini = self.ram.por_rotulo("antes_comando")
        if ini is not None and self.ram.por_rotulo("inicial") is None:
            self.ram.snapshots.insert(
                0,
                SnapshotRAM("inicial", ini.rss_bytes, ini.tracemalloc_atual, ini.tracemalloc_pico),
            )
        self.notas.append(
            "parser.parse() chama normalizar() internamente; os tempos de "
            "normalizador e parser podem se sobrepor nesta instrumentação."
        )
        return Relatorio(
            tempos=dict(self.etapas.tempos_s),
            total_s=self.etapas.total_s(),
            ram=self.ram,
            cpu=cpu,
            notas=list(self.notas),
        )


def iniciar_ciclo_comando(amostrar_cpu: bool = False) -> Optional[CicloComando]:
    global _ciclo_atual
    if not profiling_ativo():
        return None
    _ciclo_atual = CicloComando()
    _ciclo_atual.iniciar(amostrar_cpu=amostrar_cpu)
    return _ciclo_atual


def ciclo_atual() -> Optional[CicloComando]:
    return _ciclo_atual


def finalizar_ciclo_comando() -> Optional[Relatorio]:
    global _ciclo_atual
    if _ciclo_atual is None:
        return None
    rel = _ciclo_atual.finalizar()
    _ciclo_atual = None
    return rel


def envolver_falar(func_falar: Callable[..., Any]) -> Callable[..., Any]:
    """Envolve TTS para cronometrar. A função original continua responsável pela fala."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ciclo = ciclo_atual()
        medidor = ciclo.etapas if ciclo is not None else None
        with etapa(medidor, "fala"):
            return func_falar(*args, **kwargs)

    return wrapper


def publicar_relatorio(relatorio: Relatorio) -> None:
    if imprimir_relatorio_ativo():
        print(relatorio.texto_terminal())


# ── Painel de RAM para fala.py (sempre leve; sem tracemalloc/cProfile) ────────

class PainelMemoria:
    """
    Leituras RSS do processo para exibição no fluxo do fala.py.
    Não decide comandos; só observa memória do SO (não o heap do Python).
    """

    def __init__(self) -> None:
        self.rss_inicial: Optional[int] = None
        self.pico_rss: Optional[int] = None
        self.ultima_antes: Optional[int] = None
        self.ultima_depois: Optional[int] = None

    def _atualizar_pico(self, rss: Optional[int]) -> Optional[int]:
        if rss is None:
            return None
        self.pico_rss = rss if self.pico_rss is None else max(self.pico_rss, rss)
        return rss

    def marcar_inicio_processo(self) -> Optional[int]:
        self.rss_inicial = self._atualizar_pico(observador().rss_bytes())
        return self.rss_inicial

    def ler(self) -> Optional[int]:
        return self._atualizar_pico(observador().rss_bytes())

    def marcar_antes_comando(self) -> Optional[int]:
        self.ultima_antes = self.ler()
        return self.ultima_antes

    def marcar_depois_comando(self) -> Optional[int]:
        self.ultima_depois = self.ler()
        return self.ultima_depois

    def texto_terminal_inicio(self) -> str:
        if self.rss_inicial is None:
            aviso = aviso_psutil() or "RSS indisponível."
            return f"  ▶ Memória do processo: {aviso}"
        return (
            "  ▶ Memória do processo (RAM/RSS):\n"
            f"  ▶   Inicial: {formatar_mb(self.rss_inicial)}"
        )

    def texto_terminal_comando(self) -> str:
        if not psutil_disponivel():
            return f"  ▶ Memória do processo: {aviso_psutil()}"
        linhas = ["  ▶ Memória do processo (RAM/RSS):"]
        if self.rss_inicial is not None:
            linhas.append(f"  ▶   Desde o início: {formatar_mb(self.rss_inicial)}")
        if self.ultima_antes is not None:
            linhas.append(f"  ▶   Antes do comando: {formatar_mb(self.ultima_antes)}")
        if self.ultima_depois is not None:
            linhas.append(f"  ▶   Depois do comando: {formatar_mb(self.ultima_depois)}")
        if (
            self.ultima_antes is not None
            and self.ultima_depois is not None
        ):
            delta = self.ultima_depois - self.ultima_antes
            sinal = "+" if delta >= 0 else ""
            linhas.append(f"  ▶   Gasta neste comando: {sinal}{formatar_mb(delta)}")
        if self.rss_inicial is not None and self.ultima_depois is not None:
            delta_total = self.ultima_depois - self.rss_inicial
            sinal = "+" if delta_total >= 0 else ""
            linhas.append(f"  ▶   Variação desde o início: {sinal}{formatar_mb(delta_total)}")
        if self.pico_rss is not None:
            linhas.append(f"  ▶   Pico observado: {formatar_mb(self.pico_rss)}")
        return "\n".join(linhas)

    def texto_fala_inicio(self) -> str:
        if self.rss_inicial is None:
            return "Não foi possível medir a memória do processo."
        return (
            "Memória inicial do processo: "
            f"{formatar_numero_fala(bytes_para_mb(self.rss_inicial), 1)} megabytes."
        )

    def texto_fala_comando(self) -> str:
        if self.ultima_antes is None or self.ultima_depois is None:
            return "Não foi possível medir a memória gasta neste comando."
        delta = self.ultima_depois - self.ultima_antes
        verbo = "aumentou" if delta >= 0 else "diminuiu"
        partes = [
            "Neste comando a memória do processo "
            f"{verbo} {formatar_numero_fala(abs(bytes_para_mb(delta)), 1)} megabytes."
        ]
        partes.append(
            "Uso atual: "
            f"{formatar_numero_fala(bytes_para_mb(self.ultima_depois), 1)} megabytes."
        )
        if self.pico_rss is not None:
            partes.append(
                "Pico observado: "
                f"{formatar_numero_fala(bytes_para_mb(self.pico_rss), 1)} megabytes."
            )
        return " ".join(partes)


painel_memoria = PainelMemoria()


# ── Compatibilidade com MedidorCiclo já existente ─────────────────────────────

@dataclass
class MedidorCiclo:
    """Acumula tempos por etapa de um ciclo de comando (API anterior)."""

    _inicios: Dict[str, float] = field(default_factory=dict)
    tempos: Dict[str, float] = field(default_factory=dict)

    def iniciar(self, etapa_nome: str) -> None:
        self._inicios[etapa_nome] = time.perf_counter()

    def parar(self, etapa_nome: str) -> float:
        inicio = self._inicios.pop(etapa_nome, None)
        if inicio is None:
            return 0.0
        duracao = time.perf_counter() - inicio
        self.tempos[etapa_nome] = self.tempos.get(etapa_nome, 0.0) + duracao
        return duracao

    def registrar(self, etapa_nome: str, duracao: float) -> None:
        if duracao < 0:
            return
        self.tempos[etapa_nome] = self.tempos.get(etapa_nome, 0.0) + duracao

    def total(self) -> float:
        return sum(self.tempos.values())

    def relatorio(self, titulo: str = "Métricas do ciclo") -> str:
        rotulos = {
            "captura": "Captura",
            "google": "Google Speech",
            "ollama": "Ollama",
            "json": "JSON",
            "execucao": "Execução",
            "tts": "TTS",
        }
        ordem = ("captura", "google", "ollama", "json", "execucao", "tts")
        linhas = [titulo, ""]
        for chave in ordem:
            if chave in self.tempos:
                nome = rotulos.get(chave, chave)
                linhas.append(f"{nome:.<18}{self.tempos[chave]:.2f} s")
        linhas.append("")
        linhas.append(f"{'TOTAL':.<18}{self.total():.2f} s")
        return "\n".join(linhas)

    def imprimir(self, titulo: str = "Métricas do ciclo") -> None:
        print(self.relatorio(titulo))


class Cronometro:
    """Context manager simples para medir um bloco de código."""

    def __init__(self, medidor: MedidorCiclo, etapa_nome: str) -> None:
        self._medidor = medidor
        self._etapa = etapa_nome
        self.duracao: float = 0.0

    def __enter__(self) -> "Cronometro":
        self._medidor.iniciar(self._etapa)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.duracao = self._medidor.parar(self._etapa)


def medir(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator que retorna (resultado, duracao_em_segundos)."""

    def wrapper(*args: Any, **kwargs: Any) -> Tuple[Any, float]:
        inicio = time.perf_counter()
        resultado = func(*args, **kwargs)
        return resultado, time.perf_counter() - inicio

    return wrapper
