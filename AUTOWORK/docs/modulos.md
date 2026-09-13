# Modulos Python

Esta pagina documenta todos os arquivos `.py` encontrados fora de `.venv`, `__pycache__` e `.pytest_cache`.

## Raiz

### `_test_integracao.py`

**Responsabilidade:** script manual de integracao para o pipeline `texto -> normalizador -> parser -> resolvedor -> executor`, usando mocks para evitar PyAutoGUI.

**Dependencias:** `sys`, `os`, `sistema_toke.normalizador`, `sistema_toke.parser`, `sistema_toke.executor`.

**Funcoes:** `_mock_fechar_janela()` e `_mock_abrir_app(nome)` simulam acoes; `_setup_mocks()` limpa `REGISTRO_ACOES` e registra stubs; `_testar_pipeline(descricao, texto_fala, acao_esperada)` executa as etapas e imprime diagnostico; `main()` roda uma lista de casos.

**Fluxo:** executavel direto por `python _test_integracao.py`; nao e importado pelo app.

### `_test_normalizador.py`

**Responsabilidade:** script manual que valida pares de entrada, texto normalizado e acao parseada.

**Dependencias:** `sys`, `os`, `sistema_toke.normalizador.normalizar`, `sistema_toke.parser.parse`.

**Fluxo:** executa no top-level, imprime contagem de sucesso/falha e sai com codigo 1 se houver falha.

### `app.py`

**Responsabilidade:** ponto de entrada principal do AUTOWORK; configura CLI, logging, servicos, orquestrador e HUD.

**Dependencias:** `argparse`, `logging`, `sys`, `typing`, `core.estados.Estado`, e imports tardios de `audio`, `core`, `interface` e `audio.tts`.

**Classes:** `PonteInterface` adapta eventos do orquestrador para a HUD, traduz estados e normaliza RMS; `_InterfaceNula` implementa metodos vazios para modos sem HUD.

**Funcoes:** `_configurar_logging(debug)`, `_construir_orquestrador(ouvinte)`, `_executar_texto_unico(texto)`, `_executar_com_interface(orquestrador, ponte)`, `_analisar_argumentos(argv)`, `main(argv)`.

**Fluxo:** e chamado por `if __name__ == "__main__"`; tambem e reexportado por `fala.py`.

### `apresent.py`

**Responsabilidade:** gerar resposta de apresentacao do AUTOWORK usando Ollama local.

**Dependencias:** `requests`.

**Classes:** `Apresentador` guarda `modelo` e `url`; `apresentar(texto)` envia prompt para `/api/generate` e retorna o campo `response` limpo.

**Entrada/saida:** recebe texto do usuario; retorna string ou `None` em erro.

### `configui.py`

**Responsabilidade:** configuracao de voz legada ou nao integrada ao fluxo atual.

**Dependencias:** `typing`.

**Classes:** `VoiceProfileConfig` e um `TypedDict` com `voice_name`, `rate`, `pitch` e `volume`.

**Funcoes:** `get_active_voice_config()` retorna o perfil ativo; `resolve_voice_settings()` aplica overrides `VOICE_NAME`, `VOICE_RATE`, `VOICE_PITCH` e `VOICE_VOLUME`.

**Observacoes:** `audio.tts` nao importa este arquivo no codigo atual; a integracao com motor `edge`/`piper` nao aparece implementada aqui.

### `dispatcher.py`

**Responsabilidade:** rotear intencoes informativas, de apresentacao e conversa.

**Dependencias:** `typing`, `modules.clima`, `modules.localizacao`, `modules.tempo`; imports tardios de `apresent` e `conversa.chatbot`.

**Funcoes:** `_obter_apresentador()` e `_obter_chatbot()` fazem lazy singleton; `_apresentar(texto_original)` chama Ollama via `Apresentador`; `_conversar(mensagem)` chama OpenRouter via `Chatbot`; `dispatch(comando)` chama a funcao adequada por `acao`.

**Fluxo:** usado por `core.orquestrador.Orquestrador.processar_comando()` quando a intencao nao e `tipo="comando"` nem `tipo="desconhecido"`.

### `estatisticas.py`

**Responsabilidade:** arquivo vazio. Nenhuma classe, funcao ou constante foi encontrada.

