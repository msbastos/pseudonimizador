# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fitz

import fabrica as F
from pseudonimizador.leitura.modelo import ErroDeLeitura, OrigemPdf
from pseudonimizador.leitura.pdf_ import ler_pdf


def test_pdf_com_texto():
    d = ler_pdf(F.contrato_pdf(F.pasta_temporaria("leitura_pdf") / "c.pdf"))
    assert d.tipo == "pdf_texto" and d.paginas_ocr == []
    assert F.PESSOA_1 in d.texto and F.CPF in d.texto and "LOCATÁRIA" in d.texto
    assert len(d.origens) == len(d.texto)
    o = d.origens[d.texto.index(F.CPF)]
    assert isinstance(o, OrigemPdf) and o.pagina == 0 and not o.ocr
    x0, y0, x1, y1 = o.rect
    assert x1 > x0 and y1 > y0


def test_escaneado_sem_ocr_gera_aviso():
    d = ler_pdf(F.contrato_escaneado(F.pasta_temporaria("leitura_pdf2") / "e.pdf"))
    assert d.texto.strip() == ""
    assert any("sem texto" in a for a in d.avisos)


def _ocr_falso(pagina):
    return [("Fulano Teste", fitz.Rect(50, 50, 200, 70))]


def test_pagina_curta_sem_imagem_e_lida():
    """Assinatura com só um nome: menos de MIN_CARACTERES, mas sem imagem, não pode sumir."""
    caminho = F.pasta_temporaria("leitura_pdf3") / "a.pdf"
    doc = fitz.open()
    doc.new_page(width=595, height=842).insert_text((72, 72), "Ana Sá", fontname="helv", fontsize=11)
    doc.save(str(caminho))
    d = ler_pdf(caminho)
    assert "Ana Sá" in d.texto
    assert len(d.origens) == len(d.texto)
    o = d.origens[d.texto.index("Ana Sá")]
    assert isinstance(o, OrigemPdf) and o.pagina == 0 and not o.ocr


def test_escaneado_com_ocr_falso_usa_ocr():
    d = ler_pdf(F.contrato_escaneado(F.pasta_temporaria("leitura_pdf4") / "e.pdf"), ocr=_ocr_falso)
    assert d.tipo == "pdf_ocr" and d.paginas_ocr == [0]
    assert "Fulano Teste" in d.texto
    assert d.origens[d.texto.index("F")].ocr is True


def test_pagina_com_imagem_inteira_e_texto_nativo_faz_ocr_e_fica_misto():
    caminho = F.pasta_temporaria("leitura_pdf5") / "m.pdf"
    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 8, 8), False)
    pix.set_rect(pix.irect, (240, 240, 240))
    pagina.insert_image(pagina.rect, pixmap=pix)
    pagina.insert_text((72, 72), "Texto nativo do documento de teste, com mais de vinte caracteres",
                       fontname="helv", fontsize=11)
    doc.save(str(caminho))
    d = ler_pdf(caminho, ocr=_ocr_falso)
    assert "Texto nativo do documento" in d.texto and "Fulano Teste" in d.texto
    assert d.paginas_ocr == [0] and d.tipo == "pdf_misto"


def test_imagem_grande_com_texto_sem_ocr_gera_aviso():
    caminho = F.pasta_temporaria("leitura_pdf6") / "g.pdf"
    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 8, 8), False)
    pagina.insert_image(pagina.rect, pixmap=pix)
    pagina.insert_text((72, 72), "Texto nativo do documento de teste, com mais de vinte caracteres",
                       fontname="helv", fontsize=11)
    doc.save(str(caminho))
    d = ler_pdf(caminho)
    assert d.paginas_ocr == []
    assert any("não foi lida por OCR" in a for a in d.avisos)


def test_imagem_pequena_colada_com_texto_passa_pelo_ocr():
    # identidade colada (~16% da página) numa página com bastante texto nativo
    caminho = F.contrato_com_documento_colado(F.pasta_temporaria("leitura_pdf8") / "colado.pdf")
    d = ler_pdf(caminho, ocr=_ocr_falso)
    assert d.paginas_ocr == [0] and d.tipo == "pdf_misto"
    assert "Fulano Teste" in d.texto and F.CPF in d.texto
    sem = ler_pdf(caminho)
    assert sem.paginas_ocr == [] and any("página 1 tem imagem que não foi lida por OCR" in a for a in sem.avisos)


