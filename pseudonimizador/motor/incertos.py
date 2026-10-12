# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
# Origem: Ulpiano, ulpiano/nucleo/privacidade/incertos.py, commit 5bab2ff (11/10/2026); alterações descritas abaixo.
"""
==============================================================
 ARQUIVO: incertos.py
 PROJETO: Ulpiano — privacidade
 VERSAO:  0.2.0
 CRIADO:  2026-10-05
 ALTERACAO 0.2.0: a decisao do juiz pela tela (cartao "Nomes a confirmar"):
   o pedido local nomes_decididos.json, aplicado na montagem seguinte.
 Os nomes sobre os quais nao ha' certeza (pedido do juiz, 05/10/2026): o
 candidato que a regra local nao prova ser nome nem descarta, quando o Jev
 nao esta' disponivel (sem chave, opcao desligada, falha) ou nao decide
 com seguranca. Ficam no mapa do processo (local; nunca vai 'a Pasta do
 Claude), para o Ulpiano os mostrar ao juiz com a opcao de confirmar ou
 corrigir; a decisao dele vale nas montagens seguintes.

   mapa["nomes_incertos"]  = {chave: {"valor", "origem", "em_codigo", "jev"}}
   mapa["nomes_decididos"] = {chave: "nome" | "nao_nome"}

 chave = mapa.normalizar(valor). "em_codigo": o candidato foi trocado por
 codigo mesmo sem certeza (a descoberta com ancora de pessoa protege na
 duvida) ou ficou em claro (sem ancora). "jev": a probabilidade de ser
 nome de pessoa que o Jev deu, ou None quando ele nao foi ouvido.
==============================================================
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .mapa import normalizar

NOME = "nome"
NAO_NOME = "nao_nome"


def decisao(mapa: dict, valor: str) -> str | None:
    """O que o juiz ja' decidiu sobre o candidato: NOME, NAO_NOME ou None."""
    return (mapa.get("nomes_decididos") or {}).get(normalizar(valor))


def registrar(mapa: dict, valor: str, origem: str, *, em_codigo: bool, jev: float | None = None) -> None:
    """Anota o candidato como incerto; o ja' decidido pelo juiz nao volta 'a lista."""
    chave = normalizar(valor)
    if not chave or decisao(mapa, valor) is not None:
        return
    mapa.setdefault("nomes_incertos", {})[chave] = {
        "valor": " ".join(valor.split()), "origem": origem, "em_codigo": bool(em_codigo), "jev": jev}


def decidir(mapa: dict, valor: str, o_que: str) -> None:
    """Grava a decisao do juiz e tira o candidato dos incertos."""
    if o_que not in (NOME, NAO_NOME):
        raise ValueError(o_que)
    chave = normalizar(valor)
    mapa.setdefault("nomes_decididos", {})[chave] = o_que
    (mapa.get("nomes_incertos") or {}).pop(chave, None)


def pendentes(mapa: dict) -> list[dict]:
    """Os incertos ainda sem decisao, na ordem em que apareceram."""
    return list((mapa.get("nomes_incertos") or {}).values())


