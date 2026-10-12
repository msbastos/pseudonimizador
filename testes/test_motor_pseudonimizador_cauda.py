# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
r"""Pseudonimizador 0.5.0, Task 4: os pontos cegos da guarda — o nome real
que passa sem ela ver.

Casos de producao (28/09/2026):
  - a cauda: as peticoes grafavam a reclamante "PRENOME SOBRENOME3
    SOBRENOME1", diferente da capa ("PRENOME SOBRENOME1 SOBRENOME2"); so' o
    prenome virava tóken e os dois sobrenomes ficavam em claro, invisiveis
    a' guarda (nenhum valor do mapa os tinha);
  - o prenome ambiguo: a mesma testemunha registrada duas vezes (uma com
    uma palavra a mais, ou com o sobrenome a uma letra) deixava o prenome
    "de duas pessoas" — nunca trocado e nunca vigiado; remontado, o
    processo passava pela guarda com o prenome em claro.

Regras que estes testes trancam:
  - depois da troca do nome incompleto (prenome, prefixo), 1 a 3 palavras
    com maiuscula cuja ultima e' palavra do nome do mesmo tóken entram no
    tóken (para em minuscula, em "e", "contra" e palavra que nunca e'
    nome); depois do nome inteiro, nunca (vem outra pessoa) — e a pessoa da
    linha de baixo que repete o sobrenome da parte vira [[PESSOA_n]] na
    descoberta;
  - a ancora de qualificacao: prenome de PARTE da capa + 1 a 3 palavras com
    maiuscula, uma delas sobrenome da parte, + ", brasileira|qualificada|
    portador..." vira outro nome da mesma parte (alias: alvo da troca e
    vigiado pela guarda);
  - a inicial do prenome com o resto do nome e o nome sem o 1o prenome sao
    da pessoa, so' quando de uma so' (e este, nunca logo depois de outro
    nome);
  - a mesma pessoa descoberta de novo (a forma curta com 3+ palavras e'
    comeco da longa, palavra a palavra, com ate' 1 letra de diferenca) vira
    alias do tóken que ja' existe — nunca parte da capa, nunca "Ana Paula
    Souza" com "Ana Paula Lima";
  - o prenome que continua ambiguo vira [[PRENOME_n]] (reversivel, sem dizer
    de quem e'), nunca palavra comum; o filtro de saida nao o vigia.

Revisao final do ramo (29/09/2026): a ancora e a cauda juntavam na parte
quem so' dividia com ela um sobrenome muito comum ("representada por sua
socia FULANA JOSE DA SILVA", com a reclamante "FULANA TERCIANA DA SILVA") ou
um sobrenome de 4 letras a 1 letra ("LIMA" x "LIMO"), e o advogado "inscrito
na OAB" — o Claude lia a socia como a reclamante, e a reversao escrevia o
nome da reclamante no lugar dela. A palavra fora do nome da parte que e'
prenome do lexico (outra pessoa, de prenome composto) recusa a ancora e
para a cauda; a 1 letra, so' com 5+ letras; "inscrito na OAB" recusa. E a
testemunha (ou paradigma) cujo nome era o comeco do nome da parte da capa
(a mae com o nome da filha menos o ultimo sobrenome; o pai e o filho sem
sufixo; "Costa" x "Costalonga") virava a parte: com a parte, so' a forma
igual; a forma nao identica, so' para o perito com o mesmo numero de
palavras (o caso medido: a parte capturada como perito, truncada). E o
"E" maiusculo da conjuncao, em texto todo em caixa alta, era tomado por
inicial: "FULANA E CICLANA SICRANA" virava um tóken so' e a reversao apagava
a segunda pessoa — "A"/"O"/"E" so' sao inicial com ponto ou quebra de linha,
ou, com espaco, quando sao a inicial de uma palavra do nome e a seguinte e'
outra inicial ou palavra do nome (a revalidacao achou, num titulo do PJe, as
iniciais sem ponto do nome da reclamante: "FULANA O M SICRANA").

Nomes inventados.

Rodar:  python -X utf8 testes/test_pseudonimizador_cauda.py
"""
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pseudonimizador.motor.mapa import token_para  # noqa: E402
from pseudonimizador.motor.pseudonimizador import (  # noqa: E402
    construir_mapa, descobrir_pessoas, pseudonimizar)
