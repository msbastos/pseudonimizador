# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
# executar_todos: sozinho
"""Abrir a janela: mutex de verdade (Windows), instancia.json, segunda
abertura na instância viva, substituição de versão, Edge/navegador
injetados, erro sob pythonw numa caixa injetada."""
import _base  # noqa: F401
import json
import os
import secrets
import threading
import time
import urllib.request
from pathlib import Path

import fabrica as F
from pseudonimizador import VERSAO
from pseudonimizador.estado import Config
from pseudonimizador.web import abrir as A
from pseudonimizador.web.servidor import Aplicacao


def _esperar(condicao, prazo=30.0):
    fim = time.monotonic() + prazo
    while not condicao():
        assert time.monotonic() < fim, "esperou demais"
        time.sleep(0.05)


def _criar_app(inatividade_s):
    def criar(pasta):
        return Aplicacao(pasta, config=Config(pasta_base=str(Path(pasta).parent / "Base")), inatividade_s=inatividade_s)
    return criar


def _pedir(porta, caminho, token, corpo=None):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    cab = {"X-Token": token}
    if dados is not None:
        cab["Content-Type"] = "application/json"
    req = urllib.request.Request(f"http://127.0.0.1:{porta}{caminho}", data=dados, headers=cab,
                                 method="POST" if dados is not None else "GET")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status


def test_mutex_nomeado_de_verdade():
    nome = f"Pseudonimizador-Teste-{secrets.token_hex(4)}"
    m1 = A.Mutex(nome)
    m2 = A.Mutex(nome)
    assert not m1.ja_existia and m2.ja_existia
    m1.fechar()
    m2.fechar()
    m3 = A.Mutex(nome)
    assert not m3.ja_existia
    m3.fechar()
    assert A.processo_vivo(os.getpid()) and not A.processo_vivo(0)


def test_segunda_abertura_reaproveita_a_instancia():
    """Review Focus 2: duas aberturas, um só servidor."""
    pasta = F.pasta_temporaria("abrir") / "estado"
    nome = f"Pseudonimizador-Teste-{secrets.token_hex(4)}"
    urls = []
    t = threading.Thread(target=A.abrir, kwargs=dict(pasta_estado=pasta, nome_mutex=nome, abrir_janela=urls.append,
                                                     criar_app=_criar_app(60.0), vigia_s=0.1), daemon=True)
    t.start()
    _esperar(lambda: len(urls) == 1)
    inst = A.ler_instancia(pasta)
    assert inst["pid"] == os.getpid() and inst["porta"] > 0 and inst["versao"] == VERSAO and len(inst["segredo"]) >= 43
    assert urls[0] == f"http://127.0.0.1:{inst['porta']}/#t=" + urls[0].split("#t=")[1]
    assert A.abrir(pasta_estado=pasta, nome_mutex=nome, abrir_janela=urls.append, criar_app=_criar_app(60.0)) == 0
    assert len(urls) == 2 and urls[1].startswith(f"http://127.0.0.1:{inst['porta']}/#t=") and urls[1] != urls[0]
    token = urls[1].split("#t=")[1]
    assert _pedir(inst["porta"], "/api/estado", token) == 200
    assert _pedir(inst["porta"], "/api/encerrar", token, {}) == 200
    t.join(15)
    assert not t.is_alive() and A.ler_instancia(pasta) is None
    assert (pasta / "logs" / "servidor.log").read_text(encoding="utf-8").count("segunda abertura") == 1


