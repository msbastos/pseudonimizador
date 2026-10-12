# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import re

import fitz
import fabrica as F
from pseudonimizador.leitura import ler
from pseudonimizador.leitura.modelo import Documento, OrigemPdf
from pseudonimizador.leitura.ocr import ocr_pagina
from pseudonimizador.leitura.pdf_ import ler_pdf
from pseudonimizador.motor.mapa import normalizar
from pseudonimizador.motor.trocas import Troca
from pseudonimizador.revisao import Revisao
from pseudonimizador.saida import pdf_layout
from pseudonimizador.saida.pdf_layout import gerar_pdf_layout


def _gerar(origem, nome):
    doc = ler(origem)
    res = Revisao(doc).fechar()
    destino = origem.with_name(nome)
    avisos = gerar_pdf_layout(doc, res.trocas, destino)
    return destino, avisos


def _texto(caminho):
    with fitz.open(str(caminho)) as pdf:
        return "".join(p.get_text() for p in pdf), pdf.metadata


def test_pdf_texto_redigido():
    pasta = F.pasta_temporaria("saida_pdf")
    destino, _ = _gerar(F.contrato_pdf(pasta / "c.pdf"), "c - pseudonimizado.pdf")
    texto, meta = _texto(destino)
    for valor in (F.PESSOA_1, F.PESSOA_2, F.CPF, F.EMAIL, F.CNPJ):
        assert valor not in texto, valor
    assert "[[PESSOA_1]]" in texto.replace("\n", "")
    assert "LOCADOR" in texto and "Cláusula 1ª" in texto       # vizinhos intactos
    assert not (meta.get("author") or "") and not (meta.get("title") or "")


def test_pagina_girada_sem_vazamento():
    pasta = F.pasta_temporaria("saida_pdf_girada")
    destino, _ = _gerar(F.contrato_pdf(pasta / "g.pdf", girar=90), "g - pseudonimizado.pdf")
    texto, _ = _texto(destino)
    assert F.PESSOA_1 not in texto and F.CPF not in texto
    assert "LOCADOR" in texto and "[[PESSOA_1]]" in texto.replace("\n", "")


def _palavras(pdf):
    return set(re.findall(r"\w+", normalizar(" ".join(t for t, _ in ocr_pagina(pdf[0])))))


def test_escaneado_pixels_apagados():
    pasta = F.pasta_temporaria("saida_pdf_ocr")
    destino, _ = _gerar(F.contrato_escaneado(pasta / "e.pdf"), "e - pseudonimizado.pdf")
    with fitz.open(str(destino)) as pdf:
        lidas = _palavras(pdf)
    for parte in ("maria", "aparecida", "pereira", "111", "444", "777", "35"):
        assert parte not in lidas, (parte, lidas)
    assert "locador" in lidas, lidas


def _imagem_da_pagina(origem, destino, escrever):
    """PDF de uma página só com a imagem do que `escrever(pagina)` desenhou."""
    fonte = fitz.open()
    pagina = fonte.new_page(width=595, height=842)
    escrever(pagina)
    pix = pagina.get_pixmap(dpi=200)
    doc = fitz.open()
    nova = doc.new_page(width=595, height=842)
    nova.insert_image(nova.rect, pixmap=pix)
    return fonte, doc, nova, destino


def test_ocr_estimativa_errada_nao_deixa_nome_a_vista():
    # Imagem: "LOCADOR:  --  Maria  Aparecida  Pereira,  CPF" (6 palavras de tinta);
    # o OCR leu "CP F" (também 6 palavras): a contagem bate, mas o alinhamento não.
    # A área da redação só pode crescer a partir da estimativa.
    pasta = F.pasta_temporaria("saida_pdf_ocr_estimativa")
    linha = "LOCADOR:  --  Maria  Aparecida  Pereira,  CPF"

    def escrever(pagina):
        pagina.insert_text((60, 100), linha, fontsize=14, fontname="helv")

    fonte, doc, nova, _ = _imagem_da_pagina(None, None, escrever)
    ap = fonte[0].search_for("Aparecida")[0]
    pe = fonte[0].search_for("Pereira,")[0]
    ini = fonte[0].search_for("LOCADOR:")[0]
    fim = fonte[0].search_for("CPF")[0]
    caixa = fitz.Rect(ini.x0, ini.y0, fim.x1, ini.y1)
    caminho = pasta / "estimativa.pdf"
    doc.save(str(caminho))
    texto = "LOCADOR: Maria Aparecida Pereira, CP F"
    largura = caixa.width / len(texto)
    origens = [OrigemPdf(0, (caixa.x0 + largura * k, caixa.y0, caixa.x0 + largura * (k + 1), caixa.y1), True)
               for k in range(len(texto))]
    documento = Documento(caminho=caminho, tipo="pdf_ocr", texto=texto, origens=origens, paginas_ocr=[0])
    ini_t = texto.index("Maria")
    fim_t = texto.index("Pereira,") + len("Pereira")
    with fitz.open(str(caminho)) as pdf:
        grupos = pdf_layout._linhas(documento, ini_t, fim_t)
        assert len(grupos) == 1
        redacao, _ = pdf_layout._retangulos(pdf[0], grupos[0], False, pdf_layout._estimar_ocr(documento, grupos[0], pdf[0]))
    assert redacao.x0 <= ap.x0 + 0.3 and redacao.x1 >= pe.x1 - 0.3, (redacao, ap, pe)
    avisos = gerar_pdf_layout(documento, [Troca(ini_t, fim_t, "[[PESSOA_1]]")], pasta / "saida.pdf")
    assert isinstance(avisos, list)