**Observacoes:** funcionalidade indeterminada pelo codigo.

### `fala.py`

**Responsabilidade:** modulo de compatibilidade que reexporta `app.main` e oferece `processar_comando(texto)`.

**Dependencias:** `app.main`, `core.orquestrador`, `audio.captura`, `audio.reconhecimento`, `audio.tts`.

**Funcoes:** `processar_comando(texto)` cria captura/STT/orquestrador temporarios, processa texto e chama TTS se houver mensagem.

**Observacoes:** por chamar `ServicoCaptura()`, cria `Recognizer`, mas nao calibra microfone antes de processar texto. A politica de fala aqui e diferente da politica de `Orquestrador._deve_falar`, pois fala qualquer resultado com `mensagem`.

### `interpretador.py`

**Responsabilidade:** classificar texto em comandos locais, clima, hora/data, localizacao, apresentacao, conversa ou desconhecido.

**Dependencias:** `json`, `re`, `typing`, `requests` opcional, `sistema_toke.catalogo.catalogo_verbo`, `sistema_toke.normalizador`, `sistema_toke.parser`, `sistema_toke.resolvedor`.

**Classes:** `InterpretadorComplexo` monta prompt e chama Ollama; apesar do nome, nao e o caminho principal do app.

**Funcoes:** `interpretar(texto)` aplica regras deterministicas e retorna dict de intencao; `_extrair_local(frase)` busca local depois de `em/no/na`; `_intencao(...)` cria estrutura padrao.

**Fluxo:** chamado diretamente pelo orquestrador. Para comandos, exige que a frase comece com verbo ou seja comando fixo, evitando tratar perguntas sobre comandos como execucao.

### `metricas.py`

**Responsabilidade:** camada de observabilidade, formatacao de relatorios, medicao de RAM/CPU/tempo e compatibilidade com medidores antigos.

**Dependencias:** `os`, `statistics`, `threading`, `time`, `tracemalloc`, `dataclasses`, `typing`, `psutil` opcional.

**Classes principais:** `ObservadorProcesso`, `AmostradorCPU`, `SnapshotRAM`, `RegistroRAM`, `MedidorEtapas`, `etapa`, `ResumoTracemalloc`, `SessaoTracemalloc`, `Relatorio`, `ResumoComparacao`, `CicloComando`, `PainelMemoria`, `MedidorCiclo`, `Cronometro`.

**Funcoes:** ativadores por env (`profiling_ativo`, etc.), formatadores, `classificar_gargalo`, `texto_para_fala`, comparacao de relatorios, ciclo global e decorator `medir`.

### `personalidade.py`

**Responsabilidade:** reescrever frases curtas para um tom mais formal/premium.

**Dependencias:** `re`, `typing`.

**Funcoes:** `estilizar_fala(texto)` normaliza espacos, trata frases exatas e aplica padroes regex; prosa longa com mais de 12 palavras e preservada.

**Observacoes:** nao foi encontrado import deste modulo no fluxo principal atual.

### `rodar_metricas.py`

**Responsabilidade:** CLI para medir tempo, memoria, CPU e cProfile do pipeline de comandos.

**Dependencias:** `argparse`, `cProfile`, `importlib`, `io`, `pstats`, `sys`, `timeit`, `metricas`.

**Funcoes:** `_setup_mocks()`, `_medir_import_catalogo()`, `_medir_imports_pipeline()`, `_tentar_interpretador()`, `_pipeline_comando()`, `_rodar_uma()`, `_relatorio_cprofile()`, `_micro_timeit()`, `_parse_args()`, `main()`, `_falar_diagnostico()`.

**Fluxo:** executavel por `python rodar_metricas.py --modo normal` e variantes. Usa mocks por padrao; `--executar-real` permite executar acoes reais.

**Observacoes:** `_medir_import_catalogo()` chama `catalogo._construir_mapa_token_acoes()`, `catalogo._construir_mapa_sites()` e consulta `CATALOGO_ACOES`/`MAPA_SITES`, mas o `sistema_toke/catalogo/__init__.py` atual nao exporta esses nomes. Isso sugere codigo desatualizado ou incompleto nessa parte.

### `setup_dados.py`