def test_segunda_abertura_nao_constroi_aplicacao_nem_toca_no_tmp():
    """Só a instância viva pode ter Aplicacao/Registro na pasta de estado: o
    Registro apaga o tmp ao nascer, o que destruiria os envios da viva."""
    pasta = F.pasta_temporaria("abrir_sem_app") / "estado"
    nome = f"Pseudonimizador-Teste-{secrets.token_hex(4)}"
    urls = []
    t = threading.Thread(target=A.abrir, kwargs=dict(pasta_estado=pasta, nome_mutex=nome, abrir_janela=urls.append,
                                                     criar_app=_criar_app(60.0), vigia_s=0.1), daemon=True)
    t.start()
    _esperar(lambda: len(urls) == 1)
    marcador = pasta / "tmp" / "envio-vivo.bin"
    marcador.write_bytes(b"x")
    construidas = []

    def proibida(p):
        construidas.append(p)
        raise AssertionError("a segunda abertura não pode construir Aplicacao")
    assert A.abrir(pasta_estado=pasta, nome_mutex=nome, abrir_janela=urls.append, criar_app=proibida) == 0
    assert construidas == [] and marcador.read_bytes() == b"x" and len(urls) == 2
    # com o mutex preso e sem instância viva, também não constrói nada
    pasta2 = F.pasta_temporaria("abrir_sem_app2") / "estado"
    nome2 = f"Pseudonimizador-Teste-{secrets.token_hex(4)}"
    dono = A.Mutex(nome2)
    try:
        try:
            A.abrir(pasta_estado=pasta2, nome_mutex=nome2, abrir_janela=urls.append, criar_app=proibida, tentativas=2, espera_s=0.05)
        except A.ErroAbertura:
            pass
        else:
            raise AssertionError("deveria dar ErroAbertura")
    finally:
        dono.fechar()
    assert construidas == []
    token = urls[1].split("#t=")[1]
    porta = A.ler_instancia(pasta)["porta"]
    assert _pedir(porta, "/api/encerrar", token, {}) == 200
    t.join(15)
    assert not t.is_alive()


def test_instancia_vazia_de_outra_versao_e_substituida():
    pasta = F.pasta_temporaria("abrir_versao") / "estado"
    nome = f"Pseudonimizador-Teste-{secrets.token_hex(4)}"
    urls = []
    t = threading.Thread(target=A.abrir, kwargs=dict(pasta_estado=pasta, nome_mutex=nome, abrir_janela=urls.append,
                                                     criar_app=_criar_app(60.0), vigia_s=0.1, versao="0.0.1"), daemon=True)
    t.start()
    _esperar(lambda: len(urls) == 1)
    porta_velha = A.ler_instancia(pasta)["porta"]
    # sem trabalho a perder: a velha sai e a nova sobe no lugar (e sai por inatividade)
    codigo = A.abrir(pasta_estado=pasta, nome_mutex=nome, abrir_janela=urls.append, criar_app=_criar_app(0.5),
                     vigia_s=0.1, versao=VERSAO)
    assert codigo == 0 and len(urls) == 2
    porta_nova = int(urls[1].split(":")[2].split("/")[0])
    assert porta_nova != porta_velha and f":{porta_velha}/" in urls[0]
    t.join(5)
    assert not t.is_alive() and A.ler_instancia(pasta) is None


def test_instancia_com_revisao_pendente_de_outra_versao_e_mantida():
    from pseudonimizador.web.registro import Doc
    pasta = F.pasta_temporaria("abrir_versao_revisao") / "estado"
    nome = f"Pseudonimizador-Teste-{secrets.token_hex(4)}"
    urls, apps = [], []

    def criar(p):
        apps.append(_criar_app(60.0)(p))
        return apps[-1]
    t = threading.Thread(target=A.abrir, kwargs=dict(pasta_estado=pasta, nome_mutex=nome, abrir_janela=urls.append,
                                                     criar_app=criar, vigia_s=0.1, versao="0.0.1"), daemon=True)
    t.start()
    _esperar(lambda: len(urls) == 1)
    porta_velha = A.ler_instancia(pasta)["porta"]
    apps[0].registro._docs["b" * 16] = Doc("b" * 16, "x.docx", "janela", Path("x.docx"), situacao="revisao")
    construidas = []
    assert A.abrir(pasta_estado=pasta, nome_mutex=nome, abrir_janela=urls.append,
                   criar_app=lambda p: construidas.append(p), versao=VERSAO) == 0
    assert construidas == [] and len(urls) == 2 and urls[1].startswith(f"http://127.0.0.1:{porta_velha}/#t=")
    assert t.is_alive() and not apps[0].encerrar_pedido and "b" * 16 in apps[0].registro._docs
    assert _pedir(porta_velha, "/api/encerrar", urls[1].split("#t=")[1], {}) == 200      # menu Encerrar
    t.join(15)
    assert not t.is_alive()


