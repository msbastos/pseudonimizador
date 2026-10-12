# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Toda combinação entrada × formato × tipo × modo: nada em claro; no
reversível com saída DOCX, restaurar devolve o original."""
import _base  # noqa: F401
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
                if modo == "reversivel" and g.saida.suffix == ".docx" and nome == "docx" and formato == "layout":
                    restaurado = g.saida.with_name(g.saida.stem + " restaurado.docx")
                    restaurar_docx(g.saida, restaurado, mapa_do_docx(g.saida, pasta / "Mapas"))
                    if ler(restaurado).texto != doc.texto:
                        falhas.append(f"{rotulo}: restauração diferente do original")
    assert not falhas, "\n".join(falhas)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
