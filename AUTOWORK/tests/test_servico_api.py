"""Entrada textual real e observabilidade concorrente da ponte do núcleo."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from core.orquestrador import Orquestrador
from core.servico_api import ServicoApi


def test_comando_real_publica_transcricao_resposta_e_estado():
    servico = ServicoApi(tts_enabled=False)
    inicial = servico.status()
    assert inicial['core'] == 'online'
    assert inicial['ready'] is True
    assert inicial['state'] == 'IDLE'
    assert inicial['audio_initialized'] is False
    assert isinstance(servico._obter_orquestrador(), Orquestrador)

    resultado = servico.processar_comando('  que horas são em Tóquio  ')
    assert resultado['status'] == 'sucesso'
    assert resultado['acao'] == 'consultar_horario'
    assert resultado['estado'] == 'SUCESSO'
    assert resultado['dados']['timezone'] == 'Asia/Tokyo'
    final = servico.status()
    assert final['state'] == 'IDLE'
    assert final['last_transcript'] == 'que horas são em Tóquio'
    assert final['last_response'] == resultado


def test_status_nao_espera_comando_terminar(monkeypatch):
    servico = ServicoApi(tts_enabled=False)
    orquestrador = servico._obter_orquestrador()
    processar_original = orquestrador.processar_comando
    entrou = Event()
    liberar = Event()

    def processar_com_espera(texto):
        entrou.set()
        assert liberar.wait(5), 'Teste não liberou o processamento'
        return processar_original(texto)

    monkeypatch.setattr(orquestrador, 'processar_comando', processar_com_espera)
    with ThreadPoolExecutor(max_workers=2) as executor:
        comando = executor.submit(servico.processar_comando, 'que horas são')
        try:
            assert entrou.wait(2), 'Comando não iniciou'
            status = executor.submit(servico.status).result(timeout=1)
            assert status['state'] == 'PROCESSANDO'
            assert status['last_transcript'] == 'que horas são'
            assert not comando.done()
        finally:
            liberar.set()
        assert comando.result(timeout=5)['status'] == 'sucesso'


def test_excecao_e_publicada_e_propagada(monkeypatch, caplog):
    servico = ServicoApi(tts_enabled=False)
    orquestrador = servico._obter_orquestrador()

    def falhar(_texto):
        raise RuntimeError('falha controlada do teste')

    monkeypatch.setattr(orquestrador, 'processar_comando', falhar)
    with pytest.raises(RuntimeError, match='falha controlada do teste'):
        servico.processar_comando('que horas são')
    status = servico.status()
    assert status['state'] == 'ERRO'
    assert status['last_response']['status'] == 'erro_excecao'
    assert 'Erro ao processar comando textual' in caplog.text
