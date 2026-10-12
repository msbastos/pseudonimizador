# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fabrica as F
from pseudonimizador.leitura.modelo import OrigemPdf
from pseudonimizador.leitura.pdf_ import ler_pdf


def test_pdf_com_texto():
    d = ler_pdf(F.contrato_pdf(F.pasta_temporaria("leitura_pdf") / "c.pdf"))
    assert d.tipo == "pdf_texto" and d.paginas_ocr == []
    assert F.PESSOA_1 in d.texto and F.CPF in d.texto and "LOCATÁRIA" in d.texto
    assert len(d.origens) == len(d.texto)
    o = d.origens[d.texto.index(F.CPF)]
    assert isinstance(o, OrigemPdf) and o.pagina == 0 and not o.ocr
    x0, y0, x1, y1 = o.rect
    assert x1 > x0 and y1 > y0


def test_escaneado_sem_ocr_gera_aviso():
    d = ler_pdf(F.contrato_escaneado(F.pasta_temporaria("leitura_pdf2") / "e.pdf"))
    assert d.texto.strip() == ""
    assert any("sem texto" in a for a in d.avisos)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
