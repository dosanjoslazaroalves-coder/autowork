"""Implementação TTS experimental com Kokoro (PT-BR)."""

from __future__ import annotations

import logging
import os
import platform
import warnings
from importlib import import_module
from pathlib import Path
from typing import Iterable

from . import config


def _configure_warnings() -> None:
    """Suprime avisos benignos conhecidos sem ocultar erros reais."""

    _KNOWN_LOG_PATTERNS = (
        "unauthenticated requests to the HF Hub",
    )

    class _KnownLogFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            message = record.getMessage()
            return not any(pattern in message for pattern in _KNOWN_LOG_PATTERNS)

    known_log_filter = _KnownLogFilter()

    try:
        import huggingface_hub  # noqa: F401
    except ImportError:
        pass
    else:
        hf_logger = logging.getLogger("huggingface_hub")
        hf_logger.addFilter(known_log_filter)
        for handler in hf_logger.handlers:
            handler.addFilter(known_log_filter)
        logging.getLogger("huggingface_hub.utils._http").addFilter(known_log_filter)

    warnings.filterwarnings(
        "ignore",
        message="dropout option adds dropout after all but last recurrent layer.*",
        category=UserWarning,
        module=r"torch\.nn\.modules\.rnn",
    )
    warnings.filterwarnings(
        "ignore",
        message=".*weight_norm.*is deprecated.*",
        category=FutureWarning,
        module=r"torch\.nn\.utils\.weight_norm",
    )


_configure_warnings()

_PIPELINE = None
_SOUNDEVICE = None


class TTSError(RuntimeError):
    """Erro do módulo TTS com contexto de diagnóstico."""

    def __init__(
        self,
        etapa: str,
        mensagem: str,
        causa: str,
        arquivo: str,
        correcao: str,
    ) -> None:
        self.etapa = etapa
        self.causa = causa
        self.arquivo = arquivo
        self.correcao = correcao
        super().__init__(
            "\n".join(
                [
                    f"ETAPA: {etapa}",
                    f"ERRO: {mensagem}",
                    f"Tipo: {type(self).__bases__[0].__name__}",
                    f"Causa provável: {causa}",
                    f"Arquivo/configuração: {arquivo}",
                    f"Como corrigir: {correcao}",
                ]
            )
        )


def _format_error(
    etapa: str,
    mensagem: str,
    causa: str,
    arquivo: str,
    correcao: str,
) -> TTSError:
    return TTSError(etapa, mensagem, causa, arquivo, correcao)


def _configure_espeak_paths() -> None:
    """Configura o eSpeak NG nativo no Windows para o phonemizer."""

    if platform.system() != "Windows":
        return

    if not config.ESPEAK_LIBRARY.exists():
        raise _format_error(
            etapa="configuração do eSpeak NG",
            mensagem="DLL do eSpeak NG não encontrada.",
            causa=f"Caminho ausente: {config.ESPEAK_LIBRARY}",
            arquivo="modules/voz_teste/config.py",
            correcao="Instale o eSpeak NG para Windows e confirme ESPEAK_DIR em config.py.",
        )

    if not config.ESPEAK_DATA.exists():
        raise _format_error(
            etapa="configuração do eSpeak NG",
            mensagem="Dados do eSpeak NG não encontrados.",
            causa=f"Pasta ausente: {config.ESPEAK_DATA}",
            arquivo="modules/voz_teste/config.py",
            correcao="Reinstale o eSpeak NG e confirme ESPEAK_DATA em config.py.",
        )

    espeak_dir = str(config.ESPEAK_DIR)
    current_path = os.environ.get("PATH", "")
    if espeak_dir not in current_path.split(os.pathsep):
        os.environ["PATH"] = espeak_dir + os.pathsep + current_path

    os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = str(config.ESPEAK_LIBRARY)
    os.environ["PHONEMIZER_ESPEAK_DATA_PATH"] = str(config.ESPEAK_DATA)
    os.environ["ESPEAK_DATA_PATH"] = str(config.ESPEAK_DATA)

    try:
        from phonemizer.backend.espeak.wrapper import EspeakWrapper

        EspeakWrapper.set_library(str(config.ESPEAK_LIBRARY))
        EspeakWrapper.set_data_path(str(config.ESPEAK_DATA))
    except Exception as exc:
        raise _format_error(
            etapa="configuração do eSpeak NG",
            mensagem="Falha ao configurar EspeakWrapper.",
            causa=str(exc),
            arquivo="modules/voz_teste/tts.py",
            correcao="Verifique a instalação do eSpeak NG e do pacote phonemizer-fork.",
        ) from exc


