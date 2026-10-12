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


def test_pdf_layout_remove_anotacao_e_toc():
    import fitz
    import pseudonimizador.saida.conferencia as C
    pasta = F.pasta_temporaria("gerar_pdf_extras")
    caminho = F.contrato_pdf(pasta / "contrato.pdf")
    pdf = fitz.open(str(caminho))
    pdf[0].add_text_annot((300, 20), F.PESSOA_1)
    pdf.set_toc([[1, F.PESSOA_1, 1]])
    pdf.save(str(pasta / "ex.pdf"))
    pdf.close()
    doc = ler(pasta / "ex.pdf")
    g = gerar(doc, Revisao(doc).fechar(), formato="layout", modo="definitivo",
              pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    with fitz.open(str(g.saida)) as saida:
        assert not list(saida[0].annots() or []) and saida.get_toc() == []


def test_falha_na_conferencia_apaga_a_saida():
    import pseudonimizador.saida as S
    pasta, doc, res = _preparar("gerar_falha")
    original = S.conferir
    def quebrada(*a, **k):
        raise RuntimeError("ocr caiu")
    S.conferir = quebrada
    try:
        gerar(doc, res, formato="layout", modo="reversivel", pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    except RuntimeError:
        pass
    else:
        raise AssertionError("deveria propagar")
    finally:
        S.conferir = original
    assert not any((pasta / "S").iterdir())
    assert not (pasta / "M").exists() or not any((pasta / "M").iterdir())


def test_aviso_de_valores_curtos_sem_revelar_valor():
    pasta, doc, res = _preparar("gerar_curtos")
    res.mapa["tokens"]["[[PESSOA_99]]"] = {"categoria": "pessoa", "valor": "Zeferina"}
    g = gerar(doc, res, formato="layout", modo="definitivo", pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    aviso = [a for a in g.avisos if "não conferido" in a]
    assert aviso and "Zeferina" not in aviso[0] and aviso[0].startswith("1 valor")


def test_pastas_sobrepostas_recusadas():
    pasta, doc, res = _preparar("gerar_pastas")
    for saida, mapas in ((pasta / "X", pasta / "X"), (pasta / "X", pasta / "X" / "m"), (pasta / "X" / "s", pasta / "X")):
        try:
            gerar(doc, res, formato="layout", modo="reversivel", pasta_saida=saida, pasta_mapas=mapas)
        except ValueError:
            pass
        else:
            raise AssertionError("deveria recusar")
    assert not (pasta / "X").exists()


def test_gravar_nao_altera_o_mapa_do_chamador():
    from pseudonimizador.saida import mapas
    pasta = F.pasta_temporaria("gerar_copia")
    m = {"tokens": {}}
    mapas.gravar(pasta / "M", "x", m)
    assert "id" not in m



def test_nome_do_arquivo_de_entrada_nao_vaza_no_id_nem_no_mapa():
    pasta = F.pasta_temporaria("gerar_nome_parte")
    doc = ler(F.contrato_docx(pasta / f"{F.PESSOA_1}.docx"))
    g = gerar(doc, Revisao(doc).fechar(), formato="layout", modo="reversivel",
              pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    import docx
    ident = docx.Document(str(g.saida)).core_properties.identifier
    assert "maria" not in ident.lower() and "maria" not in g.mapa.name.lower()
    assert "maria" not in g.saida.name.lower()


def test_nome_da_saida_troca_valores_do_mapa_por_token():
    pasta = F.pasta_temporaria("gerar_nome_saida")
    doc = ler(F.contrato_docx(pasta / f"Contrato {F.PESSOA_1.upper()}.docx"))
    res = Revisao(doc).fechar()
    g = gerar(doc, res, formato="layout", modo="definitivo", pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    token = next(t.strip("[]") for t, i in res.mapa["tokens"].items() if i["valor"] == F.PESSOA_1)
    assert g.saida.name == f"Contrato {token} - anonimizado.docx", g.saida.name


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
