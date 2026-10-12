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


# Imagem que cobre ao menos 3% da página passa pelo OCR, mesmo com texto
# nativo farto: um documento colado (identidade, comprovante) costuma ocupar
# de 10% a 20% da página; abaixo disso ficam ícones e enfeites. Antes o limite
# era 50% (só a digitalização do corpo), e o documento colado passava sem ser
# lido nem conferido. Apagar demais é aceitável; deixar dado à vista, não.
COBERTURA_IMAGEM = 0.03


def _cobertura(pagina) -> float:
    """Fração da área da página coberta por imagens (soma, limitada a 1: na dúvida, OCR)."""
    area = pagina.rect.get_area()
    if area <= 0:
        return 0.0
    total = 0.0
    for info in pagina.get_image_info():
        total += (fitz.Rect(info["bbox"]) & pagina.rect).get_area()
    return min(total / area, 1.0)


def ler_pdf(caminho: Path, ocr=None) -> Documento:
    """Lê o PDF caractere a caractere. Páginas sem imagem são lidas do texto
    nativo, qualquer que seja o tamanho. Páginas com imagens que somam ao
    menos COBERTURA_IMAGEM (3%) da página, ou com pouco texto nativo e alguma
    imagem, passam pelo OCR quando ele é dado (texto nativo + linhas do OCR);
    sem OCR, ficam num aviso.

    `ocr(pagina) -> list[tuple[str, fitz.Rect]]`: uma entrada por linha de texto,
    com o retângulo em pontos do PDF, no mesmo sistema de coordenadas de
    `page.get_text("rawdict")` (não em pixels do pixmap)."""
    caminho = Path(caminho)
    pdf = _abrir(caminho)
    partes: list[str] = []
    origens: list = []
    avisos: list[str] = []
    paginas_ocr: list[int] = []
    com_nativo = 0
    try:
        for n, pagina in enumerate(pdf):
            nativo = len(pagina.get_text("text", flags=FLAGS).strip())
            if nativo:
                _caracteres(pagina, n, partes, origens)
                com_nativo += 1
            if not pagina.get_images():
                continue
            pouco_texto = nativo < MIN_CARACTERES
            if not pouco_texto and _cobertura(pagina) < COBERTURA_IMAGEM:
                continue
            if ocr is None:
                if pouco_texto:
                    avisos.append(f"página {n + 1} sem texto (imagem) não foi lida")
                else:
                    avisos.append(f"página {n + 1} tem imagem que não foi lida por OCR")
                continue
            _linhas_ocr(n, ocr(pagina), partes, origens)
            paginas_ocr.append(n)
    finally:
        pdf.close()
    if not paginas_ocr:
        tipo = "pdf_texto"
    else:
        tipo = "pdf_ocr" if not com_nativo else "pdf_misto"
    return Documento(caminho=caminho, tipo=tipo, texto="".join(partes), origens=origens,
                     avisos=avisos, paginas_ocr=paginas_ocr)
