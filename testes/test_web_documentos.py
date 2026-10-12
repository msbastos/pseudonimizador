# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""API de documentos: upload cru, lista, detalhe, decisão, acrescentar e descartar."""
import _base  # noqa: F401
import http.client

import fabrica as F
from _web import ServidorDeTeste


def test_upload_lista_detalhe_decisao_acrescentar_descartar():
    with ServidorDeTeste("web_docs") as s:
        arq = F.contrato_docx(s.pasta / "contrato.docx")
        status, r = s.enviar_arquivo(arq)
        assert status == 202 and r["situacao"] == "lendo" and r["nome"] == "contrato.docx", r
        id_ = r["id"]
        d = s.esperar(id_, "revisao")
        assert d["origem"] == "janela" and d["revisavel"] and isinstance(d["avisos"], list)
        valores = {it["valor"] for it in d["itens"]}
        assert F.PESSOA_1 in valores and F.CPF in valores
        item = next(it for it in d["itens"] if it["valor"] == F.EMAIL)
        assert item["aceito"] and item["ocorrencias"] >= 1 and 1 <= len(item["contextos"]) <= 3
        assert s.post(f"/api/documentos/{id_}/decisao", {"categoria": "email", "valor": F.EMAIL, "aceito": False})[0] == 200
        status, d = s.get(f"/api/documentos/{id_}")
        assert not next(it for it in d["itens"] if it["valor"] == F.EMAIL)["aceito"]
        status, e = s.post(f"/api/documentos/{id_}/decisao", {"categoria": "email", "valor": F.EMAIL, "aceito": "sim"})
        assert status == 400 and e["erro"] == "corpo"
        status, e = s.post(f"/api/documentos/{id_}/decisao", {"categoria": "pessoa", "valor": "Ninguém Assim", "aceito": True})
        assert status == 404 and e["erro"] == "item"
        status, a = s.post(f"/api/documentos/{id_}/acrescentar", {"valor": "Porto Alegre", "categoria": "outro"})
        assert status == 200 and a["item"]["acrescido"] and a["item"]["ocorrencias"] == 1
        status, e = s.post(f"/api/documentos/{id_}/acrescentar", {"valor": "texto que não existe", "categoria": "outro"})
        assert status == 409 and "não encontrado" in e["mensagem"]
        status, e = s.post(f"/api/documentos/{id_}/acrescentar", {"valor": "Porto Alegre", "categoria": "x"})
        assert status == 409
        status, lista = s.get("/api/documentos")
        assert [x["id"] for x in lista["documentos"]] == [id_] and lista["documentos"][0]["situacao"] == "revisao"
        assert (s.pasta / "estado" / "tmp" / id_ / "contrato.docx").is_file()
        assert s.delete(f"/api/documentos/{id_}")[0] == 200
        assert not (s.pasta / "estado" / "tmp" / id_).exists()
        assert s.get(f"/api/documentos/{id_}")[0] == 404
        status, e = s.delete(f"/api/documentos/{id_}")
        assert status == 404 and e["erro"] == "documento"
        assert s.post(f"/api/documentos/{id_}/decisao", {"aceito": True})[1]["erro"] == "documento"
        assert s.get("/api/documentos")[1]["documentos"] == []


def test_upload_grande_ou_de_outro_formato_e_recusado():
    """Review Focus 1: arquivo enorme ou de outro formato arrastado à janela."""
    with ServidorDeTeste("web_docs2") as s:
        status, r = s.pedir("POST", "/api/documentos", b"abc", {"X-Nome-Arquivo": "notas.txt"})
        assert status == 415 and r["erro"] == "formato"
        status, r = s.pedir("POST", "/api/documentos", b"", {"X-Nome-Arquivo": "a.docx"})
        assert status == 400
        status, r = s.pedir("POST", "/api/documentos", b"abc")
        assert status == 400 and r["erro"] == "nome"
        # 101 MB anunciados, corpo nunca enviado: a recusa vem antes de ler
        con = http.client.HTTPConnection("127.0.0.1", s.porta, timeout=30)
        con.putrequest("POST", "/api/documentos")
        con.putheader("X-Token", s.token)
        con.putheader("X-Nome-Arquivo", "grande.pdf")
        con.putheader("Content-Length", str(101 * 1024 * 1024))
        con.endheaders()
        resp = con.getresponse()
        assert resp.status == 413
        con.close()
        assert not any((s.pasta / "estado" / "tmp").iterdir())
        # nome com pasta e codificado: fica só o nome do arquivo
        status, r = s.enviar_arquivo(F.contrato_docx(s.pasta / "c.docx"), nome="..\\..\\Contrato Ação.docx")
        assert status == 202 and r["nome"] == "Contrato Ação.docx"
        s.esperar(r["id"], "revisao", "erro")


