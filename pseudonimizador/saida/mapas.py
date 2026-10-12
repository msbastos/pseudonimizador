# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Mapas do modo reversível: sempre em pasta própria, nunca ao lado da saída."""
from __future__ import annotations

import json
import re
import secrets
from datetime import datetime
from pathlib import Path

from ..motor.mapa import escrever_atomico


def novo_id(nome_base: str = "") -> str:
    """Identificador sem relação com o nome do arquivo de entrada (o nome pode
    ser o de uma parte). `nome_base` é ignorado e só existe por compatibilidade."""
    return f"{datetime.now():%Y%m%d-%H%M%S}-{secrets.token_hex(4)}"


def gravar(pasta_mapas: Path, nome_base: str, mapa: dict, identificador: str | None = None) -> tuple[str, Path]:
    identificador = identificador or novo_id(nome_base)
    mapa = {**mapa, "id": identificador}
    caminho = Path(pasta_mapas) / f"{identificador}.json"
    escrever_atomico(caminho, json.dumps(mapa, ensure_ascii=False, indent=1))
    return identificador, caminho


def carregar(caminho: Path) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


RE_ID = re.compile(r"[0-9A-Za-z_-]{1,80}")


def achar(pasta_mapas: Path, identificador: str) -> Path | None:
    """O mapa de um identificador, só se este tiver o formato dos nossos ids
    e o arquivo ficar dentro da pasta de mapas (o id pode vir de um DOCX
    alheio: nada de `..` nem de caminho absoluto)."""
    if not isinstance(identificador, str) or not RE_ID.fullmatch(identificador):
        return None
    pasta = Path(pasta_mapas)
    caminho = pasta / f"{identificador}.json"
    if caminho.resolve().parent != pasta.resolve():
        return None
    return caminho if caminho.is_file() else None
