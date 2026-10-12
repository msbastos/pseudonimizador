# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Monta build/app e compila dist/Pseudonimizador-Setup.exe (spec §2).

Uso (na raiz, com o .venv do Python 3.14 x64 e o Inno Setup 6 instalados):
    .venv\\Scripts\\python -X utf8 empacotamento/construir.py             # monta e compila
    .venv\\Scripts\\python -X utf8 empacotamento/construir.py --so-montar  # para antes do ISCC

Este é um dos dois únicos scripts do projeto que usam a rede (python.org e
PyPI); o app e os testes nunca. Passos: 1) baixa (ou usa de
empacotamento/_cache) o Python embarcável e confere o sha256 (e o tamanho, se
registrado); 2) descompacta em build/app/python e escreve o ._pth (o app e o
site-packages no caminho, sem "import site"); 3) pip --no-deps
--require-hashes do requirements.lock para Lib/site-packages; 4) copia as DLLs
do runtime do Visual C++ (app-local: sem vc_redist, sem administrador; nunca do
System32 num build publicado); 5) copia o código pelo manifesto e o ícone; 6)
fumaça: o Python embarcado, a partir de OUTRA pasta e com a rede bloqueada,
importa tudo, lê DOCX/PDF/OCR, gera e restaura (empacotamento/fumaca.py); 7)
ISCC com /DVersao e /DOrigem; escreve dist/SHA256SUMS.txt e o .wsb do Sandbox.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tomllib
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

SERIE = "3.14"
CRT = ("msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll", "msvcp140_atomic_wait.dll", "msvcp140_codecvt_ids.dll",
       "concrt140.dll", "vcruntime140.dll", "vcruntime140_1.dll", "vccorlib140.dll")
