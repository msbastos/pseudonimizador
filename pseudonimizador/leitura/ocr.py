# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""OCR local (RapidOCR, modelos embutidos no pacote): nada sai da máquina."""
from __future__ import annotations

from functools import lru_cache

import fitz
import numpy as np


@lru_cache(maxsize=1)
def _motor():
    from rapidocr import RapidOCR
    return RapidOCR()


def ocr_pagina(pagina, dpi: int = 200) -> list[tuple[str, "fitz.Rect"]]:
    pix = pagina.get_pixmap(dpi=dpi, colorspace=fitz.csRGB, alpha=False)
    imagem = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    resultado = _motor()(imagem)
    if resultado is None or resultado.boxes is None:
        return []
    escala = 72 / dpi
    linhas = []
    for caixa, texto in zip(resultado.boxes, resultado.txts):
        xs = [float(p[0]) for p in caixa]
        ys = [float(p[1]) for p in caixa]
        # a imagem é a página como aparece (girada); volta ao sistema não girado
        rect = fitz.Rect(min(xs), min(ys), max(xs), max(ys)) * escala * pagina.derotation_matrix
        linhas.append((str(texto), rect))
    linhas.sort(key=lambda l: (round(l[1].y0 / 5), l[1].x0))
    return linhas
