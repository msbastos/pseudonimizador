# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
r"""Pseudonimizador 0.5.0, Task 1: entidade nao e' pessoa na descoberta.

Caso de producao (28/09/2026): a descoberta de testemunhas roda sobre todas
as pecas e registrou como TESTEMUNHA um ente publico ("a testemunha se
encontra fora do \nEstado do ...") e tres condominios da ata ("Testemunha
da 2a reclamada - CONDOMINIO X: <testemunha>" — o polo nao aceitava o
ordinal e a ancora pousou na pessoa juridica; a testemunha verdadeira,
depois do ":", nunca era lida ali). Tambem viraram pessoa as locucoes
depois de "perito"/"testemunha" medidas no acervo (Equipamentos de
Protecao Individual, Assinatura ..., Judicial ...).

Regras que estes testes trancam:
  - a denominacao de pessoa juridica que ABRE o candidato o recusa; a que
    vem depois de 2+ palavras de nome o corta e o nome fica;
  - a palavra que nunca e' nome corta o candidato (nao o recusa inteiro);
    o titulo de funcao no inicio ("ENGENHEIRO", "MEDICO") sai, como os
    descartaveis — "TECNICO" e "ASSISTENTE" nao (precedem tambem a secao
    do laudo) e recusam, como a assinatura do advogado e o fecho da peticao;
    o qualificador do perito ("JUDICIAL", "OFICIAL", "CONTADOR") e o par
    "Nome Completo" saem do inicio, e a pessoa entra no mapa;
  - o polo aceita o ordinal, por extenso e em lista; recusada a pessoa
    juridica, a testemunha e' o nome logo depois do ":"; os sobrenomes
    depois da inicial de quem ja' esta' no mapa nao viram outra testemunha;
  - a capa continua recebendo so' pessoas fisicas (entes novos de fora; a
    palavra nova no meio do nome nao o tira do mapa; "S A" no fim e' sufixo),
    e nenhum prenome ou sobrenome comum brasileiro virou palavra proibida.

Revisao final do ramo (29/09/2026): na ancora de testemunha e de paradigma
(pessoas naturais), o candidato com sufixo societario ou CNPJ — nele ou na
sobra ate' o ":" da ata, quando depois vem um nome — e' pessoa juridica
recusada: o corte tirava o "LTDA", o resto da empresa virava testemunha
(trocada em todo o dossie, e o filtro de saida bloqueava "a reclamada Alfa
Telecom Ltda") e a testemunha verdadeira, depois do ":", nunca entrava no
mapa. No perito o corte continua (a firma "FULANO BELTRANO ENGENHARIA LTDA"
traz o nome dele). E, como na capa (eh_pessoa_fisica), as denominacoes
acrescentadas na 0.5.0 (justica, uniao, conselho...) so' recusam quando
abrem o candidato: no meio ("FULANA DA JUSTICA BELTRANA") cortavam o nome
ou tiravam a pessoa do mapa, e a guarda nao a via.

Nomes inventados.

Rodar:  python -X utf8 testes/test_pseudonimizador_entes.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pseudonimizador.motor import pseudonimizador as pz  # noqa: E402


def _mapa():
    return {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}


def _valores(m):
    return {i["valor"] for i in m["tokens"].values()}


def test_ente_publico_depois_de_testemunha_nao_vira_pessoa():
    m = _mapa()
    pz.descobrir_pessoas("Informa que a testemunha se encontra fora do \nEstado do Vale Azul, "
                         "e que outro Estado a ouvirá por carta.", m)
    assert m["tokens"] == {}, sorted(_valores(m))


def test_ata_com_ordinal_e_pessoa_juridica_acha_a_testemunha_verdadeira():
    m = _mapa()
    pz.descobrir_pessoas("Primeira testemunha da 2ª reclamada - CONDOMINIO ALFAVILLE\nNORTE: "
                         "Joana Pereira Brito, CPF 000.000.000-00.\n"
                         "Testemunha da 3ª reclamada - CONDOMINIO BETA 24:\nBEATRIZ NUNES ROCHA, "
                         "identidade 123.", m)
    assert _valores(m) == {"Joana Pereira Brito", "BEATRIZ NUNES ROCHA"}, sorted(_valores(m))
    assert all(t.startswith("[[TESTEMUNHA_RDA_") for t in m["tokens"]), list(m["tokens"])


def test_denominacao_que_abre_o_candidato_e_recusada():
    m = _mapa()
    for texto in ("A testemunha Condomínio Edifício Sol não compareceu.",
                  "testemunha: União Federal, por seu procurador",
                  "testemunha Fazenda Nacional Paulista",
                  "testemunha Tribunal Regional Federal",
                  "testemunha Residencial Jardim Azul",
                  "testemunha Shopping Centro Norte",
                  "testemunha Defensoria Pública Estadual",
                  "testemunha Ordem dos Advogados do Brasil"):
        pz.descobrir_pessoas(texto, m)
    assert m["tokens"] == {}, sorted(_valores(m))


def test_denominacao_depois_do_nome_corta_e_o_nome_fica():
    m = _mapa()
    pz.descobrir_pessoas("Testemunha do reclamante: Fulana Beltrana do Sindicato dos Comerciarios.", m)
    pz.descobrir_pessoas("Testemunha da reclamada: Joaquina Souza Hospital Modelo.", m)
    assert _valores(m) == {"Fulana Beltrana", "Joaquina Souza"}, sorted(_valores(m))


def test_locucoes_medidas_depois_de_perito_e_testemunha_nao_viram_pessoa():
    m = _mapa()
    for texto in ("O perito Equipamentos de Proteção Individual fornecidos.",
                  "testemunha Nome Completo: a preencher",
                  "testemunha TRAZIDA PELA reclamante",
                  "o perito Certificado de Aprovação vencido",
                  "o perito Manguito Rotador do ombro",
                  "perito: Quesitos de Esclarecimentos respondidos",
                  "perito Programa de Prevenção de Riscos",
                  "testemunha AJUIZOU AÇÃO CONTRA a empresa",
                  "testemunha Assinatura Digital conferida",
                  "perito Síndrome do Túnel do Carpo",
                  "PERITO SEGUNDO LUGAR",
                  "perito Judicial CRM",
                  "PERITO TÉCNICO Já respondeu",
                  "PERITO APRESENTA QUESITOS",
                  "perito Ortopedista Traumatologista",
                  "perito Oficial de Justiça",
                  "testemunha Início do Contrato",
                  "perito Cálculo Planilha anexa",
                  "perito Assistente Técnico da reclamada",
                  "PERITO ASSISTENTE TÉCNICO BRAÇO ANTEBRAÇO PUNHO",
                  "Laudo do perito\nADVOGADO FULANO BELTRANO OAB/RS 1234",
                  "honorários do perito\nNestes Termos Pede Deferimento Cidade Nova",
                  "testemunha Consolidação das Leis do Trabalho",
                  "perito CONTADOR CRC",
                  "perito CONTAD CÓDIGO",
                  "o perito Médico Federal do INSS",
                  "testemunha do reclamante: Vossa Excelência indeferiu",
                  "perito Matrícula Imóvel 12345",
                  "perito Climate Data",
                  "perito Políticas de Premiação",
                  "testemunha São Leopoldo, onde mora",
                  "testemunha Vila Nova da Serra"):
        pz.descobrir_pessoas(texto, m)
    assert m["tokens"] == {}, sorted(_valores(m))


def test_titulo_de_funcao_sai_e_palavra_que_nunca_e_nome_corta():
    m = _mapa()
    pz.descobrir_pessoas("PERITO ENGENHEIRO FULANO DE TAL SOUZA, CREA 123.", m)
    pz.descobrir_pessoas("TESTEMUNHA FULANA DE TAL SOUZA PARA DEPOR", m)
    pz.descobrir_pessoas("Testemunha do reclamante: Carla Mendes Tavares Endereço: rua tal", m)
    pz.descobrir_pessoas("Nome / CPF\nTestemunha da reclamada: Fulgencio Tavares Ca CPF 000.000.000-00", m)
    pz.descobrir_pessoas("perito CICLANO TERCIANO SICRANO PAGINA 3", m)
    assert _valores(m) == {"FULANO DE TAL SOUZA", "FULANA DE TAL SOUZA", "Carla Mendes Tavares",
                           "Fulgencio Tavares Ca", "CICLANO TERCIANO SICRANO"}, sorted(_valores(m))


def test_qualificador_do_perito_e_nome_completo_saem_do_inicio():
    # na 0.4.4 a locucao inteira virava [[PERITO_1]] (vigiada); com "judicial",
    # "oficial" e "contador" em _NUNCA_NOME, a pessoa ficava fora do mapa
    m = _mapa()
    pz.descobrir_pessoas("o laudo do Perito Judicial Fulana Beltrana Sicrana, CRM 1.", m)
    pz.descobrir_pessoas("A Perita Oficial Ciclana Terciana Sicrana respondeu aos quesitos.", m)
    pz.descobrir_pessoas("PERITO CONTADOR FULANO DE TAL SOUZA apresentou os cálculos.", m)
    pz.descobrir_pessoas("PERITA CONTÁBIL BELTRANA SICRANA TERCIANA, CRC 2.", m)
    pz.descobrir_pessoas("TESTEMUNHA DO RECLAMANTE NOME COMPLETO FULANA TERCIANA BELTRANA RG 1234", m)
    assert _valores(m) == {"Fulana Beltrana Sicrana", "Ciclana Terciana Sicrana", "FULANO DE TAL SOUZA",
                           "BELTRANA SICRANA TERCIANA", "FULANA TERCIANA BELTRANA"}, sorted(_valores(m))
    assert "[[TESTEMUNHA_RTE_1]]" in m["tokens"], list(m["tokens"])
    t = pz.pseudonimizar("o laudo do Perito Judicial Fulana Beltrana Sicrana e a Perita Fulana Beltrana Sicrana", m)
    assert t == "o laudo do Perito Judicial [[PERITO_1]] e a Perita [[PERITO_1]]", t


def test_polo_por_extenso_e_em_lista():
    m = _mapa()
    pz.descobrir_pessoas("Primeira testemunha da primeira e segunda reclamadas: Fulana Beltrana Sicrana, "
                         "CPF 000.\nTestemunha das reclamadas: Ciclana Terciana Beltrana, RG 1.", m)
    assert _valores(m) == {"Fulana Beltrana Sicrana", "Ciclana Terciana Beltrana"}, sorted(_valores(m))
    assert all(t.startswith("[[TESTEMUNHA_RDA_") for t in m["tokens"]), list(m["tokens"])


def test_sobrenomes_depois_da_inicial_de_quem_ja_esta_no_mapa():
    m = _mapa()
    pz.descobrir_pessoas("Testemunha: FULANA TERCIANA SICRANA, advertida.\nSegunda testemunha da primeira e "
                         "segunda reclamadas: F\nTerciana Sicrana, CPF 000.", m)
    assert _valores(m) == {"FULANA TERCIANA SICRANA"}, sorted(_valores(m))
    # sem a pessoa no mapa, os sobrenomes continuam protegidos (entram como testemunha)
    m = _mapa()
    pz.descobrir_pessoas("Testemunha das reclamadas: F\nTerciana Sicrana, CPF 000.", m)
    assert _valores(m) == {"Terciana Sicrana"}, sorted(_valores(m))


def test_paradigma_tambem_passa_pelo_nome_limpo():
    m = _mapa()
    pz.descobrir_pessoas("equiparação com a paradigma CONDOMINIO ALFA NORTE, que a registrou", m)
    assert m["tokens"] == {}, sorted(_valores(m))
    pz.descobrir_pessoas("aponta como paradigma FULANA DE TAL SOUZA PARA DEPOR", m)
    assert _valores(m) == {"FULANA DE TAL SOUZA"}, sorted(_valores(m))


def test_depois_dos_dois_pontos_so_entra_nome_plausivel():
    # nao-regressao: o nome achado depois do ":" passa pelo mesmo filtro
    m = _mapa()
    pz.descobrir_pessoas("testemunha da 2ª reclamada - EMPRESA ALFA LTDA: Não compareceu.", m)
    pz.descobrir_pessoas("testemunha da reclamada - CONDOMINIO GAMA: NÃO COMPROVADA a presença.", m)
    assert m["tokens"] == {}, sorted(_valores(m))


def test_sufixo_societario_na_ancora_e_pessoa_juridica_e_a_testemunha_e_a_do_dois_pontos():
    for sufixo in ("LTDA", "Ltda.", "S A", "S.A.", "S/A", "EIRELI", "ME"):
        m = _mapa()
        pz.descobrir_pessoas(f"Testemunha da 2ª reclamada - ALFA TELECOM {sufixo}: Joana Pereira Brito, CPF 000.", m)
        assert list(m["tokens"]) == ["[[TESTEMUNHA_RDA_1]]"] and _valores(m) == {"Joana Pereira Brito"}, \
            (sufixo, sorted(_valores(m)))
    m = _mapa()
    pz.descobrir_pessoas("Testemunha da reclamada - ALFA TELECOM (CNPJ 00.000.000/0001-00): Joana Pereira Brito.", m)
    assert _valores(m) == {"Joana Pereira Brito"}, sorted(_valores(m))
    # o nome depois do ":" passa pelo mesmo filtro
    m = _mapa()
    pz.descobrir_pessoas("Testemunha da reclamada - ALFA TELECOM LTDA: BETA SEGUROS LTDA, preposta.", m)
    assert m["tokens"] == {}, sorted(_valores(m))


def test_denominacao_nova_no_meio_do_nome_nao_corta_a_pessoa():
    # espelho de eh_pessoa_fisica (Decisao 3-A): as palavras da 0.5.0 so' recusam quando abrem o nome
    m = _mapa()
    pz.descobrir_pessoas("Testemunha do reclamante: FULANA DA JUSTICA BELTRANA, CPF 000.", m)
    pz.descobrir_pessoas("Testemunha: Fulana da União Sicrana, RG 1.", m)
    pz.descobrir_pessoas("Testemunha da reclamada: Ciclana Terciana da Justiça Beltrana, CPF 000.", m)
    assert _valores(m) == {"FULANA DA JUSTICA BELTRANA", "Fulana da União Sicrana",
                           "Ciclana Terciana da Justiça Beltrana"}, sorted(_valores(m))
    t = pz.pseudonimizar("a testemunha FULANA DA JUSTICA BELTRANA e Ciclana Terciana da Justiça Beltrana", m)
    assert t == "a testemunha [[TESTEMUNHA_RTE_1]] e [[TESTEMUNHA_RDA_1]]", t
    # as de sempre continuam cortando no meio; a nova, abrindo, recusa
    m = _mapa()
    pz.descobrir_pessoas("Testemunha do reclamante: Fulana Beltrana do Sindicato dos Comerciarios.", m)
    pz.descobrir_pessoas("testemunha: Justiça Federal da Quarta Região", m)
    assert _valores(m) == {"Fulana Beltrana"}, sorted(_valores(m))


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
