# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""O documento lido: texto corrido e, para cada caractere, de onde ele veio."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class ErroDeLeitura(Exception):
    """Arquivo que não pode ser lido (formato, senha, arquivo corrompido)."""


@dataclass(frozen=True)
class OrigemDocx:
    paragrafo: int     # índice em leitura.docx_.paragrafos(doc)
    run: int           # índice em leitura.docx_.runs_do_paragrafo(par)
    pos: int           # posição do caractere em run.text


@dataclass(frozen=True)
class OrigemPdf:
    pagina: int
    rect: tuple[float, float, float, float]   # no sistema de coordenadas de page.get_text / add_redact_annot
    ocr: bool


@dataclass
class Documento:
    caminho: Path
    tipo: str                                  # docx | pdf_texto | pdf_ocr | pdf_misto
    texto: str
    origens: list = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    paginas_ocr: list[int] = field(default_factory=list)
