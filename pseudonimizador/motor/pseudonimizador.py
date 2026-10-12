# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
# Origem: Ulpiano, ulpiano/nucleo/privacidade/pseudonimizador.py, commit 5bab2ff (11/10/2026); alterações descritas abaixo.
r"""
==============================================================
 ARQUIVO: pseudonimizador.py
 PROJETO: AnaliseDeProcessos / privacidade
 VERSAO:  0.5.36
 ATUALIZADO: 2026-10-07
 ALTERACAO 0.5.36: o numero de processo (CNJ) nunca vira codigo (sonda de
   07/10/2026). O dossie que cita outro processo saia com o numero partido
   ("0090006-85.[[PIS_1]]"): a cauda "AAAA.J.TR.OOOO" tem 11 digitos com um
   separador entre os grupos, e' uma janela de RE_11DIGITOS entre limites
   de palavra e, conforme o ano, o tribunal e a vara, passa no digito
   verificador do PIS ou do CPF. Processo e' publico: a janela que sobrepoe
   um CNJ completo (RE_CNJ, _spans_de_cnj) e' pulada em _cpf_pis_spans — o
   varredor dos Entendimentos, que a reusa, deixa de apontar CPF/PIS dentro
   do CNJ — e o CNJ entra nos tomados de _spans_de_identificadores, para
   nenhum outro identificador (telefone, conta...) nascer dentro dele. O
   CPF de verdade na mesma frase continua em codigo.
 ALTERACAO 0.5.35: as ancoras da execucao (Parte B; Diferido 3 da Parte
   A). O dossie da execucao leva autos de arrematacao, cartas de
   adjudicacao, atos constitutivos e AR, cujos terceiros nao sao parte da
   capa nem testemunha e saiam em claro. "arrematante(s)", "adquirente(s)",
   "socio/socia(s)" (tambem "-administrador", "-gerente", "-diretor") e
   "recebido por"/"recebedor(a)" ancoram o nome que vem depois, lido sem a
   caixa e provado pelo lexico, como a testemunha (_nomes_depois_da_ancora,
   em lista); tokens [[ARREMATANTE_n]], [[ADQUIRENTE_n]], [[SOCIO_n]],
   [[RECEBEDOR_n]]. O leiloeiro e o oficial de justica, agentes publicos,
   seguem sem ancora. A qualidade do socio ("majoritaria", "administrador",
   "retirante", ...) e' pulada antes do nome, nunca o nome.
   Revisao final do ramo (validacao no acervo): nas quatro ancoras, o
   candidato em minusculas so' entra com a primeira palavra prenome do
   ranking (1.000+ pessoas) e nenhuma palavra comum dos autos — senao e'
   pulado, nunca vai a incertos (_minusculo_da_execucao_aceito); o
   separador " - ", " – " e ":" antes do nome fica preso por teste.
 ALTERACAO 0.5.34: o documento e o telefone partidos pela quebra de linha
   da extracao do PDF. O CPF com "ddd.ddd.ddd-" no fim da linha e os dois
   digitos verificadores na seguinte ia em claro (a janela de 11 digitos
   so' aceitava um caractere entre dois digitos; o mesmo CPF numa linha
   so', na mesma peca, saia em codigo). CPF e PIS: a quebra (com espacos e
   CR-LF em volta) depois do ponto ou do hifen, so' na grafia usual
   (_documento_partido), com o codigo do mesmo numero inteiro. CNPJ: a
   mesma quebra em RE_CNPJ, e o codigo pelos digitos (_token_do_cnpj).
   Telefone: a quebra depois do hifen (RE_TEL, _SEP_TEL). Revisao: o par
   de anos partido continua fora do telefone da conversa (RE_PAR_DE_ANOS
   com o mesmo separador); o valor do CNPJ e do telefone vai ao mapa sem
   a quebra (_sem_a_quebra) — a reversao devolve o numero numa linha so'
   e o mesmo numero inteiro cai no mesmo codigo. VERSAO_DESCOBERTA_DE_NOMES
   "3": os dossies montados antes aparecem para preparar de novo.
 ALTERACAO 0.5.33: medicao de vazamento no acervo (nomes da descoberta
   antiga com a troca nova): a regra do ":" da rodada 5 deixava em claro o
   ultimo sobrenome seguido de ":" ("... Pereira Lima: que trabalhava").
   O sobrenome do ranking que nao e' palavra de lista fica no nome antes
   do ":"; o ":" tambem fecha o aposto. "Dia: 5" continua rotulo.
 ALTERACAO 0.5.32: rodada de correcao 6 — no CRM sem tratamento seguido de
   nome nem prenome provado, o recurso das 3 ultimas palavras corta a
   janela na palavra de frase, de rotulo, de parada forte, no verbo
   conjugado e na palavra com cara de lingua (_frase_no_crm); "Dr."
   seguido de verbo ou frase nao abre nome. A frase do atestado e a
   remissao do formulario ("vide", "ver", "verso", "anexa", "ficha",
   "menor", "impubere", "idem") em _PALAVRAS_DA_FRASE (nenhuma no ranking).
 ALTERACAO 0.5.31: rodada de correcao 5. O CRM: a especialidade, o cargo e
   a palavra de saude fora do ranking entre o nome e o CRM (e o separador
   "-", "," ou "/") sao pulados indo para tras (_ESPECIALIDADES,
   _nome_colado_ao_crm), e a fronteira de saude so' vale 'a esquerda do
   nome; com tratamento e prenome provado, o nome logo depois do
   tratamento e' lido mesmo com frase ate' o CRM (_nome_depois_do_tratamento).
   O nome logo depois da ancora forte (":" ou tratamento) conta como
   aberto (_ler_nome e _nome_limpo); a troca le' o valor registrado como
   aberto; no contato, a palavra do ranking entre palavras de nome fica.
   A palavra seguida de ":" e' rotulo e nao entra no nome. O prenome raro
   em "-ia" com sobrenome do ranking nao tem cara de lingua.
 ALTERACAO 0.5.30: rodada de correcao 4. Regra geral (varredura das listas
   de parada, veto e fronteira contra o ranking do IBGE: 282 de 936 casos
   falhavam, em 21 palavras): a palavra delas com 1.000+ pessoas no ranking
   (_nome_do_ranking) e' parada FRACA e nao corta (_nome_limpo(aberto=)) dentro
   de um nome aberto por prenome provado ou por tratamento; a troca
   (_nome_do_token) guarda o nome assim. Fora, de proposito:
   NUNCA_DENTRO_DO_NOME (tratamento, preposicao, siglas juridicas, sufixo
   societario, "nao"). C-1: no CRM, a palavra de nao-nome ou de saude do
   ranking nao e' fronteira; com tratamento, a saude nunca recusa; o
   comeco nunca e' palavra de saude. I-1: o papel so' conta colado ao nome;
   advogado e procurador colados nao impedem a ancora (a excecao do
   advogado da capa nao e' feita: a descoberta nao recebe os advogados).
 ALTERACAO 0.5.29: rodada de correcao 3. I-c: no CRM sem tratamento o
   comeco volta a _abre_nome ("Rosa Maria Pires CRM"); a palavra de servico
   de saude ou termo clinico e' fronteira da janela (o nome comeca depois
   dela: "Atestado Clara Nunes Bezerra CRM") e so' o candidato e'
   conferido; o recorte das 3 ultimas guarda os conectivos ("fulano de tal
   crm"). (i) o nome de 2 palavras aberto por prenome provado e fechado
   pela palavra de frase do ranking ("Rita Sabe."). (ii) o verbo de
   sistema ("saiu", "entrou") nunca e' sobrenome do contato. (iv) o
   tratamento e' pulado ao procurar o papel antes do nome, e depois de
   advogado ou procurador o nome nao e' registrado.
 ALTERACAO 0.5.28: rodada de correcao 2. I-a: a palavra de
   _PALAVRAS_DA_FRASE que esta' no ranking do IBGE (derivada do ranking na
   carga: _frase_no_ranking) para FRACA — entre duas palavras do ranking,
   ou no fim do nome aberto por prenome provado, fica no nome ("Jairo Sabe
   Lima", "Joana Pereira Norte"); no contato, a palavra de frase logo
   depois do prenome provado, no fim da linha, tambem ("Marcos Caixa").
   I-b: preposto, representante, socio, patrono (e procurador, advogado)
   nunca sao nome; o nome logo depois do papel de outra pessoa vira
   [[PESSOA_n]] (pessoa citada), nao testemunha/perito/paradigma; o valor
   de ancora nunca comeca por papel ou palavra pulavel. M-a: no CRM sem
   tratamento, so' o prenome provado abre o nome, e o termo clinico conta
   como servico de saude. M-b: a mensagem do sistema da conversa ("voce
   apagou") corta o contato. M-c: alias de parte nunca e' descartado.
 ALTERACAO 0.5.27: rodada de correcao 1 (revisao independente com sondas
   sinteticas nas tres caixas, ramo x main). C1: o prenome que e' palavra
   comum ("Rosa", "Clara", "Celeste") abre o nome seguido de prenome ou
   sobrenome do ranking (_abre_nome, _prenome_do_ranking; tambem prova o
   nome). I1: o aposto depois da virgula que fecha em virgula ou ponto
   entra sem prova (incerto em codigo); depois da empresa recusada sem o
   ":", a procura segue apos a virgula. I2: sem `lingua`, so' o verbo
   conjugado encerra pelo fim de palavra (o sobrenome raro fica no nome);
   os passos do Jev passam `lingua`; quem nao le' nome depois de ancora
   usa TODA_A_LINGUA (a regra de antes). I3: verbos e termos do depoimento,
   cargos e palavras de conversa em _PALAVRAS_DA_FRASE; o infinitivo raro
   do ranking (< 2.000) nao salva da cara de lingua; o CRM sem tratamento
   nem prenome nunca depois de preposicao nem com servico de saude. M1: o
   prefixo minusculo exige a 1a palavra exata. M2: o CRM olha so' os 200
   caracteres antes. M4: o "nao_nome" de uma palavra nao desliga o prenome
   de uma pessoa do mapa. M5: o "nao_nome" de um alias o desativa
   (aliases_descartados/variantes_descartadas), e o Desfazer o devolve.
   M6: sai _nome_limpo_recomecando (codigo morto).
 ALTERACAO 0.5.26: medicao no acervo (etapa 2) — o sobrenome raro com fim
   de palavra da lingua ("... Cantar") encerrava a leitura depois da
   ancora e ficava em claro. Agora descobrir_pessoas e
   descobrir_pessoas_de_formulario aceitam `lingua` (as palavras que o
   processo escreve em minusculas fora de nome, leitura_ocr.vocabulario,
   que a montagem passa): com ela, o fim de palavra da lingua so' encerra
   a palavra que o processo usa como palavra. Sem ela, como antes.
 ALTERACAO 0.5.25: o "nao e' nome" de trecho que ja' esta' em codigo — o
   tóken de pessoa de descoberta (nunca a parte da capa) cujo VALOR o juiz
   decidiu nao ser nome e' marcado "descartado" (aplicar_descartes, que a
   montagem chama logo depois do pedido do juiz); fica no mapa (a reversao
   o devolve), mas sai da troca (_nome_do_token), da fusao das descobertas
   e de tudo o que token_fora_da_guarda filtra (a guarda de entrada, o
   filtro de saida, a omissao por palavra). O "Desfazer" tira a marca.
 ALTERACAO 0.5.24: a conferencia do Jev nas ancoras (decisao do juiz de
   05/10/2026) — o nome que uma ancora de pessoa achou sem prova
   (testemunha, perito, paradigma, formulario, CRM, contato de conversa)
   vai sozinho a' conferencia injetada (`conferir_nome`, que a montagem
   repassa a descobrir_pessoas, descobrir_pessoas_de_formulario e
   descobrir_interlocutores; o modulo continua sem rede), so' depois dos
   vetos e das paradas da leitura e nunca com separador, dado sensivel,
   endereco ou 5+ palavras (_conferido). A decisao do juiz vem antes;
   pessoa com p alta entra em codigo sem ir aos incertos; expressao com
   p muito alta nao entra no mapa nem nos incertos; o meio e a falha,
   como antes (codigo + incerto, com `jev` = a probabilidade ou None):
   _decidir_ancorado.
 ALTERACAO 0.5.23: auditoria da caixa, #17 — a inicial do prenome com o
   resto do nome ("f. terciano sicrano") e a inicial dentro da cauda sao
   lidas em qualquer caixa; "a"/"o"/"e" continuam so' com ponto ou quebra
   de linha (com espaco sao artigo ou conjuncao).
 ALTERACAO 0.5.22: auditoria da caixa, #11 (em parte), #12 e #13. #11: o
   prenome isolado com um vizinho que prova o nome (o tratamento ou o
   papel logo antes — "a sra. clara", "a reclamante joana" —, ou a
   palavra do nome do dono logo depois) ou que o juiz decidiu ser nome
   (incertos.py) e' trocado em qualquer caixa; o que ele decidiu nao ser,
   nunca. Sem eles fica a regra de antes (a inicial maiuscula): tirar a
   caixa do prenome solto quebrava a copia do titulo (_copia_com_nomes),
   a omissao por palavra e a guarda, que contam com ele ("serviços com.
   marco 2022", "bom dia joao") — decisao que fica para o juiz. #12: a
   ancora de qualificacao ("maria pereira souza, brasileira") em qualquer
   caixa (sai RE_NOME_SEQ). #13: a linha de baixo sem a maiuscula — o
   sobrenome da parte no fim e' a prova; a palavra do meio, sem cara de
   frase; a decisao "nao_nome" do juiz vale.
 ALTERACAO 0.5.21: auditoria da caixa, #9, #8 e #10 — a troca do nome
   incompleto da parte sem a caixa. #9: a cauda do prenome ou do prefixo
   ("[[PRENOME]] sicrana") nao exige mais maiuscula; a prova e' a palavra
   do nome do dono, e a do meio que nao e' dele so' passa sem cara de
   frase. #8: o prefixo exclusivo do nome todo em minusculas ("pix para
   maria pereira", de "Maria Pereira Lima") e' trocado, salvo quando so'
   tem palavra comum ("rosa clara"). #10: o nome sem o 1o prenome (3+
   palavras) nao exige a 1a maiuscula, e "outra pessoa logo antes" deixa
   de ser a palavra com maiuscula: e' a palavra que nao para a leitura de
   um nome e nao e' das que vem antes dele ("CICLANO TERCIANO ..." continua
   outra pessoa; "INQUIRIDO TERCIANO ..." e' a parte).
 ALTERACAO 0.5.20: auditoria da caixa, #6 — o contato, o remetente de
   grupo e o da exportacao da conversa exigiam a inicial maiuscula em
   cada palavra (_nome_do_interlocutor): o contato salvo em minusculas
   nao era descoberto. A caixa sai; as ancoras do aplicativo (o status, o
   "~", a forma da exportacao, o prenome do lexico) e os vetos de sempre
   ficam, e a palavra da frase ("vou", "que", "hoje") tambem corta. O
   interlocutor sem prenome provado vai em codigo e fica anotado como
   incerto ("contato de conversa"); a decisao do juiz vale antes.
 ALTERACAO 0.5.19: auditoria da caixa, #1 (a peca central) — nas ancoras
   de pessoa (testemunha, perito, paradigma, equiparacao, o rotulo do
   formulario) o nome deixou de ser delimitado pela caixa (RE_NOME_SEQ):
   em minusculas escapava, em CAIXA ALTA qualquer palavra contava. A
   ancora so' marca onde o nome pode comecar; _ler_nome le' as palavras
   normalizadas ate' a pontuacao, a quebra de linha (salvo antes de
   sobrenome do ranking), o rotulo seguinte ou a parada (_parada): FORTE
   no vocabulario que nunca e' nome e na palavra da frase; FRACA, fora do
   ranking do IBGE, no fim de palavra da lingua e na palavra comum dos
   autos (`comuns`, opcional) — a fraca entre duas palavras de nome nao
   para ("Beltrana Exemplar Souza"). O comeco (_nomes_depois_da_ancora):
   a primeira palavra do enchimento de sempre cuja leitura da' nome; sem
   prenome provado (_nome_provado), so' logo depois da ancora, do ":" ou
   do tratamento e sem cara de lingua comum — depois da virgula ou do
   ponto, so' com prova ("o perito, no prazo de" nao e' nome). No perito,
   nunca logo depois de preposicao; a pessoa juridica recusada recomeca
   depois do ":" da ata; a lista continua por virgula, ponto-e-virgula ou
   "e" em qualquer caixa (sem prova, so' o item que acaba limpo). O nome
   ancorado sem prova vai em codigo e fica anotado como incerto. Medicao
   no acervo (96 processos): ver docs/privacidade.md.
 ALTERACAO 0.5.18: auditoria da caixa, #5 — o nome antes do CRM era a
   sequencia de palavras com forma de nome logo antes dele, sem ancora a'
   esquerda: em minusculas escapava ("dr. fulano de tal crm"), em caixa
   alta levava a palavra de antes ("AFASTAMENTO DR FULANO DE TAL CRM"
   virava um valor so', e "AFASTAMENTO" um prenome trocado em todo o
   dossie). Agora o nome comeca no tratamento ("Dr.", "Dra.", "Doutor")
   ou, sem ele, no primeiro prenome provado das ate' 5 palavras antes do
   CRM (_nomes_antes_do_crm); sem os dois, as ate' 3 ultimas. E os nomes
   incertos (pedido do juiz, incertos.py): o nome de ancora explicita de
   pessoa (aqui, o rotulo do formulario e o CRM) sem prova independente
   da caixa vai em codigo e fica anotado em mapa["nomes_incertos"] para
   o juiz confirmar; a decisao dele (mapa["nomes_decididos"]) vale antes
   de tudo: "nao_nome" descarta, "nome" registra sem anotar
   (_registrar_ancorado).
 ALTERACAO 0.5.17: auditoria da caixa, #2 — o candidato da testemunha,
   do perito e da paradigma que ABRE com palavra que nunca e' nome
   ("TESTEMUNHA COMPROMISSADA MARIA SILVA", "PERITO NOMEADO CARLOS
   WERLE") era recusado inteiro, e o nome escapava; agora recomeca
   depois dela, so' num prenome provado sem a caixa (a lista escrita 'a
   mao ou o ranking do IBGE, fora o prenome que e' palavra comum). Desde
   a 0.5.19 isso e' feito pela leitura depois da ancora
   (_nomes_depois_da_ancora). A locucao ("NOMEADO PARA AVALIACAO DE
   ADICIONAL") continua recusada.
 ALTERACAO 0.5.16: auditoria da caixa (05/10/2026, regra do juiz: a caixa
   nao e' indicio de nome), #4 e #3 — no rol em caixa alta ("MARIA
   PEREIRA E JOSE SOUZA") o "E" tambem continua a lista (so' o "e"
   minusculo continuava: a 2a testemunha em diante escapava); e o nome
   do perito nunca comeca numa preposicao nem logo depois dela, em
   qualquer caixa ("PERITO DO JUIZO, DR. FULANO": o "DO" tinha forma de
   nome, o candidato "DO JUIZO" era recusado e o perito escapava).
 ALTERACAO 0.5.15: o nome no titulo do documento de menor tambem pelo
   ranking de prenomes e sobrenomes do IBGE (lexico 0.2.0), sem caixa.
 ALTERACAO 0.5.14: o nome no titulo do documento de menor (05/10/2026,
   regra do juiz) — a caixa nao conta: maiuscula ou inicial maiuscula
   nao e' indicio de nome proprio. Vale o prenome do lexico ou a
   confirmacao do texto do documento numa ancora de pessoa, comparados
   sem caixa nem acento (_nome_no_rotulo).
 ALTERACAO 0.5.13: nivel sigiloso (04/10/2026) — as pessoas juridicas
   da capa entram no mapa (categoria 'pj', prefixo do papel) e sao
   trocadas pela denominacao inteira ou sem o sufixo societario do fim;
   todo CNPJ vira [[CNPJ_n]]. A empresa que nao e' parte fica em claro.
   A denominacao que contem o nome de uma pessoa do mapa ("Fulano Beltrano
   Transportes LTDA") vira inteira o codigo da empresa; o nome sozinho, o
   da pessoa — tambem no empresario individual, cuja forma sem sufixo e'
   o nome do dono (sem codigo de pessoa para ele, o nome sozinho fica com
   o da empresa e volta como a denominacao inteira: limite conhecido). O CNPJ dentro de trecho ja' tomado (URL, nome, denominacao)
   nao ganha codigo (nunca fica no mapa um tóken que nao esta' no texto).
   Fora do sigiloso, empresa e CNPJ como antes.
 ALTERACAO 0.5.12: nivel de protecao (04/10/2026) — com
   mapa["nivel"] == "publico" nenhuma pessoa entra no mapa nem e'
   trocada; documentos e contatos seguem em codigo; a URL de perfil
   pessoal (rede social) segue em codigo, e a que so' era trocada por
   trazer o nome de uma pessoa segue o nome, em claro; sem a chave, tudo
   como antes.
 ALTERACAO 0.5.11: re-revisao 3 das conversas (03/10/2026) — a lista fixa
   das saudacoes e dos termos trabalhistas tinha "boas", parte do
   sobrenome composto Vilas/Villas Boas: o contato "Carla Vilas Boas"
   virava "[[INTERLOCUTOR_1]] Boas", com a sobra em claro em todas as
   pecas. "boas" e "saude" saem da lista; "festas" e "vindas" cortam
   "Boas Festas" e "Boas Vindas"; entram "noturna", "gas", "cultura",
   "itinere", "equiparacao" e "salarial" ("Hora Noturna", "Vale Gas",
   "Horas Itinere", "Equiparacao Salarial" viravam interlocutor).
 ALTERACAO 0.5.10: re-revisao 2 das conversas (03/10/2026) — telefones
   ainda em claro: o segundo numero so' com o final depois da VIRGULA
   ("99999-1234,5678": so' a barra fazia o codigo unico) e o corrido de
   9 digitos entre duas letras dos dois lados ("oi999991234ok",
   "OK999991234OK"), que a guarda do rastreio (duas letras, 9 digitos,
   duas letras, tambem em minusculas) tirava da busca. Agora
   RE_TEL_COM_OUTRO_FINAL aceita a virgula com o final de 4 digitos (o
   "NNNN-NNNN,NN" de 2 digitos continua de fora) e a guarda so' vale na
   forma dos Correios: as letras em maiusculas e o digito verificador do
   S10 certo (_rastreio_dos_correios).
 ALTERACAO 0.5.9: re-revisao 2 das conversas (03/10/2026) — o par de
   anos com o outro final depois da barra ("2022-2023/2024",
   "(2019-2020/2021)") virava [[TEL_n]] por RE_TEL_COM_OUTRO_FINAL, que
   tambem roda na passada do DDD, onde o par de anos nao era olhado. Agora
   RE_PAR_DE_ANOS aceita os outros finais (barra ou virgula) e as duas
   passadas o deixam como esta'.
 ALTERACAO 0.5.8: re-revisao 2 das conversas (03/10/2026) — a regra da
   0.5.6 (ao menos uma palavra fora das comuns) deixava passar o termo
   generico com so' PARTE das palavras nas comuns do processo: com as
   comuns reais, "Recursos Humanos" com o status virava [[INTERLOCUTOR_n]]
   em 70 de 91 processos, "Boa Tarde"/"Boa Noite" em 74, "Seguro
   Desemprego" em 56, "Bom Dia" em 44, e a troca o aplicava em todas as
   pecas ("o setor de [[INTERLOCUTOR_1]] negou"). Agora a saudacao e o
   termo de pedido, beneficio, setor e documento trabalhista
   (_SAUDACAO_OU_TERMO_DO_TRABALHO, lista fixa) cortam o nome sempre, como
   a tela do aplicativo; de fora o que tambem e' sobrenome ("vale",
   "dias", "hora", "seguro", "moral"): a outra palavra do par corta.
 ALTERACAO 0.5.7: re-revisao das conversas (03/10/2026) — telefones
   vizinhos ainda em claro na conversa: o corrido de 9 digitos colado a
   letra ("contato999991234", "999991234ok"), os dois com virgula sem
   espaco ("99999-1234,98888-5678"), o fixo com espaco colado a palavra
   ("fone3333 1234") e o segundo numero so' com o final depois da barra
   ("99999-1234/5678"). Agora a virgula entre dois numeros com forma de
   telefone e' partida como a barra (RE_BARRA_ENTRE_TELEFONES), o corrido
   de 9 digitos e o fixo com espaco aceitam a letra colada — o codigo de
   rastreio (duas letras, 9 digitos, duas letras; RE_RASTREIO) fica de
   fora —, e o "99999-1234/5678" e' um codigo so' (RE_TEL_COM_OUTRO_FINAL).
 ALTERACAO 0.5.6: re-revisao das conversas (03/10/2026), regressao da
   0.5.5 — com a palavra comum cortando so' depois de 2 palavras, a linha
   feita SO' de palavras comuns dos autos ("Recursos Humanos" com o
   status, "~ Cesta Basica", "(12/03/2025 10:41) Vale Transporte:",
   "Bom Dia" com o status) virava [[INTERLOCUTOR_n]], e a troca a
   aplicava em todas as pecas, tambem em minusculas e no plural ("Requer
   [[INTERLOCUTOR_1]]" no lugar de "horas extras"); as palavras entravam
   no mapa como de nome (omitidas nas conversas). Agora
   _nome_do_interlocutor exige ao menos uma palavra fora das comuns (o
   prenome do lexico conta como fora): "Carla Vale" e "Keyvison Vale"
   continuam codigo.
 ALTERACAO 0.5.5: revisao final das conversas (02/10/2026) — a palavra
   comum dos autos (`comuns`) cortava a ancora do interlocutor: o
   sobrenome que e' palavra comum do processo ("Vale", "Domingos": em
   minusculas em 2+ documentos de dezenas de processos do acervo) ficava
   em claro logo depois do codigo, e o contato de 2 palavras caia para 1 e
   era recusado — o nome inteiro em claro. Agora, no cabecalho que o
   status do aplicativo ou o prenome do lexico confirmam (e no remetente
   "~", no da exportacao e no do grupo com o contato salvo, marcas do
   aplicativo), a palavra comum so' corta com 2+ palavras antes dela
   (_nome_do_interlocutor, minimo_antes_do_comum); o cargo, o lugar, o
   parentesco e a tela do aplicativo cortam sempre. A omissao por palavra
   tira a palavra comum que sobrou logo depois do codigo na forma do
   cabecalho (seletor/leitura_ocr.py 0.5.3).
 ALTERACAO 0.5.4: revisao final das conversas (02/10/2026) — formas
   plausiveis de telefone ficavam inteiras em claro na conversa: entre
   parenteses sem o DDD (tambem o "[99999-1234]", que o saneamento faz
   parentese), dois numeros com barra ("99999-1234/98888-5678"; com o
   DDD, ficava o segundo), depois de "/" ou "-" ("fone/99999-1234") e o
   colado a palavra terminada em o, l ou I, seguido de palavra que comeca
   por o ou l, ou entre as barras de uma tabela ("contato99999-1234",
   "Rafael99999-1234", "99999-1234ok", "|99999-1234|": a troca da sosia
   convertia a letra, o numero ganhava um digito e as guardas o vetavam).
   Agora o parentese antes nao impede, e o "/" e o "-" so' impedem junto
   de um digito (_ANTES_TEL, _FIM_TEL); a barra entre dois numeros com
   forma de telefone e' partida na busca (RE_BARRA_ENTRE_TELEFONES); a
   sosia so' vira digito quando nao encosta em outra letra (a barra
   vertical, so' entre digitos ou hifen) — "99999-l234" e "9999O-1234"
   continuam —, e a busca roda tambem sobre o texto como esta'. A data, o
   CNPJ, o valor, o par de anos e o numero com digito verificador
   ("1234-5678-9") continuam de fora.
 ALTERACAO 0.5.3: revisao final das conversas (02/10/2026) —
   descobrir_interlocutores pulava o candidato sempre que a troca mudava
   QUALQUER parte do nome: o contato no alto, o remetente "~" ou o da
   exportacao com o prenome de uma parte ou testemunha ("Maria Souza",
   com a reclamante Maria; "Jose Ramalho", com a testemunha Jose) saia
   "[[RECLAMANTE_1]] Souza" — o sobrenome do terceiro em claro (a omissao
   por palavra nao o tira: nao e' palavra do mapa) e a autoria dada a'
   parte. Agora so' se pula quando a troca leva o nome INTEIRO ou quando
   cada palavra que sobra e', a ate' 1 letra (menos de 5 letras) ou 2,
   palavra do nome de um codigo que a troca pos nele (a parte lida com
   erro, que a omissao completa; _a_troca_ja_o_leva). Nos demais casos,
   [[INTERLOCUTOR_n]], e o prenome comum as duas pessoas passa a
   [[PRENOME_n]] pelo mecanismo de sempre; o registro e' desfeito quando
   a troca nao aplica o codigo novo ao nome inteiro.
 ALTERACAO 0.5.2: conversas de WhatsApp como prova (02/10/2026), C3 (a) e
   (b). (a) So' no texto de conversa de aplicativo de mensagens
   (pseudonimizar(..., conversa=True), que o montador usa nas paginas da
   peca "conversa"): todo numero com forma de telefone vira [[TEL_n]] —
   com o +55 (tambem "+55 (51) 9.9999-1234"), com o DDD entre parenteses
   ou nao, o celular de 9 digitos com hifen, espaco, ponto ou hifen entre
   espacos, o corrido (com ou sem o DDD, com o 55), o fixo com hifen,
   espaco ou ponto (com ou sem o DDD), o internacional; a letra colada a
   um digito (l, I, O) lida como digito so' na busca (RE_TEL_CONVERSA) —,
   esteja ou nao no mapa; no fim da frase, o ponto final nao impede; o
   mesmo numero em grafias diferentes (com e sem o +55, com e sem o DDD)
   tem um codigo so', e o do mapa e' reaproveitado (_token_do_telefone,
   pelos digitos); o celular com o DDD e o +55 vem antes do PIS e do CPF
   (o "51 99999-1234" que passa no digito verificador do PIS era [[PIS_n]],
   com o +55 solto), salvo na grafia de CPF ou de PIS ou depois de "CPF",
   "PIS" ou "NIT". Nunca: o par de anos ("2019-2020", "2019 2020"), a
   hora, a data, o CEP, o valor, o numero do processo, o codigo de
   rastreio. Nas capturas do acervo, 50 numeros com forma de telefone e
   nenhum trocado. Fora da conversa nada muda: no resto dos autos o hifen
   sozinho pega CPF, PIS e codigo de barras (8.311 vezes em 4.103
   paginas). (b) descobrir_interlocutores(): o contato no alto da
   conversa (as primeiras linhas uteis) com forma de nome de pessoa — 2 a
   4 palavras com inicial maiuscula, so' letras, sem palavra da tela do
   aplicativo nem palavra comum dos autos (`comuns`, que o montador tira
   do proprio processo); o tratamento ou o parentesco na frente ("Dona",
   "Dr.") pulado, o sufixo entre parenteses e o que vem depois de " - "
   fora — vira ancora quando a linha seguinte e' o status ("online",
   "digitando", "visto por ultimo") ou a primeira palavra e' prenome do
   lexico; e o remetente de grupo ("~ Fulano Beltrano"), o da exportacao
   do aplicativo ("[dd/mm/aaaa hh:mm] Fulano Beltrano:" ou "dd/mm/aaaa
   hh:mm - Fulano Beltrano:") e o do grupo com o contato salvo (a linha
   inteira com forma de nome, prenome do lexico, 2+ vezes na pagina, logo
   depois de uma hora ou de um separador e antes da mensagem). O codigo e'
   [[INTERLOCUTOR_n]], papel "interlocutor", fundido como os descobertos
   (_PAPEIS_DESCOBERTOS); o que a troca ja' pega (a parte, o comeco do
   nome dela) nao vira outro codigo, e o codigo que a troca nao consegue
   aplicar ao proprio nome nao fica no mapa (a regra "mapa so' com token
   trocavel" do incidente de 24/09/2026).
 ALTERACAO 0.5.1: correcoes da revisao final do ramo (29/09/2026), cada uma
   com teste. (1) Os caracteres invisiveis: tirar o U+200B colava as
   palavras quando ele era o unico separador ("Fulana<U+200B><U+200B>disse"
   -> "Fulanadisse", 987 vezes entre letras em 3 processos do acervo) e
   nem a troca nem a guarda viam o nome; e a lista so' tinha 5 codigos —
   os controles de direcao (U+202D ... U+202C em volta de cada palavra, 3
   processos) e o hifen condicional (U+00AD, 14) ficavam, a janela do nome
   nao casava e so' o prenome era trocado. Uma funcao so',
   limpar_invisiveis() (a troca, o rotulo, a descoberta e a capa por
   texto_limpo(); o montador; a guarda): a sequencia de invisiveis entre
   duas letras com U+200B ou controle de direcao vira UM espaco (no acervo
   eles separam palavras — 1825 casos contra nenhum dentro de palavra); o
   resto (hifen condicional, U+200C/U+200D, U+2060-U+2064, U+FEFF) sai.
   (2) A ancora de qualificacao e a cauda juntavam na parte quem so'
   dividia com ela um sobrenome muito comum ("representada por sua socia
   FULANA JOSE DA SILVA", com a reclamante "FULANA TERCIANA DA SILVA"; a
   preposta "Sra. FULANA HELENA DA SILVA"; a mae na linha de baixo) ou um
   sobrenome de 4 letras a 1 letra ("JOAO LIMO CARVALHO" com "JOAO LIMA
   PRADO"), e o advogado substabelecido: o Claude lia a socia como a
   reclamante, e a reversao escrevia o nome da reclamante no lugar dela.
   A palavra fora do nome da parte que e' prenome do lexico (lexico.PRENOMES:
   o prenome composto de outra pessoa) recusa a ancora e para a cauda; a 1
   letra, so' com 5+ letras (o prefixo continua: "KRETZ" x "KRETZER"); a
   qualificacao "inscrito na OAB" (antes de "por seu advogado") recusa a
   ancora. Nenhuma das 36 caudas nem dos 12 aliases de parte do acervo
   muda.
   (3) A testemunha ou paradigma cujo nome, com 3+ palavras, era o comeco
   (ou quase igual, a 1 letra ou truncado) do nome da parte da capa virava
   a parte (a mae com o nome da filha menos o ultimo sobrenome; o pai e o
   filho sem sufixo; "Maria Jose Costa" com "MARIA JOSE COSTALONGA"): o
   depoimento dela saia como [[RECLAMANTE_1]], e a reversao escrevia o nome
   da parte no lugar do dela — regressao (na 0.4.4, tókens separados). Com
   a parte da capa, a testemunha e a paradigma se fundem so' pela forma
   igual (as mesmas palavras significativas); a forma nao identica, so' o
   perito, com o mesmo numero de palavras (o caso medido: a parte
   capturada como perito, com o sobrenome truncado). Entre os descobertos,
   nada muda.
   (4) A empresa com sufixo societario na ancora de testemunha ou de
   paradigma: _nome_limpo cortava o "LTDA" em vez de recusar, e o resto
   ("ALFA TELECOM") virava testemunha — trocado em todo o dossie ("Alfa"
   isolado inclusive), e o filtro de saida bloqueava "Condeno a reclamada
   Alfa Telecom Ltda" —; e o nome depois do ":" da ata ("Testemunha da 2a
   reclamada - ALFA TELECOM LTDA: Fulana ...") so' era lido quando
   _nome_limpo recusava: a testemunha verdadeira ficava em claro, sem a
   guarda ver. Nas ancoras de pessoa natural (testemunha, paradigma,
   equiparacao), o candidato com sufixo societario ou CNPJ — nele ou na
   sobra ate' o ":" quando depois vem um nome (_pj_na_ancora) — e' pessoa
   juridica recusada, e o nome depois do ":" passa pelo mesmo filtro. No
   perito o corte continua ("FULANO BELTRANO ENGENHARIA LTDA").
   (5) Na cauda, o "E" maiusculo (a conjuncao em texto todo em caixa alta)
   era tomado por inicial e pulado: "PRESENTES A RECLAMANTE FULANA E
   CICLANA SICRANA" virava um tóken so' da parte, e a reversao apagava a
   segunda pessoa (erro material na minuta; na 0.4.4, "[[RECLAMANTE_1]] E
   CICLANA SICRANA"). "A"/"O"/"E" isolados so' contam como inicial seguidos
   de ponto ou de quebra de linha, como em _trocar_parciais, ou, com espaco,
   quando sao a inicial de uma palavra do nome do dono e a palavra seguinte
   e' outra inicial ou palavra do nome (a revalidacao nos dados reais achou,
   num titulo do PJe, as iniciais sem ponto do nome da reclamante — "PRENOME
   O M SOBRENOME" — e a regra so' do ponto deixava o sobrenome em claro);
   senao a cauda para.
   (6) _corta_aqui aplicava as denominacoes acrescentadas na 0.5.0
   (justica, uniao, conselho, residencial...) em toda posicao: a pessoa com
   "da Justica" ou "da Uniao" no meio do nome saia do mapa ou entrava
   truncada — nada trocado, e a guarda nao a via (a 0.4.4 a registrava
   inteira). Como em eh_pessoa_fisica (Decisao 3-A do plano), elas so'
   recusam quando abrem o candidato; no meio, so' cortam as de sempre
   (sindicato, hospital, "estado do", "uniao federal"...).
 ALTERACAO 0.5.0: guarda sem alarme falso e sem ponto cego (caso de
   producao de 28/09/2026: o trabalho automatico parou um processo com
   "um nome apareceu sem codigo no dossie"; nada foi ao Claude). (1)
   Entidade nao e' pessoa na descoberta: _nome_limpo() tira do inicio os
   descartaveis e os titulos de funcao ("ENGENHEIRO", "MEDICO"), recusa o
   candidato que a denominacao de pessoa juridica ou uma palavra de
   _NUNCA_NOME ABRE e CORTA o que vem depois de 2+ palavras de nome
   ("Fulana Beltrana do Sindicato ..." -> "Fulana Beltrana"; antes o
   candidato inteiro virava tóken, ou era recusado e o nome vazava sem a
   guarda ver); RE_PJ_INSTITUCIONAL ganha entes e imoveis (uniao, distrito
   federal, fazenda publica, governo do, republica, procuradoria,
   defensoria, tribunal, justica, conselho, ordem dos advogados,
   seccional, edificio, residencial, shopping) — na capa, essas so' quando
   abrem o nome ("FULANA DA JUSTICA BELTRANA" e' gente) —, e "S A" no fim
   do nome e' sufixo societario; _NUNCA_NOME ganha as locucoes medidas no
   acervo depois de "perito"/"testemunha"; "segundo" vai para os
   descartaveis (so' sai do inicio: tambem e' nome de gente); os
   qualificadores do perito ("JUDICIAL", "OFICIAL", "CONTADOR") e o par
   "Nome Completo" do formulario tambem saem do inicio; o polo de
   RE_TESTEMUNHA aceita o ordinal ("da 2a reclamada", "da primeira e
   segunda reclamadas", "das reclamadas") e, com a pessoa juridica
   recusada, a testemunha e' o nome logo depois do ":"; os sobrenomes
   depois da inicial de quem ja' esta' no mapa ("F\nBeltrana Sicrana") nao
   viram outra testemunha.
   (2) Um predicado so' — eh_token_de_pj() — e as locucoes de mapa antigo
   (eh_locucao_legada) ficam fora do substituidor, da guarda e do filtro
   de saida (token_fora_da_guarda); o mapa nao e' editado: esses tókens
   ficam para a reversao. O nome real com cauda contaminada de mapa antigo
   ("Fulano ... ENGENHEIRO DE SEGURANCA") volta a ser alvo pelo nome
   (_nome_do_token). O primeiro nome isolado so' vale para tóken de
   pessoa, nunca para palavra de _NUNCA_PRENOME_ISOLADO, nunca depois de
   topônimo (Sao/Santo/Santa/Santana/Vila, Sant'; a quebra de linha so'
   depois de Sao/Santo/Santa — "Santana" e "Vila" tambem sao sobrenomes)
   e nunca quando a palavra do texto e' "MARÇO" e o prenome do mapa, sem
   cedilha, "Marco" (so' as palavras de _PALAVRAS_COMUNS_COM_CEDILHA: o
   prenome "CONCEICAO" da capa continua trocando "Conceição"; o contrario
   — capa sem acento, texto com — sempre valeu).
   (3) Janela de 2+ palavras com a 1a minuscula ("a reclamante joana
   Pereira Lima", "o condominio Alfa") passa a ser trocada quando a 1a
   casa EXATAMENTE a 1a do alvo e outra palavra da janela tem maiuscula —
   a guarda, que compara sem caixa, a via e parava a sessao com razao;
   sem fuzzy na 1a, a preposicao a uma letra do prenome nao e' engolida;
   nunca no alvo permutado nem com a 1a de menos de 3 letras ("30 dias
   Fulano" com "Fulano Dias"; o artigo antes de "Alfa S A").
   (4) Os pontos cegos da guarda. A cauda: depois da troca do nome
   incompleto (o prenome, o prefixo; nunca a do nome inteiro, depois da
   qual vem outra pessoa), ate' 3 palavras com maiuscula cuja ultima e'
   palavra do nome do mesmo tóken entram no tóken ("FULANA TERCIANA
   BELTRANA" com "FULANA BELTRANA SICRANA" na capa; auditavel em
   "casamentos_cauda"). A ancora de qualificacao: prenome de PARTE + 1 a 3
   palavras com maiuscula, uma delas sobrenome dela, + ", brasileira|
   qualificada|portador" vira outro nome da parte (chave aditiva
   "aliases": alvo da troca e, como variante, da guarda). A inicial do
   prenome com o resto do nome ("F. Terciana Sicrana") e o nome sem o 1o
   prenome (3+ palavras, nunca logo depois de outra palavra de nome) sao
   alvos da pessoa, so' quando de uma so'. A pessoa da linha de baixo que
   repete o sobrenome da parte (a lista de herdeiros, o "Nome da mae" do
   formulario) vira [[PESSOA_n]] na descoberta, antes da troca. A mesma
   pessoa descoberta de novo ("Fulana Beltrana Souza" e "FULANA BELTRANA
   SOUZA DA SILVA", a uma letra ou truncada pela coluna da ata; a parte
   da capa, so' com a forma igual ou mais curta; nunca com sufixo de
   geracao) vira alias do tóken dela, nao tóken novo — dois tókens
   deixavam o prenome ambiguo, nunca trocado e nunca vigiado. A inicial
   ("D", "M.") nao para a cauda. O prenome que continua ambiguo vira [[PRENOME_n]] (categoria
   'pessoa', o valor e' a grafia), nunca para PRENOMES_PALAVRA_COMUM; seguido
   do sobrenome de uma so' das pessoas daquele prenome, vira o tóken dela;
   seguido de palavra de nenhuma delas, fica so' o [[PRENOME_n]].
   (5) pseudonimizar_rotulo(): titulo e descricao do PJe (texto livre do
   advogado, em minusculas, com '-'/'_' entre as palavras) — numa copia de
   mesmo tamanho as palavras de nome de pessoa do mapa (palavras_de_nome)
   ganham maiuscula e '-'/'_' viram espaco; os nomes achados na copia sao
   trocados no original, e a variante registrada e' a grafia do original.
   O mesmo vale, em pseudonimizar(), para a linha da peca que cita um
   documento do PJe pelo Id ("13. servicos com. fulana 2022 (id NNNNNNN)"):
   o advogado copiou ali o titulo que digitou. Os meses e "marco" nunca
   ganham maiuscula na copia ("o marco inicial", "holerite marco 2023").
   O nome em maiusculas colado a' palavra anterior ("(C-AlfaxFULANA
   BELTRANA)") e' lido como palavra propria (_palavras), e a guarda o
   procura tambem assim.
   (6) URL (http(s):// ou www.) com palavra de nome de pessoa do mapa, ou
   de perfil pessoal (linkedin.com/in/, instagram.com/, facebook.com/,
   tiktok.com/@, x.com/, twitter.com/, wa.me/), vira [[URL_n]] inteira
   (categoria 'url'; a reversao devolve a URL exata). A continuacao na
   linha seguinte so' quando ela comeca por pontuacao de URL, por digito
   depois da URL partida em pontuacao ("-", "/", "=", "?", "&", "_"), e'
   toda minuscula sem espaco, ou e' o resto do slug com hifen depois do
   slug partido em "-"/"_" — nunca palavra com maiuscula sem hifen; o nome
   que comeca dentro da URL e termina fora corta a URL antes dele. No
   dominio institucional (.jus.br, .gov.br, .leg.br, .mp.br, .def.br), so'
   o perfil pessoal ou 2+ palavras do nome da mesma pessoa.
   (7) O texto e' lido em NFC em pseudonimizar(), pseudonimizar_rotulo(),
   descobrir_pessoas() e construir_mapa(): em NFD, RE_PALAVRA partia o nome
   na marca combinante (a troca falhava, a descoberta gravava pedacos) e a
   guarda, que tira as marcas, o via; os caracteres de largura zero
   (U+200B e afins, que a extracao do PDF deixa entre as palavras) saem
   junto (texto_limpo): com eles a janela do nome nao casava e o
   sobrenome ficava em claro. RE_ENDERECO aceita "da/de/do/das/dos" no
   fim da linha com o logradouro na seguinte.
 ALTERACAO 0.4.4: perito. Caso de producao (27/09/2026): "perito nomeado
   para avaliação de Adicional de Insalubridade" — RE_PERITO pousou na
   primeira sequencia de maiusculas e a locucao virou [[PERITO_1]],
   trocada em todo o dossie ("do respectivo [[PERITO_1]]") e bloqueando
   no filtro de saida toda minuta que dissesse "adicional de
   insalubridade". (1) RE_PERITO nao aceita nome logo apos preposicao
   (_NAO_APOS_PREPOSICAO); (2) _NUNCA_NOME ganha o vocabulario de pericia
   (adicional, insalubridade, periculosidade, laudo, nomeado, avaliacao,
   engenheiro...); (3) o nome real do perito, que vem da capa, chegava
   com o marcador PAGINA_CAPA_PROCESSO_PJE colado e nunca casava:
   construir_mapa() tira o marcador (indices antigos; o parser tambem o
   tira desde esta data) e prefixo_do_papel("Perito") passa a PERITO,
   o mesmo tóken do perito descoberto no laudo.
 ALTERACAO 0.4.3: pessoa juridica pela DENOMINACAO (RE_PJ_INSTITUCIONAL:
   sociedade, cooperativa, associacao, fundacao, instituto, banco,
   municipio, companhia, empresa, comercio, ... , "em recuperacao
   judicial"), com ou sem sufixo societario; e construir_mapa() so'
   registra parte cujo nome _nome_plausivel aceita (o que _spans_de_nomes
   consegue trocar) — o resto vai para mapa["nao_pseudonimizadas"] (papel
   e motivo, sem o nome). Caso observado em producao (24/09/2026): a capa
   quebrou o nome de uma pessoa juridica em duas linhas, o parser guardou
   so' a primeira ("... E AO", sem o LTDA), o nome virou token 'pessoa',
   nunca casou no texto (tinha palavra de _NUNCA_NOME) e o filtro de
   saida bloqueou a reversao da minuta por "valor do mapa em claro".
 ALTERACAO 0.4.2: prefixos do nome como alvos. Caso de producao (22/09/2026):
   a extracao do dispositivo da sentenca intercalou uma linha
   no meio do nome da reclamante ("por NOME SOBRENOME1" / "no merito,
   julgo..." / "DA SOBRENOME2"); nenhuma janela casava o nome completo, so'
   o primeiro nome isolado virou tóken e o SOBRENOME1 colado a ele vazou.
   _spans_de_nomes passa a ter como alvos os prefixos do nome (2+
   palavras, sem terminar em conectivo), depois dos alvos completos, com
   inicial maiuscula obrigatoria (a janela toda em minusculas continua
   valendo so' para o nome completo). Prefixo que coincida com alvo ou
   prefixo de outra pessoa e' ambiguo e fica de fora. Residual aceito: a
   cauda solta ("DA SOBRENOME2" em outra linha) nao e' tokenizada —
   sobrenome isolado nao identifica e tokeniza-lo apagaria homonimos.
 ALTERACAO 0.4.1: "nome" feito de palavras comuns nao entra no mapa nem
   e' substituido. Caso de producao (dossie com muitas contestacoes): RE_TESTEMUNHA
   roda sobre todas as pecas e capturou "DA RECLAMANTE", o nome de um
   banco, o nome da cidade, "NÃO COMPROVADA" e o nome de uma empresa de
   servicos como testemunhas; a regra do primeiro nome isolado fez todo
   "Da"/"DA" (773x), "Reclamante" (1148x), "Banco" (941x), o nome da
   cidade (862x) e "Não" (301x) do dossie
   virar [[TESTEMUNHA_n]]. Agora: (1) _nome_plausivel() tira as palavras
   comuns iniciais (conectivos, pronomes de tratamento, ordinais) e
   rejeita o candidato que fique com menos de 2 palavras ou que contenha
   palavra que nunca e' de nome de pessoa (banco, servicos, ltda, alegre,
   reclamante, nao, clt...); descobrir_pessoas() so' registra o que
   passa; (2) _spans_de_nomes() ignora nomes do mapa que nao passam (mapa
   contaminado por execucao anterior) e o primeiro nome isolado exige 3+
   letras e nao ser palavra comum.
 ALTERACAO 0.4.0: vazamento do nome da paradigma de equiparacao salarial
   (caso de 04/09/2026 — duas causas combinadas). (1)
   _spans_de_nomes: nome com 2-3 palavras significativas (fora
   conectivos) tambem casa com essas palavras em QUALQUER ordem — a
   inicial grafava os sobrenomes em ordem trocada ("Nome A B" no mapa,
   "Nome B A" no texto, erro comum de digitacao forense) e o casador so'
   aceitava a sequencia exata do mapa. Janela do mesmo tamanho, todas as
   palavras casando um-a-um em alguma permutacao, inicial maiuscula e
   adjacencia mantidas. Decisao de custo×risco: limitado a 2-3 palavras
   (ate' 6 alvos extras por nome, nada de fatorial em nomes longos); a
   tolerancia fuzzy por palavra e' mantida nas permutacoes (o cenario
   tipico e' justamente inicial degradada por OCR) porque as salvaguardas
   existentes se aplicam iguais; em empate de tamanho, alvo em ordem
   exata tenta ANTES de alvo permutado (duas pessoas reais com nomes
   permutados um do outro casam cada uma no proprio tóken); casamento por
   permutacao fica auditavel no mapa em "casamentos_permutados" (analogo
   de "casamentos_fuzzy" para o risco de fundir duas pessoas — ver risco
   residual nº 6 de docs/privacidade.md). (2) descobrir_pessoas: ancoras
   novas RE_PARADIGMA ("paradigma NOME") e RE_EQUIPARACAO ("equiparacao
   [salarial] com NOME"), no molde de RE_TESTEMUNHA/RE_PERITO — pedidos
   de equiparacao nomeiam a paradigma na inicial, antes de qualquer ata.
   Prefixo decidido: PARADIGMA_n (nao TERCEIRO_n) — o papel processual e'
   juridicamente relevante para a minuta (a analise de equiparacao
   precisa saber quem e' a paradigma), segue o padrao dos demais papeis
   descobertos (TESTEMUNHA/PERITO) e nao acrescenta risco de
   reidentificacao (o mapa continua local). Se a mesma pessoa ja' tem
   tóken (ex.: paradigma que e' testemunha), token_para devolve o tóken
   existente pela chave normalizada.
 ALTERACAO 0.3.3: _spans_de_nomes() aceita janela TODA em minusculas
   quando ela corresponde ao nome COMPLETO de um titular do mapa (2+
   palavras, exato ou fuzzy dist<=1 por palavra). Motivo: nome de
   destinatario de PIX transcrito pelo OCR todo em minusculas escapou da
   tokenizacao e ficou em claro no dossie (caso de 04/09/2026). Primeiro nome isolado segue exigindo inicial maiuscula.
   Falso positivo ACEITO conscientemente: locucao comum que coincida com
   o nome completo de um titular ("aviso previo" para titular "Aviso
   Previo") vira token — super-tokenizacao reversivel e auditavel pelo
   mapa, preferivel a vazar nome real (risco nº 4 de docs/privacidade.md).
 ALTERACAO 0.3.2: onda final de correcoes da revisao. (1) RE_CONTA: a
   alternativa final "|\d" do grupo 1 casava QUALQUER digito solto apos a
   palavra "conta" — "Levando em conta 30 dias" virava "conta
   [[CONTA_1]]0 dias" sem numero de conta bancaria nenhum por perto;
   removida, so' resta a alternativa que exige pelo menos 4 digitos.
   (2) pseudonimizar(): a fusao de spans priorizava quem comeca primeiro
   na ordenacao, nao a fonte do span — um span de endereco sem virgula
   antes do nome (nome "colado" ao numero do imovel) podia terminar no
   MEIO de um nome, fazendo o span de nome inteiro ser descartado por
   sobreposicao e a cauda do nome vazar em claro depois do fim do
   endereco. Agora nomes tem prioridade: identificador que sobrepoe
   QUALQUER span de nome e' descartado inteiro antes da fusao. (3)
   RE_TESTEMUNHA/RE_PERITO: acrescentado "Dr./Dra." a alternancia de
   pronome de tratamento (faltava so' "Sr./Sra."); RE_TESTEMUNHA agora
   captura continuacao de lista ("Fulano, Beltrano e Sicrano") no mesmo
   grupo "nome", cada NOME_SEQ da lista virando uma TESTEMUNHA_n propria
   em descobrir_pessoas(); o slot de pontuacao entre a palavra-chave e o
   nome repete a unidade "enchimento + pontuacao opcional" ate 2 vezes,
   absorvendo um marcador de lista ("1)") antes do nome. NAO foram
   acrescentadas ancoras novas "compromissad[oa]/depoente" — decisao
   consciente do controlador (spec 7.2) para nao arriscar falso positivo.
   (4) _spans_de_nomes(): quando o casamento com o nome do mapa so' bate
   por tolerancia a erro de OCR (_dist_max1), a grafia encontrada agora
   tambem entra em info["casamentos_fuzzy"] (alem de "variantes_vistas"),
   para auditar especificamente o risco residual nº 6 de
   docs/privacidade.md (duas pessoas reais fundidas no mesmo tóken por
   nomes a 1 letra de distancia).
 ALTERACAO 0.3.1: correcao de revisao da Task 4 — dois enchimentos
   gulosos vazavam dado sensivel. (1) RE_TESTEMUNHA/RE_PERITO: em texto
   todo em CAIXA ALTA (ata escaneada), o [^\n:;,.]{0,20}/{0,30} guloso
   entre a palavra-chave/polo e o nome recuava (backtrack) ate achar
   QUALQUER sequencia de 2+ maiusculas mais a frente — pousava no meio
   de uma palavra comum e o nome real vazava sem token. Trocado para
   preguicoso ({0,20}?/{0,30}?): ancora no nome logo apos a
   palavra-chave, sobra tolerada de no maximo 1-2 palavras maiusculas
   adjacentes por causa do {1,4}. (2) RE_ENDERECO: a cauda pos-virgula
   [^\n]{0,80} nao excluia virgula/ponto-e-virgula e engolia tudo o que
   viesse depois (nome de terceiro, CPF, CEP) num unico span de
   endereco. Limitada a UM segmento curto [^\n,;]{0,40} — o numero do
   imovel, em geral —, deixando nome/CPF/CEP para os proprios
   matchers.
 ALTERACAO 0.3.0: Task 4 — pseudonimizar() completo (identificadores +
   nomes). _spans_de_nomes casa nomes do mapa tolerando variacao de
   caixa/acento (normalizar) e ate' 1 erro de OCR por palavra
   (_dist_max1), com nome mais longo vencendo sobre um mais curto e
   primeiro nome isolado so' substituido quando inequivoco no mapa
   inteiro. descobrir_pessoas() acha testemunhas (com polo, quando
   citado) e peritos em ata/laudo antes da substituicao. RE_TESTEMUNHA
   e RE_PERITO usam (?i:...) escopado as palavras-chave em vez de (?i)
   global: um (?i) no regex inteiro tornava [A-ZÀ-Ö] insensivel a
   caixa, derrubando a exigencia de inicial maiuscula do nome e
   deixando [^\n:;,.]{0,20} guloso recuar ate' o meio de uma palavra
   qualquer (achado durante o TDD desta task).
 ALTERACAO 0.2.1: correcao de revisao — CPF/PIS real colado a outro
   numero por um unico separador ("99 529.982.247-25") vazava sem
   token. RE_11DIGITOS aceita separador de 1 char em qualquer
   agrupamento, entao a janela de 11 digitos podia comecar 1 ou mais
   digitos antes do numero real, falhar no DV e ser descartada — um
   finditer comum ja tinha avançado o cursor para alem do inicio do
   CPF verdadeiro e nunca mais o testava. _cpf_pis_spans agora varre
   manualmente digito a digito: quando uma janela falha (DV ou limite
   de palavra no fim), a proxima tentativa comeca 1 posicao depois,
   nao no fim da janela que falhou.
 ALTERACAO 0.2.0: identificadores e contatos por regex viram
   token. CPF e PIS reconhecidos pelo digito verificador (mesmo
   valor, com ou sem pontuacao, cai no mesmo token); CNPJ e' so'
   reconhecido para ficar de fora (entra na lista de exclusao,
   nunca vira token); CTPS/RG/titulo de eleitor/conta bancaria
   sao contextuais (a palavra-chave fica, so' o numero e'
   trocado); e-mail, telefone, endereco e CEP completam o
   conjunto. pseudonimizar(texto, mapa) nesta versao cobre so'
   identificadores — a Task 4 acrescenta os nomes por cima,
   reaproveitando _spans_de_identificadores como uma das fontes
   de spans.
 ALTERACAO 0.1.0: versao inicial. Extrai pessoas fisicas das
   partes da capa (excluindo advogados e pessoas juridicas).
   Mapeia papel para prefixo de token (Reclamante, Reclamado,
   Terceiro). Constrói mapa de pseudonimos com valores normalizados.
==============================================================
"""
from __future__ import annotations
import copy
import re
import unicodedata
from functools import lru_cache
from itertools import permutations
from .lexico import PRENOMES as PRENOMES_DO_LEXICO
from .lexico import SOBRENOMES as SOBRENOMES_DO_LEXICO
from .lexico import frequencia_de_prenome, frequencia_de_sobrenome
from . import incertos
from . import nivel as nivel_mod
from .mapa import normalizar, token_para

