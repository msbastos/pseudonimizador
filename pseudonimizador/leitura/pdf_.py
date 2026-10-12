# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Leitura de PDF: caractere a caractere, com o retângulo de cada um. Linhas
do mesmo bloco se juntam com espaço (o nome quebrado no fim da linha continua
um nome); blocos se separam com quebra de linha. O texto segue a ordem de
leitura de cada página; cabeçalhos e rodapés (faixa de margem) vão para o fim."""
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


# Faixa de margem da página: cabeçalho, rodapé e número de página não ficam
# entre o fim de uma página e o começo da seguinte (um nome que vira a página
# seria cortado); saem do fluxo do corpo e vão para o fim do texto.
MARGEM = 0.06


def _na_margem(y0: float, y1: float, altura: float) -> bool:
    return y1 < altura * MARGEM or y0 > altura * (1 - MARGEM)


class _Margens:
    """Linhas de margem de todas as páginas, na ordem em que apareceram."""

    def __init__(self) -> None:
        self.partes: list[str] = []
        self.origens: list = []

    def linha(self, caracteres) -> None:
        for c, origem in caracteres:
            self.partes.append(c); self.origens.append(origem)
        self.partes.append("\n"); self.origens.append(None)


def _caracteres(pagina, n: int, partes: list[str], origens: list, margens: _Margens) -> None:
    altura = pagina.rect.height
    for bloco in pagina.get_text("rawdict", flags=FLAGS, sort=True)["blocks"]:
        if bloco.get("type") != 0:
            continue
        k = 0
        for linha in bloco["lines"]:
            chars = [(ch["c"], OrigemPdf(n, tuple(ch["bbox"]), False))
                     for span in linha["spans"] for ch in span["chars"]]
            if _na_margem(linha["bbox"][1], linha["bbox"][3], altura):
                margens.linha(chars)
                continue
            if k:
                partes.append(" "); origens.append(None)
            k += 1
            for c, o in chars:
                partes.append(c); origens.append(o)
        if k:
            partes.append("\n"); origens.append(None)


def _linhas_ocr(n: int, linhas, partes: list[str], origens: list, margens: _Margens, altura: float) -> None:
    """Cada linha do OCR: a posição de cada caractere é estimada dividindo a
    caixa da linha em partes iguais."""
    for texto, rect in linhas:
        if not texto:
            continue
        largura = (rect.x1 - rect.x0) / len(texto)
        chars = [(c, OrigemPdf(n, (rect.x0 + largura * i, rect.y0, rect.x0 + largura * (i + 1), rect.y1), True))
                 for i, c in enumerate(texto)]
        if _na_margem(rect.y0, rect.y1, altura):
            margens.linha(chars)
            continue
        for c, o in chars:
            partes.append(c); origens.append(o)
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
    margens = _Margens()
    com_nativo = 0
    try:
        for n, pagina in enumerate(pdf):
            nativo = len(pagina.get_text("text", flags=FLAGS).strip())
            if nativo:
                _caracteres(pagina, n, partes, origens, margens)
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
            _linhas_ocr(n, ocr(pagina), partes, origens, margens, pagina.rect.height)
            paginas_ocr.append(n)
    finally:
        pdf.close()
    partes += margens.partes
    origens += margens.origens
    if not paginas_ocr:
        tipo = "pdf_texto"
    else:
        tipo = "pdf_ocr" if not com_nativo else "pdf_misto"
    return Documento(caminho=caminho, tipo=tipo, texto="".join(partes), origens=origens,
                     avisos=avisos, paginas_ocr=paginas_ocr)
