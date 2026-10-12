# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Ponto de entrada da leitura: DOCX, PDF com texto e PDF escaneado."""
from __future__ import annotations

from pathlib import Path

from .modelo import Documento, ErroDeLeitura, OrigemDocx, OrigemPdf  # noqa: F401

ACEITOS = (".docx", ".pdf")


def ler(caminho: Path) -> Documento:
    caminho = Path(caminho)
    sufixo = caminho.suffix.lower()
    if sufixo == ".docx":
        from .docx_ import ler_docx
        return ler_docx(caminho)
    if sufixo == ".pdf":
        from .ocr import ocr_pagina
        from .pdf_ import ler_pdf
        return ler_pdf(caminho, ocr=ocr_pagina)
    raise ErroDeLeitura(f"formato não aceito: {sufixo or '(sem extensão)'} (aceitos: .docx, .pdf)")
