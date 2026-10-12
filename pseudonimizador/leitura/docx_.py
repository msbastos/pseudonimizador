# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Leitura de DOCX. `preparar`, `paragrafos` e `runs_do_paragrafo` são usados
também pela saída: a mesma ordem garante que as origens apontem o mesmo run."""
from __future__ import annotations

import zipfile
from pathlib import Path

from docx.oxml.ns import qn
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


def preparar(doc) -> None:
    """Aceita as revisões controladas (inserção fica, exclusão sai) e tira as
    marcas de comentário do texto: o que sobra é o que o leitor e a saída veem."""
    for raiz in _raizes(doc):
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


def runs_do_paragrafo(par: Paragraph) -> list[Run]:
    runs: list[Run] = []
    for item in par.iter_inner_content():
        if isinstance(item, Run):
            runs.append(item)
        else:                                   # Hyperlink
            runs.extend(item.runs)
    return runs


def _abrir(caminho: Path):
    import docx
    try:
        return docx.Document(str(caminho))
    except (zipfile.BadZipFile, KeyError, ValueError, OSError) as e:
        raise ErroDeLeitura(f"não foi possível abrir o DOCX: {Path(caminho).name}") from e


def _avisos(caminho: Path) -> list[str]:
    with zipfile.ZipFile(caminho) as z:
        nomes = set(z.namelist())
    avisos = []
    if "word/footnotes.xml" in nomes or "word/endnotes.xml" in nomes:
        avisos.append("o documento tem notas de rodapé ou de fim, que não são tratadas; "
                      "se houver dado pessoal nelas, a geração será bloqueada")
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
