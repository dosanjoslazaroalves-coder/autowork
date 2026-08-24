"""
Teste de integração do pipeline completo AUTOWORK.

Valida o fluxo sem microfone nem PyAutoGUI (simulado).

Pipeline testado:
    texto → normalizador → parser → executor
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sistema_toke.normalizador import normalizar
from sistema_toke.parser import parse
from sistema_toke.executor import REGISTRO_ACOES, executar, registrar


def _mock_fechar_janela() -> None:
    print("    [MOCK] ALT + F4 enviado!")


def _mock_abrir_app(nome: str) -> None:
    print(f"    [MOCK] Abrindo {nome}...")


def _setup_mocks() -> None:
    """Registra funções mock para o teste (sem PyAutoGUI)."""
    # Limpa registros anteriores
    REGISTRO_ACOES.clear()

    registrar("fechar_janela", _mock_fechar_janela)
    registrar("alternar_janelas", lambda: print("    [MOCK] ALT + TAB enviado!"))
    registrar("mostrar_area_de_trabalho", lambda: print("    [MOCK] WIN + D enviado!"))
    registrar("maximizar_janela", lambda: print("    [MOCK] WIN + UP enviado!"))
    registrar("restaurar_ou_minimizar_janela", lambda: print("    [MOCK] WIN + DOWN enviado!"))
    registrar("encaixar_janela_esquerda", lambda: print("    [MOCK] WIN + LEFT enviado!"))
    registrar("encaixar_janela_direita", lambda: print("    [MOCK] WIN + RIGHT enviado!"))
    registrar("abrir_visao_de_tarefas", lambda: print("    [MOCK] WIN + TAB enviado!"))
    registrar("bloquear_tela", lambda: print("    [MOCK] WIN + L enviado!"))
    registrar("abrir_app", _mock_abrir_app)

    # ── Ações informativas ──
    registrar("informar_hora", lambda: print("    [MOCK] Hora informada!"))
    registrar("informar_data", lambda: print("    [MOCK] Data informada!"))

    # ── Atalhos do navegador (mocks) ──
    registrar("nova_aba", lambda: print("    [MOCK] CTRL + T (nova aba)!"))
    registrar("fechar_aba", lambda: print("    [MOCK] CTRL + W (fechar aba)!"))
    registrar("reabrir_aba", lambda: print("    [MOCK] CTRL + SHIFT + T (reabrir aba)!"))
    registrar("proxima_aba", lambda: print("    [MOCK] CTRL + TAB (próxima aba)!"))
    registrar("aba_anterior", lambda: print("    [MOCK] CTRL + SHIFT + TAB (aba anterior)!"))
    registrar("atualizar_pagina", lambda: print("    [MOCK] F5 (atualizar página)!"))
    registrar("atualizacao_forcada", lambda: print("    [MOCK] CTRL + F5 (atualização forçada)!"))
    registrar("barra_endereco", lambda: print("    [MOCK] CTRL + L (barra de endereço)!"))
    registrar("voltar_pagina", lambda: print("    [MOCK] ALT + LEFT (voltar página)!"))
    registrar("avancar_pagina", lambda: print("    [MOCK] ALT + RIGHT (avançar página)!"))
    registrar("pagina_inicial", lambda: print("    [MOCK] ALT + HOME (página inicial)!"))
    registrar("historico", lambda: print("    [MOCK] CTRL + H (histórico)!"))
    registrar("downloads", lambda: print("    [MOCK] CTRL + J (downloads)!"))
    registrar("favoritos", lambda: print("    [MOCK] CTRL + D (favoritos)!"))
    registrar("buscar_na_pagina", lambda: print("    [MOCK] CTRL + F (buscar)!"))
    registrar("janela_anonima", lambda: print("    [MOCK] CTRL + SHIFT + N (janela anônima)!"))
    registrar("nova_janela", lambda: print("    [MOCK] CTRL + N (nova janela)!"))
    registrar("salvar_pagina", lambda: print("    [MOCK] CTRL + S (salvar página)!"))
    registrar("imprimir_pagina", lambda: print("    [MOCK] CTRL + P (imprimir)!"))
    registrar("zoom_mais", lambda: print("    [MOCK] CTRL + '+' (zoom+)!"))
    registrar("zoom_menos", lambda: print("    [MOCK] CTRL + '-' (zoom-)!"))
    registrar("zoom_padrao", lambda: print("    [MOCK] CTRL + '0' (zoom padrão)!"))
    registrar("devtools", lambda: print("    [MOCK] F12 (DevTools)!"))
    registrar("inspecionar_elemento", lambda: print("    [MOCK] CTRL + SHIFT + C (inspecionar)!"))


def _testar_pipeline(
    descricao: str,
    texto_fala: str,
    acao_esperada: str | None,
) -> None:
    """Testa o pipeline completo e exibe resultado."""
    # 1. Normalizador
    normalizado = normalizar(texto_fala)

    # 2. Parser
    comando = parse(texto_fala)

    print(f"Teste: {descricao}")
    print(f"  Texto:          {texto_fala}")
    print(f"  Normalizado:    {normalizado}")

    if comando is None:
        print(f"  Ação:           None (não reconhecido)")
        if acao_esperada is not None:
            print(f"  [FALHOU] esperava acao '{acao_esperada}'")
        else:
            print(f"  [OK] nao reconhecido conforme esperado")
        print()
        return

    acao = comando["acao"]
    print(f"  Ação:           {acao}")

    if acao != acao_esperada:
        print(f"  [FALHOU] esperava '{acao_esperada}', obteve '{acao}'")
        print()
        return

    # 3. Executor - passa ação e parâmetros separadamente
    acao_comando = comando["acao"]
    params_comando = comando.get("parametros", {})
    resultado = executar(acao_comando, **params_comando)
    status = resultado["status"]

    if status == "sucesso":
        print(f"  [OK] pipeline completo funcionou")
    else:
        print(f"  [FALHOU] executor retornou {status}")

    print()


def main() -> None:
    print("=" * 55)
    print("  TESTE DE INTEGRAÇÃO - PIPELINE AUTOWORK")
    print("=" * 55)
    print()

    # Configura mocks
    _setup_mocks()

    # ── Testes de janela ──
    _testar_pipeline(
        "Fechar janela",
        "fecha a janela",
        "fechar_janela",
    )
    _testar_pipeline(
        "Fechar janela (variação)",
        "encerre essa janela por favor",
        "fechar_janela",
    )
    _testar_pipeline(
        "Alternar janelas",
        "alterna as janelas",
        "alternar_janelas",
    )
    _testar_pipeline(
        "Mostrar área de trabalho",
        "mostre a area de trabalho",
        "mostrar_area_de_trabalho",
    )
    _testar_pipeline(
        "Maximizar janela",
        "maximiza a janela",
        "maximizar_janela",
    )
    _testar_pipeline(
        "Bloquear tela",
        "bloqueia a tela",
        "bloquear_tela",
    )

    # ── Testes de app ──
    _testar_pipeline(
        "Abrir Chrome",
        "abra o chrome",
        "abrir_app",
    )
    _testar_pipeline(
        "Abrir Spotify",
        "abre o spotify",
        "abrir_app",
    )

    # ── Testes informativos ──
    _testar_pipeline(
        "Informar hora",
        "qual e a hora",
        "informar_hora",
    )
    _testar_pipeline(
        "Informar data",
        "qual a data de hoje",
        "informar_data",
    )

    # ── Testes do navegador (AtalhoNav) ──
    _testar_pipeline(
        "Nova aba",
        "abra uma nova aba",
        "nova_aba",
    )
    _testar_pipeline(
        "Nova aba (variação)",
        "nova guia",
        "nova_aba",
    )
    _testar_pipeline(
        "Fechar aba",
        "feche a aba",
        "fechar_aba",
    )
    _testar_pipeline(
        "Reabrir aba",
        "reabra a ultima aba",
        "reabrir_aba",
    )
    _testar_pipeline(
        "Próxima aba",
        "proxima aba",
        "proxima_aba",
    )
    _testar_pipeline(
        "Aba anterior",
        "aba anterior",
        "aba_anterior",
    )
    _testar_pipeline(
        "Atualizar página",
        "atualize a pagina",
        "atualizar_pagina",
    )
    _testar_pipeline(
        "Atualização forçada",
        "forcar atualizacao",
        "atualizacao_forcada",
    )
    _testar_pipeline(
        "Barra de endereço",
        "barra de endereco",
        "barra_endereco",
    )
    _testar_pipeline(
        "Voltar página",
        "volte a pagina",
        "voltar_pagina",
    )
    _testar_pipeline(
        "Avançar página",
        "avance a pagina",
        "avancar_pagina",
    )
    _testar_pipeline(
        "Página inicial",
        "pagina inicial",
        "pagina_inicial",
    )
    _testar_pipeline(
        "Histórico",
        "historico",
        "historico",
    )
    _testar_pipeline(
        "Downloads",
        "downloads",
        "downloads",
    )
    _testar_pipeline(
        "Favoritos",
        "favoritos",
        "favoritos",
    )
    _testar_pipeline(
        "Buscar na página",
        "busque na pagina",
        "buscar_na_pagina",
    )
    _testar_pipeline(
        "Janela anônima",
        "janela anonima",
        "janela_anonima",
    )
    _testar_pipeline(
        "Nova janela",
        "nova janela",
        "nova_janela",
    )
    _testar_pipeline(
        "Salvar página",
        "salve a pagina",
        "salvar_pagina",
    )
    _testar_pipeline(
        "Imprimir página",
        "imprima a pagina",
        "imprimir_pagina",
    )
    _testar_pipeline(
        "Zoom mais",
        "aumente o zoom",
        "zoom_mais",
    )
    _testar_pipeline(
        "Zoom menos",
        "diminua o zoom",
        "zoom_menos",
    )
    _testar_pipeline(
        "Zoom padrão",
        "zoom padrao",
        "zoom_padrao",
    )
    _testar_pipeline(
        "DevTools",
        "abra o devtools",
        "devtools",
    )
    _testar_pipeline(
        "Inspecionar elemento",
        "inspecione o elemento",
        "inspecionar_elemento",
    )

    # ── Teste não reconhecido ──
    _testar_pipeline(
        "Comando não reconhecido",
        "qual o sentido da vida",
        None,
    )

    print("=" * 55)
    print("  TESTE CONCLUÍDO")
    print("=" * 55)


if __name__ == "__main__":
    main()