VERSAO = "0.5.35"

# A versao da descoberta de nomes (etapa 2 da descoberta sem a caixa, 05/10/2026): entra na impressao do dossie
# (nivel.impressao, descoberta=); muda-la faz todo dossie montado antes aparecer "a preparar de novo" pelo
# mecanismo do dossie desatualizado, sem OCR e sem bloquear a copia que esta' na Pasta do Claude.
# "3" (0.5.34, decisao do juiz de 05/10/2026): refazer os dossies montados com o documento partido em claro.
VERSAO_DESCOBERTA_DE_NOMES = "3"

# Sufixos societarios da spec (secao 4.1). Na duvida — sem CNPJ e sem
# sufixo — trata como pessoa fisica: errar para o lado da protecao.
# 0.5.34: a quebra de linha da extracao do PDF (com espacos e CR-LF em volta) depois do ponto ou do hifen de um
# documento ou do hifen de um telefone ("ddd.ddd.ddd-" no fim da linha e o resto na seguinte)
_QUEBRA = r"[ \t]*\r?\n[ \t]*"
_RE_QUEBRA = re.compile(_QUEBRA)
RE_CNPJ = re.compile(r"\b\d{2}(?:\.(?:" + _QUEBRA + r")?)?\d{3}(?:\.(?:" + _QUEBRA + r")?)?\d{3}\s*/\s*\d{4}"
                     r"(?:-(?:" + _QUEBRA + r")?)?\d{2}\b")
# 0.5.0: "S A" com espaco, no fim do nome ("ALFA TELECOM S A"): a capa grafa
# assim, e a empresa entrava como pessoa (a 1a palavra dela virava prenome).
RE_SUFIXO_PJ = re.compile(
    r"(?i)(?:\bltda\.?\b|\bs\s*[./]\s*a\.?(?:\b|$)|\bs\.a\.(?:\b|$)|\bs\s+a\.?\s*$|"
    r"\beireli\b|\bepp\b|\bme\b\s*$|&\s*cia\.?\b)")
# Denominacao institucional no nome: pessoa juridica mesmo SEM sufixo
# societario (a capa do PJe quebra nome longo em duas linhas e o "LTDA"
# pode ficar na segunda — caso de 24/09/2026; e orgaos, fundacoes,
# cooperativas e condominios nao tem sufixo). Palavras que nao compoem
# nome de pessoa natural — "Bancos" (sobrenome) nao casa em \bbanco\b.
# 0.5.0: entes publicos e imoveis que a descoberta de testemunhas tomou
# por pessoa no acervo ("Estado do ...", condominios) ou que faltavam
# (uniao, distrito federal, fazenda publica, tribunal, edificio...). Na capa
# (eh_pessoa_fisica), as acrescentadas na 0.5.0 so' contam quando ABREM o
# nome: "FULANA DA JUSTICA BELTRANA" e' gente; as de antes valem em qualquer
# posicao (o "LTDA" pode ter ficado na 2a linha).
_PJ_EM_QUALQUER_POSICAO = (
    r"\b(?:sociedade|cooperativa|associa[cç][aã]o|funda[cç][aã]o|"
    r"instituto|banco|munic[ií]pio|prefeitura|companhia|empresa|com[eé]rcio|"
    r"ind[uú]stria|servi[cç]os|neg[oó]cios|solu[cç][oõ]es|transportes|"
    r"constru[cç][oõ]es|condom[ií]nio|sindicato|hospital|cons[oó]rcio|"
    r"universidade|faculdade|autarquia|secretaria|minist[eé]rio)\b|"
    r"\bcia\.?(?:\s|$)|\bcaixa econ[oô]mica\b|\bmassa falida\b|"
    r"\bestado d[oea]s?\b|\buni[aã]o federal\b|recupera[cç][aã]o judicial")
_PJ_QUANDO_ABRE = (
    r"\b(?:uni[aã]o|rep[uú]blica|procuradoria|defensoria|tribunal|justi[cç]a|"
    r"conselho|seccional|edif[ií]cio|residencial|shopping)\b|\bdistrito federal\b|"
    r"\bfazenda (?:p[uú]blica|nacional|estadual|municipal)\b|"
    r"\bgoverno d[oe]\b|\bordem dos advogados\b")
RE_PJ_INSTITUCIONAL = re.compile(r"(?i)(?:" + _PJ_EM_QUALQUER_POSICAO + "|" + _PJ_QUANDO_ABRE + ")")
_RE_PJ_EM_QUALQUER_POSICAO = re.compile(r"(?i)(?:" + _PJ_EM_QUALQUER_POSICAO + ")")
_RE_PJ_QUANDO_ABRE = re.compile(r"(?i)(?:" + _PJ_QUANDO_ABRE + ")")

def eh_pessoa_fisica(nome: str) -> bool:
    nome = (nome or "").strip()
    if RE_CNPJ.search(nome) or RE_SUFIXO_PJ.search(nome) or _RE_PJ_EM_QUALQUER_POSICAO.search(nome):
        return False
    partes = nome.split()
    while partes and normalizar(partes[0]) in _PREFIXOS_DESCARTAVEIS:
        partes = partes[1:]
    return not _RE_PJ_QUANDO_ABRE.match(" ".join(partes))

def prefixo_do_papel(papel: str | None) -> str:
    p = normalizar(papel or "")
    if p.startswith(("reclamante", "autor", "exequente", "requerente")):
        return "RECLAMANTE"
    if p.startswith(("reclamad", "reu", "executad", "requerid")) or p == "re":
        return "RECLAMADO"
    # Perito da capa ganha o mesmo prefixo do perito descoberto no laudo:
    # token_para deduplica pelo valor, entao os dois viram um so' tóken.
    if p.startswith("perit"):
        return "PERITO"
    return "TERCEIRO"

# Indices gravados ate' 27/09/2026 podem trazer o marcador da capa do PJe
# colado ao nome da ultima parte (em geral o perito) — ver
# parser_pje.sem_marcador_da_capa. Sujo, o nome nunca casava no texto.
RE_MARCADOR_CAPA = re.compile(r"\s*\bPAGINA_CAPA_PROCESSO_PJE\b\s*")
# Caracteres invisiveis (0.5.0; 0.5.1): a extracao do PDF deixa entre as
# palavras os de largura zero ("PRENOME<U+200B> <U+200B>SOBRENOME", ou so'
# "<U+200B><U+200B>" no lugar do espaco), os controles de direcao em volta
# de cada palavra ("<U+202D>PRENOME<U+202C> <U+202D>SOBRENOME<U+202C>", ou
# sem o espaco) e o hifen condicional dentro da palavra — com eles a janela
# do nome nao casava. RE_INVISIVEIS e' a classe inteira; os que separam
# palavras sao o U+200B e os controles de direcao (no acervo, entre duas
# letras sem espaco, 1825 separavam palavras e nenhum ficava dentro de uma).
_INVISIVEIS = "\u00ad\u061c\u180e\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff"
_INVISIVEIS_QUE_SEPARAM = "\u061c\u200b\u200e\u200f\u202a-\u202e\u2066-\u2069"
RE_INVISIVEIS = re.compile("[" + _INVISIVEIS + "]")
# a letra antes pode terminar em marca combinante (o texto ainda em NFD)
_DEPOIS_DE_LETRA = r"(?<=[\w\u0300-\u036f])"
_RE_SEPARADOR_INVISIVEL = re.compile(
    _DEPOIS_DE_LETRA + "[" + _INVISIVEIS + "]*[" + _INVISIVEIS_QUE_SEPARAM + "][" + _INVISIVEIS + r"]*(?=\w)")
_RE_INVISIVEIS_ENTRE_LETRAS = re.compile(_DEPOIS_DE_LETRA + "[" + _INVISIVEIS + r"]+(?=\w)")


def limpar_invisiveis(texto: str) -> str:
    """O texto sem caracteres invisiveis: a sequencia deles entre duas
    letras que tem U+200B ou controle de direcao vira UM espaco (era a
    fronteira entre as palavras: "Fulana<U+200B><U+200B>disse" -> "Fulana
    disse", nunca "Fulanadisse"); os outros saem (o hifen condicional e os
    que juntam ficam dentro da palavra: "FULA<U+00AD>NA" -> "FULANA"). A
    mesma funcao no montador, na troca e na guarda (0.5.1)."""
    return RE_INVISIVEIS.sub("", _RE_SEPARADOR_INVISIVEL.sub(" ", texto))


def invisiveis_como_espaco(texto: str) -> str:
    """Para a guarda (so' fortalece): TODA sequencia de invisiveis entre
    duas letras vira espaco, e o resto sai — a copia em que o nome partido
    por um invisivel qualquer aparece com as palavras separadas."""
    return RE_INVISIVEIS.sub("", _RE_INVISIVEIS_ENTRE_LETRAS.sub(" ", texto))


def texto_limpo(texto: str) -> str:
    """O texto em NFC e sem caracteres invisiveis (limpar_invisiveis): a
    entrada da troca, do rotulo, da descoberta e da capa, e o texto das
    paginas no montador (0.5.0; 0.5.1)."""
    return unicodedata.normalize("NFC", limpar_invisiveis(unicodedata.normalize("NFC", texto)))