# --- a decisao do juiz pela tela (0.2.0) ----------------------------------------------------------------------
# Como o pedido de nivel (nivel.gravar_pedido), a decisao vai a um pedido local na pasta do processo, nunca
# direto no mapa: o mapa e' lido no comeco da montagem e gravado no fim, e a gravacao pela tela no meio de um
# preparo se perderia. A montagem seguinte aplica o pedido ao mapa (aplicar_pedido). O pedido fica (como o de
# nivel): e' dele que sai a grafia do nome confirmado e a versao que entra na impressao do dossie.
#
#   nomes_decididos.json = {"versao": n, "decisoes": {chave: {"valor", "decisao"}}}
#
# "decisao": NOME, NAO_NOME ou REVOGADA (o juiz desfez a decisao: a montagem tira a chave de
# mapa["nomes_decididos"] e o candidato volta a ser avaliado — incerto, se nada o provar).
#
# "revisao" (rodada de correcao 3) sobe a CADA gravacao (decisao, correcao, desfazer) e entra na impressao do
# dossie ("nomes_revisao", so' quando > 0): a montagem seguinte aplica o pedido — tambem o "nao e' nome" e o
# desfazer, que sem ela seriam pulados com a execucao "feita". Nao bloqueia a copia nem a minuta.
# "versao" sobe a cada decisao que muda o que vai em codigo (o NOME novo de candidato em claro e todo nome
# digitado na correcao): entra na impressao do dossie (nivel.impressao, "nomes_confirmados") e o dossie montado
# antes dela fica a preparar (a_preparar).
NOME_PEDIDO = "nomes_decididos.json"            # na raiz da pasta do processo, no acervo (local)
MAX_NOMES_NA_CORRECAO = 5
REVOGADA = "revogada"
_LETRA_OU_SINAL = re.compile(r"^[^\W\d_]+(?:[-'’][^\W\d_]+)*$")


def _vazio() -> dict:
    return {"versao": 0, "revisao": 0, "decisoes": {}}


def _contador(valor) -> int:
    return valor if isinstance(valor, int) and not isinstance(valor, bool) and valor > 0 else 0


