# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Geração da saída: formato (layout original ou só texto), tipo (DOCX ou
PDF) e modo (reversível ou definitivo), com conferência ao final."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..motor.trocas import aplicar_trocas
from . import mapas
from .conferencia import VazamentoDetectado, conferir, valores_vigiados  # noqa: F401

PREFIXO_ID = "pseudonimizador:"


@dataclass
class Gerado:
    saida: Path
    mapa: Path | None
    avisos: list[str] = field(default_factory=list)


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
    destino = _destino(pasta_saida, f"{Path(documento.caminho).stem} - {rotulo}", f".{tipo}")
    identificador = mapas.novo_id(Path(documento.caminho).stem) if modo == "reversivel" else ""
    avisos = list(documento.avisos)

    if formato == "texto":
        from .texto import gerar_docx_texto, gerar_pdf_texto
        texto = aplicar_trocas(documento.texto, resultado.trocas)
        (gerar_docx_texto if tipo == "docx" else gerar_pdf_texto)(texto, destino)
        paginas_ocr: list[int] = []
    elif tipo == "docx":
        from .docx_layout import gerar_docx_layout
        gerar_docx_layout(documento, resultado.trocas, destino,
                          identificador=PREFIXO_ID + identificador if identificador else "")
        paginas_ocr = []
    else:
        from .pdf_layout import gerar_pdf_layout
        avisos += gerar_pdf_layout(documento, resultado.trocas, destino)
        paginas_ocr = documento.paginas_ocr

    try:
        vazados = conferir(destino, resultado.mapa, paginas_ocr)
    except BaseException:
        destino.unlink(missing_ok=True)
        raise
    if vazados:
        destino.unlink(missing_ok=True)
        raise VazamentoDetectado(vazados)
    pulados = valores_vigiados(resultado.mapa, devolver_pulados=True)[1]
    if pulados:
        avisos.append(f"{len(pulados)} valor(es) curto(s) não conferido(s) automaticamente")

    caminho_mapa = None
    if modo == "reversivel":
        _, caminho_mapa = mapas.gravar(pasta_mapas, Path(documento.caminho).stem, resultado.mapa, identificador)
    return Gerado(destino, caminho_mapa, avisos)
