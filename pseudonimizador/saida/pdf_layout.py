# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Saída PDF no layout original: redação real (o texto sai do arquivo; na
página escaneada, os pixels da área são apagados) e o tóken escrito no mesmo
lugar, com a fonte reduzida até caber (spec §7 e §14)."""
from __future__ import annotations

import bisect
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import fitz

from ..leitura.ocr import ocr_pixmap
from ..motor.mapa import normalizar

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


def _linha_ocr(documento, grupo: _Grupo) -> tuple[int, int, fitz.Rect]:
    """(início, fim no texto, caixa) da linha do OCR que contém o grupo."""
    texto = documento.texto
    a = texto.rfind(chr(10), 0, grupo.ini) + 1
    b = texto.find(chr(10), grupo.fim)
    b = len(texto) if b < 0 else b
    linha = fitz.Rect(documento.origens[a].rect)
    for o in documento.origens[a:b]:
        if o is not None:
            linha |= fitz.Rect(o.rect)
    return a, b, linha


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
    Limite conhecido: tinta que o OCR não leu (rabisco, barra, sublinhado)
    desloca a estimativa; por isso a área é só o ponto de partida, e
    _verificar_e_crescer confere com o próprio OCR antes de aplicar."""
    texto = documento.texto
    a, b, linha = _linha_ocr(documento, grupo)
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


@dataclass
class _Item:
    """Uma redação planejada: área a apagar, área do tóken e, para o OCR, a
    linha (início e fim no texto) e o trecho (início e fim) a que pertence."""
    redacao: fitz.Rect
    area: fitz.Rect
    token: str
    ocr: bool
    linha: tuple[int, int] | None = None
    caixa_linha: fitz.Rect | None = None
    trecho: tuple[int, int] = (0, 0)


VOLTAS = 3          # alargamentos de uma palavra de tinta antes de apagar a linha inteira
FOLGA_RECORTE = 2   # pontos em volta da caixa da linha do OCR na conferência


def _ocorrencias(palavra: str, texto: str) -> int:
    """Quantas vezes a palavra (normalizada) aparece no texto normalizado: como
    palavra inteira; as de 4 letras ou mais também grudadas em outra (o OCR às
    vezes junta palavras que a redação aproximou). Limite: a de 2 ou 3 letras
    grudada no vizinho sem pontuação ("nomesa") não é contada."""
    if len(palavra) >= 4:
        return texto.count(palavra)
    return len(re.findall(rf"(?<!\w){re.escape(palavra)}(?!\w)", texto))


def _ler_recorte(pagina, recorte: fitz.Rect, apagar: list[fitz.Rect]) -> str:
    """OCR do recorte da página como ficaria depois da redação: as áreas de
    `apagar` são pintadas de branco só na memória (o PDF não muda)."""
    pix = pagina.get_pixmap(dpi=DPI, clip=recorte, colorspace=fitz.csRGB, alpha=False)
    escala = fitz.Matrix(DPI / 72, DPI / 72)
    for r in apagar:
        ir = (r * escala).irect & pix.irect
        if not ir.is_empty:
            pix.set_rect(ir, (255, 255, 255))
    return normalizar(" ".join(ocr_pixmap(pix)))


def _uma_palavra_a_mais(caixa: fitz.Rect, tinta: list[tuple[float, float]],
                        esquerda: bool = True, direita: bool = True) -> fitz.Rect:
    """A caixa alargada até a palavra de tinta seguinte do lado pedido (inteira,
    também a que a borda corta)."""
    nova = fitz.Rect(caixa)
    antes = [p for p in tinta if p[0] < caixa.x0 - 0.5]
    depois = [p for p in tinta if p[1] > caixa.x1 + 0.5]
    if esquerda and antes:
        nova.x0 = min(nova.x0, max(antes)[0] - 1)
    if direita and depois:
        nova.x1 = max(nova.x1, min(depois, key=lambda p: p[1])[1] + 1)
    return nova


