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


def _estimar_ocr(documento, grupo: _Grupo, pagina=None) -> fitz.Rect:
    """Caixa estimada do trecho numa linha do OCR. O leitor divide a linha em
    partes iguais por caractere; aqui a divisão é proporcional à largura dos
    caracteres (métrica da Helvetica), que erra bem menos em fonte comum."""
    texto = documento.texto
    a = texto.rfind(chr(10), 0, grupo.ini) + 1
    b = texto.find(chr(10), grupo.fim)
    b = len(texto) if b < 0 else b
    linha = fitz.Rect(documento.origens[a].rect)
    for o in documento.origens[a:b]:
        if o is not None:
            linha |= fitz.Rect(o.rect)
    larguras = [fitz.get_text_length(c, fontname="helv", fontsize=1) or 0.3 for c in texto[a:b]]
    total = sum(larguras)
    antes = sum(larguras[:grupo.ini - a])
    dentro = sum(larguras[grupo.ini - a:grupo.fim - a])
    esc = linha.width / total
    caixa = fitz.Rect(linha.x0 + antes * esc, linha.y0, linha.x0 + (antes + dentro) * esc, linha.y1)
    if pagina is None or pagina.rotation:
        return caixa
    # Só crescem (deixar dado à vista custa mais que apagar o vizinho):
    ink = [(x, y) for x, y in _palavras_na_imagem(pagina, fitz.Rect(pagina.rect.x0, linha.y0, pagina.rect.x1, linha.y1))
           if x < linha.x1 + 2 and y > linha.x0 - 2]
    if not ink:
        return caixa
    # (b) largura que o texto lido não explica (vão, carimbo, marca não lida):
    # a estimativa se alarga dos dois lados por ela
    natural = total * linha.height / 1.25
    sobra = max(0.0, (ink[-1][1] - ink[0][0]) - natural)
    caixa.x0 -= sobra
    caixa.x1 += sobra
    # (a) com o mesmo número de palavras no texto e na imagem, as palavras da
    # imagem de mesmo índice que as do trecho entram na área
    palavras = [m.span() for m in re.finditer(r"\S+", texto[a:b])]
    if len(palavras) == len(ink):
        for k, (x, y) in enumerate(palavras):
            if x + a < grupo.fim and y + a > grupo.ini:
                caixa.x0 = min(caixa.x0, ink[k][0])
                caixa.x1 = max(caixa.x1, ink[k][1])
    return caixa


def _caixa_ocr(pagina, caixa: fitz.Rect) -> tuple[float, float]:
    """As posições dos caracteres do OCR são estimativas (a linha dividida em
    partes iguais) e, em fonte proporcional, podem errar para os dois lados.
    Regra conservadora: a área é a UNIÃO da estimativa com toda palavra inteira
    da imagem que a toque; só cresce, nunca troca nem encolhe a estimativa
    (deixar dado à vista custa mais que apagar a palavra vizinha). Página
    girada: vale só a estimativa."""
    x0, x1 = caixa.x0, caixa.x1
    if pagina.rotation:
        return x0, x1
    linha = fitz.Rect(pagina.rect.x0, caixa.y0, pagina.rect.x1, caixa.y1)
    for a, b in _palavras_na_imagem(pagina, linha):
        if a < caixa.x1 + 1 and b > caixa.x0 - 1:
            x0, x1 = min(x0, a), max(x1, b)
    return x0, x1


def _retangulos(pagina, grupo: list, cheio: bool = False, estimada: fitz.Rect | None = None) -> tuple[fitz.Rect, fitz.Rect]:
    """(área da redação, área do tóken). Na página com texto puro, a redação é
    estreitada nas pontas para não levar a letra vizinha (a letra do trecho
    sai inteira mesmo assim, porque a redação remove o caractere). Se há
    imagem sob o texto (`cheio`) ou a página é escaneada, cobre a caixa toda
    com folga de 1 pt: é ela que apaga os pixels."""
    caixa = fitz.Rect(grupo[0].rect)
    for o in grupo[1:]:
        caixa |= fitz.Rect(o.rect)
    if grupo[0].ocr:
        caixa = estimada or caixa
        x0, x1 = _caixa_ocr(pagina, caixa)
        caixa = fitz.Rect(x0, caixa.y0, x1, caixa.y1)
        return caixa + (-1, -1, 1, 1), caixa
    if cheio:
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
        por_pagina: dict[int, list[list]] = defaultdict(list)   # [redação, área, tóken, ocr]
        for t in trocas:
            for k, grupo in enumerate(_linhas(documento, t.ini, t.fim)):
                n = grupo[0].pagina
                pagina = pdf[n]
                cheio = False
                if not grupo[0].ocr:
                    caixa = fitz.Rect(grupo[0].rect)
                    for o in grupo[1:]:
                        caixa |= fitz.Rect(o.rect)
                    # imagem sob o texto (PDF pesquisável): os pixels só saem
                    # dentro da redação, então ela cobre a caixa inteira
                    cheio = n in documento.paginas_ocr or any(
                        fitz.Rect(i["bbox"]).intersects(caixa) for i in pagina.get_image_info())
                redacao, area = _retangulos(pagina, grupo, cheio, _estimar_ocr(documento, grupo, pagina) if grupo[0].ocr else None)
                por_pagina[n].append([redacao, area, t.token if k == 0 else "", grupo[0].ocr])
        for itens in por_pagina.values():
            # o mesmo nome no texto nativo e no OCR (PDF pesquisável): um só tóken,
            # o da cópia nativa; a cópia do OCR é apagada sem escrever por cima
            nativos = [i[1] for i in itens if not i[3]]
            for i in itens:
                if i[3] and i[2] and any(
                        (i[1] & a).get_area() > 0.5 * min(i[1].get_area(), a.get_area()) for a in nativos):
                    i[2] = ""
        for n, itens in sorted(por_pagina.items()):
            pagina = pdf[n]
            for redacao, _, _, _ in itens:
                pagina.add_redact_annot(redacao, fill=(1, 1, 1))
            pagina.apply_redactions(images=fitz.PDF_REDACT_IMAGE_PIXELS,
                                    graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                                    text=fitz.PDF_REDACT_TEXT_REMOVE)
            for _, area, token, _ in itens:
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
