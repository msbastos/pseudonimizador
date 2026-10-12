# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Guarda: nenhum caminho da máquina, nome de usuário ou e-mail pessoal em
arquivo do projeto. Os dados de teste são os sintéticos de testes/fabrica.py."""
import _base  # noqa: F401
import getpass
import os
import re
from _base import RAIZ
from test_licenca import _arquivos_do_projeto

RE_CAMINHO = re.compile(r"(?i)\b[a-z]:[\\/]+users[\\/]+(?!<)[^\\/\s]+")
RE_EMAIL = re.compile(r"[\w.+-]+@([\w-]+\.)+[a-z]{2,}", re.I)
DOMINIOS_PERMITIDOS = ("exemplo.com.br", "example.com", "anthropic.com", "users.noreply.github.com")
BINARIOS = (".json", ".png", ".jpg", ".pdf", ".docx", ".onnx", ".ico", ".whl", ".zip", ".exe")


def _usuarios() -> set[str]:
    nomes = {os.environ.get("USERNAME", ""), os.environ.get("USER", "")}
    try:
        nomes.add(getpass.getuser())
    except Exception:  # noqa: BLE001
        pass
    return {n.lower() for n in nomes if len(n) >= 3}


def test_sem_caminho_usuario_ou_email():
    achados = []
    usuarios = _usuarios()
    for rel in _arquivos_do_projeto():
        if rel.lower().endswith(BINARIOS) or rel == "LICENSE":
            continue
        texto = (RAIZ / rel).read_text(encoding="utf-8", errors="replace")
        if RE_CAMINHO.search(texto):
            achados.append(f"{rel}: caminho da máquina")
        for m in RE_EMAIL.finditer(texto):
            if not m.group(0).lower().endswith(DOMINIOS_PERMITIDOS):
                achados.append(f"{rel}: e-mail {m.group(0)}")
        baixo = texto.lower()
        for u in usuarios:
            if re.search(r"(?<![a-z0-9])" + re.escape(u) + r"(?![a-z0-9])", baixo):
                achados.append(f"{rel}: nome de usuário")
    assert not achados, "\n".join(achados)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
