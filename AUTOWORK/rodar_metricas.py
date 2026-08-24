"""
Executor de testes de métricas do AUTOWORK.

Não altera a arquitetura do assistente. Roda o pipeline real (normalizador,
parser, executor) sob medições. O interpretador só é medido se --interpretador
for passado: ele existe no repositório, mas não está no fluxo de fala.py.

Modos:
    python rodar_metricas.py --modo normal
    python rodar_metricas.py --modo memoria
    python rodar_metricas.py --modo cpu
    python rodar_metricas.py --modo cprofile
    python rodar_metricas.py --modo completo

O modo normal NÃO liga tracemalloc nem cProfile (overhead menor).
"""

from __future__ import annotations

import argparse
import cProfile
import importlib
import io
import pstats
import sys
import timeit
from typing import Any, Dict, List, Optional

import metricas as m


def _setup_mocks() -> None:
    from sistema_toke.executor import REGISTRO_ACOES, registrar

    REGISTRO_ACOES.clear()

    def _noop(*_a: Any, **_k: Any) -> None:
        return None

    for nome in (
        "fechar_janela",
        "alternar_janelas",
        "mostrar_area_de_trabalho",
        "maximizar_janela",
        "restaurar_ou_minimizar_janela",
        "encaixar_janela_esquerda",
        "encaixar_janela_direita",
        "abrir_visao_de_tarefas",
        "bloquear_tela",
        "informar_hora",
        "informar_data",
        "nova_aba",
        "fechar_aba",
        "reabrir_aba",
        "proxima_aba",
        "aba_anterior",
        "atualizar_pagina",
        "atualizacao_forcada",
        "barra_endereco",
        "voltar_pagina",
        "avancar_pagina",
        "pagina_inicial",
        "historico",
        "downloads",
        "favoritos",
        "buscar_na_pagina",
        "janela_anonima",
        "nova_janela",
        "salvar_pagina",
        "imprimir_pagina",
        "zoom_mais",
        "zoom_menos",
        "zoom_padrao",
        "devtools",
        "inspecionar_elemento",
        "abrir_site",
    ):
        registrar(nome, _noop)

    registrar("abrir_app", lambda nome="": None)


def _medir_import_catalogo(ram: m.RegistroRAM, etapas: m.MedidorEtapas) -> Dict[str, Any]:
    """
    Importa catalogo.py e reconstrói mapas derivados para isolar custos.

    O import já executa _construir_mapa_token_acoes e _construir_mapa_sites.
    A reconstrução mede só as funções de mapa, não o parse do arquivo.
    """
    ram.capturar("antes_catalogo")
    etapas.iniciar("catalogo")
    catalogo = importlib.import_module("sistema_toke.catalogo")
    etapas.parar("catalogo")
    ram.capturar("após_catalogo")

    etapas.iniciar("mapas_derivados")
    _ = catalogo._construir_mapa_token_acoes()
    _ = catalogo._construir_mapa_sites()
    etapas.parar("mapas_derivados")
    ram.capturar("após_mapas")

    meta = {
        "n_acoes": len(getattr(catalogo, "CATALOGO_ACOES", {})),
        "n_sites": len(getattr(catalogo, "CATALOGO_SITES", {})),
        "n_mapa_apps": len(getattr(catalogo, "MAPA_APPS", {})),
        "n_mapa_verbos": len(getattr(catalogo, "MAPA_VERBOS", {})),
        "n_mapa_sites": len(getattr(catalogo, "MAPA_SITES", {})),
        "n_token_acoes": len(getattr(catalogo, "MAPA_TOKEN_PARA_ACOES", {})),
    }
    return meta


def _medir_imports_pipeline(ram: m.RegistroRAM, etapas: m.MedidorEtapas) -> None:
    etapas.iniciar("imports")
    importlib.import_module("sistema_toke.normalizador")
    importlib.import_module("sistema_toke.parser")
    importlib.import_module("sistema_toke.executor")
    etapas.parar("imports")
    ram.capturar("após_imports")


def _tentar_interpretador(texto: str) -> tuple[Optional[float], Optional[str]]:
    """Mede InterpretadorComplexo se Ollama responder. Não faz parte do pipeline vivo."""
    try:
        from interpretador import InterpretadorComplexo
    except Exception as exc:
        return None, f"interpretador.py não importou: {exc}"

    interp = InterpretadorComplexo("qwen2.5:3b", "http://localhost:11434/api/generate")
    t0 = m.agora_ns()
    try:
        resultado = interp.interpretar(texto)
    except Exception as exc:
        return None, f"interpretador levantou exceção: {exc}"
    dur = m.ns_para_s(m.agora_ns() - t0)
    if resultado is None:
        return dur, "interpretador retornou None (conexão/timeout?). Tempo inclui a falha."
    return dur, None