**Responsabilidade:** baixar municipios do IBGE e gerar `modules/dados/municipios_brasil.json`.

**Dependencias:** `json`, `requests`, `os`, `unicodedata`.

**Funcoes:** `baixar_municipios()` chama API do IBGE, extrai nome/UF/timezone e grava JSON.

**Observacoes:** `DADOS_DIR` esta hardcoded para `c:\Users\Marco Antônio\Documents\Chat\AUTOWORK\modules\dados`, o que reduz portabilidade.

### `teste_chat.py`

**Responsabilidade:** REPL manual para conversar com `conversa.chatbot.Chatbot`.

**Dependencias:** `logging`, `sys`, `conversa.chatbot.Chatbot`.

**Funcoes:** `configurar_logs()`, `imprimir_cabecalho()`, `main()`.

**Fluxo:** aceita `/ajuda`, `/limpar` e `/sair`; demais entradas sao enviadas ao chatbot.

### `teste_interface.py`

**Responsabilidade:** demo Textual independente com mascote animado e entrada textual simulada.

**Dependencias:** `textual`, `datetime`, `random`.

**Classes:** `AutoWork(App)` monta tela, atualiza relogio, anima mascote e simula processamento ao submeter input.

**Observacoes:** nao chama `Orquestrador`, `interpretador` ou executor; e demonstracao/experimento de interface.

### `teste_viso.py`

**Responsabilidade:** app independente de visao computacional com camera, deteccao de maos, gesto de pinca e reconhecimento simples de formas desenhadas.

**Dependencias:** `cv2`, `mediapipe`, `math`, `time`, `os`, `urllib.request`, `numpy`.

**Funcoes:** `garantir_modelo()` baixa `hand_landmarker.task` se ausente; `distancia(a,b)` calcula distancia 3D; `detectar_pinca(landmarks)` compara polegar/indicador; `contar_dedos(landmarks)` estima dedos levantados; `desenhar_mao(frame, landmarks)` desenha landmarks; `reconhecer_forma(trajetoria)` classifica linha, triangulo, quadrado, retangulo, circulo ou forma; `desenhar_forma(frame,tipo,pontos)` renderiza forma; `main()` abre camera e loop OpenCV.

**Observacoes:** nao aparece integrado ao fluxo principal. `opencv-python` e `mediapipe` nao constam no `requirements.txt` principal.

## Pacote `audio`

### `audio/__init__.py`

**Responsabilidade:** marca o pacote de audio. Contem apenas docstring.

### `audio/captura.py`

**Responsabilidade:** capturar audio do microfone e calibrar o reconhecedor.

**Dependencias:** `logging`, `math`, `struct`, `time`, `typing`, `speech_recognition`.

**Classes:** `_StreamComNiveis` intercepta `read()` para medir RMS; `_FonteComNiveis` envolve `sr.AudioSource`; `_MedidorFala` registra inicio da fala; `ServicoCaptura` configura `sr.Recognizer`, inicializa microfone sob demanda, calibra ruido e captura audio.

**Funcoes:** `_rms(dados)` calcula RMS PCM 16-bit little-endian. `capturar()` e `capturar_com_niveis(callback)` retornam `sr.AudioData` ou `None` em timeout.

### `audio/reconhecimento.py`

**Responsabilidade:** transcrever `AudioData` para texto.

**Dependencias:** `logging`, `time`, `typing`, `speech_recognition`.

**Classes:** `ServicoReconhecimento` recebe um `Recognizer` e idioma; `transcrever(audio)` chama `recognize_google` e retorna texto em minusculas sem espacos externos, ou `None`.

### `audio/tts.py`

**Responsabilidade:** fachada TTS usada pelo app.

**Dependencias:** `logging`, `threading`, `time`, `typing`; imports tardios de `modules.voz_teste`, `numpy`, `sounddevice`.

**Funcoes:** `falar(texto)` delega para Kokoro e engole excecoes; `_envelope(audio,taxa_amostragem)` calcula niveis RMS normalizados; `falar_com_niveis(texto,on_nivel)` gera audio, reproduz com sounddevice e emite niveis.

### `audio/wake_word.py`

**Responsabilidade:** detectar wake word e devolver comando limpo.

**Constantes:** `WAKE_WORD="work"`; `_VARIANTES={"work", "auto-work", "auto"}`.