def construir_mapa(indice: dict, mapa: dict) -> None:
    """Partes pessoas fisicas da capa entram no mapa. Advogados (dado
    publico de registro profissional) e pessoas juridicas ficam de fora
    por decisao da spec (secao 2) — salvo no processo sigiloso, em que a
    pessoa juridica entra com categoria 'pj' (0.5.13)."""
    if not nivel_mod.nomes_em_codigo(nivel_mod.do_mapa(mapa)):
        return                      # publico: nenhuma pessoa entra no mapa
    for parte in (indice.get("processo") or {}).get("partes", []):
        nome = texto_limpo(RE_MARCADOR_CAPA.sub(" ", parte.get("nome") or "")).strip()
        if not nome:
            continue
        if not eh_pessoa_fisica(nome):
            if nivel_mod.empresas_em_codigo(nivel_mod.do_mapa(mapa)):
                # sigiloso: a pessoa juridica da capa tambem vira codigo (categoria propria, nunca 'pessoa')
                token_para(mapa, prefixo_do_papel(parte.get("papel")), "pj", nome, papel=parte.get("papel"))
            continue
        if _nome_plausivel(nome) is None:
            # So' entra no mapa o que _spans_de_nomes pode trocar no texto
            # (2+ palavras, nenhuma de _NUNCA_NOME). Um tóken sem chance
            # de casar deixava mapa e dossie inconsistentes: o nome ficava
            # em claro e o filtro de saida bloqueava a reversao da minuta
            # por "valor do mapa em claro" (caso de producao, 24/09/2026).
            # Fica registrado — sem o nome — para auditoria.
            mapa.setdefault("nao_pseudonimizadas", []).append({
                "papel": parte.get("papel"),
                "motivo": ("nome com uma palavra só" if len(nome.split()) < 2
                           else "nome com palavra que nunca compõe nome de pessoa")})
            continue
        token_para(mapa, prefixo_do_papel(parte.get("papel")), "pessoa",
                   nome, papel=parte.get("papel"))

# ---------------------------------------------------------------
# Identificadores e contatos (secao 4.1 da spec): CPF/PIS validados
# por digito verificador; CNPJ so' reconhecido para ficar de fora;
# CTPS/RG/titulo/conta sao contextuais; e-mail, telefone, endereco
# e CEP completam o conjunto.
# ---------------------------------------------------------------

def _cpf_valido(d: str) -> bool:
    if len(d) != 11 or d == d[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        dv = (soma * 10) % 11 % 10
        if dv != int(d[n]):
            return False
    return True

def _pis_valido(d: str) -> bool:
    if len(d) != 11 or d == d[0] * 11:
        return False
    pesos = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    resto = sum(int(x) * p for x, p in zip(d[:10], pesos)) % 11
    dv = 0 if 11 - resto in (10, 11) else 11 - resto
    return dv == int(d[10])

# Onze digitos com separadores opcionais (ponto, hifen ou espaco) entre
# eles, em qualquer agrupamento — CPF e PIS sao escritos com agrupamentos
# diferentes ("529.982.247-25" vs. "120.5741.316-2") e o codigo, nao a
# regex, decide qual e' pelo digito verificador. Sem \b nas pontas: os
# limites de palavra sao checados manualmente por _cpf_pis_spans, que
# tambem faz a retentativa quando uma janela falha no DV (ver docstring).
RE_11DIGITOS = re.compile(r"\d(?:[.\-\s]?\d){10}")
# 0.5.36: o numero de processo (CNJ, NNNNNNN-DD.AAAA.J.TR.OOOO) e' publico e nunca vira codigo. A cauda
# "AAAA.J.TR.OOOO" tem 11 digitos com um separador entre os grupos — uma janela de RE_11DIGITOS entre limites de
# palavra — e, conforme o ano, o tribunal e a vara, passa no digito verificador do PIS ou do CPF ("2025.5.04.9999"
# e' PIS valido): o dossie que citava outro processo saia com o numero partido ("0090006-85.[[PIS_1]]"). A janela
# que sobrepoe um CNJ completo e' pulada em _cpf_pis_spans (o varredor dos Entendimentos tambem a reusa) e o CNJ
# entra nos tomados de _spans_de_identificadores, para nenhum outro identificador nascer dentro dele.
RE_CNJ = re.compile(r"(?<!\d)\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}(?!\d)")


def _spans_de_cnj(texto: str) -> list[tuple[int, int]]:
    """[(ini, fim)] de cada numero de processo completo no texto."""
    return [m.span() for m in RE_CNJ.finditer(texto)]
# 0.5.34: o CPF e o PIS partidos pela quebra de linha depois do ponto ou do hifen ("529.982.247-" no fim da linha e
# "25" na seguinte: dois caracteres entre os digitos, que a janela acima nao aceita). So' na grafia usual de CPF
# ("ddd.ddd.ddd-dd") ou de PIS ("ddd.ddddd.dd-d", "ddd.dddd.ddd-d"), tirada a quebra: o numero que fecha a frase com
# ponto e o que abre a linha seguinte ("5299." e "8224725") sao dois numeros, mesmo com o digito verificador certo.
RE_11DIGITOS_PARTIDOS = re.compile(r"\d(?:[.\-]?(?:" + _QUEBRA + r")?\d){10}")
RE_GRAFIA_DE_DOCUMENTO = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}|\d{3}\.\d{5}\.\d{2}-\d|\d{3}\.\d{4}\.\d{3}-\d")

def _limite_de_palavra(texto: str, i: int) -> bool:
    """Equivalente a \\b do regex, mas utilizavel em qualquer indice
    arbitrario — inicio/fim de string ou transicao entre um caractere de
    palavra (\\w) e um que nao e'."""
    def _w(c: str) -> bool:
        return c.isalnum() or c == "_"
    antes = texto[i - 1] if i > 0 else ""
    depois = texto[i] if i < len(texto) else ""
    return _w(antes) != _w(depois)

def _documento_partido(texto: str, i: int) -> re.Match | None:
    """0.5.34: a janela de 11 digitos com a quebra de linha depois do ponto ou do hifen, so' quando, tirada a
    quebra, e' a grafia usual de CPF ou de PIS (RE_GRAFIA_DE_DOCUMENTO)."""
    m = RE_11DIGITOS_PARTIDOS.match(texto, i)
    if m and "\n" in m.group() and RE_GRAFIA_DE_DOCUMENTO.fullmatch(re.sub(r"\s", "", m.group())):
        return m
    return None


def _cpf_pis_spans(texto: str) -> list[tuple[int, int, str, str, str]]:
    """Varre janelas de 11 digitos e devolve as que sao CPF ou PIS validos:
    [(ini, fim, prefixo, categoria, digitos), ...].

    RE_11DIGITOS aceita separador de 1 caractere entre digitos em qualquer
    agrupamento, entao um numero curto colado a um CPF/PIS real por um
    unico separador (ex.: "99 529.982.247-25") tambem forma uma janela de
    11 digitos — que falha no DV e e' descartada. Um finditer comum
    perderia o CPF real ali: ele avancaria o cursor ate o fim da janela
    falha, que ja consumiu o comeco do CPF verdadeiro, e nunca mais o
    tentaria a partir do proprio inicio dele. Por isso a varredura aqui e'
    manual: quando uma janela falha (no DV ou no limite de palavra no
    fim), a proxima tentativa comeca 1 posicao depois — nao no fim da
    janela que falhou — para sempre dar ao numero real a chance de ser
    testado a partir do seu proprio primeiro digito.

    0.5.36: a janela que sobrepoe um numero de processo completo (RE_CNJ)
    e' pulada — a cauda do CNJ passa no DV do PIS ou do CPF por acaso, e
    processo e' publico."""
    achados: list[tuple[int, int, str, str, str]] = []
    cnjs = _spans_de_cnj(texto)
    i, n = 0, len(texto)
    while i < n:
        if texto[i].isdigit() and _limite_de_palavra(texto, i):
            achado = None
            for m in (RE_11DIGITOS.match(texto, i), _documento_partido(texto, i)):
                if not (m and _limite_de_palavra(texto, m.end()) and _livre(i, m.end(), cnjs)):
                    continue
                digitos = re.sub(r"\D", "", m.group())
                if _cpf_valido(digitos):
                    achado = (i, m.end(), "CPF", "cpf", digitos)
                elif _pis_valido(digitos):
                    achado = (i, m.end(), "PIS", "pis", digitos)
                if achado:
                    break
            if achado:
                achados.append(achado)
                i = achado[1]
                continue
        i += 1
    return achados

RE_CTPS = re.compile(r"(?i)\bCTPS\s*(?:n[ºo°.]*\s*)?"
                     r"(\d[\d.]{2,8}(?:\s*[,/-]?\s*s[ée]rie\s*[\d.]{2,6})?)")
RE_RG = re.compile(r"(?i)\b(?:RG|carteira de identidade|identidade)\s*"
                   r"(?:n[ºo°.]*\s*)?(\d[\d.]{4,12}-?[\dXx]?)")
RE_TITULO = re.compile(r"(?i)t[íi]tulo\s+(?:de\s+)?eleitor(?:al)?\s*"
                       r"(?:n[ºo°.]*\s*)?(\d[\d.\s]{9,15}\d)")
RE_CONTA = re.compile(r"(?i)(?:\bag[êe]ncia\s*[\d.-]{2,8}\s*[,;/]?\s*)?"
                      r"\b(?:conta(?:\s+(?:corrente|poupan[çc]a|sal[áa]rio))?|c/c)\s*"
                      r"(?:n[ºo°.]*\s*)?([\d][\d.\sXx-]{2,14}\d)")
RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
RE_TEL = re.compile(r"(?i)(?:(?:\b(?:tel(?:efone)?|fone|celular|cel|whatsapp|contato)\b"
                    r"[.:\s]*)?(\(\d{2}\)\s*9?\d{4}(?:-" + _QUEBRA + r"|[-.\s])?\d{4})"
                    r"|\b(?:tel(?:efone)?|fone|celular|cel|whatsapp)\b[.:\s]*"
                    r"(9?\d{4}(?:-" + _QUEBRA + r"|[-.\s])?\d{4}))")
# 0.5.2: o telefone na conversa de aplicativo de mensagens (so' com conversa=True), nesta ordem — o mais longo
# primeiro (o "51 99999-1234" inteiro, antes do "99999-1234" dentro dele). Entre os grupos, espaco, ponto ou hifen
# (com ou sem espacos); no fim, o ponto final da frase nao impede (so' o ponto seguido de digito: "1234-5678.90")
# 0.5.34: depois do hifen, tambem a quebra de linha com espacos e CR-LF em volta
_SEP_TEL = r"(?:\s?-(?:" + _QUEBRA + r"|\s?)|[\s.])"
# revisao final (02/10/2026): o "/" e o "-" so' impedem junto de um digito (o "1234/2023-1234", o "1234-5678-9"); o
# parentese antes e a palavra antes do "/" ou do "-" nao ("(99999-1234)", "fone/99999-1234"); a barra entre dois
# telefones e' partida antes (_busca_do_telefone)
_FIM_TEL = r"(?!\d|[/.,-]\d)"
_ANTES_TEL = r"(?<!\d)(?<!\d[/.,-])"
# re-revisao (03/10/2026): o segundo numero so' com o final, depois da barra ("99999-1234/5678": o mesmo comeco; tambem
# "99999-1234/5678/9012") — todos num codigo so'; sem o comeco de celular (9) ou de fixo (2 a 5), nao ("1234-5678/2023").
# Re-revisao 2: tambem depois da virgula ("99999-1234,5678"); o final de 2 digitos ("3333-1234,56", o valor) nao
RE_TEL_COM_OUTRO_FINAL = re.compile(
    _ANTES_TEL + r"(?<![+])(?:\+\s?55[\s.-]?)?(?:\(?\d{2}\)?[\s.-]?)?(?:9[\s.]?\d{4}|[2-5]\d{3})" + _SEP_TEL
    + r"\d{4}(?:\s?[/,]\s?\d{4})+" + _FIM_TEL)
RE_TEL_CONVERSA = (
    RE_TEL_COM_OUTRO_FINAL,                                                                     # 99999-1234/5678
    re.compile(r"(?<![\d+])\+\s?55[\s.-]?\(?\d{2}\)?[\s.-]?(?:9[\s.]?)?\d{4}" + _SEP_TEL + r"?\d{4}(?!\d)"),   # +55 51 99999-1234
    re.compile(r"(?<![\d+(])(?<!\d[.,/-])55\d{10,11}(?!\d)"),                                       # 5551999991234
    re.compile(r"(?<![\d+])\(\d{2}\)[\s.-]?(?:9[\s.]?)?\d{4}" + _SEP_TEL + r"?\d{4}(?!\d)"),               # (51) 99999-1234
    re.compile(_ANTES_TEL + r"(?<![+])\d{2}[\s.-]?9[\s.]?\d{4}" + _SEP_TEL + r"?\d{4}" + _FIM_TEL),          # 51 99999-1234
    re.compile(_ANTES_TEL + r"9\d{4}" + _SEP_TEL + r"\d{4}" + _FIM_TEL),                                 # 99999-1234
    re.compile(_ANTES_TEL + r"\d{4}\s?-\s?\d{4}" + _FIM_TEL),                                           # 3333-1234
    re.compile(_ANTES_TEL + r"(?:\(?\d{2}\)?[\s.]?)?[2-5]\d{3}[\s.]\d{4}(?![\d/,-]|\.\d)"),                   # 51 3333 1234
    re.compile(r"(?<![\d+])(?:\d{2})?9[6-9]\d{7}(?!\d)"),                                           # 999991234
    re.compile(r"(?<![\d\w])\+(?!55)\d{1,3}[\s().-]?(?:\d[\s().-]?){7,12}\d(?!\d)"),                    # +1 415 555 0100
)
# o celular com o DDD (e o +55): antes do PIS e do CPF (o "51 99999-1234" de digito verificador valido de PIS); o
# com o outro final, primeiro (o "(51) 99999-1234/5678" inteiro)
RE_TEL_CONVERSA_COM_DDD = (RE_TEL_CONVERSA[0], RE_TEL_CONVERSA[1], RE_TEL_CONVERSA[3], RE_TEL_CONVERSA[4])
RE_GRAFIA_CPF_OU_PIS = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}|\d{3}\.\d{5}\.\d{2}-\d")
RE_DOCUMENTO_ANTES = re.compile(r"(?i)\b(?:cpf|pis|nit|pasep)\b\W{0,3}(?:n[ºo°.]*\s*)?$")
# o par de anos — tambem com o outro final depois da barra ou da virgula ("2022-2023/2024", re-revisao 2), que
# RE_TEL_COM_OUTRO_FINAL faria um telefone (nas duas passadas)
# (0.5.34: o mesmo separador do telefone, com a quebra depois do hifen — o "2019-\n2020/2021" partido continua excluido)
RE_PAR_DE_ANOS = re.compile(r"(?:19|20)\d{2}" + _SEP_TEL + r"(?:19|20)\d{2}(?:\s?[/,]\s?(?:19|20)\d{2})*")
# a letra colada a um digito, lida como digito so' na busca do telefone (a leitura troca 1 por l ou I e 0 por O) — so'
# quando ela nao encosta em outra letra (revisao final: "contato99999-1234", "Rafael99999-1234" e "99999-1234ok"
# ganhavam um digito e escapavam); a barra vertical so' entre digitos ou hifen (a da tabela, "|99999-1234|", nao)
_LETRA = r"[^\W\d_]"
RE_SOSIA_UM_TEL = re.compile(r"(?<=\d)[lI](?!" + _LETRA + r")|(?<!" + _LETRA + r")[lI](?=\d)"
                             r"|(?<=[\d-])\|(?=\d)|(?<=\d)\|(?=[\d-])")
RE_SOSIA_ZERO_TEL = re.compile(r"(?<=\d)[Oo](?!" + _LETRA + r")|(?<!" + _LETRA + r")[Oo](?=\d)")
# a barra (ou a virgula, re-revisao de 03/10/2026) entre dois numeros com forma de telefone ("99999-1234/98888-5678",
# "(51) 99999-1234/98888-5678", "99999-1234,98888-5678"): partida na busca (a data "dd/mm/aaaa", o CNPJ e o valor
# "1.234,56" nao tem 8 digitos dos dois lados)
_FORMA_DE_TELEFONE = r"(?:\(?\d{2}\)?[\s.-]?)?(?:9[\s.]?)?\d{4}[\s.-]?\d{4}"
RE_BARRA_ENTRE_TELEFONES = re.compile(r"(?<!\d)" + _FORMA_DE_TELEFONE + r"\s?([/,])\s?(?=" + _FORMA_DE_TELEFONE
                                      + r"(?!\d))")
# o codigo de rastreio dos Correios (duas letras, 9 digitos, duas letras): fora da busca do telefone, agora que o
# corrido de 9 digitos aceita a letra colada ("contato999991234", "999991234ok"; re-revisao de 03/10/2026). Re-revisao
# 2: so' na forma dos Correios — as duas letras em MAIUSCULAS dos dois lados e o digito verificador do S10 certo
# (_rastreio_dos_correios); o telefone entre duas letras ("oi999991234ok", "OK999991234OK") vira codigo
RE_RASTREIO = re.compile(r"(?<!" + _LETRA + r")[A-Z]{2}(\d{8})(\d)[A-Z]{2}(?!" + _LETRA + r")")
_PESOS_DO_S10 = (8, 6, 4, 2, 3, 5, 9, 7)


def _rastreio_dos_correios(m: re.Match) -> bool:
    """O digito verificador do codigo de rastreio (UPU S10, o dos Correios): a soma dos 8 digitos pelos pesos 8 6 4 2
    3 5 9 7; o digito e' 11 menos o resto por 11 (10 vira 0, 11 vira 5) — "AB996543218BR" e' rastreio,
    "AB999991234CD" nao (e' telefone entre letras)."""
    dv = 11 - sum(int(c) * p for c, p in zip(m.group(1), _PESOS_DO_S10)) % 11
    return int(m.group(2)) == {10: 0, 11: 5}.get(dv, dv)


# A cauda pos-virgula fica limitada a UM segmento curto (numero do
# imovel, em geral) — "[^\n]{0,80}" sem excluir virgula/ponto-e-virgula
# engolia tudo o que vinha depois (nome de terceiro, CPF, CEP) num unico
# span de endereco, furando a auditoria de variantes e a estabilidade do
# token desses outros dados (achado de revisao da Task 4).
# 0.5.0: "Rua do" no fim da linha e o logradouro na seguinte (a extracao do
# PDF quebra a linha ali) — antes nada casava, e o logradouro ficava em
# claro. O numero sozinho numa terceira linha continua fora (residual).
RE_ENDERECO = re.compile(r"(?im)\b(?:Rua|Avenida|Av\.|Travessa|Rodovia|Alameda|"
                         r"Estrada|Beco)\s+(?:d[aeo]s?[ \t]*\n[ \t]*)?[^\n,;]{3,60}"
                         r"(?:[,;]\s*(?:n[ºo°.]*\s*)?[^\n,;]{0,40})?")
RE_CEP = re.compile(r"(?i)\bCEP[:.\s]*\d{2}\.?\d{3}-?\d{3}\b")

def _livre(ini: int, fim: int, tomados: list[tuple[int, int]]) -> bool:
    """True se [ini, fim) nao sobrepoe nenhum span ja' tomado."""
    return all(fim <= t0 or ini >= t1 for t0, t1 in tomados)

def _digitos_do_telefone(texto: str) -> str:
    """Os digitos do telefone, sem o 55 do pais (com 12 ou 13 digitos)."""
    d = re.sub(r"\D", "", texto or "")
    return d[2:] if len(d) in (12, 13) and d.startswith("55") else d


def _busca_do_telefone(texto: str) -> str:
    """O texto com a letra colada a um digito (l, I, | por 1; O, o por 0) trocada pelo digito, quando ela nao
    encosta em outra letra, e a barra (ou a virgula) entre dois telefones trocada por ";" — do mesmo tamanho: a
    posicao do trecho e' a mesma no texto, e o valor guardado e' o trecho como estava."""
    for _ in range(2):
        texto = RE_SOSIA_UM_TEL.sub("1", RE_SOSIA_ZERO_TEL.sub("0", texto))
    barras = [m.start(1) for m in RE_BARRA_ENTRE_TELEFONES.finditer(texto)]
    if barras:
        letras = list(texto)
        for i in barras:
            letras[i] = ";"
        texto = "".join(letras)
    return texto


def _telefone_com_ddd_antes_do_documento(texto: str, busca: str, inicio: int, fim: int) -> bool:
    """O celular com o DDD (ou o +55) entra antes do PIS e do CPF, salvo na grafia de CPF ou de PIS
    ("ddd.ddd.ddd-dd", "ddd.ddddd.dd-d") ou logo depois de "CPF", "PIS", "NIT" ou "PASEP"."""
    return not (RE_GRAFIA_CPF_OU_PIS.search(busca[inicio:fim]) or RE_DOCUMENTO_ANTES.search(texto[max(0, inicio - 20):inicio]))


def _sem_a_quebra(trecho: str) -> str:
    """0.5.34: o valor do CNPJ e do telefone partidos vai ao mapa sem a quebra de linha — a reversao devolve o numero
    numa linha so', e o mesmo numero inteiro, visto depois, cai no mesmo codigo."""
    return _RE_QUEBRA.sub("", trecho)


def _token_do_telefone(mapa: dict, trecho: str) -> str:
    """0.5.2: o codigo do telefone pelos DIGITOS — o mesmo numero com e sem o +55, com e sem o DDD (8+ digitos no
    fim), tem o codigo que o mapa ja' tem; senao, um novo (o valor e' o trecho como estava, para a reversao)."""
    d = _digitos_do_telefone(trecho)
    for tok, info in mapa["tokens"].items():
        if not isinstance(info, dict) or info.get("categoria") != "telefone":
            continue
        v = _digitos_do_telefone(str(info.get("valor") or ""))
        if v == d or (min(len(v), len(d)) >= 8 and (v.endswith(d) or d.endswith(v))):
            return tok
    return token_para(mapa, "TEL", "telefone", _sem_a_quebra(trecho))


def _token_do_cnpj(mapa: dict, trecho: str) -> str:
    """0.5.34: o codigo do CNPJ pelos DIGITOS — o mesmo numero partido pela quebra de linha tem o codigo que o mapa
    ja' tem; senao, um novo (o valor e' o trecho como estava, para a reversao)."""
    d = re.sub(r"\D", "", trecho)
    for tok, info in mapa["tokens"].items():
        if isinstance(info, dict) and info.get("categoria") == "cnpj" \
                and re.sub(r"\D", "", str(info.get("valor") or "")) == d:
            return tok
    return token_para(mapa, "CNPJ", "cnpj", _sem_a_quebra(trecho))


def _spans_de_identificadores(texto: str, mapa: dict, conversa: bool = False) -> list[tuple[int, int, str]]:
    """Varre identificadores/contatos e devolve [(ini, fim, token), ...].
    Nao reordena nem resolve sobreposicao — quem monta o texto final faz
    isso (aqui e' pseudonimizar; a Task 4 soma outras fontes de span).
    `conversa` (0.5.2): o texto de conversa de aplicativo de mensagens —
    todo numero com forma de telefone vira codigo (RE_TEL_CONVERSA)."""
    spans: list[tuple[int, int, str]] = []
    tomados: list[tuple[int, int]] = []
    busca = _busca_do_telefone(texto) if conversa else texto

    # 1) CNPJ so' entra na exclusao — pessoa juridica nao e' dado protegido. Na conversa, o codigo de rastreio
    #    tambem (o corrido de 9 digitos aceita a letra colada). 0.5.36: o numero de processo completo tambem
    #    (publico; a cauda dele passa no DV do PIS ou do CPF por acaso).
    tomados.extend(_spans_de_cnj(texto))
    for m in RE_CNPJ.finditer(texto):
        tomados.append(m.span())
    for m in (RE_RASTREIO.finditer(texto) if conversa else ()):
        if _rastreio_dos_correios(m):
            tomados.append(m.span())

    # 2) Endereco/CEP primeiro, para que "nº 123" caia dentro do span do
    #    endereco em vez de ser lido depois como outro numero solto.
    for regex in (RE_ENDERECO, RE_CEP):
        for m in regex.finditer(texto):
            ini, fim = m.span()
            if _livre(ini, fim, tomados):
                tok = token_para(mapa, "ENDERECO", "endereco", texto[ini:fim])
                spans.append((ini, fim, tok))
                tomados.append((ini, fim))

    # 0.5.2: na conversa, o celular com o DDD e o +55 antes do PIS e do CPF (o "+55" no mesmo codigo); o par de anos
    # com o outro final ("2022-2023/2024") nao
    for regex in (RE_TEL_CONVERSA_COM_DDD if conversa else ()):
        for m in regex.finditer(busca):
            ini, fim = m.span()
            if RE_PAR_DE_ANOS.fullmatch(m.group()):
                continue
            if _livre(ini, fim, tomados) and _telefone_com_ddd_antes_do_documento(texto, busca, ini, fim):
                spans.append((ini, fim, _token_do_telefone(mapa, texto[ini:fim])))
                tomados.append((ini, fim))

    # 3) CPF/PIS: mesmos 11 digitos, com ou sem pontuacao, mesmo token —
    #    por isso o valor gravado no mapa e' a string de digitos, nao o
    #    trecho pontuado. _cpf_pis_spans ja' cuida de retentar 1 posicao
    #    adiante quando uma janela colada a outro numero falha no DV.
    for ini, fim, prefixo, categoria, digitos in _cpf_pis_spans(texto):
        if not _livre(ini, fim, tomados):
            continue
        tok = token_para(mapa, prefixo, categoria, digitos)
        spans.append((ini, fim, tok))
        tomados.append((ini, fim))

    # 4) Contextuais: a palavra-chave (CTPS, RG, titulo de eleitor, conta)
    #    fica no texto; so' o numero (grupo 1) vira token.
    for regex, prefixo, categoria in (
        (RE_CTPS, "CTPS", "ctps"),
        (RE_RG, "RG", "rg"),
        (RE_TITULO, "TITULO_ELEITOR", "titulo_eleitor"),
        (RE_CONTA, "CONTA", "conta"),
    ):
        for m in regex.finditer(texto):
            if not m.group(1):
                continue
            ini, fim = m.span(1)
            if not _livre(ini, fim, tomados):
                continue
            tok = token_para(mapa, prefixo, categoria, texto[ini:fim])
            spans.append((ini, fim, tok))
            tomados.append((ini, fim))

    # 5) E-mail e telefone.
    for m in RE_EMAIL.finditer(texto):
        ini, fim = m.span()
        if _livre(ini, fim, tomados):
            tok = token_para(mapa, "EMAIL", "email", texto[ini:fim])
            spans.append((ini, fim, tok))
            tomados.append((ini, fim))

    # 0.5.2: na conversa, todo numero com forma de telefone (o par de anos nao) — antes de RE_TEL, para o
    # "+55 (51) 99999-1234" sair inteiro
    # (a busca com as sosias e a barra partida; e o texto como esta', para o numero que a sosia estragaria)
    for regex in (RE_TEL_CONVERSA if conversa else ()):
        for versao in ((busca, texto) if busca != texto else (busca,)):
            for m in regex.finditer(versao):
                ini, fim = m.span()
                if RE_PAR_DE_ANOS.fullmatch(m.group()) or not _livre(ini, fim, tomados):
                    continue
                spans.append((ini, fim, _token_do_telefone(mapa, texto[ini:fim])))
                tomados.append((ini, fim))

    for m in RE_TEL.finditer(texto):
        grupo = 1 if m.group(1) else 2
        if not m.group(grupo):
            continue
        ini, fim = m.span(grupo)
        if not _livre(ini, fim, tomados):
            continue
        tok = (_token_do_telefone(mapa, texto[ini:fim]) if conversa
               else token_para(mapa, "TEL", "telefone", _sem_a_quebra(texto[ini:fim])))
        spans.append((ini, fim, tok))
        tomados.append((ini, fim))

    return spans

# ---------------------------------------------------------------
# Nomes (secao 4.2/7.2 da spec): tolerantes a variacao de caixa, acento
# e a 1 erro tipico de OCR por palavra; nome mais longo (mais palavras)
# vence sobre um mais curto que seja seu prefixo; primeiro nome isolado
# so' substitui quando inequivoco no mapa inteiro.
# ---------------------------------------------------------------

RE_PALAVRA = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")
CONECTIVOS = {"da", "de", "do", "das", "dos", "e"}

# Palavras que podem preceder um nome no texto e nao fazem parte dele:
# descartadas do INICIO do candidato ("DA SILVA MARIA..." -> "SILVA MARIA...").
# 0.5.0: os ordinais masculinos tambem ("SEGUNDO LUGAR" virou perito);
# "segundo" nao vai para _NUNCA_NOME porque tambem e' nome de gente
# ("Joao Segundo Silva" sairia do mapa e a guarda ficaria cega).
_PREFIXOS_DESCARTAVEIS = CONECTIVOS | {
    "sr", "sra", "dr", "dra", "primeira", "segunda", "terceira", "unica",
    "primeiro", "segundo", "terceiro",
    "rol", "a", "o", "as", "os", "um", "uma", "em", "no", "na", "que", "com",
    "por", "para", "ao", "aos"}
# 0.5.35 (ancora do socio): a qualidade do socio entre a ancora e o nome ("socia majoritaria Fulana", "socio
# retirante Fulano", "socio administrador Fulano") nunca e' nome — nenhuma esta' no ranking do IBGE. Entra em
# _NUNCA_NOME (nao abre nem compoe o nome) e em _PULAVEIS_ANTES_DO_NOME (o comeco depois dela continua livre).
_QUALIDADES_DO_SOCIO = frozenset({
    "majoritario", "majoritaria", "minoritario", "minoritaria", "administrador", "administradora", "gerente",
    "diretor", "diretora", "ostensivo", "ostensiva", "oculto", "oculta", "retirante", "retirantes",
    "remanescente", "remanescentes", "cotista", "quotista"})
# Palavras que nunca compoem nome de pessoa fisica (o que a RE_TESTEMUNHA
# captura de fato quando a palavra-chave "testemunha" aparece numa
# contestacao, e nao numa ata): sufixo/ramo de pessoa juridica, papel
# processual, cidade, juridiques. Conectivos NAO entram aqui: "Maria DE
# Lourdes" os tem no meio; eles so' sao rejeitados como INICIO de nome
# (_PREFIXOS_DESCARTAVEIS) e como primeiro nome isolado.
_NUNCA_NOME = {
    "nao", "sim", "banco", "bancos", "servicos", "ltda", "sa", "eireli",
    "epp", "me", "cia", "comercio", "industria", "negocios", "solucoes",
    "marketing", "financeira", "credito", "intermediadora", "informacoes",
    "cadastrais", "empresa", "empresas", "porto", "alegre",
    "reclamante", "reclamantes", "reclamada", "reclamadas", "reclamado",
    "reclamados", "autor", "autora", "reu", "re", "reus", "parte", "partes",
    "testemunha", "testemunhas", "depoimento", "depoente", "compromissada",
    "compromissado", "advertida", "advertido", "comprovada", "comprovado",
    "conforme", "juizo", "juiz", "juiza", "vara", "trabalho", "tribunal",
    "regional", "processo", "autos", "tomadora", "tomador", "prestadora",
    "limitacao", "liquidacao", "contrato", "clt", "cpc", "cf", "art",
    "artigo", "oab", "id", "audiencia", "ata", "sentenca", "decisao",
    # Pericia: o que vem depois de "perito" numa peticao ou laudo sem ser
    # o nome ("perito nomeado para avaliação de Adicional de
    # Insalubridade" virou [[PERITO_1]] em 27/09/2026).
    "adicional", "adicionais", "insalubridade", "periculosidade",
    "insalubre", "perigoso", "pericia", "pericial", "periciais", "perito",
    "perita", "peritos", "laudo", "nomeado", "nomeada", "avaliacao",
    "honorarios", "engenheiro", "engenheira", "engenharia", "medico",
    "medica", "medicina", "seguranca", "ocupacional", "para",
    "reclamatoria", "trabalhista", "acao", "epigrafe",
    # 0.5.0: o que a varredura do acervo (28/09/2026) achou virando PERITO_n
    # ou TESTEMUNHA_n depois de "perito"/"testemunha" — e, pela regra do
    # primeiro nome isolado, trocando a palavra comum em todo o dossie
    "equipamento", "equipamentos", "protecao", "individual", "nome", "completo",
    "trazida", "trazido", "pela", "pelo", "certificado", "certificados",
    "aprovacao", "manguito", "rotador", "quesito", "quesitos", "esclarecimento",
    "esclarecimentos", "assinatura", "assinaturas", "programa", "ajuizou",
    "inicio", "oficial", "calculo", "calculos", "planilha", "planilhas",
    "assistente", "assistentes", "judicial", "sindrome", "estado", "condominio",
    "tecnico", "tecnica", "tecnicos", "endereco", "apresenta", "ortopedista",
    "traumatologista",
    # e o que a remontagem do acervo com o corte (validacao da 0.5.0) achou
    # antes da palavra que corta: a assinatura do advogado ("ADVOGADO
    # FULANO ... OAB"), o fecho da peticao ("Nestes Termos Pede
    # Deferimento"), a lei ("Consolidacao das Leis do Trabalho")
    "advogado", "advogada", "advogados", "advogadas", "procurador", "procuradora",
    "nestes", "termos", "pede", "deferimento", "consolidacao", "leis",
    # a cabeca da tabela ("CONTADOR / CODIGO / CRC", "Nome / CPF"), o
    # orgao ("Perito Medico Federal do INSS"), o tratamento ("Vossa
    # Excelencia"), o marcador da pagina e do documento colado ao nome, o
    # custos legis que e' um imovel ("Matricula Imovel NNNNN"), a fonte do
    # laudo ("Climate Data"), a secao ("Politicas de Premiacao")
    "contador", "contadora", "contabil", "codigo", "crc", "crm", "crea", "cpf", "federal", "inss",
    "vossa", "excelencia", "senhoria", "desembargador", "desembargadora", "pagina",
    "documento", "matricula", "imovel", "climate", "data", "politica", "politicas",
    "premiacao", "leiloeiro", "leiloeira",
    # rodada de correcao 2 (I-b): o papel de quem fala pela parte nunca comeca nem compoe o nome
    "preposto", "preposta", "prepostos", "prepostas", "representante", "representantes", "socio", "socia",
    "socios", "socias", "patrono", "patrona", "patronos"} | _QUALIDADES_DO_SOCIO