from pseudonimizador.motor.reversor import despseudonimizar_texto  # noqa: E402


def _mapa():
    return {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}


def _capa(*partes):
    m = _mapa()
    construir_mapa({"processo": {"partes": [{"papel": p, "nome": n} for p, n in partes]}}, m)
    return m


def test_inicial_no_meio_da_cauda_nao_para_a_cauda():
    m = _capa(("Reclamante", "FULANA DOS SANTOS BELTRANA"))
    for texto in ("FULANA D\nSANTOS BELTRANA, vem", "Fulana D. S. Beltrana, vem"):
        t = pseudonimizar(texto, m)
        assert t == "[[RECLAMANTE_1]], vem", repr(t)
    assert pseudonimizar("FULANA M. disse", m) == "[[RECLAMANTE_1]] M. disse"


def test_cauda_para_em_minuscula_e_em_e_e_em_contra():
    m = _capa(("Reclamante", "FULANA BELTRANA SICRANA"), ("Reclamado", "Pedro Tercio Beltrana"))
    t = pseudonimizar("FULANA disse que BELTRANA faltou; FULANA CONTRA BELTRANA LTDA; "
                      "Fulana e Pedro Beltrana assinaram.", m)
    assert t == ("[[RECLAMANTE_1]] disse que BELTRANA faltou; [[RECLAMANTE_1]] CONTRA BELTRANA LTDA; "
                 "[[RECLAMANTE_1]] e [[RECLAMADO_1]] assinaram."), t


def test_cauda_nao_estende_a_troca_do_nome_inteiro():
    # depois do nome inteiro vem outra pessoa: na lista de herdeiros, a 2a nao some no tóken da 1a
    m = _capa(("Reclamante", "FULANA BELTRANA DOS SICRANOS"))
    texto = "Herdeiros:\nFULANA BELTRANA DOS SICRANOS\nCICLANA TERCIANA DOS SICRANOS\nCPF 000"
    t = pseudonimizar(texto, m)
    assert t == "Herdeiros:\n[[RECLAMANTE_1]]\nCICLANA TERCIANA DOS SICRANOS\nCPF 000", repr(t)
    assert despseudonimizar_texto(t, m) == texto
    assert not m["tokens"]["[[RECLAMANTE_1]]"].get("casamentos_cauda"), m["tokens"]["[[RECLAMANTE_1]]"]


def test_cauda_depois_do_prenome_ambiguo_para_em_palavra_de_outra_pessoa():
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "Fulano Terciano Sicrano", papel="Reclamante")
    token_para(m, "RECLAMADO", "pessoa", "Fulano Ciclano Beltrano", papel="Reclamado")
    t = pseudonimizar("Advogado: Fulano Augusto Sicrano, OAB/RS 1.", m)
    assert t == "Advogado: [[PRENOME_1]] Augusto Sicrano, OAB/RS 1.", t


def test_inicial_do_prenome_com_o_resto_do_nome():
    m = _mapa()
    texto = ("Testemunha: FULANA TERCIANA SICRANA, advertida.\nSegunda testemunha da primeira e segunda "
             "reclamadas: F\nTerciana Sicrana, CPF 000. Assinou F. Terciana Sicrana.")
    descobrir_pessoas(texto, m)
    t = pseudonimizar(texto, m)
    assert t == ("Testemunha: [[TESTEMUNHA_1]], advertida.\nSegunda testemunha da primeira e segunda reclamadas: "
                 "[[TESTEMUNHA_1]], CPF 000. Assinou [[TESTEMUNHA_1]]."), repr(t)
    # com espaco, "A"/"O"/"E" sao artigo ou conjuncao: fica
    m = _capa(("Reclamante", "ANA TERCIANA SICRANA"))
    assert pseudonimizar("Disse que A Terciana Sicrana saiu.", m) == "Disse que A Terciana Sicrana saiu."
    assert pseudonimizar("Assinou A. Terciana Sicrana.", m) == "Assinou [[RECLAMANTE_1]]."


