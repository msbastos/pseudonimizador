# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Trocas com posição no texto ORIGINAL (spec §4): o motor trabalha sobre o
texto limpo (NFC, sem invisíveis); aqui se guarda, para cada caractere do
texto limpo, de onde ele veio, e as trocas voltam para as posições originais."""
from __future__ import annotations

import unicodedata
from typing import NamedTuple

from .pseudonimizador import (RE_CITACAO_DE_DOCUMENTO, RE_INVISIVEIS, _RE_SEPARADOR_INVISIVEL,
                              _copia_com_nomes, _spans_finais, texto_limpo)


class Troca(NamedTuple):
    ini: int
    fim: int
    token: str


def _nfc_rastreado(s: str, ini: list[int], fim: list[int]):
    """NFC grupo a grupo (caractere-base + combinantes); cada caractere
    resultante herda o início do primeiro e o fim do último do grupo."""
    out: list[str] = []
    oi: list[int] = []
    of: list[int] = []
    j, n = 0, len(s)
    while j < n:
        k = j + 1
        while k < n and unicodedata.combining(s[k]):
            k += 1
        grupo = unicodedata.normalize("NFC", s[j:k])
        out.append(grupo)
        oi.extend([ini[j]] * len(grupo))
        of.extend([fim[k - 1]] * len(grupo))
        j = k
    return "".join(out), oi, of


def _sub_rastreado(regex, repl: str, s: str, ini: list[int], fim: list[int]):
    """regex.sub(repl, s) guardando a origem: o trecho trocado por `repl`
    (um caractere ou nada) herda o início e o fim do trecho."""
    out: list[str] = []
    oi: list[int] = []
    of: list[int] = []
    pos = 0
    for m in regex.finditer(s):
        a, b = m.span()
        if a == b:
            continue
        out.append(s[pos:a]); oi.extend(ini[pos:a]); of.extend(fim[pos:a])
        if repl:
            out.append(repl); oi.append(ini[a]); of.append(fim[b - 1])
        pos = b
    out.append(s[pos:]); oi.extend(ini[pos:]); of.extend(fim[pos:])
    return "".join(out), oi, of


def limpar_com_indices(texto: str) -> tuple[str, list[int], list[int]]:
    """O mesmo que texto_limpo(texto), com a origem de cada caractere."""
    ini = list(range(len(texto)))
    fim = [i + 1 for i in ini]
    s, ini, fim = _nfc_rastreado(texto, ini, fim)
    s, ini, fim = _sub_rastreado(_RE_SEPARADOR_INVISIVEL, " ", s, ini, fim)
    s, ini, fim = _sub_rastreado(RE_INVISIVEIS, "", s, ini, fim)
    s, ini, fim = _nfc_rastreado(s, ini, fim)
    if s != texto_limpo(texto):
        raise ValueError("a normalização por grupo divergiu da do texto inteiro")
    return s, ini, fim


def trocas(texto: str, mapa: dict, conversa: bool = False) -> list[Troca]:
    limpo, ini, fim = limpar_com_indices(texto)
    citacoes = [m.span() for m in RE_CITACAO_DE_DOCUMENTO.finditer(limpo)]
    copia = _copia_com_nomes(limpo, mapa, citacoes) if citacoes else None
    return [Troca(ini[a], fim[b - 1], tok) for a, b, tok in _spans_finais(limpo, mapa, copia, conversa)]


def aplicar_trocas(texto: str, lista: list[Troca]) -> str:
    partes: list[str] = []
    pos = 0
    for t in sorted(lista):
        partes.append(texto[pos:t.ini])
        partes.append(t.token)
        pos = t.fim
    partes.append(texto[pos:])
    return "".join(partes)
