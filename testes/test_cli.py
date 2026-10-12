# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import json
import os
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


def test_restaurar_argumentos_invalidos():
    pasta = F.pasta_temporaria("cli3")
    p = _cli("restaurar", "--mapas", pasta / "M")
    assert p.returncode == 2 and "erro:" in p.stderr, p.stderr
    p = _cli("restaurar", pasta / "x.docx", "--mapas", pasta / "M")
    assert p.returncode == 2 and "erro:" in p.stderr, p.stderr
    p = _cli("restaurar", pasta / "x.docx", "--texto", pasta / "t.txt", "--saida", pasta / "o.docx")
    assert p.returncode == 2 and "erro:" in p.stderr, p.stderr


def test_arquivo_inexistente_codigo_2_sem_traceback():
    pasta = F.pasta_temporaria("cli4")
    p = _cli("gerar", pasta / "nao_existe.docx", "--formato", "layout", "--modo", "definitivo",
             "--saida", pasta / "S", "--mapas", pasta / "M")
    assert p.returncode == 2 and "Traceback" not in p.stderr and "erro:" in p.stderr, p.stderr


def test_revisao_malformada_e_de_outro_arquivo():
    pasta = F.pasta_temporaria("cli5")
    arq = F.contrato_docx(pasta / "contrato.docx")
    rev = pasta / "r.json"
    rev.write_text(json.dumps({"arquivo": str(arq), "itens": [{"categoria": "pessoa"}]}), encoding="utf-8")
    args = ("--formato", "layout", "--modo", "definitivo", "--saida", pasta / "S", "--mapas", pasta / "M")
    p = _cli("gerar", arq, "--revisao", rev, *args)
    assert p.returncode == 2 and "valor" in p.stderr and "Traceback" not in p.stderr, p.stderr
    rev.write_text(json.dumps({"arquivo": "outro.docx", "itens": []}), encoding="utf-8")
    p = _cli("gerar", arq, "--revisao", rev, *args)
    assert p.returncode == 2 and "aviso: a revisão é de outro arquivo" in p.stderr, p.stderr
    assert not (pasta / "S").exists()


def test_sem_subcomando_abre_a_janela():
    from pseudonimizador import __main__ as cli
    from pseudonimizador.web import abrir as A
    original = A.principal
    A.principal = lambda: 7
    try:
        assert cli.main([]) == 7
    finally:
        A.principal = original
    p = _cli("--help")
    assert p.returncode == 0 and "detectar" in p.stdout and "janela" in p.stdout


def _cli_estado(estado_dir, *args):
    env = {**os.environ, "PSEUDONIMIZADOR_ESTADO": str(estado_dir)}
    return subprocess.run([sys.executable, "-X", "utf8", "-m", "pseudonimizador", *map(str, args)],
                          cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", env=env)


def test_configurar_grava_config_e_cria_pastas():
    pasta = F.pasta_temporaria("cli_configurar")
    estado_dir, base = pasta / "estado", pasta / "Arquivos"
    p = _cli_estado(estado_dir, "configurar", "--pasta-base", base)
    assert p.returncode == 0, p.stderr
    cfg = json.loads((estado_dir / "config.json").read_text(encoding="utf-8"))
    assert cfg["pasta_base"] == str(base) and cfg["formato"] == "layout" and cfg["modo"] == "reversivel"
    for sub in ("Entrada", "Entrada/Processados", "Saida", "Mapas"):
        assert (base / sub).is_dir(), sub
    assert "configurar" in _cli("--help").stdout


def test_configurar_preserva_os_outros_campos_e_recusa_caminho_relativo():
    pasta = F.pasta_temporaria("cli_configurar2")
    estado_dir = pasta / "estado"
    estado_dir.mkdir()
    (estado_dir / "config.json").write_text(json.dumps({"pasta_base": str(pasta / "A"), "formato": "texto",
                                                         "tipo": "pdf", "modo": "definitivo"}), encoding="utf-8")
    p = _cli_estado(estado_dir, "configurar", "--pasta-base", pasta / "B")
    assert p.returncode == 0, p.stderr
    cfg = json.loads((estado_dir / "config.json").read_text(encoding="utf-8"))
    assert cfg["pasta_base"] == str(pasta / "B") and cfg["formato"] == "texto" and cfg["modo"] == "definitivo"
    p = _cli_estado(estado_dir, "configurar", "--pasta-base", "Relativa")
    assert p.returncode == 2 and "erro:" in p.stderr and "Traceback" not in p.stderr, p.stderr
    assert json.loads((estado_dir / "config.json").read_text(encoding="utf-8"))["pasta_base"] == str(pasta / "B")


def test_configurar_pasta_impossivel_nao_altera_a_config():
    pasta = F.pasta_temporaria("cli_configurar3")
    estado_dir = pasta / "estado"
    p = _cli_estado(estado_dir, "configurar", "--pasta-base", pasta / "A")
    assert p.returncode == 0, p.stderr
    antes = (estado_dir / "config.json").read_bytes()
    arquivo = pasta / "arquivo.txt"
    arquivo.write_text("x", encoding="utf-8")
    p = _cli_estado(estado_dir, "configurar", "--pasta-base", arquivo / "Sub")
    assert p.returncode == 2 and "erro:" in p.stderr and "Traceback" not in p.stderr, p.stderr
    assert (estado_dir / "config.json").read_bytes() == antes


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
