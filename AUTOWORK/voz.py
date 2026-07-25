from __future__ import annotations

import asyncio
import logging
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pygame

from configui import VOICE_ENGINE, VOICE_PROFILES, resolve_voice_settings
from personalidade import estilizar_fala
from vozes import get_engine
from vozes.base import VoiceSettings

logger = logging.getLogger(__name__)


class Voz:
    """Facade síncrona de TTS do AUTOWORK.

    API pública mantida:
        voz.falar("texto")
        voz.parar()
        voz.alterar_voz(...)
        voz.alterar_velocidade(...)
        voz.alterar_volume(...)
        voz.listar_vozes()
    """

    def __init__(
        self,
        voice: Optional[str] = None,
        *,
        pygame_init: bool = True,
        estilizar: bool = True,
    ) -> None:
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._playback_thread: Optional[threading.Thread] = None
        self._current_file: Optional[Path] = None
        self._estilizar = estilizar

        cfg = resolve_voice_settings()
        if voice:
            cfg = {**cfg, "voice_name": voice}

        self._settings = VoiceSettings(
            voice_name=cfg["voice_name"],
            rate=cfg["rate"],
            pitch=cfg["pitch"],
            volume=cfg["volume"],
        )
        self._engine_name = VOICE_ENGINE
        self._engine = get_engine(self._engine_name)
        self._engine.update_settings(self._settings)

        if pygame_init:
            self._init_pygame()

    def _init_pygame(self) -> None:
        try:
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

    def aplicar_perfil(self, perfil: str) -> None:
        """Aplica perfil jarvis | normal | alerta."""
        key = (perfil or "").strip().lower()
        if key not in VOICE_PROFILES:
            logger.error("Perfil desconhecido: %r", perfil)
            return
        cfg = VOICE_PROFILES[key]
        with self._lock:
            self._settings = VoiceSettings(
                voice_name=cfg["voice_name"],
                rate=cfg["rate"],
                pitch=cfg["pitch"],
                volume=cfg["volume"],
            )
            self._engine.update_settings(self._settings)

    def _run_coro(self, coro: Any) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        result: Dict[str, Any] = {}
        error: Dict[str, BaseException] = {}

        def worker() -> None:
            try:
                result["value"] = asyncio.run(coro)
            except BaseException as exc:  # noqa: BLE001
                error["exc"] = exc

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        t.join()
        if "exc" in error:
            raise error["exc"]
        return result.get("value")

    @staticmethod
    def _unload_pygame_music() -> None:
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        try:
            unload = getattr(pygame.mixer.music, "unload", None)
            if callable(unload):
                unload()
        except Exception:
            pass

    def _play_file_blocking(self, file_path: Path) -> None:
        try:
            if not file_path.exists():
                logger.error("Arquivo de áudio temporário não existe: %s", file_path)
                return

            self._unload_pygame_music()

            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
            except Exception as exc:
                logger.exception("Falha ao inicializar dispositivo de áudio: %s", exc)
                return

            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if self._stop_event.is_set():
                    self._unload_pygame_music()
                    return
                pygame.time.wait(60)
        except Exception as exc:
            logger.exception("Erro durante a reprodução de áudio: %s", exc)
        finally:
            self._unload_pygame_music()

    def aguardar_fim(self, timeout: float = 60.0) -> None:
        """Aguarda a reprodução atual terminar (útil para métricas e sincronização)."""
        with self._lock:
            thread = self._playback_thread
        if thread and thread.is_alive():
            thread.join(timeout=timeout)

    def falar(self, texto: str) -> None:
        try:
            texto_sanitizado = self._sanitize_text(texto)
        except Exception as exc:
            logger.exception("Voz.falar: texto inválido: %s", exc)
            return

        if self._estilizar:
            texto_sanitizado = estilizar_fala(texto_sanitizado)

        with self._lock:
            self._stop_event.set()
            self._unload_pygame_music()

            if self._playback_thread and self._playback_thread.is_alive():
                self._playback_thread.join(timeout=1.0)

            self._stop_event = threading.Event()

            tmp_dir = Path(tempfile.gettempdir())
            output_path: Optional[Path] = None
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
                assert output_path is not None

                try:
                    self._run_coro(
                        self._engine.synthesize_to_file(texto_sanitizado, output_path)
                    )
                except Exception as exc:
                    logger.exception("Erro ao sintetizar TTS: %s", exc)
                    self._try_remove_file(output_path)
                    self._current_file = None
                    return

                self._playback_thread = threading.Thread(
                    target=self._play_and_cleanup,
                    args=(output_path,),
                    daemon=True,
                )
                self._playback_thread.start()

            except Exception as exc:
                logger.exception("Voz.falar: falha preparando execução: %s", exc)
                if output_path is not None:
                    self._try_remove_file(output_path)
                self._current_file = None

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
        for attempt in range(5):
            try:
                if path.exists():
                    path.unlink()
                return
            except PermissionError:
                time.sleep(0.05 * (attempt + 1))
            except Exception:
                logger.exception("Falha ao remover arquivo temporário: %s", path)
                return
        logger.warning("Arquivo temporário não removido (ainda bloqueado): %s", path)

    def parar(self) -> None:
        with self._lock:
            self._stop_event.set()
            try:
                self._unload_pygame_music()
            except Exception as exc:
                logger.exception("Erro ao parar pygame.mixer.music: %s", exc)
            if self._current_file is not None:
                self._try_remove_file(self._current_file)
                self._current_file = None

    def alterar_voz(self, voz_microsoft: str) -> None:
        if not isinstance(voz_microsoft, str) or not voz_microsoft.strip():
            logger.error("alterar_voz: voz inválida: %r", voz_microsoft)
            return
        with self._lock:
            self._settings = VoiceSettings(
                voice_name=voz_microsoft.strip(),
                rate=self._settings.rate,
                pitch=self._settings.pitch,
                volume=self._settings.volume,
            )
            self._engine.update_settings(self._settings)

    def alterar_velocidade(self, speed: Union[str, float, int]) -> None:
        with self._lock:
            self._settings = VoiceSettings(
                voice_name=self._settings.voice_name,
                rate=str(speed),
                pitch=self._settings.pitch,
                volume=self._settings.volume,
            )
            self._engine.update_settings(self._settings)

    def alterar_tom(self, pitch: Union[str, float, int]) -> None:
        value = str(pitch)
        if isinstance(pitch, (int, float)) and not value.endswith("Hz"):
            value = f"{int(pitch)}Hz"
        with self._lock:
            self._settings = VoiceSettings(
                voice_name=self._settings.voice_name,
                rate=self._settings.rate,
                pitch=value,
                volume=self._settings.volume,
            )
            self._engine.update_settings(self._settings)

    def alterar_volume(self, volume: Union[str, float, int]) -> None:
        with self._lock:
            self._settings = VoiceSettings(
                voice_name=self._settings.voice_name,
                rate=self._settings.rate,
                pitch=self._settings.pitch,
                volume=str(volume),
            )
            self._engine.update_settings(self._settings)

    def listar_vozes(self) -> List[Dict[str, str]]:
        if self._engine_name != "edge":
            logger.warning("listar_vozes só está disponível para o motor edge.")
            return []
        try:
            import edge_tts

            return list(self._run_coro(edge_tts.list_voices()) or [])
        except Exception as exc:
            logger.exception("Erro ao listar vozes: %s", exc)
            return []


voz_padrao = Voz()
