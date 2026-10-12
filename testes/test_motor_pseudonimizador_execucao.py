# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
r"""As ancoras da execucao no pseudonimizador (0.5.35, Parte B; Diferido 3 da Parte A).

O DEFEITO: o dossie da execucao leva autos de arrematacao, cartas de
adjudicacao, AR e atos constitutivos; arrematante, adquirente, recebedor do
AR e socio nao sao parte da capa nem testemunha — ficavam em claro.

Regras que estes testes trancam:
  - "arrematante", "adquirente", "sócio/sócia(-administrador)" e "recebido
    por"/"recebedor" ancoram o nome que vem depois, lido sem a caixa e com
    a prova pelo lexico (como testemunha e perito);
  - prefixos ARREMATANTE, ADQUIRENTE, SOCIO, RECEBEDOR;
  - sem nome provado depois da ancora ("o sócio da empresa requereu", "sócia
    majoritária", "recebido por: [carimbo] CPF") nada entra no mapa;
  - o candidato em minusculas so' entra com a primeira palavra prenome do
    ranking (1.000+) e nenhuma palavra comum dos autos; senao e' pulado, sem
    ir a incertos (validacao no acervo: "socio" + texto corrido);
  - " - ", " – " e ":" entre a ancora e o nome;
  - leiloeiro NAO ganha ancora (agente publico, como o oficial de justica);
  - no nivel publico, nada entra (descobrir_pessoas sai antes).

Nomes inventados.
Rodar:  python -X utf8 testes/test_pseudonimizador_execucao.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pseudonimizador.motor import pseudonimizador as ps  # noqa: E402
from pseudonimizador.motor.pseudonimizador import descobrir_pessoas, pseudonimizar  # noqa: E402
from test_motor_pseudonimizador import _mapa  # noqa: E402


def _tokens(m, prefixo):
    return [t for t in m["tokens"] if t.startswith(f"[[{prefixo}_")]


def test_arrematante_e_adquirente():
    m = _mapa()
    texto = ("AUTO DE ARREMATAÇÃO. Arrematante: Joaquim Valadares Pinho, CPF em código. "
             "Carta de adjudicação expedida em favor do adquirente Teodoro Lins Quaresma.")
    descobrir_pessoas(texto, m)
    assert _tokens(m, "ARREMATANTE") and _tokens(m, "ADQUIRENTE"), m["tokens"].keys()
    t = pseudonimizar(texto, m)
    assert "Valadares" not in t and "Quaresma" not in t, t


def test_socio_com_e_sem_hifen_e_em_minusculas():
    m = _mapa()
    texto = ("Atos constitutivos: sócio-administrador CLÓVIS ABRANTES MOURÃO; sócia Dalva Quitéria Nunes; "
             "o sócio osmar peregrino lage retirou-se da sociedade.")
    descobrir_pessoas(texto, m)
    assert len(_tokens(m, "SOCIO")) == 3, m["tokens"].keys()
    t = pseudonimizar(texto, m)
    for sobrenome in ("ABRANTES", "Quitéria", "peregrino"):
        assert sobrenome not in t, t


def test_recebedor_do_ar():
    m = _mapa()
    texto = "AR — Aviso de Recebimento. Recebido por: Ivone Castilho Prates. Assinatura do recebedor: Ivone C. Prates."
    descobrir_pessoas(texto, m)
    assert _tokens(m, "RECEBEDOR"), m["tokens"].keys()
    assert "Castilho" not in pseudonimizar(texto, m)


def test_ancora_sem_nome_nao_cria_token():
    m = _mapa()
    texto = ("O sócio da empresa requereu a liberação. A sócia majoritária não foi citada. "
             "Recebido por: CPF 000.000.000-00 (carimbo). O arrematante deverá depositar o preço.")
    descobrir_pessoas(texto, m)
    for prefixo in ("SOCIO", "RECEBEDOR", "ARREMATANTE"):
        assert not _tokens(m, prefixo), (prefixo, m["tokens"].keys())


def test_qualidade_do_socio_fica_fora_do_nome():
    # "majoritária", "administrador", "retirante": pulados antes do nome, nunca parte dele
    m = _mapa()
    texto = ("A sócia majoritária Dalva Quitéria Nunes e o sócio administrador Clóvis Abrantes Mourão; "
             "o sócio retirante Osmar Peregrino Lage.")
    descobrir_pessoas(texto, m)
    valores = sorted(i["valor"] for t, i in m["tokens"].items() if t.startswith("[[SOCIO_"))
    assert valores == ["Clóvis Abrantes Mourão", "Dalva Quitéria Nunes", "Osmar Peregrino Lage"], valores


def test_ancora_dentro_de_outra_palavra_nao_conta():
    # "associado", "sociedade", "recebedoria": a ancora so' vale como palavra inteira
    m = _mapa()
    texto = ("O associado Joaquim Valadares Pinho compareceu. A sociedade Teodoro Lins Quaresma "
             "foi citada.")
    descobrir_pessoas(texto, m)
    for prefixo in ("SOCIO", "ARREMATANTE", "ADQUIRENTE", "RECEBEDOR"):
        assert not _tokens(m, prefixo), (prefixo, m["tokens"].keys())


def test_plural_e_lista():
    m = _mapa()
    texto = "Os arrematantes Joaquim Valadares Pinho e Teodoro Lins Quaresma depositaram o preço."
    descobrir_pessoas(texto, m)
    assert len(_tokens(m, "ARREMATANTE")) == 2, m["tokens"].keys()


def test_minusculas_so_com_prenome_do_ranking():
    # validacao no acervo (V2): o texto corrido em minusculas depois de "socio" (sobrenome do ranking + palavras
    # comuns) virava codigo, e a variante de uma palavra ficava em claro — a guarda nomes_em_claro barrava o dossie
    m = _mapa()
    descobrir_pessoas("O sócio nunes investidor responde pelas dívidas; o adquirente costa remanescente pagou.", m)
    for prefixo in ("SOCIO", "ADQUIRENTE"):
        assert not _tokens(m, prefixo), (prefixo, m["tokens"].keys())
    assert not [t for t in m["tokens"] if t.startswith("[[PESSOA_")], m["tokens"].keys()
    assert not m.get("nomes_incertos"), m.get("nomes_incertos")   # nunca vai a incertos por estas ancoras
    # o prenome do ranking abre o nome em minusculas: codigo
    m = _mapa()
    descobrir_pessoas("o sócio osmar peregrino lage retirou-se; recebido por ivone castilho prates.", m)
    assert _tokens(m, "SOCIO") and _tokens(m, "RECEBEDOR"), m["tokens"].keys()
    # ... salvo com palavra comum dos autos no candidato
    m = _mapa()
    descobrir_pessoas("o sócio osmar peregrino lage retirou-se", m, comuns=frozenset({"peregrino"}))
    assert not any(i["valor"].lower().startswith("osmar peregrino") for t, i in m["tokens"].items()
                   if t.startswith("[[SOCIO_")), m["tokens"]
    assert ps._minusculo_da_execucao_aceito("osmar peregrino lage")
    assert not ps._minusculo_da_execucao_aceito("nunes investidor responde")


def test_separador_antes_do_nome():
    # V3: "Adquirente - NOME" (espaco-hifen-espaco), o travessao e os dois-pontos
    for texto in ("Adquirente - Teodoro Lins Quaresma", "Adquirente - TEODORO LINS QUARESMA",
                  "Adquirente – Teodoro Lins Quaresma", "Adquirente: TEODORO LINS QUARESMA",
                  "CARTA DE ARREMATAÇÃO\nAdquirente - TEODORO LINS QUARESMA\nCPF: em código"):
        m = _mapa()
        descobrir_pessoas(texto, m)
        assert _tokens(m, "ADQUIRENTE"), (texto, m["tokens"].keys())
        assert "QUARESMA" not in pseudonimizar(texto, m).upper(), texto


def test_versao():
    assert ps.VERSAO == "0.5.35"


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
