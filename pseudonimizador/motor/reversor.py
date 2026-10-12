# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
# Origem: Ulpiano, ulpiano/nucleo/privacidade/reversor.py, commit 5bab2ff (11/10/2026); alterações descritas abaixo.
"""
==============================================================
 ARQUIVO: reversor.py
 PROJETO: AnaliseDeProcessos / privacidade
 VERSAO:  0.1.1
 ATUALIZADO: 2026-09-03
 ALTERACAO 0.1.1: correcao de revisao — _todos_paragrafos so' cobria
   doc.paragraphs e as tabelas soltas do corpo; um tóken em
   cabecalho/rodape sobrevivia a reversao, e docx_tem_token dizia False
   com dado sensivel ainda intacto no arquivo. Agora tambem itera
   doc.sections, cedendo os paragrafos (e tabelas) de header/footer
   padrao, de primeira pagina e de paginas pares de cada secao.
 ALTERACAO 0.1.0: versao inicial. despseudonimizar_texto troca tokens
   por valores reais usando so' a estrutura do mapa (nao importa
   mapa.py — quem gera o mapa e quem o consome ficam desacoplados).
   despseudonimizar_docx troca tokens dentro de um .docx preservando a
   formatacao dos runs vizinhos (substituicao run-aware, de tras para
   frente no paragrafo, para que posicoes ja calculadas nao se movam),
   varre paragrafos soltos e os de dentro de tabelas (inclusive
   tabelas aninhadas), grava atomico (.tmp + os.replace) e falha
   (TokenOrfao) se sobrar QUALQUER "[[" apos a reversao — tanto por
   token sem entrada no mapa quanto por qualquer outro residuo. O
   import de `docx` e' local as funcoes que o usam: quem so' chama
   despseudonimizar_texto nao paga a dependencia de python-docx.
==============================================================
"""
from __future__ import annotations
import os
import re
from pathlib import Path

RE_TOKEN = re.compile(r"\[\[[A-Z][A-Z0-9_]*\]\]")


class TokenOrfao(RuntimeError):
    """Token [[...]] sem entrada no mapa — nunca ignorado em silencio."""


def despseudonimizar_texto(texto: str, mapa: dict) -> str:
    """Troca cada token [[...]] pelo valor real cadastrado no mapa.
    Token sem entrada no mapa e' erro fatal (TokenOrfao) — nunca vira
    string vazia nem fica no texto por engano."""
    def troca(m: re.Match) -> str:
        info = mapa["tokens"].get(m.group(0))
        if info is None:
            raise TokenOrfao(f"tóken sem entrada no mapa: {m.group(0)}")
        return info["valor"]
    return RE_TOKEN.sub(troca, texto)


def _todos_paragrafos(doc):
    """Paragrafos soltos do documento + os de dentro de todas as tabelas
    (inclusive tabelas aninhadas dentro de celulas) + cabecalho/rodape de
    cada secao (padrao, primeira pagina e paginas pares) e as tabelas
    dentro deles. Um token em cabecalho/rodape e' tao dado sensivel quanto
    um no corpo — ficar de fora fazia docx_tem_token dizer False com dado
    ainda intacto no arquivo."""
    yield from doc.paragraphs
    yield from _paragrafos_de_tabelas(doc.tables)
    for secao in doc.sections:
        for parte in (secao.header, secao.footer,
                      secao.first_page_header, secao.first_page_footer,
                      secao.even_page_header, secao.even_page_footer):
            if parte is None:
                continue
            yield from parte.paragraphs
            yield from _paragrafos_de_tabelas(parte.tables)


def _paragrafos_de_tabelas(tabelas):
    for t in tabelas:
        for row in t.rows:
            for cell in row.cells:
                yield from cell.paragraphs
                yield from _paragrafos_de_tabelas(cell.tables)  # aninhada


def _substituir_em_paragrafo(par, mapa: dict) -> int:
    """Troca os tokens do paragrafo pelos valores reais, run a run, sem
    perder a formatacao dos runs vizinhos. O texto do paragrafo inteiro
    e' a concatenacao dos textos dos runs — um token pode comecar num
    run e terminar noutro (ex.: negrito so' numa parte da palavra); a
    troca reescreve so' os runs efetivamente tocados pelo token."""
    texto = "".join(r.text for r in par.runs)
    if "[[" not in texto:
        return 0
    trocas = 0
    # do fim para o comeco: as posicoes (spans) dos tokens anteriores no
    # texto continuam validas mesmo depois que o comprimento do texto
    # muda com uma troca mais a frente.
    for m in reversed(list(RE_TOKEN.finditer(texto))):
        info = mapa["tokens"].get(m.group(0))
        if info is None:
            raise TokenOrfao(f"tóken sem entrada no mapa: {m.group(0)}")
        ini, fim = m.span()
        pos, alcancados = 0, []
        for r in par.runs:
            r_ini, r_fim = pos, pos + len(r.text)
            if r_fim > ini and r_ini < fim:
                alcancados.append((r, max(ini - r_ini, 0),
                                    min(fim - r_ini, len(r.text))))
            pos = r_fim
        if len(alcancados) == 1:
            r, a, b = alcancados[0]
            r.text = r.text[:a] + info["valor"] + r.text[b:]
        else:
            # o valor inteiro entra no primeiro run tocado (preserva a
            # formatacao dele); os runs seguintes so' perdem o trecho do
            # token e mantem o que vinha depois, com a propria formatacao.
            r0, a, _ = alcancados[0]
            r0.text = r0.text[:a] + info["valor"]
            for r, _a, b in alcancados[1:]:
                r.text = r.text[b:]
        trocas += 1
    return trocas


def docx_tem_token(caminho: Path) -> bool:
    """True se algum paragrafo (solto ou em tabela, inclusive aninhada)
    do .docx contem um tóken [[...]]."""
    import docx
    doc = docx.Document(str(caminho))
    return any(RE_TOKEN.search(p.text) for p in _todos_paragrafos(doc))


def despseudonimizar_docx(caminho: Path, mapa: dict) -> int:
    """Troca todos os tokens do .docx pelos valores reais do mapa,
    preservando a formatacao dos runs. Devolve o numero de trocas.

    Erro fatal (TokenOrfao) se, apos a reversao, sobrar QUALQUER "[[" em
    algum paragrafo — token sem entrada no mapa (ja' barrado durante a
    troca) ou qualquer outro residuo: nunca sai um .docx com tóken
    visivel por engano. Gravacao atomica: salva num .tmp ao lado do
    arquivo final e so' substitui (os.replace) depois que o save deu
    certo — nunca deixa o .docx pela metade no disco."""
    import docx
    doc = docx.Document(str(caminho))
    trocas = sum(_substituir_em_paragrafo(p, mapa)
                 for p in list(_todos_paragrafos(doc)))
    restantes = [m.group(0) for p in _todos_paragrafos(doc)
                 for m in RE_TOKEN.finditer(p.text)]
    if restantes:
        raise TokenOrfao(f"tóken(s) restante(s) após a reversão: {restantes}")
    tmp = caminho.with_suffix(".docx.tmp")
    doc.save(str(tmp))
    os.replace(tmp, caminho)
    return trocas
