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


def valores_vigiados(mapa: dict) -> list[str]:
    """Identificadores e nomes com 2+ palavras (o prenome solto pode ser
    palavra comum em outro lugar do texto)."""
    vigiados = []
    for info in mapa.get("tokens", {}).values():
        valor = str(info.get("valor") or "").strip()
        if info.get("categoria") in ("pessoa", "pj") and len(valor.split()) < 2:
            continue
        if len(normalizar(valor)) >= 4:
            vigiados.append(valor)
    return vigiados


def _texto_docx(caminho: Path) -> str:
    with zipfile.ZipFile(caminho) as z:
        partes = [re.sub(r"<[^>]+>", "", z.read(n).decode("utf-8", "replace"))
                  for n in z.namelist() if n.endswith((".xml", ".rels"))]
    return " ".join(partes)


def _texto_pdf(caminho: Path, paginas_ocr) -> str:
    import fitz
    from ..leitura.ocr import ocr_pagina
    partes = []
    with fitz.open(str(caminho)) as pdf:
        partes.extend(str(v) for v in pdf.metadata.values() if v)
        for n, pagina in enumerate(pdf):
            partes.append(pagina.get_text())
            if n in paginas_ocr:
                partes.extend(t for t, _ in ocr_pagina(pagina))
    return " ".join(partes)


def conferir(caminho: Path, mapa: dict, paginas_ocr=()) -> list[str]:
    caminho = Path(caminho)
    bruto = _texto_docx(caminho) if caminho.suffix.lower() == ".docx" else _texto_pdf(caminho, set(paginas_ocr))
    texto = normalizar(bruto)
    return [v for v in valores_vigiados(mapa)
            if re.search(r"(?<!\w)" + re.escape(normalizar(v)) + r"(?!\w)", texto)]