**Funcoes:** `detectar(texto)` retorna `(bool, comando_limpo)`.

## Pacote `comd_rapidos`

### `comd_rapidos/abrir_app.py`

**Responsabilidade:** abrir aplicativo via menu iniciar do Windows.

**Funcao:** `abrir_app(nome)` pressiona Win, digita o nome e pressiona Enter.

### `comd_rapidos/abrir_site.py`

**Responsabilidade:** abrir URL valida no navegador padrao.

**Funcao:** `abrir_site(url)` valida scheme/netloc, chama `webbrowser.open()` e levanta excecao em falha.

### `comd_rapidos/atalho_nav.py`

**Responsabilidade:** acoes de navegador por atalhos de teclado.

**Classes:** `AtalhoNav` registra metodos no executor e implementa atalhos de abas, pagina, historico, downloads, favoritos, busca, janelas, salvar/imprimir, zoom e DevTools.

**Metodos principais:** `registrar_no_executor`, `nova_aba`, `fechar_aba`, `reabrir_aba`, `proxima_aba`, `aba_anterior`, `atualizar_pagina`, `atualizacao_forcada`, `barra_endereco`, `voltar_pagina`, `avancar_pagina`, `pagina_inicial`, `historico`, `downloads`, `favoritos`, `buscar_na_pagina`, `janela_anonima`, `nova_janela`, `fechar_janela_nav`, `salvar_pagina`, `imprimir_pagina`, `zoom_mais`, `zoom_menos`, `zoom_padrao`, `devtools`, `inspecionar_elemento`.

### `comd_rapidos/atalhos.py`

**Responsabilidade:** acoes de janela e sistema operacional por atalhos Windows.

**Classes:** `Janela` registra e executa fechamento, alternancia, area de trabalho, maximizar/restaurar, mover esquerda/direita, visao de tarefas e bloqueio de tela.

## Pacote `conversa`

### `conversa/__init__.py`

**Responsabilidade:** exporta `Chatbot`.

### `conversa/chatbot.py`

**Responsabilidade:** cliente de conversa via OpenRouter.

**Dependencias:** `logging`, `os`, `pathlib`, `typing`, SDK `openai`, `conversa.prompt.SYSTEM_PROMPT`.

**Funcoes:** `_ler_arquivo_env(caminho)` carrega pares `NOME=valor`; `carregar_api_key()` procura chave em constante, variaveis `OPENROUTER_API_KEY`/`CHAVE_API_CHAT` e arquivos `.env`.

**Classes:** `Chatbot` cria cliente `OpenAI`, mantem historico com prompt de sistema, envia mensagens e trata erros especificos de API.

### `conversa/prompt.py`

**Responsabilidade:** define `SYSTEM_PROMPT` para o chatbot.

**Observacoes:** instrui respostas sem acentos, pontuacao, numeros, emojis ou Markdown.

## Pacote `core`

### `core/__init__.py`

**Responsabilidade:** marca o pacote `core` com docstring.

### `core/estados.py`

**Responsabilidade:** enum de estados do assistente.

**Classes:** `Estado` contem `INICIALIZANDO`, `IDLE`, `OUVINDO`, `TRANSCREVENDO`, `DETECTANDO_WAKE`, `PROCESSANDO`, `EXECUTANDO`, `FALANDO`, `SUCESSO`, `ERRO`, `ENCERRANDO`.

### `core/orquestrador.py`

**Responsabilidade:** coordenar o pipeline de voz completo.

**Classes:** `Orquestrador` registra comandos padrao, mantem estado, notifica ouvinte e processa ciclos.

**Metodos principais:** `inicializar()`, `executar_loop()`, `_ciclo()`, `processar_comando(texto)`, `parar()`, `_deve_falar(resultado)`.

**Fluxo:** centraliza transicoes de estado e decide quando falar respostas.

## Pacote `interface`

### `interface/__init__.py`

**Responsabilidade:** marca o pacote de interface com docstring.

### `interface/hud.py`

**Responsabilidade:** HUD Textual e fachada thread-safe.

**Dependencias:** `logging`, `threading`, `time`, `datetime`, `typing`, `rich.text.Text`, `textual`.

