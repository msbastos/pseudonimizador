# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
# Origem: Ulpiano, ulpiano/nucleo/privacidade/mapa.py, commit 5bab2ff (11/10/2026); alterações descritas abaixo.
"""
==============================================================
 ARQUIVO: mapa.py
 PROJETO: AnaliseDeProcessos / privacidade
 VERSAO:  0.1.0
 ATUALIZADO: 2026-09-03
 ALTERACAO 0.1.0: versao inicial. Tokens estaveis para dados
   sensíveis: mesma chave normalizada sempre retorna o mesmo
   token; token atribuido jamais muda de dono. Gravacao
   atomica via arquivo temporario.
==============================================================
"""
from __future__ import annotations
import json, os, re, unicodedata
from datetime import datetime
from pathlib import Path

NOME_ARQUIVO_MAPA = "mapa_pseudonimos.json"
SCHEMA_VERSION = 1

def normalizar(s: str) -> str:
    """Chave de comparacao: sem acentos, caixa baixa, espacos colapsados."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().casefold()

def carregar_mapa(pasta_processo: Path, cnj: str) -> dict:
    caminho = pasta_processo / NOME_ARQUIVO_MAPA
    if caminho.is_file():
        return json.loads(caminho.read_text(encoding="utf-8"))
    return {"schema_version": SCHEMA_VERSION, "cnj": cnj,
            "criado_em": datetime.now().isoformat(timespec="seconds"),
            "tokens": {}}

def gravar_mapa(pasta_processo: Path, mapa: dict) -> Path:
    pasta_processo.mkdir(parents=True, exist_ok=True)
    caminho = pasta_processo / NOME_ARQUIVO_MAPA
    tmp = caminho.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(mapa, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    os.replace(tmp, caminho)   # nunca deixa o mapa pela metade no disco
    return caminho

def token_para(mapa: dict, prefixo: str, categoria: str, valor: str,
               papel: str | None = None) -> str:
    """Token estavel: mesmo valor (normalizado) na mesma categoria devolve
    sempre o mesmo token; valor novo ganha o proximo numero do prefixo.
    Um token atribuido JAMAIS muda de dono (spec, secao 4.2)."""
    chave = normalizar(valor)
    for tok, info in mapa["tokens"].items():
        if info["categoria"] == categoria and normalizar(info["valor"]) == chave:
            return tok
    usados = [int(m.group(1)) for tok in mapa["tokens"]
              if (m := re.fullmatch(r"\[\[" + re.escape(prefixo) + r"_(\d+)\]\]", tok))]
    tok = f"[[{prefixo}_{max(usados, default=0) + 1}]]"
    info: dict = {"valor": valor, "categoria": categoria}
    if papel:
        info["papel"] = papel
    if categoria == "pessoa":
        info["variantes_vistas"] = []
    mapa["tokens"][tok] = info
    return tok


def escrever_atomico(caminho: Path, texto: str) -> None:
    """Grava num .tmp ao lado e troca de uma vez (os.replace): nunca deixa o
    arquivo pela metade. Substitui ulpiano.nucleo.execucao.escrever_atomico."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(caminho.suffix + ".tmp")
    tmp.write_text(texto, encoding="utf-8")
    os.replace(tmp, caminho)


def novo_mapa() -> dict:
    """Mapa vazio de um documento avulso: sempre no nível que troca nomes e empresas."""
    return {"schema_version": SCHEMA_VERSION, "nivel": "sigiloso",
            "criado_em": datetime.now().isoformat(timespec="seconds"), "tokens": {}}