# o papel logo antes do nome que diz que ele nao e' a testemunha nem o perito (o nome vira [[PESSOA_n]], sem o papel)
# a mensagem do sistema do aplicativo ("Maria saiu", "Joao entrou"): o verbo nunca e' sobrenome do contato
_VERBOS_DE_SISTEMA = {"saiu", "entrou", "adicionou", "removeu", "apagou", "eliminou", "excluiu"}
_PAPEIS_DE_OUTRA_PESSOA = {"preposto", "preposta", "representante", "socio", "socia", "procurador", "procuradora",
                           "advogado", "advogada", "patrono", "patrona"}
# Candidato que abre com estas palavras e' lugar ("Sao Leopoldo", "Vila
# Nova"), nao pessoa. Nao vao para _NUNCA_NOME: "Maria de Sao Jose" e' nome.
_NUNCA_ABRE_NOME = {"sao", "vila"}
# Titulo de funcao que precede o nome em caixa alta ("PERITO ENGENHEIRO
# FULANO DE TAL"): sai do INICIO do candidato, como os descartaveis. So' os
# que precedem nome: "TECNICO"/"ASSISTENTE" precedem tambem a secao do laudo
# ("ASSISTENTE TECNICO: BRACO ANTEBRACO PUNHO"), e o que vinha depois
# virava pessoa (validacao da 0.5.0) — esses ficam em _NUNCA_NOME e recusam.
_TITULOS_ANTES_DO_NOME = {
    "engenheiro", "engenheira", "medico", "medica", "perito", "perita", "doutor", "doutora"}
# Qualificador entre "perito" e o nome ("PERITO JUDICIAL FULANO", "Perita
# Oficial Fulana", "PERITO CONTADOR FULANO"): sai do INICIO do candidato so'
# aqui, na descoberta; continua em _NUNCA_NOME para o corte no meio e para o
# primeiro nome isolado. Sem isto a pessoa nao entrava no mapa: nada trocado
# e a guarda muda (a 0.4.4 fazia da locucao inteira um tóken vigiado).
_QUALIFICADORES_DO_PERITO = {"judicial", "oficial", "contador", "contadora", "contabil"}


def _sem_cabeca(bruto: str | None) -> list[str]:
    """As palavras do candidato sem o que o precede e nao e' nome: os
    descartaveis, os titulos de funcao, os qualificadores do perito e o par
    "Nome Completo" do formulario da ata, em qualquer ordem."""
    partes = RE_MARCADOR_CAPA.sub(" ", bruto or "").split()
    tirar = _PREFIXOS_DESCARTAVEIS | _TITULOS_ANTES_DO_NOME | _QUALIFICADORES_DO_PERITO
    while partes:
        if normalizar(partes[0]) in tirar:
            partes = partes[1:]
        elif [normalizar(p) for p in partes[:2]] == ["nome", "completo"]:
            partes = partes[2:]
        else:
            break
    return partes


def _corta_aqui(partes: list[str], j: int) -> bool:
    """A palavra j nunca e' de nome, ou uma denominacao de pessoa juridica
    comeca nela ("Sindicato dos ...", "Estado do ..."). As acrescentadas na
    0.5.0 (_PJ_QUANDO_ABRE: justica, uniao, conselho...) so' quando abrem o
    candidato (j == 0), como em eh_pessoa_fisica: "FULANA DA JUSTICA
    BELTRANA" e' gente (0.5.1)."""
    denominacao = RE_PJ_INSTITUCIONAL if j == 0 else _RE_PJ_EM_QUALQUER_POSICAO
    return (normalizar(partes[j]) in _NUNCA_NOME
            or denominacao.match(" ".join(partes[j:])) is not None)


# Rodada de correcao 4 (varredura): a palavra das listas de parada, veto e fronteira que esta' no ranking do IBGE
# com 1.000+ pessoas ("Socorro", "Dores", "Dias", "Porto", "Nascimento", "Segundo") e' sobrenome ou prenome comum;
# dentro de um nome ja' aberto por prenome provado ou por tratamento ela nao encerra nem corta o nome. Ficam de fora,
# de proposito: o tratamento ("dr"), a preposicao ("na", "no", "para"), as siglas juridicas e o sufixo societario
# ("re", "reus", "sa") e "nao" (a palavra mais frequente da frase; o ranking a tem pela grafia de nome estrangeiro).
FREQUENCIA_DE_NOME_COMUM = 1000
NUNCA_DENTRO_DO_NOME = frozenset({"dr", "dra", "na", "no", "nos", "nas", "para", "re", "reus", "sa", "nao"})


def _nome_do_ranking(n: str) -> bool:
    """A palavra (normalizada) e' prenome ou sobrenome do ranking do IBGE com FREQUENCIA_DE_NOME_COMUM+ pessoas, e
    nao esta' entre as que nunca entram no nome (NUNCA_DENTRO_DO_NOME)."""
    return n not in NUNCA_DENTRO_DO_NOME and max(frequencia_de_prenome(n), frequencia_de_sobrenome(n)) \
        >= FREQUENCIA_DE_NOME_COMUM


def _nome_limpo(bruto: str | None, aberto: bool = False) -> str | None:
    """O nome de pessoa contido no candidato da descoberta, ou None. `aberto` (rodada de correcao 4): o nome ja'
    abriu por prenome provado ou por tratamento — a palavra do ranking (_nome_do_ranking) no meio ou no fim nao corta.

    Tira do inicio os descartaveis e os titulos de funcao; recusa se o que
    sobra ABRE com denominacao de pessoa juridica ou com palavra de
    _NUNCA_NOME; CORTA antes da primeira dessas que venha depois; tira do
    fim conectivo e descartavel; exige 2+ palavras significativas; recusa
    CNPJ e sufixo societario. Nunca eh_pessoa_fisica inteiro (search):
    "Fulana Beltrana do Sindicato dos Comerciarios" perderia a testemunha
    — e a guarda, que so' ve o mapa, nao a veria."""
    partes = _sem_cabeca(bruto)
    if not partes or _corta_aqui(partes, 0) or normalizar(partes[0]) in _NUNCA_ABRE_NOME:
        return None
    for j in range(1, len(partes)):
        if _corta_aqui(partes, j) and not (aberto and _nome_do_ranking(normalizar(partes[j]))):
            partes = partes[:j]
            break
    while partes and normalizar(partes[-1]) in _PREFIXOS_DESCARTAVEIS and not (
            aberto and _nome_do_ranking(normalizar(partes[-1]))):
        partes = partes[:-1]
    if sum(1 for p in partes if normalizar(p) not in CONECTIVOS) < 2:
        return None
    nome = " ".join(partes)
    if RE_CNPJ.search(nome) or RE_SUFIXO_PJ.search(nome):
        return None
    return nome


def _prenome_provado(palavra: str) -> bool:
    """A palavra e' prenome sem olhar a caixa: a lista escrita 'a mao ou o ranking do IBGE, fora o prenome que e'
    tambem palavra comum ("rosa", "clara") e o que nunca e' nome."""
    n = normalizar(palavra)
    return (n in PRENOMES_DO_LEXICO or bool(frequencia_de_prenome(n))) and n not in PRENOMES_PALAVRA_COMUM \
        and n not in _NUNCA_NOME and n not in CONECTIVOS


def _prenome_do_ranking(palavra: str) -> bool:
    """A palavra esta' na lista de prenomes ou no ranking de prenomes do IBGE — tambem o prenome que e' palavra
    comum ("rosa", "clara", "vitoria") —, fora o que nunca e' nome."""
    n = normalizar(palavra)
    return (n in PRENOMES_DO_LEXICO or bool(frequencia_de_prenome(n))) and n not in _NUNCA_NOME \
        and n not in CONECTIVOS and n not in _PALAVRAS_DA_FRASE


def _abre_nome(palavras: list[str]) -> bool:
    """As palavras (normalizadas, na ordem do texto, a partir do comeco do candidato) abrem um nome provado, sem a
    caixa: a primeira e' prenome provado; ou (rodada de correcao 1) a primeira e as seguintes sao prenomes do
    ranking que tambem sao palavra comum ("Rosa", "Clara", "Celeste") e a que vem depois delas e' prenome provado
    ou sobrenome do ranking ("Rosa Maria Pires", "Rosa Vitoria Franco", "Celeste Antunes Prado")."""
    sig = [w for w in palavras if w not in CONECTIVOS]
    if not sig:
        return False
    if _prenome_provado(sig[0]):
        return True
    if not _prenome_do_ranking(sig[0]):
        return False
    return any(_prenome_provado(w) or w in SOBRENOMES_DO_LEXICO or bool(frequencia_de_sobrenome(w))
               for w in sig[1:])


def _sem_inicio_descartavel(valor: str, tirar: set[str]) -> list[str]:
    partes = RE_MARCADOR_CAPA.sub(" ", valor or "").split()
    while partes and normalizar(partes[0]) in tirar:
        partes = partes[1:]
    return partes


def eh_token_de_pj(info) -> bool:
    """Tóken 'pessoa' cujo valor e' de pessoa juridica: a denominacao ABRE
    o nome (depois dos descartaveis), ou ha' CNPJ ou sufixo societario.
    Mapas anteriores a 0.5.0 os tem (ente publico e condominios descobertos
    como testemunha; condominio da capa antes da 0.4.3). O mapa nao e'
    editado — o tóken fica para a reversao —, mas o substituidor, a guarda
    e o filtro de saida o ignoram. So' a categoria 'pessoa': endereco,
    e-mail, telefone... continuam todos vigiados."""
    if not isinstance(info, dict) or info.get("categoria") != "pessoa":
        return False
    valor = str(info.get("valor") or "")
    partes = _sem_inicio_descartavel(valor, _PREFIXOS_DESCARTAVEIS)
    return bool(RE_PJ_INSTITUCIONAL.match(" ".join(partes)) or RE_CNPJ.search(valor)
                or RE_SUFIXO_PJ.search(valor))


def eh_locucao_legada(info) -> bool:
    """Tóken 'pessoa' que ABRE (depois dos descartaveis e dos titulos de
    funcao) com palavra que nunca e' nome: locucao que um mapa anterior a
    0.5.0 registrou como perito ou testemunha ("Equipamentos de Protecao
    Individual", "Assinatura ..."). O nome real com cauda contaminada
    ("Fulana Beltrana Para") abre com o nome e NAO e' locucao: a guarda
    continua a procura-lo."""
    if not isinstance(info, dict) or info.get("categoria") != "pessoa":
        return False
    partes = _sem_inicio_descartavel(str(info.get("valor") or ""),
                                     _PREFIXOS_DESCARTAVEIS | _TITULOS_ANTES_DO_NOME)
    return not partes or normalizar(partes[0]) in _NUNCA_NOME


def eh_descartado(info) -> bool:
    """Tóken de pessoa que o juiz decidiu nao ser nome (etapa 2, 05/10/2026): marcado "descartado" por
    aplicar_descartes. Fica no mapa (a minuta antiga com o codigo ainda reverte), mas fora da troca, da guarda, do
    filtro de saida e da omissao."""
    return isinstance(info, dict) and info.get("descartado") is True


def _descartar_aliases(info: dict, decididos: dict) -> None:
    """Rodada de correcao 1 (M5): o alias (e a variante vista com a mesma grafia) que o juiz decidiu nao ser nome
    sai das formas ativas do tóken — guardado em "aliases_descartados"/"variantes_descartadas", nunca apagado —, e
    volta quando a decisao sai (o "Desfazer"). O valor e as outras formas do tóken nao mudam."""
    nao = {k for k, v in decididos.items() if v == incertos.NAO_NOME}
    for ativas, guardadas in (("aliases", "aliases_descartados"), ("variantes_vistas", "variantes_descartadas")):
        formas, fora = list(info.get(ativas) or []), list(info.get(guardadas) or [])
        sai = [f for f in formas if normalizar(str(f or "")) in nao]
        volta = [f for f in fora if normalizar(str(f or "")) not in nao]
        if not sai and not volta:
            continue
        info[ativas] = [f for f in formas if f not in sai] + volta
        resto = [f for f in fora if f not in volta] + sai
        if resto:
            info[guardadas] = resto
        else:
            info.pop(guardadas, None)


def aplicar_descartes(mapa: dict) -> list[str]:
    """Marca "descartado" o tóken de pessoa cujo VALOR (nao o alias) o juiz decidiu nao ser nome
    (mapa["nomes_decididos"], incertos.NAO_NOME) e que nao e' parte da capa; tira a marca quando a decisao saiu
    (o "Desfazer" revoga a decisao). O tóken nunca e' apagado nem renumerado. A montagem a chama logo depois de
    aplicar o pedido do juiz. Devolve os tokens marcados agora."""
    decididos = mapa.get("nomes_decididos") or {}
    marcados = []
    for tok, info in (mapa.get("tokens") or {}).items():
        if not isinstance(info, dict) or info.get("categoria") != "pessoa":
            continue
        if not str(tok).startswith(_PREFIXOS_DE_PARTE):
            _descartar_aliases(info, decididos)     # rodada de correcao 2 (M-c): alias de parte, nunca
        nao = (decididos.get(normalizar(str(info.get("valor") or ""))) == incertos.NAO_NOME
               and not str(tok).startswith(_PREFIXOS_DE_PARTE))
        if nao and not info.get("descartado"):
            info["descartado"] = True
            marcados.append(tok)
        elif not nao and "descartado" in info:
            del info["descartado"]
    return marcados


def token_fora_da_guarda(info) -> bool:
    """O que a guarda de entrada e o filtro de saida nao vigiam: tóken
    'pessoa' de pessoa juridica ou locucao de mapa antigo."""
    return eh_token_de_pj(info) or eh_locucao_legada(info) or eh_descartado(info)


def _nome_plausivel(nome: str | None) -> str | None:
    """Tira as palavras comuns iniciais e devolve o que sobrou, se parecer
    nome de pessoa: 2+ palavras, nenhuma delas de _NUNCA_NOME. Senao,
    None. Trabalha sobre a grafia original (devolve o trecho original,
    sem as palavras descartadas)."""
    partes = (nome or "").split()
    while partes and normalizar(partes[0]) in _PREFIXOS_DESCARTAVEIS:
        partes = partes[1:]
    if len(partes) < 2:
        return None
    if any(normalizar(p) in _NUNCA_NOME for p in partes):
        return None
    return " ".join(partes)


def _nome_do_token(info) -> str | None:
    """O nome que o substituidor procura para um tóken 'pessoa': o valor
    inteiro, quando plausivel (como ate' a 0.4.4); senao, o nome contido
    nele (o nome real que um mapa antigo gravou com cauda contaminada —
    "Fulano de Tal ENGENHEIRO DE SEGURANCA"); None para pessoa juridica,
    locucao e prenome sozinho."""
    if not isinstance(info, dict) or info.get("categoria") != "pessoa" or eh_token_de_pj(info) or eh_descartado(info):
        return None
    valor = str(info.get("valor") or "")
    if _nome_plausivel(valor) is not None:
        return valor
    # rodada de correcao 4: o nome aberto por prenome provado guarda a palavra do ranking ("Marta Porto Lima")
    return _nome_limpo(valor, aberto=True)     # rodada 5: o valor ja' foi aceito na descoberta


# Primeiro nome isolado que nunca e' trocado sozinho (0.5.0): palavras de
# ente e de imovel que abriam valores de pessoa juridica registrados como
# pessoa ("Estado", "Condominio") e tudo o que nunca e' nome.
_NUNCA_PRENOME_ISOLADO = _NUNCA_NOME | {
    "estado", "uniao", "municipio", "condominio", "edificio", "residencial",
    "distrito", "republica", "fazenda", "governo"}
# Prenomes que sao tambem palavras comuns do portugues (a mesma escolha do
# lexico de entendimentos/varredor.py, que os deixa de fora): nunca viram
# [[PRENOME_n]] e nunca ganham maiuscula artificial num titulo ou numa URL.
PRENOMES_PALAVRA_COMUM = {
    "rosa", "clara", "vitoria", "gloria", "aparecida", "cesar", "franco", "luz", "paz",
    "graca", "dores", "neves", "flores", "natal", "branca", "socorro", "estrela",
    "aurora", "serena", "constante", "angelica", "cruz", "fe", "esperanca", "alegria",
    "amor", "lua", "sol", "mar", "celeste", "bela", "rosario", "conceicao", "penha"}
# Palavra que, logo antes do prenome, faz dele um lugar ("Sao Paulo",
# "Santa Maria", "Vila Paulo"); "Sant'Ana" pelo apostrofo. Com a quebra de
# linha no meio, so' Sao/Santo/Santa ("Sao\nPaulo"): "Santana" e "Vila" sao
# tambem sobrenomes ("o preposto Carlos Santana\nJoana, a reclamante").
TOPONIMOS = {"sao", "santo", "santa", "santana", "vila"}
_TOPONIMOS_ATRAVES_DA_LINHA = {"sao", "santo", "santa"}
# Palavra comum com cedilha que o prenome do mapa, sem cedilha, nao e'
# ("MARÇO" x "Marco"). Conjunto fechado: a capa vem sem acento, e o prenome
# "CONCEICAO" tem de continuar trocando "Conceição".
_PALAVRAS_COMUNS_COM_CEDILHA = {"março"}


def _depois_de_toponimo(texto: str, palavras: list, i: int) -> bool:
    if i == 0:
        return False
    _ini, fim_ant, _orig, norm_ant = palavras[i - 1]
    entre = texto[fim_ant:palavras[i][0]]
    if norm_ant == "sant" and entre in ("'", "’"):
        return True
    if norm_ant not in TOPONIMOS or entre == "" or entre.strip():
        return False
    return "\n" not in entre or norm_ant in _TOPONIMOS_ATRAVES_DA_LINHA

def _dist_max1(a: str, b: str) -> bool:
    """True se `a` e `b` diferem por no maximo 1 edicao (substituicao,
    insercao ou remocao de 1 caractere) — tolerancia a 1 erro de OCR."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(x != y for x, y in zip(a, b)) == 1
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = j = dif = 0
    while i < la and j < lb:
        if a[i] == b[j]:
            i += 1; j += 1
        else:
            dif += 1
            if dif > 1:
                return False
            j += 1
    return True

def _registrar_variante(mapa: dict, tok: str, grafia: str) -> None:
    info = mapa["tokens"][tok]
    norm = normalizar(grafia)
    if not any(normalizar(v) == norm for v in info["variantes_vistas"]):
        info["variantes_vistas"].append(grafia)

def _registrar_casamento(mapa: dict, tok: str, chave: str, grafia: str) -> None:
    """Grava a grafia encontrada quando o casamento com o nome do mapa nao
    foi pela sequencia exata apos normalizar — para auditoria do risco
    residual nº 6 de docs/privacidade.md (duas pessoas reais fundidas no
    mesmo tóken). Duas listas: "casamentos_fuzzy" (bateu so' por tolerancia
    a erro de OCR, _dist_max1 — nomes a 1 letra de distancia) e
    "casamentos_permutados" (bateu so' com as palavras em outra ordem —
    duas pessoas cujos nomes sao permutacao um do outro). Listas criadas
    sob demanda, aditivas ao schema (nao quebram mapa gravado por versao
    anterior sem essas chaves)."""
    info = mapa["tokens"][tok]
    lista = info.setdefault(chave, [])
    norm = normalizar(grafia)
    if not any(normalizar(v) == norm for v in lista):
        lista.append(grafia)

# A cauda (0.5.0): depois de uma troca, ate' 3 palavras com maiuscula cuja
# ULTIMA e' palavra do nome do mesmo tóken ("FULANA TERCIANA BELTRANA",
# com "FULANA BELTRANA SICRANA" na capa). Conectivo de nome no meio nao
# conta, nem a inicial ("FULANA D SANTOS GOMES", "O. M."; "A"/"O"/"E" so'
# com ponto ou quebra de linha — com espaco sao artigo ou conjuncao, e o
# "E" da caixa alta para a cauda, 0.5.1); "e", "contra", descartavel e
# palavra que nunca e' nome param. Depois de um [[PRENOME_n]],
# a ultima palavra tem de ser do nome de UMA SO' das pessoas daquele prenome
# (a troca passa a ser o tóken dela: "Fulano Souza" com "Fulano Pereira
# Souza"), e a palavra de nenhuma delas para ("Advogado: Fulano Augusto
# Souza" e' outra pessoa). O prenome do lexico que nao e' do nome para
# tambem (0.5.1): "Sra. FULANA HELENA DA SILVA", com a reclamante "FULANA
# TERCIANA DA SILVA", e' outra pessoa de prenome composto que so' divide o
# sobrenome comum com ela. So' a troca do nome incompleto — o prenome, o
# prefixo — tem cauda: a do nome inteiro ja' esta' completa, e o que vem
# depois e' outra pessoa ("Herdeiros:\nFULANA DOS SICRANOS\nCICLANA DOS
# SICRANOS": a 2a sumia no tóken da 1a, e a reversao a apagava).
_CONECTIVOS_DA_CAUDA = {"da", "de", "do", "das", "dos"}
_PARADAS_DA_CAUDA = {"contra", "versus", "vs", "face"}


def _inicial(texto: str, palavras: list, j: int, do_nome: set[str]) -> bool:
    """A letra maiuscula isolada palavras[j] e' inicial de nome. "A"/"O"/"E"
    (e acentuadas) seguidas de ponto ou de quebra de linha; com espaco, so'
    quando sao a inicial de uma palavra do nome do dono (do_nome) e a
    palavra seguinte e' outra inicial ou palavra do nome ("FULANA O M
    SICRANA", com "FULANA OTILIA MIRELA SICRANA"); senao sao artigo ou
    conjuncao ("FULANA E CICLANA SICRANA"; 0.5.1). As demais, sempre."""
    if palavras[j][3] not in ("a", "o", "e"):
        return True
    fim = palavras[j + 1][0] if j + 1 < len(palavras) else len(texto)
    depois = texto[palavras[j][1]:fim]
    if depois.strip() == "." or (not depois.strip() and "\n" in depois):
        return True
    if depois.strip() or j + 1 >= len(palavras) or not any(w[:1] == palavras[j][3] for w in do_nome):
        return False
    seguinte = palavras[j + 1]
    return len(seguinte[3]) == 1 or seguinte[3] in do_nome      # 0.5.23 (#17): sem a caixa


def _estender_caudas(texto: str, palavras: list, ocupada: list[bool], trocas: list[list],
                     pessoas: list, mapa: dict, grafias: str) -> None:
    do_nome = {tok: {w for forma in (nome, *apelidos) for w in normalizar(forma).split()
                     if w not in CONECTIVOS}
               for tok, nome, apelidos in pessoas}
    parar = _NUNCA_NOME | _PREFIXOS_DESCARTAVEIS | _PARADAS_DA_CAUDA
    for troca in trocas:
        primeira, ultima, tok, grupo, estende = troca
        donos = [tok] if tok in do_nome else list(grupo or [])
        if not donos or not estende:
            continue
        j, contadas, ate, dono = ultima + 1, 0, None, None
        nomes_dos_donos = set().union(*(do_nome.get(t, set()) for t in donos))
        while j < len(palavras) and contadas < 3 and not ocupada[j]:
            entre = texto[palavras[j - 1][1]:palavras[j][0]].strip()
            if entre and not (entre == "." and len(palavras[j - 1][3]) == 1):
                break               # so' espaco (ou o ponto da inicial) separa as palavras de um nome
            orig, norm = palavras[j][2], palavras[j][3]
            if norm in _CONECTIVOS_DA_CAUDA or (len(norm) == 1 and _inicial(texto, palavras, j, nomes_dos_donos)):
                j += 1              # conectivo e inicial ("D", "M.", "E.") nao contam
                continue
            # 0.5.21 (auditoria da caixa, #9): sem a maiuscula — a prova e' a palavra do nome do dono; a do meio,
            # que nao e' dele, so' passa sem cara de frase ("Fulana pagou sicrana" para no "pagou")
            if len(norm) < 2 or norm in parar or (
                    not any(norm in do_nome[t] for t in donos) and _parada(norm, 1, frozenset(), TODA_A_LINGUA) != CONTINUA):
                break
            contadas += 1
            de_quem = [t for t in donos if norm in do_nome[t]]
            if grupo and not de_quem:
                break               # depois do [[PRENOME_n]], palavra de nenhuma das pessoas dele
            if not de_quem and norm in PRENOMES_DO_LEXICO:
                break               # o prenome (composto) de outra pessoa
            if len(de_quem) == 1:
                ate, dono = j, de_quem[0]
            j += 1
        if ate is None:
            continue
        for x in range(ultima + 1, ate + 1):
            ocupada[x] = True
        troca[1], troca[2] = ate, dono
        grafia = grafias[palavras[primeira][0]:palavras[ate][1]]
        _registrar_variante(mapa, dono, grafia)
        _registrar_casamento(mapa, dono, "casamentos_cauda", grafia)


def _casa_janela(texto: str, palavras: list, i: int, alvo: list[str]) -> tuple[bool, bool]:
    """(casou, fuzzy): as palavras a partir de i casam o alvo, cada uma
    exata ou a 1 letra (erro de OCR), separadas so' por espaco."""
    fuzzy = False
    for j, alvo_w in enumerate(alvo):
        norm = palavras[i + j][3]
        if norm != alvo_w:
            if not _dist_max1(norm, alvo_w):
                return False, False
            fuzzy = True
        if j and texto[palavras[i + j - 1][1]:palavras[i + j][0]].strip():
            return False, False
    return True, fuzzy


def _trocar_parciais(texto: str, palavras: list, ocupada: list[bool], trocas: list[list], pessoas: list,
                     mapa: dict, grafias: str) -> None:
    """Dois alvos do nome incompleto, so' de UMA pessoa (o de duas fica), com
    a variante registrada para a guarda: a inicial do prenome com o resto do
    nome ("F. Terciano Sicrano", "F\\nTerciano Sicrano"; a inicial "A"/"O"/"E"
    so' com ponto ou quebra de linha — com espaco e' artigo) e o nome sem o
    1o prenome, com 3+ palavras significativas (a parte que usa o segundo
    nome: "RECLAMANTE: TERCIANO BELTRANO SICRANO", com "FULANO TERCIANO
    BELTRANO SICRANO" na capa) — este, nunca logo depois de outra palavra
    com maiuscula que possa ser nome ("CICLANO TERCIANO BELTRANO SICRANO" e'
    outra pessoa, talvez parente). Nenhum dos dois tem cauda."""
    com_inicial: dict[tuple[str, tuple[str, ...]], set[str]] = {}
    sem_prenome: dict[tuple[str, ...], set[str]] = {}
    for tok, nome, _apelidos in pessoas:
        partes = normalizar(nome).split()
        resto = partes[1:]
        while resto and resto[0] in CONECTIVOS:
            resto = resto[1:]
        significativas = sum(1 for w in resto if w not in CONECTIVOS)
        if significativas >= 2:
            com_inicial.setdefault((partes[0][0], tuple(resto)), set()).add(tok)
        if significativas >= 3:
            sem_prenome.setdefault(tuple(resto), set()).add(tok)
    nome_antes = _NUNCA_NOME | _PREFIXOS_DESCARTAVEIS

    def trocar(i: int, fim: int, tok: str, fuzzy: bool) -> None:
        for x in range(i, fim + 1):
            ocupada[x] = True
        trocas.append([i, fim, tok, None, False])
        grafia = grafias[palavras[i][0]:palavras[fim][1]]
        _registrar_variante(mapa, tok, grafia)
        if fuzzy:
            _registrar_casamento(mapa, tok, "casamentos_fuzzy", grafia)

    for (inicial, resto), toks in com_inicial.items():
        k = len(resto)
        if len(toks) != 1:
            continue
        for i in range(len(palavras) - k):
            orig = palavras[i][2]
            # 0.5.23 (auditoria da caixa, #17): a inicial e o resto do nome em qualquer caixa ("f. terciano
            # sicrano"); a prova e' o resto inteiro do nome da pessoa. "a"/"o"/"e" continuam so' com ponto ou quebra
            # de linha (com espaco sao artigo ou conjuncao)
            if ocupada[i] or any(ocupada[i + 1:i + 1 + k]) or len(orig) != 1 or palavras[i][3] != inicial:
                continue
            entre = texto[palavras[i][1]:palavras[i + 1][0]]
            if entre.strip() not in ("", ".") or (entre.strip() == "" and "\n" not in entre
                                                   and palavras[i][3] in ("a", "o", "e")):
                continue
            casou, fuzzy = _casa_janela(texto, palavras, i + 1, list(resto))
            if casou:
                trocar(i, i + k, next(iter(toks)), fuzzy)
    for resto, toks in sem_prenome.items():
        k = len(resto)
        if len(toks) != 1:
            continue
        for i in range(len(palavras) - k + 1):
            if any(ocupada[i:i + k]):
                continue
            # 0.5.21 (auditoria da caixa, #10): "outra palavra de nome logo antes" sem a caixa — a palavra que nao
            # para a leitura de um nome (_parada) e nao e' das que vem antes dele ("CICLANO", "Ciclano",
            # "ciclano"); "INQUIRIDO", "a reclamante", o ":" nao sao
            anterior = palavras[i - 1][3] if i else ""
            if i and not texto[palavras[i - 1][1]:palavras[i][0]].strip() and len(anterior) >= 2 \
                    and anterior not in nome_antes and _parada(anterior, 0, frozenset(), TODA_A_LINGUA) == CONTINUA:
                continue            # outra palavra de nome logo antes: e' outra pessoa
            casou, fuzzy = _casa_janela(texto, palavras, i, list(resto))
            if casou:
                trocar(i, i + k - 1, next(iter(toks)), fuzzy)


# O nome em maiusculas colado a' palavra anterior, no titulo do PJe
# ("Contestacao (C-AlfaxFULANA BELTRANA)"): a minuscula seguida do resto da
# palavra todo em maiusculas, 2+ letras, e' o comeco de outra palavra.
RE_COLADO = re.compile(r"(?<=[a-zß-öø-ÿ])(?=[A-ZÀ-ÖØ-Þ]{2,}$)")


def _palavras(texto: str) -> list[tuple[int, int, str, str]]:
    """[(ini, fim, grafia, normalizada)] das palavras do texto (RE_PALAVRA),
    com a palavra em maiusculas colada a' anterior separada (RE_COLADO)."""
    saida = []
    for m in RE_PALAVRA.finditer(texto):
        ini, palavra = m.start(), m.group()
        c = RE_COLADO.search(palavra)
        if c:
            saida.append((ini, ini + c.start(), palavra[:c.start()], normalizar(palavra[:c.start()])))
            ini, palavra = ini + c.start(), palavra[c.start():]
        saida.append((ini, ini + len(palavra), palavra, normalizar(palavra)))
    return saida


_VIZINHOS_ANTES_DO_PRENOME = {"sr", "sra", "srta", "dona", "seu", "dr", "dra", "doutor", "doutora", "reclamante",
                              "reclamada", "reclamado", "autor", "autora", "testemunha", "perito", "perita",
                              "preposta", "preposto", "depoente", "paradigma"}


def _vizinho_de_nome(texto: str, palavras: list, i: int, do_dono: set[str]) -> bool:
    """O prenome palavras[i] tem vizinho que prova o nome, sem a caixa: o tratamento ou o papel logo antes ("a
    sra. clara", "a reclamante Clara"), ou, logo depois (so' espaco no meio), uma palavra do nome do dono."""
    if i and palavras[i - 1][3] in _VIZINHOS_ANTES_DO_PRENOME \
            and not texto[palavras[i - 1][1]:palavras[i][0]].strip(" \t.:"):
        return True
    return i + 1 < len(palavras) and palavras[i + 1][3] in do_dono \
        and palavras[i + 1][3] not in PRENOMES_PALAVRA_COMUM and not texto[palavras[i][1]:palavras[i + 1][0]].strip()


