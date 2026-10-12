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


import hashlib  # noqa: E402
import io  # noqa: E402
import sys  # noqa: E402
import zipfile  # noqa: E402

from empacotamento import construir  # noqa: E402


def _zip_python_falso() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("python.exe", b"MZ")
        z.writestr("pythonw.exe", b"MZ")
        z.writestr("python314.dll", b"MZ")
        z.writestr("python314._pth", "python314.zip\n.\n#import site\n")
    return buf.getvalue()


def _repo_falso(tmp: Path, *, icone: bool = True) -> Path:
    raiz = tmp / "repo"
    for c in ("LICENSE", "CREDITOS.md", "README.md", "pseudonimizador/__init__.py", "pseudonimizador/web/estatico/app.js",
              "requirements.lock", "testes/test_x.py", "saida_testes/x.docx"):
        (raiz / c).parent.mkdir(parents=True, exist_ok=True)
        (raiz / c).write_text("x", encoding="utf-8")
    (raiz / "pseudonimizador" / "__init__.py").write_text('VERSAO = "0.2.0"\n', encoding="utf-8")
    (raiz / "empacotamento").mkdir()
    (raiz / "empacotamento" / "python-embarcavel.toml").write_text(
        'versao = "3.14.0"\nurl = "https://www.python.org/ftp/python/3.14.0/python-3.14.0-embed-amd64.zip"\n'
        'sha256 = "' + hashlib.sha256(_zip_python_falso()).hexdigest() + '"\n', encoding="utf-8")
    if icone:
        (raiz / "empacotamento" / "pseudonimizador.ico").write_bytes(b"\x00\x00\x01\x00")
    return raiz


def test_pth_poe_o_app_e_o_site_packages_no_caminho():
    linhas = construir.conteudo_pth().splitlines()
    assert linhas == ["python314.zip", ".", "..", "Lib\\site-packages"]
    assert "import site" not in construir.conteudo_pth()   # senão entra o site-packages do usuário no sys.path


def test_pip_instala_do_lock_com_hashes_sem_dependencias():
    args = construir.argumentos_pip(Path("requirements.lock"), Path("build/app/python/Lib/site-packages"))
    assert args[:4] == [sys.executable, "-m", "pip", "install"]
    for flag in ("--no-deps", "--require-hashes", "--only-binary=:all:", "--python-version", "3.14", "--platform",
                 "win_amd64", "--implementation", "cp", "--abi", "cp314", "--target"):
        assert flag in args, flag
    assert args[args.index("-r") + 1] == "requirements.lock"


def test_crt_app_local_tem_as_dlls_do_onnxruntime():
    with tempfile.TemporaryDirectory() as d:
        assert {"msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll", "msvcp140_1.dll"} <= set(construir.nomes_do_crt())
        vazia, cheia = Path(d) / "a", Path(d) / "b"
        cheia.mkdir()
        for n in construir.nomes_do_crt():
            (cheia / n).write_bytes(b"MZ")
        assert construir.localizar_crt([vazia, cheia]) == cheia and construir.localizar_crt([vazia]) is None


def test_crt_do_system32_so_com_a_flag_explicita():
    assert not any(p.name.lower() == "system32" for p in construir.candidatos_crt())
    assert construir.candidatos_crt(sistema=True)[-1].name.lower() == "system32"
    with tempfile.TemporaryDirectory() as d:
        raiz = _repo_falso(Path(d))
        original = construir.candidatos_crt
        construir.candidatos_crt = lambda sistema=False: []
        try:
            construir.montar(raiz, Path(d) / "build", executar=lambda *a, **k: 0,
                             baixar=lambda url, destino, sha: (destino.write_bytes(_zip_python_falso()), destino)[1],
                             fumaca=False)
        except SystemExit as e:
            assert "--crt" in str(e) and "--crt-do-sistema" in str(e) and "não publique" in str(e), e
        else:
            raise AssertionError("sem CRT e sem a flag deveria falhar")
        finally:
            construir.candidatos_crt = original