def test_instancia_morta_no_json_nao_e_usada():
    """Mutex preso (como se outro processo estivesse abrindo) + instancia.json de um
    pid que já saiu: processo_vivo() é falso, ninguém é contatado e o erro é o claro."""
    import subprocess
    import sys
    pasta = F.pasta_temporaria("abrir_morto") / "estado"
    pasta.mkdir(parents=True)
    filho = subprocess.Popen([sys.executable, "-c", "pass"])
    filho.wait(30)
    assert not A.processo_vivo(filho.pid)
    (pasta / "instancia.json").write_text(json.dumps({"pid": filho.pid, "porta": 1, "segredo": "x", "versao": VERSAO}), encoding="utf-8")
    nome = f"Pseudonimizador-Teste-{secrets.token_hex(4)}"
    dono = A.Mutex(nome)
    urls, construidas = [], []
    try:
        try:
            A.abrir(pasta_estado=pasta, nome_mutex=nome, abrir_janela=urls.append, criar_app=construidas.append,
                    tentativas=2, espera_s=0.05)
        except A.ErroAbertura as e:
            assert "abrindo ou fechando" in str(e)
        else:
            raise AssertionError("a instância morta não pode ser usada")
    finally:
        dono.fechar()
    assert urls == [] and construidas == []
    # sem o mutex preso, o json velho é simplesmente sobrescrito
    assert A.abrir(pasta_estado=pasta, nome_mutex=nome, abrir_janela=urls.append, criar_app=_criar_app(0.5), vigia_s=0.1) == 0
    assert len(urls) == 1 and A.ler_instancia(pasta) is None


def test_mutex_preso_sem_instancia_viva_da_erro_claro():
    pasta = F.pasta_temporaria("abrir_preso") / "estado"
    nome = f"Pseudonimizador-Teste-{secrets.token_hex(4)}"
    dono = A.Mutex(nome)
    try:
        A.abrir(pasta_estado=pasta, nome_mutex=nome, abrir_janela=lambda u: None, tentativas=2, espera_s=0.05)
    except A.ErroAbertura as e:
        assert "abrindo ou fechando" in str(e)
    else:
        raise AssertionError("deveria avisar que outro Pseudonimizador está abrindo ou fechando")
    finally:
        dono.fechar()


def test_edge_ou_navegador_injetados():
    chamadas = []
    url = "http://127.0.0.1:1/#t=x"
    assert A.abrir_janela_web(url, localizar=lambda: Path("msedge.exe"), lancar=lambda args, **k: chamadas.append(args),
                              navegador=lambda u: chamadas.append(("nav", u))) == "edge"
    assert chamadas == [["msedge.exe", f"--app={url}"]]
    assert A.abrir_janela_web(url, localizar=lambda: None, lancar=lambda *a, **k: chamadas.append("edge"),
                              navegador=lambda u: chamadas.append(("nav", u))) == "navegador"
    assert chamadas[-1] == ("nav", url)
    edge = A.localizar_edge(registro=False)
    assert edge is None or edge.name.lower() == "msedge.exe"


def test_avisar_erro_usa_a_caixa_injetada():
    caixas = []
    A.avisar_erro("algo deu errado", caixa=lambda texto, titulo: caixas.append((texto, titulo)))
    assert caixas == [("algo deu errado", A.TITULO_ERRO)]


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
