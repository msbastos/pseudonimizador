# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import json
import zipfile

import fabrica as F
from pseudonimizador.leitura import ler
from pseudonimizador.revisao import Revisao
from pseudonimizador.saida import gerar
from pseudonimizador.saida.conferencia import VazamentoDetectado


def _preparar(nome):
    pasta = F.pasta_temporaria(nome)
    doc = ler(F.contrato_docx(pasta / "contrato.docx"))
    return pasta, doc, Revisao(doc).fechar()


def test_reversivel_grava_mapa_separado_e_identificador():
    pasta, doc, res = _preparar("gerar_rev")
    g = gerar(doc, res, formato="layout", modo="reversivel", pasta_saida=pasta / "Saida", pasta_mapas=pasta / "Mapas")
    assert g.saida.name == "contrato - pseudonimizado.docx" and g.saida.parent.name == "Saida"
    assert g.mapa and g.mapa.parent.name == "Mapas"
    mapa = json.loads(g.mapa.read_text(encoding="utf-8"))
    import docx
    assert docx.Document(str(g.saida)).core_properties.identifier == "pseudonimizador:" + mapa["id"]


def test_definitivo_sem_mapa():
    pasta, doc, res = _preparar("gerar_def")
    g = gerar(doc, res, formato="texto", tipo="pdf", modo="definitivo",
              pasta_saida=pasta / "Saida", pasta_mapas=pasta / "Mapas")
    assert g.mapa is None and g.saida.name == "contrato - anonimizado.pdf"
    assert not (pasta / "Mapas").exists() or not any((pasta / "Mapas").iterdir())


def test_nao_sobrescreve():
    pasta, doc, res = _preparar("gerar_dup")
    a = gerar(doc, res, formato="layout", modo="definitivo", pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    b = gerar(doc, res, formato="layout", modo="definitivo", pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    assert a.saida != b.saida and b.saida.name == "contrato - anonimizado (2).docx"


def test_nota_de_rodape_bloqueia():
    pasta, doc, res = _preparar("gerar_nota")
    # injeta uma nota de rodapé com o nome no DOCX de entrada
    com_nota = pasta / "com_nota.docx"
    tipo_rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes"
    tipo_ct = "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"
    with zipfile.ZipFile(doc.caminho) as z, zipfile.ZipFile(com_nota, "w") as w:
        for item in z.infolist():
            dados = z.read(item.filename)
            if item.filename == "word/_rels/document.xml.rels":
                dados = dados.decode("utf-8").replace(
                    "</Relationships>",
                    f'<Relationship Id="rIdNota1" Type="{tipo_rel}" Target="footnotes.xml"/></Relationships>').encode("utf-8")
            elif item.filename == "[Content_Types].xml":
                dados = dados.decode("utf-8").replace(
                    "</Types>", f'<Override PartName="/word/footnotes.xml" ContentType="{tipo_ct}"/></Types>').encode("utf-8")
            w.writestr(item, dados)
        w.writestr("word/footnotes.xml",
                   '<?xml version="1.0"?><w:footnotes xmlns:w="http://schemas.openxmlformats.org/'
                   f'wordprocessingml/2006/main"><w:footnote w:id="1"><w:p><w:r><w:t>{F.PESSOA_1}</w:t>'
                   '</w:r></w:p></w:footnote></w:footnotes>')
    doc2 = ler(com_nota)
    assert any("notas de rodapé" in a for a in doc2.avisos)
    try:
        gerar(doc2, Revisao(doc2).fechar(), formato="layout", modo="reversivel",
              pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    except VazamentoDetectado as e:
        assert F.PESSOA_1 in e.valores
    else:
        raise AssertionError("deveria bloquear")
    assert not (pasta / "S").exists() or not any((pasta / "S").iterdir())
    assert not (pasta / "M").exists() or not any((pasta / "M").iterdir())


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