def test_ocr_vao_na_linha_nao_deixa_nome_a_vista():
    # Uma só caixa de OCR cobre "Nome:" (x=60) e, bem adiante (x=260), o resto da
    # linha: a estimativa proporcional cai longe do nome. A área tem de crescer
    # até cobrir toda a tinta de Maria, Aparecida e Pereira,.
    pasta = F.pasta_temporaria("saida_pdf_ocr_vao")

    def escrever(pagina):
        pagina.insert_text((60, 100), "Nome:", fontsize=14, fontname="helv")
        pagina.insert_text((260, 100), "Maria Aparecida Pereira, CPF 111.444.777-35", fontsize=14, fontname="helv")

    fonte, doc, nova, _ = _imagem_da_pagina(None, None, escrever)
    alvo = [fonte[0].search_for(p)[0] for p in ("Maria", "Aparecida", "Pereira,")]
    ini = fonte[0].search_for("Nome:")[0]
    fim = fonte[0].search_for("111.444.777-35")[0]
    caixa = fitz.Rect(ini.x0, ini.y0, fim.x1, ini.y1)
    caminho = pasta / "vao.pdf"
    doc.save(str(caminho))
    texto = "Nome: Maria Aparecida Pereira, CPF 111.444.777-35"
    largura = caixa.width / len(texto)
    origens = [OrigemPdf(0, (caixa.x0 + largura * k, caixa.y0, caixa.x0 + largura * (k + 1), caixa.y1), True)
               for k in range(len(texto))]
    documento = Documento(caminho=caminho, tipo="pdf_ocr", texto=texto, origens=origens, paginas_ocr=[0])
    ini_t = texto.index("Maria")
    fim_t = texto.index("Pereira,") + len("Pereira")
    with fitz.open(str(caminho)) as pdf:
        grupos = pdf_layout._linhas(documento, ini_t, fim_t)
        redacao, _ = pdf_layout._retangulos(pdf[0], grupos[0], False, pdf_layout._estimar_ocr(documento, grupos[0], pdf[0]))
    for r in alvo:
        assert redacao.x0 <= r.x0 + 0.3 and redacao.x1 >= r.x1 - 0.3, (redacao, r)


def test_token_duplicado_nativo_e_ocr_sai_uma_vez():
    pasta = F.pasta_temporaria("saida_pdf_duplicado")
    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)
    pagina.insert_text((60, 100), F.PESSOA_1, fontsize=14, fontname="helv")
    r = pagina.search_for(F.PESSOA_1)[0]
    caminho = pasta / "dup.pdf"
    doc.save(str(caminho))
    n = len(F.PESSOA_1)
    w = r.width / n
    caixas = [(r.x0 + w * k, r.y0, r.x0 + w * (k + 1), r.y1) for k in range(n)]
    origens = ([OrigemPdf(0, c, False) for c in caixas] + [None]
               + [OrigemPdf(0, c, True) for c in caixas] + [None])
    texto = F.PESSOA_1 + chr(10) + F.PESSOA_1 + chr(10)
    documento = Documento(caminho=caminho, tipo="pdf_misto", texto=texto, origens=origens, paginas_ocr=[0])
    trocas = [Troca(0, n, "[[PESSOA_1]]"), Troca(n + 1, 2 * n + 1, "[[PESSOA_1]]")]
    destino = pasta / "dup - pseudonimizado.pdf"
    gerar_pdf_layout(documento, trocas, destino)
    texto_saida, _ = _texto(destino)
    assert texto_saida.count("[[PESSOA_1]]") == 1, texto_saida


RESTO_VAO = ["Maria", "Aparecida", "Lima,", "brasileira,", "casada,", "residente", "na", "Rua", "das", "Flores,", "12"]


