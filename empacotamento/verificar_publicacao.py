# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Conferência antes de publicar (spec §4). Não publica nada: só diz se pode.

    .venv\\Scripts\\python -X utf8 empacotamento/verificar_publicacao.py [--sem-suite] [--sem-termos]

1. a suíte inteira (testes/executar_todos.py) e a guarda test_sem_dados_reais.py;
2. varredura do histórico INTEIRO (git log --all -p -m) por e-mail fora dos domínios
   de placeholder, caminho de máquina (C:\\Users\\<nome>, /c/Users/<nome>,
   /home/<nome>) e os termos de empacotamento/termos_proibidos.txt (lista local,
   ignorada pelo git, um termo por linha, sem diferenciar maiúsculas). Sem essa
   lista a conferência é pendência, salvo --sem-termos;
3. autor e responsável de todo commit com o e-mail privado do GitHub;
4. dist\\ com Pseudonimizador-Setup.exe e SHA256SUMS.txt batendo.
Os achados mostram o commit, o arquivo e uma dica mascarada, nunca o valor.
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
RE_EMAIL = re.compile(r"\w[\w.+-]*@(?:[\w-]+\.)+[a-z]{2,}", re.I)
RE_CAMINHO = re.compile(
    r"(?i)(?:\b[a-z]:[\\/]+users[\\/]+|(?<![\w.:-])/[a-z]/users/|(?<![\w.:-])/" r"home/)(?!<)(\w[^\\/\s\"'<>|]*)")
RE_COMMIT = re.compile(r"^commit ([0-9a-f]{7,40})")
RE_ARQUIVO = re.compile(r"^diff --git a/.* b/(.*)$|^diff --(?:cc|combined) (.*)$")
DOMINIOS_PERMITIDOS = ("anthropic.com", "users.noreply.github.com", "exemplo.com.br", "example.com")


def email_permitido(email: str) -> bool:
    dominio = email.lower().rsplit("@", 1)[-1]
    return any(dominio == d or dominio.endswith("." + d) for d in DOMINIOS_PERMITIDOS)


def mascarar_email(email: str) -> str:
    local, _, dominio = email.partition("@")
    rotulos = dominio.split(".")
    return f"{local[:1]}***@{rotulos[0][:1]}***.{rotulos[-1]}"


def mascarar_termo(termo: str) -> str:
    return "**" if len(termo) <= 2 else termo[0] + "*" * (len(termo) - 2) + termo[-1]


def carregar_termos(caminho: Path) -> list[str]:
    if not Path(caminho).is_file():
        return []
    linhas = Path(caminho).read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in linhas if l.strip() and not l.strip().startswith("#")]


def varrer(texto: str, termos: list[str]) -> list[str]:
    """Achados mascarados, 'commit arquivo: tipo dica', um por valor distinto."""
    achados: list[str] = []
    vistos: set[tuple[str, str]] = set()
    termos_cf = [(t.casefold(), t) for t in termos]
    commit, arquivo = "texto", ""

    def registrar(tipo: str, bruto: str, dica: str) -> None:
        chave = (tipo, bruto.casefold())
        if chave not in vistos:
            vistos.add(chave)
            onde = f"{commit} {arquivo}" if arquivo else commit
            achados.append(f"{onde}: {tipo} {dica}")

    for linha in texto.splitlines():
        m = RE_COMMIT.match(linha)
        if m:
            commit, arquivo = m.group(1)[:7], ""
        m = RE_ARQUIVO.match(linha)
        if m:
            arquivo = m.group(1) or m.group(2)
        for m in RE_EMAIL.finditer(linha):
            if not email_permitido(m.group(0)):
                registrar("e-mail", m.group(0), mascarar_email(m.group(0)))
        for m in RE_CAMINHO.finditer(linha):
            nome = m.group(1)
            if "***" in nome:   # já é máscara (o relato de uma varredura anterior), não um nome
                continue
            registrar("caminho", m.group(0), m.group(0)[:len(m.group(0)) - len(nome)] + nome[:1] + "***")
        baixa = linha.casefold()
        for cf, original in termos_cf:
            if cf in baixa:
                registrar("termo", cf, mascarar_termo(original))
    return achados