def _spans_de_nomes(texto: str, mapa: dict, original: str | None = None,
                    urls: list[tuple[int, int]] = ()) -> list[tuple[int, int, str]]:
    """Varre `texto` procurando os nomes cadastrados no mapa (categoria
    'pessoa') e devolve [(ini, fim, token), ...]. Nao reordena nem resolve
    sobreposicao com outras fontes de span — isso e' tarefa de
    pseudonimizar. `original` (0.5.0): o texto de mesmo tamanho de onde vem
    a grafia das variantes registradas, quando `texto` e' a copia que
    pseudonimizar_rotulo prepara. `urls`: dentro delas nao nasce
    [[PRENOME_n]] (a URL e' tokenizada inteira, e o tóken ficaria orfao)."""
    if not nivel_mod.nomes_em_codigo(nivel_mod.do_mapa(mapa)):
        return []                   # publico: nem as pessoas de um mapa de rodada anterior sao trocadas
    grafias = original if original is not None else texto
    palavras = _palavras(texto)
    if not palavras:
        return []
    ocupada = [False] * len(palavras)
    # cada troca como [1a palavra, ultima palavra, tóken, grupo, estende]
    # (indices em `palavras`; grupo: as pessoas do prenome ambiguo do
    # [[PRENOME_n]]; estende: o nome incompleto — prenome, prefixo — que a
    # cauda (0.5.0) pode completar pela ultima palavra)
    trocas: list[list] = []

    # mapa contaminado por execucao anterior (o nome de um banco, "Da
    # Limitação", um ente publico descoberto como testemunha): so' e' alvo
    # o nome de pessoa que _nome_do_token acha no valor (0.5.0), mais os
    # outros nomes da mesma pessoa (aliases)
    pessoas = [(tok, nome, [str(a) for a in info.get("aliases") or [] if a])
               for tok, info in mapa["tokens"].items() if (nome := _nome_do_token(info))]

    # Alvos de 2+ palavras: nome completo normalizado, a variante sem
    # conectivos (quando diferente) e — para nome com 2-3 palavras
    # significativas — as permutacoes dessas palavras (a inicial pode
    # grafar sobrenomes em ordem trocada, erro comum de digitacao
    # forense; caso de 04/09/2026). Limitado a 2-3 palavras: ate' 6 alvos
    # extras por nome, sem explosao fatorial em nomes longos. Ordenados
    # do mais longo (mais palavras, depois mais caracteres) para o mais
    # curto, para que um nome maior "coma" antes de um menor que seja seu
    # prefixo/sufixo; em empate, alvo em ordem exata ANTES de permutado —
    # duas pessoas reais cujos nomes sao permutacao um do outro casam
    # cada uma no proprio tóken, nunca no da outra.
    alvos: list[tuple[list[str], str, bool]] = []
    for tok, nome, apelidos in pessoas:
        nome_norm = normalizar(nome)
        palavras_nome = nome_norm.split()
        if len(palavras_nome) < 2:
            continue
        alvos.append((palavras_nome, tok, False))
        sem_conectivo = [w for w in palavras_nome if w not in CONECTIVOS]
        if len(sem_conectivo) >= 2 and sem_conectivo != palavras_nome:
            alvos.append((sem_conectivo, tok, False))
        if 2 <= len(sem_conectivo) <= 3:
            exatas = {tuple(palavras_nome), tuple(sem_conectivo)}
            for perm in sorted(set(permutations(sem_conectivo))):
                if perm not in exatas:
                    alvos.append((list(perm), tok, True))
        # 0.5.0: os outros nomes da mesma pessoa (a ancora de qualificacao,
        # a mesma testemunha descoberta de novo) sao alvo como o nome
        # completo — sem permutacao nem prefixo
        for apelido in apelidos:
            palavras_apelido = normalizar(apelido).split()
            if len(palavras_apelido) < 2:
                continue
            alvos.append((palavras_apelido, tok, False))
            sem_conectivo = [w for w in palavras_apelido if w not in CONECTIVOS]
            if len(sem_conectivo) >= 2 and sem_conectivo != palavras_apelido:
                alvos.append((sem_conectivo, tok, False))
    # Prefixos do nome (primeiro nome + palavras seguintes, 2+ palavras,
    # sem terminar em conectivo): a extracao do PDF pode partir o nome e
    # intercalar outra linha no meio (caso de 22/09/2026) — sem este alvo, so' o
    # primeiro nome isolado virava tóken e o sobrenome colado a ele vazava.
    # Prefixo que coincide com alvo de outra pessoa (ou com prefixo dela) e'
    # ambiguo e fica de fora, como o primeiro nome isolado ambiguo.
    donos: dict[tuple[str, ...], set[str]] = {}
    for palavras_alvo, tok, _ in alvos:
        donos.setdefault(tuple(palavras_alvo), set()).add(tok)
    prefixos: list[tuple[list[str], str]] = []
    for tok, nome, _apelidos in pessoas:
        palavras_nome = normalizar(nome).split()
        for j in range(2, len(palavras_nome)):
            prefixo = palavras_nome[:j]
            if prefixo[-1] in CONECTIVOS:
                continue
            donos.setdefault(tuple(prefixo), set()).add(tok)
            prefixos.append((prefixo, tok))
    alvos = [(p, t, perm, False) for p, t, perm in alvos]
    alvos += [(p, t, False, True) for p, t in prefixos
              if donos[tuple(p)] == {t}]
    alvos.sort(key=lambda a: (-len(a[0]), -sum(len(w) for w in a[0]),
                              a[3], a[2]))

    for alvo_palavras, tok, permutado, prefixo in alvos:
        k = len(alvo_palavras)
        i = 0
        limite = len(palavras) - k
        while i <= limite:
            if any(ocupada[i:i + k]):
                i += 1
                continue
            casou = True
            fuzzy = False
            for j in range(k):
                norm = palavras[i + j][3]
                alvo_w = alvo_palavras[j]
                if norm != alvo_w:
                    if not _dist_max1(norm, alvo_w):
                        casou = False
                        break
                    fuzzy = True  # bateu so' por tolerancia a erro de OCR
                if j > 0:
                    # RE_PALAVRA nao tokeniza digito/pontuacao: sem essa
                    # checagem, "João 123 Silva" ligaria "João" a "Silva"
                    # como se fossem adjacentes na lista de palavras — a
                    # janela venceria de ini("João") a fim("Silva") e
                    # apagaria o "123" do meio ao reconstruir o texto.
                    # So' espaco em branco pode separar palavras casadas
                    # (uma quebra de linha entre elas continua ok).
                    entre = texto[palavras[i + j - 1][1]:palavras[i + j][0]]
                    if entre.strip():
                        casou = False
                        break
            # Inicial maiuscula na 1ª palavra OU janela TODA em minusculas
            # (OCR de comprovante — ex.: destinatario de PIX — transcreve o
            # nome sem maiuscula alguma; nome completo multi-palavra em
            # minusculas dificilmente e' falso positivo, ao contrario do
            # primeiro nome isolado, que segue exigindo maiuscula abaixo).
            # 0.5.21 (auditoria da caixa, #8): o prefixo do nome tambem ("pix para maria pereira", de "Maria
            # Pereira Lima"), quando nem todas as palavras dele sao palavra comum ou palavra que nunca e' nome
            # rodada de correcao 1 (M1): no prefixo, a 1a palavra exata ("pago para lucia" nao e' "Mara Lucia")
            janela_minuscula = all(palavras[i + j][2].islower() for j in range(k)) and (
                not prefixo or palavras[i][3] == alvo_palavras[0]) and (
                not prefixo or not all(w in PRENOMES_PALAVRA_COMUM or _parada(w, 0, frozenset(), TODA_A_LINGUA) == PARADA_FORTE
                                       for w in alvo_palavras if w not in CONECTIVOS))
            # 0.5.0: 1a palavra minuscula que casa EXATAMENTE (sem fuzzy) a 1a
            # do alvo, com outra palavra da janela com maiuscula ("a
            # reclamante joana Pereira Lima"). Sem fuzzy na 1a: "pago para
            # Lucia Santos" nao e' "Mara Lucia Santos". Nunca no alvo
            # permutado nem com a 1a de menos de 3 letras: o sobrenome que e'
            # palavra comum ("30 dias Fulano", com "Fulano Dias") e o artigo
            # ("a Alfa S.A.") seriam engolidos.
            primeira_exata = (not permutado and len(alvo_palavras[0]) >= 3
                              and palavras[i][3] == alvo_palavras[0] and any(
                                  palavras[i + j][2][:1].isupper() for j in range(1, k)))
            if casou and (palavras[i][2][:1].isupper() or janela_minuscula or primeira_exata):
                ini, fim = palavras[i][0], palavras[i + k - 1][1]
                trocas.append([i, i + k - 1, tok, None, prefixo])
                for j in range(k):
                    ocupada[i + j] = True
                _registrar_variante(mapa, tok, grafias[ini:fim])
                if fuzzy:
                    _registrar_casamento(mapa, tok, "casamentos_fuzzy",
                                         grafias[ini:fim])
                if permutado:
                    _registrar_casamento(mapa, tok, "casamentos_permutados",
                                         grafias[ini:fim])
                i += k
            else:
                i += 1

    # 0.5.0: a inicial do prenome com o resto do nome; o nome sem o 1o prenome
    _trocar_parciais(texto, palavras, ocupada, trocas, pessoas, mapa, grafias)

    # Primeiro nome isolado: casamento exato (sem fuzzy) com inicial
    # maiuscula. Inequivoco (um unico token do mapa inteiro tem aquele
    # primeiro nome): o tóken da pessoa. Ambiguo (0.5.0): um tóken proprio
    # [[PRENOME_n]], reversivel, que nao diz de quem e' — antes ficava em
    # claro e fora da guarda —, nunca para palavra comum.
    primeiros: dict[str, list[str]] = {}
    grafia_do_primeiro: dict[str, str] = {}
    for tok, nome, _apelidos in pessoas:
        nome_norm = normalizar(nome)
        if not nome_norm:
            continue
        primeiro = nome_norm.split()[0]
        primeiros.setdefault(primeiro, []).append(tok)
        grafia_do_primeiro.setdefault(tok, nome.split()[0])

    for primeiro, toks in primeiros.items():
        # "Da", "Não", "Banco", "Estado" isolados nunca sao primeiro nome de ninguem
        if len(primeiro) < 3 or primeiro in CONECTIVOS or primeiro in _NUNCA_PRENOME_ISOLADO:
            continue
        if len(toks) == 1:
            dono = toks[0]
        elif primeiro in PRENOMES_PALAVRA_COMUM:
            continue                # "a Rosa vermelha" com duas Rosas no mapa
        else:
            dono = None
        sem_cedilha = all("ç" not in grafia_do_primeiro[t].casefold() for t in toks)
        # 0.5.22 (auditoria da caixa, #11, em parte): o prenome com um vizinho que prova o nome (o tratamento ou o
        # papel logo antes, a palavra do nome do dono logo depois) ou que o juiz decidiu ser nome e' trocado em
        # qualquer caixa; o que o juiz decidiu nao ser nome nunca. Sem eles, fica a regra de antes (a inicial
        # maiuscula): o prenome minusculo solto continua com a omissao por palavra e a guarda, que comparam sem
        # caixa — tirar a caixa daqui mudaria a copia do titulo, a omissao e a guarda (ver docs/privacidade.md)
        # rodada de correcao 1 (M4): o "nao_nome" vale para candidatos de 2+ palavras; o de uma palavra nunca desliga
        # o prenome de uma pessoa do mapa — so' o "nome" do juiz conta aqui
        decidido = incertos.decisao(mapa, primeiro)
        do_dono = {w for t in toks for f in [*(n for tk, n, _a in pessoas if tk == t)] for w in normalizar(f).split()
                   if w != primeiro and w not in CONECTIVOS}
        for i, (ini, fim, orig, norm) in enumerate(palavras):
            if ocupada[i] or norm != primeiro:
                continue
            if _depois_de_toponimo(texto, palavras, i):
                continue            # "Sao Paulo", "Santa Maria": lugar, nao a pessoa
            if sem_cedilha and orig.casefold() in _PALAVRAS_COMUNS_COM_CEDILHA:
                continue            # "MARÇO" nao e' o prenome "Marco"
            if not (orig[:1].isupper() or decidido == incertos.NOME or _vizinho_de_nome(texto, palavras, i, do_dono)):
                continue
            if dono is None:
                if any(u_ini <= ini < u_fim for u_ini, u_fim in urls):
                    continue
                tok = token_para(mapa, "PRENOME", "pessoa", orig.capitalize())
            else:
                tok = dono
                _registrar_variante(mapa, tok, grafias[ini:fim])
            trocas.append([i, i, tok, None if dono else toks, True])
            ocupada[i] = True

    _estender_caudas(texto, palavras, ocupada, trocas, pessoas, mapa, grafias)
    return [(palavras[a][0], palavras[b][1], tok) for a, b, tok, _grupo, _estende in trocas]

# ---------------------------------------------------------------
# Descoberta de testemunhas e peritos (secao 7.2 da spec): nao constam
# da capa do processo, entram no mapa quando aparecem em ata de audiencia
# ou em laudo pericial. Roda ANTES da substituicao.
# ---------------------------------------------------------------

# 0.5.22: RE_NOME_SEQ (o nome pela forma — palavras com inicial maiuscula ou em caixa alta) saiu: as ancoras de
# pessoa (0.5.19) e a de qualificacao (0.5.22) leem as palavras sem a caixa. A palavra de nome, em qualquer caixa:
_PALAVRA = r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ']*"
# 0.5.0: o polo aceita o ordinal ("da 2ª reclamada", "do 1º reclamado"), por
# extenso e em lista ("da primeira e segunda reclamadas", "das reclamadas") —
# sem ele, o enchimento atravessava "da 2ª reclamada -" e pousava na pessoa
# juridica que a ata escreve antes da testemunha, ou nem chegava ao nome.
_ORDINAL_DO_POLO = r"(?:\d{1,2}\s*[ªº°aAoO]\.?|(?i:primeir[oa]|segund[oa]|terceir[oa]|quart[oa]|quint[oa]))"
# 0.5.19 (auditoria da caixa, #1): as ancoras so' marcam ONDE o nome pode comecar; o nome e' lido sem a caixa por
# _nomes_depois_da_ancora (palavras normalizadas ate' a pontuacao, a quebra de linha, o rotulo seguinte ou o termo
# que nunca e' nome). Antes, RE_NOME_SEQ (palavras com maiuscula) delimitava o nome: em minusculas a testemunha,
# o perito, a paradigma e o "Nome:" do formulario escapavam; em CAIXA ALTA qualquer palavra contava como nome.
RE_ANCORA_TESTEMUNHA = re.compile(
    r"\b(?i:testemunhas?)\b(?:[^\n:;,.]{0,20}?\b(?i:d[oa]s?)\s+"
    r"(?:" + _ORDINAL_DO_POLO + r"\s+(?:(?i:e)\s+" + _ORDINAL_DO_POLO + r"\s+)?)?"
    r"(?P<polo>(?i:reclamantes?|reclamad[oa]s?))\b)?")
RE_ANCORA_PERITO = re.compile(r"\b(?i:perit[oa])\b")
# Paradigma de equiparacao salarial: nomeada na PETICAO INICIAL ("pede
# equiparacao com NOME", "aponta como paradigma NOME"), antes de qualquer
# ata — sem estas ancoras, uma paradigma que nao fosse tambem parte ou
# testemunha ficava fora do mapa e o nome saia em claro no dossie (caso
# de 04/09/2026). Lista como a testemunha; prefixo PARADIGMA_n (0.4.0).
RE_ANCORA_PARADIGMA = re.compile(r"\b(?i:paradigmas?)\b")
RE_ANCORA_EQUIPARACAO = re.compile(r"\b(?i:equipara[çc][ãa]o)\b(?:\s+(?i:salarial))?\s+(?i:com)\b")
# 0.5.35 (Parte B da execucao; Diferido 3 da Parte A): os terceiros da execucao que nao sao
# parte da capa nem testemunha — arrematante e adquirente (autos de arrematacao, cartas),
# socio (atos constitutivos, IDPJ) e quem recebeu o AR. O leiloeiro e o oficial de justica
# sao agentes publicos: sem ancora, como ate' aqui. O nome e' lido sem a caixa e provado
# pelo lexico, como a testemunha (_nomes_depois_da_ancora).
RE_ANCORA_ARREMATANTE = re.compile(r"\b(?i:arrematantes?)\b")
RE_ANCORA_ADQUIRENTE = re.compile(r"\b(?i:adquirentes?)\b")
RE_ANCORA_SOCIO = re.compile(r"\b(?i:s[óo]ci[oa]s?)(?:-(?i:administrador|gerente|diretor)[a]?)?\b")
RE_ANCORA_RECEBEDOR = re.compile(r"\b(?i:recebid[oa]\s+por|recebedor(?:a)?)\b")
ANCORAS_DA_EXECUCAO = ((RE_ANCORA_ARREMATANTE, "ARREMATANTE", "arrematante"),
                       (RE_ANCORA_ADQUIRENTE, "ADQUIRENTE", "adquirente"),
                       (RE_ANCORA_SOCIO, "SOCIO", "sócio"),
                       (RE_ANCORA_RECEBEDOR, "RECEBEDOR", "recebedor do AR"))
# "socio"/"socia" esta' entre os papeis de outra pessoa (_PAPEIS_DE_OUTRA_PESSOA: o socio colado ao nome, na ancora
# da testemunha, nao e' a testemunha); na ancora do socio, e' a propria ancora
_PAPEIS_DA_ANCORA_DO_SOCIO = frozenset({"socio", "socia", "socios", "socias"})
# O enchimento entre a ancora e o nome: ate' duas vezes "ate' 30 caracteres sem pontuacao + uma pontuacao", e
# espaco ("Testemunha:\nFulano"); a quebra de linha conta como caractere (no maximo 2: a empresa da ata partida
# em duas linhas, "CONDOMINIO ALFAVILLE\nNORTE: Fulana"). Absorve o polo escrito de outro jeito, o marcador de
# lista ("Rol de testemunhas: 1) Maria"), a empresa antes do ":" da ata e o tratamento ("O perito do juizo, Dr.
# Carlos").
RE_ENCHIMENTO_DA_ANCORA = re.compile(r"(?:[^:;,.]{0,30}[:;,.]?){1,2}\s*")
# A inicial do prenome, isolada, logo antes do resto do nome ("Primeira
# testemunha das reclamadas: F\nBeltrana Sicrana"): se o mapa ja' tem a
# pessoa ("FULANA BELTRANA SICRANA"), e' ela — a troca a acha pela inicial —, e os
# sobrenomes nao viram outra testemunha.
RE_INICIAL_ANTES = re.compile(r"(?<![A-Za-zÀ-ÖØ-öø-ÿ])([A-ZÀ-Ö])\.?\s*$")


_RE_SUFIXO_LOGO_DEPOIS = re.compile(r"(?i)[ \t]*(?:ltda|s\s*[./]\s*a|s\.a\.|s\s+a|eireli|epp|&\s*cia)\b")


def _pj_na_ancora(texto: str, ini: int, fim: int) -> bool:
    """O candidato texto[ini:fim] de uma ancora de pessoa natural
    (testemunha, paradigma) e' pessoa juridica: sufixo societario ou CNPJ
    nele ("ALFA TELECOM LTDA") ou na sobra ate' o ":" da ata, na mesma linha
    e a ate' 30 caracteres, sem virgula ("ALFA TELECOM S.A.: Fulana ..." —
    o "S" e o "A" soltos nao entram no candidato) — ou, sem o ":", ate' a
    virgula ("BETA SEGUROS LTDA, preposta": a leitura sem a caixa para
    antes do sufixo, 0.5.19). Recusado, e nao cortado: o resto da empresa
    nao e' gente (0.5.1)."""
    alvo = texto[ini:fim]
    resto = texto[fim:fim + 31].split("\n")[0]
    if ":" in resto:
        sobra = resto.split(":")[0]
        if not re.search(r"[,;]", sobra):
            alvo += sobra
    elif _RE_SUFIXO_LOGO_DEPOIS.match(resto):
        return True                 # "BETA SEGUROS LTDA, preposta" (a testemunha que trabalhou na Alfa Ltda, nao)
    alvo = alvo.rstrip()
    return bool(RE_SUFIXO_PJ.search(alvo) or RE_CNPJ.search(alvo))


def _ja_no_mapa_pela_inicial(texto: str, ini: int, nome: str, mapa: dict) -> bool:
    m = RE_INICIAL_ANTES.search(texto, max(0, ini - 8), ini)
    if not m:
        return False
    inicial = normalizar(m.group(1))
    resto = [w for w in normalizar(nome).split() if w not in CONECTIVOS]
    for info in mapa["tokens"].values():
        if not isinstance(info, dict) or info.get("categoria") != "pessoa":
            continue
        sig = [w for w in normalizar(str(info.get("valor") or "")).split() if w not in CONECTIVOS]
        if len(sig) == len(resto) + 1 and sig[0].startswith(inicial) and sig[1:] == resto:
            return True
    return False


# Ancora de qualificacao (0.5.0): depois do prenome de uma PARTE, 1 a 3
# palavras com maiuscula e ", brasileira" / ", ja' qualificada" /
# ", portador" — o nome com que as peticoes qualificam a parte, que pode
# nao ser o da capa ("PRENOME SOBRENOME3 SOBRENOME1"). So' com um sobrenome
# em comum com o da capa: sem isso, o socio da reclamada, o advogado
# substabelecido ou o preposto com o mesmo prenome virava a parte.
RE_QUALIFICACAO = re.compile(
    r"(?P<resto>(?:\s+(?:(?i:d[aeo]s?)\s+)?(?:%s)){1,3})\s*,\s*"
    r"(?i:brasileir[oa]s?\b|(?:j[áa]\s+)?(?:devidamente\s+)?qualificad[oa]s?\b|"
    r"portador[a]?\b|inscrit[oa]s?\b)" % _PALAVRA)
# papeis de quem a descoberta registra (a mesma pessoa descoberta de novo
# vira alias do tóken dela; parte da capa nunca e' fundida)
_PAPEIS_DESCOBERTOS = {"testemunha", "perito", "perita", "paradigma", "interlocutor"}
# o sufixo de geracao separa as pessoas ("Fulano Beltrano" e "Fulano Beltrano Filho")
_SUFIXOS_DE_GERACAO = {"filho", "filha", "neto", "neta", "junior", "jr", "sobrinho", "sobrinha", "bisneto",
                       "bisneta"}
_PREFIXOS_DE_PARTE = ("[[RECLAMANTE_", "[[RECLAMADO_", "[[TERCEIRO_")


def _significativas(nome: str) -> list[str]:
    return [w for w in normalizar(nome).split() if w not in CONECTIVOS]


def _mesma_pessoa(a: list[str], b: list[str]) -> bool:
    """As mesmas palavras significativas (2+), ou a forma curta com 3+ e'
    o comeco da longa, palavra a palavra — o prenome igual, os sobrenomes
    com ate' 1 letra de diferenca ("Anisia Mirtes Bastiani" x "ANISIA
    MIRTES BASTIANI DA SILVA"; "... Castanheira" x "... CASTANHEIRAS") e a
    ultima palavra da curta podendo ser o comeco da palavra da longa (a coluna da
    ata trunca o nome: "... Bastiani Ca" x "... BASTIANI CAMPOS"). Com 2
    palavras so' a igualdade ("Ana Paula Souza" e "Ana Paula Lima" sao duas
    pessoas); o prenome nunca por aproximacao ("Fulano" e "Fulana de Tal
    Souza" sao irmaos, nao a mesma pessoa)."""
    if a == b:
        return len(a) >= 2
    curto, longo = sorted((a, b), key=len)
    if len(curto) < 3 or curto[0] != longo[0] or _SUFIXOS_DE_GERACAO & set(longo[len(curto):]):
        return False
    ultima = len(curto) - 1
    return all(x == y or _dist_max1(x, y)
               or (i == ultima and min(len(x), len(y)) >= 2 and (y.startswith(x) or x.startswith(y)))
               for i, (x, y) in enumerate(zip(curto, longo)) if i > 0)


def _formas(info: dict) -> list[str]:
    return [str(info.get("valor") or ""), *(str(a) for a in info.get("aliases") or [])]


def _acrescentar_alias(mapa: dict, tok: str, nome: str) -> None:
    """Outro nome da mesma pessoa: alvo da troca (_spans_de_nomes) e, como
    variante vista, vigiado pela guarda. Chave aditiva do mapa ("aliases"),
    criada sob demanda; o reversor nao a usa."""
    info = mapa["tokens"][tok]
    chave = normalizar(nome)
    if all(normalizar(f) != chave for f in _formas(info)):
        info.setdefault("aliases", []).append(nome)
    info.setdefault("variantes_vistas", [])
    _registrar_variante(mapa, tok, nome)


def _mesma_pessoa_que_a_parte(novo: list[str], sig: list[str], papel: str) -> bool:
    """A pessoa descoberta e' a parte da capa: a forma igual (as mesmas
    palavras significativas); a nao identica (_mesma_pessoa: a 1 letra ou
    truncada na ultima palavra), so' para o perito e com o mesmo numero de
    palavras — o caso medido na validacao (a parte capturada como perito,
    truncada pela coluna). A testemunha e a paradigma com o comeco do nome
    da parte sao outra pessoa (a mae com o nome da filha menos o ultimo
    sobrenome; o pai e o filho sem sufixo; "Costa" x "Costalonga"; 0.5.1)."""
    if novo == sig:
        return len(novo) >= 2
    return normalizar(papel) in ("perito", "perita") and len(novo) == len(sig) and _mesma_pessoa(novo, sig)


def _registrar_descoberta(mapa: dict, prefixo: str, nome: str, papel: str) -> str:
    """token_para, mas a mesma pessoa descoberta de novo (_mesma_pessoa com
    UM tóken antes: testemunha, perito, paradigma; ou a parte da capa, so'
    com a forma igual, ou, para o perito, a quase igual com o mesmo numero
    de palavras — _mesma_pessoa_que_a_parte) vira alias dele, e nao um
    tóken novo: dois tókens da mesma pessoa deixavam o prenome dela
    ambiguo, fora da troca e da guarda, e o prefixo do nome, de dois donos,
    fora da troca."""
    novo = _significativas(nome)
    donos = []
    for tok, info in mapa["tokens"].items():
        if (not isinstance(info, dict) or info.get("categoria") != "pessoa" or eh_token_de_pj(info)
                or eh_descartado(info) or tok.startswith("[[PRENOME_")):
            continue
        descoberto = normalizar(str(info.get("papel") or "")) in _PAPEIS_DESCOBERTOS
        if any(_mesma_pessoa(novo, sig) if descoberto else _mesma_pessoa_que_a_parte(novo, sig, papel)
               for sig in (_significativas(f) for f in _formas(info))):
            donos.append(tok)
    if len(donos) == 1:
        _acrescentar_alias(mapa, donos[0], nome)
        return donos[0]
    return token_para(mapa, prefixo, "pessoa", nome, papel=papel)


def _sobrenome_em_comum(a: list[str], b: list[str]) -> bool:
    """Alguma palavra de `a` e' sobrenome de `b`: igual; com 4+ letras, uma
    o comeco da outra ("KRETZ" x "KRETZER"); com 5+ letras, a 1 letra. Com 4
    letras, a 1 letra e' outro sobrenome ("LIMA" x "LIMO", "LEAL" x "LEAO";
    0.5.1)."""
    return any(x == y or (min(len(x), len(y)) >= 4 and (x.startswith(y) or y.startswith(x)))
               or (min(len(x), len(y)) >= 5 and _dist_max1(x, y))
               for x in a for y in b)


# A qualificacao de advogado ("inscrito na OAB"), antes de a peticao passar
# a falar de quem representa a parte ("por seu advogado", "procurador"):
# e' o advogado substabelecido que divide o prenome e um sobrenome com a
# parte, nao ela (0.5.1).
_RE_INSCRITO_NA_OAB = re.compile(r"(?i)\binscrit[oa]s?\s+n[ao]\s+(?:OAB|ordem\s+dos\s+advogados)\b")
_RE_FIM_DA_QUALIFICACAO = re.compile(
    r"(?i)\bpor\s+(?:seus?|suas?|interm[eé]dio)\b|\bprocurador|\brepresentad[oa]|\bneste\s+ato\b|\n\s*\n")


def _qualificacao_de_advogado(texto: str, fim: int) -> bool:
    trecho = texto[fim:fim + 150]
    corte = _RE_FIM_DA_QUALIFICACAO.search(trecho)
    return bool(_RE_INSCRITO_NA_OAB.search(trecho[:corte.start()] if corte else trecho))


def _ancorar_qualificacao(texto: str, mapa: dict) -> None:
    """O nome com que o texto qualifica uma PARTE da capa (prenome dela,
    inequivoco entre as pessoas do mapa, + 1 a 3 palavras com maiuscula,
    uma delas sobrenome da parte, + ", brasileira"...) vira alias da parte —
    nunca o que ja' e' outro tóken, nunca com palavra fora do nome dela que
    seja prenome do lexico (o prenome composto de outra pessoa: "FULANA JOSE
    DA SILVA" com "FULANA TERCIANA DA SILVA"), nunca o "inscrito na OAB"."""
    pessoas = {tok: nome for tok, info in mapa["tokens"].items() if (nome := _nome_do_token(info))}
    donos_do_prenome: dict[str, list[str]] = {}
    for tok, nome in pessoas.items():
        sig = _significativas(nome)
        if sig:
            donos_do_prenome.setdefault(sig[0], []).append(tok)
    for tok, nome in pessoas.items():
        if not tok.startswith(_PREFIXOS_DE_PARTE):
            continue
        prenome = _significativas(nome)[0]
        if len(prenome) < 3 or donos_do_prenome.get(prenome) != [tok]:
            continue
        for w in RE_PALAVRA.finditer(texto):
            if normalizar(w.group()) != prenome:   # 0.5.22 (#12): em qualquer caixa
                continue
            q = RE_QUALIFICACAO.match(texto, w.end())
            if not q:
                continue
            candidato = " ".join(texto[w.start():q.end("resto")].split())
            if _nome_limpo(candidato) != candidato:
                continue
            if not _sobrenome_em_comum(_significativas(candidato)[1:], _significativas(nome)[1:]):
                continue            # o mesmo prenome, sem sobrenome em comum: outra pessoa
            do_nome = {w for f in _formas(mapa["tokens"][tok]) for w in _significativas(f)}
            if any(w not in do_nome and w in PRENOMES_DO_LEXICO for w in _significativas(candidato)[1:]):
                continue            # o prenome composto de outra pessoa, que so' divide o sobrenome
            if _qualificacao_de_advogado(texto, q.end("resto")):
                continue            # o advogado substabelecido, nao a parte
            chave = normalizar(candidato)
            if any(normalizar(f) == chave for t, i in mapa["tokens"].items()
                   if t != tok and isinstance(i, dict) for f in _formas(i)):
                continue
            _acrescentar_alias(mapa, tok, candidato)


# A pessoa da linha de baixo (0.5.0): na lista de herdeiros ou no formulario
# ("Nome" / "Nome da mae"), o nome inteiro de uma PARTE no fim da linha e, na
# linha seguinte, 1 a 3 palavras com maiuscula que terminam num sobrenome
# dela — outra pessoa, que vira tóken proprio ([[PESSOA_n]]) aqui, ANTES da
# troca: a cauda nao a funde na parte (a reversao a apagava) e ela nao fica
# em claro. Nunca o logradouro ("RUA DOS SICRANOS"), nunca quem abre com o
# prenome de alguem do mapa (a mesma pessoa noutra grafia, ou um homonimo:
# o prenome ficaria ambiguo), nunca o que _nome_limpo recusa.
_PREFIXO_DA_LINHA_DE_BAIXO = "PESSOA"
_LOGRADOUROS = {"rua", "avenida", "av", "travessa", "rodovia", "alameda", "estrada", "beco", "praca", "largo"}


def _descobrir_linha_de_baixo(texto: str, mapa: dict) -> None:
    pessoas = {tok: nome for tok, info in mapa["tokens"].items() if (nome := _nome_do_token(info))}
    prenomes = {sig[0] for nome in pessoas.values() if (sig := _significativas(nome))}
    ws = [(m.start(), m.end(), m.group(), normalizar(m.group())) for m in RE_PALAVRA.finditer(texto)]
    for tok, nome in pessoas.items():
        alvo, sobrenomes = normalizar(nome).split(), set(_significativas(nome)[1:])
        k = len(alvo)
        if not tok.startswith(_PREFIXOS_DE_PARTE) or k < 2 or not sobrenomes:
            continue
        for i in range(len(ws) - k):
            if [w[3] for w in ws[i:i + k]] != alvo or any(texto[ws[x][1]:ws[x + 1][0]].strip()
                                                           for x in range(i, i + k - 1)):
                continue
            fim = i + k - 1
            entre = texto[ws[fim][1]:ws[fim + 1][0]]
            if entre.strip() or entre.count("\n") != 1:
                continue            # so' a quebra de linha separa o nome da parte da linha de baixo
            j, contadas, ate = fim + 1, 0, None
            while j < len(ws) and contadas < 3:
                separador = texto[ws[j - 1][1]:ws[j][0]]
                if j > fim + 1 and (not separador or separador.strip() or "\n" in separador):
                    break           # a linha de baixo, so' ela
                orig, norm = ws[j][2], ws[j][3]
                if norm in _CONECTIVOS_DA_CAUDA and j > fim + 1:
                    j += 1
                    continue
                # 0.5.22 (auditoria da caixa, #13): sem a maiuscula — o sobrenome da parte no fim e' a prova; a
                # palavra do meio so' passa sem cara de frase
                if len(norm) < 2 or (norm not in sobrenomes and _parada(norm, contadas, frozenset(), TODA_A_LINGUA) != CONTINUA):
                    break
                contadas += 1
                if norm in sobrenomes:
                    ate = j
                j += 1
            if ate is None:
                continue
            candidato = " ".join(texto[ws[fim + 1][0]:ws[ate][1]].split())
            if ws[fim + 1][3] in _LOGRADOUROS or ws[fim + 1][3] in prenomes or _nome_limpo(candidato) != candidato:
                continue
            if incertos.decisao(mapa, candidato) != incertos.NAO_NOME:
                _registrar_descoberta(mapa, _PREFIXO_DA_LINHA_DE_BAIXO, candidato, "pessoa da linha de baixo")


# A pessoa do formulario (provas documentais, 03/10/2026): no contracheque, na folha de pagamento, no recibo, na
# ficha de registro, no TRCT e no atestado, o nome logo depois do rotulo ("Nome:", "Funcionário:", "Empregado:",
# "Colaborador:", "Nome da mãe:", "Filiação:", "Dependente:", "Paciente:", "Médico:"...) ou seguido do CRM — o
# colega da folha, a mae e os dependentes da ficha, o medico do atestado — que nenhuma outra ancora pega. Vira
# [[PESSOA_n]] ANTES da troca (a parte da capa vira alias do codigo dela: _registrar_descoberta). O nome e' cortado
# no rotulo seguinte da mesma linha ("Cargo", "Admissão", "CPF"...). So' a montagem das pecas de prova a chama.
_ROTULO_DE_PESSOA = (r"(?i:nome(?:\s+d[oa]\s+(?:empregad[oa]|funcion[aá]ri[oa]|colaborador[a]?|trabalhador[a]?"
                     r"|segurad[oa]|paciente|pai|m[ãa]e|c[ôo]njuge|dependente|benefici[aá]ri[oa]|m[ée]dic[oa]))?"
                     r"|funcion[aá]ri[oa]|empregad[oa]|colaborador[a]?|trabalhador[a]?|benefici[aá]ri[oa]"
                     r"|segurad[oa]|paciente|filia[çc][ãa]o|pai|m[ãa]e|c[ôo]njuge|dependentes?"
                     r"|m[ée]dic[oa](?:\s+respons[aá]vel)?|recebedor[a]?)")
