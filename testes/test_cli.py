# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import json
import subprocess
import sys

import fabrica as F
from _base import RAIZ


def _cli(*args):
    return subprocess.run([sys.executable, "-X", "utf8", "-m", "pseudonimizador", *map(str, args)],
                          cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")


def test_detectar_editar_gerar_restaurar():
    pasta = F.pasta_temporaria("cli")
    arq = F.contrato_docx(pasta / "contrato.docx")
    rev = pasta / "revisao.json"
    p = _cli("detectar", arq, "--revisao", rev)
    assert p.returncode == 0, p.stderr
    dados = json.loads(rev.read_text(encoding="utf-8"))
    for item in dados["itens"]:
        if item["categoria"] == "email":
            item["aceito"] = False
    dados["acrescentar"] = [{"valor": "Porto Alegre", "categoria": "outro"}]
    rev.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    p = _cli("gerar", arq, "--revisao", rev, "--formato", "layout", "--modo", "reversivel",
             "--saida", pasta / "Saida", "--mapas", pasta / "Mapas")
    assert p.returncode == 0, p.stderr
    saida = pasta / "Saida" / "contrato - pseudonimizado.docx"
    from pseudonimizador.leitura import ler
    texto = ler(saida).texto
    assert F.EMAIL in texto and "Porto Alegre" not in texto and F.PESSOA_1 not in texto
    p = _cli("restaurar", saida, "--saida", pasta / "restaurado.docx", "--mapas", pasta / "Mapas")
    assert p.returncode == 0, p.stderr
    assert "Porto Alegre" in ler(pasta / "restaurado.docx").texto


def test_erro_de_leitura_codigo_2():
    pasta = F.pasta_temporaria("cli2")
    (pasta / "x.txt").write_text("a", encoding="utf-8")
    p = _cli("detectar", pasta / "x.txt", "--revisao", pasta / "r.json")
    assert p.returncode == 2 and "formato não aceito" in p.stderr


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
