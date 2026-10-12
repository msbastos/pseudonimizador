# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Gerar pela janela, resultado, abrir arquivo/pasta (injetado) e o vazamento na tela."""
import _base  # noqa: F401
from pathlib import Path

import fabrica as F
from _web import ServidorDeTeste
from pseudonimizador.leitura import ler
from pseudonimizador.saida import VazamentoDetectado


def _enviar_e_revisar(s, nome="contrato.docx"):
    status, r = s.enviar_arquivo(F.contrato_docx(s.pasta / nome))
    assert status == 202, r
    s.esperar(r["id"], "revisao")
    return r["id"]


def test_gerar_resultado_e_abrir():
    abertos = []
    with ServidorDeTeste("web_gerar", abrir_no_windows=abertos.append) as s:
        id_ = _enviar_e_revisar(s)
        status, e = s.post(f"/api/documentos/{id_}/abrir", {"alvo": "arquivo"})
        assert status == 409 and e["erro"] == "situacao"
        status, g = s.post(f"/api/documentos/{id_}/gerar", {"formato": "layout", "modo": "reversivel"})
        assert status == 202 and g["situacao"] == "gerando", g
        d = s.esperar(id_, "pronto", "erro")
        assert d["situacao"] == "pronto", d["erro"]
        r = d["resultado"]
        assert r["saida_nome"] == "contrato - pseudonimizado.docx" and r["mapa_nome"].endswith(".json")
        saida = s.pasta / "Base" / "Saida" / r["saida_nome"]
        assert saida.is_file() and (s.pasta / "Base" / "Mapas" / r["mapa_nome"]).is_file()
        assert F.PESSOA_1 not in ler(saida).texto
        assert not (s.pasta / "estado" / "tmp" / id_).exists()
        assert s.post(f"/api/documentos/{id_}/abrir", {"alvo": "arquivo"})[0] == 200
        assert s.post(f"/api/documentos/{id_}/abrir", {"alvo": "pasta"})[0] == 200
        assert abertos == [saida, saida.parent]
        assert s.post(f"/api/documentos/{id_}/abrir", {"alvo": "outro"})[0] == 400
        assert s.post(f"/api/documentos/{id_}/gerar", {"formato": "layout", "modo": "reversivel"})[0] == 409
        assert s.post(f"/api/documentos/{id_}/decisao", {"categoria": "cpf", "valor": F.CPF, "aceito": False})[0] == 409


def test_gerar_com_padroes_da_config_e_valores_invalidos():
    with ServidorDeTeste("web_gerar2") as s:
        id_ = _enviar_e_revisar(s)
        status, e = s.post(f"/api/documentos/{id_}/gerar", {"formato": "foto", "modo": "reversivel"})
        assert status == 409 and e["erro"] == "valor"
        status, e = s.post(f"/api/documentos/{id_}/gerar", {"formato": "texto", "tipo": "txt", "modo": "definitivo"})
        assert status == 409
        assert s.post("/api/documentos/0000000000000000/gerar", {})[0] == 404
        status, g = s.post(f"/api/documentos/{id_}/gerar", {})      # vazio: os padrões da config (layout, reversível)
        assert status == 202
        d = s.esperar(id_, "pronto", "erro")
        assert d["situacao"] == "pronto" and d["resultado"]["saida_nome"] == "contrato - pseudonimizado.docx"


def test_vazamento_vira_erro_na_tela_e_nao_no_log():
    """Review Focus 4: VazamentoDetectado -> situação erro com os valores só na
    tela; a revisão continua aberta e pode gerar de novo."""
    def gerar_vazando(*a, **k):
        raise VazamentoDetectado([F.PESSOA_1, F.CPF])
    with ServidorDeTeste("web_vaza", gerar=gerar_vazando) as s:
        id_ = _enviar_e_revisar(s)
        assert s.post(f"/api/documentos/{id_}/gerar", {"formato": "layout", "modo": "definitivo"})[0] == 202
        d = s.esperar(id_, "pronto", "erro")
        assert d["situacao"] == "erro" and d["erro"]["valores"] == [F.PESSOA_1, F.CPF] and d["revisavel"]
        assert d["itens"] and d["resultado"] is None
        assert s.get("/api/documentos")[1]["documentos"][0]["erro"].startswith("2 dado(s)")
        assert s.post(f"/api/documentos/{id_}/decisao", {"categoria": "cpf", "valor": F.CPF, "aceito": False})[0] == 200
        assert s.post(f"/api/documentos/{id_}/gerar", {"formato": "layout", "modo": "definitivo"})[0] == 202
        s.esperar(id_, "pronto", "erro")
    log = s.log_texto()
    assert "vazamento detectado (2 valor(es))" in log
    assert F.PESSOA_1 not in log and F.CPF not in log and "contrato" not in log


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
