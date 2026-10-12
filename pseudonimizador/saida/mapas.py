# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Mapas do modo reversível: sempre em pasta própria, nunca ao lado da saída."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from ..motor.mapa import escrever_atomico


def novo_id(nome_base: str) -> str:
    seguro = re.sub(r"[^\w\-]+", "_", nome_base).strip("_")[:60] or "documento"
    return f"{seguro}-{datetime.now():%Y%m%d-%H%M%S-%f}"


def gravar(pasta_mapas: Path, nome_base: str, mapa: dict, identificador: str | None = None) -> tuple[str, Path]:
    identificador = identificador or novo_id(nome_base)
    mapa = {**mapa, "id": identificador}
    caminho = Path(pasta_mapas) / f"{identificador}.json"
    escrever_atomico(caminho, json.dumps(mapa, ensure_ascii=False, indent=1))
    return identificador, caminho


def carregar(caminho: Path) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def achar(pasta_mapas: Path, identificador: str) -> Path | None:
    caminho = Path(pasta_mapas) / f"{identificador}.json"
    return caminho if caminho.is_file() else None
