# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Gera requirements.lock (com --hash=sha256) para Python 3.14 x64 Windows.

Uso (na raiz do repositório, com internet — este é um dos dois únicos scripts
do projeto que usam a rede; o app e os testes nunca):
    .venv\\Scripts\\python -X utf8 empacotamento/gerar_lock.py

1. pip download de requirements.txt (só wheels, para o interpretador que roda);
2. tira o opencv-python (o rapidocr o declara) e baixa, na MESMA versão,
   o opencv-python-headless (sem GUI: menos 30 MB); tira sympy e mpmath
   (dependência declarada do onnxruntime que o OCR não usa ao rodar) —
   spec §2; a fumaça da montagem prova que o OCR funciona sem eles;
3. escreve requirements.lock: nome==versao --hash=sha256:... (instalado com
   --no-deps --require-hashes, por isso a lista é fechada).
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RE_WHEEL = re.compile(r"^(?P<nome>[^-]+)-(?P<versao>[^-]+)-.+\.whl$")
EXCLUIDOS = frozenset({"opencv-python", "sympy", "mpmath"})
SUBSTITUTO = "opencv-python-headless"


def nome_e_versao(wheel: Path) -> tuple[str, str]:
    m = RE_WHEEL.match(Path(wheel).name)
    if m is None:
        raise SystemExit(f"nome de wheel inesperado: {Path(wheel).name}")
    return m.group("nome").lower().replace("_", "-"), m.group("versao")


def filtrar(wheels: list[Path], excluidos: frozenset[str] = EXCLUIDOS) -> list[Path]:
    return [w for w in wheels if nome_e_versao(w)[0] not in excluidos]


def linhas_do_lock(wheels: list[Path]) -> list[str]:
    linhas = []
    for w in sorted(wheels, key=lambda p: p.name.lower()):
        nome, versao = nome_e_versao(w)
        linhas.append(f"{nome}=={versao} \\")
        linhas.append(f"    --hash=sha256:{hashlib.sha256(Path(w).read_bytes()).hexdigest()}")
    return linhas


def problemas_do_lock(nomes: set[str]) -> list[str]:
    probs = []
    if SUBSTITUTO not in nomes:
        probs.append(f"o lock não tem {SUBSTITUTO}")
    for n in sorted(nomes & EXCLUIDOS):
        probs.append(f"o lock ainda tem {n}")
    return probs


def _baixar_padrao(destino: Path, argumentos: list[str]) -> None:
    subprocess.run([sys.executable, "-m", "pip", "download", "-q", "-d", str(destino), "--only-binary=:all:",
                    *argumentos], check=True)


def main(argv=None, *, baixar=_baixar_padrao) -> int:
    ap = argparse.ArgumentParser(description="gera requirements.lock com hashes para o Python embarcado")
    ap.add_argument("--raiz", type=Path, default=RAIZ)
    args = ap.parse_args(argv)
    x64 = struct.calcsize("P") == 8
    if sys.version_info[:2] != (3, 14) or sys.platform != "win32" or not x64:
        print(f"Rode com o Python 3.14 x64 do Windows (este é {sys.version.split()[0]} em {sys.platform}).")
        return 2
    with tempfile.TemporaryDirectory() as td:
        pasta = Path(td)
        baixar(pasta, ["-r", str(args.raiz / "requirements.txt")])
        wheels = sorted(pasta.glob("*.whl"))
        versoes = dict(nome_e_versao(w) for w in wheels)
        if "opencv-python" in versoes and SUBSTITUTO not in versoes:
            baixar(pasta, ["--no-deps", f"{SUBSTITUTO}=={versoes['opencv-python']}"])
            wheels = sorted(pasta.glob("*.whl"))
        wheels = filtrar(wheels)
        if probs := problemas_do_lock({nome_e_versao(w)[0] for w in wheels}):
            print("\n".join(probs))
            return 2
        linhas = ["# Gerado por empacotamento/gerar_lock.py — NÃO editar à mão.",
                  "# Python 3.14 x64 Windows. Instalar com:",
                  "#   python -m pip install --no-deps --require-hashes -r requirements.lock",
                  ""] + linhas_do_lock(wheels)
        (args.raiz / "requirements.lock").write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")
        print(f"requirements.lock: {len(wheels)} pacotes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