def _as_float32_array(audio):
    try:
        import numpy as np
    except ImportError as exc:
        raise _format_error(
            etapa="conversão de áudio",
            mensagem="NumPy não está instalado.",
            causa=str(exc),
            arquivo="modules/voz_teste/requirements.txt",
            correcao="Execute: python -m pip install -r modules/voz_teste/requirements.txt",
        ) from exc

    try:
        if hasattr(audio, "detach"):
            audio = audio.detach().cpu().numpy()
        return np.asarray(audio, dtype="float32")
    except Exception as exc:
        raise _format_error(
            etapa="conversão de áudio",
            mensagem="Formato de áudio inesperado retornado pelo Kokoro.",
            causa=f"{type(audio)!r}: {exc}",
            arquivo="modules/voz_teste/tts.py",
            correcao="Atualize kokoro e torch conforme requirements.txt.",
        ) from exc


def _join_audio(chunks: Iterable):
    try:
        import numpy as np
    except ImportError as exc:
        raise _format_error(
            etapa="junção de áudio",
            mensagem="NumPy não está instalado.",
            causa=str(exc),
            arquivo="modules/voz_teste/requirements.txt",
            correcao="Execute: python -m pip install -r modules/voz_teste/requirements.txt",
        ) from exc

    arrays = [_as_float32_array(chunk) for chunk in chunks]
    if not arrays:
        raise _format_error(
            etapa="geração de áudio",
            mensagem="Kokoro não retornou trechos de áudio.",
            causa="O pipeline gerou zero chunks para o texto informado.",
            arquivo="modules/voz_teste/config.py",
            correcao=f"Confirme VOICE={config.VOICE!r} e LANG_CODE={config.LANG_CODE!r}.",
        )

    return arrays[0] if len(arrays) == 1 else np.concatenate(arrays)


def _get_pipeline():
    """Inicializa o KPipeline uma única vez por processo."""

    global _PIPELINE

    if _PIPELINE is not None:
        return _PIPELINE

    _configure_espeak_paths()

    try:
        kokoro = import_module("kokoro")
    except ImportError as exc:
        raise _format_error(
            etapa="carregamento do motor TTS",
            mensagem="Pacote kokoro não encontrado.",
            causa=str(exc),
            arquivo="modules/voz_teste/requirements.txt",
            correcao="Execute: python -m pip install -r modules/voz_teste/requirements.txt",
        ) from exc

    # misaki/espeak.py sobrescreve EspeakWrapper com espeakng_loader no import.
    _configure_espeak_paths()

    try:
        import_module("torch")
    except ImportError as exc:
        raise _format_error(
            etapa="carregamento do motor TTS",
            mensagem="PyTorch não encontrado.",
            causa=str(exc),
            arquivo="modules/voz_teste/requirements.txt",
            correcao="Execute: python -m pip install -r modules/voz_teste/requirements.txt",
        ) from exc

    if config.LANG_CODE != "p":
        raise _format_error(
            etapa="validação de configuração",
            mensagem="LANG_CODE inválido para este módulo.",
            causa=f"Recebido {config.LANG_CODE!r}, esperado 'p' (PT-BR).",
            arquivo="modules/voz_teste/config.py",
            correcao="Defina LANG_CODE = 'p'.",
        )

    if config.VOICE not in config.VOZES_PT_BR:
        raise _format_error(
            etapa="validação de configuração",
            mensagem="Voz PT-BR não suportada.",
            causa=f"VOICE={config.VOICE!r} não está em {config.VOZES_PT_BR}.",
            arquivo="modules/voz_teste/config.py",
            correcao="Use pf_dora, pm_alex ou pm_santa.",
        )

    try:
        _PIPELINE = kokoro.KPipeline(lang_code=config.LANG_CODE, repo_id=config.MODEL_REPO)
    except Exception as exc:
        raise _format_error(
            etapa="inicialização do KPipeline",
            mensagem="Falha ao criar KPipeline.",
            causa=str(exc),
            arquivo="modules/voz_teste/tts.py",
            correcao=(
                "No Windows, confirme o eSpeak NG em C:\\Program Files\\eSpeak NG. "
                "O misaki pode sobrescrever o EspeakWrapper com espeakng_loader."
            ),
        ) from exc

    return _PIPELINE