**Funcoes:** `mascote(olhos,simbolo)` e `_deque_zeros(tamanho)`.

**Classes:** `AppHUD(App)` monta layout, timers, mascote, log, modulos e visualizador; `HUD` recebe chamadas de qualquer thread e as repassa ao app Textual com throttling de audio.

### `interface/terminal.py`

**Responsabilidade:** imprimir banner, status e resultados no terminal.

**Funcoes:** `mostrar_banner()`, `mostrar_status(mensagem)`, `mostrar_resultado(texto, normalizado, comando, resultado_execucao=None)`.

## Pacote `modules`

### `modules/__init__.py`

**Responsabilidade:** docstring dizendo que os pacotes em `modules` sao experimentais/isolados.

### `modules/clima/__init__.py`

**Responsabilidade:** exporta `ClimaError` e `consultar_clima`.

### `modules/clima/clima.py`

**Responsabilidade:** consultar clima atual/previsao com Open-Meteo depois de resolver localidade.

**Classes:** `ClimaError` representa erro de clima.

**Funcoes:** `_get(url)` faz HTTP GET e valida JSON; `consultar_clima(local="Sao Paulo", data="hoje")` resolve local/data, limita previsao a 7 dias e retorna dados/mensagem.

### `modules/localizacao/__init__.py`

**Responsabilidade:** exporta `localizar_usuario`, `resolver_localidade` e `LocalizacaoError`.

### `modules/localizacao/localizacao.py`

**Responsabilidade:** resolver localidades e localizar usuario por IP.

**Classes:** `LocalizacaoError`.

**Funcoes:** `localizar_usuario(timeout)` chama ip-api.com; `carregar_json(caminho)` carrega bases; `normalizar_nome(nome)` remove acentos; `localizar_nominatim(local)` busca lat/lon; `resolver_localidade(local_str)` usa aliases, capitais, municipios brasileiros e Nominatim.

### `modules/tempo/__init__.py`

**Responsabilidade:** exporta funcoes de tempo/data.

### `modules/tempo/datas.py`

**Responsabilidade:** resolver expressoes temporais relativas.

**Funcao:** `resolver_data_relativa(expressao, timezone="America/Sao_Paulo", agora=None)` trata hoje, amanha, ontem, daqui a N dias, daqui a uma semana e proxima semana.

### `modules/tempo/tempo.py`

**Responsabilidade:** consultar data, horario, converter horario e calcular diferenca entre fusos.

**Funcoes:** `_resolver_tz(local)`, `consultar_data`, `consultar_horario`, `converter_horario`, `diferenca_horario`.

### `modules/voz_teste/__init__.py`

**Responsabilidade:** exporta API publica do TTS experimental: `TTSError`, `falar`, `gerar_audio`, `salvar_audio`.

### `modules/voz_teste/config.py`

**Responsabilidade:** constantes de configuracao do Kokoro/eSpeak.

**Constantes:** `ENGINE`, `MODEL_REPO`, `LANG_CODE`, `VOICE`, `SPEED`, `SAMPLE_RATE`, `VOZES_PT_BR`, caminhos `ESPEAK_*` e `OUTPUT_DIR`.

### `modules/voz_teste/teste_voz.py`

**Responsabilidade:** teste executavel manual do TTS experimental.

**Funcoes:** `_garantir_import()` adiciona raiz ao `sys.path`; `main()` carrega pipeline, gera e reproduz audio, retornando codigo 0/1.

### `modules/voz_teste/tts.py`

**Responsabilidade:** implementacao do TTS Kokoro PT-BR.

**Classes:** `TTSError` carrega etapa, causa, arquivo e correcao.

**Funcoes:** `_configure_warnings`, `_format_error`, `_configure_espeak_paths`, `_as_float32_array`, `_join_audio`, `_get_pipeline`, `_get_sounddevice`, `gerar_audio`, `salvar_audio`, `falar`.

## Pacote `sistema_toke`

### `sistema_toke/catalogo/__init__.py`

**Responsabilidade:** reexportar constantes e tipos dos catalogos.

### `sistema_toke/catalogo/catalogo_app.py`

**Responsabilidade:** mapa de nomes/sinonimos de apps para nomes reais pesquisados no Windows.

