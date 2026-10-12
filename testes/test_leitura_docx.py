# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fabrica as F
from pseudonimizador.leitura.docx_ import ler_docx
from pseudonimizador.leitura.modelo import OrigemDocx


def _doc():
    return ler_docx(F.contrato_docx(F.pasta_temporaria("leitura_docx") / "c.docx"))


def test_texto_inclui_corpo_tabela_cabecalho_hyperlink_insercao_e_caixa():
    d = _doc()
    assert d.tipo == "docx"
    assert "LOCADOR: Maria Aparecida Pereira, brasileira" in d.texto       # nome partido entre runs
    assert d.texto.count(F.PESSOA_1) >= 5   # parágrafo, assinatura, tabela, cabeçalho, caixa de texto
    assert F.EMAIL in d.texto                                               # hyperlink
    assert "Testemunha: " + F.PESSOA_2 in d.texto                           # revisão aceita
    assert "Fiadora: " + F.PESSOA_1 in d.texto                              # caixa de texto


def test_origens_alinhadas_ao_texto():
    d = _doc()
    assert len(d.origens) == len(d.texto)
    i = d.texto.index("recida Pereira")
    o = d.origens[i]
    assert isinstance(o, OrigemDocx) and o.run == 1 and o.pos == 0
    assert all(d.origens[k] is None for k, c in enumerate(d.texto) if c == "\n")


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
