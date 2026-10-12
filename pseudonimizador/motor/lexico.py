# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
# Origem: Ulpiano, ulpiano/nucleo/privacidade/lexico.py, commit 5bab2ff (11/10/2026); alterações descritas abaixo.
"""
==============================================================
 ARQUIVO: lexico.py
 PROJETO: Ulpiano — privacidade
 VERSAO:  0.2.0
 CRIADO:  2026-09-29
 ALTERACAO 0.2.0 (05/10/2026): o ranking de prenomes e sobrenomes do IBGE
   (Nomes no Brasil, Censo 2022), com a frequencia, em lexico_ibge.json —
   consulta 'a parte (frequencia_de_prenome, frequencia_de_sobrenome), sem
   caixa nem acento. PRENOMES e SOBRENOMES, escritos 'a mao e sem os
   prenomes que sao palavra comum, NAO mudam: o varredor e o filtro das
   palavras comuns dependem de serem poucos e sem ambiguidade. O arquivo
   vem da API publica do IBGE (servicodados.ibge.gov.br/api/v3/nomes/2022/
   localidade/BR/ranking/nome e .../sobrenome), os mais frequentes do pais.
 ALTERACAO 0.1.0: os lexicos de prenomes e sobrenomes comuns, que eram de
   entendimentos/varredor.py (0.2.3), passam ao nucleo: o pseudonimizador
   (0.5.1) os usa para reconhecer o prenome composto de OUTRA pessoa que
   so' divide com a parte um sobrenome comum ("FULANA JOSE DA SILVA", com a
   reclamante "FULANA TERCIANA DA SILVA") — o nucleo nao depende de
   entendimentos; o varredor os importa daqui.
==============================================================
"""
from __future__ import annotations
import json
import unicodedata
from functools import lru_cache
from pathlib import Path

# Formas sem acento, em minusculas (mapa.normalizar). Os prenomes que tambem
# sao palavras comuns do portugues (rosa, vitoria, gloria, clara, aparecida,
# cesar, franco...) ficaram de fora de proposito: no varredor, o preco de um
# falso positivo e' bloquear um modelo legitimo; no pseudonimizador, a
# palavra comum no meio do nome nao pode passar por prenome de outra pessoa.
PRENOMES = frozenset("""
joao jose antonio francisco carlos paulo pedro lucas luiz luis marcos gabriel rafael daniel
marcelo bruno eduardo felipe raimundo rodrigo manoel manuel mateus matheus andre fernando fabio
leonardo gustavo guilherme leandro tiago thiago anderson ricardo marcio jorge sebastiao alexandre
roberto edson diego vitor victor sergio claudio geraldo adriano luciano julio renato vinicius
rogerio samuel ronaldo mario flavio igor douglas davi jefferson danilo henrique otavio wagner
wellington alan alex joaquim benedito valdir osvaldo gilberto nelson fabricio murilo heitor enzo
arthur artur miguel bernardo lorenzo theo nicolas
maria ana francisca antonia adriana juliana marcia fernanda patricia aline sandra camila amanda
bruna jessica leticia julia luciana vanessa mariana gabriela larissa claudia beatriz rita luana
sonia renata eliane josefa simone natalia cristiane carla debora rosangela jaqueline daniela
marlene terezinha tereza teresa raimunda andreia andrea fabiana lucia raquel angela rafaela joana
luzia elaine daiane cristina silvia tatiane regina sabrina sueli michele priscila paula marta
helena isabel isabela lorena carolina caroline alice laura valentina sofia manuela heloisa
giovana yasmin lourdes cassia neusa vania rosana solange denise monica viviane
""".split())
SOBRENOMES = frozenset("""
silva santos oliveira souza sousa rodrigues ferreira alves pereira lima gomes costa ribeiro
martins carvalho almeida lopes soares fernandes vieira barbosa rocha dias nascimento andrade
moreira nunes marques machado mendes freitas cardoso ramos goncalves santana teixeira araujo
castro pinto campos correia correa azevedo cavalcanti medeiros moura cunha monteiro borges farias
melo mello barros leite reis duarte nogueira batista siqueira fonseca brito miranda xavier prado
vasconcelos coelho sales viana bezerra aguiar amaral tavares peixoto guimaraes
""".split())

_ARQUIVO_IBGE = Path(__file__).with_name("lexico_ibge.json")


@lru_cache(maxsize=1)
def _ibge() -> dict:
    """O ranking do IBGE, lido uma vez; sem o arquivo (pacote incompleto), vazio: sobra a lista escrita 'a mao."""
    try:
        return json.loads(_ARQUIVO_IBGE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"prenomes": {}, "sobrenomes": {}}


def _chave(palavra: str) -> str:
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", palavra or "") if not unicodedata.combining(c))
    return sem_acento.strip().casefold()


def frequencia_de_prenome(palavra: str) -> int:
    """Quantas pessoas tem a palavra como primeiro nome no Censo 2022 (0: fora do ranking), sem caixa nem acento."""
    return int(_ibge()["prenomes"].get(_chave(palavra), 0))


def frequencia_de_sobrenome(palavra: str) -> int:
    """Quantas pessoas tem a palavra como sobrenome no Censo 2022 (0: fora do ranking), sem caixa nem acento."""
    return int(_ibge()["sobrenomes"].get(_chave(palavra), 0))
