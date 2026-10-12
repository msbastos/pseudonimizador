# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
r"""Testes: partes da capa → tókens (pessoa física × jurídica, papel → prefixo).

Valida que pessoas jurídicas (LTDA, S.A., CNPJ etc.) e advogados são
excluídos do mapa de pseudonimos, enquanto pessoas físicas das partes
entram com token por papel (Reclamante, Reclamado, Terceiro).

Rodar: python -X utf8 testes/test_pseudonimizador.py
"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pseudonimizador.motor.mapa import carregar_mapa, token_para
from pseudonimizador.motor.pseudonimizador import (construir_mapa,
    descobrir_pessoas, eh_pessoa_fisica, prefixo_do_papel, pseudonimizar)

def _mapa():
    return carregar_mapa(Path(tempfile.gettempdir()) / "x", "0000000-00")

def _mapa_com_joao():
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "João da Silva", papel="Reclamante")
    return m

def test_pessoa_juridica_pelo_sufixo_ou_cnpj():
    assert not eh_pessoa_fisica("GALPÕES E CONSTRUÇÕES GAÚCHA LTDA")
    assert not eh_pessoa_fisica("Mercado Modelo S.A.")
    assert not eh_pessoa_fisica("Transportes Sul S/A")
    assert not eh_pessoa_fisica("Padaria Trigal EIRELI")
    assert not eh_pessoa_fisica("Oficina do Zé ME")
    assert not eh_pessoa_fisica("Fulano & Cia")
    assert not eh_pessoa_fisica("Empresa X (CNPJ 11.222.333/0001-81)")

def test_na_duvida_e_pessoa_fisica():
    assert eh_pessoa_fisica("João da Silva")
    assert eh_pessoa_fisica("Maria Medeiros")          # sem CNPJ e sem sufixo

def test_pessoa_juridica_pela_denominacao_institucional_sem_sufixo():
    """Caso observado em produção (24/09/2026): a capa quebrou o nome em
    duas linhas e o 'LTDA' ficou na segunda; sem sufixo, a pessoa
    juridica virou 'pessoa'. Denominacao institucional no nome ja' e'
    pessoa juridica, com ou sem sufixo. Nomes de pessoa natural
    continuam pessoa."""
    for pj in ("OMEGA ASSOCIACAO DE APOIO AO PEQUENO PRODUTOR E AO",
               # 'sociedade' + 'credito' (de _NUNCA_NOME), sem sufixo: o tipo do caso original
               "Omega Sociedade de Credito Ficticia",
               "Cooperativa Agrícola do Vale", "Associação Beneficente Sul",
               "Fundação Pró-Saúde", "Instituto de Ensino Norte", "Banco Alfa",
               "Município de Cidade Nova", "Companhia Estadual de Energia",
               "Empresa Brasileira de Encomendas", "Sindicato dos Metalúrgicos de Cidade",
               "Hospital Santa Vida", "Condomínio Edifício Sol", "Massa Falida de Beta Comércio",
               "Beta & Gama Serviços Logísticos (em Recuperação Judicial)"):
        assert not eh_pessoa_fisica(pj), pj
    for pf in ("João da Silva", "Maria Medeiros", "Cristina Bancos", "Pedro Instituto Neto"):
        assert eh_pessoa_fisica(pf) == (pf != "Pedro Instituto Neto"), pf

def test_prefixo_do_papel():
    assert prefixo_do_papel("Reclamante") == "RECLAMANTE"
    assert prefixo_do_papel("Reclamado") == "RECLAMADO"
    assert prefixo_do_papel("Reclamada") == "RECLAMADO"
    assert prefixo_do_papel("Réu") == "RECLAMADO"
    assert prefixo_do_papel("Executado") == "RECLAMADO"
    assert prefixo_do_papel("Terceiro Interessado") == "TERCEIRO"
    assert prefixo_do_papel(None) == "TERCEIRO"


def test_cpf_com_e_sem_pontuacao_e_dv():
    m = _mapa()
    t = pseudonimizar("CPF 529.982.247-25 e CPF 52998224725; inválido 111.111.111-12",
                      m)
    assert t.count("[[CPF_1]]") == 2          # mesmo CPF, mesmo token
    assert "111.111.111-12" in t              # DV invalido: nao e' CPF, fica

def test_cpf_colado_a_outro_numero_por_um_separador_nao_vaza():
    m = _mapa()
    t = pseudonimizar("99 529.982.247-25 dado real", m)
    assert "[[CPF_1]]" in t
    assert "529.982.247-25" not in t

def test_cpf_todos_digitos_iguais_nao_e_valido():
    m = _mapa()
    t = pseudonimizar("CPF 111.111.111-11 do reclamante", m)
    assert "[[" not in t and "111.111.111-11" in t


def test_pis_com_dv():
    m = _mapa()
    assert "[[PIS_1]]" in pseudonimizar("PIS 120.5741.316-2", m)

def test_ctps_rg_titulo_conta_contextuais():
    m = _mapa()
    t = pseudonimizar("CTPS nº 12345, série 0012; RG 1023456789; "
                      "título de eleitor 1234 5678 9012; "
                      "agência 0434, conta corrente 12.345-6", m)
    assert "CTPS" in t and "[[CTPS_1]]" in t and "12345" not in t
    assert "[[RG_1]]" in t and "[[TITULO_ELEITOR_1]]" in t and "[[CONTA_1]]" in t

def test_conta_nao_pega_digito_solto_apos_a_palavra():
    # Regressao: a alternativa final "|\d" do grupo 1 de RE_CONTA casava
    # qualquer digito solto apos a palavra "conta" — "Levando em conta 30
    # dias" virava "conta [[CONTA_1]]0 dias", tokenizando o "3" de "30" sem
    # nenhum numero de conta bancaria de verdade por perto.
    m = _mapa()
    texto = "Levando em conta 30 dias de aviso prévio, defiro."
    assert pseudonimizar(texto, m) == texto

def test_email_e_telefone():
    m = _mapa()
    t = pseudonimizar("contato: fulano@example.com, tel. (99) 99999-8888", m)
    assert "[[EMAIL_1]]" in t and "[[TEL_1]]" in t

def test_telefone_sem_contexto_nao_pega_numero_de_processo():
    m = _mapa()
    t = pseudonimizar("processo 0090028-80.2026.5.04.9999, id 4842161", m)
    assert "[[" not in t

def test_endereco_e_cep():
    m = _mapa()
    t = pseudonimizar("residente na Rua das Flores, nº 123, Cidade Exemplo, "
                      "CEP 12345-678", m)
    assert "[[ENDERECO_1]]" in t and "Rua das Flores" not in t

# ---------------------------------------------------------------
# Task 4: substituicao de nomes (normalizacao, tolerancia a OCR) e
# descoberta de testemunhas/peritos.
# ---------------------------------------------------------------

def test_nome_com_variacao_de_caixa_acento_e_ocr():
    m = _mapa_com_joao()
    assert pseudonimizar("depoimento de JOAO DA SILVA", m) == \
        "depoimento de [[RECLAMANTE_1]]"
    assert pseudonimizar("o autor Joáo da Siilva disse", m) == \
        "o autor [[RECLAMANTE_1]] disse"          # 1 erro de OCR por palavra
    assert m["tokens"]["[[RECLAMANTE_1]]"]["variantes_vistas"]  # auditoria

def test_casamento_fuzzy_e_registrado_separado_do_exato():
    # Risco residual nº 6 (docs/privacidade.md): um casamento tolerante a
    # OCR (_dist_max1) pode fundir duas pessoas reais no mesmo tóken. Para
    # dar como auditar esses casos especificamente, a grafia que so' bateu
    # por tolerancia a erro entra tambem em "casamentos_fuzzy" — alem de
    # "variantes_vistas", que registra toda grafia (exata ou fuzzy).
    m = _mapa_com_joao()  # mapa["[[RECLAMANTE_1]]"] = "João da Silva"
    pseudonimizar("o autor Joáo da Siilva disse", m)  # "Siilva" e' fuzzy
    info = m["tokens"]["[[RECLAMANTE_1]]"]
    assert info.get("casamentos_fuzzy")
    assert any("Siilva" in v for v in info["casamentos_fuzzy"])

    m2 = _mapa_com_joao()
    pseudonimizar("depoimento de JOAO DA SILVA", m2)  # so' caixa/acento: exato
    info2 = m2["tokens"]["[[RECLAMANTE_1]]"]
    assert not info2.get("casamentos_fuzzy")

def test_nome_sem_conectivo_tambem_casa():
    m = _mapa_com_joao()
    assert "[[RECLAMANTE_1]]" in pseudonimizar("assina João Silva", m)

def test_nome_longo_substitui_antes_do_curto():
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "João da Silva")
    token_para(m, "TERCEIRO", "pessoa", "João da Silva Sobrinho")
    t = pseudonimizar("presentes João da Silva Sobrinho e João da Silva", m)
    assert t == "presentes [[TERCEIRO_1]] e [[RECLAMANTE_1]]"

def test_primeiro_nome_isolado_so_quando_inequivoco():
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "João da Silva")
    token_para(m, "RECLAMADO", "pessoa", "João Pereira")
    # dois "João": ambiguo — nao vira o tóken de nenhum dos dois; desde a
    # 0.5.0 vira um tóken proprio do prenome, que nao diz de quem e'
    assert pseudonimizar("disse João que sim", m) == "disse [[PRENOME_1]] que sim"
    m2 = _mapa_com_joao()
    assert "[[RECLAMANTE_1]]" in pseudonimizar("disse João que sim", m2)

def test_nome_completo_todo_minusculo_e_tokenizado():
    # OCR de comprovante PIX transcreve o destinatario todo em minusculas
    # (processo 0090021-88.2025.5.04.9999, dossie de 04/09/2026): o nome
    # COMPLETO de um titular do mapa (2+ palavras) casa mesmo sem
    # maiuscula alguma na janela.
    m = _mapa_com_joao()
    assert pseudonimizar("pix recebido de joao da silva", m) == \
        "pix recebido de [[RECLAMANTE_1]]"

def test_nome_completo_minusculo_com_erro_de_ocr_tambem_casa():
    m = _mapa_com_joao()
    t = pseudonimizar("pix recebido de joao da siva", m)  # dist 1 em "silva"
    assert t == "pix recebido de [[RECLAMANTE_1]]"

def test_primeiro_nome_isolado_minusculo_continua_fora():
    # O relaxamento de caixa vale so' para o nome completo multi-palavra:
    # primeiro nome sozinho em minusculas segue exigindo inicial maiuscula
    # (senao "silva" em "engenheiro joao pediu" tokenizaria texto corrido).
    m = _mapa_com_joao()
    assert "[[" not in pseudonimizar("disse joão que sim", m)

def test_palavra_minuscula_nao_e_nome():
    # Contrato ajustado em 04/09/2026: janela toda minuscula que coincide
    # com o nome COMPLETO de um titular agora vira token — "aviso prévio
    # indenizado" com titular "Aviso Prévio" e' falso positivo ACEITO
    # (super-tokenizacao reversivel pelo mapa), em troca de nao vazar nome
    # real que o OCR transcreveu em minusculas. Nome de titular vem da capa
    # do PJe; colisao com locucao comum e' improvavel na pratica.
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "Aviso Prévio")  # nome improvavel
    assert pseudonimizar("aviso prévio indenizado", m) == \
        "[[RECLAMANTE_1]] indenizado"

def test_descobre_testemunha_com_polo_e_perito():
    m = _mapa()
    texto = ("Primeira testemunha do reclamante: MARIA DE LOURDES FARIAS, "
             "compromissada. Testemunha da reclamada, Sr. José Antunes. "
             "O perito Carlos Werle apresentou o laudo.")
    descobrir_pessoas(texto, m)
    valores = {i["valor"].upper() for i in m["tokens"].values()}
    assert "MARIA DE LOURDES FARIAS" in valores
    assert any(t.startswith("[[TESTEMUNHA_RTE_") for t in m["tokens"])
    assert any(t.startswith("[[TESTEMUNHA_RDA_") for t in m["tokens"])
    assert any(t.startswith("[[PERITO_") for t in m["tokens"])
    t = pseudonimizar(texto, m)
    assert "FARIAS" not in t and "Antunes" not in t and "Werle" not in t

def test_testemunha_caixa_alta_sem_pontuacao_nao_vaza_nome():
    # Regressao: enchimento guloso entre a palavra-chave/polo e o nome
    # recuava (backtrack) ate achar QUALQUER sequencia de 2+ maiusculas
    # mais a frente no texto (tudo em CAIXA ALTA casa com _NOME), pousando
    # no meio de "OUVIDA" em vez de no nome real — que vazava sem token.
    m = _mapa()
    texto = ("TESTEMUNHA DO RECLAMANTE MARIA DE LOURDES FARIAS OUVIDA EM "
             "AUDIENCIA CONFIRMOU OS FATOS.")
    descobrir_pessoas(texto, m)
    valores = {i["valor"] for i in m["tokens"].values()}
    assert any("MARIA DE LOURDES FARIAS" in v for v in valores)
    t = pseudonimizar(texto, m)
    assert "MARIA DE LOURDES FARIAS" not in t
    assert any(t.startswith("[[TESTEMUNHA_RTE_") for t in m["tokens"])

def test_endereco_nao_engole_nome_e_cpf_vizinhos():
    # Regressao: a cauda do endereco ([^\n]{0,80}, sem excluir virgula)
    # engolia tudo depois da virgula ate 80 caracteres — nome de terceiro
    # e CPF citados "aos cuidados de" ficavam dentro do span de endereco
    # em vez de virarem os proprios tokens.
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "João da Silva", papel="Reclamante")
    t = pseudonimizar(
        "Rua das Flores, nº 123, aos cuidados de João da Silva, "
        "CPF 529.982.247-25, CEP 12345-678", m)
    assert "[[ENDERECO_1]]" in t
    assert "[[RECLAMANTE_1]]" in t
    assert "[[CPF_1]]" in t
    assert "João da Silva" not in t and "529.982.247-25" not in t

def test_span_de_endereco_nao_apaga_cauda_do_nome_por_sobreposicao():
    # Regressao: a fusao de spans em pseudonimizar() mantem o primeiro
    # span (por posicao inicial) e descarta qualquer outro que comece
    # antes do fim dele — mesmo quando o descartado e' um span de NOME
    # que se estende PARA ALEM do fim do span descartante. Um endereco
    # sem virgula antes do nome (nome "colado" ao numero do imovel/rua)
    # casa como um unico span de endereco que termina no MEIO do nome —
    # o span do nome inteiro e' descartado e a cauda que sobra depois do
    # fim do endereco ("... dos Santos") vaza em claro na saida, em vez
    # de ser coberta pelo tóken de pessoa.
    m = _mapa()
    nome = "Joao da Silva Pereira dos Santos"
    token_para(m, "RECLAMANTE", "pessoa", nome, papel="Reclamante")
    texto = ("Rua Marechal Deodoro numero mil e duzentos " + nome +
             ", Cidade Exemplo, CEP 12345-678")
    t = pseudonimizar(texto, m)
    assert "[[RECLAMANTE_1]]" in t
    assert "Pereira dos Santos" not in t and "Silva" not in t

def test_descobre_perito_com_pronome_de_tratamento_doutor():
    # (a) Dr./Dra. acrescentado a alternancia de pronome de tratamento.
    m = _mapa()
    texto = "O perito do juízo, Dr. Carlos Werle, engenheiro, apresentou o laudo."
    descobrir_pessoas(texto, m)
    valores = {i["valor"] for i in m["tokens"].values()}
    assert "Carlos Werle" in valores
    t = pseudonimizar(texto, m)
    assert "Werle" not in t

def test_descobre_todas_as_testemunhas_de_um_rol_em_lista():
    # (b) continuacao de lista apos o primeiro nome: virgula/"e" encadeiam
    # mais nomes, cada um registrado como uma TESTEMUNHA_n propria.
    m = _mapa()
    texto = ("Arrola as seguintes testemunhas: Maria de Lourdes Farias, "
             "Paulo Roberto Nunes e Jose Antunes.")
    descobrir_pessoas(texto, m)
    valores = {i["valor"] for i in m["tokens"].values()}
    assert "Maria de Lourdes Farias" in valores
    assert "Paulo Roberto Nunes" in valores
    assert "Jose Antunes" in valores
    toks_testemunha = [t for t in m["tokens"] if t.startswith("[[TESTEMUNHA")]
    assert len(toks_testemunha) == 3
    t = pseudonimizar(texto, m)
    assert "Farias" not in t and "Nunes" not in t and "Antunes" not in t

def test_nome_com_palavras_em_ordem_trocada():
    # Regressao (caso de produção, 04/09/2026): a inicial grafava o nome
    # da paradigma com os sobrenomes em ordem trocada ("Nome A B" no mapa,
    # "Nome B A" no texto — erro comum de digitacao forense) e o casador,
    # que so' aceitava a sequencia exata de palavras do mapa, deixava o
    # nome passar em claro. Nomes com 2-3 palavras significativas casam em
    # qualquer permutacao (janela do mesmo tamanho, todas as palavras
    # casando um-a-um, inicial maiuscula mantida).
    m = _mapa()
    token_para(m, "TESTEMUNHA_RTE", "pessoa", "Fernanda Souza Machado",
               papel="testemunha")
    t = pseudonimizar("comparou-se com Fernanda Machado Souza, vendedora", m)
    assert "[[TESTEMUNHA_RTE_1]]" in t
    assert "Fernanda" not in t and "Machado" not in t and "Souza" not in t
    # auditoria: casamento por permutacao fica registrado no mapa, como os
    # casamentos fuzzy (risco de fundir duas pessoas de nomes permutados)
    info = m["tokens"]["[[TESTEMUNHA_RTE_1]]"]
    assert any("Fernanda Machado Souza" in v
               for v in info.get("casamentos_permutados", []))

def test_nome_de_duas_palavras_com_ordem_invertida():
    # Sem a permutacao, o primeiro nome inequivoco ("João") ja' virava
    # tóken sozinho, mas o sobrenome anteposto ("Silva") vazava em claro.
    m = _mapa_com_joao()   # "João da Silva" → significativas [joao, silva]
    t = pseudonimizar("assina Silva João", m)
    assert "[[RECLAMANTE_1]]" in t
    assert "Silva" not in t

def test_nome_partido_por_linha_intercalada_nao_vaza_o_segundo_nome():
    # Regressao (0090049-90, 22/09/2026): a extracao do dispositivo da
    # sentenca intercalou uma linha no meio do nome da reclamante (trecho
    # em negrito extraido fora de ordem): "por NOME SOBRENOME1" / "no
    # merito, julgo..." / "DA SOBRENOME2". Nenhuma janela casava o nome
    # completo; so' o primeiro nome isolado virava tóken e o sobrenome
    # colado a ele ficou em claro ("[[RECLAMANTE_1]] SOBRENOME1").
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "Fulana Pereira da Costa",
               papel="Reclamante")
    texto = ("e, \n formulados por FULANA PEREIRA\nno mérito, julgo "
             "PROCEDENTES EM PARTE os pedidos\nDA COSTA em face de EMPRESA LTDA")
    t = pseudonimizar(texto, m)
    assert "[[RECLAMANTE_1]]" in t
    assert "PEREIRA" not in t, t
    assert "no mérito, julgo" in t

def test_prefixo_do_nome_nao_engole_conectivo_final():
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "Fulana Pereira da Costa",
               papel="Reclamante")
    t = pseudonimizar("Fulana Pereira da empresa ré", m)
    assert t == "[[RECLAMANTE_1]] da empresa ré", t

def test_prefixo_comum_a_duas_pessoas_nao_vira_tóken_de_nenhuma():
    # Prefixo ambiguo (mesma regra do primeiro nome isolado): atribui-lo a
    # uma das pessoas fundiria duas pessoas reais no mesmo tóken.
    m = _mapa()
    token_para(m, "RECLAMANTE", "pessoa", "Maria Pereira Souza",
               papel="Reclamante")
    token_para(m, "TESTEMUNHA", "pessoa", "Maria Pereira Lima",
               papel="testemunha")
    t = pseudonimizar("Maria Pereira Souza e Maria Pereira Lima; "
                      "depois, Maria Pereira assinou", m)
    assert t.startswith("[[RECLAMANTE_1]] e [[TESTEMUNHA_1]];"), t
    assert "[[RECLAMANTE_1]] assinou" not in t
    assert "[[TESTEMUNHA_1]] assinou" not in t

def test_descobre_paradigma_pelas_ancoras_de_equiparacao():
    # Ancoras de descoberta na inicial (antes de qualquer ata): pedidos de
    # equiparacao salarial nomeiam a paradigma por "equiparacao com NOME"
    # ou "paradigma NOME" — no mesmo molde de RE_TESTEMUNHA/RE_PERITO.
    m = _mapa()
    texto = ("Postula equiparação salarial com Fulana Tal, vendedora do "
             "mesmo setor. Aponta como paradigma a Sra. Beltrana Qual "
             "desde 2020.")
    descobrir_pessoas(texto, m)
    valores = {i["valor"] for i in m["tokens"].values()}
    assert "Fulana Tal" in valores
    assert "Beltrana Qual" in valores
    assert any(t.startswith("[[PARADIGMA_") for t in m["tokens"])
    t = pseudonimizar(texto, m)
    assert "Fulana" not in t and "Beltrana" not in t

def test_paradigma_sem_nome_proprio_nao_vira_token():
    m = _mapa()
    texto = "adotou o paradigma normativo aplicável, sem equiparação com ninguém."
    descobrir_pessoas(texto, m)
    assert not m["tokens"]
    assert pseudonimizar(texto, m) == texto

def test_paradigma_que_tambem_e_testemunha_nao_vaza_com_ordem_trocada():
    # Cenario completo do mesmo caso de 04/09/2026: a paradigma ja' esta' no mapa
    # como testemunha (descoberta na ata), e a inicial a nomeia com os
    # sobrenomes em ordem trocada num pedido de equiparacao. As duas
    # causas combinadas deixavam o nome inteiro em claro no dossie.
    m = _mapa()
    token_para(m, "TESTEMUNHA_RTE", "pessoa", "Fernanda Souza Machado",
               papel="testemunha")
    texto = "pede equiparação com Fernanda Machado Souza, sua paradigma."
    descobrir_pessoas(texto, m)
    t = pseudonimizar(texto, m)
    assert "Fernanda" not in t and "Machado" not in t and "Souza" not in t

def test_marcadores_de_pagina_e_avisos_passam_intactos():
    m = _mapa_com_joao()
    texto = ("--- página 3 (PDF) ---\n[ALARME DE OCR — divergência numérica.\n"
             " CONFERIR NO PDF antes de citar valores ou trechos desta página.\n"
             " alarme abc:1:3]\nJoão da Silva depôs.")
    t = pseudonimizar(texto, m)
    assert "[ALARME DE OCR" in t and "--- página 3 (PDF) ---" in t
    assert "[[RECLAMANTE_1]]" in t

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
        except Exception as e:  # noqa: BLE001
            falhas += 1
            print(f"FALHA {nome}\n      {e!r}")
    print(f"\n{len(testes) - falhas}/{len(testes)} passaram, {falhas} falha(s)")
    sys.exit(1 if falhas else 0)
