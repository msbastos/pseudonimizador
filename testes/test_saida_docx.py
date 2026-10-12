# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import zipfile

import docx
import fabrica as F
from pseudonimizador.leitura import ler
from pseudonimizador.revisao import Revisao
from pseudonimizador.saida.docx_layout import gerar_docx_layout


def _gerar():
    pasta = F.pasta_temporaria("saida_docx")
    doc = ler(F.contrato_docx(pasta / "c.docx"))
    res = Revisao(doc).fechar()
    destino = pasta / "c - pseudonimizado.docx"
    gerar_docx_layout(doc, res.trocas, destino, identificador="pseudonimizador:teste")
    return destino, res


def test_nada_em_claro_em_nenhuma_parte_do_arquivo():
    destino, _ = _gerar()
    with zipfile.ZipFile(destino) as z:
        bruto = " ".join(z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.endswith(".xml"))
    for valor in (F.PESSOA_1, F.PESSOA_2, F.CPF, F.EMAIL, "Autor Original", "Editor Sintético",
                  "Comentarista Sintético", "Conferir o CPF", "Revisor"):
        assert valor not in bruto, valor


def test_layout_preservado_e_tokens_no_lugar():
    destino, res = _gerar()
    d = ler(destino)
    assert "LOCADOR: [[PESSOA_1]], brasileira" in d.texto
    assert "Cláusula 1ª. O aluguel mensal" in d.texto
    original = docx.Document(str(destino))
    p = original.paragraphs[1]
    assert p.runs[0].text == "LOCADOR: [[PESSOA_1]]" and p.runs[1].text == "" and p.runs[1].bold
    assert original.core_properties.identifier == "pseudonimizador:teste"


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
