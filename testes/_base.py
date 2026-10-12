# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Importado no topo de cada teste: põe a raiz do projeto no sys.path."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

# O RapidOCR escreve "detection result is empty" (WARNING) em páginas sem texto e
# reinicia o nível do seu logger ao ser importado; um filtro sobrevive a isso.
import logging as _logging


class _SoErros(_logging.Filter):
    def filter(self, registro):
        return registro.levelno >= _logging.ERROR


_logging.getLogger("RapidOCR").addFilter(_SoErros())