def test_ancora_exige_sobrenome_em_comum_com_a_parte():
    # o socio e o advogado com o prenome do reclamante nao viram o reclamante
    m = _capa(("Reclamante", "Fulano Beltrano Sicrano"))
    descobrir_pessoas("ALFA LTDA, representada por seu sócio FULANO TERCIANO CICLANO, brasileiro, casado.", m)
    descobrir_pessoas("substabeleço ao Dr. FULANO TERCIANO CICLANO, brasileiro, advogado, inscrito na OAB/RS 1", m)
    assert not m["tokens"]["[[RECLAMANTE_1]]"].get("aliases"), m["tokens"]["[[RECLAMANTE_1]]"]
    # 0.5.35: o socio ganhou ancora propria — o nome inteiro vai em codigo como [[SOCIO_n]], nunca como o reclamante
    t = pseudonimizar("Assinado eletronicamente por: FULANO TERCIANO CICLANO", m)
    assert t == "Assinado eletronicamente por: [[SOCIO_1]]", t


def test_alias_e_alvo_por_si():
    # o nome das peticoes, todo em minusculas (o prenome isolado exige maiuscula), so' casa como alvo
    m = _capa(("Reclamante", "FULANA BELTRANA SICRANA"))
    descobrir_pessoas("FULANA TERCIANA SICRANA, brasileira, solteira, vem propor", m)
    assert m["tokens"]["[[RECLAMANTE_1]]"].get("aliases") == ["FULANA TERCIANA SICRANA"], m["tokens"]
    t = pseudonimizar("pix para fulana terciana sicrana", m)
    assert t == "pix para [[RECLAMANTE_1]]", t


def test_ancora_nao_funde_pessoas_quando_o_prenome_e_de_mais_de_uma():
    m = _capa(("Reclamante", "JOANA KRETZER LOPES"), ("Reclamado", "JOANA PAES LIMA"))
    descobrir_pessoas("JOANA VITORINO KRETZ, brasileira, solteira", m)
    assert all(not i.get("aliases") for i in m["tokens"].values()), m["tokens"]
    m = _capa(("Reclamante", "JOANA KRETZER LOPES"))
    descobrir_pessoas("Rol de testemunhas: JOANA SILVA SOUZA, brasileira, casada.", m)
    assert not m["tokens"]["[[RECLAMANTE_1]]"].get("aliases"), m["tokens"]


def test_mesma_testemunha_descoberta_de_novo_vira_alias():
    m = _mapa()
    descobrir_pessoas("Testemunha: Anísia Mirtes Bastiani, compromissada.", m)
    descobrir_pessoas("TESTEMUNHA ANISIA MIRTES BASTIANI DA SILVA, advertida.", m)
    descobrir_pessoas("Testemunha: Deolinda Farias Castanheira.", m)
    descobrir_pessoas("Testemunha: DEOLINDA FARIAS CASTANHEIRAS, compromissada.", m)
    descobrir_pessoas("Testemunha: Evandro da Mata Lauxen.", m)
    descobrir_pessoas("Testemunha: EVANDRO MATA LAUXEN.", m)
    # a coluna da ata truncou o nome (e o "CPF" da coluna seguinte colou nele)
    descobrir_pessoas("Testemunha da reclamada: Josefina Arruda Mont CPF 000.000.000-00", m)
    descobrir_pessoas("TESTEMUNHA DA RECLAMADA JOSEFINA ARRUDA MONTENEGRO, compromissada.", m)
    assert sorted(i["valor"] for i in m["tokens"].values()) == [
        "Anísia Mirtes Bastiani", "Deolinda Farias Castanheira", "Evandro da Mata Lauxen",
        "Josefina Arruda Mont"], m["tokens"]
    t = pseudonimizar("ANISIA MIRTES BASTIANI DA SILVA disse; Anísia confirmou; DEOLINDA FARIAS CASTANHEIRAS "
                      "e Deolinda; EVANDRO MATA LAUXEN; JOSEFINA ARRUDA MONTENEGRO.", m)
    assert t == ("[[TESTEMUNHA_1]] disse; [[TESTEMUNHA_1]] confirmou; [[TESTEMUNHA_2]] "
                 "e [[TESTEMUNHA_2]]; [[TESTEMUNHA_3]]; [[TESTEMUNHA_RDA_1]]."), t


