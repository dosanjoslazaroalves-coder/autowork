# Guia de desenvolvimento

## Antes de modificar

- Use `app.py` como entrada principal do sistema.
- Considere `core/orquestrador.py` a fonte do fluxo de voz real.
- Nao altere catalogos, parser e resolvedor sem rodar testes de interpretacao e fluxo.
- Acoes locais reais usam `pyautogui`; em testes, substitua por mocks/stubs para nao abrir janelas.
- APIs externas podem falhar; preserve retornos estruturados com `sucesso`, `status`, `mensagem`, `erro` e `dados`.

## Onde adicionar funcionalidades

### Novo app para abrir

Adicione sinonimos em `sistema_toke/catalogo/catalogo_app.py`, no dict `MAPA_APPS`. O valor deve ser o nome digitado no menu iniciar pelo `pyautogui`.

### Novo site

Adicione entrada em `sistema_toke/catalogo/catalogo_site.py`, usando `SiteInfo(nome, url, sinonimos, categoria)`. `resolvedor.py` compara alvo com `site.nome` e `site.sinonimos`.

### Novo atalho local

1. Adicione entrada em `sistema_toke/catalogo/catalogo_atalho.py`.
2. Implemente metodo em `comd_rapidos/atalhos.py` ou `comd_rapidos/atalho_nav.py`.
3. Registre o metodo em `registrar_no_executor()`.
4. Confirme se `sistema_toke/parser.py` consegue mapear sinonimos para a nova acao.
5. Adicione teste em `tests/test_interpretador.py` e/ou `_test_integracao.py`.

### Nova consulta informativa

1. Crie ou edite modulo em `modules/`.
2. Faca a funcao retornar dict com `sucesso`, `acao`, `dados`, `mensagem` e `erro`.
3. Adicione regra em `interpretador.interpretar()` para produzir `acao` e `parametros`.
4. Registre a funcao no dict `funcoes` em `dispatcher.dispatch()`.
5. Adicione testes de interpretador e dispatcher.

### Conversa ou apresentacao

- Conversa fica em `conversa/chatbot.py` e usa OpenRouter.
- Apresentacao fica em `apresent.py` e usa Ollama local.
- `dispatcher.py` cria ambos sob demanda; evite inicializar clientes externos no import do modulo.

## Sistema de comandos

O caminho de comandos locais e:

```text
texto -> interpretador.interpretar -> parser.parse -> resolvedor.resolver -> executor.executar -> comd_rapidos
```

`normalizador.normalizar()` remove pontuacao, aplica verbos canonicos e palavras descartaveis. `parser.parse()` trata comandos fixos e tenta criar uma intencao. `resolvedor.resolver()` transforma essa intencao em acao executavel com parametros. `executor.executar()` busca a funcao em `REGISTRO_ACOES`.

## Politica de fala

No fluxo principal, `Orquestrador._deve_falar()` evita falar confirmacoes de comando de sucesso quando `falar=False`. Resultados informativos e erros podem ser falados. O modulo `fala.py` de compatibilidade fala qualquer resultado com `mensagem`, entao nao use seu comportamento como unica referencia para o app principal.

## Como executar

```powershell
python app.py
python app.py --terminal
python app.py --texto "que horas sao em londres"
python teste_chat.py
python modules/voz_teste/teste_voz.py
python teste_viso.py
```

## Como executar testes

```powershell
python -m pytest
python _test_normalizador.py
python _test_integracao.py
```

Para evitar acoes reais, prefira testes com mocks. Nao rode comandos com `--executar-real` em `rodar_metricas.py` sem confirmar o efeito local.

## Configuracao segura

- Guarde `OPENROUTER_API_KEY` ou `CHAVE_API_CHAT` em `.env` ou variavel de ambiente.
- Nao versione `.env`, WAVs de saida ou caches.
- Se mudar eSpeak/Kokoro, atualize `modules/voz_teste/config.py` e `modules/voz_teste/README.md`.

## Pontos de atencao

- `setup_dados.py` tem caminho absoluto hardcoded; ajuste antes de usar em outra maquina.
- `rodar_metricas.py` aparenta esperar simbolos antigos em `sistema_toke.catalogo`; revise antes de confiar nos modos de metricas.
- `teste_viso.py` baixa modelo se ausente e depende de camera, OpenCV e MediaPipe.
- `estatisticas.py` esta vazio.
- `configui.py` e `personalidade.py` nao aparecem conectados ao caminho principal.
- Muitos modulos fazem imports tardios para reduzir custo ou evitar dependencias ate o uso; preserve esse padrao quando integrar servicos pesados.
