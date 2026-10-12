# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fitz
import fabrica as F
from pseudonimizador.leitura import ler
from pseudonimizador.leitura.ocr import ocr_pagina
from pseudonimizador.motor.mapa import normalizar
from pseudonimizador.revisao import Revisao
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


def test_escaneado_pixels_apagados():
    pasta = F.pasta_temporaria("saida_pdf_ocr")
    destino, _ = _gerar(F.contrato_escaneado(pasta / "e.pdf"), "e - pseudonimizado.pdf")
    with fitz.open(str(destino)) as pdf:
        lido = normalizar(" ".join(t for t, _ in ocr_pagina(pdf[0])))
    assert "maria aparecida pereira" not in lido and "111.444.777-35" not in lido, lido
    assert "locador" in lido


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