def _pipeline_comando(
    texto: str,
    etapas: m.MedidorEtapas,
    ram: m.RegistroRAM,
    executar_real: bool,
) -> Dict[str, Any]:
    from sistema_toke.normalizador import normalizar
    from sistema_toke.parser import parse
    from sistema_toke.executor import executar

    if not executar_real:
        _setup_mocks()

    ram.capturar("antes_comando")

    etapas.iniciar("normalizador")
    normalizado = normalizar(texto)
    etapas.parar("normalizador")

    etapas.iniciar("parser")
    comando = parse(texto)
    etapas.parar("parser")

    resultado_exec: Optional[dict] = None
    if comando is not None:
        etapas.iniciar("executor")
        resultado_exec = executar(comando["acao"], **comando.get("parametros", {}))
        etapas.parar("executor")

    etapas.iniciar("resposta")
    _ = {
        "texto": texto,
        "normalizado": normalizado,
        "comando": comando,
        "execucao": resultado_exec,
    }
    etapas.parar("resposta")
    ram.capturar("depois_comando")

    return {
        "normalizado": normalizado,
        "comando": comando,
        "execucao": resultado_exec,
    }


def _rodar_uma(
    texto: str,
    modo: str,
    executar_real: bool,
    incluir_interpretador: bool,
    ja_importou: bool,
) -> m.Relatorio:
    ram = m.RegistroRAM()
    etapas = m.MedidorEtapas()
    notas: List[str] = []
    meta: Dict[str, Any] = {}
    tm: Optional[m.SessaoTracemalloc] = None
    cpu_am: Optional[m.AmostradorCPU] = None

    if m.aviso_psutil():
        notas.append(m.aviso_psutil() or "")

    ram.capturar("inicial")
    etapas.iniciar_total()

    if modo in {"memoria", "completo"}:
        tm = m.SessaoTracemalloc()
        tm.iniciar()
        notas.append(
            "tracemalloc estava ligado nesta execução — há overhead de alocação; "
            "não compare estes tempos com o modo normal como se fossem iguais."
        )

    if modo in {"cpu", "completo"}:
        cpu_am = m.AmostradorCPU(intervalo=0.1)
        cpu_am.iniciar()
        notas.append(
            "Amostragem de CPU em thread (0,1 s). cpu_percent(interval>0) não foi "
            "usado para não bloquear o teste de velocidade."
        )

    etapas.iniciar("inicializacao")
    _ = sys.version
    etapas.parar("inicializacao")

    if not ja_importou:
        meta = _medir_import_catalogo(ram, etapas)
        _medir_imports_pipeline(ram, etapas)
        notas.append(
            "Contagem de entradas do catálogo (NÃO é métrica de desempenho): "
            + ", ".join(f"{k}={v}" for k, v in meta.items())
        )
        notas.append(
            "Tempo de 'catálogo' = import do módulo (parse + execução das literais + "
            "primeira construção dos mapas). 'Mapas derivados' = reconstrução isolada."
        )
    else:
        notas.append("Warm start: catálogo e pipeline já estavam importados nesta execução.")
        ram.capturar("após_catalogo")
        ram.capturar("após_mapas")
        ram.capturar("após_imports")

    notas.append(
        "parser.parse() chama normalizar() de novo; o tempo do parser inclui uma "
        "segunda normalização. O normalizador imprime debug no terminal (I/O)."
    )
    notas.append(
        "InterpretadorComplexo não está ligado em fala.py. Medição só ocorre com "
        "--interpretador."
    )

    _pipeline_comando(texto, etapas, ram, executar_real)

    if incluir_interpretador:
        dur, aviso = _tentar_interpretador(texto)
        if dur is not None:
            etapas.registrar("interpretador", dur)
        if aviso:
            notas.append(aviso)
        else:
            notas.append("Interpretador medido via HTTP Ollama (latência de rede/modelo).")

    etapas.parar_total()
    ram.capturar("final")

    cpu: Dict[str, Optional[float]] = {}
    if cpu_am is not None:
        cpu_am.parar()
        cpu = cpu_am.resumo()

    tm_resumo = tm.parar_e_resumo() if tm is not None else None

    return m.Relatorio(
        tempos=dict(etapas.tempos_s),
        total_s=etapas.total_s(),
        ram=ram,
        cpu=cpu,
        tracemalloc=tm_resumo,
        notas=notas,
        metadados=meta,
    )


