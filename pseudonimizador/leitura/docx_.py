# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Leitura de DOCX. `preparar`, `paragrafos` e `runs_do_paragrafo` são usados
também pela saída: a mesma ordem garante que as origens apontem o mesmo run."""
from __future__ import annotations

import zipfile
from pathlib import Path

from docx.oxml.ns import qn
from lxml import etree
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from .modelo import Documento, ErroDeLeitura, OrigemDocx


def _raizes(doc) -> list:
    """O corpo e cada cabeçalho/rodapé que tem definição própria (sem criar nenhum)."""
    raizes = [doc.element.body]
    vistos = set()
    for secao in doc.sections:
        for hf in (secao.header, secao.first_page_header, secao.even_page_header,
                   secao.footer, secao.first_page_footer, secao.even_page_footer):
            if hf._has_definition and id(hf._element) not in vistos:
                vistos.add(id(hf._element))
                raizes.append(hf._element)
    return raizes


def _desembrulhar(el) -> None:
    pai = el.getparent()
    i = pai.index(el)
    for filho in list(el):
        pai.insert(i, filho)
        i += 1
    pai.remove(el)


# revisões de formatação: ficam dentro dos *Pr (nunca contêm runs), então
# tirá-las não muda a contagem de parágrafos nem de runs
_MUDANCAS_DE_FORMATACAO = " | ".join(f".//w:{t}" for t in (
    "rPrChange", "pPrChange", "sectPrChange", "tblPrChange", "tcPrChange", "trPrChange",
    "tblGridChange", "numberingChange", "tblPrExChange"))
_AUTORIA = (qn("w:author"), qn("w:initials"))


def preparar(doc) -> None:
    """Aceita as revisões controladas (inserção fica, exclusão sai), descarta
    as revisões de formatação, tira as marcas de comentário do texto e os
    atributos de autoria (w:author, w:initials) que sobrarem: o que fica é o
    que o leitor e a saída veem."""
    for raiz in _raizes(doc):
        for el in raiz.xpath(_MUDANCAS_DE_FORMATACAO):
            el.getparent().remove(el)
        for el in raiz.xpath(".//w:del | .//w:moveFrom"):
            el.getparent().remove(el)
        for el in raiz.xpath(".//w:ins | .//w:moveTo"):
            _desembrulhar(el)
        for el in raiz.xpath(".//w:commentRangeStart | .//w:commentRangeEnd | .//w:commentReference"):
            pai = el.getparent()
            pai.remove(el)
            # o run que só carregava a referência ao comentário some junto
            if pai.tag == qn("w:r") and all(f.tag == qn("w:rPr") for f in pai):
                pai.getparent().remove(pai)
        for el in raiz.iter(etree.Element):   # só elementos (sem comentários XML)
            for atributo in _AUTORIA:
                el.attrib.pop(atributo, None)


def _blocos(pai, elemento, vistos: set):
    for filho in elemento.iterchildren():
        if filho.tag == qn("w:p"):
            yield Paragraph(filho, pai)
        elif filho.tag == qn("w:tbl"):
            for linha in Table(filho, pai).rows:
                for celula in linha.cells:
                    if id(celula._tc) in vistos:      # célula mesclada aparece repetida
                        continue
                    vistos.add(id(celula._tc))
                    yield from _blocos(celula, celula._tc, vistos)
        elif filho.tag == qn("w:sdt"):
            conteudo = filho.find(qn("w:sdtContent"))
            if conteudo is not None:
                yield from _blocos(pai, conteudo, vistos)


def paragrafos(doc) -> list[Paragraph]:
    saida: list[Paragraph] = []
    for raiz in _raizes(doc):
        vistos: set = set()
        saida.extend(_blocos(doc.part, raiz, vistos))
        for caixa in raiz.xpath(".//w:txbxContent"):
            saida.extend(_blocos(doc.part, caixa, vistos))
    return saida


_ENVOLTORIOS = tuple(qn(t) for t in ("w:hyperlink", "w:smartTag", "w:customXml", "w:fldSimple"))


def runs_do_paragrafo(par: Paragraph) -> list[Run]:
    """Os runs em ordem de documento, inclusive dentro de hyperlink, smartTag,
    customXml, fldSimple e sdt em linha (recursivo)."""
    runs: list[Run] = []

    def andar(elemento) -> None:
        for filho in elemento.iterchildren():
            if filho.tag == qn("w:r"):
                runs.append(Run(filho, par))
            elif filho.tag in _ENVOLTORIOS:
                andar(filho)
            elif filho.tag == qn("w:sdt"):
                conteudo = filho.find(qn("w:sdtContent"))
                if conteudo is not None:
                    andar(conteudo)

    andar(par._p)
    return runs


def _abrir(caminho: Path):
    import docx
    from docx.opc.exceptions import PackageNotFoundError
    from lxml.etree import XMLSyntaxError
    try:
        return docx.Document(str(caminho))
    except (zipfile.BadZipFile, KeyError, ValueError, OSError, PackageNotFoundError, XMLSyntaxError) as e:
        raise ErroDeLeitura(f"não foi possível abrir o DOCX: {Path(caminho).name}") from e


def _avisos(caminho: Path) -> list[str]:
    with zipfile.ZipFile(caminho) as z:
        nomes = set(z.namelist())
    avisos = []
    if "word/footnotes.xml" in nomes or "word/endnotes.xml" in nomes:
        avisos.append("o documento tem notas de rodapé ou de fim, que não são lidas nem tratadas; "
                      "confira-as antes de compartilhar a saída")
    if any(n.startswith(("word/media/", "word/embeddings/")) for n in nomes):
        avisos.append("o documento tem imagem(ns) ou objeto(s) embutido(s) que não são lidos nem "
                      "tratados; confira-os")
    return avisos


def ler_docx(caminho: Path) -> Documento:
    caminho = Path(caminho)
    doc = _abrir(caminho)
    preparar(doc)
    partes: list[str] = []
    origens: list = []
    for i, par in enumerate(paragrafos(doc)):
        for j, run in enumerate(runs_do_paragrafo(par)):
            t = run.text
            partes.append(t)
            origens.extend(OrigemDocx(i, j, k) for k in range(len(t)))
        partes.append("\n")
        origens.append(None)
    return Documento(caminho=caminho, tipo="docx", texto="".join(partes), origens=origens,
                     avisos=_avisos(caminho))
