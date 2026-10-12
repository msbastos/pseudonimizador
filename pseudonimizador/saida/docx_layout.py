# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Saída DOCX no layout original: a troca é feita nos runs. Trecho que
atravessa runs: o tóken fica no primeiro (com a formatação dele) e os demais
perdem a parte trocada. Metadados, comentários e revisões saem (spec §7).

Também são limpos: os alvos dos hyperlinks externos (cada trecho trocado, sem
distinguir caixa; formas codificadas em URL, como %40, não são tratadas), os
atributos `w:tooltip`, o texto alternativo (`descr`, `title` de `wp:docPr`) e
o modelo anexado (`w:attachedTemplate` de settings.xml e a sua relação).

NÃO são editados: notas de rodapé e de fim, códigos de campo (`w:instrText`),
`w:docVar` e imagens. Se um valor do mapa sobrar aí, a verificação de saída de
uma tarefa posterior bloqueia o arquivo."""
from __future__ import annotations

import os
import re
from collections import defaultdict
from itertools import groupby
from pathlib import Path

from docx.opc.constants import RELATIONSHIP_TYPE as RT

from docx.oxml.ns import qn

from ..leitura.docx_ import _raizes, paragrafos, preparar, runs_do_paragrafo

_CUSTOM_XML = "/customXml"
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
        elif rel.reltype.endswith(_CUSTOM_XML):
            doc.part.rels.pop(rid)
    _tirar_modelo_anexado(doc)
    pacote = doc.part.package
    for rid, rel in list(pacote.rels.items()):
        if rel.reltype in (RT.EXTENDED_PROPERTIES, RT.CUSTOM_PROPERTIES, RT.THUMBNAIL):
            pacote.rels.pop(rid)


def _tirar_modelo_anexado(doc) -> None:
    """word/settings.xml: o w:attachedTemplate aponta o modelo do Word, e o alvo
    da relação pode ser um caminho local com o nome do usuário. Saem os dois."""
    parte = doc.part._settings_part
    for el in parte.element.findall(qn("w:attachedTemplate")):
        parte.element.remove(el)
    for rid, rel in list(parte.rels.items()):
        if rel.reltype.endswith("/attachedTemplate"):
            parte.rels.pop(rid)


def _partes_com_hyperlinks(doc):
    partes = {id(doc.part): doc.part}
    for secao in doc.sections:
        for hf in (secao.header, secao.first_page_header, secao.even_page_header,
                   secao.footer, secao.first_page_footer, secao.even_page_footer):
            if hf._has_definition:
                partes[id(hf.part)] = hf.part
    return partes.values()


def _limpar_alvos_e_atributos(doc, substituicoes: dict[str, str]) -> None:
    if substituicoes:
        padrao = re.compile("|".join(re.escape(k) for k in sorted(substituicoes, key=len, reverse=True)),
                            re.IGNORECASE)
        tokens = {k.lower(): v for k, v in substituicoes.items()}
        for parte in _partes_com_hyperlinks(doc):
            for rel in parte.rels.values():
                if rel.is_external and rel.reltype == RT.HYPERLINK:
                    rel._target = padrao.sub(lambda m: tokens[m.group(0).lower()], rel._target)
    for raiz in _raizes(doc):
        for el in raiz.xpath(".//w:hyperlink"):
            el.attrib.pop(qn("w:tooltip"), None)
        for el in raiz.xpath(".//wp:docPr"):
            el.attrib.pop("descr", None)
            el.attrib.pop("title", None)


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
    _limpar_alvos_e_atributos(doc, {documento.texto[t.ini:t.fim]: t.token for t in trocas})
    limpar_metadados_docx(doc, identificador)
    tmp = Path(destino).with_suffix(".docx.tmp")
    try:
        doc.save(str(tmp))
        os.replace(tmp, destino)
    finally:
        tmp.unlink(missing_ok=True)
