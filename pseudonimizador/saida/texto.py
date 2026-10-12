# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Saída "só o texto": um documento novo e limpo, um parágrafo por linha."""
from __future__ import annotations

import html
import os
from pathlib import Path

import fitz


def gerar_docx_texto(texto: str, destino: Path) -> None:
    import docx
    from .docx_layout import limpar_metadados_docx
    d = docx.Document()
    for linha in texto.split("\n"):
        d.add_paragraph(linha)
    limpar_metadados_docx(d)
    tmp = Path(destino).with_suffix(".docx.tmp")
    try:
        d.save(str(tmp))
        os.replace(tmp, destino)
    finally:
        tmp.unlink(missing_ok=True)


def gerar_pdf_texto(texto: str, destino: Path) -> None:
    corpo = "".join(f"<p>{html.escape(l) or '&nbsp;'}</p>" for l in texto.split("\n"))
    story = fitz.Story(html=corpo, user_css="p{font-family:sans-serif;font-size:11pt;margin:0 0 6pt 0}")
    tmp = Path(destino).with_suffix(".pdf.tmp")
    try:
        escritor = fitz.DocumentWriter(str(tmp))
        pagina = fitz.paper_rect("a4")
        area = pagina + (56, 56, -56, -56)
        mais = True
        while mais:
            dispositivo = escritor.begin_page(pagina)
            mais, _ = story.place(area)
            story.draw(dispositivo)
            escritor.end_page()
        escritor.close()
        del escritor, dispositivo, story      # o Windows só libera o arquivo quando o escritor é descartado
        with fitz.open(str(tmp)) as pdf:
            pdf.set_metadata({})
            pdf.save(str(destino), garbage=4, deflate=True)
    finally:
        Path(tmp).unlink(missing_ok=True)
