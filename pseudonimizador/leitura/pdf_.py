# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Leitura de PDF: caractere a caractere, com o retângulo de cada um. Linhas
do mesmo bloco se juntam com espaço (o nome quebrado no fim da linha continua
um nome); blocos se separam com quebra de linha."""
from __future__ import annotations

from pathlib import Path

import fitz

from .modelo import Documento, ErroDeLeitura, OrigemPdf

MIN_CARACTERES = 20
# sem TEXT_PRESERVE_LIGATURES: a ligadura "ﬁ" vira "f" + "i"
FLAGS = fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_MEDIABOX_CLIP


def _abrir(caminho: Path):
    try:
        pdf = fitz.open(str(caminho))
    except Exception as e:  # noqa: BLE001 — o PyMuPDF levanta tipos variados
        raise ErroDeLeitura(f"não foi possível abrir o PDF: {Path(caminho).name}") from e
    if pdf.needs_pass:
        pdf.close()
        raise ErroDeLeitura(f"o PDF está protegido por senha: {Path(caminho).name}")
    return pdf


def _caracteres(pagina, n: int, partes: list[str], origens: list) -> None:
    for bloco in pagina.get_text("rawdict", flags=FLAGS)["blocks"]:
        if bloco.get("type") != 0:
            continue
        for k, linha in enumerate(bloco["lines"]):
            if k:
                partes.append(" "); origens.append(None)
            for span in linha["spans"]:
                for ch in span["chars"]:
                    partes.append(ch["c"])
                    origens.append(OrigemPdf(n, tuple(ch["bbox"]), False))
        partes.append("\n"); origens.append(None)


def _linhas_ocr(n: int, linhas, partes: list[str], origens: list) -> None:
    """Cada linha do OCR: a posição de cada caractere é estimada dividindo a
    caixa da linha em partes iguais."""
    for texto, rect in linhas:
        if not texto:
            continue
        largura = (rect.x1 - rect.x0) / len(texto)
        for i, c in enumerate(texto):
            partes.append(c)
            origens.append(OrigemPdf(n, (rect.x0 + largura * i, rect.y0, rect.x0 + largura * (i + 1), rect.y1), True))
        partes.append("\n"); origens.append(None)


def ler_pdf(caminho: Path, ocr=None) -> Documento:
    caminho = Path(caminho)
    pdf = _abrir(caminho)
    partes: list[str] = []
    origens: list = []
    avisos: list[str] = []
    paginas_ocr: list[int] = []
    com_texto = 0
    try:
        for n, pagina in enumerate(pdf):
            if len(pagina.get_text("text", flags=FLAGS).strip()) >= MIN_CARACTERES:
                _caracteres(pagina, n, partes, origens)
                com_texto += 1
            elif pagina.get_images():
                if ocr is None:
                    avisos.append(f"página {n + 1} sem texto (imagem) não foi lida")
                    continue
                _linhas_ocr(n, ocr(pagina), partes, origens)
                paginas_ocr.append(n)
    finally:
        pdf.close()
    tipo = "pdf_texto" if not paginas_ocr else ("pdf_ocr" if not com_texto else "pdf_misto")
    return Documento(caminho=caminho, tipo=tipo, texto="".join(partes), origens=origens,
                     avisos=avisos, paginas_ocr=paginas_ocr)
