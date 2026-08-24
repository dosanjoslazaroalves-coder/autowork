"""
Teste completo do normalizador.py — linguagem natural.
Execute com: python _test_normalizador.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sistema_toke.normalizador import normalizar
from sistema_toke.parser import parse

print("=" * 50)
print("TESTE DO NORMALIZADOR - LINGUAGEM NATURAL")
print("=" * 50)

testes = [
    ("Abra o Chrome", "abrir chrome", "abrir_app"),
    ("abra o chrome", "abrir chrome", "abrir_app"),
    ("abrir chrome", "abrir chrome", "abrir_app"),
    ("Por favor abra o Chrome", "abrir chrome", "abrir_app"),
    ("Voce consegue abrir o Chrome?", "abrir chrome", "abrir_app"),
    ("Gostaria de iniciar o Spotify.", "abrir spotify", "abrir_app"),
    ("Por favor execute o Visual Studio Code.", "abrir visual studio code", "abrir_app"),
    ("Preciso abrir a calculadora.", "abrir calculadora", "abrir_app"),
    ("Abra o navegador para mim.", "abrir navegador", "abrir_app"),
    ("Pode abrir meu navegador?", "abrir navegador", "abrir_app"),
    ("Abra o explorador de arquivos.", "abrir explorador arquivos", "abrir_app"),
    ("executar spotify", "abrir spotify", "abrir_app"),
    ("inicie o vscode", "abrir vscode", "abrir_app"),
    ("rode chrome", "abrir chrome", "abrir_app"),
    ("Qual e a hora?", "hora", "informar_hora"),
    ("Que horas sao?", "horas", "informar_hora"),
    ("Qual a data de hoje?", "data", "informar_data"),
    ("Que dia e hoje?", "dia", "informar_data"),
    ("qual o sentido da vida", "sentido vida", None),
    ("", None, None),
]

passou = 0
falhou = 0

for entrada, esperado_norm, esperado_acao in testes:
    resultado_norm = normalizar(entrada)
    resultado_parse = parse(entrada)
    acao_obtida = resultado_parse["acao"] if resultado_parse else None

    norm_ok = resultado_norm == esperado_norm
    parse_ok = acao_obtida == esperado_acao

    if norm_ok:
        passou += 1
    else:
        falhou += 1
        print("  [NORM] Entrada=%r esperado=%r obtido=%r" % (entrada, esperado_norm, resultado_norm))

    if parse_ok:
        passou += 1
    else:
        falhou += 1
        print("  [PARSE] Entrada=%r esperado=%r obtido=%r" % (entrada, esperado_acao, acao_obtida))

print()
print("=" * 50)
print("RESULTADO: %d passaram, %d falharam" % (passou, falhou))
print("=" * 50)

if falhou == 0:
    print("TODOS OS TESTES PASSARAM!")
else:
    print("ALGUNS TESTES FALHARAM!")
    sys.exit(1)
