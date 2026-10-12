# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
r"""O lexico de nomes do IBGE (Nomes no Brasil, Censo 2022): prenomes e
sobrenomes com a frequencia, consultados sem caixa nem acento, e o uso dele
no nome do titulo do documento de menor (pseudonimizador._nome_no_rotulo) —
o prenome que a lista escrita 'a mao nao tem e' reconhecido, e o resto de
titulo que nao e' nome continua fora do mapa em qualquer caixa.

Rodar:  python -X utf8 testes/test_lexico_ibge.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pseudonimizador.motor import lexico  # noqa: E402
from pseudonimizador.motor import nivel as nv  # noqa: E402
from pseudonimizador.motor.mapa import normalizar  # noqa: E402


def test_o_arquivo_diz_a_fonte_e_tem_os_dois_rankings():
    dados = json.loads((RAIZ / "pseudonimizador" / "motor" / "lexico_ibge.json").read_text(encoding="utf-8"))
    assert "IBGE" in dados["fonte"] and "2022" in dados["fonte"] and dados["baixado_em"]
    assert len(dados["prenomes"]) >= 5000 and len(dados["sobrenomes"]) >= 5000
    for chave in ("prenomes", "sobrenomes"):
        for nome, freq in dados[chave].items():
            assert nome == normalizar(nome) and nome.isalpha() and isinstance(freq, int) and freq > 0, (chave, nome)


def test_a_frequencia_nao_olha_caixa_nem_acento():
    for forma in ("Kauã", "KAUÃ", "kaua"):
        assert lexico.frequencia_de_prenome(forma) > 0, forma
    for forma in ("Schneider", "SCHNEIDER", "schneider", "Conceição"):
        assert lexico.frequencia_de_sobrenome(forma) > 0, forma
    assert lexico.frequencia_de_prenome("maria") > lexico.frequencia_de_prenome("kaua")
    for palavra in ("copia", "Autenticada", "DOCUMENTOS", "certidão", "verso", ""):
        assert lexico.frequencia_de_prenome(palavra) == 0, palavra


def test_a_lista_escrita_a_mao_nao_muda():
    """PRENOMES e SOBRENOMES seguem pequenos e sem os prenomes que sao palavra comum: o varredor dos Entendimentos
    e o filtro das palavras comuns dependem disso; o ranking do IBGE e' consulta 'a parte."""
    assert len(lexico.PRENOMES) < 400 and len(lexico.SOBRENOMES) < 200
    assert not {"rosa", "vitoria", "franco"} & lexico.PRENOMES


def _nomes_do_rotulo(titulo: str, comuns=frozenset()) -> list:
    from pseudonimizador.motor.pseudonimizador import descobrir_nome_do_rotulo
    mapa = {"tokens": {}, "nivel": nv.PROTEGIDO}
    for nome in nv.nomes_no_rotulo_de_menor(titulo):
        descobrir_nome_do_rotulo(nome, mapa, comuns)
    return [normalizar(i["valor"]) for i in mapa["tokens"].values()]


def _em_toda_caixa(texto: str) -> tuple:
    return (texto, texto.upper(), texto.lower())


def test_prenome_fora_da_lista_a_mao_e_reconhecido_no_titulo():
    for nome in ("Kauã Schneider", "Pietro Schneider da Silva", "Kauã Pietro de Tal"):
        assert normalizar(nome.split()[0]) not in lexico.PRENOMES
        for titulo in _em_toda_caixa("Certidão de nascimento - " + nome):
            assert _nomes_do_rotulo(titulo) == [normalizar(nome)], titulo


def test_resto_de_titulo_continua_fora_do_mapa_com_o_ranking():
    """As frases de rotulo, inclusive as que tem palavra que tambem e' prenome ou sobrenome no ranking."""
    for resto in ("Cópia Autenticada", "Frente e Verso", "Frente Verso", "Cartório Central", "Inteiro Teor",
                  "Via Original", "Cópia Simples", "Carteira de Vacinação", "Comprovante Escolar",
                  "Declaração Escolar", "Termo Aditivo", "Documentos Diversos", "Outros Documentos",
                  "Documentos Pessoais", "Segunda Via", "Registro Civil", "Rosa Branca", "Santa Casa",
                  "Vitória Régia", "Nova Via", "Bela Vista"):
        for titulo in _em_toda_caixa("Certidão de nascimento - " + resto):
            assert _nomes_do_rotulo(titulo) == [], titulo


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
