# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Guarda de licença e autoria: cabeçalho SPDX em todo .py, LICENSE e CREDITOS."""
import _base  # noqa: F401
import subprocess
from _base import RAIZ

L1 = "# SPDX-License-Identifier: AGPL-3.0-only"
L2 = "# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md."


def _arquivos_do_projeto(raiz=RAIZ) -> list[str]:
    """Arquivos rastreados e novos (não ignorados). Falha do git levanta
    CalledProcessError: a guarda nunca passa com a lista vazia."""
    saida = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                           cwd=raiz, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    arquivos = [l for l in saida.splitlines() if l.strip()]
    assert arquivos, "git ls-files não listou nenhum arquivo do projeto"
    return arquivos


def test_todo_py_tem_cabecalho_spdx():
    sem = []
    for rel in _arquivos_do_projeto():
        if rel.endswith(".py"):
            linhas = (RAIZ / rel).read_text(encoding="utf-8").splitlines()[:2]
            if linhas != [L1, L2]:
                sem.append(rel)
    assert not sem, f"sem cabeçalho SPDX: {sem}"


def test_guarda_nao_passa_em_vazio():
    """Fora de um repositório git, a lista de arquivos não pode sair vazia em silêncio."""
    import tempfile
    from pathlib import Path
    assert _arquivos_do_projeto(), "git ls-files devolveu lista vazia"
    with tempfile.TemporaryDirectory() as fora:
        try:
            _arquivos_do_projeto(Path(fora))
        except subprocess.CalledProcessError:
            pass
        else:
            raise AssertionError("git ls-files fora de um repositório deveria falhar")


def test_runner_sai_com_erro_sem_nenhum_teste():
    import sys
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as pasta:
        arquivo = Path(pasta) / "test_vazio.py"
        arquivo.write_text("import sys\nsys.path.insert(0, sys.argv[1])\n"
                           "from _runner import rodar\nrodar(globals())\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "-X", "utf8", str(arquivo), str(RAIZ / "testes")],
                           capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)


def test_licenca_e_creditos():
    assert (RAIZ / "LICENSE").read_text(encoding="utf-8").lstrip().startswith("GNU AFFERO GENERAL PUBLIC LICENSE")
    creditos = (RAIZ / "CREDITOS.md").read_text(encoding="utf-8")
    assert "Maurício Schmidt Bastos" in creditos and "Ulpiano" in creditos


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
