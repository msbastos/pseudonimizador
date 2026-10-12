# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Nenhuma conexão de rede fora de 127.0.0.1/::1 durante o fluxo inteiro,
inclusive o OCR (spec §9)."""
import _base  # noqa: F401
import socket

LOCAIS = {"127.0.0.1", "::1", "localhost"}
_tentativas: list[str] = []
_connect_original = socket.socket.connect
_create_original = socket.create_connection
_getaddrinfo_original = socket.getaddrinfo


def _host(endereco):
    return endereco[0] if isinstance(endereco, tuple) else str(endereco)


def _connect(self, endereco):
    if _host(endereco) not in LOCAIS:
        _tentativas.append(_host(endereco))
        raise OSError("rede bloqueada no teste")
    return _connect_original(self, endereco)


def _create(endereco, *a, **k):
    if _host(endereco) not in LOCAIS:
        _tentativas.append(_host(endereco))
        raise OSError("rede bloqueada no teste")
    return _create_original(endereco, *a, **k)


def _getaddrinfo(host, *a, **k):
    if host not in LOCAIS and host is not None:
        _tentativas.append(str(host))
        raise OSError("rede bloqueada no teste")
    return _getaddrinfo_original(host, *a, **k)


def test_fluxo_completo_sem_rede():
    socket.socket.connect = _connect
    socket.create_connection = _create
    socket.getaddrinfo = _getaddrinfo
    try:
        import fabrica as F
        from pseudonimizador.leitura import ler
        from pseudonimizador.revisao import Revisao
        from pseudonimizador.saida import gerar
        pasta = F.pasta_temporaria("sem_rede")
        for arq in (F.contrato_docx(pasta / "a.docx"), F.contrato_escaneado(pasta / "b.pdf")):
            doc = ler(arq)
            gerar(doc, Revisao(doc).fechar(), formato="layout", modo="reversivel",
                  pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    finally:
        socket.socket.connect = _connect_original
        socket.create_connection = _create_original
        socket.getaddrinfo = _getaddrinfo_original
    assert not _tentativas, f"tentativas de rede: {_tentativas}"


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
