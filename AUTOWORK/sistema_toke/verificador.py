"""Módulo Verificador — inspeção de estado do Windows para confirmação real de ações.

Princípios:
    - Nunca assumir sucesso sem evidência real.
    - Fechar só se o HWND deixou de existir. Perda de foco não é fechamento.
    - Sem user32: observado=None, nunca True.
"""
from __future__ import annotations

import ctypes
import logging
import time
from dataclasses import dataclass
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

CLASSES_DESKTOP = frozenset({
    "Progman",
    "WorkerW",
    "Shell_TrayWnd",
    "Shell_SecondaryTrayWnd",
})

TITULOS_DESKTOP = frozenset({
    "Program Manager",
    "",
})

CLASSES_NAVEGADOR = frozenset({
    "Chrome_WidgetWin_1",
    "Chrome_WidgetWin_2",
    "MozillaWindowClass",
    "IEFrame",
    "OperaWindowClass",
})

PALAVRAS_NAVEGADOR = (
    "chrome",
    "firefox",
    "edge",
    "opera",
    "brave",
    "navegador",
    "mozilla",
)


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


@dataclass
class JanelaInfo:
    """Informações de uma janela do Windows."""
    hwnd: int
    titulo: str
    classe: str
    eh_desktop: bool
    maximizada: bool = False
    minimizada: bool = False
    rect: Optional[Tuple[int, int, int, int]] = None

    def __str__(self) -> str:
        origem = "Desktop" if self.eh_desktop else "Janela"
        return f"[{origem}] hwnd={self.hwnd} titulo={self.titulo!r} classe={self.classe!r}"


def _obter_user32():
    try:
        return ctypes.windll.user32
    except (AttributeError, OSError):
        return None


def _montar_info(user32, hwnd: int) -> Optional[JanelaInfo]:
    if not hwnd:
        return None
    tam_titulo = user32.GetWindowTextLengthW(hwnd)
    buf_titulo = ctypes.create_unicode_buffer(tam_titulo + 1)
    user32.GetWindowTextW(hwnd, buf_titulo, tam_titulo + 1)
    titulo = buf_titulo.value.strip()

    buf_classe = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf_classe, 256)
    classe = buf_classe.value.strip()

    eh_desktop = classe in CLASSES_DESKTOP or (
        titulo in TITULOS_DESKTOP and classe in CLASSES_DESKTOP
    )

    maximizada = bool(user32.IsZoomed(hwnd))
    minimizada = bool(user32.IsIconic(hwnd))

    rect = _RECT()
    rect_tuple = None
    if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        rect_tuple = (rect.left, rect.top, rect.right, rect.bottom)

    return JanelaInfo(
        hwnd=int(hwnd),
        titulo=titulo,
        classe=classe,
        eh_desktop=eh_desktop,
        maximizada=maximizada,
        minimizada=minimizada,
        rect=rect_tuple,
    )


def capturar_janela_ativa() -> Optional[JanelaInfo]:
    user32 = _obter_user32()
    if user32 is None:
        return None

    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        info = _montar_info(user32, hwnd)
        logger.debug("Verificador: janela ativa capturada: %s", info)
        return info
    except Exception as exc:
        logger.debug("Verificador: erro ao capturar janela ativa: %s", exc)
        return None


def consultar_janela(hwnd_alvo: int) -> Optional[JanelaInfo]:
    user32 = _obter_user32()
    if user32 is None:
        return None
    try:
        if not user32.IsWindow(hwnd_alvo):
            return None
        return _montar_info(user32, hwnd_alvo)
    except Exception as exc:
        logger.debug("Verificador: erro ao consultar hwnd=%s: %s", hwnd_alvo, exc)
        return None


def janela_parece_navegador(janela: Optional[JanelaInfo]) -> bool:
    if janela is None or janela.eh_desktop:
        return False
    if janela.classe in CLASSES_NAVEGADOR:
        return True
    titulo = (janela.titulo or "").lower()
    return any(palavra in titulo for palavra in PALAVRAS_NAVEGADOR)


def verificar_fechamento_janela(hwnd_alvo: int, timeout_ms: int = 800) -> Optional[bool]:
    """True se o HWND deixou de existir; False se ainda existe; None se não observável."""
    user32 = _obter_user32()
    if user32 is None:
        return None

    inicio = time.time()
    limite = timeout_ms / 1000.0

    while (time.time() - inicio) < limite:
        try:
            if not user32.IsWindow(hwnd_alvo):
                logger.debug("Verificador: hwnd=%d não é mais uma janela válida.", hwnd_alvo)
                return True
        except Exception as exc:
            logger.debug("Verificador: falha ao inspecionar hwnd=%d: %s", hwnd_alvo, exc)
            return None
        time.sleep(0.05)

    try:
        existe = bool(user32.IsWindow(hwnd_alvo))
    except Exception:
        return None

    if existe:
        logger.warning("Verificador: hwnd=%d ainda existe após comando de fechamento.", hwnd_alvo)
        return False
    return True


def esperar_foreground_diferente(hwnd_antes: int, timeout_ms: int = 700) -> Optional[bool]:
    user32 = _obter_user32()
    if user32 is None:
        return None
    inicio = time.time()
    limite = timeout_ms / 1000.0
    while (time.time() - inicio) < limite:
        try:
            atual = user32.GetForegroundWindow()
            if atual and int(atual) != int(hwnd_antes):
                return True
        except Exception:
            return None
        time.sleep(0.05)
    return False


def esperar_desktop_ativo(timeout_ms: int = 800) -> Optional[bool]:
    inicio = time.time()
    limite = timeout_ms / 1000.0
    visto = None
    while (time.time() - inicio) < limite:
        atual = capturar_janela_ativa()
        if atual is None:
            visto = None
        elif atual.eh_desktop:
            return True
        else:
            visto = False
        time.sleep(0.05)
    return visto if visto is not None else False


def esperar_titulo_compativel(
    trecho: str,
    hwnd_anterior: Optional[int] = None,
    timeout_ms: int = 2000,
) -> Optional[JanelaInfo]:
    if not trecho:
        return None
    alvo = trecho.strip().lower()
    partes = [p for p in alvo.replace("-", " ").split() if len(p) > 2]
    inicio = time.time()
    limite = timeout_ms / 1000.0
    while (time.time() - inicio) < limite:
        atual = capturar_janela_ativa()
        if atual is None:
            time.sleep(0.05)
            continue
        if hwnd_anterior is not None and atual.hwnd == hwnd_anterior and not atual.eh_desktop:
            titulo_atual = (atual.titulo or "").lower()
            if alvo not in titulo_atual and not any(p in titulo_atual for p in partes):
                time.sleep(0.05)
                continue
        titulo = (atual.titulo or "").lower()
        if alvo in titulo or any(p in titulo for p in partes):
            return atual
        time.sleep(0.05)
    return None
