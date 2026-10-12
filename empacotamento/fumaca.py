# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Fumaça da montagem: roda NO PYTHON EMBARCADO (build/app/python/python.exe), a
partir de OUTRA pasta (build/), com a rede bloqueada e só com dados sintéticos,
o que o Pseudonimizador faz de verdade: importa tudo, lê DOCX, PDF com texto e
PDF escaneado (OCR), gera a saída reversível e restaura. Importar não basta: o
pacote sem sympy e com opencv-python-headless (spec §2) só é aceito se isto
passar. Sai com 0 se tudo passa; 1 e a lista FALHA se algo falha."""
from __future__ import annotations

import socket
import sys
import tempfile
import traceback
import warnings
from pathlib import Path

warnings.simplefilter("ignore")
LOCAIS = {"127.0.0.1", "::1", "localhost"}
PESSOA = "Maria Aparecida Pereira"            # sintético (o mesmo de testes/fabrica.py)
CPF = "111.444.777-35"
LINHAS = ["CONTRATO DE LOCAÇÃO RESIDENCIAL",
          f"LOCADOR: {PESSOA}, portadora do CPF {CPF}, residente na Rua das Acácias, 120.",
          "Cláusula 1ª. O aluguel mensal é de R$ 1.500,00.", "Porto Alegre, 11 de outubro de 2026."]
_tentativas: list[str] = []


def _bloquear_rede():
    def host(e):
        return e[0] if isinstance(e, tuple) else str(e)
    conn, cria, gai = socket.socket.connect, socket.create_connection, socket.getaddrinfo

    def connect(self, e):
        if host(e) not in LOCAIS:
            _tentativas.append(host(e))
            raise OSError("rede bloqueada na fumaça")
        return conn(self, e)

    def create(e, *a, **k):
        if host(e) not in LOCAIS:
            _tentativas.append(host(e))
            raise OSError("rede bloqueada na fumaça")
        return cria(e, *a, **k)

    def getaddrinfo(h, *a, **k):
        if h is not None and h not in LOCAIS:
            _tentativas.append(str(h))
            raise OSError("rede bloqueada na fumaça")
        return gai(h, *a, **k)
    socket.socket.connect, socket.create_connection, socket.getaddrinfo = connect, create, getaddrinfo


def _docx(caminho: Path) -> Path:
    import docx
    d = docx.Document()
    for l in LINHAS:
        d.add_paragraph(l)
    d.save(str(caminho))
    return caminho


def _pdf(caminho: Path) -> Path:
    import pymupdf
    d = pymupdf.open()
    p = d.new_page()
    for i, l in enumerate(LINHAS):
        p.insert_text((72, 100 + 20 * i), l, fontsize=11)
    d.save(str(caminho))
    d.close()
    return caminho


def _pdf_escaneado(caminho: Path) -> Path:
    """A mesma página, mas só como imagem (sem camada de texto): obriga o OCR."""
    import pymupdf
    origem = pymupdf.open()
    p = origem.new_page()
    for i, l in enumerate(LINHAS):
        p.insert_text((72, 100 + 20 * i), l, fontsize=14)
    pix = p.get_pixmap(dpi=200)
    d = pymupdf.open()
    pagina = d.new_page(width=p.rect.width, height=p.rect.height)
    pagina.insert_image(pagina.rect, pixmap=pix)
    d.save(str(caminho))
    d.close()
    origem.close()
    return caminho


def _gerar(arquivo: Path, pasta: Path):
    from pseudonimizador.leitura import ler
    from pseudonimizador.revisao import Revisao
    from pseudonimizador.saida import gerar
    doc = ler(arquivo)
    g = gerar(doc, Revisao(doc).fechar(), formato="layout", modo="reversivel",
              pasta_saida=pasta / "Saida", pasta_mapas=pasta / "Mapas")
    assert Path(g.saida).is_file(), g.saida
    return doc, g


def importacoes():
    import cv2, docx, fitz, numpy, onnxruntime, pyclipper, pymupdf, rapidocr, shapely  # noqa: F401,E401
    import pseudonimizador
    from pseudonimizador import deteccao, estado, leitura, motor, restaurar, revisao, saida, web  # noqa: F401
    from pseudonimizador.web import abrir, pasta_monitorada, registro, servidor  # noqa: F401
    assert "CPUExecutionProvider" in onnxruntime.get_available_providers()
    assert pseudonimizador.VERSAO


def codigo_do_pacote():
    """O que importou é o de build/app (o ".." do ._pth), não o do repositório nem o site-packages do usuário."""
    import pseudonimizador
    raiz = Path(pseudonimizador.__file__).resolve().parents[1]
    assert raiz.name == "app" and (raiz / "python" / "python314._pth").is_file(), raiz
    assert not any("APPDATA" in p.upper() or "site-packages" in p and "app" not in p for p in sys.path), sys.path


def docx_pseudonimizar_e_restaurar():
    from pseudonimizador.leitura import ler
    from pseudonimizador.restaurar import mapa_do_docx, restaurar_docx
    with tempfile.TemporaryDirectory() as td:
        pasta = Path(td)
        _, g = _gerar(_docx(pasta / "contrato.docx"), pasta)
        texto = ler(Path(g.saida)).texto
        assert PESSOA not in texto and CPF not in texto and "[[" in texto, texto[:200]
        mapa = mapa_do_docx(Path(g.saida), pasta / "Mapas")
        assert mapa is not None
        n = restaurar_docx(Path(g.saida), pasta / "restaurado.docx", mapa)
        assert n >= 1 and PESSOA in ler(pasta / "restaurado.docx").texto


def pdf_com_texto():
    from pseudonimizador.leitura import ler
    with tempfile.TemporaryDirectory() as td:
        pasta = Path(td)
        doc, g = _gerar(_pdf(pasta / "contrato.pdf"), pasta)
        assert PESSOA in doc.texto
        assert PESSOA not in ler(Path(g.saida)).texto


def pdf_escaneado_ocr():
    with tempfile.TemporaryDirectory() as td:
        pasta = Path(td)
        doc, g = _gerar(_pdf_escaneado(pasta / "escaneado.pdf"), pasta)
        assert "Maria" in doc.texto and "Pereira" in doc.texto, doc.texto[:200]   # o OCR leu a imagem
        assert Path(g.saida).stat().st_size > 0


def rede_bloqueada():
    assert not _tentativas, f"tentativas de rede durante a fumaça: {_tentativas}"


VERIFICACOES = (importacoes, codigo_do_pacote, docx_pseudonimizar_e_restaurar, pdf_com_texto, pdf_escaneado_ocr,
                rede_bloqueada)


def main() -> int:
    _bloquear_rede()
    falhas = []
    for verificacao in VERIFICACOES:
        try:
            verificacao()
            print(f"  ok     {verificacao.__name__}")
        except BaseException as e:  # noqa: BLE001 — lista tudo o que falha, não só a primeira
            falhas.append(verificacao.__name__)
            print(f"  FALHA  {verificacao.__name__}: {e!r}")
            traceback.print_exc(limit=3)
    if falhas:
        print("fumaça falhou em: " + ", ".join(falhas))
        return 1
    print(f"fumaça: {len(VERIFICACOES)} verificações passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