def test_montagem_com_comandos_falsos_produz_a_arvore():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        raiz = _repo_falso(tmp)
        crt = tmp / "crt"
        crt.mkdir()
        for n in construir.nomes_do_crt():
            (crt / n).write_bytes(b"MZ")
        chamadas = []

        def executar(args, **kw):
            chamadas.append(list(args))
            if "pip" in args:
                Path(args[args.index("--target") + 1]).mkdir(parents=True, exist_ok=True)
            return 0

        def baixar(url, destino, sha256):
            assert url.endswith("python-3.14.0-embed-amd64.zip") and destino.name == "python-3.14.0-embed-amd64.zip"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(_zip_python_falso())
            return destino
        app = construir.montar(raiz, tmp / "build", executar=executar, baixar=baixar, crt=crt, fumaca=False)
        assert app == tmp / "build" / "app"
        assert (app / "python" / "python.exe").is_file() and (app / "python" / "msvcp140.dll").is_file()
        assert (app / "python" / "python314._pth").read_text(encoding="utf-8") == construir.conteudo_pth()
        assert (app / "python" / "Lib" / "site-packages").is_dir()
        assert (app / "pseudonimizador" / "__init__.py").is_file() and (app / "LICENSE").is_file()
        assert (app / "pseudonimizador.ico").is_file()
        assert not (app / "requirements.lock").exists() and not (app / "testes").exists()
        assert sum("pip" in c for c in chamadas) == 1 and not any("fumaca" in " ".join(c) for c in chamadas)


def test_tamanho_do_zip_diferente_do_registrado_e_recusado():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        raiz = _repo_falso(tmp)
        toml = raiz / "empacotamento" / "python-embarcavel.toml"
        toml.write_text(toml.read_text(encoding="utf-8") + "tamanho = 1\n", encoding="utf-8")
        crt = tmp / "crt"
        crt.mkdir()
        for n in construir.nomes_do_crt():
            (crt / n).write_bytes(b"MZ")
        try:
            construir.montar(raiz, tmp / "build", executar=lambda *a, **k: 0, crt=crt, fumaca=False,
                             baixar=lambda url, destino, sha: (destino.parent.mkdir(parents=True, exist_ok=True),
                                                               destino.write_bytes(_zip_python_falso()), destino)[2])
        except SystemExit as e:
            assert "tamanho" in str(e)
        else:
            raise AssertionError("tamanho diferente deveria dar SystemExit")


class _RespostaFalsa:
    def __init__(self, dados: bytes):
        self._dados = dados

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._dados


def _com_urlopen_falso(resposta: bytes, fn):
    chamadas = []
    original = construir.urllib.request.urlopen

    def falso(url, timeout=None):
        chamadas.append(url)
        return _RespostaFalsa(resposta)
    construir.urllib.request.urlopen = falso
    try:
        fn(chamadas)
    finally:
        construir.urllib.request.urlopen = original


def test_download_com_hash_errado_e_recusado_e_o_arquivo_removido():
    import hashlib
    with tempfile.TemporaryDirectory() as d:
        destino = Path(d) / "_cache" / "python.zip"
        esperado = hashlib.sha256(b"o zip oficial").hexdigest()

        def corpo(chamadas):
            try:
                construir._baixar_padrao("https://www.python.org/x/python.zip", destino, esperado)
            except SystemExit as e:
                assert "não bate" in str(e) and esperado in str(e)
            else:
                raise AssertionError("hash errado deveria dar SystemExit")
            assert chamadas == ["https://www.python.org/x/python.zip"] and not destino.exists()
        _com_urlopen_falso(b"zip adulterado", corpo)


def test_cache_com_o_hash_certo_nao_baixa_de_novo():
    import hashlib
    with tempfile.TemporaryDirectory() as d:
        destino = Path(d) / "python.zip"
        destino.write_bytes(b"o zip oficial")
        esperado = hashlib.sha256(b"o zip oficial").hexdigest()

        def corpo(chamadas):
            assert construir._baixar_padrao("https://www.python.org/x/python.zip", destino, esperado) == destino
            assert chamadas == []
        _com_urlopen_falso(b"nao deveria ser lido", corpo)