### `sistema_toke/catalogo/catalogo_atalho.py`

**Responsabilidade:** catalogo declarativo de atalhos de janela/navegador.

**Classes:** `AtalhoInfo(TypedDict)`.

### `sistema_toke/catalogo/catalogo_site.py`

**Responsabilidade:** catalogo de sites conhecidos.

**Classes:** `SiteInfo(dataclass)` com `nome`, `url`, `sinonimos`, `categoria`.

### `sistema_toke/catalogo/catalogo_verbo.py`

**Responsabilidade:** sinonimos verbais e palavras descartaveis.

**Constantes:** conjuntos por acao, `MAPA_VERBOS`, `VERBOS_POR_ACAO`, `PALAVRAS_DESCARTE`.

### `sistema_toke/executor.py`

**Responsabilidade:** registro e execucao de acoes.

**Constantes:** `REGISTRO_ACOES`, dict global de `acao -> callable`.

**Funcoes:** `registrar(nome_acao, funcao)`, `registrar_comandos_padrao()`, `executar(acao, **parametros)`.

### `sistema_toke/normalizador.py`

**Responsabilidade:** transformar fala em texto canonico simples.

**Funcoes:** `_remover_pontuacao`, `_limpar`, `_tokenizar`, `_encontrar_verbo`, `_remover_descartaveis`, `_extrair_objeto`, `_exibir_debug`, `normalizar(texto)`.

**Saida:** string normalizada ou `None`.

### `sistema_toke/parser.py`

**Responsabilidade:** converter texto normalizado em intencao inicial.

**Constantes:** `COMANDOS_FIXOS`, `MAPA_TOKEN_PARA_ACOES`.

**Funcoes:** `_construir_mapa_token_acoes`, `_extrair_verbo_e_objeto`, `_classificar_alvo_abrir`, `_resolver_intencao_por_token`, `parse(texto)`.

### `sistema_toke/resolvedor.py`

**Responsabilidade:** transformar intencao do parser em acao executavel e parametros.

**Funcao:** `resolver(intencao)` trata comandos prontos, atalhos, apps e sites; retorna dict `acao/parametros` ou `None`.

## Testes em `tests/`

### `tests/test_captura.py`

Valida construcao de `ServicoCaptura`, parametros recomendados, erro de configuracao `non_speaking_duration > pause_threshold`, chamada a `listen` e retorno `None` em timeout.

### `tests/test_estados.py`

Confirma existencia de estados essenciais em `Estado`.

### `tests/test_fluxo.py`

Testa interpretador + dispatcher para clima, horario em Londres, diferenca de horario e clima amanha em Salvador. Depende de rede/APIs para clima/localizacao.

### `tests/test_fluxo_apresentacao.py`

Script executavel que stubba acoes e TTS, chama `fala.processar_comando` para apresentacao, conversa, abertura e caso desconhecido.

### `tests/test_integracao_fluxo.py`

Testa fluxo por `fala.processar_comando` com TTS e executor simulados, incluindo politica de voz e casos de clima/localizacao/apresentacao/conversa. Alguns testes dependem de servicos externos se nao forem mockados internamente.

### `tests/test_integracao_wake.py`

Testa um ciclo do orquestrador com transcricao `autowork fechar`, esperando `Estado.ENCERRANDO`.

### `tests/test_interpretador.py`

Cobre estrutura de intencao, comandos, parametros, pergunta sobre comando como conversa, hora/data, clima, localizacao, apresentacao, conversa e politica `falar`.

### `tests/test_orquestrador.py`

Cobre inicializacao e ciclos com captura vazia ou transcricao vazia.

### `tests/test_reconhecimento.py`

Cobre STT, normalizacao e tratamento de erros da Google Speech API.

### `tests/test_tts.py`

Cobre chamada a `audio.tts.falar` e texto vazio. O patch usa `audio.tts._falar_kokoro` com `create=True`, mas a funcao real e importada dentro de `falar()` a partir de `modules.voz_teste`; dependendo do ambiente, o teste pode tocar o TTS real.

### `tests/test_tudo.py`

Cobre localizacao, datas, horario, diferenca e clima com dados/API reais.

### `tests/test_wake_word.py`

Cobre variantes de wake word e texto limpo retornado.
