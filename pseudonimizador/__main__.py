# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Linha de comando do Pseudonimizador. Sem subcomando, abre a janela.

  (nada)                                abre a janela (servidor local + Edge)
  detectar  ARQ --revisao R.json        detecta e grava a revisão para editar
  gerar     ARQ [--revisao R.json] ...  aplica a revisão e gera a saída
  restaurar ARQ.docx|--texto T.txt ...  devolve os nomes (modo reversível)
  configurar --pasta-base PASTA         grava a pasta dos arquivos e cria Entrada, Saida e Mapas (o instalador usa)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import VERSAO


def _revisao(arq: Path):
    from .leitura import ler
    from .revisao import Revisao
    return Revisao(ler(arq))


def _detectar(a) -> int:
    rev = _revisao(a.arquivo)
    dados = {"arquivo": str(a.arquivo), "acrescentar": [],
             "itens": [{"categoria": it.categoria, "valor": it.valor, "aceito": it.aceito,
                        "exemplo": rev.contexto(*it.ocorrencias[0])} for it in rev.itens]}
    Path(a.revisao).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(rev.itens)} item(ns) detectado(s); revise {a.revisao} e rode 'gerar'.")
    print("Atenção: o arquivo de revisão contém os dados em claro; guarde-o com cuidado.")
    for aviso in rev.documento.avisos:
        print(f"aviso: {aviso}")
    return 0


def _ler_revisao_json(caminho: Path, arquivo: Path) -> dict:
    try:
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"revisão inválida (JSON): {e}") from e
    if not isinstance(dados, dict):
        raise ValueError("revisão inválida: esperado um objeto JSON")
    if dados.get("arquivo") and Path(dados["arquivo"]).name != Path(arquivo).name:
        print("aviso: a revisão é de outro arquivo", file=sys.stderr)
        raise ValueError(f"a revisão foi feita para {Path(dados['arquivo']).name}, não para {Path(arquivo).name}")
    for i in dados.get("itens", []):
        for campo in ("categoria", "valor", "aceito"):
            if not isinstance(i, dict) or campo not in i:
                raise ValueError(f"revisão inválida: item sem o campo '{campo}'")
    for e in dados.get("acrescentar", []):
        if not isinstance(e, dict) or "valor" not in e:
            raise ValueError("revisão inválida: item de 'acrescentar' sem o campo 'valor'")
    return dados


def _gerar(a) -> int:
    from .motor.mapa import normalizar
    from .saida import gerar
    dados = _ler_revisao_json(a.revisao, a.arquivo) if a.revisao else None
    rev = _revisao(a.arquivo)
    if dados is not None:
        decisoes = {(i["categoria"], normalizar(i["valor"])): bool(i["aceito"]) for i in dados.get("itens", [])}
        for it in rev.itens:
            if it.chave in decisoes:
                it.aceito = decisoes[it.chave]
        for extra in dados.get("acrescentar", []):
            rev.acrescentar(extra["valor"], extra.get("categoria", "pessoa"))
    g = gerar(rev.documento, rev.fechar(), formato=a.formato, tipo=a.tipo, modo=a.modo,
              pasta_saida=Path(a.saida), pasta_mapas=Path(a.mapas))
    print(f"saída: {g.saida}")
    if g.mapa:
        print(f"mapa (guarde à parte): {g.mapa}")
    for aviso in g.avisos:
        print(f"aviso: {aviso}")
    return 0


def _restaurar(a) -> int:
    if (a.arquivo is None) == (a.texto is None):
        raise ValueError("informe exatamente um entre ARQUIVO.docx e --texto")
    if a.arquivo is not None and a.saida is None:
        raise ValueError("--saida é obrigatório ao restaurar um DOCX")
    from .restaurar import mapa_do_docx, restaurar_docx, restaurar_texto
    from .saida import mapas
    if a.mapa:
        mapa = mapas.carregar(a.mapa)
    elif a.texto:
        raise ValueError("para texto colado, informe --mapa")
    else:
        mapa = mapa_do_docx(a.arquivo, Path(a.mapas))
        if mapa is None:
            raise ValueError("mapa não encontrado para este DOCX; informe --mapa")
    if a.texto:
        print(restaurar_texto(Path(a.texto).read_text(encoding="utf-8"), mapa))
    else:
        n = restaurar_docx(a.arquivo, Path(a.saida), mapa)
        print(f"{n} troca(s); restaurado: {a.saida}")
    return 0


def _configurar(a) -> int:
    """Grava a pasta dos arquivos na config (mantendo os outros campos, se já havia
    config) e cria as pastas. O instalador chama isto ao terminar."""
    from dataclasses import asdict
    from . import estado
    pasta = estado.pasta_estado()
    dados = asdict(estado.carregar(pasta))
    dados["pasta_base"] = str(a.pasta_base)
    cfg = estado.validar(dados)
    pasta.mkdir(parents=True, exist_ok=True)
    estado.preparar_pastas(cfg)        # antes de gravar: pasta impossível não troca a config
    estado.gravar(pasta, cfg)
    print(f"pasta dos arquivos: {cfg.pasta_base}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="pseudonimizador", description=f"Pseudonimizador {VERSAO} — sem subcomando, abre a janela")
    sub = p.add_subparsers(dest="comando", required=False)
    d = sub.add_parser("detectar")
    d.add_argument("arquivo", type=Path)
    d.add_argument("--revisao", type=Path, required=True)
    g = sub.add_parser("gerar")
    g.add_argument("arquivo", type=Path)
    g.add_argument("--revisao", type=Path)
    g.add_argument("--formato", choices=("layout", "texto"), required=True)
    g.add_argument("--tipo", choices=("docx", "pdf"))
    g.add_argument("--modo", choices=("reversivel", "definitivo"), required=True)
    g.add_argument("--saida", type=Path, required=True)
    g.add_argument("--mapas", type=Path, required=True)
    r = sub.add_parser("restaurar")
    r.add_argument("arquivo", type=Path, nargs="?")
    r.add_argument("--texto", type=Path)
    r.add_argument("--saida", type=Path)
    r.add_argument("--mapa", type=Path)
    r.add_argument("--mapas", type=Path, default=Path("Mapas"))
    c = sub.add_parser("configurar", help="grava a pasta dos arquivos (o instalador usa)")
    c.add_argument("--pasta-base", type=Path, required=True)
    a = p.parse_args(argv)
    if a.comando is None:
        from .web import abrir
        return abrir.principal()

    from .leitura import ErroDeLeitura
    from .restaurar import TokenOrfao
    from .saida import VazamentoDetectado
    try:
        return {"detectar": _detectar, "gerar": _gerar, "restaurar": _restaurar,
                "configurar": _configurar}[a.comando](a)
    except (ErroDeLeitura, ValueError, OSError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    except VazamentoDetectado as e:
        print(f"erro: {e}:", file=sys.stderr)
        for v in e.valores:
            print(f"  - {v}", file=sys.stderr)
        return 3
    except TokenOrfao as e:
        print(f"erro: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
