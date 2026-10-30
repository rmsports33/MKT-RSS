"""pytest -p tools.pytest_offline_guard: proíbe DNS e conexões reais.
Não altera respostas simuladas. Tentativas bloqueadas são reportadas.
"""
import socket
import pytest

_attempts = []
_patch = pytest.MonkeyPatch()


def _deny(*args, **kwargs):
    _attempts.append('conexao/DNS bloqueado')
    raise OSError('rede proibida na validacao offline')


def pytest_configure(config):
    _patch.setattr(socket, 'getaddrinfo', _deny)
    _patch.setattr(socket.socket, 'connect', _deny)
    _patch.setattr(socket.socket, 'connect_ex', _deny)


def pytest_unconfigure(config):
    _patch.undo()


def pytest_terminal_summary(terminalreporter):
    terminalreporter.write_line(f'OFFLINE GUARD: conexoes permitidas=0; tentativas bloqueadas={len(_attempts)}')
