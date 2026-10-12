# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Servidor local: token, Host, cabeçalhos de segurança, estáticos, estado,
abertura por segredo e encerramento."""
import _base  # noqa: F401
import time
import urllib.error
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


def test_encerrar_por_segredo_recusa_se_ha_revisao_pendente():
    """Substituição de versão: com documento em revisão/erro/lendo/gerando o /encerrar
    do segredo responde 409 e NÃO deixa pedido pendente; pronto não conta."""
    from pathlib import Path
    from pseudonimizador.web.registro import Doc
    with ServidorDeTeste("web_srv_subst", vigia_s=0.1) as s:
        reg = s.app.registro
        for sit in ("revisao", "erro", "lendo", "gerando"):
            reg._docs["a" * 16] = Doc("a" * 16, "x.docx", "janela", Path("x.docx"), situacao=sit)
            status, r = s.post("/encerrar", {"segredo": s.app.segredo}, token=False)
            assert status == 409 and r["erro"] == "ocupado", (sit, status, r)
            assert not s.app.encerrar_pedido and s.thread.is_alive()
        reg._docs["a" * 16] = Doc("a" * 16, "x.docx", "janela", Path("x.docx"), situacao="pronto")
        status, r = s.post("/encerrar", {"segredo": s.app.segredo}, token=False)
        assert status == 200 and r["ok"] and s.app.encerrar_pedido
        s.thread.join(5)
        assert not s.thread.is_alive()


def test_nao_ascii_no_token_e_no_segredo_da_403_nao_500():
    with ServidorDeTeste("web_srv7") as s:
        # http.client só envia latin-1 nos cabeçalhos: "é" chega como o byte 0xE9
        status, r = s.get("/api/estado", token="é")
        assert status == 403 and r["erro"] == "token", (status, r)
        status, r = s.post("/abrir", {"segredo": "é"}, token=False)
        assert status == 403 and r["erro"] == "segredo", (status, r)
        status, r = s.post("/encerrar", {"segredo": "日本"}, token=False)
        assert status == 403, (status, r)


def test_host_errado_ou_ausente_e_recusado_em_tudo():
    import http.client
    with ServidorDeTeste("web_srv8") as s:
        mau = f"exemplo.com.br:{s.porta}"
        for caminho in ("/", "/estatico/app.css"):
            assert s.get(caminho, token=False, host=mau)[0] == 403, caminho
        assert s.post("/abrir", {"segredo": s.app.segredo}, token=False, host=mau)[0] == 403
        assert s.post("/encerrar", {"segredo": s.app.segredo}, token=False, host=mau)[0] == 403
        assert not s.app.encerrar_pedido
        con = http.client.HTTPConnection("127.0.0.1", s.porta, timeout=10)
        con.putrequest("GET", "/api/estado", skip_host=True)      # sem cabeçalho Host
        con.putheader("X-Token", s.token)
        con.endheaders()
        assert con.getresponse().status == 403
        con.close()


def test_corpo_de_abrir_texto_simples_ou_grande_demais():
    import http.client
    with ServidorDeTeste("web_srv9") as s:
        status, r = s.pedir("POST", "/abrir", b"x", {"Content-Type": "text/plain"}, token=False)
        assert status == 400 and r["erro"] == "corpo", (status, r)
        con = http.client.HTTPConnection("127.0.0.1", s.porta, timeout=10)
        con.putrequest("POST", "/abrir")
        con.putheader("Content-Type", "application/json")
        con.putheader("Content-Length", str(3 * 1024 * 1024))     # acima de LIMITE_JSON, corpo nunca enviado
        con.endheaders()
        assert con.getresponse().status == 413
        con.close()


def test_toda_resposta_leva_referrer_policy():
    with ServidorDeTeste("web_srv10") as s:
        for metodo, caminho, com_token in (("GET", "/", False), ("GET", "/estatico/app.css", False),
                                           ("GET", "/api/estado", True), ("GET", "/api/estado", False),
                                           ("GET", "/nada", False), ("PUT", "/api/estado", True)):
            req = urllib.request.Request(f"http://127.0.0.1:{s.porta}{caminho}", method=metodo,
                                         headers={"X-Token": s.token} if com_token else {})
            try:
                resp = urllib.request.urlopen(req, timeout=10)
            except urllib.error.HTTPError as e:
                resp = e
            assert resp.headers["Referrer-Policy"] == "no-referrer", (metodo, caminho, resp.status)
            resp.close()


def test_recusa_4xx_com_corpo_pendente_nao_derruba_a_conexao():
    """Corpo até o limite JSON é lido e descartado antes da recusa (no Windows, fechar com
    corpo não lido manda RST); acima do limite, não se espera por ele."""
    with ServidorDeTeste("web_srv_drena") as s:
        mau = f"exemplo.com.br:{s.porta}"
        corpo = b"{" + b" " * (1024 * 1024) + b"}"
        for _ in range(25):
            assert s.pedir("POST", "/abrir", corpo, {"Content-Type": "application/json"},
                           token=False, host=mau)[0] == 403
            assert s.pedir("POST", "/api/documentos", corpo, {"Content-Type": "application/json"},
                           token="errado")[0] == 403
            assert s.pedir("PUT", "/api/estado", corpo, {"Content-Type": "application/json"})[0] == 405


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