def test_pessoas_diferentes_com_o_mesmo_comeco_nao_se_fundem():
    m = _mapa()
    descobrir_pessoas("Testemunhas: Ana Paula Souza e Ana Paula Lima; testemunha Maria da Silva; "
                      "testemunha Maria da Costa; testemunha Mário Lopes Duarte; testemunha Maria Lopes Duarte.", m)
    assert sorted(i["valor"] for i in m["tokens"].values()) == [
        "Ana Paula Lima", "Ana Paula Souza", "Maria Lopes Duarte", "Maria da Costa", "Maria da Silva",
        "Mário Lopes Duarte"], m["tokens"]
    m = _capa(("Reclamante", "Maria Pereira Souza"))
    descobrir_pessoas("Testemunha do reclamante: Maria Pereira Souza Lima, filha.", m)
    assert sorted(m["tokens"]) == ["[[RECLAMANTE_1]]", "[[TESTEMUNHA_RTE_1]]"], m["tokens"]
    assert not m["tokens"]["[[RECLAMANTE_1]]"].get("aliases")


def test_parte_da_capa_descoberta_de_novo_truncada_vira_alias_da_parte():
    # o laudo trouxe o nome da reclamante truncado pela coluna, como se fosse o perito
    m = _capa(("Reclamante", "JOSEFA LINDALVA TERCIANA SICRANA"))
    descobrir_pessoas("Perito: JOSEFA LINDALVA TERCIANA SICRAN", m)
    assert list(m["tokens"]) == ["[[RECLAMANTE_1]]"], m["tokens"]
    t = pseudonimizar("Impugnação ao laudo (JOSEFA LINDALVA) e JOSEFA LINDALVA TERCIANA SICRAN", m)
    assert t == "Impugnação ao laudo ([[RECLAMANTE_1]]) e [[RECLAMANTE_1]]", t


def test_sufixo_de_geracao_separa_as_pessoas():
    m = _mapa()
    descobrir_pessoas("Testemunha: Antero Brusque Lemos. Testemunha: ANTERO BRUSQUE LEMOS FILHO.", m)
    assert sorted(i["valor"] for i in m["tokens"].values()) == ["ANTERO BRUSQUE LEMOS FILHO",
                                                               "Antero Brusque Lemos"], m["tokens"]


def test_sobrenome_depois_do_prenome_ambiguo_diz_de_quem_e():
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "Ivo Jose Bertolini", papel="Reclamante")
    token_para(m, "TESTEMUNHA", "pessoa", "Ivo Carlos Matte", papel="testemunha")
    t = pseudonimizar("assinou Ivo Bertolini; depois, Ivo Matte; e Ivo Ramos", m)
    assert t == "assinou [[RECLAMANTE_1]]; depois, [[TESTEMUNHA_1]]; e [[PRENOME_1]] Ramos", t


def test_prenome_ambiguo_que_e_palavra_comum_nunca_vira_tokien():
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "Rosa Maria Flores", papel="Reclamante")
    token_para(m, "RECLAMADO", "pessoa", "Rosa Helena Dias", papel="Reclamado")
    assert pseudonimizar("a Rosa dos Ventos e a Rosa vermelha", m) == "a Rosa dos Ventos e a Rosa vermelha"


