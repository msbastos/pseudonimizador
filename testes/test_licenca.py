# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Guarda de licença e autoria: cabeçalho SPDX em todo .py, LICENSE e CREDITOS."""
import _base  # noqa: F401
import subprocess
from _base import RAIZ

L1 = "# SPDX-License-Identifier: AGPL-3.0-only"
L2 = "# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md."


def _arquivos_do_projeto() -> list[str]:
    saida = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                           cwd=RAIZ, capture_output=True, text=True, encoding="utf-8").stdout
    return [l for l in saida.splitlines() if l.strip()]


def test_todo_py_tem_cabecalho_spdx():
    sem = []
    for rel in _arquivos_do_projeto():
        if rel.endswith(".py"):
            linhas = (RAIZ / rel).read_text(encoding="utf-8").splitlines()[:2]
            if linhas != [L1, L2]:
                sem.append(rel)
    assert not sem, f"sem cabeçalho SPDX: {sem}"


def test_licenca_e_creditos():
    assert (RAIZ / "LICENSE").read_text(encoding="utf-8").lstrip().startswith("GNU AFFERO GENERAL PUBLIC LICENSE")
    creditos = (RAIZ / "CREDITOS.md").read_text(encoding="utf-8")
    assert "Maurício Schmidt Bastos" in creditos and "Ulpiano" in creditos


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
