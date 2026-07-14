

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import edge_tts
import pygame

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _EdgeTtsSettings:
    voice: str
    speed: Optional[str] = None  # edge-tts espera str
    volume: Optional[str] = None  # edge-tts espera str (ex: "+0%" ou "-5dB")


class Voz:
    """Síntese de voz (TTS) usando Edge-TTS + pygame.

    Observações de design:
    - A API pública é síncrona (falar/parar/etc), porque o restante do AUTOWORK
      chama esses métodos de forma direta.
    - Internamente, usamos asyncio para sintetizar com edge-tts.
    - O áudio é gerado em arquivo temporário e removido após a reprodução.
    - `parar()` interrompe imediatamente a reprodução atual.
    """

    def __init__(
        self,
        voice: str = "pt-BR-AntonioNeural",
        *,
        pygame_init: bool = True,
    ) -> None:
        self._lock = threading.RLock()

        # Controle de cancelamento/stop
        self._stop_event = threading.Event()
        self._playback_thread: Optional[threading.Thread] = None
        self._current_file: Optional[Path] = None

        self._settings = _EdgeTtsSettings(voice=voice)

        if pygame_init:
            self._init_pygame()

        # Garantia: edge-tts é usado via asyncio; não precisamos inicialização.

    def _init_pygame(self) -> None:
        try:
            # Inicializa mixer para reprodução de arquivos.
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception as exc:  # pragma: no cover
            logger.exception("Falha ao inicializar pygame: %s", exc)

    @staticmethod
    def _sanitize_text(texto: Any) -> str:
        if texto is None:
            raise ValueError("texto não pode ser None")
        if not isinstance(texto, str):
            raise TypeError(f"texto deve ser str, recebido: {type(texto).__name__}")
        texto = texto.strip()
        if not texto:
            raise ValueError("texto não pode ser vazio")
        return texto

    def _format_speed_volume(
        self,
        *,
        speed: Optional[Union[str, float, int]] = None,
        volume: Optional[Union[str, float, int]] = None,
    ) -> _EdgeTtsSettings:
        current = self._settings

        new_speed: Optional[str] = current.speed
        new_volume: Optional[str] = current.volume

        if speed is not None:
            # edge-tts aceita speed como string numérica (ex: "+10%", "-5%", "1.0")
            new_speed = str(speed)
        if volume is not None:
            # edge-tts aceita volume como string (ex: "+0%", "-5%" ou variação suportada pelo edge-tts)
            new_volume = str(volume)

        return _EdgeTtsSettings(voice=current.voice, speed=new_speed, volume=new_volume)

    def _ensure_event_loop(self) -> asyncio.AbstractEventLoop:
        """Garante um loop para execução do edge-tts.

        - Se já houver loop em execução na thread atual, reutiliza.
        - Se não houver loop, cria um novo.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop

    async def _synthesize_to_file(self, texto: str, output_path: Path) -> None:
        """Sinteze texto -> arquivo usando edge-tts."""
        settings = self._settings

        communicate_kwargs: Dict[str, Any] = {
            "text": texto,
            "voice": settings.voice,
        }
        if settings.speed is not None:
            communicate_kwargs["rate"] = settings.speed
        if settings.volume is not None:
            communicate_kwargs["volume"] = settings.volume

        # edge-tts produz arquivos de áudio em base64/stream; provide `save`.
        # edge-tts usa ffmpeg internamente quando necessário (dependendo do formato).
        tts = edge_tts.Communicate(**communicate_kwargs)
        await tts.save(str(output_path))

    def _play_file_blocking(self, file_path: Path) -> None:
        """Reproduz o arquivo e bloqueia até terminar ou parar()."""
        try:
            if not file_path.exists():
                logger.error("Arquivo de áudio temporário não existe: %s", file_path)
                return

            # Interrompe qualquer áudio em andamento.
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

            # Garante que o dispositivo de áudio está aberto.
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
            except Exception as exc:
                logger.exception("Falha ao inicializar dispositivo de áudio: %s", exc)
                return

            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()


            # Espera: usa loop curto para responsividade ao stop_event.
            while pygame.mixer.music.get_busy():
                if self._stop_event.is_set():
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass
                    return
                # sleep pequena usando pygame clock/timing (sem asyncio aqui)
                pygame.time.wait(60)
        except Exception as exc:
            logger.exception("Erro durante a reprodução de áudio: %s", exc)
        finally:
            # Remoção do arquivo é feita fora (no método falar), porém tentamos também aqui.
            pass

    def falar(self, texto: str) -> None:
        """Recebe qualquer texto e reproduz utilizando Edge-TTS.

        Esta função é síncrona para manter compatibilidade com o restante do
        AUTOWORK. Internamente, cria um arquivo temporário, sintetiza e toca.

        Args:
            texto: Conteúdo a ser falado.
        """
        try:
            texto_sanitizado = self._sanitize_text(texto)
        except Exception as exc:
            logger.exception("Voz.falar: texto inválido: %s", exc)
            return

        with self._lock:
            # Cancela reprodução anterior imediatamente.
            self._stop_event.set()
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

            # Aguarda thread anterior (se existir)
            if self._playback_thread and self._playback_thread.is_alive():
                # Não bloqueia indefinidamente para manter robustez.
                self._playback_thread.join(timeout=1.0)

            # Reset stop_event para a nova fala.
            self._stop_event = threading.Event()

            tmp_dir = Path(tempfile.gettempdir())
            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    suffix=".mp3",
                    prefix="autowork_tts_",
                    dir=str(tmp_dir),
                    delete=False,
                ) as tmp:
                    output_path = Path(tmp.name)

                self._current_file = output_path

                # Sintetiza usando edge-tts via asyncio.
                try:
                    loop = self._ensure_event_loop()
                    if loop.is_running():
                        # Cenário raro: loop já em execução na thread atual.
                        # Para manter robustez, sintetizamos em nova thread.
                        self._synthesize_in_thread_and_play(texto_sanitizado, output_path)
                        return

                    loop.run_until_complete(self._synthesize_to_file(texto_sanitizado, output_path))
                except Exception as exc:
                    logger.exception("Erro ao sintetizar com Edge-TTS: %s", exc)
                    # Garante limpeza.
                    self._try_remove_file(output_path)
                    self._current_file = None
                    return

                # Reproduz (em thread para permitir chamar parar() sem bloqueio total).
                self._playback_thread = threading.Thread(
                    target=self._play_and_cleanup,
                    args=(output_path,),
                    daemon=True,
                )
                self._playback_thread.start()

            except Exception as exc:
                logger.exception("Voz.falar: falha preparando execução: %s", exc)
                # Fallback: tentativa de limpeza.
                if "output_path" in locals():
                    self._try_remove_file(output_path)  # type: ignore[name-defined]
                self._current_file = None

    def _synthesize_in_thread_and_play(self, texto: str, output_path: Path) -> None:
        """Synthesizes in a separate thread when there is already a running loop."""

        def worker() -> None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._synthesize_to_file(texto, output_path))
            except Exception as exc:
                logger.exception("Edge-TTS (thread) falhou: %s", exc)
                self._try_remove_file(output_path)
                return
            finally:
                try:
                    loop = asyncio.get_event_loop()
                    loop.close()
                except Exception:
                    pass

            self._play_file_as_thread(output_path)

        self._playback_thread = threading.Thread(target=worker, daemon=True)
        self._playback_thread.start()

    def _play_file_as_thread(self, output_path: Path) -> None:
        with self._lock:
            self._playback_thread = threading.Thread(
                target=self._play_and_cleanup,
                args=(output_path,),
                daemon=True,
            )
            self._playback_thread.start()

    def _play_and_cleanup(self, output_path: Path) -> None:
        try:
            self._play_file_blocking(output_path)
        finally:
            self._try_remove_file(output_path)
            with self._lock:
                if self._current_file == output_path:
                    self._current_file = None

    @staticmethod
    def _try_remove_file(path: Path) -> None:
        try:
            if path.exists():
                path.unlink(missing_ok=True)  # type: ignore[call-arg]
        except TypeError:
            # Compatibilidade com Python mais antigo (sem missing_ok)
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass
        except Exception:
            logger.exception("Falha ao remover arquivo temporário: %s", path)

    def parar(self) -> None:
        """Interrompe imediatamente qualquer áudio em reprodução."""
        with self._lock:
            try:
                self._stop_event.set()
            except Exception:
                pass

            try:
                pygame.mixer.music.stop()
            except Exception as exc:
                logger.exception("Erro ao parar pygame.mixer.music: %s", exc)

            # Cleanup agressivo do arquivo atual, se existir.
            if self._current_file is not None:
                self._try_remove_file(self._current_file)
                self._current_file = None

    def alterar_voz(self, voz_microsoft: str) -> None:
        """Altera a voz neural da Microsoft.

        Exemplo:
            voz.alterar_voz("pt-BR-AntonioNeural")

        Args:
            voz_microsoft: Nome/ID da voz do edge-tts.
        """
        if not isinstance(voz_microsoft, str) or not voz_microsoft.strip():
            logger.error("alterar_voz: voz inválida: %r", voz_microsoft)
            return

        with self._lock:
            self._settings = _EdgeTtsSettings(
                voice=voz_microsoft.strip(),
                speed=self._settings.speed,
                volume=self._settings.volume,
            )

    def alterar_velocidade(self, speed: Union[str, float, int]) -> None:
        """Define a velocidade da fala (edge-tts rate).

        Exemplos (dependem da aceitação pelo edge-tts):
            - 1.0, "1.0"
            - "+10%", "-5%"

        Args:
            speed: Velocidade (string ou número).
        """
        with self._lock:
            self._settings = self._format_speed_volume(speed=speed)

    def alterar_volume(self, volume: Union[str, float, int]) -> None:
        """Define o volume da fala (edge-tts volume).

        Exemplos (dependem da aceitação pelo edge-tts):
            - "+0%", "-5%"
            - "-3dB"

        Args:
            volume: Volume (string ou número).
        """
        with self._lock:
            self._settings = self._format_speed_volume(volume=volume)

    def listar_vozes(self) -> List[Dict[str, str]]:
        """Retorna todas as vozes disponíveis do edge-tts.

        Returns:
            Lista de dicts com pelo menos: name, shortName, locale.
        """
        try:
            loop = self._ensure_event_loop()
            if loop.is_running():
                # Caso extremo: loop já em execução. Criamos thread para buscar vozes.
                result_container: List[List[Dict[str, str]]] = []

                def worker() -> None:
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        voices = new_loop.run_until_complete(edge_tts.list_voices())
                        result_container.append(voices)
                    except Exception as exc:
                        logger.exception("listar_vozes (thread) falhou: %s", exc)
                    finally:
                        try:
                            new_loop.close()  # type: ignore[name-defined]
                        except Exception:
                            pass

                t = threading.Thread(target=worker, daemon=True)
                t.start()
                t.join(timeout=5.0)
                return result_container[0] if result_container else []

            voices = loop.run_until_complete(edge_tts.list_voices())
            return voices
        except Exception as exc:
            logger.exception("Erro ao listar vozes: %s", exc)
            return []

