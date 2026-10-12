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


def test_manifesto_e_lista_fechada_de_sufixos():
    with tempfile.TemporaryDirectory() as d:
        raiz = _arvore(Path(d), ["LICENSE", "pseudonimizador/a.py", "pseudonimizador/web/estatico/i.html",
                                 "pseudonimizador/web/estatico/e.css", "pseudonimizador/notas.txt",
                                 "pseudonimizador/x.db", "pseudonimizador/t.csv", "pseudonimizador/p.xlsx"])
        rel = {p.as_posix() for p in manifesto.arquivos_do_pacote(raiz)}
    assert rel == {"LICENSE", "pseudonimizador/a.py", "pseudonimizador/web/estatico/i.html",
                   "pseudonimizador/web/estatico/e.css"}, rel
    for estranho in ("notas.txt", "x.db", "t.csv", "p.xlsx"):
        assert manifesto.problemas([Path("pseudonimizador") / estranho]), estranho
    assert manifesto.problemas([Path("outra/coisa.py")]) and manifesto.problemas([Path("setup.py")])


def test_manifesto_acusa_mapa_fora_do_motor_e_ignora_a_caixa():
    assert manifesto.problemas([Path("pseudonimizador/mapa_pseudonimos.json")])
    assert manifesto.problemas([Path("pseudonimizador/mapa_x.json")])
    assert manifesto.problemas([Path("pseudonimizador/web/MAPA-1.JSON")])
    assert manifesto.problemas([Path("pseudonimizador/motor/mapa_pseudonimos.json")])
    assert manifesto.problemas([Path("mapas/x.json")]) and manifesto.problemas([Path("Entrada/x.pdf")])
    assert manifesto.problemas([Path("pseudonimizador/ENTRADA/x.json")])
    assert manifesto.problemas([Path("pseudonimizador/motor/lexico_ibge.json"),
                                Path("pseudonimizador/motor/nivel_sinais.json"),
                                Path("pseudonimizador/saida/mapas.py"), Path("pseudonimizador/saida/docx.py")]) == []


def test_manifesto_do_repositorio_real_e_limpo():
    rel = manifesto.arquivos_do_pacote(RAIZ)
    assert Path("pseudonimizador/__init__.py") in rel and Path("LICENSE") in rel and Path("CREDITOS.md") in rel
    assert Path("pseudonimizador/motor/lexico_ibge.json") in rel
    assert manifesto.problemas(rel) == []
    assert not any(p.parts[0] in ("testes", "saida_testes", "docs", "empacotamento") for p in rel)


from empacotamento import gerar_lock  # noqa: E402


def test_lock_troca_o_opencv_pelo_headless_e_tira_o_sympy():
    wheels = [Path(n) for n in ("opencv_python-5.0.0.93-cp37-abi3-win_amd64.whl",
                                "opencv_python_headless-5.0.0.93-cp37-abi3-win_amd64.whl",
                                "sympy-1.14.0-py3-none-any.whl", "mpmath-1.3.0-py3-none-any.whl",
                                "onnxruntime-1.24.4-cp314-cp314-win_amd64.whl", "numpy-2.5.4-cp314-cp314-win_amd64.whl")]
    assert gerar_lock.nome_e_versao(wheels[0]) == ("opencv-python", "5.0.0.93")
    restantes = [w.name for w in gerar_lock.filtrar(wheels)]
    assert "opencv_python-5.0.0.93-cp37-abi3-win_amd64.whl" not in restantes
    assert not any(w.startswith(("sympy-", "mpmath-")) for w in restantes)
    assert "opencv_python_headless-5.0.0.93-cp37-abi3-win_amd64.whl" in restantes and len(restantes) == 3
    assert gerar_lock.problemas_do_lock({"onnxruntime", "opencv-python-headless"}) == []
    assert gerar_lock.problemas_do_lock({"onnxruntime", "opencv-python"})            # faltou o headless, sobrou o cheio
    assert gerar_lock.problemas_do_lock({"onnxruntime", "opencv-python-headless", "sympy"})


def test_lock_tem_hash_por_wheel_e_e_gerado_sem_rede_com_baixar_falso():
    import hashlib
    with tempfile.TemporaryDirectory() as d:
        a = Path(d) / "numpy-2.5.4-cp314-cp314-win_amd64.whl"
        a.write_bytes(b"roda falsa")
        linhas = gerar_lock.linhas_do_lock([a])
        assert linhas[0] == "numpy==2.5.4 \\" and linhas[1] == f"    --hash=sha256:{hashlib.sha256(b'roda falsa').hexdigest()}"
        raiz = Path(d) / "repo"
        raiz.mkdir()
        (raiz / "requirements.txt").write_text("rapidocr==3.9.2\n", encoding="utf-8")
        chamadas = []

        def baixar(destino, argumentos):
            chamadas.append(argumentos)
            if "-r" in argumentos:
                for n in ("opencv_python-5.0.0.93-cp37-abi3-win_amd64.whl", "rapidocr-3.9.2-py3-none-any.whl",
                          "onnxruntime-1.24.4-cp314-cp314-win_amd64.whl", "sympy-1.14.0-py3-none-any.whl"):
                    (destino / n).write_bytes(b"x")
            else:
                (destino / "opencv_python_headless-5.0.0.93-cp37-abi3-win_amd64.whl").write_bytes(b"y")
        assert gerar_lock.main(["--raiz", str(raiz)], baixar=baixar) == 0
        texto = (raiz / "requirements.lock").read_text(encoding="utf-8")
    assert "opencv-python-headless==5.0.0.93" in texto and "opencv-python==" not in texto and "sympy" not in texto
    assert texto.count("--hash=sha256:") == 3 and "NÃO editar" in texto
    assert chamadas[1][:2] == ["--no-deps", "opencv-python-headless==5.0.0.93"]   # a mesma versão do wheel cheio


def test_requirements_lock_do_repositorio_esta_coerente():
    texto = (RAIZ / "requirements.lock").read_text(encoding="utf-8")
    pacotes = [l.split("==")[0] for l in texto.splitlines() if "==" in l]
    assert {"pymupdf", "python-docx", "rapidocr", "onnxruntime", "numpy", "opencv-python-headless"} <= set(pacotes)
    assert len(pacotes) == texto.count("--hash=sha256:"), "todo pacote do lock leva o seu hash"
    assert "opencv-python==" not in texto
    # Se a Task 5 desfizer a redução (fumaça falhou sem sympy), retire a linha abaixo e diga o motivo no commit.
    assert "sympy" not in texto


def test_python_embarcavel_tem_versao_url_e_hash():
    from empacotamento import construir
    d = construir.ler_python_embarcavel(RAIZ / "empacotamento" / "python-embarcavel.toml")
    assert d["versao"].startswith("3.14.") and d["url"] == f"https://www.python.org/ftp/python/{d['versao']}/python-{d['versao']}-embed-amd64.zip"
    assert len(d["sha256"]) == 64 and int(d["sha256"], 16) > 0 and d["sha256"] != "0" * 64


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