def test_imagem_minuscula_nao_passa_pelo_ocr():
    # imagem de menos de 3% da página (um ícone) não obriga o OCR
    caminho = F.pasta_temporaria("leitura_pdf9") / "icone.pdf"
    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 8, 8), False)
    pagina.insert_image(fitz.Rect(500, 40, 540, 80), pixmap=pix)
    pagina.insert_text((72, 72), "Texto nativo do documento de teste, com mais de vinte caracteres",
                       fontname="helv", fontsize=11)
    doc.save(str(caminho))
    d = ler_pdf(caminho, ocr=_ocr_falso)
    assert d.paginas_ocr == [] and not d.avisos


def _pdf_nome_na_virada(caminho):
    """Duas páginas: o nome do titular começa na última linha do corpo da página 1
    e termina na primeira da página 2. Na página 1 o fluxo do PDF traz a linha do
    nome ANTES de outro bloco do corpo e do rodapé (como nos PDFs reais)."""
    doc = fitz.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((72, 700), "Titular: Zuleiva Maria", fontname="helv", fontsize=11)
    p1.insert_text((72, 120), "Cláusula primeira do contrato sintético de teste.", fontname="helv", fontsize=11)
    p1.insert_text((72, 820), "Página 1 de 2", fontname="helv", fontsize=9)
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text((72, 100), "Fernandes, inscrita no CPF 111.444.777-35.", fontname="helv", fontsize=11)
    p2.insert_text((72, 820), "Página 2 de 2", fontname="helv", fontsize=9)
    doc.save(str(caminho))
    return caminho


def test_ordem_de_leitura_junta_o_nome_da_virada_de_pagina():
    d = ler_pdf(_pdf_nome_na_virada(F.pasta_temporaria("leitura_pdf10") / "v.pdf"))
    assert "Zuleiva Maria\nFernandes" in d.texto, repr(d.texto)
    assert len(d.origens) == len(d.texto)


def test_rodape_vai_para_o_fim_do_texto_e_mantem_a_origem():
    d = ler_pdf(_pdf_nome_na_virada(F.pasta_temporaria("leitura_pdf11") / "v.pdf"))
    t = d.texto
    assert t.index("Página 1 de 2") > t.index("Fernandes") and t.index("Página 2 de 2") > t.index("Fernandes"), repr(t)
    assert t.index("Página 1 de 2") < t.index("Página 2 de 2")
    assert t.index("Cláusula primeira") < t.index("Titular")  # corpo em ordem de leitura
    o = d.origens[t.index("Página 1 de 2")]
    assert isinstance(o, OrigemPdf) and o.pagina == 0 and o.rect[1] > 790
    o = d.origens[t.index("Página 2 de 2")]
    assert o.pagina == 1


def test_cabecalho_baixo_selo_vertical_e_cabecalho_repetido_nao_ficam_entre_as_paginas():
    caminho = F.pasta_temporaria("leitura_pdf12") / "m.pdf"
    doc = fitz.open()
    f = dict(fontname="helv", fontsize=11)
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((72, 60), "Cabeçalho Baixo Sintético", **f)                       # baseline ~60 pt (7%)
    p1.insert_text((72, 110), "Contrato Sintético de Prestação de Serviços", **f)    # repete na página 2, na faixa de cima (15%)
    p1.insert_text((72, 700), "Titular: Zuleiva Maria", **f)
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text((72, 60), "Cabeçalho Baixo Sintético", **f)
    p2.insert_text((72, 110), "Contrato Sintético de Prestação de Serviços", **f)
    p2.insert_text((300, 400), "Selo vertical no meio", rotate=90, **f)               # linha não horizontal
    p2.insert_text((18, 500), "Selo na margem lateral", rotate=90, **f)
    p2.insert_text((72, 300), "Fernandes, inscrita no CPF 111.444.777-35.", **f)
    doc.save(str(caminho))
    t = ler_pdf(caminho).texto
    assert "Zuleiva Maria\nFernandes" in t, repr(t)
    depois = t.index("Fernandes")
    for lixo in ("Cabeçalho Baixo Sintético", "Selo vertical no meio", "Selo na margem lateral",
                 "Contrato Sintético de Prestação"):
        assert lixo in t and t.index(lixo) > depois, (lixo, t)


def test_pdf_com_senha_levanta_erro():
    caminho = F.pasta_temporaria("leitura_pdf7") / "s.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Conteúdo protegido do documento de teste", fontname="helv")
    doc.save(str(caminho), encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="dono", user_pw="usuario")
    try:
        ler_pdf(caminho)
    except ErroDeLeitura as e:
        assert "senha" in str(e)
    else:
        raise AssertionError("PDF com senha deveria levantar ErroDeLeitura")


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