def test_python_embarcavel_sem_sha256_e_recusado():
    with tempfile.TemporaryDirectory() as d:
        toml = Path(d) / "python-embarcavel.toml"
        toml.write_text('versao = "3.14.0"\nurl = "https://www.python.org/ftp/python/3.14.0/x.zip"\n', encoding="utf-8")
        try:
            construir.ler_python_embarcavel(toml)
        except ValueError as e:
            assert "sha256" in str(e)
        else:
            raise AssertionError("sem sha256 deveria dar ValueError")


def test_argumentos_do_iscc_e_localizacao():
    args = construir.argumentos_iscc(Path("C:/Inno/ISCC.exe"), Path("empacotamento/pseudonimizador.iss"),
                                     versao="0.2.0", origem=Path("build/app"), saida=Path("dist"))
    assert args[0].endswith("ISCC.exe") and "/DVersao=0.2.0" in args and args[-1].endswith("pseudonimizador.iss")
    assert any(a.startswith("/DOrigem=") for a in args) and any(a.startswith("/O") for a in args)
    with tempfile.TemporaryDirectory() as d:
        falso = Path(d) / "ISCC.exe"
        falso.write_bytes(b"MZ")
        assert construir.localizar_iscc(falso) == falso
        assert construir.localizar_iscc(Path(d) / "nao-existe.exe") is None


def _crt_falso(pasta: Path) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    for n in construir.nomes_do_crt():
        (pasta / n).write_bytes(b"MZ")
    return pasta


def _montar_falso(tmp: Path, **kw):
    raiz = tmp / "repo" if (tmp / "repo").exists() else _repo_falso(tmp)
    kw.setdefault("baixar", lambda url, destino, sha: (destino.write_bytes(_zip_python_falso()), destino)[1])
    return construir.montar(raiz, tmp / "build", executar=lambda *a, **k: 0, fumaca=False, **kw)


def test_crt_explicito_vazio_ou_com_typo_e_recusado():
    with tempfile.TemporaryDirectory() as d:
        vazia = Path(d) / "crt-vazia"
        vazia.mkdir()
        for pasta in (vazia, Path(d) / "nao-existe"):
            try:
                _montar_falso(Path(d), crt=pasta)
            except SystemExit as e:
                assert "--crt" in str(e)
            else:
                raise AssertionError("--crt sem as DLLs deveria dar SystemExit")


def test_crt_explicito_system32_exige_a_flag_do_sistema():
    with tempfile.TemporaryDirectory() as d:
        sys32 = _crt_falso(Path(d) / "Windows" / "System32")
        try:
            _montar_falso(Path(d), crt=sys32)
        except SystemExit as e:
            assert "--crt-do-sistema" in str(e)
        else:
            raise AssertionError("System32 sem a flag deveria dar SystemExit")
        assert (_montar_falso(Path(d), crt=sys32, crt_do_sistema=True) / "python" / "msvcp140.dll").is_file()


def test_build_de_teste_tem_outro_nome_e_o_iscc_recebe_o_nome():
    assert construir.nome_do_setup(False) == "Pseudonimizador-Setup.exe"
    assert construir.nome_do_setup(True) == "Pseudonimizador-Setup-TESTE.exe"
    args = construir.argumentos_iscc(Path("ISCC.exe"), Path("x.iss"), versao="0.2.0", origem=Path("a"),
                                     saida=Path("dist"), nome_setup=construir.nome_do_setup(True))
    assert "/FPseudonimizador-Setup-TESTE" in args


def test_linha_do_sha256sums_e_o_wsb_substitui_o_dist():
    dados = b"instalador"
    assert construir.linha_sha256sums("Pseudonimizador-Setup.exe", dados) == \
        hashlib.sha256(dados).hexdigest() + "  Pseudonimizador-Setup.exe\n"
    with tempfile.TemporaryDirectory() as d:
        modelo = Path(d) / "m.wsb"
        modelo.write_text("<Host>{DIST}</Host><Host>{DIST}</Host>", encoding="utf-8")
        saida = construir.gerar_wsb(modelo, Path(d) / "dist")
        assert "{DIST}" not in saida and saida.count(str((Path(d) / "dist").resolve())) == 2


