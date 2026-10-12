# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import docx
import fitz
import fabrica as F
from pseudonimizador.saida.texto import gerar_docx_texto, gerar_pdf_texto

TEXTO = "Primeira linha com [[PESSOA_1]].\nCláusula 2ª — acentuação: ação, côncavo."


def test_docx_texto():
    destino = F.pasta_temporaria("saida_texto") / "t.docx"
    gerar_docx_texto(TEXTO, destino)
    d = docx.Document(str(destino))
    assert [p.text for p in d.paragraphs] == TEXTO.split("\n")
    assert d.core_properties.author == ""


def test_pdf_texto():
    destino = F.pasta_temporaria("saida_texto2") / "t.pdf"
    gerar_pdf_texto(TEXTO, destino)
    with fitz.open(str(destino)) as pdf:
        extraido = "".join(p.get_text() for p in pdf)
        assert "[[PESSOA_1]]" in extraido and "côncavo" in extraido
        assert not (pdf.metadata.get("author") or "")


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
