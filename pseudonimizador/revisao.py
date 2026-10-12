# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Revisão de um documento: os itens detectados (agrupados por categoria e
valor), as decisões do usuário e o fechamento em mapa + trocas (spec §6).
Tudo começa aceito: recusar é o gesto consciente."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .deteccao import detectar
from .motor.mapa import normalizar, novo_mapa, token_para
from .motor.trocas import Troca, trocas

PREFIXOS = {"pessoa": "PESSOA", "empresa": "EMPRESA", "cpf": "CPF", "cnpj": "CNPJ", "pis": "PIS",
            "rg": "RG", "ctps": "CTPS", "email": "EMAIL", "telefone": "TEL", "endereco": "ENDERECO",
            "conta": "CONTA", "url": "URL", "outro": "DADO"}
_CATEGORIA_NO_MAPA = {"empresa": "pj"}      # o motor chama empresa de "pj"


@dataclass
class Item:
    categoria: str
    valor: str
    ocorrencias: list[tuple[int, int]] = field(default_factory=list)
    aceito: bool = True
    acrescido: bool = False

    @property
    def chave(self) -> tuple[str, str]:
        return (self.categoria, normalizar(self.valor))


@dataclass
class Resultado:
    mapa: dict
    trocas: list[Troca]


def _buscar(texto: str, valor: str) -> list[tuple[int, int]]:
    """Ocorrências literais do valor, sem diferenciar maiúsculas e com
    qualquer espaço entre as palavras."""
    partes = valor.split()
    if not partes:
        return []
    padrao = r"(?<!\w)" + r"\s+".join(re.escape(p) for p in partes) + r"(?!\w)"
    return [m.span() for m in re.finditer(padrao, texto, re.I)]


class Revisao:
    def __init__(self, documento):
        self.documento = documento
        self.itens: list[Item] = []
        por_chave: dict[tuple[str, str], Item] = {}
        for o in detectar(documento.texto):
            novo = Item(o.categoria, o.valor)
            item = por_chave.setdefault(novo.chave, novo)
            if item is novo:
                self.itens.append(item)
            item.ocorrencias.append((o.ini, o.fim))
        for item in self.itens:                      # também as ocorrências sem âncora
            for span in _buscar(documento.texto, item.valor):
                if span not in item.ocorrencias:
                    item.ocorrencias.append(span)
            item.ocorrencias.sort()

    def item(self, chave: tuple[str, str]) -> Item:
        for it in self.itens:
            if it.chave == chave:
                return it
        raise KeyError(chave)

    def aceitar(self, chave) -> None:
        self.item(chave).aceito = True

    def recusar(self, chave) -> None:
        self.item(chave).aceito = False

    def acrescentar(self, valor: str, categoria: str = "pessoa") -> Item:
        valor = valor.strip()
        ocorrencias = _buscar(self.documento.texto, valor)
        if not ocorrencias:
            raise ValueError(f"não encontrado no documento: {valor!r}")
        item = Item(categoria, valor, ocorrencias, aceito=True, acrescido=True)
        self.itens.append(item)
        return item

    def contexto(self, ini: int, fim: int, largura: int = 60) -> str:
        t = self.documento.texto
        return t[max(0, ini - largura):fim + largura].replace("\n", " ")

    def _token(self, mapa: dict, item: Item) -> str:
        return token_para(mapa, PREFIXOS.get(item.categoria, item.categoria.upper()),
                          _CATEGORIA_NO_MAPA.get(item.categoria, item.categoria), item.valor)

    def fechar(self) -> Resultado:
        texto = self.documento.texto
        mapa = novo_mapa()
        aceitos = [it for it in self.itens if it.aceito]
        recusados = {(_CATEGORIA_NO_MAPA.get(it.categoria, it.categoria), normalizar(it.valor))
                     for it in self.itens if not it.aceito}
        for it in aceitos:
            if it.categoria in ("pessoa", "empresa"):
                self._token(mapa, it)
        # o motor guarda CPF/PIS só em dígitos: o recusado também se reconhece pela posição
        spans_recusados = [s for it in self.itens if not it.aceito for s in it.ocorrencias]
        lista = [t for t in trocas(texto, mapa)
                 if (mapa["tokens"][t.token]["categoria"], normalizar(mapa["tokens"][t.token]["valor"]))
                 not in recusados
                 and not any(a <= t.ini and t.fim <= b for a, b in spans_recusados)]
        # rede de segurança: toda ocorrência aceita que o motor não cobriu
        for it in aceitos:
            for a, b in it.ocorrencias:
                if all(b <= t.ini or a >= t.fim for t in lista):
                    lista.append(Troca(a, b, self._token(mapa, it)))
        lista.sort()
        usados = {t.token for t in lista}
        mapa["tokens"] = {tok: info for tok, info in mapa["tokens"].items() if tok in usados}
        return Resultado(mapa, lista)
