# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Saída DOCX no layout original: a troca é feita nos runs. Trecho que
atravessa runs: o tóken fica no primeiro (com a formatação dele) e os demais
perdem a parte trocada. Metadados, comentários e revisões saem (spec §7)."""
from __future__ import annotations

import os
from collections import defaultdict
from itertools import groupby
from pathlib import Path

from docx.opc.constants import RELATIONSHIP_TYPE as RT

from ..leitura.docx_ import paragrafos, preparar, runs_do_paragrafo

_RELS_DE_COMENTARIO = ("/comments", "/commentsExtended", "/commentsIds", "/commentsExtensible", "/people")


def limpar_metadados_docx(doc, identificador: str = "") -> None:
    cp = doc.core_properties
    for campo in ("author", "last_modified_by", "comments", "title", "subject", "keywords",
                  "category", "content_status"):
        setattr(cp, campo, "")
    cp.identifier = identificador
    cp.revision = 1
    for rid, rel in list(doc.part.rels.items()):
        if rel.reltype.endswith(_RELS_DE_COMENTARIO):
            doc.part.rels.pop(rid)           # drop_rel só solta com a referência já tirada do XML
    pacote = doc.part.package
    for rid, rel in list(pacote.rels.items()):
        if rel.reltype in (RT.EXTENDED_PROPERTIES, RT.CUSTOM_PROPERTIES):
            pacote.rels.pop(rid)


def gerar_docx_layout(documento, trocas, destino: Path, identificador: str = "") -> None:
    import docx
    doc = docx.Document(str(documento.caminho))
    preparar(doc)
    runs = [runs_do_paragrafo(p) for p in paragrafos(doc)]
    edicoes: dict[tuple[int, int], list[tuple[int, int, str]]] = defaultdict(list)
    for t in trocas:
        origens = [o for o in documento.origens[t.ini:t.fim] if o is not None]
        for k, (chave, grupo) in enumerate(groupby(origens, key=lambda o: (o.paragrafo, o.run))):
            g = list(grupo)
            edicoes[chave].append((g[0].pos, g[-1].pos + 1, t.token if k == 0 else ""))
    for (p, r), lista in edicoes.items():
        run = runs[p][r]
        s = run.text
        for a, b, novo in sorted(lista, reverse=True):
            s = s[:a] + novo + s[b:]
        run.text = s
    limpar_metadados_docx(doc, identificador)
    tmp = Path(destino).with_suffix(".docx.tmp")
    doc.save(str(tmp))
    os.replace(tmp, destino)