def test_nome_invalido_e_estado_errado_dao_4xx_nunca_500():
    from urllib.parse import quote
    with ServidorDeTeste("web_docs4") as s:
        for ruim in ("a<b.docx", 'a"b.pdf', "a|b.docx", "a?b.docx", "a*b.pdf", "a\x01b.docx"):     # "a:b" vira "b" em Path.name no Windows: sem risco
            status, r = s.pedir("POST", "/api/documentos", b"abc", {"X-Nome-Arquivo": quote(ruim)})
            assert status == 400 and r["erro"] == "nome", (ruim, status, r)
        assert not any((s.pasta / "estado" / "tmp").iterdir())
        status, r = s.enviar_arquivo(F.contrato_docx(s.pasta / "c.docx"))
        id_ = r["id"]
        s.esperar(id_, "revisao")
        s.app.registro.obter(id_).situacao = "gerando"           # simula a geração em curso
        status, e = s.post(f"/api/documentos/{id_}/decisao", {"categoria": "email", "valor": F.EMAIL, "aceito": False})
        assert status == 409 and e["erro"] == "situacao", (status, e)
        status, e = s.post(f"/api/documentos/{id_}/acrescentar", {"valor": "Porto Alegre", "categoria": "outro"})
        assert status == 409 and e["erro"] == "situacao", (status, e)
        s.app.registro.obter(id_).situacao = "revisao"
        s.app.registro.encerrar(timeout=30)                       # depois do encerramento, o upload é recusado
        status, e = s.pedir("POST", "/api/documentos", b"abc", {"X-Nome-Arquivo": "a.docx"})
        assert status == 503 and e["erro"] == "encerrando", (status, e)


def test_nomes_longos_reservados_e_sem_tamanho_dao_400():
    from urllib.parse import quote
    with ServidorDeTeste("web_docs5") as s:
        ruins = ["a" * 300 + ".docx", "con.docx", "NUL.pdf", "Com1.docx", "lpt9.tar.docx", "CONIN$.docx",
                 "CONOUT$.pdf", "aux.x.pdf", "a.docx.", "a.docx ", "PRN .docx"]
        for ruim in ruins:
            status, r = s.pedir("POST", "/api/documentos", b"abc", {"X-Nome-Arquivo": quote(ruim)})
            assert status in (400, 415) and (status == 415 or r["erro"] == "nome"), (ruim[:20], status, r)
        for ruim in ("a" * 300 + ".docx", "con.docx", "NUL.pdf", "lpt9.tar.docx", "CONIN$.docx"):
            status, r = s.pedir("POST", "/api/documentos", b"abc", {"X-Nome-Arquivo": quote(ruim)})
            assert status == 400 and r["erro"] == "nome", (ruim[:20], status, r)
        assert s.pedir("POST", "/api/documentos", b"abc", {"X-Nome-Arquivo": "comum.docx"})[0] == 202
        assert not [p for p in (s.pasta / "estado" / "tmp").iterdir() if p.is_file()]
        # sem Content-Length (corpo em pedaços)
        con = http.client.HTTPConnection("127.0.0.1", s.porta, timeout=30)
        con.putrequest("POST", "/api/documentos")
        con.putheader("X-Token", s.token)
        con.putheader("X-Nome-Arquivo", "b.docx")
        con.putheader("Transfer-Encoding", "chunked")
        con.endheaders()
        con.send(b"3\r\nabc\r\n0\r\n\r\n")
        resp = con.getresponse()
        assert resp.status == 400 and "não informado" in resp.read().decode("utf-8")
        con.close()
        status, r = s.pedir("POST", "/api/documentos", b"", {"X-Nome-Arquivo": "a.docx"})
        assert status == 400 and "vazio" in r["mensagem"]


def test_log_nunca_leva_nome_de_arquivo_nem_valores():
    with ServidorDeTeste("web_docs3") as s:
        arq = F.contrato_docx(s.pasta / f"{F.PESSOA_2}.docx")
        status, r = s.enviar_arquivo(arq)
        s.esperar(r["id"], "revisao")
        s.post(f"/api/documentos/{r['id']}/decisao", {"categoria": "cpf", "valor": F.CPF, "aceito": False})
        s.post(f"/api/documentos/{r['id']}/acrescentar", {"valor": "Porto Alegre", "categoria": "outro"})
        s.delete(f"/api/documentos/{r['id']}")
    log = s.log_texto()
    assert r["id"] in log and "registrado" in log and "descartado" in log
    for proibido in (F.PESSOA_1, F.PESSOA_2, "Souza", F.CPF, F.EMAIL, "Porto Alegre", ".docx"):
        assert proibido not in log, proibido


def test_nome_longo_e_recusado_antes_de_ler_o_corpo():
    """Nome com mais de 150 caracteres: 400 "nome" já pelo cabeçalho, mesmo com
    corpo anunciado grande (que nem chega a ser lido)."""
    import http.client
    from urllib.parse import quote
    with ServidorDeTeste("web_nome_longo") as s:
        nome = quote("a" * 151 + ".docx")
        con = http.client.HTTPConnection("127.0.0.1", s.porta, timeout=20)
        con.putrequest("POST", "/api/documentos")
        for k, v in (("X-Token", s.token), ("X-Nome-Arquivo", nome), ("Content-Length", str(50 * 1024 * 1024)),
                     ("Content-Type", "application/octet-stream")):
            con.putheader(k, v)
        con.endheaders()
        r = con.getresponse()
        corpo = r.read()
        con.close()
        assert r.status == 400 and b'"nome"' in corpo, (r.status, corpo)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
