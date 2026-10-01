"""Orquestrador — coordena o fluxo de voz completo do AUTOWORK."""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

from core.estados import Estado
from persn_emcoes import EstadoEmocional, Personalidade

logger = logging.getLogger(__name__)

# Callbacks typealias
OnEstadoCallback = Callable[[Estado], None]

COMANDO_FECHAR = frozenset({"fechar", "encerrar", "desligar"})

# Status que merecem resposta por voz mesmo sem a flag "falar" explícita.
STATUS_FALAVEIS = frozenset({
    "falha",
    "nao_reconhecido",
    "acao_nao_encontrada",
    "nao_confirmado",
    "contrato_invalido",
    "erro_excecao",
    "erro_stt",
    "erro_tts",
    "erro_voz",
})
STATUS_ERRO = frozenset({
    "falha",
    "nao_confirmado",
    "acao_nao_encontrada",
    "contrato_invalido",
    "erro_excecao",
    "erro_stt",
    "erro_tts",
    "erro_voz",
})


class Orquestrador:
    """Pipeline central: captura → transcrição → wake word → execução → TTS.

    Opcionalmente notifica um ``ouvinte`` (interface) com eventos de estado,
    transcrição, resposta e nível de áudio. O ouvinte é duck-typed: métodos
    ausentes são simplesmente ignorados.
    """

    # Duração da janela de escuta ativa (segundos).
    _JANELA_ATIVA_SEGUNDOS = 180

    def __init__(
        self,
        servico_captura,       # audio.captura.ServicoCaptura
        servico_stt,           # audio.reconhecimento.ServicoReconhecimento
        on_estado: Optional[OnEstadoCallback] = None,
        ouvinte: Optional[Any] = None,
        personalidade: Optional[Personalidade] = None,
    ) -> None:
        from sistema_toke.executor import registrar_comandos_padrao
        registrar_comandos_padrao()

        self._captura = servico_captura
        self._stt = servico_stt
        self._personalidade = personalidade or Personalidade()
        self._estado = Estado.INICIALIZANDO
        self._on_estado = on_estado or (lambda e: None)
        self._ouvinte = ouvinte
        self._rodando = False
        self._lock_processamento = threading.RLock()
        from core.agendador import Agendador
        from core.contexto_execucao import ContextoExecucao
        from core.eventos import EventBus
        from core.fila_execucao import FilaExecucao
        from core.gerenciador_tarefas import GerenciadorTarefas

        self.eventos = EventBus()
        self.contexto_execucao = ContextoExecucao()
        self.gerenciador_tarefas = GerenciadorTarefas(self.eventos)
        self.agendador = Agendador()
        self.fila_execucao = FilaExecucao()
        self._executor_workflow_ativo = None
        # Controle de escuta REPOUSO/ATIVO
        self._modo_ativo = False       # True = aceita comandos sem wake word
        self._ativo_ate: float = 0.0   # time.monotonic() do fim da janela

    @property
    def personalidade(self) -> Personalidade:
        """Camada de personalidade e manifestações emocionais simuladas."""
        return self._personalidade

    @property
    def estado(self) -> Estado:
        """Estado atual do sistema."""
        return self._estado

    def _set_estado(self, novo: Estado) -> None:
        """Atualiza estado e notifica callback e ouvinte."""
        self._estado = novo
        self._on_estado(novo)
        self._notificar_ouvinte("ao_estado", novo)
        logger.debug("Estado → %s", novo.name)

    def _notificar_ouvinte(self, metodo: str, *args: Any) -> None:
        """Encaminha um evento ao ouvinte sem nunca quebrar o pipeline."""
        if self._ouvinte is None:
            return
        acao = getattr(self._ouvinte, metodo, None)
        if acao is None:
            return
        try:
            acao(*args)
        except Exception:
            logger.debug("Ouvinte falhou em %s.", metodo, exc_info=True)

    def _tem_ouvinte(self, metodo: str) -> bool:
        return self._ouvinte is not None and hasattr(self._ouvinte, metodo)

    # ── Controle de escuta REPOUSO / ATIVO ──────────────────────────

    def _ativar_escuta(self) -> None:
        """Entra (ou renova) MODO ATIVO: aceita comandos sem wake word."""
        import time as _time
        self._modo_ativo = True
        self._ativo_ate = _time.monotonic() + self._JANELA_ATIVA_SEGUNDOS
        logger.info(
            "[ESCUTA] MODO ATIVO — janela de %ds iniciada.",
            self._JANELA_ATIVA_SEGUNDOS,
        )

    def _verificar_janela_ativa(self) -> bool:
        """Retorna True se o MODO ATIVO ainda é válido; expira se necessário."""
        if not self._modo_ativo:
            return False
        import time as _time
        if _time.monotonic() >= self._ativo_ate:
            self._modo_ativo = False
            self._ativo_ate = 0.0
            logger.info("[ESCUTA] Janela expirou — MODO REPOUSO.")
            return False
        return True

    # ────────────────────────────────────────────────────────────────

    def inicializar(self) -> None:
        """Calibra microfone e prepara o sistema."""
        self._set_estado(Estado.INICIALIZANDO)
        self._captura.calibrar()
        self._set_estado(Estado.IDLE)

    def executar_loop(self) -> None:
        """Loop principal do assistente."""
        from interface.terminal import mostrar_status, mostrar_banner

        mostrar_banner()
        saudacao = self._personalidade.saudar()
        mostrar_status(f"AUTOWORK online! {saudacao}")
        self._notificar_ouvinte("ao_resposta", {"mensagem": saudacao})
        self._set_estado(Estado.FALANDO)
        if not self._falar_resposta(saudacao):
            self._set_estado(Estado.ERRO)
        self._set_estado(Estado.IDLE)

        self._rodando = True
        while self._rodando:
            self._ciclo()

    def _ao_feedback_espera(self, mensagem: str) -> None:
        """Emite fala curta de espera durante processamentos demorados."""
        logger.info("[FEEDBACK ESPERA] %s", mensagem)
        self._notificar_ouvinte("ao_resposta", {"mensagem": mensagem})
        try:
            self._falar_resposta(mensagem)
        except Exception:
            pass

    def _capturar_com_ou_sem_niveis(self):
        """Captura áudio, emitindo níveis reais se o ouvinte os consumir."""
        if self._tem_ouvinte("ao_nivel") and hasattr(
            self._captura, "capturar_com_niveis"
        ):
            return self._captura.capturar_com_niveis(self._ao_nivel_microfone)
        return self._captura.capturar()

    def _ao_nivel_microfone(self, rms: float) -> None:
        """Repassa o RMS bruto do microfone ao ouvinte (sem normalização)."""
        self._notificar_ouvinte("ao_nivel", rms)

    def _falar_resposta(self, mensagem: str) -> bool:
        """Fala a mensagem emitindo níveis reais e aplicando características da personalidade."""
        import audio.tts as tts

        config_fala = self._personalidade.configurar_fala(mensagem)
        texto = config_fala.texto
        velocidade = config_fala.velocidade
        voz = config_fala.voz

        if self._tem_ouvinte("ao_nivel") and hasattr(tts, "falar_com_niveis"):
            return bool(tts.falar_com_niveis(texto, self._ao_nivel_tts, voice=voz, speed=velocidade))
        return bool(tts.falar(texto, voice=voz, speed=velocidade))

    def _ao_nivel_tts(self, nivel: float) -> None:
        self._notificar_ouvinte("ao_nivel", nivel)

    @staticmethod
    def _deve_falar(resultado: Dict[str, Any]) -> bool:
        """Política de voz: respostas informativas falam; confirmações de
        comando de sucesso não (evita repetição excessiva)."""
        if "falar" in resultado:
            return bool(resultado["falar"])
        return resultado.get("status") in STATUS_FALAVEIS

    def _ciclo(self) -> None:
        """Um ciclo completo: ouvir → transcrever → detectar wake → processar."""
        from audio import wake_word
        from interface.terminal import mostrar_status

        # 1. Captura (None = ninguém falou no tempo limite da escuta)
        self._set_estado(Estado.OUVINDO)
        audio = self._capturar_com_ou_sem_niveis()
        if audio is None:
            self._set_estado(Estado.IDLE)
            return

        # 2. Transcrição
        self._set_estado(Estado.TRANSCREVENDO)
        texto = self._stt.transcrever(audio)
        if texto is None:
            erro_stt = getattr(self._stt, "ultimo_erro", None)
            if erro_stt:
                self._notificar_ouvinte("ao_resposta", {
                    "status": "erro_stt",
                    "mensagem": f"Falha no reconhecimento de voz: {erro_stt}",
                    "falar": False,
                })
                self._set_estado(Estado.ERRO)
            self._set_estado(Estado.IDLE)
            return  # Silêncio — NÃO fala "não entendi"

        self._notificar_ouvinte("ao_transcricao", texto)

        # 3. Wake word / Controle de escuta
        self._set_estado(Estado.DETECTANDO_WAKE)
        detectado, comando = wake_word.detectar(texto)

        if detectado:
            # Wake word presente — (re)ativa a janela de 3 minutos
            self._ativar_escuta()
            if not comando:
                # Usuário disse apenas "work" sem comando junto
                self._set_estado(Estado.IDLE)
                return
        else:
            # Sem wake word — aceita somente se estiver em MODO ATIVO
            if not self._verificar_janela_ativa():
                logger.debug("Ignorando (REPOUSO, sem wake word): %r", texto)
                self._set_estado(Estado.IDLE)
                return
            # MODO ATIVO: usa o texto inteiro como comando
            comando = texto

        # 4. Comando de encerramento
        if comando in COMANDO_FECHAR:
            mostrar_status("Encerrando AUTOWORK...")
            despedida = self._personalidade.despedir()
            self._set_estado(Estado.FALANDO)
            self._falar_resposta(despedida)
            self._set_estado(Estado.ENCERRANDO)
            self._rodando = False
            return

        # 5. Processamento
        self._set_estado(Estado.PROCESSANDO)
        resultado = self.processar_comando(comando)
        self._notificar_ouvinte("ao_resposta", resultado)

        # 6. TTS da resposta
        mensagem = resultado.get("mensagem", "")
        tts_ok = True
        if mensagem and self._deve_falar(resultado):
            self._set_estado(Estado.FALANDO)
            tts_ok = self._falar_resposta(mensagem)

        # 7. Estado final
        status = resultado.get("status", "")
        if not tts_ok:
            self._set_estado(Estado.ERRO)
        elif status == "sucesso" and resultado.get("confirmado") is True:
            self._set_estado(Estado.SUCESSO)
        elif status in STATUS_ERRO:
            self._set_estado(Estado.ERRO)
        self._set_estado(Estado.IDLE)

    def processar_comando(self, texto: str) -> Dict[str, Any]:
        """Interpreta e executa um comando de texto (sem áudio).

        Este método pode ser chamado diretamente para testes,
        sem depender de captura de áudio real.
        """
        logger.info("[Orquestrador] processando comando: %r", texto)
        controle = self._processar_controle_tarefa(texto)
        if controle is not None:
            return controle
        with self._lock_processamento:
            self._personalidade.emocao.transitar(EstadoEmocional.PROCESSANDO)
            with self._personalidade.feedback.monitorar(self._ao_feedback_espera):
                resultado = self._executar_processamento(texto)

            status = resultado.get("status", "")
            if status == "sucesso":
                self._personalidade.emocao.transitar(EstadoEmocional.SATISFEITO)
            elif status in STATUS_ERRO:
                self._personalidade.emocao.transitar(EstadoEmocional.ERRO)
            elif status == "nao_reconhecido":
                self._personalidade.emocao.transitar(EstadoEmocional.ALERTA)
            else:
                self._personalidade.emocao.transitar(EstadoEmocional.NEUTRO)

            logger.info("[Orquestrador] resultado status=%s acao=%s",
                        status, resultado.get("acao"))
            return resultado

    def _executar_processamento(self, texto: str) -> Dict[str, Any]:
        from dispatcher import dispatch
        from interpretador import interpretar
        from sistema_toke.executor import executar
        from sistema_toke.normalizador import normalizar
        from interface.terminal import mostrar_resultado

        inicio_interpretacao = time.perf_counter()
        self.eventos.publish("ASSISTANT_UNDERSTANDING", texto=texto)
        intencao = interpretar(texto, contexto=self.contexto_execucao.snapshot())
        logger.info(
            "[PERF] interpretação concluída em %.1f ms",
            (time.perf_counter() - inicio_interpretacao) * 1000,
        )
        tipo = intencao.get("tipo", "desconhecido")
        texto_filtrado = intencao.get("texto_filtrado", texto)
        if texto_filtrado and texto_filtrado != texto:
            logger.info("Filtro STT: %r → %r", texto, texto_filtrado)

        if intencao.get("agendamento"):
            return self._agendar_intencao(intencao, texto)

        if tipo == "comando_complexo":
            from sist_comd_complex.executor_complexo import executar_workflow

            logger.debug("Executando workflow complexo: %s", intencao)
            self.eventos.publish("ASSISTANT_PLANNING", plano=intencao)
            tarefa = self.gerenciador_tarefas.criar(
                intencao.get("descricao", texto),
                intencao.get("etapas", []),
                task_id=intencao.get("id"),
            )
            task_id = tarefa.get("task_id")
            from sist_comd_complex.executor_complexo import ExecutorComplexo

            self._executor_workflow_ativo = ExecutorComplexo(
                ao_iniciar_etapa=lambda etapa: self._ao_iniciar_etapa(task_id, etapa),
                ao_finalizar_etapa=lambda etapa, resultado: self._ao_finalizar_etapa(task_id, etapa, resultado),
                pode_cancelar_etapa=lambda etapa: self.gerenciador_tarefas.deve_cancelar(task_id, etapa.get("id")),
            )
            self._set_estado(Estado.EXECUTANDO)
            self.eventos.publish("ASSISTANT_EXECUTING", task_id=task_id)
            resultado = executar_workflow(intencao, executor=self._executor_workflow_ativo)
            self._executor_workflow_ativo = None
            for etapa_resultado in resultado.get("resultados", []):
                # Dependências quebradas e cancelamento antes do início não
                # passam pelo callback de execução; sincronize-os igualmente.
                self.gerenciador_tarefas.concluir_acao(
                    task_id,
                    etapa_resultado.get("etapa_id"),
                    etapa_resultado,
                )
            self.gerenciador_tarefas.finalizar(task_id, resultado)
            mostrar_resultado(texto, None, intencao, resultado)
            return resultado

        # Comando específico: o interpretador já passou pelo parser/resolvedor.
        if tipo == "comando":
            normalizado = normalizar(texto_filtrado)
            logger.debug("Normalizado: %r", normalizado)

            if intencao.get("resolvido") is False:
                logger.debug(
                    "Resolvedor não encontrou ação para a intenção: %s",
                    intencao,
                )
                resultado = {
                    "status": "falha",
                    "acao": intencao.get("acao", ""),
                    "mensagem": "Não foi possível resolver a ação.",
                }
            else:
                logger.debug("Executando comando: %s", intencao)
                self._set_estado(Estado.EXECUTANDO)
                self.eventos.publish(
                    "ACTION_STARTED",
                    acao=intencao["acao"],
                    parametros=intencao.get("parametros", {}),
                )
                resultado = executar(
                    intencao["acao"],
                    **intencao.get("parametros", {}),
                )
                self.eventos.publish(
                    "ACTION_COMPLETED" if resultado.get("confirmado") else "ACTION_FAILED",
                    acao=intencao["acao"],
                    resultado=resultado,
                )
                self.contexto_execucao.registrar_acao(
                    intencao["acao"], intencao.get("parametros", {}), resultado
                )

            mostrar_resultado(texto, normalizado, intencao, resultado)

            return resultado

        # Intenção vazia: nada reconhecido.
        if tipo == "desconhecido":
            logger.debug("Intenção não reconhecida: %r", texto)
            mostrar_resultado(texto, None, None)
            return {
                "status": "nao_reconhecido",
                "texto": texto,
                "mensagem": self._personalidade.nao_reconhecido(),
            }

        # Clima, hora, apresentação e conversa seguem pelo dispatcher.
        self._set_estado(Estado.EXECUTANDO)
        resultado = dispatch(intencao)
        mostrar_resultado(texto, None, intencao, resultado)

        return resultado

    def _ao_iniciar_etapa(self, task_id: str, etapa: Dict[str, Any]) -> None:
        self.gerenciador_tarefas.iniciar_acao(task_id, etapa.get("id"))
        self.eventos.publish("ACTION_STARTED", task_id=task_id, action_id=etapa.get("id"), acao=etapa.get("acao"))

    def _ao_finalizar_etapa(self, task_id: str, etapa: Dict[str, Any], resultado: Dict[str, Any]) -> None:
        self.gerenciador_tarefas.concluir_acao(task_id, etapa.get("id"), resultado)
        self.contexto_execucao.registrar_acao(etapa.get("acao", ""), etapa.get("parametros", {}), resultado)

    def _processar_controle_tarefa(self, texto: str) -> Dict[str, Any] | None:
        """Trata interrupções antes do lock que serializa comandos normais."""
        import re

        frase = " ".join(str(texto or "").casefold().split())
        if not frase:
            return None
        task_id = self.gerenciador_tarefas.tarefa_ativa_id
        if frase in {"parar", "pare", "interromper", "interrompa", "cancela tudo", "cancelar tudo"}:
            if task_id:
                self.gerenciador_tarefas.cancelar_tarefa(task_id)
                if self._executor_workflow_ativo is not None:
                    self._executor_workflow_ativo.cancelar_workflow()
                self.eventos.publish("USER_INTERRUPTED", task_id=task_id)
                return {
                    "status": "cancelado",
                    "sucesso": False,
                    "confirmado": False,
                    "executado": False,
                    "acao": "cancelar_tarefa",
                    "mensagem": "A tarefa atual foi cancelada.",
                    "falar": True,
                }
            return None

        if task_id and re.search(r"\b(?:cancela|cancelar|pare|parar)\b", frase):
            alvo = re.sub(r".*?\b(?:cancela|cancelar|pare|parar)\b", "", frase).strip()
            alvo = re.sub(r"^(?:o|a|os|as)\s+", "", alvo).strip()
            tarefa = self.gerenciador_tarefas.snapshot(task_id)
            for acao in tarefa.get("acoes", []):
                candidatos = [acao.get("id"), acao.get("alvo"), acao.get("parametros", {}).get("nome"), acao.get("parametros", {}).get("aplicativo")]
                if any(alvo and str(c).casefold() == alvo for c in candidatos if c):
                    if self.gerenciador_tarefas.cancelar_acao(acao.get("id"), task_id):
                        return {
                            "status": "cancelado",
                            "sucesso": False,
                            "confirmado": False,
                            "executado": False,
                            "acao": "cancelar_acao",
                            "parametros": {"task_id": task_id, "acao_id": acao.get("id")},
                            "mensagem": f"A ação {alvo} foi cancelada.",
                            "falar": True,
                        }
        return None

    def _agendar_intencao(self, intencao: Dict[str, Any], texto: str) -> Dict[str, Any]:
        agendamento = dict(intencao.get("agendamento") or {})
        atraso = float(agendamento.get("atraso_segundos") or 0)
        plano = dict(intencao)
        plano.pop("agendamento", None)

        def executar_depois() -> None:
            self.eventos.publish("ASSISTANT_EXECUTING", agendamento=True, texto=texto)
            if plano.get("tipo") == "comando" and plano.get("acao"):
                from sistema_toke.executor import executar

                resultado = executar(plano["acao"], **plano.get("parametros", {}))
                self.contexto_execucao.registrar_acao(
                    plano["acao"], plano.get("parametros", {}), resultado
                )
            else:
                resultado = self._executar_processamento(
                    plano.get("texto_comando") or plano.get("texto_filtrado") or texto
                )
            self._notificar_ouvinte("ao_resposta", resultado)

        agendado = self.agendador.agendar(
            executar_depois,
            atraso=atraso,
            descricao=texto,
        )
        self.eventos.publish("ASSISTANT_WAITING", agendamento=agendado)
        return {
            "status": "agendado",
            "sucesso": False,
            "confirmado": False,
            "executado": False,
            "tipo": "agendamento",
            "acao": intencao.get("acao"),
            "parametros": intencao.get("parametros", {}),
            "agendamento": agendado,
            "mensagem": f"Ação agendada para {agendado['executar_em']}.",
            "falar": True,
        }

    def parar(self) -> None:
        """Sinaliza encerramento do loop."""
        self._rodando = False

    def enfileirar_comando(self, texto: str, prioridade: int = 20) -> str:
        """Entrada não bloqueante para consumidores interativos.

        ``processar_comando`` continua síncrono por compatibilidade com o modo
        terminal e com a API atual; esta fachada serializa novas solicitações
        quando o consumidor deseja alimentar a fila explicitamente.
        """
        from core.fila_execucao import Prioridade

        nivel = Prioridade(prioridade) if prioridade in {0, 10, 20, 30} else Prioridade.NORMAL
        return self.fila_execucao.submeter(lambda: self.processar_comando(texto), nivel)