def test_montar_confere_o_hash_do_zip_por_conta_propria():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        crt = _crt_falso(tmp / "crt")
        try:
            _montar_falso(tmp, crt=crt, baixar=lambda url, destino, sha: (destino.write_bytes(b"outro zip"), destino)[1])
        except SystemExit as e:
            assert "sha256" in str(e)
        else:
            raise AssertionError("zip com hash diferente deveria ser recusado mesmo com baixar falso")


def test_python_embarcavel_fora_da_serie_e_recusado():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        raiz = _repo_falso(tmp)
        toml = raiz / "empacotamento" / "python-embarcavel.toml"
        toml.write_text(toml.read_text(encoding="utf-8").replace('"3.14.0"', '"3.13.9"'), encoding="utf-8")
        try:
            construir.montar(raiz, tmp / "build", executar=lambda *a, **k: 0, crt=_crt_falso(tmp / "crt"), fumaca=False)
        except SystemExit as e:
            assert "3.14" in str(e)
        else:
            raise AssertionError("versão fora da série deveria dar SystemExit")


def test_candidatos_do_crt_ordenados_por_versao_numerica():
    import os
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        for msvc in ("14.9.1", "14.10.5", "14.9.9", "14.50.1"):
            (base / "Microsoft Visual Studio" / "18" / "Community" / "VC" / "Redist" / "MSVC" / msvc / "x64" /
             "Microsoft.VC145.CRT").mkdir(parents=True)
        antigo = {k: os.environ.get(k) for k in ("ProgramFiles", "ProgramFiles(x86)")}
        os.environ["ProgramFiles"] = str(base)
        os.environ.pop("ProgramFiles(x86)", None)
        try:
            achados = [p.parent.parent.name for p in construir.candidatos_crt()]
        finally:
            for k, v in antigo.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        assert achados == ["14.50.1", "14.10.5", "14.9.9", "14.9.1"], achados


def test_pip_roda_isolado():
    assert "--isolated" in construir.argumentos_pip(Path("requirements.lock"), Path("x"))


def test_fumaca_roda_o_script_no_python_embarcado_de_outra_pasta():
    chamadas = []

    def executar(args, **kw):
        chamadas.append((list(args), kw))
        return 0
    app = Path("X") / "app"
    construir.fumacar(app, executar=executar)
    assert len(chamadas) == 1
    args, kw = chamadas[0]
    assert args[0].endswith("python.exe") and args[1:3] == ["-X", "utf8"] and args[-1].endswith("fumaca.py")
    assert Path(args[-1]).is_file() and kw["cwd"] == str(app.parent)
    try:
        construir.fumacar(app, executar=lambda *a, **k: 1)
    except SystemExit as e:
        assert "OCR" in str(e) and "requirements.lock" in str(e)
    else:
        raise AssertionError("fumaça que falha tem de derrubar o build")


def test_fumaca_cobre_importacoes_docx_pdf_ocr_restauracao_e_rede():
    import ast
    fonte = (RAIZ / "empacotamento" / "fumaca.py").read_text(encoding="utf-8")
    ast.parse(fonte)
    lista = fonte.split("VERIFICACOES = (")[1]
    for nome in ("importacoes", "codigo_do_pacote", "docx_pseudonimizar_e_restaurar", "pdf_com_texto",
                 "pdf_escaneado_ocr", "rede_bloqueada"):
        assert f"def {nome}()" in fonte and nome in lista, nome
    assert "socket" in fonte and "127.0.0.1" in fonte


