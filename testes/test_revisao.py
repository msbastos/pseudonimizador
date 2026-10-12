# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
from pathlib import Path

import fabrica as F
from pseudonimizador.leitura import Documento
from pseudonimizador.motor.mapa import normalizar
from pseudonimizador.motor.trocas import aplicar_trocas
from pseudonimizador.revisao import Revisao

TEXTO = "\n".join(F.LINHAS_CONTRATO) + "\nObservação: a senhora Pereira assinou.\n"


def _rev():
    return Revisao(Documento(Path("x.docx"), "docx", TEXTO, [None] * len(TEXTO)))


def test_tudo_aceito_por_padrao_e_nada_em_claro():
    r = _rev()
    res = r.fechar()
    saida = aplicar_trocas(TEXTO, res.trocas)
    for valor in (F.PESSOA_1, F.PESSOA_2, F.EMPRESA, F.CPF, F.CNPJ, F.EMAIL):
        assert valor not in saida, (valor, saida)
    assert "Cláusula 1ª" in saida


def test_recusar_identificador_deixa_em_claro():
    r = _rev()
    r.recusar(("email", normalizar(F.EMAIL)))
    saida = aplicar_trocas(TEXTO, r.fechar().trocas)
    assert F.EMAIL in saida and F.CPF not in saida


def test_recusar_cpf_deixa_em_claro():
    r = _rev()
    r.recusar(("cpf", normalizar(F.CPF)))
    saida = aplicar_trocas(TEXTO, r.fechar().trocas)
    assert F.CPF in saida and F.EMAIL not in saida


def test_recusar_pessoa_deixa_em_claro():
    r = _rev()
    r.recusar(("pessoa", normalizar(F.PESSOA_2)))
    saida = aplicar_trocas(TEXTO, r.fechar().trocas)
    assert F.PESSOA_2 in saida and F.PESSOA_1 not in saida


def test_acrescentar_nome_que_escapou():
    r = _rev()
    item = r.acrescentar("senhora Pereira", "outro")
    assert item.acrescido and item.ocorrencias
    saida = aplicar_trocas(TEXTO, r.fechar().trocas)
    assert "senhora Pereira" not in saida
    try:
        r.acrescentar("Nome Que Não Existe", "pessoa")
    except ValueError:
        pass
    else:
        raise AssertionError("deveria recusar valor ausente")


def test_mapa_so_com_tokens_usados_e_contexto():
    r = _rev()
    res = r.fechar()
    usados = {t.token for t in res.trocas}
    assert set(res.mapa["tokens"]) == usados
    i = TEXTO.index(F.CPF)
    assert F.CPF in r.contexto(i, i + len(F.CPF))


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
