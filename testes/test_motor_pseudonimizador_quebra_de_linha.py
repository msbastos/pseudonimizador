# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
r"""Pseudonimizador 0.5.34: o documento e o telefone partidos pela quebra de
linha da extracao do PDF.

Caso de producao (05/10/2026, dossie de formato 0.9.0, nivel "protegido"):
a peca trazia o CPF com a quebra de linha depois do hifen — "ddd.ddd.ddd-"
no fim da linha e os dois digitos verificadores no comeco da seguinte — e
ele ia em claro; o mesmo CPF numa linha so', na mesma peca, saia em
[[CPF_n]]. A janela de 11 digitos so' aceitava UM caractere entre dois
digitos, e "-" + quebra sao dois.

Regras que estes testes trancam:
  - o CPF e o PIS na grafia usual, com a quebra (e espacos, CR-LF) depois
    do ponto ou do hifen, viram o codigo do mesmo numero numa linha so';
  - so' na grafia de CPF ou de PIS: o numero que fecha a frase com ponto e
    o numero que abre a linha seguinte nao viram documento;
  - o CNPJ partido do mesmo jeito e' reconhecido (fica, fora do sigiloso;
    no sigiloso, vai no codigo do mesmo CNPJ numa linha so');
  - o telefone partido depois do hifen vira codigo (com o DDD entre
    parenteses, no texto comum; na conversa, tambem com CR-LF).

Numeros inventados (os de exemplo dos outros testes).

Rodar:  python -X utf8 testes/test_pseudonimizador_quebra_de_linha.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pseudonimizador.motor import nivel as nv  # noqa: E402
from pseudonimizador.motor.pseudonimizador import pseudonimizar  # noqa: E402

QUEBRAS = ("\n", "\r\n", " \n", "\n  ", " \r\n\t")


def _mapa(nivel=nv.PROTEGIDO):
    return {"schema_version": 1, "cnj": "0090001-10.2026.5.04.9999", "nivel": nivel, "tokens": {}}


def test_cpf_partido_depois_do_hifen_tem_o_codigo_do_cpf_inteiro():
    for nivel in (nv.PROTEGIDO, nv.PUBLICO, nv.SIGILOSO):
        for q in QUEBRAS:
            m = _mapa(nivel)
            t = pseudonimizar(f"inscrito no CPF 529.982.247-25, intimado (CPF nº 529.982.247-{q}25), "
                              "na pessoa do advogado", m)
            assert t == "inscrito no CPF [[CPF_1]], intimado (CPF nº [[CPF_1]]), na pessoa do advogado", (nivel, q, t)
            assert [k for k in m["tokens"] if k.startswith("[[CPF_")] == ["[[CPF_1]]"], m["tokens"]


def test_cpf_partido_sem_a_ocorrencia_inteira_ganha_codigo_novo():
    m = _mapa()
    t = pseudonimizar("(CPF nº 529.982.247-\n25), na pessoa do advogado", m)
    assert t == "(CPF nº [[CPF_1]]), na pessoa do advogado", repr(t)
    assert m["tokens"]["[[CPF_1]]"] == {"valor": "52998224725", "categoria": "cpf"}, m["tokens"]


def test_cpf_partido_depois_do_ponto():
    for q in QUEBRAS:
        for partido in (f"529.{q}982.247-25", f"529.982.{q}247-25"):
            t = pseudonimizar(f"CPF {partido} do reclamante", _mapa())
            assert t == "CPF [[CPF_1]] do reclamante", (partido, t)


def test_pis_partido_pela_quebra_de_linha():
    for q in QUEBRAS:
        for partido in (f"120.5741.316-{q}2", f"120.5741.{q}316-2", f"120.57413.16-{q}2"):
            m = _mapa()
            t = pseudonimizar(f"PIS 120.5741.316-2 e PIS {partido}, admitido", m)
            assert t == "PIS [[PIS_1]] e PIS [[PIS_1]], admitido", (partido, t)


def test_numero_que_fecha_a_frase_e_numero_da_linha_seguinte_nao_viram_documento():
    # os 11 digitos formam um CPF valido, mas nao na grafia de CPF: sao dois numeros
    for texto in ("no total de 5299.\n8224725 unidades", "itens 529-\n98224725 do lote", "soma 52998.\n224-725 fim"):
        assert pseudonimizar(texto, _mapa()) == texto, texto


def test_telefone_partido_depois_do_hifen():
    for q in QUEBRAS:
        t = pseudonimizar(f"telefone (51) 99999-{q}8888, e-mail", _mapa())
        assert t == "telefone [[TEL_1]], e-mail", (q, t)
        t = pseudonimizar(f"celular 99999-{q}8888, e-mail", _mapa())
        assert t == "celular [[TEL_1]], e-mail", (q, t)


def test_telefone_partido_na_conversa():
    for q in QUEBRAS:
        m = _mapa()
        t = pseudonimizar(f"me chama no 51 99999-1234 ou 51 99999-{q}1234 depois", m, conversa=True)
        assert t == "me chama no [[TEL_1]] ou [[TEL_1]] depois", (q, t)


def test_par_de_anos_partido_na_conversa_nao_vira_telefone():
    # revisao (05/10/2026): o separador do telefone aceitava a quebra, mas o par de anos que o exclui nao
    for texto in ("periodo 2019-\n  2020/2021 trabalhado", "periodo 2019-\r\n2020/2021 trabalhado",
                  "periodo 2019 -\n  2020/2021 trabalhado", "anos 2022-\r\n2023,2024", "ferias 2019-\n  2020, 2020-\n  2021"):
        assert pseudonimizar(texto, _mapa(), conversa=True) == texto, repr(texto)


def test_o_valor_do_cnpj_e_do_telefone_partidos_vai_ao_mapa_sem_a_quebra():
    # revisao (05/10/2026): o valor com a quebra levava a quebra a minuta na reversao
    from pseudonimizador.motor.reversor import despseudonimizar_texto
    m = _mapa(nv.SIGILOSO)
    t = pseudonimizar("CNPJ 12.345.678/0001-\n95, contesta. Adiante: CNPJ 12.345.678/0001-95.", m)
    assert t == "CNPJ [[CNPJ_1]], contesta. Adiante: CNPJ [[CNPJ_1]]."
    assert m["tokens"]["[[CNPJ_1]]"]["valor"] == "12.345.678/0001-95", m["tokens"]
    assert despseudonimizar_texto(t, m) == "CNPJ 12.345.678/0001-95, contesta. Adiante: CNPJ 12.345.678/0001-95."
    m = _mapa()
    t = pseudonimizar("telefone (51) 99999- \r\n 8888 e telefone (51) 99999-8888", m)
    assert t == "telefone [[TEL_1]] e telefone [[TEL_1]]", t
    assert m["tokens"]["[[TEL_1]]"]["valor"] == "(51) 99999-8888", m["tokens"]
    assert despseudonimizar_texto(t, m) == "telefone (51) 99999-8888 e telefone (51) 99999-8888"
    m = _mapa()
    t = pseudonimizar("me chama no 51 99999-\n1234 depois", m, conversa=True)
    assert t == "me chama no [[TEL_1]] depois" and m["tokens"]["[[TEL_1]]"]["valor"] == "51 99999-1234", m["tokens"]


def test_a_versao_da_descoberta_subiu_para_refazer_os_dossies():
    # decisao do juiz (05/10/2026): o dossie montado com o CPF partido em claro deve aparecer "a preparar de novo"
    from pseudonimizador.motor.pseudonimizador import VERSAO_DESCOBERTA_DE_NOMES
    assert VERSAO_DESCOBERTA_DE_NOMES == "3", VERSAO_DESCOBERTA_DE_NOMES


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
