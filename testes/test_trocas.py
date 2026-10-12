# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import unicodedata
from pseudonimizador.motor import mapa as M
from pseudonimizador.motor.pseudonimizador import pseudonimizar, texto_limpo
from pseudonimizador.motor.trocas import Troca, aplicar_trocas, limpar_com_indices, trocas

TEXTO = ("LOCADOR: Maria Aparecida Pereira, CPF 111.444.777-35, residente na Rua das Acácias, 120, "
         "telefone (51) 99876-5432, e-mail contato@exemplo.com.br.\n"
         "LOCATÁRIA: Exemplo Comércio de Tecidos Ltda., CNPJ 11.222.333/0001-81.")


def _mapa():
    mapa = M.novo_mapa()
    M.token_para(mapa, "PESSOA", "pessoa", "Maria Aparecida Pereira")
    M.token_para(mapa, "EMPRESA", "pj", "Exemplo Comércio de Tecidos Ltda.")
    return mapa


def test_aplicar_trocas_da_o_mesmo_que_pseudonimizar():
    t = trocas(TEXTO, _mapa())
    assert aplicar_trocas(TEXTO, t) == pseudonimizar(TEXTO, _mapa())
    assert all(isinstance(x, Troca) for x in t)
    assert [x.ini for x in t] == sorted(x.ini for x in t)


def test_posicoes_apontam_o_trecho_original():
    t = trocas(TEXTO, _mapa())
    trechos = {TEXTO[x.ini:x.fim] for x in t}
    assert "Maria Aparecida Pereira" in trechos
    assert "111.444.777-35" in trechos


def test_texto_decomposto_e_hifen_condicional():
    original = unicodedata.normalize("NFD", "Assina João Carlos Souza e MA­RIA APARECIDA PEREIRA.")
    mapa = M.novo_mapa()
    M.token_para(mapa, "PESSOA", "pessoa", "João Carlos Souza")
    M.token_para(mapa, "PESSOA", "pessoa", "Maria Aparecida Pereira")
    t = trocas(original, mapa)
    assert texto_limpo(aplicar_trocas(original, t)) == pseudonimizar(original, mapa)
    assert all(original[x.ini:x.fim].strip() for x in t)


def test_limpar_com_indices():
    original = "é a​b"
    limpo, ini, fim = limpar_com_indices(original)
    assert limpo == texto_limpo(original)
    assert len(limpo) == len(ini) == len(fim)
    assert (ini[0], fim[0]) == (0, 2)        # "é" composto vem dos dois caracteres


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
