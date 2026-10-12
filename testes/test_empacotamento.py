# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
# executar_todos: sozinho
"""Empacotamento: manifesto, lock, montagem (comandos externos falsos), fumaça,
pseudonimizador.iss, .wsb, ícone e roteiro. Nada aqui baixa nem compila.
Roda sozinho porque, quando build/app existe, a fumaça de verdade faz OCR."""
import _base  # noqa: F401
import tempfile
from pathlib import Path

from _base import RAIZ
from empacotamento import manifesto


def _arvore(tmp: Path, caminhos: list[str]) -> Path:
    for c in caminhos:
        p = tmp / c
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")
    return tmp


def test_manifesto_leva_o_aplicativo_e_deixa_o_que_e_do_mantenedor():
    with tempfile.TemporaryDirectory() as d:
        raiz = _arvore(Path(d), [
            "LICENSE", "CREDITOS.md", "README.md", "Pseudonimizador.bat", "requirements.txt", "requirements.lock",
            "pseudonimizador/__init__.py", "pseudonimizador/motor/lexico_ibge.json",
            "pseudonimizador/web/estatico/app.js", "pseudonimizador/__pycache__/x.pyc",
            "testes/test_x.py", "saida_testes/cli/contrato.docx", "docs/superpowers/plans/p.md",
            "docs/release-notes/v0.2.0.md", ".git/HEAD", ".claude/settings.json",
            "empacotamento/construir.py", "empacotamento/termos_proibidos.txt", "build/app/x", "dist/x.exe",
            "pseudonimizador/config.json", "pseudonimizador/instancia.json", "pseudonimizador/x.log"])
        rel = {p.as_posix() for p in manifesto.arquivos_do_pacote(raiz)}
    assert {"LICENSE", "CREDITOS.md", "README.md", "pseudonimizador/__init__.py",
            "pseudonimizador/motor/lexico_ibge.json", "pseudonimizador/web/estatico/app.js"} <= rel
    for fora in ("Pseudonimizador.bat", "requirements.txt", "requirements.lock", "pseudonimizador/__pycache__/x.pyc",
                 "testes/test_x.py", "saida_testes/cli/contrato.docx", "docs/superpowers/plans/p.md",
                 "docs/release-notes/v0.2.0.md", ".git/HEAD", ".claude/settings.json", "empacotamento/construir.py",
                 "empacotamento/termos_proibidos.txt", "build/app/x", "dist/x.exe", "pseudonimizador/config.json",
                 "pseudonimizador/instancia.json", "pseudonimizador/x.log"):
        assert fora not in rel, fora


def test_manifesto_acusa_o_que_nao_pode_viajar():
    probs = manifesto.problemas([Path("pseudonimizador/a.py"), Path("docs/superpowers/x.md"),
                                 Path("saida_testes/a/b.docx"), Path("Mapas/MAPA-1.json"),
                                 Path("empacotamento/termos_proibidos.txt"), Path("pseudonimizador/config.json")])
    assert len(probs) == 5, probs
    assert manifesto.problemas([Path("pseudonimizador/motor/mapa.py"), Path("LICENSE")]) == []   # "mapa.py" é código


def test_manifesto_do_repositorio_real_e_limpo():
    rel = manifesto.arquivos_do_pacote(RAIZ)
    assert Path("pseudonimizador/__init__.py") in rel and Path("LICENSE") in rel and Path("CREDITOS.md") in rel
    assert Path("pseudonimizador/motor/lexico_ibge.json") in rel
    assert manifesto.problemas(rel) == []
    assert not any(p.parts[0] in ("testes", "saida_testes", "docs", "empacotamento") for p in rel)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