RE_ROTULO_DE_PESSOA = re.compile(r"(?<![^\W\d_])" + _ROTULO_DE_PESSOA + r"[ \t]*[:\-–][ \t]*")
# o rotulo seguinte do formulario, na mesma linha: o nome acaba antes dele
_ROTULOS_SEGUINTES = {"cargo", "funcao", "admissao", "demissao", "matricula", "cpf", "pis", "pasep", "nit", "ctps",
                      "rg", "salario", "setor", "departamento", "competencia", "referencia", "cbo", "banco",
                      "agencia", "conta", "data", "nascimento", "endereco", "lotacao", "empresa", "cnpj", "horario",
                      "local", "filial", "codigo", "cod", "total", "valor", "crm", "sexo", "estado", "nacionalidade",
                      "naturalidade", "escolaridade", "registro", "periodo", "mes", "ano", "folha", "cid", "dias"}


def _corta_no_rotulo_seguinte(nome: str) -> str:
    partes = nome.split()
    for i, w in enumerate(partes):
        if i and normalizar(w) in _ROTULOS_SEGUINTES:
            return " ".join(partes[:i])
    return nome


# --- 0.5.19: o nome depois da ancora, lido sem a caixa (auditoria da caixa, #1) --------------------------------
# A palavra da frase que vem logo depois do nome e nunca e' nome (artigo, pronome, conjuncao, verbo curto): para a
# leitura. Os descartaveis (_PREFIXOS_DESCARTAVEIS, fora os conectivos de nome) tambem.
_PALAVRAS_DA_FRASE = {
    "e", "que", "se", "nao", "sim", "foi", "era", "eram", "sao", "esta", "estava", "tem", "tinha", "ha", "havia",
    "disse", "diz", "fez", "viu", "sabe", "sabia", "pode", "podia", "deve", "vai", "ia", "ja", "mas", "nem", "ou",
    "pois", "porque", "quando", "como", "onde", "quem", "cujo", "cuja", "seu", "sua", "seus", "desde", "ainda",
    "tambem", "apenas", "somente", "sempre", "nunca", "muito", "mais", "menos", "bem", "aqui", "ali", "la", "hoje",
    "ontem", "entao", "depois", "antes", "agora", "durante", "contra", "perante",
    "suas", "ele", "ela", "eles", "elas", "este", "esta", "esse", "essa", "isso", "isto", "aquele", "aquela",
    "nos", "nas", "pelo", "pela", "pelos", "pelas", "num", "numa", "sobre", "entre", "apos", "ate", "sem", "sob",
    "conforme", "fls", "fl", "pag", "id", "brasileiro", "brasileira", "casado", "casada", "solteiro", "solteira",
    "divorciado", "divorciada", "viuvo", "viuva", "residente", "domiciliado", "domiciliada", "portador",
    "portadora", "inscrito", "inscrita", "qualificado", "qualificada", "ouvido", "ouvida", "presente", "ausente",
    "paradigma", "paradigmas", "informante", "depoente",
    # o que a medicao no acervo achou depois de "perito,"/"testemunha," sem ser nome (vocabulario comum de 25+
    # processos, fora do ranking do IBGE)
    "ser", "ter", "sera", "seja", "sejam", "tenha", "tenham", "deva", "devem", "devera", "deverao", "podera",
    "poderao", "foram", "vem", "cada", "todo", "toda", "todos", "todas", "outro", "outra", "outros", "outras",
    "neste", "nesta", "nesse", "nessa", "deste", "desta", "desse", "dessa", "dele", "dela", "deles", "delas",
    "quanto", "quanta", "via", "vias", "atraves", "acerca", "abaixo", "acima", "inclusive",
    "embora", "senao", "fora", "dentre", "caso", "acaso", "cujos", "cujas", "alguns", "algumas", "nenhum",
    "nenhuma", "pouco", "vez", "modo", "tipo", "prazo", "forma", "formas", "fato", "ordem", "prova", "lei", "teor",
    "dez", "comp", "mesmo", "mesma", "mesmos", "mesmas", "proprio", "propria",
    # rodada de correcao 1 (I3): o verbo e o termo do depoimento logo depois de "testemunha"/"perito"/"paradigma"
    # ("a testemunha nada soube informar", "testemunha relata horas extras") e o cargo comum ("paradigma: vendedor
    # externo"); "vou" e afins, que cortam o contato da conversa (M3)
    "nada", "soube", "sabe", "sabia", "relata", "relatou", "relatam", "afirma", "afirmou", "afirmam", "confirma",
    "confirmou", "confirmam", "nega", "negou", "negam", "informa", "informou", "declara", "declarou", "esclarece",
    "esclareceu", "reconhece", "reconheceu", "aduz", "alega", "alegou", "explica", "explicou", "conta", "contou",
    "trabalha", "trabalhou", "trabalhava", "recebe", "recebia", "recebeu", "labora", "laborava", "exerce",
    "exercia", "presta", "prestava", "compareceu", "comparece", "nao", "vou", "vai", "vamos", "estou", "estamos",
    "chego", "chegou", "chegar", "tou", "ta", "to", "pra", "pro", "aqui", "ai", "obrigado",
    "atesta", "atestou", "atestamos", "constata", "constatou", "recomenda", "recomendou", "solicita",
    # rodada de correcao 6: a frase do atestado e a remissao do formulario ("vide ficha anexa", "ver verso")
    "paciente", "necessita", "necessitou", "atendido", "atendida", "permanecer", "permanece", "afastado",
    "afastada", "deve", "devera", "fins", "trabalhistas", "trabalhista", "repouso", "vide", "ver", "verso",
    "anexa", "anexo", "anexas", "anexos", "ficha", "menor", "impubere", "idem", "supra", "retro",
    "vendedor", "vendedora", "externo", "externa", "interno", "interna", "auxiliar", "administrativo",
    "administrativa", "operador", "operadora", "plantonista", "atendente", "conferente", "ajudante", "servente",
    "estoquista", "caixa", "repositor", "repositora", "balconista", "pedido", "entregas", "entrega", "compra",
    "compras", "zona", "sul", "norte", "leste", "oeste",
    # rodada de correcao 2 (M-b): a mensagem do sistema do aplicativo ("voce apagou esta mensagem")
    "voce", "apagou", "apagada", "apagado", "eliminou", "excluiu", "removeu", "adicionou", "saiu", "entrou"}
# O fim de palavra da lingua (verbo, adverbio, substantivo e adjetivo derivados) que, fora do ranking do IBGE e das
# listas de nomes, para a leitura: "o perito carlos werle apresentou o laudo" para no "apresentou". So' em palavra
# de 5+ letras.
_FINS_DA_LINGUA = (
    "ou", "aram", "eram", "iram", "ava", "avam", "ia", "iam", "ndo", "ado", "ada", "ados", "adas", "ido", "ida",
    "idos", "idas", "ar", "er", "ir", "mente", "cao", "coes", "dade", "ente", "ante", "encia", "ancia", "ivel",
    "avel", "ismo", "ista", "oria", "orio", "eu", "iu", "al", "ais", "oso", "osos", "mento", "mentos", "eza",
    "ssem", "sse")
# Sem prova do nome (o comeco que nao e' prenome provado nem tem sobrenome do ranking), o candidato com cara de
# lingua comum e' recusado: alem dos fins acima, o plural, o adjetivo e o verbo em -em/-am ("eventos diferentes",
# "processos", "definitiva", "possuem"). So' fora do ranking e em palavra de 5+ letras.
_FINS_DA_LINGUA_SEM_PROVA = _FINS_DA_LINGUA + (
    "os", "as", "es", "ivo", "iva", "ivos", "ivas", "em", "am", "oes", "eis")
# A palavra que fica no comeco do candidato sem tirar dele a ancora: o tratamento, o titulo da funcao, o
# qualificador do perito, o "Nome Completo" do formulario, o descartavel e a parte ("testemunha do autor Fulano")
_PULAVEIS_ANTES_DO_NOME = (_PREFIXOS_DESCARTAVEIS | _TITULOS_ANTES_DO_NOME | _QUALIFICADORES_DO_PERITO
                           | {"nome", "completo", "doutor", "doutora", "autor", "autora", "reu", "re", "reclamante",
                              "reclamantes", "reclamada", "reclamadas", "reclamado", "reclamados", "parte",
                              "testemunha", "testemunhas", "perito", "perita", "paradigma", "paradigmas"}
                           | _QUALIDADES_DO_SOCIO)
# a preposicao logo antes da palavra: o que vem depois dela e' o objeto ("perito nomeado para avaliacao de
# Adicional de Insalubridade", "perito do juizo"), nao o nome
_PREPOSICOES_ANTES_DO_NOME = {"da", "de", "do", "das", "dos", "para", "em", "no", "na", "nos", "nas", "ao", "aos",
                              "com", "sobre", "pelo", "pela"}
_RE_PALAVRA_DO_NOME = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ']*")
_RE_CONTINUA_A_LISTA = re.compile(r"[ \t]*(?:[,;][ \t]*(?:\n[ \t]*)?|[ \t]+(?i:e)[ \t]+|\n[ \t]*(?i:e)[ \t]+)")
_RE_SEPARADOR_DO_NOME = re.compile(r"\.?[ \t]*(?:\n[ \t]*)?")
MAX_PALAVRAS_DO_NOME = 5
# o item da lista que acaba limpo: outro separador, o fim da frase, a quebra de linha ou o fim do texto
_RE_FIM_DO_ITEM = re.compile(r"[ \t]*(?:[,;.\n]|(?i:e)[ \t]|$)")
_RE_FIM_DO_APOSTO = re.compile(r"[ \t]*[,.:]")      # o ":" do depoimento tambem fecha (medicao de vazamento)


def _no_ranking(n: str) -> bool:
    return (n in PRENOMES_DO_LEXICO or n in SOBRENOMES_DO_LEXICO or bool(frequencia_de_prenome(n))
            or bool(frequencia_de_sobrenome(n)))


CONTINUA, PARADA_FRACA, PARADA_FORTE = 0, 1, 2


@lru_cache(maxsize=1)
def _frase_no_ranking() -> frozenset:
    """As palavras de _PALAVRAS_DA_FRASE que estao no ranking do IBGE (prenome ou sobrenome), derivadas do ranking
    na primeira chamada (rodada de correcao 2, I-a: "sabe" tem 11.250 pessoas como sobrenome, "norte" 2.716)."""
    return frozenset(w for w in _PALAVRAS_DA_FRASE if w not in CONECTIVOS and _no_ranking(w))


def _parada(n: str, antes: int, comuns, lingua=None) -> int:
    """Se a palavra normalizada `n` encerra o nome lido (com `antes` palavras significativas ja' lidas). FORTE: o
    vocabulario que nunca e' nome (o de _nome_no_rotulo, mais a frase). FRACA (fora do ranking do IBGE e das
    listas de nomes): o fim de palavra da lingua e, quando o chamador tem, a palavra comum dos autos (`comuns`) —
    a do ranking so' com 2+ palavras antes, como no interlocutor ("Fulano Dias" fica inteiro). A fraca entre duas
    palavras de nome nao para (_ler_nome). Nunca a caixa. `lingua` (etapa 2, medicao no acervo): as palavras que
    o processo escreve em minusculas fora de nome (leitura_ocr.vocabulario); com ela, o fim de palavra da lingua
    so' encerra a palavra que o processo usa como palavra — o sobrenome raro ("... Cantar", "... Furtado") que
    o processo nunca escreve assim fica no nome."""
    if n in _PALAVRAS_DA_FRASE and n not in _NUNCA_NOME and n in _frase_no_ranking():
        # rodada de correcao 2 (I-a): a palavra da frase que tambem e' prenome ou sobrenome do ranking ("Sabe",
        # "Norte", "Pra") para FRACA — entre duas palavras do ranking fica no nome (_ler_nome)
        return PARADA_FRACA
    if len(n) < 2 or n in _NUNCA_NOME or n in _PALAVRAS_DA_FRASE or n in _TELA_DO_APLICATIVO \
            or (n in _PREFIXOS_DESCARTAVEIS and n not in CONECTIVOS) or n in _TITULOS_ANTES_DO_NOME:
        return PARADA_FORTE
    ranking = _no_ranking(n)
    if not ranking and (n in _SAUDACAO_OU_TERMO_DO_TRABALHO or n in _CARGO_LUGAR_OU_PARENTESCO
                        or n in _ROTULOS_SEGUINTES):
        return PARADA_FORTE
    if ranking:
        return PARADA_FRACA if (n in comuns and antes >= 2) else CONTINUA
    if n in comuns:
        return PARADA_FRACA
    if len(n) >= 5 and n.endswith(_FINS_DA_LINGUA):
        # rodada de correcao 1 (I2): sem o vocabulario do processo, so' o verbo conjugado encerra — o sobrenome
        # raro ("Kroeger", "Wolkmer") com cara de infinitivo ou de substantivo fica no nome (proteger a mais)
        if (n in lingua) if lingua is not None else n.endswith(_FINS_DE_VERBO_CONJUGADO):
            return PARADA_FRACA
    return CONTINUA


class _TodaALingua:
    """O `lingua` que contem toda palavra: o fim de palavra da lingua sempre encerra (a regra de antes da rodada de
    correcao 1, para quem nao le' nome depois de ancora: a cauda, o prefixo, a linha de baixo, o vocabulario)."""
    def __contains__(self, _palavra) -> bool:
        return True


TODA_A_LINGUA = _TodaALingua()
_FINS_DE_VERBO_CONJUGADO = ("ou", "aram", "eram", "iram", "ava", "avam", "iam", "ndo", "eu", "iu")


def _ler_nome(texto: str, ini: int, comuns=frozenset(), lingua=None, aberto: bool = False) -> tuple[int, int] | None:
    """(ini, fim) do nome que comeca na palavra em `ini`, lido sem a caixa: palavras separadas so' por espaco
    (a inicial com ponto, "Maria S. Souza", passa; uma quebra de linha, so' antes de sobrenome do ranking), os
    conectivos de nome no meio, ate' a parada (_parada) ou MAX_PALAVRAS_DO_NOME palavras significativas. A
    parada fraca logo seguida, na mesma linha, de palavra do ranking que nao para e' do nome ("Beltrana
    Exemplar Souza"). None se a primeira palavra ja' para."""
    pos, sig, fim = ini, 0, None
    primeira = _RE_PALAVRA_DO_NOME.match(texto, ini)
    aberto = aberto or bool(primeira and _prenome_provado(normalizar(primeira.group())))
    while sig < MAX_PALAVRAS_DO_NOME:
        m = _RE_PALAVRA_DO_NOME.match(texto, pos)
        if not m:
            break
        n = normalizar(m.group()).replace("'", "")
        inicial = len(n) == 1 and n not in ("a", "e", "o") and sig > 0 and texto.startswith(".", m.end())
        sep = _RE_SEPARADOR_DO_NOME.match(texto, m.end()).group()
        if texto[m.end():m.end() + 3].lstrip(" \t").startswith(":") and (
                not sig or not _no_ranking(n) or _parada(n, sig, comuns, TODA_A_LINGUA) != CONTINUA
                or n in _PALAVRAS_DA_FRASE or n in _SAUDACAO_OU_TERMO_DO_TRABALHO or n in _ROTULOS_SEGUINTES
                or n in _CARGO_LUGAR_OU_PARENTESCO or n in _NUNCA_NOME or n in _TELA_DO_APLICATIVO):
            # rodada de correcao 5: a palavra seguida de ":" e' rotulo ("Dia: 5"); medicao de vazamento: o
            # sobrenome do ranking que nao e' palavra de lista fecha o nome ("... Pereira Lima: que trabalhava")
            break
        if n in CONECTIVOS and n != "e":
            if sig == 0:
                break               # o nome nunca comeca no conectivo
        elif not inicial:
            parada = _parada(n, sig, comuns, lingua)
            if parada == PARADA_FORTE and aberto and sig and _nome_do_ranking(n):
                parada = PARADA_FRACA   # rodada de correcao 4: a palavra do ranking dentro do nome aberto
            if parada == PARADA_FRACA and sig and sep and not sep.strip(" \t"):
                seguinte = _RE_PALAVRA_DO_NOME.match(texto, m.end() + len(sep))
                ns = normalizar(seguinte.group()) if seguinte else ""
                if ns and _no_ranking(ns) and _parada(ns, sig + 1, comuns, lingua) == CONTINUA:
                    parada = CONTINUA   # entre duas palavras de nome
            if (parada == PARADA_FRACA and sig >= 1 and aberto
                    and (n in _frase_no_ranking() or _nome_do_ranking(n))
                    and (n in SOBRENOMES_DO_LEXICO or frequencia_de_sobrenome(n) or frequencia_de_prenome(n))
                    and not _RE_PALAVRA_DO_NOME.match(texto, m.end() + len(re.match(r"[ \t]*", texto[m.end():]).group()))):
                parada = CONTINUA       # rodada de correcao 2 (I-a): o sobrenome do ranking no fim ("Joana Pereira Norte,")
            if parada != CONTINUA:
                break
            sig += 1
            fim = m.end()
        if sep.strip(" \t\n") and not inicial:
            break                   # o ponto so' depois da inicial ("S.")
        if not sep.replace(".", ""):
            break                   # pontuacao, digito ou fim do texto logo depois
        if "\n" in sep:
            seguinte = _RE_PALAVRA_DO_NOME.match(texto, m.end() + len(sep))
            ns = normalizar(seguinte.group()) if seguinte else ""
            if not (sig and ns and (ns in SOBRENOMES_DO_LEXICO or frequencia_de_sobrenome(ns))
                    and _parada(ns, sig, comuns, lingua) == CONTINUA):
                break               # a linha de baixo, so' com o sobrenome do ranking
        pos = m.end() + len(sep)
    return (ini, fim) if fim else None


LIVRE_NAO, LIVRE_FRACO, LIVRE_FORTE = 0, 1, 2
_RE_SO_TRATAMENTO = re.compile(r"[ \t]*(?:(?i:sra?|dra?|doutora?)\.?[ \t]+)?")
_RE_TRATAMENTO_COM_PONTO = re.compile(r"(?i)\b(sra?|dra?)\.")


def _comeco_livre(enchimento: str) -> tuple[int, bool]:
    """(livre, depois_de_preposicao) para o comeco de nome logo depois de `enchimento` (o texto entre a ancora e a
    palavra). As palavras depois da ultima pontuacao tem de ser todas pulaveis (o tratamento, o titulo, o
    descartavel, a parte, a inicial solta); entao o comeco e' FORTE logo depois da ancora, do ":", do "-", do ")"
    ou do tratamento, e FRACO depois da virgula, do ponto ou do ponto-e-virgula (la' vem tambem a frase: "o
    perito, no prazo de"). Senao, NAO: o nome so' comeca num prenome provado."""
    enchimento = _RE_TRATAMENTO_COM_PONTO.sub(r"\1 ", enchimento)
    pedacos = re.split(r"([:;,.\-–)])", enchimento)
    trecho, pontuacao = pedacos[-1], (pedacos[-2] if len(pedacos) > 1 else "")
    palavras = [normalizar(w) for w in _RE_PALAVRA_DO_NOME.findall(trecho)]
    preposicao = bool(palavras) and palavras[-1] in _PREPOSICOES_ANTES_DO_NOME
    if not all(w in _PULAVEIS_ANTES_DO_NOME or len(w) == 1 for w in palavras):
        return LIVRE_NAO, preposicao
    tratamento = bool(palavras) and palavras[-1] in ("sr", "sra", "dr", "dra", "doutor", "doutora")
    if tratamento or pontuacao in ("", ":", "-", "–", ")"):
        return LIVRE_FORTE, preposicao
    return LIVRE_FRACO, preposicao


def _com_cara_de_lingua(nome: str) -> bool:
    """Alguma palavra do candidato sem prova tem cara de lingua comum (fora do ranking do IBGE): o fim de palavra de _FINS_DA_LINGUA_SEM_PROVA ("eventos diferentes", "processos"). Quando a ultima palavra e'
    sobrenome do ranking, so' a primeira conta: a do meio esta' entre palavras de nome ("Beltrana Exemplar
    Souza")."""
    sig = _significativas(nome)
    fins = _FINS_DA_LINGUA_SEM_PROVA
    if len(sig) >= 2 and (sig[-1] in SOBRENOMES_DO_LEXICO or frequencia_de_sobrenome(sig[-1])) \
            and not _infinitivo_raro(sig[-1]):
        sig = sig[:1]
        # rodada de correcao 5: com o sobrenome do ranking no fim, o prenome raro em "-ia" e' nome ("Zorbelia")
        fins = tuple(f for f in fins if f != "ia")
    return any((not _no_ranking(w) or _infinitivo_raro(w)) and len(w) >= 5 and w.endswith(fins) for w in sig)


# rodada de correcao 1 (I3): "informar" esta' no ranking de sobrenomes (1.116 pessoas); o sobrenome de verdade com
# cara de infinitivo ("Aguilar", "Salazar", "Schneider") tem dezenas de milhares. Abaixo de 2.000 no ranking de
# prenomes e no de sobrenomes, a palavra em -ar/-er/-ir nao e' salva pelo ranking (medido: so' "Olivier", 1.073,
# fica abaixo entre os sobrenomes desse fim que a sonda conferiu)
FREQUENCIA_BAIXA = 2000


def _infinitivo_raro(w: str) -> bool:
    return w.endswith(("ar", "er", "ir")) and frequencia_de_sobrenome(w) < FREQUENCIA_BAIXA \
        and frequencia_de_prenome(w) < FREQUENCIA_BAIXA


def _depois_dos_dois_pontos(texto: str, fim: int) -> int | None:
    """A posicao logo depois do ":" que vem a ate' 30 caracteres de `fim`, na mesma linha (a ata: "Testemunha da
    reclamada - ALFA TELECOM LTDA: Fulana")."""
    resto = texto[fim:fim + 31].split("\n")[0]
    return fim + resto.index(":") + 1 if ":" in resto else None


def _nomes_depois_da_ancora(texto: str, pos: int, comuns=frozenset(), lista: bool = False, lingua=None,
                            enchimento: bool = True, perito: bool = False) -> list[tuple[int, int, str]]:
    """[(ini, fim, nome)] lidos depois da ancora que termina em `pos`. O comeco e' a primeira palavra, dentro do
    enchimento (RE_ENCHIMENTO_DA_ANCORA, com ate' 2 quebras de linha; sem ele, so' logo depois), cuja leitura
    (_ler_nome) da' um nome (_nome_limpo) e que e' comeco livre (_comeco_livre) ou prenome provado — a palavra
    vetada no comeco faz recomecar na seguinte (#2). No perito, nunca logo depois de preposicao ("perito do
    juizo", "nomeado para avaliacao de ...") e a firma depois do nome so' corta ("FULANO BELTRANO ENGENHARIA
    LTDA"); nas demais, a pessoa juridica (_pj_na_ancora, tambem com o sufixo logo depois) e' recusada e a
    procura recomeca depois do ":" da ata. Com `lista`, os nomes seguintes separados por virgula,
    ponto-e-virgula ou "e" (em qualquer caixa)."""
    achados: list[tuple[int, int, str]] = []
    base = pos
    for _volta in range(3):
        pulo = None
        for w in _RE_PALAVRA_DO_NOME.finditer(texto, base):
            meio = texto[base:w.start()]
            if enchimento and (not RE_ENCHIMENTO_DA_ANCORA.fullmatch(meio) or meio.rstrip().count("\n") > 2):
                break
            if not enchimento and not _RE_SO_TRATAMENTO.fullmatch(meio):
                break               # o rotulo do formulario: o nome logo depois (so' o tratamento no meio)
            if w.start() > base and texto[w.start() - 1] in "'’":
                continue
            livre, depois_de_preposicao = _comeco_livre(meio)
            if perito and depois_de_preposicao:
                continue
            lido = _ler_nome(texto, w.start(), comuns, lingua, aberto=livre == LIVRE_FORTE)
            if not lido:
                continue
            ini, fim = lido
            if not perito and _pj_na_ancora(texto, ini, fim):
                pulo = _depois_dos_dois_pontos(texto, fim)
                if pulo is None:
                    # rodada de correcao 1: sem o ":", o nome depois da virgula que fecha a empresa ("TRANSPORTES
                    # ALFA LTDA, preposto Fulano Beltrano"), so' com prova (o comeco depois da virgula e' fraco)
                    resto = texto[fim:fim + 41].split("\n")[0]
                    pulo = fim + resto.index(",") + 1 if "," in resto else None
                break
            nome = _nome_limpo(" ".join(texto[ini:fim].split()),
                               aberto=livre == LIVRE_FORTE or _prenome_provado(normalizar(w.group())))
            if not nome:
                continue
            provado = _prenome_provado(w.group()) or _nome_provado(nome)
            # sem prova: so' no comeco livre de verdade (logo depois da ancora, do ":" ou do tratamento) e sem
            # cara de lingua comum; depois da virgula, so' o aposto que fecha em virgula ou ponto (rodada de
            # correcao 1, I1: "Testemunha arrolada pela reclamada, Fulana Rara Sobrenome, ouvida")
            aposto = (livre == LIVRE_FRACO and meio.rstrip().endswith(",") and _RE_FIM_DO_APOSTO.match(texto, fim))
            if not provado and (not (livre == LIVRE_FORTE or aposto) or _com_cara_de_lingua(nome)):
                continue
            achados.append((ini, fim, nome))
            break
        if achados or pulo is None:
            break
        base = pulo
    while lista and achados:
        sep = _RE_CONTINUA_A_LISTA.match(texto, achados[-1][1])
        lido = _ler_nome(texto, sep.end(), comuns, lingua) if sep else None
        if not lido:
            break
        ini, fim = lido
        nome = _nome_limpo(" ".join(texto[ini:fim].split()),
                           aberto=_prenome_provado(normalizar(texto[ini:fim].split()[0])))
        if not nome or _pj_na_ancora(texto, ini, fim):
            break
        if not _nome_provado(nome) and (_com_cara_de_lingua(nome) or not _RE_FIM_DO_ITEM.match(texto, fim)):
            break                   # sem prova, so' o item que acaba na lista ("Fulana Tal, vendedora do mesmo setor")
        achados.append((ini, fim, nome))
    return achados


def descobrir_pessoas_de_formulario(texto: str, mapa: dict, conferir_nome=None, lingua=None) -> None:
    """Registra no mapa a pessoa do formulario (rotulo + nome, ou nome + CRM) das pecas de prova (provas.py)."""
    if not nivel_mod.nomes_em_codigo(nivel_mod.do_mapa(mapa)):
        return                      # publico: nenhuma pessoa entra no mapa
    # linha a linha: o formulario poe um rotulo por linha, e o nome nunca continua na linha de baixo
    for linha in texto_limpo(texto).splitlines():
        _descobrir_na_linha_de_formulario(linha, mapa, conferir_nome, lingua)


def _nome_provado(nome: str) -> bool:
    """Ha' prova do nome sem a caixa: a primeira palavra significativa e' prenome provado (_prenome_provado: a
    lista escrita 'a mao ou o ranking de prenomes do IBGE, fora o prenome que e' palavra comum). O sobrenome do
    ranking sozinho nao prova: o ranking tem palavra comum ("nova", "campos", "dias")."""
    sig = _significativas(nome)
    return len(sig) >= 2 and _abre_nome(sig)     # rodada de correcao 1: "Rosa Maria Pires" tambem


def _conferido(candidato: str, conferir_nome=None) -> tuple[str | None, float | None]:
    """(zona, p de pessoa) da conferencia injetada (jev_nomes.Conferencia) para um candidato que ja' passou nos
    vetos e nas paradas da regra local. Nunca vai: sem conferencia, o separador de dois nomes, o dado sensivel ou o
    endereco, mais de 5 palavras significativas. Zona: incertos.NOME, incertos.NAO_NOME ou None (o meio, a falha,
    nada consultado). A conferencia nunca promove a nome o que a regra veta (o Jev deu 0,99 de pessoa para "Danos
    Morais"): so' decide entre o que a regra deixou em duvida."""
    if (conferir_nome is None or tem_separador(candidato) or sensivel_ou_endereco(candidato)
            or len(_significativas(candidato)) > 5):
        return None, None
    try:
        veredito = conferir_nome(candidato)
    except Exception:  # noqa: BLE001 — a conferencia nunca derruba a montagem
        veredito = None
    if veredito is None:
        return None, None
    zona = getattr(veredito, "zona", None)
    return (zona if zona in (incertos.NOME, incertos.NAO_NOME) else None), round(float(veredito.p_pessoa), 4)


def _decidir_ancorado(mapa: dict, nome: str, origem: str, conferir_nome=None) -> bool:
    """O nome que uma ancora explicita de pessoa achou entra no mapa? A decisao do juiz (incertos.py) antes de tudo:
    "nao_nome" descarta, "nome" registra. Com prova independente da caixa (_nome_provado), registra. Senao, a
    conferencia do Jev (etapa 2, decisao do juiz de 05/10/2026), quando ligada: pessoa com p alta registra sem
    anotar; expressao com p alta descarta sem anotar (a "confusao com expressao"); no meio, sem conferencia ou com
    falha, a ancora basta para proteger — o nome vai em codigo e fica anotado como incerto, com a probabilidade."""
    decidido = incertos.decisao(mapa, nome)
    if decidido == incertos.NAO_NOME:
        return False
    if normalizar(nome.split()[0]) in (_PULAVEIS_ANTES_DO_NOME | _PAPEIS_DE_OUTRA_PESSOA) - CONECTIVOS:
        return False            # rodada de correcao 2 (I-b): o valor nunca comeca por papel ou palavra pulavel
    if decidido == incertos.NOME or _nome_provado(nome):
        return True
    zona, p = _conferido(nome, conferir_nome)
    if zona == incertos.NAO_NOME:
        return False
    if zona != incertos.NOME:
        incertos.registrar(mapa, nome, origem, em_codigo=True, jev=p)
    return True


def _registrar_ancorado(mapa: dict, prefixo: str, nome: str, papel: str, origem: str,
                        conferir_nome=None) -> str | None:
    """Registra o nome que uma ancora explicita de pessoa achou (testemunha, perito, paradigma, rotulo de
    formulario, CRM), se _decidir_ancorado o aceita."""
    if not _decidir_ancorado(mapa, nome, origem, conferir_nome):
        return None
    return _registrar_descoberta(mapa, prefixo, nome, papel)


# O CRM do atestado (auditoria da caixa, #5): o nome antes dele comeca no tratamento ("Dr.", "Dra.", "Doutor") ou,
# sem ele, no primeiro prenome provado das ate' 5 palavras significativas antes do CRM — nunca na palavra comum de
# antes ("AFASTAMENTO DR FULANO DE TAL CRM"); sem tratamento nem prenome, as ate' 3 ultimas, como incerto.
# rodada de correcao 1 (I3): o servico de saude antes do CRM nao e' o nome do medico
_SERVICO_DE_SAUDE = {"pronto", "socorro", "plantao", "plantonista", "atendimento", "emergencia", "clinica",
                     "hospital", "hospitalar", "ambulatorio", "upa", "posto", "unidade", "consultorio", "setor",
                     "servico", "medicina", "medico", "medica", "responsavel", "dia",
                     # rodada de correcao 2 (M-a): o termo clinico do atestado
                     "dor", "dores", "lombar", "lombares", "lombalgia", "coluna", "cervical", "cervicalgia",
                     "toracica", "joelho", "ombro", "punho", "fratura", "lesao", "entorse", "febre", "gripe",
                     "atestado", "afastamento", "repouso", "doenca", "cid", "consulta", "exame"}
RE_CRM = re.compile(r"(?i)(?<![^\W\d_])crm(?![^\W\d_])")
_TRATAMENTO_DO_MEDICO = {"dr", "dra", "doutor", "doutora"}
_SEPARADOR_ANTES_DO_CRM = re.compile(r"[ \t]*[-–,/]?[ \t]*$")
_PALAVRAS_ANTES_DO_CRM = re.compile(r"(?:[A-Za-zÀ-ÖØ-öø-ÿ']+\.?[ \t]+)*[A-Za-zÀ-ÖØ-öø-ÿ']+$")


# Rodada de correcao 5: a especialidade, o cargo e a palavra de saude entre o nome e o CRM ("Dra. Ana Costa Medica do
# Trabalho CRM", "Dr. Paulo Mendes Clinica Geral - CRM") sao puladas indo para tras; a fronteira de saude so' vale
# a' esquerda do nome
_ESPECIALIDADES = {
    "medico", "medica", "medicos", "plantonista", "clinica", "clinico", "geral", "consultorio", "central",
    "trabalho", "ortopedista", "ortopedia", "traumatologista", "traumatologia", "cardiologista", "cardiologia",
    "psiquiatra", "psiquiatria", "pediatra", "pediatria", "perito", "perita", "ginecologista", "ginecologia",
    "obstetra", "neurologista", "neurologia", "dermatologista", "oftalmologista", "otorrinolaringologista",
    "urologista", "cirurgiao", "cirurgia", "anestesista", "radiologista", "fisiatra", "reumatologista",
    "endocrinologista", "gastroenterologista", "pneumologista", "nefrologista", "oncologista", "infectologista",
    "geriatra", "psicologo", "psicologa", "fisioterapeuta", "dentista", "odontologo", "assistente", "responsavel",
    "residente", "especialista", "familia", "comunidade", "emergencia", "intensivista", "do", "da"}
_RE_PALAVRA_COM_POSICAO = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ']*")
_RE_TRATAMENTO_NO_SEGMENTO = re.compile(r"(?i)(?<![^\W\d_])(?:dra?|doutora?)\.?[ \t]+")


