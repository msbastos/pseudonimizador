# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Restaurar nomes (modo reversível): DOCX ou texto colado + o mapa. Tóken
sem correspondência no mapa é apontado (TokenOrfao), nunca ignorado."""
from __future__ import annotations

import os
from pathlib import Path

from .motor.reversor import RE_TOKEN, TokenOrfao, despseudonimizar_texto
from .saida import PREFIXO_ID, mapas


def restaurar_texto(texto: str, mapa: dict) -> str:
    return despseudonimizar_texto(texto, mapa)


def restaurar_docx(origem: Path, destino: Path, mapa: dict) -> int:
    """Troca os tókens pelos valores do mapa, percorrendo os mesmos lugares em que
    a saída os escreveu (corpo, tabelas, caixas de texto, cabeçalhos e rodapés,
    runs dentro de hyperlink/sdt/etc. e alvos de hyperlink externo). Não chama
    `preparar`: o arquivo restaurado não perde revisões nem comentários que
    a saída já tenha tratado. Devolve o número de trocas."""
    import docx
    from docx.opc.constants import RELATIONSHIP_TYPE as RT

    from .leitura.docx_ import paragrafos, runs_do_paragrafo
    from .saida.docx_layout import _partes_com_hyperlinks

    origem, destino = Path(origem), Path(destino)
    doc = docx.Document(str(origem))
    trocas = 0
    for par in paragrafos(doc):
        for run in runs_do_paragrafo(par):
            texto = run.text
            if "[[" in texto:
                novo = despseudonimizar_texto(texto, mapa)
                trocas += len(RE_TOKEN.findall(texto))
                run.text = novo
    for parte in _partes_com_hyperlinks(doc):
        for rel in parte.rels.values():
            if rel.is_external and rel.reltype == RT.HYPERLINK and "[[" in rel._target:
                trocas += len(RE_TOKEN.findall(rel._target))
                rel._target = despseudonimizar_texto(rel._target, mapa)
    restantes = [m.group(0) for par in paragrafos(doc) for m in RE_TOKEN.finditer(par.text)]
    for parte in _partes_com_hyperlinks(doc):
        restantes += [m.group(0) for rel in parte.rels.values() if rel.is_external
                      for m in RE_TOKEN.finditer(rel._target)]
    if restantes:
        raise TokenOrfao(f"tóken(s) restante(s) após a restauração: {restantes}")
    tmp = destino.with_suffix(".docx.tmp")
    try:
        doc.save(str(tmp))
        os.replace(tmp, destino)
    finally:
        tmp.unlink(missing_ok=True)
    return trocas


def id_do_mapa(caminho_docx: Path) -> str | None:
    import docx
    ident = docx.Document(str(caminho_docx)).core_properties.identifier or ""
    return ident[len(PREFIXO_ID):] if ident.startswith(PREFIXO_ID) else None


def mapa_do_docx(caminho_docx: Path, pasta_mapas: Path) -> dict | None:
    ident = id_do_mapa(caminho_docx)
    caminho = mapas.achar(pasta_mapas, ident) if ident else None
    return mapas.carregar(caminho) if caminho else None
