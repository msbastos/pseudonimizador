# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Restaurar pela janela: DOCX (mapa pelo identificador ou escolhido) e texto colado."""
import _base  # noqa: F401
import fabrica as F
from _web import ServidorDeTeste
from pseudonimizador.leitura import ler
from pseudonimizador.motor.trocas import aplicar_trocas
from pseudonimizador.revisao import Revisao
from pseudonimizador.saida import gerar


def _gerado(s):
    doc = ler(F.contrato_docx(s.pasta / "contrato.docx"))
    res = Revisao(doc).fechar()
    g = gerar(doc, res, formato="layout", modo="reversivel",
              pasta_saida=s.pasta / "Base" / "Saida", pasta_mapas=s.pasta / "Base" / "Mapas")
    return doc, res, g


def test_restaurar_docx_pela_janela():
    import docx
    with ServidorDeTeste("web_rest") as s:
        doc, res, g = _gerado(s)
        status, m = s.get("/api/mapas")
        assert status == 200 and [x["id"] for x in m["mapas"]] == [g.mapa.stem]
        assert len(m["mapas"][0]["data"]) == 16 and set(m["mapas"][0]) == {"id", "data"}
        status, r = s.enviar_arquivo(g.saida, rota="/api/restaurar/docx")
        assert status == 200 and r["trocas"] > 0 and r["saida_nome"] == "contrato - pseudonimizado - restaurado.docx", r
        assert ler(s.pasta / "Base" / "Saida" / r["saida_nome"]).texto == doc.texto
        status, r2 = s.enviar_arquivo(g.saida, rota="/api/restaurar/docx")
        assert r2["saida_nome"] == "contrato - pseudonimizado - restaurado (2).docx"
        # DOCX sem identificador: pede o mapa; com X-Mapa, restaura
        sem_id = s.pasta / "sem_id.docx"
        d2 = docx.Document(str(g.saida))
        d2.core_properties.identifier = ""
        d2.save(str(sem_id))
        status, r3 = s.enviar_arquivo(sem_id, rota="/api/restaurar/docx")
        assert status == 409 and r3["erro"] == "mapa"
        status, r4 = s.enviar_arquivo(sem_id, rota="/api/restaurar/docx", cabecalhos={"X-Mapa": g.mapa.stem})
        assert status == 200 and r4["saida_nome"] == "sem_id - restaurado.docx"
        status, r5 = s.enviar_arquivo(sem_id, rota="/api/restaurar/docx", cabecalhos={"X-Mapa": "nao-existe"})
        assert status == 404 and r5["erro"] == "mapa"
        assert s.enviar_arquivo(sem_id, rota="/api/restaurar/docx", cabecalhos={"X-Mapa": "../x"})[0] == 400
        assert s.enviar_arquivo(g.mapa, rota="/api/restaurar/docx")[0] == 415
        quebrado = s.pasta / "quebrado.docx"
        quebrado.write_bytes(b"nao e docx")
        status, r6 = s.enviar_arquivo(quebrado, rota="/api/restaurar/docx")
        assert status == 409 and r6["erro"] == "arquivo"
        assert not list((s.pasta / "estado" / "tmp").iterdir())
    log = s.log_texto()
    assert "restaura" in log and F.PESSOA_1 not in log and "contrato" not in log


def test_restaurar_docx_valida_o_nome_como_o_upload():
    with ServidorDeTeste("web_rest3") as s:
        doc, res, g = _gerado(s)
        for nome in ("a" * 150 + ".docx", "a<b.docx", "con.docx", "a.docx.", "a\x01.docx", "x?.docx"):
            status, e = s.enviar_arquivo(g.saida, rota="/api/restaurar/docx", nome=nome)
            assert status == 400 and e["erro"] == "nome", (nome, status, e)
        assert not list((s.pasta / "Base" / "Saida").glob("*restaurado*"))
        assert not list((s.pasta / "estado" / "tmp").iterdir())


def test_identificador_hostil_nao_le_fora_dos_mapas():
    import docx
    with ServidorDeTeste("web_rest4") as s:
        doc, res, g = _gerado(s)
        (s.pasta / "Base" / "fora.json").write_text('{"tokens": {}}', encoding="utf-8")
        hostil = s.pasta / "hostil.docx"
        d = docx.Document(str(g.saida))
        d.core_properties.identifier = "pseudonimizador:..\\fora"
        d.save(str(hostil))
        status, e = s.enviar_arquivo(hostil, rota="/api/restaurar/docx")
        assert status == 409 and e["erro"] == "mapa", (status, e)
        d.core_properties.identifier = "pseudonimizador:../fora"
        d.save(str(hostil))
        assert s.enviar_arquivo(hostil, rota="/api/restaurar/docx")[0] == 409


def test_mapa_corrompido_da_409_e_erro_de_gravacao_nao_e_docx_invalido():
    import docx
    with ServidorDeTeste("web_rest5") as s:
        doc, res, g = _gerado(s)
        for conteudo in ("{nao json", "[1, 2]", '{"tokens": 3}'):
            g.mapa.write_text(conteudo, encoding="utf-8")
            status, e = s.post("/api/restaurar/texto", {"texto": "[[PESSOA_1]]", "mapa": g.mapa.stem})
            assert status == 409 and e["erro"] == "mapa" and "corrompido" in e["mensagem"], (conteudo, status, e)
            status, e = s.enviar_arquivo(g.saida, rota="/api/restaurar/docx")
            assert status == 409 and e["erro"] == "mapa" and "corrompido" in e["mensagem"], (conteudo, status, e)
            status, e = s.enviar_arquivo(g.saida, rota="/api/restaurar/docx", cabecalhos={"X-Mapa": g.mapa.stem})
            assert status == 409 and e["erro"] == "mapa", (status, e)
        assert not list((s.pasta / "estado" / "tmp").iterdir())


def test_falha_de_gravacao_da_restauracao_da_409_arquivo():
    import pseudonimizador.web.servidor as W
    original = W.restaurar_docx

    def quebrada(*a, **k):
        raise PermissionError("sem espaço")
    with ServidorDeTeste("web_rest6") as s:
        doc, res, g = _gerado(s)
        W.restaurar_docx = quebrada
        try:
            status, e = s.enviar_arquivo(g.saida, rota="/api/restaurar/docx")
        finally:
            W.restaurar_docx = original
        assert status == 409 and e["erro"] == "arquivo" and "gravar" in e["mensagem"], (status, e)
        W.restaurar_docx = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("bug"))
        try:
            status, e = s.enviar_arquivo(g.saida, rota="/api/restaurar/docx")
        finally:
            W.restaurar_docx = original
        assert status == 500, (status, e)


def test_restaurar_texto_e_token_orfao():
    with ServidorDeTeste("web_rest2") as s:
        doc, res, g = _gerado(s)
        protegido = aplicar_trocas(doc.texto, res.trocas)
        status, r = s.post("/api/restaurar/texto", {"texto": protegido, "mapa": g.mapa.stem})
        assert status == 200 and r["texto"] == doc.texto
        status, e = s.post("/api/restaurar/texto", {"texto": "resposta citando [[PESSOA_99]]", "mapa": g.mapa.stem})
        assert status == 409 and e["erro"] == "orfao" and "[[PESSOA_99]]" in e["mensagem"]
        assert s.post("/api/restaurar/texto", {"texto": protegido})[0] == 400
        assert s.post("/api/restaurar/texto", {"texto": "   ", "mapa": g.mapa.stem})[0] == 400
        assert s.post("/api/restaurar/texto", {"texto": protegido, "mapa": "nao-existe"})[0] == 404


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