def test_ancora_e_cauda_nao_juntam_quem_so_divide_um_sobrenome_comum_com_a_parte():
    # a socia com prenome composto: nem alias (ancora) nem cauda. Ate' a 0.5.34 saia errada, mas visivel; desde a
    # 0.5.35 a ancora do socio a registra como [[SOCIO_n]] — em codigo inteira e nunca confundida com a reclamante
    m = _capa(("Reclamante", "FULANA TERCIANA DA SILVA"))
    texto = "ALFA LTDA, representada por sua sócia FULANA JOSÉ DA SILVA, brasileira. A sócia FULANA JOSÉ DA SILVA assinou."
    descobrir_pessoas(texto, m)
    assert not m["tokens"]["[[RECLAMANTE_1]]"].get("aliases"), m["tokens"]["[[RECLAMANTE_1]]"]
    t = pseudonimizar(texto, m)
    assert t == ("ALFA LTDA, representada por sua sócia [[SOCIO_1]], brasileira. "
                 "A sócia [[SOCIO_1]] assinou."), t
    # a preposta, pela cauda (sem ancora); desde a 0.5.35 o prenome "FULANA" e' de duas pessoas do mapa (a
    # reclamante e a socia) e vira [[PRENOME_n]], que nao diz de quem e'
    t = pseudonimizar("Presente a preposta da reclamada, Sra. FULANA HELENA DA SILVA.", m)
    assert t == "Presente a preposta da reclamada, Sra. [[PRENOME_1]] HELENA DA SILVA.", t
    assert not m["tokens"]["[[RECLAMANTE_1]]"].get("casamentos_cauda"), m["tokens"]["[[RECLAMANTE_1]]"]
    # a mae na linha de baixo nao some na reversao
    m = _capa(("Reclamante", "FULANA BELTRANA SICRANA"))
    t = pseudonimizar("Partes:\nFULANA BELTRANA\nMARIA SICRANA, mãe", m)
    assert t == "Partes:\n[[RECLAMANTE_1]]\nMARIA SICRANA, mãe", repr(t)
    assert despseudonimizar_texto(t, m) == "Partes:\nFULANA BELTRANA SICRANA\nMARIA SICRANA, mãe"


def test_ancora_sobrenome_de_quatro_letras_a_uma_letra_e_o_advogado_inscrito_na_oab():
    # "LIMA" x "LIMO", "LEAL" x "LEAO": outro sobrenome; a 1 letra, so' com 5+ letras ("KRETZ" x "KRETZER" e'
    # prefixo e continua valendo)
    m = _capa(("Reclamante", "JOAO LIMA PRADO"))
    descobrir_pessoas("sócio JOÃO LIMO CARVALHO, brasileiro, casado.", m)
    descobrir_pessoas("sócio JOÃO LEAL CARVALHO, brasileiro, casado.", m)
    assert not m["tokens"]["[[RECLAMANTE_1]]"].get("aliases"), m["tokens"]["[[RECLAMANTE_1]]"]
    m = _capa(("Reclamante", "FULANA BELTRANA SICRANO"))
    descobrir_pessoas("FULANA TERCIANA SICRANI, brasileira, solteira, vem propor", m)
    assert m["tokens"]["[[RECLAMANTE_1]]"].get("aliases") == ["FULANA TERCIANA SICRANI"], m["tokens"]
    # o advogado substabelecido que divide o prenome e o sobrenome com a parte
    m = _capa(("Reclamante", "FULANO BELTRANO DA SILVA"))
    descobrir_pessoas("substabeleço ao Dr. FULANO CICLANO DA SILVA, brasileiro, advogado, inscrito na OAB/RS 1", m)
    descobrir_pessoas("FULANO TERCIANO DA SILVA, inscrito na Ordem dos Advogados do Brasil, Seção RS", m)
    assert not m["tokens"]["[[RECLAMANTE_1]]"].get("aliases"), m["tokens"]["[[RECLAMANTE_1]]"]
    # a parte qualificada, com a advogada dela mencionada depois, continua valendo
    descobrir_pessoas("FULANO TERCIANO SILVA, brasileiro, por sua advogada inscrita na OAB/RS 1, vem propor", m)
    assert m["tokens"]["[[RECLAMANTE_1]]"].get("aliases") == ["FULANO TERCIANO SILVA"], m["tokens"]


