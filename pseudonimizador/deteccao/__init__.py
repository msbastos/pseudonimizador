# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Detecção: os identificadores do motor (CPF, CNPJ, e-mail, telefone,
endereço…) e os candidatos a pessoa e empresa, com posição no texto original."""
from __future__ import annotations

from dataclasses import dataclass

from ..motor.mapa import novo_mapa
from ..motor.pseudonimizador import RE_CNPJ, _spans_de_identificadores
from ..motor.trocas import limpar_com_indices
from .candidatos import pessoas_e_empresas


@dataclass(frozen=True)
class Ocorrencia:
    ini: int
    fim: int
    categoria: str
    valor: str


def _identificadores(limpo: str) -> list[tuple[int, int, str]]:
    rascunho = novo_mapa()
    achados = [(a, b, rascunho["tokens"][tok]["categoria"])
               for a, b, tok in _spans_de_identificadores(limpo, rascunho)]
    achados += [(m.start(), m.end(), "cnpj") for m in RE_CNPJ.finditer(limpo)]
    return achados


def detectar(texto: str) -> list[Ocorrencia]:
    limpo, ini, fim = limpar_com_indices(texto)
    nomes = pessoas_e_empresas(limpo)
    # nomes primeiro (como no motor): identificador que cruza um nome cede
    candidatos = nomes + [i for i in _identificadores(limpo)
                          if all(i[1] <= n[0] or i[0] >= n[1] for n in nomes)]
    candidatos.sort(key=lambda a: (a[0], -(a[1] - a[0])))
    saida: list[Ocorrencia] = []
    for a, b, cat in candidatos:
        o_ini, o_fim = ini[a], fim[b - 1]
        if saida and o_ini < saida[-1].fim:
            continue
        saida.append(Ocorrencia(o_ini, o_fim, cat, texto[o_ini:o_fim]))
    return saida