def emails_fora_do_github(linhas: str) -> list[str]:
    if not linhas.strip():
        return ["git log sem commits (saída vazia): nada a conferir"]
    fora = []
    for linha in linhas.splitlines():
        if not linha.strip():
            continue
        partes = linha.split()
        if len(partes) < 3:
            fora.append(f"{partes[0] if partes else '?'}: linha sem autor e responsável (e-mail vazio?)")
            continue
        for email in partes[1:3]:
            if not email.lower().endswith("@users.noreply.github.com"):
                fora.append(f"{partes[0]}: {mascarar_email(email)}")
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


def _cauda(r, n: int = 20) -> str:
    linhas = ((getattr(r, "stdout", "") or "") + (getattr(r, "stderr", "") or "")).splitlines()
    return "\n".join("      " + l for l in linhas[-n:])


def main(argv=None, *, executar=subprocess.run) -> int:
    ap = argparse.ArgumentParser(description="conferência antes de publicar; não publica nada")
    ap.add_argument("--dist", type=Path, default=RAIZ / "dist")
    ap.add_argument("--termos", type=Path, default=RAIZ / "empacotamento" / "termos_proibidos.txt")
    ap.add_argument("--sem-suite", action="store_true", help="pula a suíte (só para iterar)")
    ap.add_argument("--sem-termos", action="store_true", help="aceita não ter a lista local de termos")
    args = ap.parse_args(argv)
    pendencias: list[str] = []
    feito: list[str] = []
    kw = dict(cwd=str(RAIZ), capture_output=True, text=True, encoding="utf-8", errors="replace")

    def rodar(cmd: list[str]):
        try:
            return executar(cmd, **kw)
        except FileNotFoundError as e:
            pendencias.append(f"comando não encontrado: {cmd[0]} ({e})")
            return None

    py = [sys.executable, "-X", "utf8"]
    if args.sem_suite:
        feito.append("suíte: NÃO conferida (--sem-suite)")
    else:
        print("1. suíte inteira")
        r = rodar(py + [str(RAIZ / "testes" / "executar_todos.py")])
        if r is not None and r.returncode != 0:
            pendencias.append("a suíte falhou (rode testes/executar_todos.py); fim da saída:\n" + _cauda(r))
        feito.append("suíte: conferida")
    print("1b. guarda de dados reais")
    r = rodar(py + [str(RAIZ / "testes" / "test_sem_dados_reais.py")])
    if r is not None and r.returncode != 0:
        pendencias.append("test_sem_dados_reais.py falhou; fim da saída:\n" + _cauda(r))
    feito.append("guarda de dados reais: conferida")
    print("2. histórico inteiro (git log --all -p -m)")
    termos = carregar_termos(args.termos)
    if termos:
        feito.append(f"termos: conferidos ({len(termos)})")
    else:
        feito.append("termos: NÃO conferidos")
        if not args.sem_termos:
            pendencias.append(f"sem {args.termos.name} (ou vazio): crie a lista local ou passe --sem-termos")
    log = rodar(["git", "log", "--all", "-p", "-m", "--no-color"])
    if log is not None:
        if log.returncode != 0:
            pendencias.append("git log --all -p falhou")
        else:
            pendencias += [f"histórico: {a}" for a in varrer(log.stdout, termos)]
            feito.append("histórico: varrido (e-mails, caminhos)")
    print("3. e-mails dos commits")
    ids = rodar(["git", "log", "--all", "--format=%h %ae %ce"])
    if ids is not None:
        if ids.returncode != 0:
            pendencias.append("git log --format falhou")
        else:
            pendencias += [f"commit sem o e-mail privado do GitHub — {f}" for f in emails_fora_do_github(ids.stdout)]
            feito.append("e-mails dos commits: conferidos")
    print("4. dist")
    pendencias += conferir_dist(args.dist)
    feito.append("dist: conferido")
    print("\nConferências: " + "; ".join(feito))
    if pendencias:
        print("\nNÃO publique ainda:")
        for p in pendencias:
            print(f"  - {p}")
        return 1
    print("\nPode publicar: tudo acima passou.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