def _relatorio_cprofile(texto: str, executar_real: bool, sort: str = "tottime") -> str:
    profiler = cProfile.Profile()

    def _alvo() -> None:
        ram = m.RegistroRAM()
        etapas = m.MedidorEtapas()
        _pipeline_comando(texto, etapas, ram, executar_real)

    # Garante imports fora do profile pesado de bootstrap, se já carregados.
    importlib.import_module("sistema_toke.catalogo")
    importlib.import_module("sistema_toke.normalizador")
    importlib.import_module("sistema_toke.parser")
    importlib.import_module("sistema_toke.executor")

    profiler.enable()
    _alvo()
    profiler.disable()

    buf = io.StringIO()
    stats = pstats.Stats(profiler, stream=buf)
    stats.strip_dirs()
    buf.write("\n--- Ordenado por tottime (tempo interno da função) ---\n")
    stats.sort_stats("tottime").print_stats(25)
    buf.write("\n--- Ordenado por cumtime (tempo total incluindo callees) ---\n")
    stats.sort_stats("cumtime").print_stats(25)
    buf.write(
        "\nNota: ncalls alto não prova gargalo. Compare tottime e cumtime "
        "e, se possível, tottime/ncalls.\n"
    )
    return buf.getvalue()


def _micro_timeit(texto: str, n: int) -> str:
    importlib.import_module("sistema_toke.catalogo")
    setup = (
        "from sistema_toke.normalizador import normalizar\n"
        "from sistema_toke.parser import parse\n"
        f"texto = {texto!r}\n"
    )
    t_norm = timeit.timeit("normalizar(texto)", setup=setup, number=n)
    t_parse = timeit.timeit("parse(texto)", setup=setup, number=n)
    return (
        f"timeit ({n} voltas, após warm import):\n"
        f"  normalizar médio: {t_norm / n * 1000:.4f} ms\n"
        f"  parse médio:      {t_parse / n * 1000:.4f} ms\n"
        "  timeit mede só o corpo; não inclui RSS/CPU. Útil para micro-etapas, "
        "não para o ciclo completo com I/O."
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Métricas e profiling do AUTOWORK")
    p.add_argument(
        "--modo",
        choices=("normal", "memoria", "cpu", "cprofile", "completo"),
        default="normal",
        help="Tipo de teste. normal = leve (sem tracemalloc/cProfile).",
    )
    p.add_argument("--texto", default="abra o chrome", help="Comando de teste")
    p.add_argument("--repeticoes", type=int, default=1, help="Repetições na mesma VM (warm)")
    p.add_argument(
        "--executar-real",
        action="store_true",
        help="Usa o executor real (abre apps). Padrão: mocks.",
    )
    p.add_argument(
        "--interpretador",
        action="store_true",
        help="Tenta medir interpretador.py (Ollama). Fora do pipeline de fala.py.",
    )
    p.add_argument(
        "--timeit",
        type=int,
        default=0,
        metavar="N",
        help="Microbenchmark timeit com N voltas (após warm import).",
    )
    p.add_argument(
        "--falar",
        action="store_true",
        help="Narra o diagnóstico via fala.py/TTS (não mistura TTS no tempo do comando).",
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    print(f"Python {sys.version.split()[0]} | modo={args.modo} | texto={args.texto!r}")
    print("RAM do processo = RSS (psutil). Alocações Python = tracemalloc (modos memoria/completo).")
    print()

    if args.modo == "cprofile":
        # Warm import + profile só do pipeline de comando (prioridade: velocidade).
        rel_base = _rodar_uma(
            args.texto,
            modo="normal",
            executar_real=args.executar_real,
            incluir_interpretador=args.interpretador,
            ja_importou=False,
        )
        print(rel_base.texto_terminal())
        print()
        print(_relatorio_cprofile(args.texto, args.executar_real))
        if args.falar:
            _falar_diagnostico(rel_base)
        return 0

    relatorios: List[m.Relatorio] = []
    for i in range(max(1, args.repeticoes)):
        ja = i > 0 or "catalogo" in sys.modules
        if i == 0:
            ja = False
        rel = _rodar_uma(
            args.texto,
            modo=args.modo,
            executar_real=args.executar_real,
            incluir_interpretador=args.interpretador,
            ja_importou=ja,
        )
        etiqueta = "cold start (import nesta VM)" if i == 0 else f"warm start #{i + 1}"
        print(f"----- Execução {i + 1} ({etiqueta}) -----")
        print(rel.texto_terminal())
        print()
        relatorios.append(rel)

    if len(relatorios) >= 2:
        resumo = m.comparar_totais(relatorios)
        if resumo:
            print(m.texto_comparacao(resumo, "COMPARAÇÃO (1=cold, demais=warm)"))

    if args.timeit > 0:
        print()
        print(_micro_timeit(args.texto, args.timeit))

    if args.falar and relatorios:
        _falar_diagnostico(relatorios[-1])

    return 0


def _falar_diagnostico(relatorio: m.Relatorio) -> None:
    """fala.py só pronuncia; a coleta já terminou."""
    texto = m.texto_para_fala(relatorio)
    print()
    print("Texto enviado à fala:")
    print(f"  {texto}")
    try:
        from modules.voz_teste import falar

        falar(texto)
    except Exception as exc:
        print(f"(TTS indisponível: {exc})")


if __name__ == "__main__":
    raise SystemExit(main())
