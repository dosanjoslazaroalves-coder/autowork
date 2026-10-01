from __future__ import annotations

from threading import Event
from types import SimpleNamespace

from core.estados import Estado
from core.servico_api import ServicoApi


class _FakeOrquestrador:
    def __init__(self) -> None:
        self.estado = Estado.IDLE
        self.started = Event()
        self.stopped = Event()
        self._captura = SimpleNamespace(_microfone=None)
        self.gerenciador_tarefas = SimpleNamespace(snapshot=lambda: {})
        self.agendador = SimpleNamespace(listar=lambda: [])
        self.fila_execucao = SimpleNamespace(tamanho=lambda: 0)
        self.contexto_execucao = SimpleNamespace(snapshot=lambda: {})

    def _set_estado(self, estado: Estado) -> None:
        self.estado = estado

    def inicializar(self) -> None:
        self._set_estado(Estado.IDLE)

    def executar_loop(self) -> None:
        self.started.set()
        while not self.stopped.wait(0.01):
            pass

    def parar(self) -> None:
        self.stopped.set()


def test_hud_inicia_um_unico_ciclo_de_voz(monkeypatch) -> None:
    servico = ServicoApi(tts_enabled=False)
    orquestrador = _FakeOrquestrador()
    monkeypatch.setattr(servico, "_obter_orquestrador", lambda: orquestrador)

    inicial = servico.start_voice()
    assert inicial["voice_running"] is True
    assert orquestrador.started.wait(1)

    segundo = servico.start_voice()
    assert segundo["voice_running"] is True

    final = servico.stop_voice()
    assert final["voice_running"] is False
    assert orquestrador.stopped.is_set()


def test_status_expoe_transcricao_e_nivel_de_audio() -> None:
    servico = ServicoApi(tts_enabled=False)
    servico._ouvinte.ao_transcricao("work, abra o chrome")
    servico._ouvinte.ao_nivel(0.75)

    status = servico.status()
    assert status["last_transcript"] == "work, abra o chrome"
    assert status["audio_level"] == 0.75
