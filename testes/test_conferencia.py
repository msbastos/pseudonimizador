# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import zipfile

import fitz

import fabrica as F
from pseudonimizador.saida.conferencia import conferir, valores_vigiados

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
CPF = "111.444.777-35"


def _mapa(*itens):
    return {"tokens": {f"[[T{i}]]": {"categoria": c, "valor": v} for i, (c, v) in enumerate(itens)}}


def _docx(nome, corpo, extras=None):
    pasta = F.pasta_temporaria(nome)
    caminho = pasta / "x.docx"
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr("word/document.xml", f'<?xml version="1.0"?><w:document {W}><w:body>{corpo}</w:body></w:document>')
        for k, v in (extras or {}).items():
            z.writestr(k, v)
    return caminho


def _achou(corpo, mapa, extras=None):
    return conferir(_docx("conf", corpo, extras), mapa)


PESSOA = _mapa(("pessoa", F.PESSOA_1))


def test_runs_do_mesmo_paragrafo_juntam():
    a, b = F.PESSOA_1.split(" ", 1)
    assert _achou(f"<w:p><w:r><w:t>{a} </w:t></w:r><w:r><w:t>{b}</w:t></w:r></w:p>", PESSOA) == [F.PESSOA_1]


def test_fim_de_paragrafo_separa():
    corpo = f"<w:p><w:r><w:t>{F.PESSOA_1}</w:t></w:r></w:p><w:p><w:r><w:t>Testemunha</w:t></w:r></w:p>"
    assert _achou(corpo, PESSOA) == [F.PESSOA_1]


def test_celula_separa():
    corpo = (f"<w:tbl><w:tr><w:tc><w:p><w:r><w:t>{F.PESSOA_1}</w:t></w:r></w:p></w:tc>"
             "<w:tc><w:p><w:r><w:t>Locador</w:t></w:r></w:p></w:tc></w:tr></w:tbl>")
    assert _achou(corpo, PESSOA) == [F.PESSOA_1]


def test_br_tab_cr_entre_palavras_do_nome():
    a, b, c = F.PESSOA_1.split(" ")
    for marca in ("<w:br/>", "<w:tab/>", "<w:cr/>"):
        corpo = f"<w:p><w:r><w:t>{a}</w:t>{marca}<w:t>{b} {c}</w:t></w:r></w:p>"
        assert _achou(corpo, PESSOA) == [F.PESSOA_1], marca


def test_cpf_seguido_de_paragrafo_com_digito():
    corpo = f"<w:p><w:r><w:t>{CPF}</w:t></w:r></w:p><w:p><w:r><w:t>352</w:t></w:r></w:p>"
    assert _achou(corpo, _mapa(("cpf", CPF))) == [CPF]


def test_rede_de_seguranca_sem_espacos_nem_pontuacao():
    corpo = "<w:p><w:r><w:t>Maria-Aparecida,Pereira</w:t></w:r></w:p>"
    assert _achou(corpo, PESSOA) == [F.PESSOA_1]


def test_docvar_em_atributo():
    extras = {"word/settings.xml": f'<w:settings {W}><w:docVars><w:docVar w:name="n" w:val="{F.PESSOA_1}"/></w:docVars></w:settings>'}
    assert _achou("<w:p/>", PESSOA, extras) == [F.PESSOA_1]


def test_entidade_decodificada():
    mapa = _mapa(("pj", "Silva & Filhos Ltda"))
    assert _achou("<w:p><w:r><w:t>Silva &amp; Filhos Ltda</w:t></w:r></w:p>", mapa) == ["Silva & Filhos Ltda"]


def test_mailto_no_rels():
    mapa = _mapa(("email", "fulano.exemplo@example.com"))
    rels = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="r1" Type="x" Target="mailto:fulano.exemplo@example.com" TargetMode="External"/></Relationships>')
    assert _achou("<w:p/>", mapa, {"word/_rels/document.xml.rels": rels}) == ["fulano.exemplo@example.com"]


def test_sem_vazamento_nao_acusa():
    assert _achou("<w:p><w:r><w:t>[[PESSOA_1]] Testemunha</w:t></w:r></w:p>", PESSOA) == []


def test_valores_curtos_listados():
    mapa = _mapa(("pessoa", "Maria"), ("pj", "Acme"), ("cpf", "123"), ("pessoa", F.PESSOA_1))
    vigiados, pulados = valores_vigiados(mapa, devolver_pulados=True)
    assert vigiados == [F.PESSOA_1] and sorted(pulados) == ["123", "Acme", "Maria"]


def _pdf_com_extras(nome):
    pasta = F.pasta_temporaria(nome)
    doc = fitz.open()
    pg = doc.new_page()
    pg.insert_text((72, 72), "Texto qualquer")
    pg.add_text_annot((100, 100), F.PESSOA_1)
    doc.set_toc([[1, F.PESSOA_1, 1]])
    caminho = pasta / "e.pdf"
    doc.save(str(caminho))
    return caminho


def test_pdf_anotacao_e_toc_sao_vigiados():
    assert conferir(_pdf_com_extras("conf_pdf"), PESSOA) == [F.PESSOA_1]


def test_pdf_anexo_e_xmp_sao_vigiados():
    pasta = F.pasta_temporaria("conf_pdf2")
    doc = fitz.open()
    doc.new_page()
    doc.embfile_add(f"{F.PESSOA_1}.txt", b"x", desc="d")
    caminho = pasta / "a.pdf"
    doc.save(str(caminho))
    assert conferir(caminho, PESSOA) == [F.PESSOA_1]


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
