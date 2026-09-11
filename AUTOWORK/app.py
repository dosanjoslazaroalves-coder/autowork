"""AUTOWORK — Ponto de entrada e orquestração da execução.

Fluxo: MICROFONE → CAPTURA → RECONHECIMENTO → WAKE WORD → INTERPRETADOR
→ (comando | conversa | clima | hora | apresentação) → RESPOSTA → TTS → INTERFACE.

O app.py compõe os serviços existentes (audio/, core/, dispatcher, interface/)
e injeta uma ponte que traduz os eventos do Orquestrador para a interface HUD.
A lógica de cada etapa permanece nos seus módulos originais.
"""
from __future__ import annotations

import argparse
import logging
import sys
from typing import Any, Dict

from core.estados import Estado

logger = logging.getLogger("auto")

# Estado interno do pipeline → estado visual da interface.
MAPA_ESTADO_UI: Dict[Estado, str] = {
    Estado.INICIALIZANDO: "THINKING",
    Estado.IDLE: "IDLE",
    Estado.OUVINDO: "LISTENING",
    Estado.TRANSCREVENDO: "THINKING",
    Estado.DETECTANDO_WAKE: "THINKING",
    Estado.PROCESSANDO: "THINKING",
    Estado.EXECUTANDO: "THINKING",
    Estado.FALANDO: "SPEAKING",
    Estado.SUCESSO: "IDLE",
    Estado.ERRO: "ERROR",
    Estado.ENCERRANDO: "IDLE",
}

# RMS de referência para normalizar o nível do microfone (PCM 16 bits).
RMS_REFERENCIA = 2500.0
RMS_PISO = 400.0


class PonteInterface:
    """Traduz eventos do Orquestrador para a fachada da interface HUD.

    Mantém a interface desacoplada do áudio: a ponte apenas adapta os dados
    (Estado → rótulo, RMS → nível 0..1). Nunca lança exceções para cima.
    """

    def __init__(self, interface) -> None:
        self._interface = interface
        self._pico_rms = RMS_PISO
        self._voz_confirmada = False

    def definir_interface(self, interface) -> None:
        """Conecta a fachada real quando a interface HUD é criada."""
        self._interface = interface

    def ao_estado(self, estado: Estado) -> None:
        self._interface.set_state(MAPA_ESTADO_UI.get(estado, "IDLE"))
        if estado == Estado.FALANDO and not self._voz_confirmada:
            self._voz_confirmada = True
            self._interface.set_modulo("VOZ", "ONLINE")

    def ao_transcricao(self, texto: str) -> None:
        if texto:
            self._interface.set_transcript(texto)

    def ao_resposta(self, resultado: Dict[str, Any]) -> None:
        mensagem = resultado.get("mensagem", "")
        if mensagem:
            self._interface.set_response(mensagem)

    def ao_nivel(self, rms: float) -> None:
        """Normaliza o RMS bruto (microfone ou TTS) em um nível 0..1."""
        self._pico_rms = max(rms, self._pico_rms * 0.999, RMS_PISO)
        self._interface.set_audio_level(min(1.0, rms / self._pico_rms))

    def ao_status(self, nome: str, valor: str) -> None:
        self._interface.set_modulo(nome, valor)


def _configurar_logging(debug: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # Ruído de bibliotecas de terceiros fora do modo debug.
    if not debug:
        for nome in ("httpx", "httpcore", "urllib3", "openai"):
            logging.getLogger(nome).setLevel(logging.WARNING)


def _construir_orquestrador(ouvinte: PonteInterface):
    from audio.captura import ServicoCaptura
    from audio.reconhecimento import ServicoReconhecimento
    from core.orquestrador import Orquestrador

    captura = ServicoCaptura()
    stt = ServicoReconhecimento(captura.recognizer)
    return Orquestrador(captura, stt, ouvinte=ouvinte)


def _executar_texto_unico(texto: str) -> None:
    """Processa um comando em texto direto, sem microfone nem interface."""
    from core.orquestrador import Orquestrador

    orquestrador = _construir_orquestrador(PonteInterface(_InterfaceNula()))
    resultado = orquestrador.processar_comando(texto)

    from audio.tts import falar

    if Orquestrador._deve_falar(resultado):
        mensagem = resultado.get("mensagem", "")
        if mensagem:
            falar(mensagem)


def _executar_com_interface(orquestrador, ponte: PonteInterface) -> None:
    """Roda o pipeline em thread própria com a interface na thread principal."""
    from interface.hud import HUD

    interface = HUD()
    ponte.definir_interface(interface)

    def trabalho() -> None:
        try:
            orquestrador.inicializar()
        except Exception as exc:
            logger.error("Falha na inicialização: %s", exc)
            ponte.ao_estado(Estado.ERRO)
            ponte.ao_status("MICROFONE", "ERRO")
            ponte.ao_resposta({"mensagem": f"Microfone indisponível: {exc}"})
            return

        ponte.ao_status("MICROFONE", "ONLINE")
        ponte.ao_status("RECONHECIMENTO", "ONLINE")
        try:
            orquestrador.executar_loop()
        except Exception:
            logger.exception("Erro no ciclo do assistente.")
            ponte.ao_estado(Estado.ERRO)
            ponte.ao_resposta({"mensagem": "Erro interno. Veja o log."})
        else:
            # Encerramento solicitado por voz: fecha a interface.
            interface.encerrar()

    interface.executar(trabalho)


class _InterfaceNula:
    """Interface descartável para modos sem HUD (texto/terminal)."""

    def set_state(self, estado: str) -> None:
        pass

    def set_audio_level(self, nivel: float) -> None:
        pass

    def set_transcript(self, texto: str) -> None:
        pass

    def set_response(self, mensagem: str) -> None:
        pass

    def set_modulo(self, nome: str, valor: str) -> None:
        pass


def _analisar_argumentos(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AUTOWORK — assistente de voz")
    parser.add_argument(
        "--texto",
        metavar="FRASE",
        help="processa uma frase em texto, sem microfone nem interface",
    )
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="roda o loop no terminal, sem a interface HUD",
    )
    parser.add_argument("--debug", action="store_true", help="logging detalhado")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = _analisar_argumentos(argv)
    _configurar_logging(args.debug)

    if args.texto:
        _executar_texto_unico(args.texto)
        return

    ponte = PonteInterface(_InterfaceNula())
    orquestrador = _construir_orquestrador(ponte)

    if args.terminal:
        try:
            orquestrador.inicializar()
            orquestrador.executar_loop()
        except KeyboardInterrupt:
            from interface.terminal import mostrar_status

            mostrar_status("Interrompido pelo usuário.")
        finally:
            from interface.terminal import mostrar_status

            mostrar_status("AUTOWORK encerrado.")
        return

    logger.info("Iniciando interface HUD do AUTOWORK.")
    _executar_com_interface(orquestrador, ponte)
    logger.info("AUTOWORK encerrado.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
