# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
r"""Pseudonimizador 0.5.0, Task 2: o substituidor ignora o tóken de pessoa
juridica e a locucao de mapa antigo, e o primeiro nome isolado so' vale
para quem e' pessoa, fora de topônimo e de palavra comum.

Caso de producao (28/09/2026): num mapa com um ente publico registrado
como testemunha, "outro Estado" virou "outro [[TESTEMUNHA_11]]" (a
reversao diria "outro Estado do ..."), e a variante "Estado" passou a ser
vigiada pela guarda em todo texto; "Sao Paulo", com uma testemunha
chamada Paulo, virou "Sao [[TESTEMUNHA_1]]"; e o "MARÇO" das datas virou
o tóken do reclamante "Marco".

Nomes inventados.

Rodar:  python -X utf8 testes/test_pseudonimizador_prenome.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pseudonimizador.motor import pseudonimizador as pz  # noqa: E402
from pseudonimizador.motor.mapa import token_para  # noqa: E402


def _mapa():
    return {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}


def test_predicado_de_pessoa_juridica_so_para_tokien_de_pessoa():
    assert pz.eh_token_de_pj({"categoria": "pessoa", "valor": "Estado do Vale Azul"})
    assert pz.eh_token_de_pj({"categoria": "pessoa", "valor": "CONDOMINIO ALFA NORTE"})
    assert pz.eh_token_de_pj({"categoria": "pessoa", "valor": "Da Cooperativa Beta"})
    assert pz.eh_token_de_pj({"categoria": "pessoa", "valor": "Padaria Trigal Ltda"})
    # o "S A" com espaco no fim (a empresa da capa de mapa antigo sai da troca e da guarda, sem editar o mapa)
    assert pz.eh_token_de_pj({"categoria": "pessoa", "valor": "ALFA TELECOM S A"})
    # a denominacao so' conta quando ABRE o nome: a pessoa continua pessoa
    assert not pz.eh_token_de_pj({"categoria": "pessoa",
                                  "valor": "Fulana Beltrana do Sindicato dos Comerciarios"})
    assert not pz.eh_token_de_pj({"categoria": "pessoa", "valor": "Joana Kretzer Lopes"})
    # endereco, e-mail etc. nunca sao "pessoa juridica" para a guarda
    assert not pz.eh_token_de_pj({"categoria": "endereco", "valor": "Rua do Comércio, 10"})
    assert not pz.eh_token_de_pj({"categoria": "email", "valor": "contato@hospitalalfa.exemplo.com.br"})


def test_tokien_de_pessoa_juridica_de_mapa_antigo_nao_troca_nem_vira_prenome():
    m = _mapa()
    token_para(m, "TESTEMUNHA", "pessoa", "Estado do Vale Azul", papel="testemunha")
    token_para(m, "TESTEMUNHA", "pessoa", "CONDOMINIO ALFA NORTE", papel="testemunha")
    token_para(m, "TESTEMUNHA", "pessoa", "Hospital Santa Vida", papel="testemunha")
    token_para(m, "TESTEMUNHA", "pessoa", "Sindicato Unido Norte", papel="testemunha")
    token_para(m, "RECLAMANTE", "pessoa", "Joana Kretzer Lopes", papel="Reclamante")
    texto = ("A testemunha mora em outro Estado; o Estado do Vale Azul e o Condomínio Alfa Norte "
             "respondem. O Hospital Santa Vida, o Hospital Central e o Sindicato pagaram. Joana confirmou.")
    t = pz.pseudonimizar(texto, m)
    assert t == texto.replace("Joana confirmou", "[[RECLAMANTE_1]] confirmou"), t
    assert all(m["tokens"][t]["variantes_vistas"] == [] for t in
               ("[[TESTEMUNHA_1]]", "[[TESTEMUNHA_2]]", "[[TESTEMUNHA_3]]", "[[TESTEMUNHA_4]]"))


def test_locucao_de_mapa_antigo_nao_troca_palavra_comum():
    m = _mapa()
    token_para(m, "PERITO", "pessoa", "Equipamentos de Proteção Individual", papel="perito")
    token_para(m, "TESTEMUNHA", "pessoa", "Assinatura Digital", papel="testemunha")
    texto = "Os Equipamentos de Proteção Individual e a Assinatura do contrato."
    assert pz.pseudonimizar(texto, m) == texto


def test_nome_real_com_cauda_contaminada_volta_a_ser_trocado():
    # mapa anterior a 0.4.4: o perito entrou com a profissao colada
    m = _mapa()
    token_para(m, "PERITO", "pessoa", "CARLOS DE ALMEIDA WERLE ENGENHEIRO DE SEGURANÇA", papel="perito")
    t = pz.pseudonimizar("Laudo assinado por CARLOS DE ALMEIDA WERLE em 2024.", m)
    assert t == "Laudo assinado por [[PERITO_1]] em 2024.", t


def test_toponimo_nao_e_o_prenome():
    m = _mapa()
    token_para(m, "TESTEMUNHA", "pessoa", "Paulo Henrique Souza", papel="testemunha")
    token_para(m, "TESTEMUNHA", "pessoa", "Ana Beatriz Lima", papel="testemunha")
    texto = ("Trabalhou em São Paulo, em Santa Ana, na Vila Paulo e em Sant'Ana da Serra Azul. "
             "Paulo disse que sim. Ana confirmou.")
    t = pz.pseudonimizar(texto, m)
    assert t == ("Trabalhou em São Paulo, em Santa Ana, na Vila Paulo e em Sant'Ana da Serra Azul. "
                 "[[TESTEMUNHA_1]] disse que sim. [[TESTEMUNHA_2]] confirmou."), t
    assert [v for v in m["tokens"]["[[TESTEMUNHA_1]]"]["variantes_vistas"]] == ["Paulo"]


def test_mes_com_cedilha_nao_e_o_prenome_sem_cedilha():
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "Marco Beltrano Sicrano", papel="Reclamante")
    t = pz.pseudonimizar("Em 10 de MARÇO de 2024 e em Março de 2025, MARCO e Marco assinaram.", m)
    assert t == "Em 10 de MARÇO de 2024 e em Março de 2025, [[RECLAMANTE_1]] e [[RECLAMANTE_1]] assinaram.", t
    assert "MARÇO" not in m["tokens"]["[[RECLAMANTE_1]]"]["variantes_vistas"]


def test_cedilha_do_texto_que_a_capa_nao_tem_continua_valendo():
    # a excecao da cedilha e' so' para "MARÇO": o prenome "CONCEICAO" da capa
    # (sem acento) continua trocando "Conceição" isolado
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "CONCEICAO BELTRANA SICRANA", papel="Reclamante")
    t = pz.pseudonimizar("Disse que Conceição chegava cedo e que CONCEICAO saía tarde.", m)
    assert t == "Disse que [[RECLAMANTE_1]] chegava cedo e que [[RECLAMANTE_1]] saía tarde.", t


def test_quebra_de_linha_so_depois_de_sao_santo_santa():
    # "Santana" e "Vila" tambem sao sobrenomes: atraves da linha, o prenome e' a pessoa
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "FULANA BELTRANA SICRANA", papel="Reclamante")
    token_para(m, "TESTEMUNHA", "pessoa", "Paulo Terciano Souza", papel="testemunha")
    t = pz.pseudonimizar("Presentes o preposto Ciclano Santana\nFulana, a reclamante; Beltrano Vila\nFulana "
                         "assinou. Mora em São\nPaulo e em Santana Paulo.", m)
    assert t == ("Presentes o preposto Ciclano Santana\n[[RECLAMANTE_1]], a reclamante; Beltrano Vila\n"
                 "[[RECLAMANTE_1]] assinou. Mora em São\nPaulo e em Santana Paulo."), t


def test_acento_no_texto_que_a_capa_nao_tem_continua_valendo():
    # a capa do PJe vem em maiusculas sem acento; o texto traz o acento
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "JOSE CARLOS SOUZA", papel="Reclamante")
    assert pz.pseudonimizar("José confirmou; Jose também.", m) == \
        "[[RECLAMANTE_1]] confirmou; [[RECLAMANTE_1]] também."


def test_prenome_que_e_palavra_institucional_nao_e_trocado_sozinho():
    m = _mapa()
    token_para(m, "TERCEIRO", "pessoa", "Fazenda Boa Vista", papel="Terceiro Interessado")
    token_para(m, "TERCEIRO", "pessoa", "Distrito Novo Horizonte", papel="Terceiro Interessado")
    texto = "A Fazenda Pública e o Distrito arrecadam; a Fazenda Boa Vista vendeu."
    t = pz.pseudonimizar(texto, m)
    assert t == "A Fazenda Pública e o Distrito arrecadam; a [[TERCEIRO_1]] vendeu.", t


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