CRT_OBRIGATORIAS = ("msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll")
ISCC_PADRAO = (Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
               Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe")
FUMACA = Path(__file__).resolve().parent / "fumaca.py"
NOME_SETUP = "Pseudonimizador-Setup.exe"


def ler_python_embarcavel(toml: Path) -> dict:
    d = tomllib.loads(Path(toml).read_text(encoding="utf-8"))
    for k in ("versao", "url", "sha256"):
        if not d.get(k):
            raise ValueError(f"python-embarcavel.toml sem '{k}'")
    saida = {"versao": d["versao"], "url": d["url"], "sha256": d["sha256"].lower()}
    if d.get("tamanho"):   # conferência barata além do hash
        saida["tamanho"] = int(d["tamanho"])
    return saida


def conteudo_pth() -> str:
    # ".." é {app}: `-m pseudonimizador` funciona de qualquer pasta de trabalho. Sem "import site": ele poria o
    # site-packages DO USUÁRIO (%APPDATA%\Python\...) e seus .pth no sys.path.
    return "python314.zip\n.\n..\nLib\\site-packages\n"


def argumentos_pip(lock: Path, destino: Path) -> list[str]:
    return [sys.executable, "-m", "pip", "install", "--no-deps", "--require-hashes", "--only-binary=:all:",
            "--python-version", SERIE, "--platform", "win_amd64", "--implementation", "cp", "--abi", "cp314",
            "--upgrade", "--target", str(destino), "-r", str(lock)]


def nomes_do_crt() -> tuple[str, ...]:
    return CRT


def localizar_crt(candidatos: list[Path]) -> Path | None:
    for pasta in candidatos:
        if pasta and all((Path(pasta) / n).is_file() for n in CRT_OBRIGATORIAS):
            return Path(pasta)
    return None


def candidatos_crt(sistema: bool = False) -> list[Path]:
    """Onde procurar o CRT redistribuível (Visual Studio 2022/18: Microsoft.VC14x.CRT). O System32 só entra com
    a flag explícita (--crt-do-sistema): as DLLs dele são da versão do Windows da máquina, não as do redistribuível."""
    achados: list[Path] = []
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if base:
            achados += sorted(Path(base).glob("Microsoft Visual Studio/*/*/VC/Redist/MSVC/*/x64/Microsoft.VC14?.CRT"),
                              reverse=True)
    if sistema:
        achados.append(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32")
    return achados


def localizar_iscc(explicito: Path | None) -> Path | None:
    if explicito is not None:
        return Path(explicito) if Path(explicito).is_file() else None
    return next((p for p in ISCC_PADRAO if p.is_file()), None)


def argumentos_iscc(iscc: Path, iss: Path, *, versao: str, origem: Path, saida: Path) -> list[str]:
    return [str(iscc), f"/DVersao={versao}", f"/DOrigem={origem}", f"/O{saida}", str(iss)]


def _baixar_padrao(url: str, destino: Path, sha256: str) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    if not destino.is_file() or hashlib.sha256(destino.read_bytes()).hexdigest() != sha256:
        print(f"baixando {url}")
        with urllib.request.urlopen(url, timeout=120) as r:
            destino.write_bytes(r.read())
    real = hashlib.sha256(destino.read_bytes()).hexdigest()
    if real != sha256:
        destino.unlink(missing_ok=True)
        raise SystemExit(f"sha256 do Python embarcável não bate: esperado {sha256}, veio {real}")
    return destino


def _executar_padrao(args, **kw) -> int:
    print("  >", " ".join(str(a) for a in args))
    return subprocess.run(args, check=False, **kw).returncode


def montar(raiz: Path, build: Path, *, executar=_executar_padrao, baixar=_baixar_padrao, crt: Path | None = None,
           fumaca: bool = True, crt_do_sistema: bool = False) -> Path:
    from empacotamento import manifesto
    raiz, build = Path(raiz), Path(build)
    app = build / "app"
    if app.exists():
        shutil.rmtree(app)
    (app / "python").mkdir(parents=True)
    # 1-2: o Python embarcável
    py = ler_python_embarcavel(raiz / "empacotamento" / "python-embarcavel.toml")
    cache = raiz / "empacotamento" / "_cache"
    cache.mkdir(parents=True, exist_ok=True)
    zip_local = baixar(py["url"], cache / Path(py["url"]).name, py["sha256"])
    if "tamanho" in py and Path(zip_local).stat().st_size != py["tamanho"]:
        raise SystemExit(f"tamanho do Python embarcável não bate: esperado {py['tamanho']} bytes, "
                         f"veio {Path(zip_local).stat().st_size}")
    with zipfile.ZipFile(zip_local) as z:
        z.extractall(app / "python")
    (app / "python" / "python314._pth").write_text(conteudo_pth(), encoding="utf-8")
    # 3: as bibliotecas, do lock
    if executar(argumentos_pip(raiz / "requirements.lock", app / "python" / "Lib" / "site-packages")) != 0:
        raise SystemExit("pip falhou")
    # 4: o runtime do Visual C++ (app-local)
    pasta_crt = crt or localizar_crt(candidatos_crt(sistema=crt_do_sistema))
    if pasta_crt is None:
        raise SystemExit("não achei as DLLs do redistribuível do Visual C++ (msvcp140.dll e companhia); passe "
                         "--crt PASTA ou, só num build de teste, --crt-do-sistema (usa o System32: não publique)")
    if not crt and crt_do_sistema and Path(pasta_crt).name.lower() == "system32":
        print("AVISO: CRT do System32, só para teste; não publique este instalador.")
    for n in CRT:
        if (Path(pasta_crt) / n).is_file():
            shutil.copy2(Path(pasta_crt) / n, app / "python" / n)
    # 5: o código, pelo manifesto, e o ícone
    rel = manifesto.arquivos_do_pacote(raiz)
    if problemas := manifesto.problemas(rel):
        raise SystemExit("\n".join(problemas))
    for r in rel:
        (app / r).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raiz / r, app / r)
    shutil.copy2(raiz / "empacotamento" / "pseudonimizador.ico", app / "pseudonimizador.ico")
    # 6: fumaça
    if fumaca:
        fumacar(app, executar=executar)
    return app


def fumacar(app: Path, *, executar=_executar_padrao) -> None:
    """O Python embarcado, a partir de OUTRA pasta de trabalho (build/), roda empacotamento/fumaca.py."""
    rc = executar([str(app / "python" / "python.exe"), "-X", "utf8", str(FUMACA)], cwd=str(Path(app).parent))
    if rc != 0:
        raise SystemExit("fumaça falhou: o Python embarcado não fez o que o Pseudonimizador faz (importar, ler DOCX/PDF, "
                         "OCR, gerar, restaurar); veja a linha FALHA acima e confira o requirements.lock")


def gerar_wsb(modelo: Path, dist: Path) -> str:
    """Config do Windows Sandbox: mapeia dist/ (só leitura) e abre o Setup. {DIST} vem do modelo."""
    return Path(modelo).read_text(encoding="utf-8").replace("{DIST}", str(Path(dist).resolve()))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="monta build/app e compila dist/Pseudonimizador-Setup.exe")
    ap.add_argument("--so-montar", action="store_true")
    ap.add_argument("--crt", type=Path, help="pasta com msvcp140.dll e companhia")
    ap.add_argument("--iscc", type=Path, help="caminho do ISCC.exe")
    ap.add_argument("--crt-do-sistema", action="store_true",
                    help="build de teste: aceita as DLLs do System32 como CRT (não publique)")
    args = ap.parse_args(argv)
    if sys.version_info[:2] != (3, 14) or sys.platform != "win32":
        print("Rode com o Python 3.14 x64 do Windows (o mesmo do requirements.lock).")
        return 2
    from pseudonimizador import VERSAO
    build, dist = RAIZ / "build", RAIZ / "dist"
    app = montar(RAIZ, build, crt=args.crt, crt_do_sistema=args.crt_do_sistema)
    if args.so_montar:
        print(f"montado em {app}")
        return 0
    iscc = localizar_iscc(args.iscc)
    if iscc is None:
        print("ISCC.exe não encontrado: instale o Inno Setup 6 ou passe --iscc.")
        return 2
    dist.mkdir(exist_ok=True)
    rc = _executar_padrao(argumentos_iscc(iscc, RAIZ / "empacotamento" / "pseudonimizador.iss", versao=VERSAO,
                                          origem=app, saida=dist))
    if rc != 0:
        return rc
    setup = dist / NOME_SETUP
    (dist / "SHA256SUMS.txt").write_text(f"{hashlib.sha256(setup.read_bytes()).hexdigest()}  {setup.name}\n",
                                         encoding="utf-8")
    (dist / "Pseudonimizador-Sandbox.wsb").write_text(
        gerar_wsb(RAIZ / "empacotamento" / "sandbox.wsb.modelo", dist), encoding="utf-8")
    print(f"pronto: {setup} ({setup.stat().st_size // 1_000_000} MB), SHA256SUMS.txt e Pseudonimizador-Sandbox.wsb em {dist}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