def _pagina_com_vao(pasta, nome, vao):
    """Imagem de uma linha em Times 12: "Nome:", um vão `vao` pt com um rabisco
    no meio e as outras palavras com 6 pt entre elas. Devolve (caminho, página
    de origem, retângulos de Maria/Aparecida/Lima,, retângulo de Nome: e do fim)."""
    fonte = fitz.open()
    pagina = fonte.new_page(width=595, height=842)
    pagina.insert_text((60, 100), "Nome:", fontsize=12, fontname="tiro")
    x = 60 + fitz.get_text_length("Nome:", fontname="tiro", fontsize=12) + vao
    meio = x - vao / 2
    pontos = [(meio - 8 + 2 * k, 97 if k % 2 else 100) for k in range(9)]
    pagina.draw_polyline(pontos, color=(0, 0, 0), width=1)
    for palavra in RESTO_VAO:
        pagina.insert_text((x, 100), palavra, fontsize=12, fontname="tiro")
        x += fitz.get_text_length(palavra, fontname="tiro", fontsize=12) + 6
    alvo = [pagina.search_for(p)[0] for p in ("Maria", "Aparecida", "Lima,")]
    nome = pagina.search_for("Nome:")[0]
    fim = pagina.search_for("12")[-1]
    pix = pagina.get_pixmap(dpi=200)
    doc = fitz.open()
    nova = doc.new_page(width=595, height=842)
    nova.insert_image(nova.rect, pixmap=pix)
    caminho = pasta / f"vao{int(vao)}.pdf"
    doc.save(str(caminho))
    return caminho, alvo, nome, fim


def test_ocr_real_vao_e_rabisco_nao_deixam_nome_a_vista():
    for vao in (40, 55):
        pasta = F.pasta_temporaria(f"saida_pdf_vao_real_{vao}")
        caminho, _, _, _ = _pagina_com_vao(pasta, "vao", vao)
        destino, _ = _gerar(caminho, "vao - pseudonimizado.pdf")
        with fitz.open(str(destino)) as pdf:
            lidas = _palavras(pdf)
        for parte in ("lima", "maria", "aparecida"):
            assert parte not in lidas, (vao, parte, lidas)
        assert "nome" in lidas, (vao, lidas)


def test_ocr_caixa_alta_do_ocr_cobre_a_tinta_com_vao():
    # Caixa do OCR com altura 1,42 x o corpo (como o RapidOCR), Times 12, vãos de 30/50/80 pt.
    texto = "Nome: " + " ".join(RESTO_VAO)
    for vao in (30, 50, 80):
        pasta = F.pasta_temporaria(f"saida_pdf_vao_fn_{vao}")
        caminho, alvo, nome, fim = _pagina_com_vao(pasta, "vao", vao)
        centro = (nome.y0 + nome.y1) / 2
        caixa = fitz.Rect(nome.x0, centro - 8.5, fim.x1, centro + 8.5)
        largura = caixa.width / len(texto)
        origens = [OrigemPdf(0, (caixa.x0 + largura * k, caixa.y0, caixa.x0 + largura * (k + 1), caixa.y1), True)
                   for k in range(len(texto))]
        documento = Documento(caminho=caminho, tipo="pdf_ocr", texto=texto, origens=origens, paginas_ocr=[0])
        ini_t = texto.index("Maria")
        fim_t = texto.index("Lima,") + len("Lima")
        with fitz.open(str(caminho)) as pdf:
            grupos = pdf_layout._linhas(documento, ini_t, fim_t)
            redacao, _ = pdf_layout._retangulos(
                pdf[0], grupos[0], False, pdf_layout._estimar_ocr(documento, grupos[0], pdf[0]))
        for r in alvo:
            assert redacao.x0 <= r.x0 + 0.3 and redacao.x1 >= r.x1 - 0.3 - (1.5 if r is alvo[2] else 0), (vao, redacao, r)


def test_pdf_pesquisavel_apaga_pixels_sob_o_texto():
    # Escaneado com camada de texto invisível: a redação do texto nativo tem de
    # apagar também os pixels da caixa inteira (não só uma faixa estreitada).
    pasta = F.pasta_temporaria("saida_pdf_pesquisavel")
    fonte = fitz.open()
    pagina = fonte.new_page(width=595, height=842)
    F._pdf_de_linhas(pagina, tamanho=14)
    pix = pagina.get_pixmap(dpi=200)
    doc = fitz.open()
    nova = doc.new_page(width=595, height=842)
    nova.insert_image(nova.rect, pixmap=pix)
    nova.insert_textbox(nova.rect + (56, 56, -56, -56), (chr(10) * 2).join(F.LINHAS_CONTRATO),
                        fontsize=14, fontname="helv", render_mode=3)
    caminho = pasta / "p.pdf"
    doc.save(str(caminho))
    documento = ler_pdf(caminho)          # sem OCR: só o texto nativo
    assert not documento.paginas_ocr and F.PESSOA_1 in documento.texto
    res = Revisao(documento).fechar()
    destino = pasta / "p - pseudonimizado.pdf"
    gerar_pdf_layout(documento, res.trocas, destino)
    with fitz.open(str(destino)) as pdf:
        lidas = _palavras(pdf)
    for parte in ("maria", "aparecida", "pereira", "111", "444", "777", "35"):
        assert parte not in lidas, (parte, lidas)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
