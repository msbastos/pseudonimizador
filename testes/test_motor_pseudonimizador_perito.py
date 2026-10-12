# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Perito: o nome de verdade entra no mapa; locucao juridica nunca.

Caso observado em produção (27/09/2026): a peticao do perito dizia
"perito nomeado para avaliação de Adicional de Insalubridade" e RE_PERITO,
com o enchimento preguicoso entre "perito" e o nome, pousou na primeira
sequencia de maiusculas — "Adicional de Insalubridade" virou [[PERITO_1]].
O tóken passou a trocar a locucao em todo o dossie (inclusive "do
respectivo adicional de insalubridade" na inicial) e o filtro de saida
bloqueava o restaurar-nomes de qualquer minuta que falasse em "adicional
de insalubridade" (valor do mapa em claro). Enquanto isso o nome real do
perito, que vinha da capa, ficou em claro: a linha seguinte da capa era o
marcador PAGINA_CAPA_PROCESSO_PJE, colado ao nome como "continuacao", e o
nome assim sujo nunca casava no texto.

Nomes aqui sao inventados.

Rodar:  python -X utf8 testes/test_pseudonimizador_perito.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pseudonimizador.motor.mapa import token_para  # noqa: E402
from pseudonimizador.motor.pseudonimizador import (  # noqa: E402
    construir_mapa, descobrir_pessoas, prefixo_do_papel, pseudonimizar)

NOME = "CARLOS DE ALMEIDA WERLE"


def _mapa():
    return {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}


def _valores(m):
    return {normalizado.upper() for normalizado in
            (i["valor"] for i in m["tokens"].values())}


def test_perito_nomeado_para_avaliacao_de_adicional_nao_vira_nome():
    m = _mapa()
    texto = ("CARLOS DE ALMEIDA WERLE, perito nomeado para avaliação de "
             "Adicional de Insalubridade, vem, respeitosamente, apresentar "
             "o laudo.")
    descobrir_pessoas(texto, m)
    assert not any(t.startswith("[[PERITO_") for t in m["tokens"]), m["tokens"]
    assert pseudonimizar("não efetuava o pagamento do respectivo adicional "
                         "de insalubridade", m) == \
        "não efetuava o pagamento do respectivo adicional de insalubridade"


def test_perito_nomeado_para_avaliacao_de_insalubridade_minusculo():
    m = _mapa()
    texto = ("Laudo pericial. O perito nomeado para avaliação de "
             "insalubridade nos autos da Reclamatória Trabalhista em epígrafe "
             "passa a expor.")
    descobrir_pessoas(texto, m)
    assert m["tokens"] == {}, m["tokens"]


def test_locucoes_de_pericia_em_caixa_alta_nao_viram_nome():
    m = _mapa()
    descobrir_pessoas("PERITO NOMEADO PARA AVALIAÇÃO DE ADICIONAL DE "
                      "INSALUBRIDADE E PERICULOSIDADE.", m)
    descobrir_pessoas("Perito: Engenheiro de Segurança do Trabalho.", m)
    descobrir_pessoas("honorários do perito Adicional de Periculosidade", m)
    assert m["tokens"] == {}, m["tokens"]


def test_perito_de_verdade_continua_descoberto():
    for texto in ("O perito Carlos Werle apresentou o laudo.",
                  "Perito: Carlos Werle",
                  "O perito do juízo, Dr. Carlos Werle, engenheiro, apresentou.",
                  "Nomeio perito o engenheiro Carlos Werle, que deverá"):
        m = _mapa()
        descobrir_pessoas(texto, m)
        assert "CARLOS WERLE" in _valores(m), (texto, m["tokens"])
        assert "Werle" not in pseudonimizar(texto, m), texto


def test_indice_antigo_com_nome_sujo_ainda_vira_tokien_do_perito():
    # Indices ja' gravados trazem o nome com o marcador colado: o
    # pseudonimizador limpa antes de registrar, e o papel vira PERITO_n.
    m = _mapa()
    indice = {"processo": {"partes": [
        {"papel": "Perito", "nome": f"{NOME} PAGINA_CAPA_PROCESSO_PJE"}]}}
    construir_mapa(indice, m)
    assert list(m["tokens"]) == ["[[PERITO_1]]"], m["tokens"]
    assert m["tokens"]["[[PERITO_1]]"]["valor"] == NOME
    t = pseudonimizar(f"{NOME}\nEngenheiro de Segurança do Trabalho\n"
                      "Resumo: Partes: " + NOME, m)
    assert "WERLE" not in t and "[[PERITO_1]]" in t, t


def test_perito_da_capa_e_do_laudo_ganham_o_mesmo_tokien():
    m = _mapa()
    construir_mapa({"processo": {"partes": [{"papel": "Perito", "nome": NOME}]}}, m)
    descobrir_pessoas(f"Perito: {NOME}", m)
    assert list(m["tokens"]) == ["[[PERITO_1]]"], m["tokens"]


def test_prefixo_do_papel_perito():
    assert prefixo_do_papel("Perito") == "PERITO"
    assert prefixo_do_papel("PERITA") == "PERITO"
    assert prefixo_do_papel("Terceiro Interessado") == "TERCEIRO"


def test_tokien_de_perito_existente_nao_e_afetado():
    m = _mapa()
    token_para(m, "PERITO", "pessoa", "Carlos Werle", papel="perito")
    assert pseudonimizar("adicional de insalubridade; laudo de Carlos Werle", m) \
        == "adicional de insalubridade; laudo de [[PERITO_1]]"


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
