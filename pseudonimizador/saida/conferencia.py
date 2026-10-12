# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Conferência depois de gerar: nenhum valor do mapa pode aparecer no arquivo
de saída — em nenhuma parte dele (spec §7)."""
from __future__ import annotations

import re
import zipfile
from urllib.parse import unquote
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
_DML = "{http://schemas.openxmlformats.org/drawingml/"


def _local(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _com_decodificado(valores) -> list[str]:
    """Cada valor como veio e, se tinha %XX, também decodificado."""
    saida = []
    for v in valores:
        v = str(v)
        saida.append(v)
        d = unquote(v)
        if d != v:
            saida.append(d)
    return saida


def _texto_xml(dados: bytes) -> tuple[str, str]:
    """(corpo, atributos) de uma parte XML. Corpo: runs do mesmo parágrafo
    (w:p ou a:p) colados; espaço em quebra, tabulação e fim de
    parágrafo/célula/linha. Atributos (docVar, Target, descr, tooltips...)
    ficam à parte, também decodificados de %XX."""
    from lxml import etree
    try:
        raiz = etree.fromstring(dados, etree.XMLParser(resolve_entities=False, no_network=True, recover=True))
    except etree.XMLSyntaxError:
        raiz = None
    if raiz is None:
        import html
        return html.unescape(re.sub(r"<[^>]+>", " ", dados.decode("utf-8", "replace"))), ""
    word = raiz.tag.startswith("{http://schemas.openxmlformats.org/wordprocessingml/")
    atributos: list[str] = []
    for el in raiz.iter():
        atributos.extend(el.attrib.values())
    saida: list[str] = []

    def visitar(el, colado):
        nome = _local(el.tag)
        dml = isinstance(el.tag, str) and el.tag.startswith(_DML)
        if dml and nome == "p":
            colado = True
        sep = (word or dml) and nome in _SEPARADORES
        if sep:
            saida.append(" ")
        if el.text and isinstance(el.tag, str):
            saida.append(el.text if colado else " " + el.text + " ")
        for filho in el:
            visitar(filho, colado)
            if filho.tail:
                saida.append(filho.tail if colado else " " + filho.tail + " ")
        if sep:
            saida.append(" ")

    visitar(raiz, word)
    return "".join(saida), " ".join(_com_decodificado(atributos))


def _texto_docx(caminho: Path) -> tuple[str, str]:
    corpo, attrs = [], []
    with zipfile.ZipFile(caminho) as z:
        for n in z.namelist():
            if n.endswith((".xml", ".rels")):
                c, a = _texto_xml(z.read(n))
                corpo.append(c)
                attrs.append(a)
    return " ".join(corpo), " ".join(attrs)


def _texto_pdf(caminho: Path, paginas_ocr) -> tuple[str, str]:
    import fitz
    from ..leitura.ocr import ocr_pagina
    from ..leitura.pdf_ import ler_pdf
    corpo, extras = [], []
    try:   # o texto na ordem de leitura do leitor (rodapés ao fim), além da extração simples abaixo
        corpo.append(ler_pdf(caminho).texto)
    except Exception as e:  # noqa: BLE001 — a extração simples continua valendo
        import logging   # só o tipo da exceção: nada de caminho nem de valor
        logging.getLogger(__name__).warning("conferência: leitura em ordem de leitura falhou (%s)", type(e).__name__)
    with fitz.open(str(caminho)) as pdf:
        extras.extend(str(v) for v in pdf.metadata.values() if v)
        extras.append(pdf.get_xml_metadata() or "")
        extras.extend(str(t) for _, t, *_ in pdf.get_toc(simple=False) or [])
        for nome in pdf.embfile_names():
            extras.append(nome)
            extras.extend(str(v) for v in pdf.embfile_info(nome).values() if v)
        for n, pagina in enumerate(pdf):
            corpo.append(pagina.get_text())
            for anot in pagina.annots() or []:
                extras.extend(str(v) for v in anot.info.values() if v)
            for campo in pagina.widgets() or []:
                extras.extend(str(v) for v in (campo.field_name, campo.field_value, campo.field_label) if v)
            extras.extend(str(l["uri"]) for l in pagina.get_links() if l.get("uri"))
            if n in paginas_ocr:
                corpo.extend(t for t, _ in ocr_pagina(pagina))
    return " ".join(corpo), " ".join(_com_decodificado(extras))


def conferir(caminho: Path, mapa: dict, paginas_ocr=()) -> list[str]:
    caminho = Path(caminho)
    corpo, extras = _texto_docx(caminho) if caminho.suffix.lower() == ".docx" else _texto_pdf(caminho, set(paginas_ocr))
    fontes = []
    for bruto in (corpo, extras):  # nunca concatenados: a rede de segurança não cruza a fronteira
        texto = normalizar(bruto)
        fontes.append((texto, re.sub(r"[\W_]+", "", texto)))
    achados = []
    for v in valores_vigiados(mapa):
        alvo = normalizar(v)
        sem = re.sub(r"[\W_]+", "", alvo)
        for texto, compacto in fontes:
            if re.search(r"(?<!\w)" + re.escape(alvo) + r"(?!\w)", texto):
                achou = True
            elif len(sem) >= 8:
                borda = (r"(?<!\d)", r"(?!\d)") if sem.isdigit() else ("", "")
                achou = bool(re.search(borda[0] + re.escape(sem) + borda[1], compacto))
            else:
                achou = False
            if achou:
                achados.append(v)
                break
    return achados
