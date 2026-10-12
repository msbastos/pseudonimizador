# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Conferência depois de gerar: nenhum valor do mapa pode aparecer no arquivo
de saída — em nenhuma parte dele (spec §7)."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

from ..motor.mapa import normalizar


class VazamentoDetectado(RuntimeError):
    def __init__(self, valores: list[str]):
        super().__init__(f"{len(valores)} dado(s) continuariam visíveis na saída; nada foi gerado")
        self.valores = valores


def valores_vigiados(mapa: dict, devolver_pulados: bool = False):
    """Identificadores e nomes com 2+ palavras (o prenome solto pode ser
    palavra comum em outro lugar do texto). Com `devolver_pulados`, devolve
    também os valores que a conferência não vigia (par vigiados, pulados)."""
    vigiados, pulados = [], []
    for info in mapa.get("tokens", {}).values():
        valor = str(info.get("valor") or "").strip()
        if not valor:
            continue
        solto = info.get("categoria") in ("pessoa", "pj") and len(valor.split()) < 2
        if solto or len(normalizar(valor)) < 4:
            pulados.append(valor)
        else:
            vigiados.append(valor)
    return (vigiados, pulados) if devolver_pulados else vigiados


_SEPARADORES = {"p", "tc", "tr", "br", "tab", "cr", "txbxContent"}


def _local(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _texto_xml(dados: bytes) -> str:
    """Texto de uma parte XML: runs do mesmo parágrafo colados; espaço em
    quebra, tabulação e fim de parágrafo/célula/linha; todos os valores de
    atributos (docVar, Target, descr, tooltips...) entram no texto."""
    from lxml import etree
    try:
        raiz = etree.fromstring(dados, etree.XMLParser(resolve_entities=False, no_network=True, recover=True))
    except etree.XMLSyntaxError:
        raiz = None
    if raiz is None:
        import html
        return html.unescape(re.sub(r"<[^>]+>", " ", dados.decode("utf-8", "replace")))
    word = raiz.tag.startswith("{http://schemas.openxmlformats.org/wordprocessingml/")
    partes: list[str] = []
    for el in raiz.iter():
        partes.extend(str(v) for v in el.attrib.values())
    saida: list[str] = []

    def visitar(el):
        nome = _local(el.tag)
        if word and nome in _SEPARADORES:
            saida.append(" ")
        if el.text and isinstance(el.tag, str):
            saida.append(el.text if word else " " + el.text + " ")
        for filho in el:
            visitar(filho)
            if filho.tail:
                saida.append(filho.tail if word else " " + filho.tail + " ")
        if word and nome in _SEPARADORES:
            saida.append(" ")

    visitar(raiz)
    return "".join(saida) + " " + " ".join(partes)


def _texto_docx(caminho: Path) -> str:
    with zipfile.ZipFile(caminho) as z:
        partes = [_texto_xml(z.read(n)) for n in z.namelist() if n.endswith((".xml", ".rels"))]
    return " ".join(partes)


def _texto_pdf(caminho: Path, paginas_ocr) -> str:
    import fitz
    from ..leitura.ocr import ocr_pagina
    partes = []
    with fitz.open(str(caminho)) as pdf:
        partes.extend(str(v) for v in pdf.metadata.values() if v)
        partes.append(pdf.get_xml_metadata() or "")
        partes.extend(str(t) for _, t, *_ in pdf.get_toc(simple=False) or [])
        for nome in pdf.embfile_names():
            partes.append(nome)
            partes.extend(str(v) for v in pdf.embfile_info(nome).values() if v)
        for n, pagina in enumerate(pdf):
            partes.append(pagina.get_text())
            for anot in pagina.annots() or []:
                partes.extend(str(v) for v in anot.info.values() if v)
            for campo in pagina.widgets() or []:
                partes.extend(str(v) for v in (campo.field_name, campo.field_value, campo.field_label) if v)
            partes.extend(str(l["uri"]) for l in pagina.get_links() if l.get("uri"))
            if n in paginas_ocr:
                partes.extend(t for t, _ in ocr_pagina(pagina))
    return " ".join(partes)


def conferir(caminho: Path, mapa: dict, paginas_ocr=()) -> list[str]:
    caminho = Path(caminho)
    bruto = _texto_docx(caminho) if caminho.suffix.lower() == ".docx" else _texto_pdf(caminho, set(paginas_ocr))
    texto = normalizar(bruto)
    compacto = re.sub(r"[\W_]+", "", texto)
    achados = []
    for v in valores_vigiados(mapa):
        alvo = normalizar(v)
        if re.search(r"(?<!\w)" + re.escape(alvo) + r"(?!\w)", texto):
            achados.append(v)
            continue
        sem = re.sub(r"[\W_]+", "", alvo)
        if len(sem) >= 8 and sem in compacto:
            achados.append(v)
    return achados