def _verificar_e_crescer(pagina, texto_linha: str, linha: fitz.Rect, da_linha: list[_Item],
                         todas: list[_Item]) -> str | None:
    """Confere com o próprio OCR, antes de aplicar a redação, se alguma palavra
    (de 2 letras ou mais) dos trechos desta linha do OCR continua legível.

    O recorte da linha (caixa do OCR com folga) é lido com todas as redações
    planejadas da página pintadas de branco. Uma palavra do trecho conta como
    legível quando aparece no recorte mais vezes do que no resto da linha
    (fora dos trechos) ou, se também aparece no resto, quando aparece ao menos
    uma vez (não dá para saber se a lida é a do resto ou a do trecho).
    Enquanto houver palavra legível, a caixa do trecho culpado cresce uma
    palavra de tinta inteira para o lado em que ela falta (a primeira palavra
    do trecho legível: à esquerda; a última: à direita; outra: dos dois lados),
    até VOLTAS vezes; se ainda sobrar (ou não houver mais tinta para tomar), a
    caixa vira a linha inteira do OCR.

    Leitura não confiável também leva à linha inteira (para todos os trechos
    da linha): recorte lido vazio havendo texto que devia continuar à vista;
    menos da metade das palavras (de 3 letras ou mais) do resto lidas; ou uma
    palavra do trecho que também está no resto lida menos vezes do que no
    resto. Linha só com os trechos e recorte vazio é o esperado: a caixa vira
    a linha inteira sem aviso (nada mais se perde).

    Limites conhecidos: parte de 2 ou 3 letras grudada no vizinho sem
    pontuação ("NomeSá") não é achada (as de 4 ou mais são, por trecho da
    palavra); e a conferência confia na leitura do RapidOCR (resto de tinta
    que ele lê como outras letras passa).

    Altera `redacao` dos itens; devolve o motivo do aviso quando a linha
    inteira foi usada, ou None."""
    recorte = (linha + (-FOLGA_RECORTE, -FOLGA_RECORTE, FOLGA_RECORTE, FOLGA_RECORTE)) & pagina.rect
    a = da_linha[0].linha[0]
    # o resto da linha: o texto do OCR com os trechos em branco
    resto = list(texto_linha)
    for item in da_linha:
        for k in range(item.trecho[0] - a, item.trecho[1] - a):
            resto[k] = " "
    resto = normalizar("".join(resto))
    resto_palavras = re.findall(r"\w+", resto)
    resto_longas = [p for p in resto_palavras if len(p) >= 3]
    palavras = {id(item): re.findall(r"\w+", normalizar(texto_linha[item.trecho[0] - a:item.trecho[1] - a]))
                for item in da_linha}
    tinta = _palavras_na_imagem(pagina, linha)
    motivo = "o trecho continuava legível"
    culpados: list[_Item] = []
    for volta in range(VOLTAS + 1):
        lido = _ler_recorte(pagina, recorte, [i.redacao for i in todas if i.redacao.intersects(recorte)])
        if not re.search(r"\w", lido):
            if resto_palavras:
                motivo, culpados = "leitura de conferência vazia", da_linha
                break
            # só os trechos na linha e nada lido: o esperado
            for item in da_linha:
                item.redacao = item.redacao | recorte
            return None
        lidas_do_resto = sum(min(_ocorrencias(p, lido), n) for p, n in Counter(resto_longas).items())
        compartilhadas = {p for ps in palavras.values() for p in ps if len(p) >= 2 and _ocorrencias(p, resto)}
        if 2 * lidas_do_resto < len(resto_longas) or any(
                _ocorrencias(p, lido) < _ocorrencias(p, resto) for p in compartilhadas):
            motivo, culpados = "leitura de conferência não confiável", da_linha
            break
        por_item: list[tuple[_Item, set[int]]] = []
        for item in da_linha:
            lidas = set()
            for k, p in enumerate(palavras[id(item)]):
                if len(p) < 2:
                    continue
                no_lido, no_resto = _ocorrencias(p, lido), _ocorrencias(p, resto)
                if no_lido > no_resto or (no_resto and no_lido):
                    lidas.add(k)
            if lidas:
                por_item.append((item, lidas))
        if not por_item:
            return None
        culpados = [item for item, _ in por_item]
        mudou = False
        if volta < VOLTAS:
            for item, lidas in por_item:
                ultima = len(palavras[id(item)]) - 1
                esquerda = 0 in lidas or ultima not in lidas
                direita = ultima in lidas or 0 not in lidas
                nova = _uma_palavra_a_mais(item.redacao, tinta, esquerda, direita)
                if nova == item.redacao:
                    nova = _uma_palavra_a_mais(item.redacao, tinta)
                mudou = mudou or nova != item.redacao
                item.redacao = nova
        if not mudou:
            break
    # ainda legível, ou leitura não confiável: a linha inteira do OCR
    for item in culpados:
        item.redacao = item.redacao | recorte
    return motivo


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
        por_pagina: dict[int, list[_Item]] = defaultdict(list)
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
                item = _Item(redacao, area, t.token if k == 0 else "", grupo[0].ocr)
                if grupo[0].ocr:
                    a, b, item.caixa_linha = _linha_ocr(documento, grupo)
                    item.linha = (a, b)
                    item.trecho = (grupo.ini, grupo.fim)
                por_pagina[n].append(item)
        for n, itens in sorted(por_pagina.items()):
            # cada linha do OCR com redação é conferida pelo próprio OCR antes de
            # aplicar; na página girada (o recorte da imagem não está no mesmo
            # sistema das caixas), a linha inteira do OCR é apagada direto
            pagina = pdf[n]
            linhas: dict[tuple[int, int], list[_Item]] = defaultdict(list)
            for item in itens:
                if item.ocr:
                    linhas[item.linha].append(item)
            for (a, b), da_linha in linhas.items():
                caixa = da_linha[0].caixa_linha
                if pagina.rotation:
                    for item in da_linha:
                        item.redacao |= caixa + (-FOLGA_RECORTE, -FOLGA_RECORTE, FOLGA_RECORTE, FOLGA_RECORTE)
                elif motivo := _verificar_e_crescer(pagina, documento.texto[a:b], caixa, da_linha, itens):
                    avisos.append(f"página {n + 1}: linha inteira do OCR apagada ({motivo})")
        for itens in por_pagina.values():
            # o mesmo nome no texto nativo e no OCR (PDF pesquisável): um só tóken,
            # o da cópia nativa; a cópia do OCR é apagada sem escrever por cima
            nativos = [i.area for i in itens if not i.ocr]
            for i in itens:
                if i.ocr and i.token and any(
                        (i.area & a).get_area() > 0.5 * min(i.area.get_area(), a.get_area()) for a in nativos):
                    i.token = ""
        for n, itens in sorted(por_pagina.items()):
            pagina = pdf[n]
            for item in itens:
                pagina.add_redact_annot(item.redacao, fill=(1, 1, 1))
            pagina.apply_redactions(images=fitz.PDF_REDACT_IMAGE_PIXELS,
                                    graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                                    text=fitz.PDF_REDACT_TEXT_REMOVE)
            for item in itens:
                if item.token and (aviso := _escrever(pagina, item.area, item.token, n)):
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
