# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Servidor local: token, Host, cabeçalhos de segurança, estáticos, estado,
abertura por segredo e encerramento."""
import _base  # noqa: F401
import time
import urllib.request

from _web import ServidorDeTeste
from pseudonimizador import VERSAO


def test_estado_exige_token_e_host_certos():
    with ServidorDeTeste("web_srv") as s:
        status, r = s.get("/api/estado")
        assert status == 200 and r["versao"] == VERSAO and r["ocupado"] is False and r["pastas"]["entrada"].endswith("Entrada")
        assert s.get("/api/estado", token=False)[0] == 403
        assert s.get("/api/estado", token="x" * 43)[0] == 403
        status, r = s.get("/api/estado", host=f"exemplo.com.br:{s.porta}")
        assert status == 403 and r["erro"] == "host"
        assert s.get("/api/estado", host=f"localhost:{s.porta}")[0] == 200
        assert s.get("/api/nao_existe")[0] == 404
        assert s.pedir("PUT", "/api/estado")[0] == 405
        req = urllib.request.Request(f"http://127.0.0.1:{s.porta}/api/estado", headers={"X-Token": s.token})
        with urllib.request.urlopen(req, timeout=10) as resp:
            assert resp.headers["Content-Security-Policy"] == "default-src 'self'"
            assert resp.headers["X-Content-Type-Options"] == "nosniff"
            assert resp.headers["Cache-Control"] == "no-store"
            assert "Access-Control-Allow-Origin" not in resp.headers


def test_estaticos_so_da_lista_fechada():
    with ServidorDeTeste("web_srv2") as s:
        assert s.get("/estatico/outro.js", token=False)[0] == 404
        assert s.get("/estatico/../servidor.py", token=False)[0] == 404
        assert s.get("/qualquer", token=False)[0] == 404
        status, corpo = s.get("/estatico/app.js", token=False)
        assert status in (200, 404)           # o arquivo chega na Task 8; aqui só a lista fechada


def test_abrir_com_segredo_emite_token_novo():
    with ServidorDeTeste("web_srv3") as s:
        status, r = s.post("/abrir", {"segredo": "errado"}, token=False)
        assert status == 403
        status, r = s.post("/abrir", {"segredo": s.app.segredo}, token=False)
        assert status == 200 and r["token"] and r["token"] != s.token
        assert s.get("/api/estado", token=r["token"])[0] == 200
        assert s.post("/abrir", b"nao e json", token=False)[0] == 400


def test_encerrar_espera_o_trabalho_em_curso():
    with ServidorDeTeste("web_srv4", vigia_s=0.1) as s:
        marcas = []

        def lento():
            marcas.append("ini")
            time.sleep(0.8)
            marcas.append("fim")
        s.app.registro.fila.enfileirar(lento)
        time.sleep(0.1)
        status, r = s.post("/api/encerrar")
        assert status == 200 and r["ok"]
        time.sleep(0.3)
        assert s.thread.is_alive() and marcas == ["ini"]      # ocupado: ainda não saiu
        s.thread.join(5)
        assert not s.thread.is_alive() and marcas == ["ini", "fim"] and s.servidor.encerrado


def test_encerrar_por_segredo_e_por_inatividade():
    with ServidorDeTeste("web_srv5", vigia_s=0.1) as s:
        assert s.post("/encerrar", {"segredo": "errado"}, token=False)[0] == 403
        status, r = s.post("/encerrar", {"segredo": s.app.segredo}, token=False)
        assert status == 200 and r["ok"]
        s.thread.join(5)
        assert not s.thread.is_alive()
    with ServidorDeTeste("web_srv6", inatividade_s=0.3, vigia_s=0.1) as s:
        s.thread.join(5)
        assert not s.thread.is_alive() and s.servidor.encerrado
    assert "inatividade" in s.log_texto()


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
