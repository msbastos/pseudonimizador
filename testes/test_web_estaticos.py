# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Os estáticos da janela: só arquivos locais, nada inline (CSP), rotas do
app.js existentes no servidor, rótulos acessíveis, e servidos pelo servidor."""
import _base  # noqa: F401
import re

from _web import ServidorDeTeste
from pseudonimizador.web.servidor import ESTATICOS, PASTA_ESTATICO, ROTAS

TELAS = ("documentos", "revisao", "resultado", "restaurar", "configuracoes")


def _ler(nome):
    return (PASTA_ESTATICO / nome).read_text(encoding="utf-8")


def test_estaticos_existem_sao_locais_e_sem_inline():
    html, js, css = _ler("index.html"), _ler("app.js"), _ler("app.css")
    for nome in ESTATICOS:
        assert "http://" not in _ler(nome) and "https://" not in _ler(nome), nome
    assert 'href="/estatico/app.css"' in html and 'src="/estatico/app.js"' in html
    assert not re.search(r"<script[^>]*>[^<]*\S[^<]*</script>", html), "script inline"
    assert not re.search(r"\son\w+\s*=", html) and " style=" not in html
    assert "@import" not in css and "url(" not in css
    assert "eval(" not in js and "innerHTML" not in js and "new Function" not in js
    assert '<html lang="pt-BR">' in html and '<meta charset="utf-8">' in html
    for tela in TELAS:
        assert f'id="tela-{tela}"' in html, tela
    for texto in ("Documentos", "Pendentes", "Revisão", "Restaurar nomes", "Configurações", "Encerrar"):
        assert texto in html, texto


def test_todo_campo_tem_rotulo():
    html = _ler("index.html")
    campos = re.findall(r'<(?:input|select|textarea)[^>]*\sid="([^"]+)"', html)
    assert campos
    rotulos = set(re.findall(r'<label[^>]*\sfor="([^"]+)"', html))
    for id_ in campos:
        assert id_ in rotulos, f"campo sem <label for> exato: {id_}"
    for r in rotulos:
        assert r in campos, f"label for sem campo com esse id: {r}"


def test_rotas_do_app_js_existem_no_servidor():
    js = _ler("app.js")
    js = re.sub(r"'\s*\+\s*\w+\s*\+\s*'", "0" * 16, js)        # '/api/documentos/' + id + '/gerar'
    js = re.sub(r"'\s*\+\s*\w+\b", "0" * 16 + "'", js)           # '/api/documentos/' + id
    usos = set(re.findall(r"api\('([A-Z]+)',\s*'(/api/[^']*)'", js))
    assert {p for _, p in usos} >= {"/api/documentos", "/api/config", "/api/mapas", "/api/encerrar"}
    assert usos == set(re.findall(r"'([A-Z]+)',\s*'(/api/[^']*)'", js)), "chamada a /api/ sem api(metodo, rota)"
    for metodo, rota in usos:
        assert any(m == metodo and re.fullmatch(p, rota) for m, p in ROTAS), f"app.js usa {metodo} {rota}, sem rota no servidor"


def test_app_js_confere_o_tamanho_antes_de_enviar():
    """Um fetch com mais de 100 MB tem a conexão derrubada pelo servidor (sem o
    JSON do 413): o navegador confere o limite antes, no envio e na restauração."""
    js = _ler("app.js")
    assert "100 * 1024 * 1024" in js
    assert len(re.findall(r"\.size\s*>\s*LIMITE", js)) >= 2, "conferir arq.size no envio e na restauração de DOCX"
    assert "LIMITE" in js.split("async function enviar")[1].split("function linhaDocumento")[0]
    assert "LIMITE" in js.split("form-rest-docx')")[1].split("form-rest-texto')")[0]


def test_servidor_entrega_a_pagina():
    with ServidorDeTeste("web_estaticos") as s:
        status, corpo = s.get("/", token=False)
        assert status == 200 and b"<title>Pseudonimizador</title>" in corpo
        status, corpo = s.get("/estatico/app.js", token=False)
        assert status == 200 and b"X-Token" in corpo
        assert s.get("/estatico/app.css", token=False)[0] == 200


def test_app_js_tem_batimento_e_aviso_de_pastas_e_checa_nome_longo():
    js, html = _ler("app.js"), _ler("index.html")
    assert re.search(r"setInterval\(.{0,200}api\('GET', '/api/estado'\).{0,120}60000\)", js, re.S), "batimento de 60 s"
    assert "pastas_disponiveis" in js and 'id="aviso-pastas"' in html
    assert "As pastas configuradas não estão acessíveis; ajuste em Configurações." in html
    assert re.search(r"arq\.name\.length\s*>\s*150", js)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