def _nome_colado_ao_crm(seg: str, nao_nome: set) -> tuple[list[str], bool] | None:
    """(palavras do candidato, aberto) do nome que termina logo antes do CRM em `seg` (os ate' 200 caracteres
    antes dele): indo para tras, a especialidade e a palavra de saude fora do ranking (e o separador "-", "," ou "/"
    entre elas) sao puladas; depois, as palavras do nome, so' com espaco entre elas, ate' o tratamento (que abre o
    nome), a palavra de nao-nome ou de saude fora do ranking (fronteira a' esquerda), a pontuacao ou 5 palavras."""
    toks = [(m.start(), m.end(), m.group()) for m in _RE_PALAVRA_COM_POSICAO.finditer(seg)]
    i, fim_anterior = len(toks) - 1, len(seg)
    pulaveis = (_ESPECIALIDADES | _SERVICO_DE_SAUDE | _QUALIFICADORES_DO_PERITO | _TITULOS_ANTES_DO_NOME) - {"do", "da"}
    while i >= 0:
        n = normalizar(toks[i][2])
        entre = seg[toks[i][1]:fim_anterior]
        if entre.strip(" \t-–,/") or not ((n in pulaveis and not _nome_do_ranking(n)) or (
                n in CONECTIVOS and i > 0 and normalizar(toks[i - 1][2]) in pulaveis)):
            break
        fim_anterior = toks[i][0]
        i -= 1
    if i < 0 or seg[toks[i][1]:fim_anterior].strip(" \t-–,/"):
        return None
    janela: list[str] = []
    while i >= 0:
        ini_w, fim_w, w = toks[i]
        n = normalizar(w)
        if janela:
            entre = seg[fim_w:toks[i + 1][0]]
            if entre.strip(" \t") not in ("", "."):
                break               # a pontuacao separa: o nome acabou
            if entre.strip(" \t") == "." and n not in _TRATAMENTO_DO_MEDICO and len(n) > 1:
                break
        if n in _TRATAMENTO_DO_MEDICO:
            janela.insert(0, w)
            break
        if ((n in nao_nome or n in _SERVICO_DE_SAUDE) and not _nome_do_ranking(n)) or sum(
                1 for x in janela if normalizar(x) not in CONECTIVOS) >= 5:
            break
        janela.insert(0, w)
        i -= 1
    return janela, False


def _frase_no_crm(n: str) -> bool:
    """A palavra (normalizada) de frase, de rotulo de formulario, de parada forte, de verbo conjugado ou com cara de
    lingua, fora do ranking — nunca entra no nome sem prova antes do CRM (rodada de correcao 6)."""
    if n in CONECTIVOS:
        return False
    if n in _PALAVRAS_DA_FRASE or n in _ROTULOS_SEGUINTES or _parada(n, 1, frozenset(), TODA_A_LINGUA) == PARADA_FORTE:
        return True
    return not _no_ranking(n) and len(n) >= 5 and n.endswith(_FINS_DE_VERBO_CONJUGADO + _FINS_DA_LINGUA_SEM_PROVA)


def _nome_depois_do_tratamento(seg: str) -> str | None:
    """Rodada de correcao 5: o tratamento seguido de prenome provado, com frase entre o nome e o CRM ("Dr. Joao Dias
    atesta dores no joelho CRM"): o nome lido logo depois do tratamento."""
    ultimo = None
    for m in _RE_TRATAMENTO_NO_SEGMENTO.finditer(seg):
        ultimo = m
    if not ultimo:
        return None
    primeira = _RE_PALAVRA_COM_POSICAO.match(seg, ultimo.end())
    if not primeira or not _prenome_provado(normalizar(primeira.group())):
        return None
    lido = _ler_nome(seg, primeira.start(), aberto=True)
    return _nome_limpo(" ".join(seg[lido[0]:lido[1]].split()), aberto=True) if lido else None


def _nomes_antes_do_crm(linha: str) -> list[str]:
    nao_nome = _NUNCA_NOME | _ROTULOS_SEGUINTES | (_PREFIXOS_DESCARTAVEIS - CONECTIVOS) | _QUALIFICADORES_DO_PERITO
    saida = []
    for m in RE_CRM.finditer(linha):
        # rodada de correcao 1 (M2): so' os ~200 caracteres antes do CRM (a linha longa era quadratica)
        seg = linha[max(0, m.start() - 200):m.start()]
        nome = None
        achado = _nome_colado_ao_crm(seg, nao_nome)
        if achado:
            janela = achado[0]
            normais = [normalizar(x).rstrip(".") for x in janela]
            aberto = False
            candidato = None
            if normais and normais[0] in _TRATAMENTO_DO_MEDICO:
                candidato, aberto = janela[1:], True    # com tratamento, a palavra de saude nunca recusa
                if candidato and _frase_no_crm(normalizar(candidato[0]).rstrip(".")):
                    candidato = None    # rodada de correcao 6: "Dr." seguido de verbo ou frase nao abre nome
            else:
                # o comeco no primeiro trecho que abre nome (_abre_nome), nunca numa palavra de saude ou de
                # nao-nome ("dores lombares crm")
                k = next((i for i in range(len(janela)) if normais[i] not in _SERVICO_DE_SAUDE
                          and normais[i] not in nao_nome and _abre_nome(normais[i:])), None)
                if k is not None:
                    candidato, aberto = janela[k:], True
                else:
                    # sem tratamento nem prenome (rodada de correcao 1, I3): depois da ultima palavra de saude ou
                    # de nao-nome, as ate' 3 ultimas palavras significativas, com os conectivos do meio, nunca
                    # logo depois de preposicao
                    # rodada de correcao 6: a janela tambem e' cortada na palavra de frase, de rotulo, de parada
                    # forte, no verbo conjugado e na palavra com cara de lingua ("o paciente foi atendido hoje")
                    corte = max((i + 1 for i, n in enumerate(normais)
                                 if n in _SERVICO_DE_SAUDE or n in nao_nome or _frase_no_crm(n)), default=0)
                    janela, normais = janela[corte:], normais[corte:]
                    sig = [i for i, n in enumerate(normais) if n not in CONECTIVOS]
                    if sig:
                        inicio = sig[-3] if len(sig) >= 3 else sig[0]
                        anterior = normais[inicio - 1] if inicio else _palavra_antes(seg, janela)
                        if anterior not in _PREPOSICOES_ANTES_DO_NOME:
                            candidato = janela[inicio:]
            if candidato:
                nome = _nome_limpo(" ".join(candidato), aberto=aberto)
        if not nome:
            nome = _nome_depois_do_tratamento(seg)
        if nome:
            saida.append(nome)
    return saida


def _palavra_antes(seg: str, janela: list[str]) -> str:
    """A palavra (normalizada) logo antes da janela no segmento."""
    if not janela:
        return ""
    texto = " ".join(janela)
    pos = seg.rfind(janela[0])
    antes = _RE_PALAVRA_COM_POSICAO.findall(seg[:pos]) if pos > 0 else []
    return normalizar(antes[-1]).rstrip(".") if antes and texto else ""


def _descobrir_na_linha_de_formulario(texto: str, mapa: dict, conferir_nome=None, lingua=None) -> None:
    for m in RE_ROTULO_DE_PESSOA.finditer(texto):
        # o nome logo depois do rotulo (o tratamento pulado), lido sem a caixa e cortado no rotulo seguinte
        for _ini, _fim, nome in _nomes_depois_da_ancora(texto, m.end(), enchimento=False, lingua=lingua):
            _registrar_ancorado(mapa, _PREFIXO_DA_LINHA_DE_BAIXO, nome, "pessoa do formulário", "formulário",
                               conferir_nome)
    for nome in _nomes_antes_do_crm(texto):
        _registrar_ancorado(mapa, _PREFIXO_DA_LINHA_DE_BAIXO, nome, "pessoa do formulário", "médico (CRM)",
                           conferir_nome)


# A ancora de pessoa no texto do documento de menor, sobre o texto normalizado (sem acento nem caixa): o que vem
# logo antes do nome ("Nome:", "o menor", "filho", "certidao de nascimento de") ou logo depois (", filho de",
# "nascido").
_ANCORA_ANTES_DO_NOME_DO_MENOR = (r"(?:nome(?: d[oa] [a-z]+)?|registrad[oa]|crianca|menor|filh[oa]|dependentes?"
                                  r"|beneficiari[oa]|filiacao|pai|mae|nascimento de)\s*[:\-–]?\s*")
_ANCORA_DEPOIS_DO_NOME_DO_MENOR = r"\s*,?\s*(?:filh[oa] de|nascid[oa])\b"


def _confirmado_no_texto(significativas: list[str], corpo: str) -> bool:
    """O candidato do titulo aparece no texto do documento numa ancora de pessoa, comparado sem caixa nem acento
    (os conectivos entre as palavras do nome podem variar)."""
    nome = r"(?:\s+(?:d[aeo]s?|e))*\s+".join(re.escape(w) for w in significativas)
    return re.search(r"(?<![a-z0-9])(?:" + _ANCORA_ANTES_DO_NOME_DO_MENOR + nome + r"(?![a-z0-9])|"
                     + nome + _ANCORA_DEPOIS_DO_NOME_DO_MENOR + ")", normalizar(corpo)) is not None


def _nome_no_rotulo(nome: str, comuns=frozenset(), corpo: str = "") -> bool:
    """O resto do titulo do documento de menor e' nome de pessoa. A caixa nao conta, nem para aceitar nem para
    recusar (regra do juiz, 05/10/2026: titulo em maiusculas ou com iniciais maiusculas nao e' nome proprio).
    Veto: digito, menos de 2 palavras significativas (fora dos conectivos), palavra do vocabulario que o modulo ja'
    trata como nao-nome (_NUNCA_NOME, os termos do trabalho e a saudacao, o cargo, o lugar e o parentesco, a tela
    do aplicativo, o sufixo de geracao, os rotulos de formulario, os descartaveis) ou nome de tipo de documento do
    PJe (a taxonomia). Prova, uma das tres: a primeira palavra e' prenome do lexico e nenhuma das outras e' palavra
    comum do processo (`comuns`: leitura_ocr.palavras_comuns); a primeira e' prenome do ranking do IBGE e outra
    e' sobrenome ou prenome dele (ver abaixo); ou o texto do documento (`corpo`) traz o candidato
    numa ancora de pessoa (_confirmado_no_texto). Na duvida, nao."""
    if not _passa_nos_vetos_do_rotulo(nome):
        return False
    significativas = [n for w in nome.split() if (n := normalizar(w)) not in CONECTIVOS]
    primeira, outras = significativas[0], significativas[1:]
    if primeira in PRENOMES_DO_LEXICO and not any(n in comuns for n in outras):
        return True
    # 0.5.15: o ranking do IBGE (lexico 0.2.0) reconhece o prenome que a lista escrita 'a mao nao tem. Como o
    # ranking tem palavra que tambem e' comum, pede mais: a primeira nao e' prenome-palavra-comum, nenhuma e'
    # palavra comum do processo e ao menos uma das outras e' sobrenome ou prenome do ranking
    if (frequencia_de_prenome(primeira) and primeira not in PRENOMES_PALAVRA_COMUM
            and not any(n in comuns for n in significativas)
            and any(frequencia_de_sobrenome(n) or frequencia_de_prenome(n) for n in outras)):
        return True
    return _confirmado_no_texto(significativas, corpo)


ORIGEM_ROTULO_DE_MENOR = "título do documento de menor"


def _passa_nos_vetos_do_rotulo(nome: str) -> bool:
    """Os vetos de _nome_no_rotulo, sem a prova: sem digito, 2+ palavras significativas, nenhuma do vocabulario de
    nao-nome, nao e' tipo de documento da taxonomia. So' o que passa aqui pode ir a' conferencia ou aos incertos."""
    if not nome or any(c.isdigit() for c in nome):
        return False
    nao_nome = (_NUNCA_NOME | _SAUDACAO_OU_TERMO_DO_TRABALHO | _CARGO_LUGAR_OU_PARENTESCO | _TELA_DO_APLICATIVO
                | _SUFIXOS_DE_GERACAO | _ROTULOS_SEGUINTES | (_PREFIXOS_DESCARTAVEIS - CONECTIVOS))
    significativas = [n for w in nome.split() if (n := normalizar(w)) not in CONECTIVOS]
    return len(significativas) >= 2 and not any(n in nao_nome for n in significativas)


# rodada de correcao 1 (05/10/2026): o candidato com dado sensivel (saude, violencia, gravidez...) ou endereco nunca
# vai ao Jev nem vira "incerto" com esse texto (os sinais do nivel, nivel_sinais.json, mais as palavras abaixo)
_SENSIVEL_NO_CANDIDATO = {
    "vitima", "abuso", "abusada", "abusado", "sexual", "estupro", "violencia", "agressao", "assedio", "maus", "tratos",
    "autismo", "autista", "tea", "tdah", "transtorno", "espectro", "sindrome", "deficiencia", "deficiente",
    "portador", "portadora", "doenca", "doente", "cancer", "hiv", "aids", "depressao", "ansiedade", "psicologico",
    "psicologica", "psicologo", "psicologa", "psiquiatrico", "psiquiatrica", "psiquiatra", "neurologico",
    "neurologica", "laudo", "cid", "diagnostico", "tratamento", "internacao", "internado", "internada", "hospital",
    "hospitalar", "clinica", "medico", "medica", "saude", "gravidez", "gravida", "gestante", "gestacao", "aborto",
    "obito", "falecido", "falecida", "dependencia", "drogas", "alcoolismo", "hiv"}
_ENDERECO_NO_CANDIDATO = {"rua", "avenida", "av", "travessa", "alameda", "rodovia", "estrada", "praca", "bairro",
                          "beco", "largo", "quadra", "lote", "loteamento", "condominio", "apartamento", "apto", "cep",
                          "bloco", "residencial", "logradouro", "km"}


def sensivel_ou_endereco(candidato: str) -> bool:
    """O candidato traz dado sensivel (os sinais de documento medico e de pedido sensivel do nivel, ou uma palavra
    de saude, violencia ou gravidez) ou endereco? Entao nao vai ao Jev; fica incerto (rodada de correcao 2: "Estrada",
    "Lote" e "Bloco" tambem sao sobrenomes, e o nome ficaria em claro sem aviso)."""
    texto = candidato or ""
    if nivel_mod.SINAIS["documento"].search(texto) or any(p.search(texto) for p in nivel_mod.SINAIS["pedidos"].values()):
        return True
    palavras = {normalizar(w) for w in re.findall(r"[^\W\d_]+", texto)}
    return bool(palavras & (_SENSIVEL_NO_CANDIDATO | _ENDERECO_NO_CANDIDATO))


# o que separa dois nomes num titulo: "e", "ou" e o travessao isolados, e o ponto final de uma palavra de 2+ letras
# seguido de outra ("Fulano Silva. Beltrana Silva"; "J. Silva" e "S.A." nao separam)
_SEPARADORES_DE_NOMES = {"e", "ou", "-", "–", "—"}
_RE_PALAVRA_COM_PONTO_FINAL = re.compile(r"[^\W\d_]{2,}\.")


def tem_separador(candidato: str) -> bool:
    """O candidato tem um separador de dois nomes ("e", "ou", travessao ou hifen com espaco, ponto entre palavras)?
    Esse candidato nunca vai ao Jev: juntaria dois nomes numa requisicao."""
    texto = candidato or ""
    return (any(normalizar(w) in _SEPARADORES_DE_NOMES for w in texto.split())
            or re.search(r"\s[-–—]|[-–—]\s", texto) is not None
            or re.search(r"[^\W\d_]{2,}\.\s+\S", texto) is not None
            or re.search(r"\s\.\s*[^\W\d_]", texto) is not None)       # " . " e " .Palavra" (rodada 4)


def _n_significativas(palavras: list[str]) -> int:
    return len([x for x in palavras if normalizar(x).rstrip(".") not in CONECTIVOS])


def partes_do_candidato(candidato: str) -> list[str]:
    """O candidato partido nos separadores de nomes quando eles separam trechos de 2+ palavras significativas cada
    ("Fulano Silva e Beltrana Silva" -> dois nomes): cada parte e' avaliada sozinha. A ultima parte curta volta para
    a anterior ("Maria Pereira e Silva" nao se parte)."""
    return [" ".join(p) for _sep, p in _partes_com_separadores(candidato)]


def _partes_com_separadores(candidato: str) -> list[tuple[str, list[str]]]:
    """As partes de partes_do_candidato, cada uma com o separador que a precede ("" na primeira)."""
    partes, separadores, atual = [], [], []
    for w in candidato.split():
        if normalizar(w) in _SEPARADORES_DE_NOMES and _n_significativas(atual) >= 2:
            partes.append(atual)
            separadores.append(w)
            atual = []
            continue
        atual.append(w)
        if _RE_PALAVRA_COM_PONTO_FINAL.fullmatch(w) and _n_significativas(atual) >= 2:
            atual[-1] = w[:-1]
            partes.append(atual)
            separadores.append(".")
            atual = []
    partes.append(atual)
    if len(partes) > 1 and _n_significativas(partes[-1]) < 2:
        ultima, separador = partes.pop(), separadores.pop()     # a ultima parte curta volta para a anterior
        anterior = partes.pop()
        if separador == ".":
            anterior = anterior[:-1] + [anterior[-1] + "."]
            partes.append(anterior + ultima)
        else:
            partes.append(anterior + [separador] + ultima)
    return [(sep, p) for sep, p in zip(["", *separadores], partes) if p]


def _abre_por_prenome(parte: str) -> bool:
    """A primeira palavra significativa e' predominantemente prenome: do lexico, ou mais prenome que sobrenome no
    ranking do IBGE (e nao prenome-palavra-comum)."""
    w = next((n for x in parte.split() if (n := normalizar(x)) not in CONECTIVOS), "")
    return w in PRENOMES_DO_LEXICO or (frequencia_de_prenome(w) > frequencia_de_sobrenome(w)
                                       and w not in PRENOMES_PALAVRA_COMUM)


def _nomes_que_se_abrem(candidato: str) -> list[str]:
    """Rodada de correcao 3: o candidato partido so' onde a parte seguinte abre por prenome ("Joao Silva e Ana
    Silva" -> dois nomes); a parte que nao abre por prenome fica junto da anterior (sobrenome composto)."""
    grupos: list[list[str]] = []
    for sep, palavras in _partes_com_separadores(candidato):
        if grupos and not _abre_por_prenome(" ".join(palavras)):
            anterior = grupos[-1]
            if sep == ".":
                grupos[-1] = anterior[:-1] + [anterior[-1] + "."] + palavras
            else:
                grupos[-1] = anterior + [sep] + palavras
        else:
            grupos.append(list(palavras))
    return [" ".join(g) for g in grupos]


def zona_do_candidato(candidato: str, mapa: dict, origem: str, conferir_nome=None) -> str:
    """O candidato que a regra local nao prova nem descarta (05/10/2026, pedido do juiz): "nome", "nao_nome" ou
    "incerto" (incertos.NOME, incertos.NAO_NOME, "incerto"). Primeiro a decisao do juiz (incertos.decisao); sem ela,
    a conferencia injetada (`conferir_nome(candidato)` -> veredito com `.zona` e `.p_pessoa`, ou None; o
    seletor/jev_nomes.py, so' com a opcao ligada) — sem conferencia, com falha ou na zona do meio, o candidato
    vira incerto no mapa local (incertos.registrar, em claro). Para outras descobertas reusarem."""
    from . import incertos
    decidido = incertos.decisao(mapa, candidato)
    if decidido is not None:
        return decidido
    veredito = None
    # o separador que sobrou (nao separou dois nomes), o dado sensivel e o endereco nunca vao ao Jev: incerto
    if (conferir_nome is not None and not tem_separador(candidato)
            and not sensivel_ou_endereco(candidato)):
        try:
            veredito = conferir_nome(candidato)
        except Exception:  # noqa: BLE001 — a conferencia nunca derruba a montagem
            veredito = None
    zona = getattr(veredito, "zona", None)
    if zona in (incertos.NOME, incertos.NAO_NOME):
        return zona
    incertos.registrar(mapa, candidato, origem, em_codigo=False,
                       jev=None if veredito is None else round(float(veredito.p_pessoa), 4))
    return "incerto"


PAPEL_CONFIRMADO_PELO_JUIZ = "nome confirmado pelo juiz"


def registrar_nome_confirmado(nome: str, mapa: dict) -> None:
    """O nome que o juiz confirmou (ou digitou ao corrigir) no cartao "Nomes a confirmar" entra no mapa como pessoa,
    pela rotina de registro das descobertas (a mesma pessoa ja' no mapa vira alias, nao codigo novo), para ser
    trocado em todo o dossie. Com o mapa publico, nada (fora do documento de menor, que a montagem trata dentro de
    nivel.elevado)."""
    if not nivel_mod.nomes_em_codigo(nivel_mod.do_mapa(mapa)):
        return
    limpo = " ".join((nome or "").split())
    if len(_significativas(limpo)) >= 2:
        _registrar_descoberta(mapa, _PREFIXO_DA_LINHA_DE_BAIXO, limpo, PAPEL_CONFIRMADO_PELO_JUIZ)


def descobrir_nome_do_rotulo(nome: str | None, mapa: dict, comuns=frozenset(), corpo: str = "",
                             conferir_nome=None) -> None:
    """Task 11 (calibracao do juiz, 04/10/2026): o nome que o titulo do documento de menor traz antes ou depois do
    sinal ("Certidao de nascimento - Fulaninho de Tal": nivel.nomes_no_rotulo_de_menor) entra no mapa como pessoa,
    para ser trocado no texto daquele documento — a certidao nomeia a crianca sem ancora que a descoberta conheca.
    So' o que e' nome (_nome_no_rotulo, que nao olha a caixa): o mapa nunca perde toquen, e o resto que nao e' nome
    ("frente e verso", "Copia Autenticada") viraria codigo em todo o dossie da rodada seguinte. `corpo` e' o texto
    do proprio documento. So' a montagem do documento de menor a chama (no publico, dentro de nivel.elevado); com
    o mapa publico, nada. 05/10/2026: o que passa nos vetos mas a regra nao prova vai a zona_do_candidato (a
    decisao do juiz, a conferencia do Jev injetada pela montagem, ou o registro de nome incerto); so' acrescenta."""
    if not nivel_mod.nomes_em_codigo(nivel_mod.do_mapa(mapa)):
        return
    from . import incertos
    candidato = " ".join(_sem_cabeca(texto_limpo(nome or "")))
    # rodada de correcao 2: o inteiro primeiro (a regra local e a decisao do juiz); so' o que nao se prova inteiro
    # se parte nos separadores de nomes, e o sobrenome composto nao se parte
    decidido = incertos.decisao(mapa, candidato)
    if decidido == incertos.NAO_NOME:
        return
    abertos = _nomes_que_se_abrem(candidato) if decidido is None else [candidato]
    if len(abertos) > 1:
        partes = abertos               # rodada de correcao 3: a parte que abre por prenome e' outro nome
    elif decidido == incertos.NOME or _nome_no_rotulo(candidato, comuns, corpo):
        partes = []
        limpo = _nome_limpo(candidato)
        if limpo == candidato:
            _registrar_descoberta(mapa, _PREFIXO_DA_LINHA_DE_BAIXO, limpo, "pessoa do documento de menor")
    else:
        # rodada de correcao 4: sem parte que abra por prenome nada se parte — o candidato com separador fica
        # incerto inteiro, sem ir ao Jev (zona_do_candidato)
        partes = [candidato]
    # rodada de correcao 1: dois nomes unidos por "e" sao duas pessoas, cada uma avaliada sozinha
    for parte in partes:
        if not _nome_no_rotulo(parte, comuns, corpo):
            if not _passa_nos_vetos_do_rotulo(parte):
                continue
            if zona_do_candidato(parte, mapa, ORIGEM_ROTULO_DE_MENOR, conferir_nome) != "nome":
                continue
        limpo = _nome_limpo(parte)
        if limpo == parte:
            _registrar_descoberta(mapa, _PREFIXO_DA_LINHA_DE_BAIXO, limpo, "pessoa do documento de menor")


def _minusculo_da_execucao_aceito(nome: str, comuns=frozenset(), lingua=None) -> bool:
    """O candidato escrito em minusculas depois de uma das quatro ancoras da execucao (validacao no acervo: o texto
    corrido depois de "socio" — um sobrenome do ranking e palavras comuns — virava codigo, e a variante de uma
    palavra ficava em claro em 5 arquivos, barrando o dossie pela guarda nomes_em_claro). So' entra quando a
    primeira palavra e' prenome do ranking do IBGE (FREQUENCIA_DE_NOME_COMUM+ pessoas, fora o prenome que e'
    palavra comum) e nenhuma palavra e' comum dos autos: `comuns`, a frase, o que nunca e' nome, ou a palavra que
    o processo escreve em minusculas (`lingua`) fora do ranking. Recusado, nao vai a incertos: e' pulado."""
    sig = _significativas(nome)
    if not sig or sig[0] in PRENOMES_PALAVRA_COMUM or frequencia_de_prenome(sig[0]) < FREQUENCIA_DE_NOME_COMUM:
        return False
    vocabulario = lingua if lingua is not None and not isinstance(lingua, _TodaALingua) else frozenset()
    return not any(w in comuns or w in _PALAVRAS_DA_FRASE or w in _NUNCA_NOME
                   or (w in vocabulario and not _no_ranking(w)) for w in sig)


def _registrar_na_ancora(texto: str, ini: int, mapa: dict, prefixo: str, nome: str, papel: str,
                         conferir_nome=None, papeis_proprios=frozenset()) -> None:
    """_registrar_ancorado com o papel da ancora — salvo quando a palavra logo antes do nome e' o papel de outra
    pessoa ("..., preposto Fulano"; rodada de correcao 2, I-b): entao o nome vira [[PESSOA_n]] (pessoa citada),
    nunca a testemunha, o perito ou a paradigma. `papeis_proprios` (0.5.35): as palavras que sao a propria ancora
    ("socia Fulana" na ancora do socio) e nao o papel de outra pessoa."""
    # rodada de correcao 4 (I-1): o papel so' conta COLADO ao nome — so' espaco e o tratamento entre eles ("...,
    # preposto Fulano", "preposta Dra. Fulana"); a pontuacao no meio ("arrolada pelo procurador, Fulana") separa
    colado = re.search(r"([^\W\d_]+)[ \t]+(?:(?i:dra?|sra?|doutora?)\.?[ \t]+)?$", texto[max(0, ini - 40):ini])
    papel_antes = normalizar(colado.group(1)) if colado else ""
    if papel_antes in _PAPEIS_DE_OUTRA_PESSOA - {"advogado", "advogada", "procurador", "procuradora"} - papeis_proprios:
        # o preposto, o socio, o representante: [[PESSOA_n]], o papel fora do valor. O advogado ou procurador colado
        # ao nome, na ancora de pessoa, e' registrado pela ancora, como antes ("Testemunha: advogado Fulano") —
        # a excecao do advogado da capa nao e' feita: a descoberta nao recebe os advogados da capa (construir_mapa
        # os deixa de fora do mapa)
        _registrar_ancorado(mapa, _PREFIXO_DA_LINHA_DE_BAIXO, nome, "pessoa citada", papel, conferir_nome)
        return
    _registrar_ancorado(mapa, prefixo, nome, papel, papel, conferir_nome)


def descobrir_pessoas(texto: str, mapa: dict, comuns=frozenset(), conferir_nome=None, lingua=None) -> None:
    """Testemunhas e peritos nao constam da capa: entram no mapa quando
    aparecem em ata ou laudo. Roda ANTES da substituicao (spec 7.2). O texto
    e' lido em NFC (0.5.0): em NFD, RE_PALAVRA partia o nome na marca
    combinante e a descoberta registrava pedacos dele. O nome depois da
    ancora e' lido sem a caixa (_nomes_depois_da_ancora, 0.5.19); `comuns`
    (opcional): as palavras comuns dos autos, que tambem encerram o nome."""
    if not nivel_mod.nomes_em_codigo(nivel_mod.do_mapa(mapa)):
        return                      # publico: nenhuma pessoa entra no mapa
    texto = texto_limpo(texto)
    for m in RE_ANCORA_TESTEMUNHA.finditer(texto):
        polo = normalizar(m.group("polo") or "")
        pref = ("TESTEMUNHA_RTE" if polo.startswith("reclamante")
                else "TESTEMUNHA_RDA" if polo.startswith("reclamad")
                else "TESTEMUNHA")
        # a lista ("Maria..., Paulo... e Jose..."): cada nome vira uma testemunha propria, com token proprio
        for ini, _fim, nome in _nomes_depois_da_ancora(texto, m.end(), comuns, lista=True, lingua=lingua):
            if _ja_no_mapa_pela_inicial(texto, ini, nome, mapa):
                continue
            _registrar_na_ancora(texto, ini, mapa, pref, nome, "testemunha", conferir_nome)
    for m in RE_ANCORA_PERITO.finditer(texto):
        for ini, _fim, nome in _nomes_depois_da_ancora(texto, m.end(), comuns, perito=True, lingua=lingua):
            _registrar_na_ancora(texto, ini, mapa, "PERITO", nome, "perito", conferir_nome)
    # Paradigma citada duas vezes ("equiparacao com a paradigma Fulana")
    # cai nas duas ancoras — token_para deduplica pela chave normalizada,
    # entao a pessoa ganha um unico tóken.
    for regex in (RE_ANCORA_PARADIGMA, RE_ANCORA_EQUIPARACAO):
        for m in regex.finditer(texto):
            for ini, _fim, nome in _nomes_depois_da_ancora(texto, m.end(), comuns, lista=True, lingua=lingua):
                _registrar_na_ancora(texto, ini, mapa, "PARADIGMA", nome, "paradigma", conferir_nome)
    _terceiros_da_execucao(texto, mapa, comuns, conferir_nome, lingua)
    _ancorar_qualificacao(texto, mapa)
    _descobrir_linha_de_baixo(texto, mapa)


def descobrir_terceiros_da_execucao(texto: str, mapa: dict, comuns=frozenset(), conferir_nome=None,
                                    lingua=None) -> None:
    """So' as quatro ancoras da execucao (arrematante, adquirente, socio, recebedor do AR), para o texto dos
    documentos que nao sao peca integral (revisao final do ramo, validacao no acervo: o "Adquirente - NOME" estava
    num documento so' listado, e o nome, sem ancora, em claro nas pecas integrais). Nada no nivel publico."""
    if not nivel_mod.nomes_em_codigo(nivel_mod.do_mapa(mapa)):
        return
    _terceiros_da_execucao(texto_limpo(texto), mapa, comuns, conferir_nome, lingua)


def _terceiros_da_execucao(texto: str, mapa: dict, comuns, conferir_nome, lingua) -> None:
    # 0.5.35: as ancoras da execucao (a lista: "sócios Fulano, Beltrano e Sicrano")
    for regex, prefixo, papel in ANCORAS_DA_EXECUCAO:
        for m in regex.finditer(texto):
            for ini, _fim, nome in _nomes_depois_da_ancora(texto, m.end(), comuns, lista=True, lingua=lingua):
                if nome[:1].islower() and not _minusculo_da_execucao_aceito(nome, comuns, lingua):
                    continue        # o texto corrido em minusculas depois da ancora: nem codigo nem incerto
                if _ja_no_mapa_pela_inicial(texto, ini, nome, mapa):
                    continue
                _registrar_na_ancora(texto, ini, mapa, prefixo, nome, papel, conferir_nome,
                                     _PAPEIS_DA_ANCORA_DO_SOCIO if prefixo == "SOCIO" else frozenset())


# --- 0.5.2: o interlocutor da conversa de aplicativo de mensagens ---------------
LINHAS_DO_ALTO = 5
# a linha de status do contato, logo abaixo do nome (e o mesmo status no fim da linha do nome)
RE_STATUS_DO_CONTATO = re.compile(r"(?i)^\W*(?:online|digitando|gravando|visto\s+(?:por\s+[úu]ltimo|hoje|ontem))")
RE_STATUS_NO_FIM = re.compile(r"(?i)\s+(?:online|digitando\W*|gravando\b.*|visto\s+(?:por\s+[úu]ltimo|hoje|ontem)\b.*)$")
# as palavras da tela do aplicativo, que nunca sao nome
_TELA_DO_APLICATIVO = {
    "online", "digitando", "gravando", "visto", "ultimo", "hoje", "ontem", "mensagem", "mensagens", "grupo",
    "contato", "contatos", "dados", "conversa", "conversas", "chamada", "chamadas", "video", "voz", "audio",
    "arquivo", "foto", "fotos", "midia", "anexo", "buscar", "pesquisar", "editar", "responder", "encaminhar",
    "encaminhada", "sair", "voltar", "camera", "status", "configuracoes", "whatsapp", "telegram", "instagram",
    "messenger", "direct", "business", "apagada", "figurinha", "silenciar", "bloquear", "denunciar", "toque"}
# o cargo, o lugar, o parentesco e o apelido que o contato salvo leva depois do nome ("Fulana Supervisora Vila
# Nova", "Beltrano Obra", "Ciclano Novo"): cortam o nome (no acervo, a ancora "Fulana Supervisor Vila" faria de
# "supervisor" e "vila" palavras de nome, omitidas em toda conversa)
_CARGO_LUGAR_OU_PARENTESCO = {
    "supervisor", "supervisora", "gerente", "encarregado", "encarregada", "chefe", "coordenador", "coordenadora",
    "diretor", "diretora", "rh", "financeiro", "financeira", "vendas", "loja", "obra", "filial", "unidade", "setor",
    "vila", "centro", "matriz", "escritorio", "trabalho", "novo", "nova", "antigo", "antiga", "pessoal",
    "particular", "celular", "casa", "mae", "pai", "irmao", "irma", "tio", "tia", "amor", "vizinho", "vizinha",
    "colega", "patrao", "patroa", "dona", "seu", "sr", "sra", "dr", "dra", "motorista", "porteiro", "portaria",
    "recepcao", "administracao", "adm", "dp", "contabilidade", "juridico", "advogado", "advogada", "cliente"}
