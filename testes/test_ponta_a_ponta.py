# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Toda combinação entrada × formato × tipo × modo: nada em claro; no
reversível com saída DOCX (layout ou só texto), a saída leva o identificador do
mapa e restaurar devolve os dados; do DOCX no layout, o original inteiro."""
import _base  # noqa: F401
import json

import docx
import fabrica as F
from pseudonimizador.leitura import ler
from pseudonimizador.restaurar import mapa_do_docx, restaurar_docx
from pseudonimizador.revisao import Revisao
from pseudonimizador.saida import gerar

COMBINACOES = [("layout", None), ("texto", "docx"), ("texto", "pdf")]


def _entradas(pasta):
    return {"docx": F.contrato_docx(pasta / "c_docx.docx"),
            "pdf": F.contrato_pdf(pasta / "c_pdf.pdf"),
            "escaneado": F.contrato_escaneado(pasta / "c_esc.pdf")}


def test_matriz_completa():
    pasta = F.pasta_temporaria("ponta")
    falhas = []
    for nome, arq in _entradas(pasta).items():
        doc = ler(arq)
        res = Revisao(doc).fechar()
        for formato, tipo in COMBINACOES:
            for modo in ("reversivel", "definitivo"):
                rotulo = f"{nome}/{formato}/{tipo}/{modo}"
                try:
                    g = gerar(doc, res, formato=formato, tipo=tipo, modo=modo,
                              pasta_saida=pasta / "Saida", pasta_mapas=pasta / "Mapas")
                except Exception as e:  # noqa: BLE001
                    falhas.append(f"{rotulo}: {e!r}")
                    continue
                texto_saida = ler(g.saida).texto
                for dado in (F.PESSOA_1, F.PESSOA_2, F.CPF, F.EMAIL):
                    if dado in texto_saida:
                        falhas.append(f"{rotulo}: '{dado}' em claro na saída")
                if (modo == "reversivel") != (g.mapa is not None):
                    falhas.append(f"{rotulo}: mapa inesperado")
                if modo == "reversivel" and g.saida.suffix == ".docx":
                    ident = docx.Document(str(g.saida)).core_properties.identifier
                    if ident != "pseudonimizador:" + json.loads(g.mapa.read_text(encoding="utf-8"))["id"]:
                        falhas.append(f"{rotulo}: identificador do mapa ausente na saída ({ident!r})")
                        continue
                    restaurado = g.saida.with_name(g.saida.stem + " restaurado.docx")
                    restaurar_docx(g.saida, restaurado, mapa_do_docx(g.saida, pasta / "Mapas"))
                    texto_restaurado = ler(restaurado).texto
                    if nome == "docx" and formato == "layout" and texto_restaurado != doc.texto:
                        falhas.append(f"{rotulo}: restauração diferente do original")
                    if nome != "escaneado" and not all(d in texto_restaurado for d in (F.PESSOA_1, F.CPF)):
                        falhas.append(f"{rotulo}: restauração sem os dados originais")
    assert not falhas, "\n".join(falhas)


def _gerar_layout_reversivel(caminho, pasta):
    doc = ler(caminho)
    res = Revisao(doc).fechar()
    g = gerar(doc, res, formato="layout", modo="reversivel",
              pasta_saida=pasta / "Saida", pasta_mapas=pasta / "Mapas")
    return ler(g.saida).texto


def test_nome_que_vira_a_pagina_nao_escapa():
    import fitz
    pasta = F.pasta_temporaria("ponta_virada")
    caminho = pasta / "virada.pdf"
    doc = fitz.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((72, 700), "Titular: Zuleiva Maria", fontname="helv", fontsize=11)
    p1.insert_text((72, 120), "Cláusula primeira do contrato sintético de teste.", fontname="helv", fontsize=11)
    p1.insert_text((72, 820), "Página 1 de 2", fontname="helv", fontsize=9)
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text((72, 100), "Fernandes, inscrita no CPF 111.444.777-35.", fontname="helv", fontsize=11)
    p2.insert_text((72, 820), "Página 2 de 2", fontname="helv", fontsize=9)
    doc.save(str(caminho))
    texto = _gerar_layout_reversivel(caminho, pasta)
    assert "Fernandes" not in texto and "Zuleiva" not in texto and "111.444.777-35" not in texto, texto
    assert "Página 1 de 2" in texto and "Página 2 de 2" in texto, texto


def test_prenome_raro_antes_do_nome_nas_assinaturas_nao_escapa():
    import fitz
    pasta = F.pasta_temporaria("ponta_prenome_raro")
    caminho = pasta / "assinaturas.pdf"
    doc = fitz.open()
    p = doc.new_page(width=595, height=842)
    p.insert_text((72, 120), "Cláusula primeira do contrato sintético de teste.", fontname="helv", fontsize=11)
    p.insert_text((72, 600), "Testemunha 1; CPF", fontname="helv", fontsize=11)
    p.insert_text((72, 616), "Zuleiva Maria Souza", fontname="helv", fontsize=11)
    p.insert_text((72, 632), "CPF: 111.444.777-35", fontname="helv", fontsize=11)
    doc.save(str(caminho))
    texto = _gerar_layout_reversivel(caminho, pasta)
    assert "Zuleiva" not in texto and "Souza" not in texto, texto
    assert "Cláusula primeira" in texto, texto


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