def test_fumaca_roda_de_verdade_no_python_embarcado_quando_ha_build():
    """Só se build/app existir (montagem local): o script de verdade, no Python embarcado, passa."""
    import subprocess
    py = RAIZ / "build" / "app" / "python" / "python.exe"
    if not py.is_file():
        return
    r = subprocess.run([str(py), "-X", "utf8", str(construir.FUMACA)], cwd=str(RAIZ / "build"),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, (r.stdout[-800:], r.stderr[-800:])


def _iss() -> str:
    bruto = (RAIZ / "empacotamento" / "pseudonimizador.iss").read_bytes()
    assert bruto.startswith(b"\xef\xbb\xbf"), "o .iss precisa de BOM UTF-8 (o ISCC lê os acentos assim)"
    return bruto.decode("utf-8-sig")


def _secao(iss: str, nome: str) -> list[str]:
    corpo = iss.split(f"[{nome}]")[1].split("\n[")[0]
    return [l.strip() for l in corpo.splitlines() if l.strip() and not l.strip().startswith(";")]


def test_icone_e_um_ico_valido_com_varios_tamanhos():
    import struct
    dados = (RAIZ / "empacotamento" / "pseudonimizador.ico").read_bytes()
    reservado, tipo, n = struct.unpack("<HHH", dados[:6])
    assert (reservado, tipo) == (0, 1) and n >= 3
    for i in range(n):
        _, _, _, _, _, _, tam, desl = struct.unpack("<BBBBHHII", dados[6 + 16 * i:22 + 16 * i])
        assert 0 < tam and desl + tam <= len(dados)


def test_iss_instala_sem_administrador_so_x64_e_fecha_o_app_aberto():
    from pseudonimizador.web import abrir
    iss = _iss()
    for exigido in ("PrivilegesRequired=lowest", "DefaultDirName={localappdata}\\Programs\\Pseudonimizador",
                    "DisableDirPage=yes", "DisableProgramGroupPage=yes", "ArchitecturesAllowed=x64compatible",
                    "ArchitecturesInstallIn64BitMode=x64compatible", "MinVersion=10.0.17763",
                    f"AppMutex={abrir.NOME_MUTEX}", "CloseApplications=yes", "OutputBaseFilename=Pseudonimizador-Setup",
                    "SetupIconFile=pseudonimizador.ico", "Languages\\BrazilianPortuguese.isl", "AppVersion={#Versao}",
                    '#error Passe /DVersao', 'Parameters: "-X utf8 -m pseudonimizador"', 'WorkingDir: "{app}"',
                    "python\\pythonw.exe", "{userdesktop}\\Pseudonimizador", "Tasks: atalho",
                    "Flags: postinstall nowait skipifsilent"):
        assert exigido in iss, exigido
    for proibido in ("{pf}", "{commonpf", "{commonappdata}", "runascurrentuser", "PrivilegesRequired=admin",
                     "C:\\Users", "DirectML", "claude", "Mistral", "agendado"):
        assert proibido not in iss, proibido


def test_iss_pagina_da_pasta_chama_configurar_e_avisa_se_falhar():
    iss = _iss()
    assert "CreateInputDirPage(" in iss and "{userdocs}\\Pseudonimizador" in iss
    assert "'Entrada'" not in iss and "Entrada" in iss and "Saida" in iss and "Mapas" in iss   # a explicação da página
    passo = iss.split("procedure CurStepChanged")[1].split("\nend;")[0]
    assert "configurar --pasta-base" in passo and "SW_HIDE" in passo and "ewWaitUntilTerminated" in passo
    assert "python\\python.exe" in passo and "RemoveBackslashUnlessRoot" in passo    # aspas: "C:\x\" quebraria
    assert "Codigo <> 0" in passo and "ConfigFalhou := True" in passo and "SuppressibleMsgBox" in passo
    assert "  MsgBox(" not in passo                              # silencioso nunca trava numa caixa
    fim = iss.split("procedure CurPageChanged")[1].split("\nend;")[0]
    assert "ConfigFalhou" in fim and "Configurações" in fim and "AdjustLabelHeight" in fim


def test_iss_pula_a_pagina_da_pasta_na_atualizacao():
    iss = _iss()
    pular = iss.split("function ShouldSkipPage")[1].split("\nend;")[0]
    assert "PaginaPasta.ID" in pular and "ConfigExiste" in pular
    assert "{localappdata}\\Pseudonimizador\\config.json" in iss
    passo = iss.split("procedure CurStepChanged")[1].split("\nend;")[0]
    assert "if ConfigExiste then exit" in passo                  # config existente nunca é sobrescrita pelo Setup


def test_iss_instalacao_nova_limpa_so_as_pastas_do_programa():
    iss = _iss()
    assert _secao(iss, "InstallDelete") == ['Type: filesandordirs; Name: "{app}\\python"',
                                            'Type: filesandordirs; Name: "{app}\\pseudonimizador"']
    assert iss.index("[InstallDelete]") < iss.index("[Files]")


def test_iss_pergunta_de_apagar_dados_padrao_nao_e_silencio_respeitado():
    iss = _iss()
    assert _secao(iss, "UninstallDelete") == ['Type: filesandordirs; Name: "{app}"']
    assert "[UninstallRun]" not in iss and "function InitializeUninstall" not in iss
    codigo = iss.split("procedure CurUninstallStepChanged")[1]
    assert "UninstallSilent" in codigo and "MB_DEFBUTTON2" in codigo and "MB_YESNO" in codigo
    assert "ApagarDadosResposta := False" in codigo.split("UninstallSilent")[1].split("else")[0]
    assert "DelTree(ExpandConstant('{localappdata}\\Pseudonimizador')" in codigo
    assert "nunca é apagada" in codigo and "userdocs" not in codigo and "pasta_base" not in codigo


def test_wsb_do_sandbox_mapeia_o_dist_so_leitura_sem_rede_e_abre_o_setup():
    from empacotamento import construir
    modelo = RAIZ / "empacotamento" / "sandbox.wsb.modelo"
    with tempfile.TemporaryDirectory() as d:
        texto = construir.gerar_wsb(modelo, Path(d) / "dist")
        assert str((Path(d) / "dist").resolve()) in texto and "{DIST}" not in texto
    assert "<ReadOnly>true</ReadOnly>" in texto and "<Networking>Disable</Networking>" in texto
    assert "<VGpu>Enable</VGpu>" in texto and "Pseudonimizador-Setup.exe" in texto
    assert "C:\\Users" not in modelo.read_text(encoding="utf-8")        # nem o usuário padrão do Sandbox
    assert "<SandboxFolder>" not in texto                                  # sem SandboxFolder, cai na Área de Trabalho


def test_roteiro_do_mantenedor_cobre_montagem_aceitacao_e_limites():
    texto = (RAIZ / "empacotamento" / "README.md").read_text(encoding="utf-8")
    for exigido in ("construir.py", "--so-montar", "--crt", "--iscc", "gerar_lock.py", "python-embarcavel.toml",
                    "Pseudonimizador-Sandbox.wsb", "SHA256SUMS.txt", "Pseudonimizador-Setup.exe", "SmartScreen",
                    "Redução de tamanho", "Aceitação no Windows Sandbox", "Instala sem pedir administrador",
                    "Pasta dos arquivos", "DOCX", "PDF com texto", "PDF escaneado", "Restaurar", "Encerrar",
                    "Desinstalar", "nunca apaga", "Atualização por cima", "verificar_publicacao.py"):
        assert exigido in texto, exigido


def test_iss_recusa_pasta_dentro_do_programa_ou_do_estado_e_versao_numerica():
    iss = _iss()
    prox = iss.split("function NextButtonClick")[1].split("\nend;")[0]
    assert "{app}" in prox and "{localappdata}\\Pseudonimizador" in prox and "Lowercase(" in iss and "DentroDe(" in prox
    assert "dentro da pasta do programa" in prox
    assert "VersionInfoVersion={#VersaoNum}.0" in iss and "AppVersion={#Versao}" in iss
    assert "#ifndef VersaoNum" in iss
    args = construir.argumentos_iscc(Path("ISCC.exe"), Path("x.iss"), versao="0.3.0rc1", origem=Path("a"),
                                     saida=Path("dist"))
    assert "/DVersao=0.3.0rc1" in args and "/DVersaoNum=0.3.0" in args
    assert construir.versao_numerica("1.2.3-beta.4") == "1.2.3" and construir.versao_numerica("2.0") == "2.0.0"


def test_wsb_escapa_o_caminho_em_xml():
    modelo = RAIZ / "empacotamento" / "sandbox.wsb.modelo"
    with tempfile.TemporaryDirectory() as d:
        texto = construir.gerar_wsb(modelo, Path(d) / "a&b<c" / "dist")
    assert "a&amp;b&lt;c" in texto and "a&b" not in texto
    import xml.dom.minidom
    xml.dom.minidom.parseString(texto)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