def test_testemunha_com_o_comeco_do_nome_da_parte_e_outra_pessoa():
    # a mae com o nome da filha menos o ultimo sobrenome; o pai e o filho sem sufixo; "Costa" x "Costalonga"
    for capa, texto, tok in (
            ("ANA PAULA SOUZA LIMA", "Testemunha da reclamada: ANA PAULA SOUZA, compromissada.", "[[TESTEMUNHA_RDA_1]]"),
            ("JOSE CARLOS DA SILVA SOUZA", "Testemunha do reclamante: José Carlos da Silva, compromissado.",
             "[[TESTEMUNHA_RTE_1]]"),
            ("MARIA JOSE COSTALONGA", "Testemunha: Maria José Costa, RG 1.", "[[TESTEMUNHA_1]]")):
        m = _capa(("Reclamante", capa))
        descobrir_pessoas(texto, m)
        assert sorted(m["tokens"]) == ["[[RECLAMANTE_1]]", tok], (capa, m["tokens"])
        assert not m["tokens"]["[[RECLAMANTE_1]]"].get("aliases"), m["tokens"]["[[RECLAMANTE_1]]"]
    m = _capa(("Reclamante", "JOSE CARLOS DA SILVA SOUZA"))
    descobrir_pessoas("Testemunha do reclamante: José Carlos da Silva, compromissado.", m)
    t = pseudonimizar("A testemunha José Carlos da Silva disse.", m)
    assert t == "A testemunha [[TESTEMUNHA_RTE_1]] disse.", t
    assert despseudonimizar_texto(t, m) == "A testemunha José Carlos da Silva disse."
    # a forma igual a' da parte continua sendo a parte (a mesma pessoa)
    m = _capa(("Reclamante", "ANA PAULA SOUZA LIMA"))
    descobrir_pessoas("Testemunha: Ana Paula Souza Lima, informante. Paradigma: ANA PAULA DE SOUZA LIMA.", m)
    assert list(m["tokens"]) == ["[[RECLAMANTE_1]]"], m["tokens"]


def test_e_maiusculo_da_conjuncao_para_a_cauda():
    m = _capa(("Reclamante", "FULANA BELTRANA SICRANA"))
    texto = "PRESENTES A RECLAMANTE FULANA E CICLANA SICRANA, SUA ADVOGADA."
    t = pseudonimizar(texto, m)
    assert t == "PRESENTES A RECLAMANTE [[RECLAMANTE_1]] E CICLANA SICRANA, SUA ADVOGADA.", t
    assert despseudonimizar_texto(t, m) == ("PRESENTES A RECLAMANTE FULANA BELTRANA SICRANA E CICLANA SICRANA, "
                                           "SUA ADVOGADA.")
    assert pseudonimizar("FULANA O SICRANA", m) == "[[RECLAMANTE_1]] O SICRANA"
    # "E." e o "E" no fim da linha continuam sendo inicial
    m = _capa(("Reclamante", "FULANA ELISA BELTRANA"))
    for texto in ("FULANA E. BELTRANA, vem", "FULANA E\nBELTRANA, vem"):
        assert pseudonimizar(texto, m) == "[[RECLAMANTE_1]], vem", repr(texto)
    # com espaco, a conjuncao antes de outra pessoa para mesmo quando a letra e' a inicial de um nome da parte
    assert pseudonimizar("FULANA E CICLANA BELTRANA assinaram", m) == "[[RECLAMANTE_1]] E CICLANA BELTRANA assinaram"
    # as iniciais sem ponto do nome da parte, num titulo do PJe, continuam na cauda
    m = _capa(("Reclamante", "FULANA OTILIA MIRELA SICRANA"))
    t = pseudonimizar("Documentos Diversos (FULANA O M SICRANA x ALFA LTDA)", m)
    assert t == "Documentos Diversos ([[RECLAMANTE_1]] x ALFA LTDA)", t


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
