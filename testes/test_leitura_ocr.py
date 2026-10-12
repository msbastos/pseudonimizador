# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fabrica as F
from pseudonimizador.leitura import ErroDeLeitura, ler
from pseudonimizador.motor.mapa import normalizar


def test_escaneado_lido_por_ocr():
    d = ler(F.contrato_escaneado(F.pasta_temporaria("ocr") / "e.pdf"))
    assert d.tipo == "pdf_ocr" and d.paginas_ocr == [0]
    n = normalizar(d.texto)
    for esperado in ("locador", "maria aparecida pereira", "111.444.777-35", "clausula"):
        assert esperado in n, f"OCR não leu {esperado!r}: {d.texto[:300]!r}"
    o = d.origens[d.texto.index("1")]
    assert o.ocr and o.pagina == 0


def test_erros_de_leitura():
    import fitz
    pasta = F.pasta_temporaria("erros")
    (pasta / "x.txt").write_text("texto", encoding="utf-8")
    (pasta / "quebrado.docx").write_bytes(b"isto nao e um zip")
    doc = fitz.open(); doc.new_page()
    doc.save(str(pasta / "senha.pdf"), encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="dono", user_pw="usuario")
    for nome, trecho in (("x.txt", "formato"), ("quebrado.docx", "DOCX"), ("senha.pdf", "senha")):
        try:
            ler(pasta / nome)
        except ErroDeLeitura as e:
            assert trecho in str(e), str(e)
        else:
            raise AssertionError(f"{nome} deveria falhar")


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