def ler_pedido(dossie: Path | None) -> dict:
    """O pedido gravado pela tela; sem ele, ilegivel ou fora do formato, nada decidido (versao 0)."""
    if dossie is None:
        return _vazio()
    try:
        dados = json.loads((Path(dossie) / NOME_PEDIDO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _vazio()
    if not isinstance(dados, dict) or not isinstance(dados.get("decisoes"), dict):
        return _vazio()
    versao_ = dados.get("versao")
    decisoes = {normalizar(str(v.get("valor"))): {"valor": str(v.get("valor")), "decisao": v.get("decisao")}
                for v in dados["decisoes"].values()
                if isinstance(v, dict) and isinstance(v.get("valor"), str) and v.get("decisao") in (NOME, NAO_NOME, REVOGADA)}
    return {"versao": _contador(versao_), "revisao": _contador(dados.get("revisao")), "decisoes": decisoes}


def versao(dossie: Path | None) -> int:
    return ler_pedido(dossie)["versao"]


def revisao(dossie: Path | None) -> int:
    return ler_pedido(dossie)["revisao"]


def _gravar_pedido(dossie: Path, dados: dict) -> None:
    """Escrita atomica (o pedido truncado seria lido como "nada decidido"). Import tardio, como em nivel._gravar."""
    from .mapa import escrever_atomico
    dados["revisao"] = int(dados.get("revisao") or 0) + 1        # toda gravacao: a montagem seguinte a aplica
    Path(dossie).mkdir(parents=True, exist_ok=True)
    escrever_atomico(Path(dossie) / NOME_PEDIDO, json.dumps(dados, ensure_ascii=False, indent=1))


def _anotar(dados: dict, valor: str, o_que: str) -> bool:
    """Anota a decisao; True quando ela e' um NOME que ainda nao estava decidido como NOME."""
    valor = " ".join(valor.split())
    chave = normalizar(valor)
    antes = (dados["decisoes"].get(chave) or {}).get("decisao")
    dados["decisoes"][chave] = {"valor": valor, "decisao": o_que}
    return o_que == NOME and antes != NOME


def gravar_decisao(dossie: Path, valor: str, o_que: str, *, em_codigo: bool) -> bool:
    """O juiz confirmou (NOME) ou descartou (NAO_NOME) o candidato. Devolve True quando a decisao muda o que vai
    em codigo — o NOME novo de candidato que estava em claro: o dossie tem de ser preparado de novo. O NAO_NOME
    de candidato ja' em codigo (desativar o codigo) fica so' gravado: a montagem ainda nao o desfaz."""
    if o_que not in (NOME, NAO_NOME):
        raise ValueError(o_que)
    dados = ler_pedido(dossie)
    muda = _anotar(dados, valor, o_que) and not em_codigo
    if muda:
        dados["versao"] += 1
    _gravar_pedido(dossie, dados)
    return muda


def nome_valido(texto) -> str | None:
    """O nome digitado na correcao, com os espacos arrumados, ou None: so' letras, espacos, hifen e apostrofo;
    de 2 a 8 palavras; de 5 a 80 caracteres; sem separador de dois nomes ("e", "ou", travessao — rodada de
    correcao 1: dois nomes numa linha virariam um codigo so', e a segunda pessoa ficaria em claro)."""
    if not isinstance(texto, str) or "\n" in texto or "\r" in texto:
        return None
    limpo = " ".join(texto.split())
    palavras = limpo.split(" ")
    if not (5 <= len(limpo) <= 80) or not (2 <= len(palavras) <= 8):
        return None
    if not all(_LETRA_OU_SINAL.match(p) for p in palavras):
        return None
    return None if dois_nomes(limpo) else limpo


def dois_nomes(texto: str) -> bool:
    """O trecho parece trazer dois nomes (rodada de correcao 2): ele se abre em dois pelo criterio do
    pseudonimizador (a parte depois do separador tem 2+ palavras significativas e abre por prenome —
    _nomes_que_se_abrem, "João Silva e Ana Silva"), ou tem um separador que nao e' o "e" (travessao, ponto, "ou").
    O "e" seguido de sobrenome ("… Pereira e Silva") e' um nome so'."""
    from .pseudonimizador import _nomes_que_se_abrem, tem_separador   # import tardio: ele importa este modulo
    texto = " ".join((texto or "").split())
    if len(_nomes_que_se_abrem(texto)) > 1:
        return True
    return tem_separador(" ".join(w for w in texto.split() if normalizar(w) != "e"))


def talvez_dois(texto: str) -> bool:
    """O "e" que nao abre dois nomes: um nome so' ("Pereira e Silva") ou duas pessoas que o criterio nao
    reconhece (prenomes desconhecidos). A tela deixa confirmar inteiro, com o aviso, ou corrigir."""
    from .pseudonimizador import tem_separador
    return tem_separador(texto or "") and not dois_nomes(texto)


def gravar_correcao(dossie: Path, valor: str, nomes, *, em_codigo: bool = False) -> bool:
    """O juiz corrigiu o candidato: ele fica NAO_NOME e cada nome digitado, NOME (o nome igual ao candidato e' a
    confirmacao dele). ValueError para a lista vazia, com mais de MAX_NOMES_NA_CORRECAO ou com nome invalido —
    nada e' gravado. Devolve True (e sobe a versao) so' quando algum nome passa a ir em codigo: o proprio
    candidato que ja' estava em codigo (`em_codigo`) nao conta."""
    if not isinstance(nomes, list) or not 1 <= len(nomes) <= MAX_NOMES_NA_CORRECAO:
        raise ValueError("lista de nomes inválida")
    limpos = [nome_valido(n) for n in nomes]
    if any(n is None for n in limpos):
        raise ValueError("nome inválido")
    dados = ler_pedido(dossie)
    chaves = {normalizar(n) for n in limpos}
    if normalizar(valor) not in chaves:
        _anotar(dados, valor, NAO_NOME)
    muda = False
    for n in limpos:
        novo = _anotar(dados, n, NOME)
        muda = (novo and not (em_codigo and normalizar(n) == normalizar(valor))) or muda
    if muda:
        dados["versao"] += 1
    _gravar_pedido(dossie, dados)
    return muda


def desfazer(dossie: Path, valor: str) -> None:
    """O juiz desfez a decisao sobre `valor` (rodada de correcao 1): ela fica revogada no pedido, e a montagem
    seguinte tira a chave do mapa. Nao sobe a versao: o codigo ja' criado por um NOME montado fica (o mapa nunca
    perde tóken); o candidato so' volta a ser avaliado. ValueError quando nao ha' decisao a desfazer."""
    dados = ler_pedido(dossie)
    chave = normalizar(" ".join((valor or "").split()))
    if (dados["decisoes"].get(chave) or {}).get("decisao") not in (NOME, NAO_NOME):
        raise ValueError("sem decisão a desfazer")
    dados["decisoes"][chave] = {"valor": dados["decisoes"][chave]["valor"], "decisao": REVOGADA}
    _gravar_pedido(dossie, dados)


def decididos(pedido: dict) -> list[dict]:
    """As decisoes em vigor do pedido ({valor, decisao}), na ordem em que foram tomadas (a tela as lista em "Ja'
    decididos", com o Desfazer)."""
    return [dict(i) for i in (pedido.get("decisoes") or {}).values() if i.get("decisao") in (NOME, NAO_NOME)]


def a_reavaliar(mapa: dict | None, pedido: dict) -> list[dict]:
    """As decisoes desfeitas que a montagem ainda nao tirou do mapa ({valor}): o trecho saiu dos incertos e so'
    volta a ser avaliado no proximo preparo (a tela o mostra assim, ate' la')."""
    no_mapa = (mapa or {}).get("nomes_decididos") or {}
    return [{"valor": i["valor"]} for i in (pedido.get("decisoes") or {}).values()
            if i.get("decisao") == REVOGADA and normalizar(i["valor"]) in no_mapa]


def tem_codigo(mapa: dict | None, valor: str) -> bool:
    """O trecho ja' tem codigo de pessoa no mapa (o valor ou um alias): o incerto que volta depois de desfeito um
    "e' nome" ja' montado continua em codigo no dossie."""
    chave = normalizar(valor or "")
    for info in ((mapa or {}).get("tokens") or {}).values():
        # o toquen descartado (o "nao e' nome" de trecho ja' em codigo, pseudonimizador.aplicar_descartes) nao conta
        if isinstance(info, dict) and info.get("categoria") == "pessoa" and info.get("descartado") is not True \
                and chave and any(
                normalizar(str(f or "")) == chave for f in [info.get("valor"), *(info.get("aliases") or [])]):
            return True
    return False


def a_confirmar(mapa: dict, pedido: dict) -> list[dict]:
    """Os incertos do mapa que o pedido ainda nao decidiu (o que a tela mostra antes da montagem seguinte)."""
    em_vigor = {normalizar(i["valor"]) for i in decididos(pedido)}
    return [i for i in pendentes(mapa) if normalizar(str(i.get("valor") or "")) not in em_vigor]


def aplicar_pedido(mapa: dict, pedido: dict) -> list[str]:
    """A montagem aplica o pedido ao mapa (decidir) e recebe os nomes confirmados, na grafia do juiz, para entrarem
    no mapa como pessoa."""
    nomes = []
    for item in (pedido.get("decisoes") or {}).values():
        if item["decisao"] == REVOGADA:
            # a decisao desfeita: o candidato volta a ser avaliado (a descoberta o anota de novo, se for o caso)
            (mapa.get("nomes_decididos") or {}).pop(normalizar(item["valor"]), None)
            continue
        decidir(mapa, item["valor"], item["decisao"])
        if item["decisao"] == NOME:
            nomes.append(item["valor"])
    return nomes


def a_preparar(versao_do_pedido: int, marcador: dict | None) -> bool:
    """O dossie montado (o marcador da execucao) e' anterior a' ultima decisao que muda o que vai em codigo."""
    if not versao_do_pedido:
        return False
    montada = (((marcador or {}).get("impressao") or {}).get("nivel") or {}).get("nomes_confirmados", 0)
    return montada != versao_do_pedido
