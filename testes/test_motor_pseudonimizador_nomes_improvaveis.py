# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Descoberta de testemunhas nao pode registrar "nomes" feitos de palavras
comuns, e o primeiro nome isolado nunca e' conectivo/palavra comum.

Caso observado em produção (08/09/2026): descobrir_pessoas() roda sobre
TODAS as pecas integrais (muitas contestacoes, dezenas de manifestacoes) e
RE_TESTEMUNHA, ancorada em "testemunha(s)", capturou como nome qualquer
sequencia de maiusculas que viesse depois: "DA RECLAMANTE", o nome de um
banco, o nome da cidade, "NÃO COMPROVADA", o nome de uma empresa de
servicos. A regra do "primeiro nome isolado, quando inequivoco" fez o
resto: todo "Da"/"DA", "Reclamante", "Banco", o nome da cidade e "Não" do
dossie viraram [[TESTEMUNHA_n]] — o texto ficou ilegivel ("§ 8º,
[[TESTEMUNHA_12]] CLT", "[[TESTEMUNHA_3]] ALFA").

Regras que estes testes trancam:
  - candidato a testemunha/perito perde as palavras comuns iniciais e so'
    entra no mapa se sobrarem 2+ palavras de nome;
  - primeiro nome isolado so' substitui quando tem 3+ letras e nao e'
    palavra comum (conectivo, "nao", "banco", "reclamante", cidade...);
  - nomes de verdade continuam sendo descobertos e substituidos.

Rodar:  python testes/test_pseudonimizador_nomes_improvaveis.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pseudonimizador.motor.mapa import token_para  # noqa: E402
from pseudonimizador.motor.pseudonimizador import (  # noqa: E402
    descobrir_pessoas, pseudonimizar)


def _mapa():
    return {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}


def _valores(m):
    return {i["valor"] for i in m["tokens"].values()}


def test_palavras_comuns_apos_testemunha_nao_viram_nome():
    m = _mapa()
    texto = ("As testemunhas ouvidas não confirmam que o BANCO ALFA "
             "tomava os serviços. TESTEMUNHAS DA RECLAMANTE. Rol de "
             "testemunhas: PORTO VELHO, 10 de maio de 2024. Testemunha, "
             "NÃO COMPROVADA a prestação. Testemunha DOS SANTOS SERVIÇOS.")
    descobrir_pessoas(texto, m)
    assert m["tokens"] == {}, _valores(m)


def test_palavra_comum_inicial_e_descartada_mas_o_nome_fica():
    m = _mapa()
    texto = "Testemunha da reclamante, DA SILVA MARIA DE LOURDES FARIAS, compromissada."
    descobrir_pessoas(texto, m)
    vals = {v.upper() for v in _valores(m)}
    assert vals == {"SILVA MARIA DE LOURDES FARIAS"}, vals


def test_nomes_de_verdade_continuam_sendo_descobertos():
    m = _mapa()
    texto = ("Primeira testemunha do reclamante: MARIA DE LOURDES FARIAS, "
             "compromissada. Testemunha da reclamada, Sr. José Antunes. "
             "O perito Carlos Werle apresentou o laudo.")
    descobrir_pessoas(texto, m)
    vals = {v.upper() for v in _valores(m)}
    assert {"MARIA DE LOURDES FARIAS", "JOSÉ ANTUNES", "CARLOS WERLE"} <= vals, vals
    t = pseudonimizar(texto, m)
    assert "FARIAS" not in t and "Antunes" not in t and "Werle" not in t


def test_primeiro_nome_isolado_nunca_e_palavra_comum():
    m = _mapa()
    # mapa vindo de execucao anterior, ja' contaminado: a regra do primeiro
    # nome isolado nao pode espalhar o estrago pelo texto
    token_para(m, "TESTEMUNHA", "pessoa", "Da Limitação")
    token_para(m, "TESTEMUNHA", "pessoa", "Banco Omega")
    token_para(m, "TESTEMUNHA", "pessoa", "Não Comprovada")
    token_para(m, "TESTEMUNHA", "pessoa", "Reclamante Beltrana")
    token_para(m, "TESTEMUNHA", "pessoa", "Porto Velho")
    texto = ("Multa do art. 477, § 8º, DA CLT. A Reclamante pugna. O Banco "
             "pagava. Não havendo acordo. Porto Velho, 10 de maio.")
    assert pseudonimizar(texto, m) == texto


def test_primeiro_nome_isolado_com_tres_letras_ou_mais_continua_valendo():
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "Beltrana Exemplo Souza")
    assert "[[RECLAMANTE_1]]" in pseudonimizar("disse Beltrana que sim", m)


if __name__ == "__main__":
    testes = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("test_") and callable(f)]
    falhas = 0
    for nome, fn in testes:
        try:
            fn()
            print(f"ok    {nome}")
        except AssertionError as e:
            falhas += 1
            print(f"FALHA {nome}\n      {e}")
    print(f"\n{len(testes) - falhas}/{len(testes)} passaram, {falhas} falha(s)")
    sys.exit(1 if falhas else 0)
