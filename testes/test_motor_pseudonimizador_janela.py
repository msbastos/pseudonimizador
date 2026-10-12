# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
r"""Pseudonimizador 0.5.0, Task 3: a troca de um nome de 2+ palavras cuja
1a palavra esta' em minusculas e alguma outra tem maiuscula.

Caso de producao (28/09/2026): "o condominio Alfa", "a reclamante joana
Pereira Lima" — a 1a palavra minuscula (o substantivo comum, ou o nome
digitado assim) nao abria a janela, que exigia a 1a maiuscula ou a janela
toda minuscula. A guarda, que compara sem caixa, via o nome e parava a
sessao: com razao, porque ele estava em claro. Quem se alarga e' a troca:
a 1a palavra minuscula abre a janela se casar EXATAMENTE (sem tolerancia
a erro de OCR) a 1a palavra do nome e outra palavra da janela tiver
maiuscula. Sem tolerancia na 1a, a preposicao a uma letra do prenome nao
e' engolida ("pago para Lucia Santos" com "Mara Lucia Santos" fica); e a
regra nunca vale no alvo permutado nem com a 1a palavra de menos de 3
letras (o sobrenome que e' palavra comum, "30 dias Fulano", e o artigo
seriam engolidos). O prefixo todo em minusculas ficava fora (decisao da
0.4.2); desde a auditoria da caixa (05/10/2026, #8; pseudonimizador
0.5.20) e' trocado como os outros, salvo quando so' tem palavra comum.

Nomes inventados.

Rodar:  python -X utf8 testes/test_pseudonimizador_janela.py
"""
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pseudonimizador.motor.mapa import token_para  # noqa: E402
from pseudonimizador.motor.pseudonimizador import pseudonimizar  # noqa: E402


def _mapa(*pessoas):
    m = {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}
    for prefixo, nome in pessoas:
        token_para(m, prefixo, "pessoa", nome, papel=prefixo.title())
    return m


def test_primeira_palavra_minuscula_exata_com_outra_maiuscula_troca():
    m = _mapa(("RECLAMANTE", "Joana Pereira Lima"))
    for texto in ("a reclamante joana Pereira Lima disse", "a reclamante joana pereira Lima disse"):
        t = pseudonimizar(texto, m)
        assert t == "a reclamante [[RECLAMANTE_1]] disse", t


def test_prefixo_com_primeira_palavra_minuscula_tambem():
    m = _mapa(("RECLAMANTE", "Fulana Pereira da Costa"))
    t = pseudonimizar("formulados por fulana PEREIRA\nno mérito, julgo", m)
    assert t == "formulados por [[RECLAMANTE_1]]\nno mérito, julgo", repr(t)


def test_preposicao_a_uma_letra_do_prenome_nao_e_engolida():
    # nao-regressao obrigatoria (cetico da troca incompleta)
    m = _mapa(("RECLAMANTE", "Mara Lucia Santos"))
    t = pseudonimizar("pago para Lucia Santos em dinheiro", m)
    assert t == "pago para Lucia Santos em dinheiro", t
    t = pseudonimizar("a mara Lucia Santos recebeu", m)
    assert t == "a [[RECLAMANTE_1]] recebeu", t


def test_prefixo_todo_minusculo_tambem_e_trocado():
    # auditoria da caixa (#8): a caixa nao decide — o prefixo exclusivo da parte em minusculas e' ela
    m = _mapa(("RECLAMANTE", "Fulana Pereira da Costa"))
    assert pseudonimizar("a fulana pereira assinou", m) == "a [[RECLAMANTE_1]] assinou"
    # o prefixo feito so' de palavra comum continua fora
    m = _mapa(("RECLAMANTE", "Rosa Clara da Costa"))
    assert pseudonimizar("a rosa clara floresceu", m) == "a rosa clara floresceu"


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