# 0.5.8: a saudacao e o termo de pedido, de beneficio, de setor e de documento trabalhista, que nunca sao nome de
# pessoa: cortam o nome do interlocutor sempre, como a tela do aplicativo, estejam ou nao nas comuns do processo
# ("Recursos Humanos", "Bom Dia", "Seguro Desemprego", "Vale Transporte" com o status, no "~" ou na exportacao nao
# viram codigo). Lista fixa; de fora a palavra que tambem e' sobrenome ("vale", "dias", "hora", "seguro", "morais",
# "moral", "rosa", "paz"...): a outra palavra do par corta ("Hora Extra" pela "extra", "Seguro Desemprego" pela
# "desemprego"). "rh", "setor", "pessoal" e "financeiro" ja' estao no cargo; "adicional", "banco", "inss" e os
# adicionais, em _NUNCA_NOME.
_SAUDACAO_OU_TERMO_DO_TRABALHO = {
    # "boas" e "saude" ficam de fora: "Vilas Boas" e' sobrenome composto (re-revisao 3); "festas" e "vindas"
    # cortam "Boas Festas" e "Boas Vindas", e "plano" corta "Plano de Saude"
    "bom", "boa", "bons", "festas", "vindas", "dia", "tarde", "noite", "tudo", "certo", "ok", "obrigado",
    "obrigada", "recursos", "humanos", "departamento", "desemprego", "extra", "extras", "cesta", "basica",
    "transporte", "plano", "refeicao", "alimentacao", "aviso", "previo", "justa", "causa", "folha", "ponto",
    "cartao", "salario", "familia", "dano", "danos", "assedio", "intervalo", "intrajornada", "interjornada",
    "ferias", "decimo", "terceiro", "fgts", "rescisao", "noturno", "noturna", "gas", "cultura", "itinere",
    "equiparacao", "salarial", "holerite", "contracheque", "recibo", "ctps"}
RE_REMETENTE_DE_GRUPO = re.compile(r"(?m)^\W{0,3}(?:\+?\d[\d\s().-]{7,}\d\s*)?~\s*(?P<nome>[^\n~]{2,60})$")
# o remetente da exportacao do aplicativo ("[12/03/2025 10:41] Fulano Beltrano:", "12/03/2025 10:41 - Fulano:"); no
# texto saneado da conversa, o colchete vira parentese ("(12/03/2025, 10:41:07) Fulano:")
RE_REMETENTE_DA_EXPORTACAO = re.compile(
    r"(?m)^\W{0,2}?(?:[\[(]\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?[\])]\s*|\d{1,2}/\d{1,2}/\d{2,4},?\s+"
    r"\d{1,2}:\d{2}(?::\d{2})?\s+-\s+)(?P<nome>[^:\n]{2,45}):")
RE_TELEFONE_DO_REMETENTE = re.compile(r"\+?\d[\d\s().-]{6,}\d")
# o grupo com o contato salvo: o nome logo depois de uma hora ou de um separador de data ("Hoje", "12/03/2025")
RE_HORA_DA_LINHA = re.compile(r"(?i)^\W{0,3}\d{1,2}[:h]\d{2}(?::\d{2})?\s*(?:[ap]\.?m\.?)?\W{0,6}$")
RE_SEPARADOR_DA_LINHA = re.compile(r"(?i)^\W*(?:hoje|ontem|(?:segunda|ter[çc]a|quarta|quinta|sexta)(?:-feira)?|s[áa]bado"
                                   r"|domingo|\d{1,2} de [a-zç]+(?: de \d{4})?|\d{1,2}/\d{1,2}/\d{2,4})\W*$")
# o tratamento ou o parentesco NA FRENTE do nome ("Dona Marlene Couto", "Dr. Carlos Andrade"): pulado
_TRATAMENTO_NA_FRENTE = {"dona", "seu", "sr", "sra", "dr", "dra", "tia", "tio", "chefe", "patrao", "patroa"}
RE_SO_LETRAS_DE_NOME = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ' .-]+$")


def _nome_do_interlocutor(linha: str, comuns=frozenset(), minimo_antes_do_comum: int = 0) -> str | None:
    """O nome de pessoa na linha do contato (ou do remetente de grupo), ou None: sem o status no fim, sem o sufixo
    entre parenteses ("(Obra)") nem o que vem depois de " - " ("- RH"), e sem o que nao e' letra nas pontas (a
    seta, o numero de nao lidas); o tratamento ou o parentesco na frente ("Dona", "Tia", "Dr.") pulado; 2 a 4
    palavras com inicial maiuscula, so' letras, cortado na primeira palavra da tela do aplicativo, de cargo,
    lugar ou parentesco, palavra comum dos autos (`comuns`) ou que nunca e' nome (o sobrenome que e' palavra de
    _NUNCA_NOME, "Porto", fica fora: a omissao por palavra o tira logo depois do codigo); aceito por _nome_limpo
    e sem cara de pessoa juridica. As palavras se comparam sem o ponto final ("Dr." e' "dr").
    `minimo_antes_do_comum` (revisao final de 02/10/2026): a palavra comum dos autos so' corta o nome com ao menos
    esse numero de palavras antes dela — o cabecalho confirmado (o status do aplicativo, o prenome do lexico, a
    marca do remetente) usa 2: "Carla Vale" com "vale" comum nos autos fica inteiro, "Ana Ficticia Vale" fica
    "Ana Ficticia" (e a omissao tira o "Vale" logo depois do codigo); o cargo, o lugar, o parentesco, a tela do
    aplicativo e o que nunca e' nome cortam sempre. E (re-revisao de 03/10/2026) o nome precisa de ao menos uma
    palavra fora das comuns — o prenome do lexico conta como fora: "Recursos Humanos", "Hora Extra", "Vale
    Transporte", "Bom Dia" nao sao nome; "Carla Vale" e "Keyvison Vale" sao. E (0.5.8) a saudacao e o termo de
    pedido, beneficio, setor e documento trabalhista (_SAUDACAO_OU_TERMO_DO_TRABALHO) cortam sempre, tambem com so'
    parte das palavras (ou nenhuma) nas comuns."""
    linha = RE_STATUS_NO_FIM.sub("", linha or "").strip()
    linha = re.split(r"\(|\s[-–]\s", linha, maxsplit=1)[0]
    linha = re.sub(r"^[^A-Za-zÀ-ÖØ-öø-ÿ]+|[^A-Za-zÀ-ÖØ-öø-ÿ]+$", "", linha)
    if (not linha or len(linha) > 40 or not RE_SO_LETRAS_DE_NOME.match(linha) or RE_SUFIXO_PJ.search(linha)
            or RE_PJ_INSTITUCIONAL.match(linha)):
        return None
    nome: list[str] = []
    palavras_da_linha = linha.split()
    for k, w in enumerate(palavras_da_linha):
        n = normalizar(w).rstrip(".")
        if not nome and n in _TRATAMENTO_NA_FRENTE:
            continue            # o tratamento ou o parentesco na frente do nome: pulado
        if n in CONECTIVOS and nome:
            nome.append(w)
            continue
        # 0.5.20 (auditoria da caixa, #6): sem a exigencia da inicial maiuscula — o contato salvo em minusculas e'
        # nome do mesmo jeito; a palavra da frase ("vou", "que", "hoje") para, como nas ancoras
        ultima = k == len(palavras_da_linha) - 1 and len(nome) == 1 and _prenome_provado(nome[0])
        seguinte = normalizar(palavras_da_linha[k + 1]).rstrip(".") if k + 1 < len(palavras_da_linha) else ""
        if (nome and _prenome_provado(normalizar(nome[0])) and _nome_do_ranking(n) and n not in _VERBOS_DE_SISTEMA
                and n not in comuns and seguinte and _no_ranking(seguinte) and seguinte not in comuns
                and seguinte not in _SAUDACAO_OU_TERMO_DO_TRABALHO and seguinte not in _PALAVRAS_DA_FRASE):
            # rodada de correcao 5: a palavra do ranking ENTRE palavras de nome, no nome aberto ("Marta Porto Lima");
            # no fim, a regra de sempre ("Ana Ficticia Vale", "Carla Ficticia Boa Tarde")
            nome.append(w)
            continue
        if n in _PALAVRAS_DA_FRASE and n not in _NUNCA_NOME and n not in _VERBOS_DE_SISTEMA and ultima:
            nome.append(w)      # rodada de correcao 2 (I-a): "Marcos Caixa" — o sobrenome que tambem e' palavra
            break
        if (len(n) < 2 or n in _TELA_DO_APLICATIVO or n in _CARGO_LUGAR_OU_PARENTESCO
                or n in _SAUDACAO_OU_TERMO_DO_TRABALHO or n in _NUNCA_NOME or n in CONECTIVOS
                or n in _PALAVRAS_DA_FRASE):
            break
        if n in comuns and sum(1 for x in nome if normalizar(x) not in CONECTIVOS) >= minimo_antes_do_comum:
            break
        nome.append(w)
    while nome and normalizar(nome[-1]) in CONECTIVOS:
        nome.pop()
    palavras = [normalizar(w).rstrip(".") for w in nome if normalizar(w) not in CONECTIVOS]
    if not 2 <= len(palavras) <= 4:
        return None
    if all(n in comuns and n not in PRENOMES_DO_LEXICO for n in palavras):
        return None             # so' palavras comuns dos autos ("Recursos Humanos", "Hora Extra"): nao e' nome
    candidato = " ".join(nome)
    aberto = bool(nome) and _prenome_provado(normalizar(nome[0]))
    if (_nome_limpo(candidato, aberto=aberto) != candidato or RE_PJ_INSTITUCIONAL.match(candidato)
            or RE_SUFIXO_PJ.search(candidato)):
        return None
    return candidato


def descobrir_interlocutores(texto: str, mapa: dict, comuns=frozenset(), conferir_nome=None) -> list[str]:
    """0.5.2: os interlocutores de uma pagina de conversa de aplicativo de mensagens que viram ancora: o contato
    no alto (a primeira das LINHAS_DO_ALTO linhas uteis com forma de nome — _nome_do_interlocutor —, quando a
    linha seguinte, ou o fim dela, e' o status do aplicativo, ou quando a primeira palavra e' prenome do lexico) e
    o remetente de grupo ("~ Fulano Beltrano"), o da exportacao do aplicativo ("[dd/mm/aaaa hh:mm] Fulano:"; a
    forma da exportacao e' a marca do aplicativo, como o "~") e o do grupo com o contato salvo
    (_remetentes_salvos). O que a troca ja' pega (a parte da capa, o comeco do nome dela, o interlocutor ja'
    registrado) nao vira outro codigo; o codigo que a troca nao aplica ao proprio nome e' desfeito (nunca fica no
    mapa um tóken que nao casa no texto). Devolve os codigos registrados agora (o mapa ganha o tóken
    [[INTERLOCUTOR_n]], papel "interlocutor"). `comuns`: as palavras comuns dos autos do processo, que cortam o
    nome ("Patricia Supervisora" fica com uma palavra so': fora). Revisao final (02/10/2026): "a troca ja' o
    pega" e' a troca levar o nome INTEIRO, ou o que sobra ser, a ate' 1-2 letras, palavra do mesmo codigo
    (_a_troca_ja_o_leva); o contato com o prenome de uma parte ("Maria Souza", com a reclamante Maria) ganha
    codigo proprio, e o prenome comum as duas passa a [[PRENOME_n]]."""
    if not nivel_mod.nomes_em_codigo(nivel_mod.do_mapa(mapa)):
        return []
    linhas = [l.strip() for l in texto_limpo(texto or "").splitlines() if l.strip()]
    achados: list[str] = []
    for i, linha in enumerate(linhas[:LINHAS_DO_ALTO]):
        status = RE_STATUS_NO_FIM.search(linha) or (i + 1 < len(linhas) and RE_STATUS_DO_CONTATO.match(linhas[i + 1]))
        nome = _nome_do_interlocutor(linha, comuns)
        if nome is None:
            # a palavra comum dos autos nao corta abaixo de 2 palavras o cabecalho que o status ou o prenome do
            # lexico confirmam; sem a confirmacao, a linha continua sem forma de nome (a de baixo pode ser o contato)
            nome = _nome_do_interlocutor(linha, comuns, minimo_antes_do_comum=2)
            if nome is None or not (status or normalizar(nome.split()[0]) in PRENOMES_DO_LEXICO):
                continue
        if status or normalizar(nome.split()[0]) in PRENOMES_DO_LEXICO:
            achados.append(nome)
        break                   # so' a primeira linha com forma de nome: a de baixo ja' pode ser mensagem
    for m in RE_REMETENTE_DE_GRUPO.finditer("\n".join(linhas)):
        nome = _nome_do_interlocutor(m.group("nome"), comuns, minimo_antes_do_comum=2)
        if nome:
            achados.append(nome)
    for m in RE_REMETENTE_DA_EXPORTACAO.finditer("\n".join(linhas)):
        nome = _nome_do_interlocutor(RE_TELEFONE_DO_REMETENTE.sub(" ", m.group("nome")).replace("~", " "), comuns,
                                     minimo_antes_do_comum=2)
        if nome:
            achados.append(nome)
    achados += _remetentes_salvos(linhas, comuns)
    registrados: list[str] = []
    for nome in achados:
        if incertos.decisao(mapa, nome) == incertos.NAO_NOME:
            continue            # o juiz ja' disse que nao e' nome
        if _a_troca_ja_o_leva(nome, pseudonimizar(nome, mapa), mapa):
            continue            # a troca ja' o pega: inteiro, ou a pessoa do mapa lida com erro
        antes = copy.deepcopy(mapa)
        # a marca do aplicativo (o status, o "~", a exportacao) e' a ancora: a decisao do juiz, a prova, a
        # conferencia do Jev; na duvida, o codigo, anotado como incerto (_decidir_ancorado)
        if not _decidir_ancorado(mapa, nome, "contato de conversa", conferir_nome):
            continue
        tok = _registrar_descoberta(mapa, "INTERLOCUTOR", nome, "interlocutor")
        depois = pseudonimizar(nome, mapa)
        if tok not in depois or _sobras_da_troca(depois):
            mapa.clear()        # o codigo que nunca casa no texto nao fica no mapa (o incidente de 24/09/2026)
            mapa.update(antes)
            continue
        if tok not in registrados:
            registrados.append(tok)
    return registrados


RE_CODIGO_NA_TROCA = re.compile(r"\[\[[A-Z][A-Z0-9_]*\]\]")


def _sobras_da_troca(trocado: str) -> list[str]:
    """As palavras (normalizadas) do nome trocado que ficaram fora de todo codigo, sem os conectivos."""
    return [w for w in (normalizar(x) for x in RE_PALAVRA.findall(RE_CODIGO_NA_TROCA.sub(" ", trocado or "")))
            if w and w not in CONECTIVOS]


def _ate_k_letras(a: str, b: str, k: int) -> bool:
    """Distancia de edicao entre a e b no maximo k (a palavra lida com erro)."""
    if abs(len(a) - len(b)) > k:
        return False
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        atual = [i]
        for j, cb in enumerate(b, 1):
            atual.append(min(anterior[j] + 1, atual[j - 1] + 1, anterior[j - 1] + (ca != cb)))
        anterior = atual
    return anterior[-1] <= k


def _a_troca_ja_o_leva(nome: str, trocado: str, mapa: dict) -> bool:
    """O nome do interlocutor ja' e' de uma pessoa do mapa (nada de codigo novo): a troca o leva INTEIRO (nenhuma
    palavra fora de codigo e conectivo), ou cada palavra que sobra e', a ate' 1 letra (menos de 5 letras) ou 2, uma
    palavra do nome de um codigo que a troca pos nele (a parte lida com erro: "Maria Exenpl" e' a reclamante, e a
    omissao por palavra tira o "Exenpl"). O prenome de uma parte com o sobrenome de outra pessoa ("Maria Souza")
    nao e' (revisao final de 02/10/2026: saia "[[RECLAMANTE_1]] Souza", e a autoria ia para a parte)."""
    if trocado == nome:
        return False
    sobras = _sobras_da_troca(trocado)
    if not sobras:
        return True
    palavras: set[str] = set()
    for tok in RE_CODIGO_NA_TROCA.findall(trocado):
        info = (mapa.get("tokens") or {}).get(tok)
        if isinstance(info, dict):
            for forma in [*_formas(info), *(info.get("variantes_vistas") or [])]:
                palavras |= {w for w in normalizar(str(forma or "")).split() if len(w) >= 3 and w not in CONECTIVOS}
    return all(any(_ate_k_letras(w, p, 1 if len(w) < 5 else 2) for p in palavras) for w in sobras)


def _remetentes_salvos(linhas: list[str], comuns=frozenset()) -> list[str]:
    """O remetente do grupo com o contato salvo (sem o "~"): a linha inteira com forma de nome (_nome_do_interlocutor
    igual a ela), com a primeira palavra prenome do lexico, que se repete 2+ vezes na pagina e, ao menos uma vez,
    vem logo depois de uma hora ou de um separador de data e antes de uma linha de mensagem. O nome do grupo e a
    notificacao do celular (sem a repeticao, sem o prenome ou sem a hora antes) ficam de fora."""
    vezes: dict[str, list[int]] = {}
    for i, linha in enumerate(linhas):
        vezes.setdefault(linha, []).append(i)
    achados: list[str] = []
    for linha, posicoes in vezes.items():
        if len(posicoes) < 2:
            continue
        nome = _nome_do_interlocutor(linha, comuns, minimo_antes_do_comum=2)
        limpa = re.sub(r"^[^A-Za-zÀ-ÖØ-öø-ÿ]+|[^A-Za-zÀ-ÖØ-öø-ÿ]+$", "", linha)
        if nome is None or nome != limpa or normalizar(nome.split()[0]) not in PRENOMES_DO_LEXICO:
            continue
        if any(0 < i < len(linhas) - 1 and (RE_HORA_DA_LINHA.match(linhas[i - 1]) or RE_SEPARADOR_DA_LINHA.match(
                linhas[i - 1])) and not RE_HORA_DA_LINHA.match(linhas[i + 1]) and linhas[i + 1] != linha
               for i in posicoes):
            achados.append(nome)
    return achados


def pseudonimizar(texto: str, mapa: dict, conversa: bool = False) -> str:
    """Troca identificadores/contatos e nomes de pessoas pelos tokens do
    mapa. Nomes tem prioridade sobre identificadores na fusao dos spans:
    um span de identificador (endereco, CPF etc.) que sobrepoe QUALQUER
    span de nome e' descartado inteiro antes de juntar as duas fontes —
    nunca o contrario. Sem essa prioridade, um endereco sem virgula antes
    do nome (nome "colado" ao numero do imovel/rua) casa como um unico
    span que pode terminar no MEIO do nome; como o merge abaixo mantem o
    span que comeca antes e descarta qualquer outro que comece antes do
    fim dele, o span do nome inteiro seria descartado e a cauda que sobra
    depois do fim do identificador vazaria em claro na saida (achado de
    revisao). Ordena o resultado por inicio e, na sobreposicao residual
    entre spans da MESMA fonte (que cada uma delas ja evita internamente),
    mantem o que comeca antes (spec 4.2). A linha que cita um documento do
    PJe pelo Id traz o titulo digitado pelo advogado: o nome nela e'
    procurado como no titulo (pseudonimizar_rotulo, 0.5.0). `conversa`
    (0.5.2): o texto de conversa de aplicativo de mensagens — todo numero
    com forma de telefone vira codigo."""
    texto = texto_limpo(texto)
    citacoes = [m.span() for m in RE_CITACAO_DE_DOCUMENTO.finditer(texto)]
    return _pseudonimizar(texto, mapa, _copia_com_nomes(texto, mapa, citacoes) if citacoes else None,
                          conversa=conversa)


def palavras_de_nome(mapa: dict) -> set[str]:
    """As palavras (normalizadas) dos nomes de pessoa do mapa — do valor e
    dos aliases de cada tóken 'pessoa' que nao e' pessoa juridica, locucao
    de mapa antigo nem [[PRENOME_n]] —, com 3+ letras e fora de
    CONECTIVOS, _NUNCA_NOME e PRENOMES_PALAVRA_COMUM."""
    return set().union(*_palavras_por_pessoa(mapa))


def _palavras_por_pessoa(mapa: dict) -> list[set[str]]:
    """As palavras de palavras_de_nome, separadas por pessoa (a URL de
    dominio institucional exige 2+ palavras do nome da MESMA pessoa)."""
    saida: list[set[str]] = []
    for tok, info in nivel_mod.tokens_vigiados(mapa).items():
        if (not isinstance(info, dict) or info.get("categoria") != "pessoa"
                or token_fora_da_guarda(info) or str(tok).startswith("[[PRENOME_")):
            continue
        palavras = {w for forma in _formas(info) for w in normalizar(forma).split()
                    if len(w) >= 3 and w not in CONECTIVOS and w not in _NUNCA_NOME
                    and w not in PRENOMES_PALAVRA_COMUM}
        if palavras:
            saida.append(palavras)
    return saida


# '-' e '_' entre letras: o slug e o nome de arquivo ("procuracao_joana_...")
RE_JUNCAO_ENTRE_LETRAS = re.compile(r"(?<=[A-Za-zÀ-ÖØ-öø-ÿ])[-_](?=[A-Za-zÀ-ÖØ-öø-ÿ])")
# a linha da peca que cita um documento do PJe pelo Id ("13. servicos com.
# fulana 2022 (id 1234567)"): o titulo que o advogado digitou, copiado
RE_CITACAO_DE_DOCUMENTO = re.compile(r"(?im)^[^\n]*\(\s*id\.?\s*:?\s*[0-9a-f]{7}\b[^\n]*$")


# Palavras que nunca ganham maiuscula na copia, mesmo sendo nome do mapa: o
# mes digitado sem cedilha e o substantivo "marco" ("o marco inicial da
# prescricao", "holerite marco 2023"). "Marco" com maiuscula continua
# trocado; fora de PRENOMES_PALAVRA_COMUM, o [[PRENOME_n]] do "Marco"
# ambiguo continua valendo.
_NUNCA_MAIUSCULA_NA_COPIA = {"janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto",
                             "setembro", "outubro", "novembro", "dezembro"}


def _copia_com_nomes(texto: str, mapa: dict, trechos: list[tuple[int, int]]) -> str:
    """Copia de MESMO tamanho do texto em que, dentro dos trechos, cada
    palavra de nome de pessoa do mapa (palavras_de_nome) ganha inicial
    maiuscula — so' se o tamanho nao mudar, nunca o mes nem "marco" — e
    '-'/'_' entre letras viram espaco. Palavra que nao e' de nome do mapa
    nunca muda de caixa."""
    nomes = palavras_de_nome(mapa) - _NUNCA_MAIUSCULA_NA_COPIA
    copia = list(texto)
    for ini, fim in trechos:
        for m in RE_JUNCAO_ENTRE_LETRAS.finditer(texto, ini, fim):
            copia[m.start()] = " "
        for m in RE_PALAVRA.finditer(texto, ini, fim):
            palavra = m.group()
            inicial = palavra[0].upper()
            if normalizar(palavra) in nomes and palavra[0] != inicial and len(inicial) == 1:
                copia[m.start()] = inicial
    return "".join(copia)


def pseudonimizar_rotulo(texto: str | None, mapa: dict) -> str | None:
    """Titulo ou descricao de documento do PJe (texto livre que o advogado
    digita: "Carteira de Identidade/RG (oab joana)",
    "procuracao_joana_kretzer_assinado"). Monta uma copia de MESMO tamanho
    em que cada palavra de nome de pessoa do mapa (palavras_de_nome) ganha
    inicial maiuscula — so' se o tamanho nao mudar — e '-'/'_' entre letras
    viram espaco; os nomes sao procurados na copia e trocados no original.
    Palavra que nao e' de nome do mapa nunca muda de caixa. Os
    identificadores vem do original, como em pseudonimizar()."""
    if not texto:
        return texto
    texto = texto_limpo(texto)
    return _pseudonimizar(texto, mapa, _copia_com_nomes(texto, mapa, [(0, len(texto))]))


# URL (0.5.0): esquema http(s):// ou www. A classe exclui espaco, aspas,
# barra invertida (o JSON do dossie e' pseudonimizado como texto), '|' (a
# tabela do resumo), '<' '>' '[' ']' '(' ')' '{' '}' e crase.
RE_URL = re.compile(r"(?i)\b(?:https?://|www\.)[^\s\"'\\|<>\[\](){}`]+")
_CONTINUACAO_DE_URL = re.compile(r"[^\s\"'\\|<>\[\](){}`]+")
_FIM_DE_URL = ".,;:!?"
# perfil pessoal: a URL identifica a pessoa mesmo sem nome do mapa (com
# "/" ou "." antes do dominio: "webex.com/" nao e' "x.com/")
RE_PERFIL_PESSOAL = re.compile(
    r"(?i)(?:^|[/.])(?:linkedin\.com/in/|instagram\.com/|facebook\.com/|fb\.com/|tiktok\.com/@|"
    r"x\.com/|twitter\.com/|wa\.me/)")
# dominio institucional: a palavra do caminho igual a um sobrenome do mapa
# ("…/portais/campos/…", "…/trabalho/campos-gerais") nao basta — exige perfil
# pessoal ou 2+ palavras do nome da MESMA pessoa
RE_DOMINIO_INSTITUCIONAL = re.compile(r"(?i)^(?:https?://)?(?:www\.)?[^/?#\s]*\.(?:jus|gov|leg|mp|def)\.br(?![^/?#:])")
# a URL partida no meio pela extracao termina em pontuacao de URL (o "." fica
# de fora: e' tambem o fim da frase, e a linha seguinte pode comecar por data)
_URL_PARTIDA = "-/=?&_"


def _urls(texto: str) -> list[tuple[int, int]]:
    """[(ini, fim)] das URLs, sem a pontuacao final. A extracao do PDF parte
    a URL longa na linha: a continuacao na linha seguinte so' entra quando
    ela comeca por pontuacao de URL (/ ? = & % #), ou por digito depois da
    URL terminada em pontuacao de URL ("…-⏎1234567/"; a data da linha
    seguinte, depois da URL inteira, nao), ou e' toda minuscula e sem
    espaco, ou e' o resto do slug com hifen depois do slug terminado em "-"
    ou "_" ("…/in/fulana-⏎Beltrana-Sicrana-123") — NUNCA a palavra com
    maiuscula sem hifen: o nome da parte na linha de baixo seria engolido, e
    os sobrenomes dele ficariam em claro sem a guarda ver (demonstrado pelo
    cetico, 28/09/2026)."""
    saida = []
    for m in RE_URL.finditer(texto):
        ini, fim = m.span()
        if texto[fim:fim + 1] == "\n":
            linha = texto[fim + 1:].split("\n", 1)[0]
            c = _CONTINUACAO_DE_URL.match(linha)
            ultimo = texto[fim - 1]
            if c and ((c.group()[0].isdigit() and ultimo in _URL_PARTIDA) or c.group()[0] in "/?=&%#"
                      or (c.group() == linha.rstrip() and not any(ch.isupper() for ch in c.group()))
                      or (ultimo in "-_" and ("-" in c.group() or "_" in c.group()))):
                fim += 1 + c.end()
        while fim > ini and texto[fim - 1] in _FIM_DE_URL:
            fim -= 1
        saida.append((ini, fim))
    return saida


def _spans_de_urls(texto: str, mapa: dict, urls: list[tuple[int, int]],
                   spans_nomes: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    """A URL inteira vira [[URL_n]] (categoria 'url') quando os trechos em
    letras dela tem palavra de nome de pessoa do mapa (palavras_de_nome) ou
    quando e' perfil pessoal. O nome que comeca dentro da URL e termina fora
    corta a URL antes dele (o nome e' trocado como nome). URL institucional
    sem nome (jus.br, gov.br) fica — e a de dominio institucional so' vira
    tóken com 2+ palavras do nome da mesma pessoa (uma palavra do caminho
    pode ser um sobrenome que e' palavra comum)."""
    pessoas = _palavras_por_pessoa(mapa)
    nomes = set().union(*pessoas)
    spans = []
    for ini, fim in urls:
        for n_ini, n_fim, _tok in spans_nomes:
            if ini < n_ini < fim < n_fim:
                fim = n_ini
        url = texto[ini:fim]
        palavras = {normalizar(p) for p in RE_PALAVRA.findall(url)}
        if RE_PERFIL_PESSOAL.search(url):
            pass
        elif RE_DOMINIO_INSTITUCIONAL.match(url):
            if not any(len(p & palavras) >= 2 for p in pessoas):
                continue
        elif not palavras & nomes:
            continue
        spans.append((ini, fim, token_para(mapa, "URL", "url", url)))
    return spans


_RE_SUFIXO_SOCIETARIO_NO_FIM = re.compile(
    r"[\s,.\-–]+(LTDA\.?|S\.?\s?/?\s?A\.?|EIRELI|EPP|ME|MEI)(\s*[-–]\s*(ME|EPP))?\s*$", re.I)


def _formas_da_pj(nome: str) -> list[str]:
    """A denominacao inteira e, sobrando 2+ palavras, a forma sem o sufixo societario do fim."""
    nome = " ".join((nome or "").split())
    formas = [nome] if nome else []
    sem = _RE_SUFIXO_SOCIETARIO_NO_FIM.sub("", nome).strip()
    if sem and sem != nome and len(sem.split()) >= 2:
        formas.append(sem)
    return formas


def _spans_de_pj(texto: str, mapa: dict, tomados: list[tuple[int, int]] = (),
                 spans_nomes: list[tuple[int, int, str]] = ()) -> list[tuple[int, int, str]]:
    """Sigiloso: a denominacao das pessoas juridicas da capa (categoria 'pj'), nas formas de _formas_da_pj,
    sem diferenciar maiusculas e com qualquer espaco entre as palavras, e todo CNPJ. Limite assumido: a
    grafia sem acento de um nome acentuado e a empresa que nao e' parte ficam em claro. `tomados`: os
    trechos ja' trocados (as URLs) — nada nasce neles. `spans_nomes`: a denominacao que CONTEM o nome de uma
    pessoa ("Fulano Beltrano Transportes LTDA") fica com a empresa (quem chama tira o nome contido); a que
    so' cruza um nome, ou coincide com ele (a forma sem sufixo do empresario individual), cede a ele. O CNPJ so' ganha codigo fora de todo trecho tomado (URL, nome, denominacao)."""
    spans: list[tuple[int, int, str]] = []
    for tok, info in list(mapa["tokens"].items()):
        if not isinstance(info, dict) or info.get("categoria") != "pj":
            continue
        for forma in _formas_da_pj(str(info.get("valor") or "")):
            padrao = r"(?<!\w)" + r"\s+".join(re.escape(p) for p in forma.split()) + r"(?!\w)"
            for m in re.finditer(padrao, texto, re.I):
                ini, fim = m.span()
                cruzados = [(a, b) for a, b, _ in spans_nomes if not _livre(a, b, [(ini, fim)])]
                # so' a denominacao ESTRITAMENTE mais longa que o nome o leva: a forma sem sufixo do empresario
                # individual ("Fulano Beltrano ME" -> "Fulano Beltrano") igual ao nome da pessoa cede a ela
                if _livre(ini, fim, list(tomados)) and all(ini <= a and b <= fim and b - a < fim - ini
                                                           for a, b in cruzados):
                    spans.append((ini, fim, tok))
    ocupados = list(tomados) + [(a, b) for a, b, _ in spans_nomes] + [(a, b) for a, b, _ in spans]
    for m in RE_CNPJ.finditer(texto):
        if _livre(m.start(), m.end(), ocupados):      # o codigo so' nasce para o CNPJ que fica no texto
            spans.append((m.start(), m.end(), _token_do_cnpj(mapa, m.group(0))))
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))          # no mesmo inicio, a forma mais longa primeiro
    return spans


def _pseudonimizar(texto: str, mapa: dict, texto_dos_nomes: str | None = None, conversa: bool = False) -> str:
    urls = _urls(texto)
    spans_nomes = (_spans_de_nomes(texto_dos_nomes, mapa, original=texto, urls=urls)
                   if texto_dos_nomes is not None else _spans_de_nomes(texto, mapa, urls=urls))
    # a URL tokenizada leva junto o nome que estiver dentro dela
    spans_url = _spans_de_urls(texto, mapa, urls, spans_nomes)
    tomados_por_url = [(ini, fim) for ini, fim, _ in spans_url]
    spans_nomes = [s for s in spans_nomes if _livre(s[0], s[1], tomados_por_url)]
    spans_pj = []
    if nivel_mod.empresas_em_codigo(nivel_mod.do_mapa(mapa)):
        spans_pj = _spans_de_pj(texto, mapa, tomados_por_url, spans_nomes)
        # a denominacao que contem o nome do dono leva o nome junto (vira inteira o codigo da empresa)
        spans_nomes = [s for s in spans_nomes
                       if not any(p0 <= s[0] and s[1] <= p1 for p0, p1, _ in spans_pj)]
    spans_ident = _spans_de_identificadores(texto, mapa, conversa)
    tomados_por_nome = [(ini, fim) for ini, fim, _ in spans_nomes + spans_url + spans_pj]
    spans_ident = [s for s in spans_ident
                  if _livre(s[0], s[1], tomados_por_nome)]
    spans = spans_nomes + spans_url + spans_pj + spans_ident
    spans.sort(key=lambda s: s[0])
    partes: list[str] = []
    pos = 0
    fim_do_ultimo = -1
    for ini, fim, tok in spans:
        if ini < fim_do_ultimo:
            continue  # sobreposicao residual: fica o que comeca antes
        partes.append(texto[pos:ini])
        partes.append(tok)
        pos = fim
        fim_do_ultimo = fim
    partes.append(texto[pos:])
    return "".join(partes)
