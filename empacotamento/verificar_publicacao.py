# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Conferência antes de publicar (spec §4). Não publica nada: só diz se pode.

    .venv\\Scripts\\python -X utf8 empacotamento/verificar_publicacao.py [--sem-suite]

1. a suíte inteira (testes/executar_todos.py) e a guarda test_sem_dados_reais.py;
2. varredura do histórico INTEIRO (git log --all -p) por e-mail fora dos domínios
   de placeholder, caminho de máquina (C:\\Users\\<nome>) e os termos de
   empacotamento/termos_proibidos.txt (lista local, ignorada pelo git, um termo
   por linha; se não existir, só os padrões embutidos valem);
3. autor e responsável de todo commit com o e-mail privado do GitHub;
4. dist\\ com Pseudonimizador-Setup.exe e SHA256SUMS.txt batendo.
Sai com 0 se tudo passa; 1 e a lista das pendências se não."""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOME_SETUP = "Pseudonimizador-Setup.exe"
RE_EMAIL = re.compile(r"\w[\w.+-]*@([\w-]+\.)+[a-z]{2,}", re.I)
RE_CAMINHO = re.compile(r"(?i)\b[a-z]:[\\/]+users[\\/]+(?!<)[^\\/\s\"'<>|]+")
DOMINIOS_PERMITIDOS = ("users.noreply.github.com", "anthropic.com")
TRECHOS_PERMITIDOS = ("exemplo", "example")


def email_permitido(email: str) -> bool:
    dominio = email.lower().rsplit("@", 1)[-1]
    return dominio.endswith(DOMINIOS_PERMITIDOS) or any(t in dominio for t in TRECHOS_PERMITIDOS)


def carregar_termos(caminho: Path) -> list[str]:
    if not Path(caminho).is_file():
        return []
    linhas = Path(caminho).read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in linhas if l.strip() and not l.strip().startswith("#")]


def varrer(texto: str, termos: list[str]) -> list[str]:
    achados: list[str] = []
    for m in RE_EMAIL.finditer(texto):
        if not email_permitido(m.group(0)):
            achados.append(f"e-mail: {m.group(0)}")
    for m in RE_CAMINHO.finditer(texto):
        achados.append(f"caminho: {m.group(0)}")
    for t in termos:
        if t in texto:
            achados.append(f"termo: {t}")
    return list(dict.fromkeys(achados))


def emails_fora_do_github(linhas: str) -> list[str]:
    fora = []
    for linha in linhas.splitlines():
        partes = linha.split()
        if len(partes) < 3:
            continue
        for email in partes[1:3]:
            if not email.lower().endswith("@users.noreply.github.com"):
                fora.append(f"{partes[0]}: {email}")
    return fora


def conferir_dist(dist: Path) -> list[str]:
    dist = Path(dist)
    setup, sums = dist / NOME_SETUP, dist / "SHA256SUMS.txt"
    if not setup.is_file():
        return [f"dist sem {NOME_SETUP}: rode empacotamento/construir.py"]
    if not sums.is_file():
        return ["dist sem SHA256SUMS.txt"]
    esperado = next((l.split()[0] for l in sums.read_text(encoding="utf-8").splitlines() if NOME_SETUP in l), "")
    real = hashlib.sha256(setup.read_bytes()).hexdigest()
    return [] if esperado == real else [f"SHA256SUMS.txt não bate com {NOME_SETUP} (esperado {esperado}, real {real})"]


def main(argv=None, *, executar=subprocess.run) -> int:
    ap = argparse.ArgumentParser(description="conferência antes de publicar; não publica nada")
    ap.add_argument("--dist", type=Path, default=RAIZ / "dist")
    ap.add_argument("--termos", type=Path, default=RAIZ / "empacotamento" / "termos_proibidos.txt")
    ap.add_argument("--sem-suite", action="store_true", help="pula a suíte (só para iterar)")
    args = ap.parse_args(argv)
    pendencias: list[str] = []
    kw = dict(cwd=str(RAIZ), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not args.sem_suite:
        print("1. suíte inteira")
        if executar([sys.executable, "-X", "utf8", str(RAIZ / "testes" / "executar_todos.py")], **kw).returncode != 0:
            pendencias.append("a suíte falhou (rode testes/executar_todos.py)")
    print("1b. guarda de dados reais")
    if executar([sys.executable, "-X", "utf8", str(RAIZ / "testes" / "test_sem_dados_reais.py")], **kw).returncode != 0:
        pendencias.append("test_sem_dados_reais.py falhou")
    print("2. histórico inteiro (git log --all -p)")
    termos = carregar_termos(args.termos)
    if not termos:
        print(f"   (sem {args.termos.name}: só os padrões embutidos)")
    log = executar(["git", "log", "--all", "-p", "--no-color"], **kw)
    if log.returncode != 0:
        pendencias.append("git log --all -p falhou")
    else:
        pendencias += [f"histórico: {a}" for a in varrer(log.stdout, termos)]
    print("3. e-mails dos commits")
    ids = executar(["git", "log", "--all", "--format=%h %ae %ce"], **kw)
    if ids.returncode != 0:
        pendencias.append("git log --format falhou")
    else:
        pendencias += [f"commit sem o e-mail privado do GitHub — {f}" for f in emails_fora_do_github(ids.stdout)]
    print("4. dist")
    pendencias += conferir_dist(args.dist)
    if pendencias:
        print("\nNÃO publique ainda:")
        for p in pendencias:
            print(f"  - {p}")
        return 1
    print("\nPode publicar: suíte verde, histórico limpo, commits com o e-mail do GitHub, dist conferido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
