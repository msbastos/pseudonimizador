# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
r"""Pseudonimizador 0.5.0, Task 7: o texto com acento decomposto (NFD) e o
endereco quebrado entre linhas.

Achados da varredura do acervo (28/09/2026):
  - 11 de 85 dossies tinham texto em NFD (a letra e o acento como dois
    caracteres): RE_PALAVRA parte a palavra na marca combinante, e o nome
    acentuado nao casava — mas a guarda (mapa.normalizar tira as marcas)
    o via; a descoberta, na mesma situacao, registrava pedacos do nome;
  - "Rua do" no fim da linha e o logradouro na linha seguinte: RE_ENDERECO
    le' linha a linha e so' "Rua do" virava tóken;
  - (validacao do plano) 10 de 85 dossies com U+200B em volta do espaco
    entre as palavras: a janela do nome nao casava, e os sobrenomes de um
    perito ficaram em claro sem a guarda ver.
O texto que vai ao dossie passa a NFC e sem caracteres de largura zero (no
montador, na entrada do pseudonimizador e na leitura da guarda);
RE_ENDERECO aceita "da/de/do/das/dos" no fim da linha.
Residual: o numero do imovel sozinho numa terceira linha.

Revisao final do ramo (29/09/2026): tirar o U+200B colava as palavras quando
ele era o unico separador ("Fulana<U+200B><U+200B>disse" -> "Fulanadisse";
987 sequencias assim entre letras em 3 processos do acervo), e nem a troca
nem a guarda viam o nome; e a lista era estreita — os controles de direcao
(U+202C U+202D em volta de cada palavra, 3 processos, 17.588 ocorrencias) e o
hifen condicional (U+00AD, 14 processos) ficavam, a janela do nome nao
casava e so' o prenome era trocado. Agora uma funcao so'
(pseudonimizador.limpar_invisiveis, no montador, na troca e na guarda): a
sequencia de invisiveis entre duas letras com U+200B ou controle de direcao
vira UM espaco (no acervo eles separam palavras: 1825 casos contra nenhum
dentro de palavra); o resto sai. A guarda procura tambem numa copia em que
toda sequencia de invisiveis entre letras vira espaco (so' fortalece).

Nomes inventados.

Rodar:  python -X utf8 testes/test_pseudonimizador_nfc_endereco.py
"""
import sys
import tempfile
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pseudonimizador.motor.mapa import token_para  # noqa: E402
from pseudonimizador.motor.pseudonimizador import (  # noqa: E402
    construir_mapa, descobrir_pessoas, pseudonimizar, pseudonimizar_rotulo)


def _nfd(s: str) -> str:
    return unicodedata.normalize("NFD", s)


def _mapa():
    m = {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}
    token_para(m, "RECLAMANTE", "pessoa", "Maria da Conceição Araújo", papel="Reclamante")
    return m


def test_texto_em_nfd_e_trocado_e_sai_em_nfc():
    m = _mapa()
    t = pseudonimizar(_nfd("A reclamante MARIA DA CONCEIÇÃO ARAÚJO disse; Conceição e Araújo"), m)
    assert t == "A reclamante [[RECLAMANTE_1]] disse; Conceição e Araújo", ascii(t)
    assert unicodedata.is_normalized("NFC", t)
    assert pseudonimizar_rotulo(_nfd("procuração maria da conceição araújo"), m) == "procuração [[RECLAMANTE_1]]"


def test_descoberta_em_nfd_registra_o_nome_inteiro():
    m = {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}
    descobrir_pessoas(_nfd("Testemunha do reclamante: Beatriz Conceição Araújo, compromissada."), m)
    valores = [i["valor"] for i in m["tokens"].values()]
    assert valores == ["Beatriz Conceição Araújo"], [ascii(v) for v in valores]


def test_capa_em_nfd_entra_no_mapa_em_nfc():
    m = {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}
    construir_mapa({"processo": {"partes": [{"papel": "Reclamante", "nome": _nfd("MARIA DA CONCEIÇÃO ARAÚJO")}]}}, m)
    valor = m["tokens"]["[[RECLAMANTE_1]]"]["valor"]
    assert valor == "MARIA DA CONCEIÇÃO ARAÚJO" and unicodedata.is_normalized("NFC", valor), ascii(valor)


def test_endereco_com_logradouro_na_linha_seguinte():
    m = _mapa()
    t = pseudonimizar("residente na Rua do\nPinheiral, nº 45, bairro Centro", m)
    assert t == "residente na [[ENDERECO_1]], bairro Centro", repr(t)
    t = pseudonimizar("com sede na rua dos\nJacarandás, 1000", m)
    assert t == "com sede na [[ENDERECO_2]]", repr(t)
    # o que ja' funcionava continua igual
    assert pseudonimizar("na Avenida\nBrasil, 100", m) == "na [[ENDERECO_3]]"
    assert pseudonimizar("Rua do Comércio, 10", m) == "[[ENDERECO_4]]"


ZWSP, PDF, LRO, LRM, SHY = "\u200b", "\u202c", "\u202d", "\u200e", "\u00ad"


def _mapa_fulana(variante: bool = False):
    m = {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}
    tok = token_para(m, "RECLAMANTE", "pessoa", "FULANA BELTRANA SICRANA", papel="Reclamante")
    if variante:
        m["tokens"][tok]["variantes_vistas"].append("Fulana")
    return m


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
