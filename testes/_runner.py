# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Runner dos testes (sem pytest). No fim de cada testes/test_*.py:

    if __name__ == "__main__":
        from _runner import rodar
        rodar(globals())

Roda toda função test_* em ordem alfabética, imprime ok/FALHA e sai com 1
se houver falha (é o que testes/executar_todos.py lê)."""
import os
import sys


def rodar(globais: dict) -> None:
    os.environ.setdefault("PSEUDONIMIZADOR_TESTE", "1")
    testes = [(n, f) for n, f in sorted(globais.items()) if n.startswith("test_") and callable(f)]
    falhas = 0
    for nome, fn in testes:
        try:
            fn()
            print(f"ok    {nome}")
        except AssertionError as e:
            falhas += 1
            print(f"FALHA {nome}\n      {e}")
        except Exception as e:  # noqa: BLE001
            falhas += 1
            print(f"FALHA {nome}\n      {e!r}")
    print(f"\n{len(testes) - falhas}/{len(testes)} passaram, {falhas} falha(s)")
    sys.exit(1 if falhas else 0)
