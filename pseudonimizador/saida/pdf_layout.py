# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Saída PDF no layout original: redação real (o texto sai do arquivo; na
página escaneada, os pixels da área são apagados) e o tóken escrito no mesmo
lugar, com a fonte reduzida até caber (spec §7 e §14)."""
from __future__ import annotations

import bisect
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


DPI = 200


def _colunas_com_tinta(pagina, linha: fitz.Rect) -> tuple[float, list[bool]]:
    """(x0 em pontos, para cada coluna de pixel da faixa `linha`: tem tinta?).
    Lê os pixels da página como estão."""
    recorte = (linha + (-2, 0, 2, 0)) & pagina.rect
    pix = pagina.get_pixmap(dpi=DPI, clip=recorte, colorspace=fitz.csGRAY, alpha=False)
    amostras = pix.samples
    if not pix.width or not pix.height:
        return recorte.x0, []
    tinta = [any(amostras[y * pix.stride + x] < 140 for y in range(pix.height)) for x in range(pix.width)]
    return recorte.x0, tinta


def _palavras_das_colunas(x0: float, tinta: list[bool], altura_pt: float) -> list[tuple[float, float]]:
    """Faixas horizontais (x0, x1, em pontos) com tinta, separadas por vãos de
    espaço de palavra."""
    vao_minimo = max(3, int(0.22 * altura_pt * DPI / 72))
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
    escala = 72 / DPI
    return [(x0 + a * escala, x0 + (b + 1) * escala) for a, b in palavras]


def _palavras_na_imagem(pagina, linha: fitz.Rect) -> list[tuple[float, float]]:
    x0, tinta = _colunas_com_tinta(pagina, linha)
    return _palavras_das_colunas(x0, tinta, linha.height)


def _estimar_ocr(documento, grupo: _Grupo, pagina=None) -> fitz.Rect:
    """Caixa estimada do trecho numa linha do OCR. Sem a página, a linha é
    dividida em partes proporcionais à largura dos caracteres (Helvetica).
    Com a página, a posição vem da imagem: a fração do texto da linha (pesos
    da Helvetica) em que o trecho começa e termina é levada para as colunas de
    pixel da faixa, contando a tinta e, do vão em branco, só a largura de um
    espaço (vão grande, carimbo apagado ou rabisco não lido não entram na
    conta; nenhuma métrica de fonte mede o vão). O núcleo se alarga em meio
    corpo de linha por lado, só por espaço em branco: não entra em palavra da
    imagem que o núcleo não toca (o rótulo vizinho fica). Com o mesmo número de
    palavras no texto e na imagem, as palavras da imagem de mesmo índice que as
    do trecho entram. Depois, _caixa_ocr une as palavras inteiras que a tocam.
    Limite conhecido: tinta que o OCR não leu (rabisco) desloca a estimativa
    em até a sua largura; se o núcleo cair em palavra vizinha, ela é apagada
    inteira (excesso, não vazamento)."""
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
    x0, tinta = _colunas_com_tinta(pagina, linha)
    if not any(tinta):
        return caixa
    # posição efetiva de cada coluna: tinta avança; vão em branco avança só até
    # o tamanho de um espaço (o resto do vão, ou do carimbo apagado, não conta)
    espaco = max(2, int(0.25 * linha.height * DPI / 72))
    efetiva: list[int] = []
    pos = vazio = 0
    for t in tinta:
        vazio = 0 if t else vazio + 1
        if t or vazio <= espaco:
            pos += 1
        efetiva.append(pos)
    soma = sum(larguras)
    f0 = sum(larguras[:grupo.ini - a]) / soma
    f1 = sum(larguras[:grupo.fim - a]) / soma
    k0 = bisect.bisect_left(efetiva, max(1, int(f0 * pos)))
    k1 = bisect.bisect_left(efetiva, max(1, int(f1 * pos)))
    k0, k1 = min(k0, len(tinta) - 1), min(max(k1, k0), len(tinta) - 1)
    escala = 72 / DPI
    nucleo = (x0 + k0 * escala, x0 + (k1 + 1) * escala)
    ink = _palavras_das_colunas(x0, tinta, linha.height)
    # cada lado se alarga em meio corpo de linha (um caractere médio), mas o
    # alargamento só avança por espaço em branco: não entra em palavra da
    # imagem que o núcleo não toca (o rótulo vizinho, como "Nome:", fica)
    folga = linha.height * 0.5
    esq, dir_ = nucleo[0] - folga, nucleo[1] + folga
    for ini_p, fim_p in ink:
        if fim_p < nucleo[0] - 1:
            esq = max(esq, min(fim_p + 1.5, nucleo[0]))
        elif ini_p > nucleo[1] + 1:
            dir_ = min(dir_, max(ini_p - 1.5, nucleo[1]))
    caixa = fitz.Rect(esq, linha.y0, dir_, linha.y1)
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
        if a < caixa.x1 and b > caixa.x0:
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
