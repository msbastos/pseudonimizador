# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fabrica as F
from pseudonimizador.deteccao import detectar

TEXTO = "\n".join(F.LINHAS_CONTRATO)


def _por_categoria(texto):
    achados = {}
    for o in detectar(texto):
        achados.setdefault(o.categoria, set()).add(o.valor)
    return achados


def test_contrato_completo():
    a = _por_categoria(TEXTO)
    assert F.PESSOA_1 in a["pessoa"] and F.PESSOA_2 in a["pessoa"], a
    assert F.EMPRESA in a["empresa"], a
    assert F.CPF in a["cpf"] and F.CNPJ in a["cnpj"], a
    assert F.EMAIL in a["email"], a
    assert any(F.TELEFONE in v for v in a["telefone"]), a
    assert any("Acácias" in v for v in a["endereco"]), a


def test_sem_falso_positivo_nas_clausulas():
    a = _por_categoria("Cláusula 1ª. O aluguel mensal é de R$ 1.500,00.\nPorto Alegre, 11 de outubro de 2026.")
    assert not a.get("pessoa") and not a.get("empresa"), a


def test_nome_fora_do_lexico_pela_ancora_e_pela_qualificacao():
    a = _por_categoria("CONTRATANTE: Xandrelo Quintebor Vasques, brasileiro, solteiro.\n"
                       "e Ylmara Torquesi Bento, portadora do RG 1234567.")
    assert "Xandrelo Quintebor Vasques" in a["pessoa"], a
    assert "Ylmara Torquesi Bento" in a["pessoa"], a


def test_caixa_nao_decide():
    a = _por_categoria("assinado por maria aparecida pereira em 2026.")
    assert "maria aparecida pereira" in a["pessoa"], a


def test_ocorrencias_ordenadas_sem_sobreposicao():
    oc = detectar(TEXTO)
    for x, y in zip(oc, oc[1:]):
        assert x.fim <= y.ini, (x, y)
    assert all(TEXTO[o.ini:o.fim] == o.valor for o in oc)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
