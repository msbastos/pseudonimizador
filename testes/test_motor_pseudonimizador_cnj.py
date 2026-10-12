# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
r"""Pseudonimizador 0.5.36: o numero de processo (CNJ) nunca vira codigo.

Sonda de 07/10/2026: o dossie que cita outro processo ("conexo com o
0090006-85.2025.5.04.9999") saia com o numero partido —
"0090006-85.[[PIS_1]]". A cauda "AAAA.J.TR.OOOO" tem exatamente 11 digitos
com um separador entre os grupos, e' uma janela de RE_11DIGITOS que comeca e
termina em limite de palavra, e por acaso passa no digito verificador do
PIS (ou do CPF, conforme o ano, o tribunal e a vara). Processo judicial e'
publico: o numero inteiro fica em claro, e nenhum identificador (CPF, PIS,
telefone, conta...) pode nascer dentro dele.

Regras que estes testes trancam:
  - a cauda do CNJ completo nao vira [[PIS_n]] nem [[CPF_n]], e nada do
    numero entra no mapa;
  - o CPF de verdade na mesma frase continua em codigo (a exclusao e' so'
    do que sobrepoe o CNJ);
  - o varredor dos Entendimentos nao aponta CPF/PIS dentro do CNJ (ele
    reusa _cpf_pis_spans; o CNJ em si continua apontado como "cnj").

Numeros de processo SINTETICOS (testes/cnj_sinteticos.txt); nomes inventados.

Rodar:  python -X utf8 testes/test_pseudonimizador_cnj.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pseudonimizador.motor.pseudonimizador import (  # noqa: E402
    _cpf_pis_spans, _cpf_valido, _pis_valido, pseudonimizar)

# a cauda "2025.5.04.9999" passa no DV do PIS; a "2018.5.04.0101", no do CPF
CNJ_CAUDA_PIS = "0090006-85.2025.5.04.9999"
CNJ_CAUDA_CPF = "0090006-85.2018.5.04.0101"
CPF_SINTETICO = "529.982.247-25"   # DV valido (exemplo classico)


def _mapa():
    return {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}


def test_as_caudas_escolhidas_passam_no_dv():
    # o teste so' vale se as caudas de fato enganam o DV (senao nada e' trancado)
    assert _pis_valido("20255049999"), "a cauda do CNJ_CAUDA_PIS deveria passar no DV do PIS"
    assert _cpf_valido("20185040101"), "a cauda do CNJ_CAUDA_CPF deveria passar no DV do CPF"


def test_cnj_com_cauda_de_pis_fica_inteiro():
    texto = f"Conexo com o processo {CNJ_CAUDA_PIS}, em que a mesma testemunha depos."
    mapa = _mapa()
    saida = pseudonimizar(texto, mapa)
    assert saida == texto, saida
    assert not mapa["tokens"], mapa["tokens"]


def test_cnj_com_cauda_de_cpf_fica_inteiro():
    texto = f"Ver a sentenca dos autos {CNJ_CAUDA_CPF} (mesmo grupo economico)."
    mapa = _mapa()
    saida = pseudonimizar(texto, mapa)
    assert saida == texto, saida
    assert not mapa["tokens"], mapa["tokens"]


def test_cpf_de_verdade_na_mesma_frase_continua_em_codigo():
    texto = f"Reclamante CPF {CPF_SINTETICO}, autor tambem do {CNJ_CAUDA_PIS}."
    mapa = _mapa()
    saida = pseudonimizar(texto, mapa)
    assert "[[CPF_1]]" in saida and CNJ_CAUDA_PIS in saida, saida
    assert "PIS" not in saida, saida


def test_cpf_pis_spans_nao_entra_no_cnj():
    texto = f"{CNJ_CAUDA_PIS} e {CNJ_CAUDA_CPF}; CPF {CPF_SINTETICO}"
    achados = [(p, d) for _i, _f, p, _c, d in _cpf_pis_spans(texto)]
    assert achados == [("CPF", "52998224725")], achados


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
