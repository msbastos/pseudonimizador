# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Candidatos a nome de pessoa e de empresa num documento avulso (sem capa do
PJe): âncoras de qualificação de contrato, a qualificação depois do nome, o
léxico de prenomes e sobrenomes do motor e os sufixos societários. Tudo é
sugestão: a revisão humana decide (spec §6). A caixa não decide nada."""
from __future__ import annotations

import re

from ..motor.lexico import SOBRENOMES, frequencia_de_sobrenome
from ..motor.mapa import normalizar
from ..motor.pseudonimizador import CONECTIVOS, RE_SUFIXO_PJ, _NUNCA_NOME, _prenome_provado

RE_PALAVRA = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*")
RE_SO_ESPACO = re.compile(r"[ \t\u00a0]{1,3}")

RE_ANCORA = re.compile(
    r"(?i)\b(?:contratante|contratad[ao]|locador[a]?|locat[áa]ri[ao]|outorgante|outorgad[ao]|"
    r"comprador[a]?|vendedor[a]?|promitentes?\s+(?:comprador|vendedor)[a]?|fiador[a]?|cedente|"
    r"cession[áa]ri[ao]|empregador[a]?|empregad[ao]|testemunhas?|representante\s+legal|s[óo]ci[ao]|"
    r"procurador[a]?|interveniente|devedor[a]?|credor[a]?)\s*(?:\d+\s*)?[:\-–—]\s*"
    r"|(?i:\brepresentad[ao]\s+(?:neste\s+ato\s+)?por\s+)"
    r"|(?i:\b(?:raz[ãa]o\s+social|denominad[ao])\s*:?\s+)")
RE_QUALIFICACAO = re.compile(
    r"(?i),\s*(?:brasileir[oa]|estrangeir[oa]|nacionalidade|portador[a]?|inscrit[oa]|CPF|CNPJ|RG|"
    r"estado\s+civil|solteir[oa]|casad[oa]|divorciad[oa]|vi[úu]v[oa]|maior|menor)\b")
RE_SUFIXO = re.compile(r"(?<!\w)(?:ltda\.?|s\.\s?a\.?|s/a|eireli|epp|ME|SLU)(?!\w)", re.I)
_SUFIXO_EXIGE_DUAS = {"me", "epp", "slu"}

_PARADAS = {"brasileiro", "brasileira", "estrangeiro", "estrangeira", "portador", "portadora",
            "inscrito", "inscrita", "residente", "domiciliado", "domiciliada", "casado", "casada",
            "solteiro", "solteira", "nacionalidade", "neste", "ato", "doravante", "pessoa", "empresa",
            "sociedade", "com", "sede", "cpf", "cnpj", "rg", "denominado", "denominada", "representado",
            "representada", "que", "para", "por", "pelo", "pela", "o", "a", "os", "as", "sr", "sra",
            "senhor", "senhora", "entre", "em", "no", "na", "ao", "firma", "razao", "social"}
MAX_PALAVRAS = 8


def _sobrenome(n: str) -> bool:
    return (n in SOBRENOMES or frequencia_de_sobrenome(n) > 0) and n not in _NUNCA_NOME and n not in CONECTIVOS


def _significativas(nome: str) -> int:
    return sum(1 for w in nome.split() if normalizar(w) not in CONECTIVOS)


def _ler_adiante(s: str, pos: int) -> tuple[int, int] | None:
    """Palavras a partir de `pos`, separadas por espaço simples, até pontuação,
    quebra de linha ou palavra de parada. Tira conectivos do fim."""
    palavras = []
    i = pos
    while len(palavras) < MAX_PALAVRAS:
        m = RE_PALAVRA.match(s, i)
        if not m or normalizar(m.group()) in _PARADAS:
            break
        palavras.append(m)
        prox = RE_SO_ESPACO.match(s, m.end())
        if not prox:
            break
        i = prox.end()
    while palavras and normalizar(palavras[-1].group()) in CONECTIVOS:
        palavras.pop()
    if not palavras:
        return None
    ini, fim = palavras[0].start(), palavras[-1].end()
    # sufixo societário logo depois ("... Tecidos Ltda.") faz parte do nome
    suf = re.compile(r"\s*" + RE_SUFIXO.pattern, re.I).match(s, fim)
    if suf:
        fim = suf.end()
    return (ini, fim) if _significativas(s[ini:fim]) >= 2 else None


def _ler_atras(s: str, pos: int) -> tuple[int, int] | None:
    """Palavras imediatamente antes de `pos`, de trás para a frente, até
    pontuação ou palavra de parada. Tira conectivos do começo."""
    palavras = [m for m in RE_PALAVRA.finditer(s, max(0, pos - 200), pos)]
    escolhidas = []
    fim_esperado = pos
    for m in reversed(palavras):
        if not RE_SO_ESPACO.fullmatch(s[m.end():fim_esperado]) and m.end() != fim_esperado:
            break
        if normalizar(m.group()) in _PARADAS or len(escolhidas) >= MAX_PALAVRAS:
            break
        escolhidas.insert(0, m)
        fim_esperado = m.start()
    while escolhidas and normalizar(escolhidas[0].group()) in CONECTIVOS:
        escolhidas.pop(0)
    if not escolhidas:
        return None
    ini, fim = escolhidas[0].start(), escolhidas[-1].end()
    return (ini, fim) if _significativas(s[ini:fim]) >= 2 else None


def _categoria(nome: str, contexto: str = "") -> str:
    return "empresa" if RE_SUFIXO_PJ.search(nome) or RE_SUFIXO.search(nome) or "cnpj" in contexto.lower() \
        else "pessoa"


def _por_ancora(s: str) -> list[tuple[int, int, str]]:
    achados = []
    for m in RE_ANCORA.finditer(s):
        span = _ler_adiante(s, m.end())
        if span:
            achados.append((*span, _categoria(s[span[0]:span[1]])))
    return achados


def _por_qualificacao(s: str) -> list[tuple[int, int, str]]:
    achados = []
    for m in RE_QUALIFICACAO.finditer(s):
        fim_nome = m.start()
        # "Ltda., inscrita": o sufixo com ponto antes da vírgula
        suf = None
        for sm in RE_SUFIXO.finditer(s, max(0, fim_nome - 8), fim_nome):
            if sm.end() == fim_nome:
                suf = sm
        span = _ler_atras(s, suf.start() if suf else fim_nome)
        if span:
            fim = suf.end() if suf else span[1]
            achados.append((span[0], fim, _categoria(s[span[0]:fim], m.group())))
    return achados


def _por_lexico(s: str) -> list[tuple[int, int, str]]:
    palavras = list(RE_PALAVRA.finditer(s))
    achados = []
    i = 0
    while i < len(palavras):
        if not _prenome_provado(palavras[i].group()):
            i += 1
            continue
        j, ultimo, tem_sobrenome = i, None, False
        while j + 1 < len(palavras) and RE_SO_ESPACO.fullmatch(s[palavras[j].end():palavras[j + 1].start()]):
            w = palavras[j + 1].group()
            n = normalizar(w)
            if n in CONECTIVOS:
                j += 1
                continue
            if _sobrenome(n) or _prenome_provado(w):
                j += 1
                ultimo = j
                tem_sobrenome = tem_sobrenome or _sobrenome(n)
                continue
            break
        if ultimo is not None and tem_sobrenome:
            achados.append((palavras[i].start(), palavras[ultimo].end(), "pessoa"))
            i = ultimo + 1
        else:
            i += 1
    return achados


def _por_sufixo(s: str) -> list[tuple[int, int, str]]:
    achados = []
    for m in RE_SUFIXO.finditer(s):
        span = _ler_atras(s, m.start())
        if not span:
            continue
        if normalizar(m.group()).strip(".") in _SUFIXO_EXIGE_DUAS and _significativas(s[span[0]:span[1]]) < 2:
            continue
        achados.append((span[0], m.end(), "empresa"))
    return achados


def pessoas_e_empresas(limpo: str) -> list[tuple[int, int, str]]:
    todos = _por_ancora(limpo) + _por_qualificacao(limpo) + _por_sufixo(limpo) + _por_lexico(limpo)
    # o mais longo primeiro; empresa vence pessoa no mesmo trecho
    todos.sort(key=lambda a: (a[0], -(a[1] - a[0]), a[2] != "empresa"))
    escolhidos: list[tuple[int, int, str]] = []
    for a in todos:
        if all(a[1] <= b[0] or a[0] >= b[1] for b in escolhidos):
            escolhidos.append(a)
    return sorted(escolhidos)