def _get_sounddevice():
    global _SOUNDEVICE

    if _SOUNDEVICE is not None:
        return _SOUNDEVICE

    try:
        _SOUNDEVICE = import_module("sounddevice")
    except ImportError as exc:
        raise _format_error(
            etapa="reprodução de áudio",
            mensagem="Pacote sounddevice não encontrado.",
            causa=str(exc),
            arquivo="modules/voz_teste/requirements.txt",
            correcao="Execute: python -m pip install sounddevice",
        ) from exc

    return _SOUNDEVICE


def gerar_audio(texto: str):
    """Converte texto em array numpy float32 (24 kHz)."""

    if not texto or not texto.strip():
        raise _format_error(
            etapa="geração de áudio",
            mensagem="Texto vazio.",
            causa="Nenhum conteúdo foi informado para síntese.",
            arquivo="modules/voz_teste/tts.py",
            correcao="Passe uma frase com conteúdo para gerar_audio() ou falar().",
        )

    pipeline = _get_pipeline()

    try:
        generator = pipeline(
            texto,
            voice=config.VOICE,
            speed=config.SPEED,
            split_pattern=r"\n+",
        )
        chunks = []
        for _graphemes, _phonemes, audio in generator:
            chunks.append(audio)
        return _join_audio(chunks)
    except TTSError:
        raise
    except Exception as exc:
        raise _format_error(
            etapa="geração de áudio",
            mensagem="Falha durante a inferência do Kokoro.",
            causa=str(exc),
            arquivo="modules/voz_teste/config.py",
            correcao="Verifique conexão (download do modelo), voz e dependências.",
        ) from exc


def salvar_audio(texto: str, caminho: str | Path) -> Path:
    """Gera áudio e salva em arquivo WAV."""

    try:
        from scipy.io import wavfile
    except ImportError as exc:
        raise _format_error(
            etapa="salvar áudio",
            mensagem="SciPy não está instalado.",
            causa=str(exc),
            arquivo="modules/voz_teste/requirements.txt",
            correcao="Execute: python -m pip install scipy",
        ) from exc

    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)

    audio = gerar_audio(texto)
    wavfile.write(str(destino), config.SAMPLE_RATE, audio)
    return destino


def falar(texto: str) -> None:
    """Gera áudio e reproduz no dispositivo padrão do sistema."""

    audio = gerar_audio(texto)
    sd = _get_sounddevice()

    try:
        sd.play(audio, config.SAMPLE_RATE)
        sd.wait()
    except Exception as exc:
        raise _format_error(
            etapa="reprodução de áudio",
            mensagem="Falha ao reproduzir no dispositivo de saída.",
            causa=str(exc),
            arquivo="modules/voz_teste/tts.py",
            correcao="Verifique o dispositivo de som padrão do Windows e reinstale sounddevice.",
        ) from exc
