# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Documentos SINTÉTICOS para os testes (nomes, números e endereço inventados;
o CPF e o CNPJ são os exemplos clássicos de dígito verificador válido)."""
import _base  # noqa: F401
import shutil
from pathlib import Path

from _base import RAIZ

PESSOA_1 = "Maria Aparecida Pereira"
PESSOA_2 = "João Carlos Souza"
EMPRESA = "Exemplo Comércio de Tecidos Ltda."
CPF = "111.444.777-35"
CNPJ = "11.222.333/0001-81"
EMAIL = "contato@exemplo.com.br"
TELEFONE = "(51) 99876-5432"
ENDERECO = "Rua das Acácias, 120"

LINHAS_CONTRATO = [
    "CONTRATO DE LOCAÇÃO RESIDENCIAL",
    f"LOCADOR: {PESSOA_1}, brasileira, casada, portadora do CPF {CPF}, residente na {ENDERECO}, "
    f"telefone {TELEFONE}, e-mail {EMAIL}.",
    f"LOCATÁRIA: {EMPRESA}, inscrita no CNPJ {CNPJ}, representada por {PESSOA_2}.",
    "Cláusula 1ª. O aluguel mensal é de R$ 1.500,00, com vencimento no dia 10.",
    "Cláusula 2ª. O prazo da locação é de 30 meses.",
    "Porto Alegre, 11 de outubro de 2026.",
    f"{PESSOA_1} — {PESSOA_2}",
]

_NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_NS_WPS = "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
_NS_MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"


def pasta_temporaria(nome: str) -> Path:
    pasta = RAIZ / "saida_testes" / nome
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True)
    return pasta


def contrato_docx(caminho: Path) -> Path:
    """Contrato com: nome partido entre dois runs (o segundo em negrito), tabela,
    cabeçalho, hyperlink, caixa de texto, revisão controlada, comentário e autor
    nos metadados."""
    import docx
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls
    d = docx.Document()
    d.core_properties.author = "Autor Original Sintético"
    d.core_properties.last_modified_by = "Editor Sintético"
    d.sections[0].header.paragraphs[0].text = f"Contrato — {PESSOA_1}"
    d.add_paragraph(LINHAS_CONTRATO[0])
    p = d.add_paragraph("LOCADOR: Maria Apa")
    p.add_run("recida Pereira").bold = True
    p.add_run(LINHAS_CONTRATO[1][len("LOCADOR: " + PESSOA_1):])
    for linha in LINHAS_CONTRATO[2:]:
        d.add_paragraph(linha)
    tabela = d.add_table(rows=1, cols=2)
    tabela.cell(0, 0).text = "Locador"
    tabela.cell(0, 1).text = PESSOA_1
    # hyperlink com o e-mail
    ph = d.add_paragraph("Contato: ")
    ph._p.append(parse_xml(
        f'<w:hyperlink {nsdecls("w")}><w:r><w:t>{EMAIL}</w:t></w:r></w:hyperlink>'))
    # revisão controlada: inserção com o nome da segunda pessoa
    pr = d.add_paragraph("Testemunha: ")
    pr._p.append(parse_xml(
        f'<w:ins {nsdecls("w")} w:id="1" w:author="Revisor" w:date="2026-10-11T00:00:00Z">'
        f'<w:r><w:t>{PESSOA_2}</w:t></w:r></w:ins>'))
    # caixa de texto (só o conteúdo txbx; basta para o Word e para o leitor)
    pc = d.add_paragraph()
    pc._p.append(parse_xml(
        f'<w:r xmlns:w="{_NS_W}" xmlns:wps="{_NS_WPS}" xmlns:mc="{_NS_MC}">'
        f'<mc:AlternateContent><mc:Choice Requires="wps">'
        f'<w:drawing><wps:txbx><w:txbxContent><w:p><w:r><w:t>Fiadora: {PESSOA_1}</w:t></w:r></w:p>'
        f'</w:txbxContent></wps:txbx></w:drawing></mc:Choice></mc:AlternateContent></w:r>'))
    d.add_comment(d.paragraphs[1].runs[0], text="Conferir o CPF", author="Comentarista Sintético")
    caminho = Path(caminho)
    d.save(str(caminho))
    return caminho


def _pdf_de_linhas(pagina, tamanho: float = 11):
    import fitz
    area = pagina.rect + (56, 56, -56, -56)
    pagina.insert_textbox(area, "\n\n".join(LINHAS_CONTRATO), fontsize=tamanho, fontname="helv")


def contrato_pdf(caminho: Path, girar: int = 0) -> Path:
    import fitz
    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)
    _pdf_de_linhas(pagina)
    if girar:
        pagina.set_rotation(girar)
    doc.set_metadata({"author": "Autor Original Sintético", "title": f"Contrato {PESSOA_1}"})
    caminho = Path(caminho)
    doc.save(str(caminho))
    return caminho


def contrato_escaneado(caminho: Path) -> Path:
    """Página só com imagem (sem camada de texto), como um papel digitalizado."""
    import fitz
    fonte = fitz.open()
    pagina = fonte.new_page(width=595, height=842)
    _pdf_de_linhas(pagina, tamanho=14)
    pix = pagina.get_pixmap(dpi=200)
    doc = fitz.open()
    nova = doc.new_page(width=595, height=842)
    nova.insert_image(nova.rect, pixmap=pix)
    caminho = Path(caminho)
    doc.save(str(caminho))
    return caminho
