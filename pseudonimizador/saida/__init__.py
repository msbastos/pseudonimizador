# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Geração da saída: formato (layout original ou só texto), tipo (DOCX ou
PDF) e modo (reversível ou definitivo), com conferência ao final."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..motor.mapa import normalizar
from ..motor.trocas import aplicar_trocas
from . import mapas
from .conferencia import VazamentoDetectado, conferir, valores_vigiados  # noqa: F401

PREFIXO_ID = "pseudonimizador:"


@dataclass
class Gerado:
    saida: Path
    mapa: Path | None
    avisos: list[str] = field(default_factory=list)


_PALAVRA = re.compile(r"[^\W_]+")
_CONECTIVOS = {"da", "de", "do", "das", "dos", "e"}


def _palavras(texto: str) -> list[str]:
    return [normalizar(m.group()) for m in _PALAVRA.finditer(texto)]


def _base_anonima(stem: str, mapa: dict) -> str:
    """Nome do arquivo de entrada sem os valores do mapa. O nome é dividido em
    palavras (o que fica entre espaço, _, ., - e outros separadores, que são
    mantidos) comparadas sem caixa nem acento e sempre inteiras: um valor casa
    como a sua sequência de palavras, com quaisquer separadores entre elas, e
    vira o seu tóken sem colchetes (sequências mais longas primeiro). Cada
    palavra solta de nome de pessoa ou de empresa (3 letras ou mais, fora os
    conectivos) também vira o tóken: "Contrato Pereira" não guarda o
    sobrenome. Uma só passada pelo nome original: o tóken inserido não é relido."""
    sequencias: list[tuple[tuple[str, ...], str]] = []
    soltas: dict[str, str] = {}
    for tok, info in mapa.get("tokens", {}).items():
        palavras = tuple(_palavras(str(info.get("valor") or "")))
        if not palavras:
            continue
        rotulo = tok.strip("[]")
        sequencias.append((palavras, rotulo))
        if info.get("categoria") in ("pessoa", "pj"):
            for w in palavras:
                if len(w) >= 3 and w not in _CONECTIVOS:
                    soltas.setdefault(w, rotulo)
    sequencias.sort(key=lambda p: (-len(p[0]), -sum(map(len, p[0]))))
    achadas = list(_PALAVRA.finditer(stem))
    chaves = [normalizar(m.group()) for m in achadas]
    partes: list[str] = []
    fim_anterior = 0
    i = 0
    while i < len(achadas):
        for palavras, rotulo in sequencias:
            n = len(palavras)
            if tuple(chaves[i:i + n]) == palavras:
                break
        else:
            n, rotulo = 1, soltas.get(chaves[i])
        if rotulo is not None:
            partes.append(stem[fim_anterior:achadas[i].start()])
            partes.append(rotulo)
            fim_anterior = achadas[i + n - 1].end()
        i += n
    partes.append(stem[fim_anterior:])
    return "".join(partes).strip()


def _destino(pasta: Path, base: str, sufixo: str) -> Path:
    candidato = pasta / f"{base}{sufixo}"
    n = 2
    while candidato.exists():
        candidato = pasta / f"{base} ({n}){sufixo}"
        n += 1
    return candidato


def gerar(documento, resultado, *, formato: str, modo: str, pasta_saida: Path, pasta_mapas: Path,
          tipo: str | None = None) -> Gerado:
    if formato not in ("layout", "texto") or modo not in ("reversivel", "definitivo"):
        raise ValueError(f"formato/modo inválido: {formato}/{modo}")
    entrada = "docx" if documento.tipo == "docx" else "pdf"
    tipo = entrada if formato == "layout" else tipo
    if tipo not in ("docx", "pdf"):
        raise ValueError("no formato 'texto', escolha o tipo: docx ou pdf")
    pasta_saida = Path(pasta_saida)
    a, b = pasta_saida.resolve(), Path(pasta_mapas).resolve()
    if a == b or a in b.parents or b in a.parents:
        raise ValueError("a pasta dos mapas não pode ser a da saída nem ficar dentro dela (ou vice-versa)")
    pasta_saida.mkdir(parents=True, exist_ok=True)
    rotulo = "pseudonimizado" if modo == "reversivel" else "anonimizado"
    destino = _destino(pasta_saida, f"{_base_anonima(Path(documento.caminho).stem, resultado.mapa)} - {rotulo}", f".{tipo}")
    identificador = mapas.novo_id(Path(documento.caminho).stem) if modo == "reversivel" else ""
    avisos = list(documento.avisos)

    # o arquivo é escrito e conferido com um nome provisório (oculto) na mesma
    # pasta; só depois de passar na conferência recebe o nome final
    provisorio = destino.with_name(f".{destino.stem}.conferindo{destino.suffix}")
    id_completo = PREFIXO_ID + identificador if identificador else ""
    try:
        if formato == "texto":
            from .texto import gerar_docx_texto, gerar_pdf_texto
            texto = aplicar_trocas(documento.texto, resultado.trocas)
            if tipo == "docx":
                gerar_docx_texto(texto, provisorio, identificador=id_completo)
            else:
                gerar_pdf_texto(texto, provisorio)
            paginas_ocr: list[int] = []
        elif tipo == "docx":
            from .docx_layout import gerar_docx_layout
            gerar_docx_layout(documento, resultado.trocas, provisorio, identificador=id_completo)
            paginas_ocr = []
        else:
            from .pdf_layout import gerar_pdf_layout
            avisos += gerar_pdf_layout(documento, resultado.trocas, provisorio)
            paginas_ocr = documento.paginas_ocr
        vazados = conferir(provisorio, resultado.mapa, paginas_ocr)
        if vazados:
            raise VazamentoDetectado(vazados)
        os.replace(provisorio, destino)
    except BaseException:
        provisorio.unlink(missing_ok=True)
        raise
    pulados = valores_vigiados(resultado.mapa, devolver_pulados=True)[1]
    if pulados:
        avisos.append(f"{len(pulados)} valor(es) curto(s) não conferido(s) automaticamente")

    caminho_mapa = None
    if modo == "reversivel":
        try:
            _, caminho_mapa = mapas.gravar(pasta_mapas, Path(documento.caminho).stem, resultado.mapa, identificador)
        except BaseException:
            # saída reversível sem o mapa não se restaura: não fica
            destino.unlink(missing_ok=True)
            raise
    return Gerado(destino, caminho_mapa, avisos)
