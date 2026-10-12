# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Roda a suíte inteira, cada arquivo no seu processo, em paralelo.
Arquivo marcado com "# executar_todos: sozinho" nas 15 primeiras linhas roda
depois, sozinho. PSEUDONIMIZADOR_TESTES_TRABALHOS=1 roda tudo em série."""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
MARCA_SOZINHO = "# executar_todos: sozinho"


def _rodar(arq: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-X", "utf8", str(arq)], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def _sozinho(arq: Path) -> bool:
    with open(arq, encoding="utf-8", errors="replace") as f:
        return any(l.startswith(MARCA_SOZINHO) for l, _ in zip(f, range(15)))


def _trabalhos() -> int:
    try:
        return max(1, int(os.environ["PSEUDONIMIZADOR_TESTES_TRABALHOS"]))
    except (KeyError, ValueError):
        return min(8, os.cpu_count() or 2)


def main() -> int:
    arquivos = sorted(RAIZ.glob("test_*.py"))
    os.environ["PSEUDONIMIZADOR_TESTE"] = "1"
    comuns = [a for a in arquivos if not _sozinho(a)]
    resultados = {}
    with ThreadPoolExecutor(max_workers=_trabalhos()) as pool:
        resultados.update(zip(comuns, pool.map(_rodar, comuns)))
    for arq in arquivos:
        if arq not in resultados:
            resultados[arq] = _rodar(arq)
    falharam = []
    for arq in arquivos:
        proc = resultados[arq]
        situacao = "ok   " if proc.returncode == 0 else "FALHA"
        print(f"{situacao} {arq.name}")
        if proc.returncode != 0:
            falharam.append(arq.name)
            for linha in (proc.stdout + proc.stderr).splitlines():
                if linha.startswith(("FALHA", "      ", "Traceback", "  File", "    ")) or "Error" in linha:
                    print(f"      {linha}")
    print(f"\n{len(arquivos) - len(falharam)}/{len(arquivos)} arquivos passaram")
    return 1 if falharam else 0


if __name__ == "__main__":
    sys.exit(main())
