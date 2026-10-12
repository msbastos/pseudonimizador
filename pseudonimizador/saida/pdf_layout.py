# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Saída PDF no layout original: redação real (o texto sai do arquivo; na
página escaneada, os pixels da área são apagados) e o tóken escrito no mesmo
lugar, com a fonte reduzida até caber (spec §7 e §14)."""
from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path

import fitz

FONTE_MINIMA = 4.0


class _Grupo(list):
    """Caracteres (OrigemPdf) de um trecho numa mesma linha; `ini`/`fim` são os
    índices deles no texto do documento."""
    ini: int = 0
    fim: int = 0


def _linhas(documento, ini: int, fim: int) -> list[_Grupo]:
    """Agrupa os caracteres de um trecho por página, tipo de origem e linha."""
    grupos: list[_Grupo] = []
    for i in range(ini, fim):
        o = documento.origens[i]
        if o is None:
            continue
        if grupos:
            u = grupos[-1][-1]
            altura = u.rect[3] - u.rect[1]
            if (o.pagina == u.pagina and o.ocr == u.ocr
                    and abs(o.rect[1] - u.rect[1]) < altura / 2):
                grupos[-1].append(o)
                grupos[-1].fim = i + 1
                continue
        g = _Grupo([o])
        g.ini, g.fim = i, i + 1
        grupos.append(g)
    return grupos


def _palavras_na_imagem(pagina, linha: fitz.Rect) -> list[tuple[float, float]]:
    """Faixas horizontais (x0, x1, em pontos) com tinta na linha, separadas por
    vãos de espaço de palavra. Lê os pixels da página como está."""
    dpi = 200
    recorte = (linha + (-2, 0, 2, 0)) & pagina.rect
    pix = pagina.get_pixmap(dpi=dpi, clip=recorte, colorspace=fitz.csGRAY, alpha=False)
    amostras = pix.samples
    largura, altura = pix.width, pix.height
    if not largura or not altura:
        return []
    tinta = [any(amostras[y * pix.stride + x] < 140 for y in range(altura)) for x in range(largura)]
    vao_minimo = max(3, int(0.22 * altura))
    palavras: list[list[int]] = []
    vazios = vao_minimo
    for x, t in enumerate(tinta):
        if t:
            if vazios >= vao_minimo:
                palavras.append([x, x])
            else:
                palavras[-1][1] = x
            vazios = 0
        else:
            vazios += 1
    escala = 72 / dpi
    return [(recorte.x0 + a * escala, recorte.x0 + (b + 1) * escala) for a, b in palavras]


def _peso(c: str) -> float:
    """Largura relativa de um caractere: pontuação é bem mais estreita."""
    return 1.0 if c.isalnum() else 0.4


def _caixa_ocr(documento, pagina, grupo: _Grupo) -> tuple[float, float] | None:
    """As posições dos caracteres do OCR são estimativas (a linha dividida em
    partes iguais) e, em fonte proporcional, erram a ponto de cobrir a palavra
    vizinha. Contamos as palavras da linha no texto e na imagem; se o número
    coincide, o trecho ocupa as palavras da imagem de mesmo número (nas pontas,
    uma palavra só em parte, como '(51)' ou 'nome,', é dividida pelo peso
    dos caracteres). Senão (ou em página girada), None: vale a estimativa."""
    if pagina.rotation or not grupo.ini < grupo.fim:
        return None
    texto = documento.texto
    a = texto.rfind("\n", 0, grupo.ini) + 1
    b = texto.find("\n", grupo.fim)
    b = len(texto) if b < 0 else b
    palavras = [m.span() for m in re.finditer(r"\S+", texto[a:b])]
    palavras = [(x + a, y + a) for x, y in palavras]
    dentro = [k for k, (x, y) in enumerate(palavras) if x < grupo.fim and y > grupo.ini]
    if not dentro:
        return None
    todas = [documento.origens[i] for i in range(a, b)]
    caixa = fitz.Rect(todas[0].rect)
    for o in todas[1:]:
        caixa |= fitz.Rect(o.rect)
    na_imagem = _palavras_na_imagem(pagina, caixa)
    if len(na_imagem) != len(palavras):
        return None
    k0, k1 = dentro[0], dentro[-1]
    x0, y0 = palavras[k0]
    x1, y1 = palavras[k1]
    esq, dir_ = na_imagem[k0][0], na_imagem[k1][1]
    if grupo.ini > x0:      # começa no meio da palavra
        antes = sum(_peso(c) for c in texto[x0:grupo.ini])
        total = sum(_peso(c) for c in texto[x0:y0])
        esq = na_imagem[k0][0] + (na_imagem[k0][1] - na_imagem[k0][0]) * antes / total
    if grupo.fim < y1:      # termina no meio da palavra
        depois = sum(_peso(c) for c in texto[grupo.fim:y1])
        total = sum(_peso(c) for c in texto[x1:y1])
        dir_ = na_imagem[k1][1] - (na_imagem[k1][1] - na_imagem[k1][0]) * depois / total
    return esq, dir_


def _retangulos(grupo: list, horizontal: tuple[float, float] | None = None) -> tuple[fitz.Rect, fitz.Rect]:
    """(área da redação, área do tóken). Na página com texto, a redação é
    estreitada nas pontas para não levar a letra vizinha (a letra do trecho
    sai inteira mesmo assim, porque a redação remove o caractere). Na página
    escaneada, cobre a caixa toda com folga: é ela que apaga os pixels."""
    caixa = fitz.Rect(grupo[0].rect)
    for o in grupo[1:]:
        caixa |= fitz.Rect(o.rect)
    if grupo[0].ocr:
        if horizontal:
            caixa = fitz.Rect(horizontal[0], caixa.y0, horizontal[1], caixa.y1)
        return caixa + (-1, -1, 1, 1), caixa
    w0 = grupo[0].rect[2] - grupo[0].rect[0]
    w1 = grupo[-1].rect[2] - grupo[-1].rect[0]
    alto = caixa.height
    redacao = fitz.Rect(caixa.x0 + 0.2 * w0, caixa.y0 + 0.2 * alto, caixa.x1 - 0.2 * w1, caixa.y1 - 0.2 * alto)
    return redacao, caixa


def _escrever(pagina, area: fitz.Rect, token: str, n: int) -> str | None:
    tamanho = max(FONTE_MINIMA, area.height * 0.8)
    while tamanho >= FONTE_MINIMA:
        if pagina.insert_textbox(area, token, fontsize=tamanho, fontname="helv") >= 0:
            return None
        tamanho -= 0.5
    # não coube: o tóken vai inteiro (a restauração depende dele), avançando à direita
    pagina.insert_text((area.x0, area.y1 - 1), token, fontsize=FONTE_MINIMA, fontname="helv")
    return f"página {n + 1}: código maior que o espaço do original"


def gerar_pdf_layout(documento, trocas, destino: Path) -> list[str]:
    # Página girada: no PyMuPDF 1.28, tanto os retângulos de get_text quanto os
    # de add_redact_annot/insert_textbox ficam no sistema SEM rotação da página
    # (verificado: a página com /Rotate 90 devolve bbox não girado), então não
    # há conversão a fazer; test_pagina_girada_sem_vazamento garante.
    avisos: list[str] = []
    destino = Path(destino)
    tmp = destino.with_suffix(".pdf.tmp")
    pdf = fitz.open(str(documento.caminho))
    try:
        por_pagina: dict[int, list[tuple[fitz.Rect, fitz.Rect, str]]] = defaultdict(list)
        for t in trocas:
            for k, grupo in enumerate(_linhas(documento, t.ini, t.fim)):
                horizontal = _caixa_ocr(documento, pdf[grupo[0].pagina], grupo) if grupo[0].ocr else None
                redacao, area = _retangulos(grupo, horizontal)
                por_pagina[grupo[0].pagina].append((redacao, area, t.token if k == 0 else ""))
        for n, itens in sorted(por_pagina.items()):
            pagina = pdf[n]
            for redacao, _, _ in itens:
                pagina.add_redact_annot(redacao, fill=(1, 1, 1))
            pagina.apply_redactions(images=fitz.PDF_REDACT_IMAGE_PIXELS,
                                    graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                                    text=fitz.PDF_REDACT_TEXT_REMOVE)
            for _, area, token in itens:
                if token and (aviso := _escrever(pagina, area, token, n)):
                    avisos.append(aviso)
        pdf.set_metadata({})
        pdf.del_xml_metadata()
        pdf.save(str(tmp), garbage=4, deflate=True)
    except BaseException:
        pdf.close()
        tmp.unlink(missing_ok=True)
        raise
    pdf.close()
    os.replace(tmp, destino)
    return avisos
