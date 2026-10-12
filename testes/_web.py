# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Servidor de verdade em porta 0 para os testes da janela, consultado com
urllib. Nenhum navegador, nenhum os.startfile."""
import _base  # noqa: F401
import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

import fabrica as F
from pseudonimizador.estado import Config
from pseudonimizador.web.servidor import Aplicacao, Servidor


class ServidorDeTeste:
    def __init__(self, nome: str, *, inatividade_s: float = 1800.0, vigia_s: float = 0.2, **kw):
        self.pasta = F.pasta_temporaria(nome)
        cfg = Config(pasta_base=str(self.pasta / "Base"))
        self.app = Aplicacao(self.pasta / "estado", config=cfg, inatividade_s=inatividade_s, **kw)
        self.servidor = Servidor(self.app, 0)
        self.porta = self.app.porta
        self.token = self.app.emitir_token()
        self.vigia_s = vigia_s
        self.thread = None

    def __enter__(self):
        self.servidor.vigiar(self.vigia_s)
        self.thread = threading.Thread(target=self.servidor.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_):
        if not self.servidor.encerrado:
            self.servidor.shutdown()
        self.servidor.server_close()
        self.app.encerrar()

    def pedir(self, metodo, caminho, corpo=None, cabecalhos=None, token=True, host=None):
        cab = {}
        if token:
            cab["X-Token"] = self.token if token is True else token
        if host:
            cab["Host"] = host
        dados = None
        if isinstance(corpo, (dict, list)):
            dados = json.dumps(corpo).encode("utf-8")
            cab["Content-Type"] = "application/json"
        elif isinstance(corpo, bytes):
            dados = corpo
            cab["Content-Type"] = "application/octet-stream"
        cab.update(cabecalhos or {})
        req = urllib.request.Request(f"http://127.0.0.1:{self.porta}{caminho}", data=dados, headers=cab, method=metodo)
        try:
            r = urllib.request.urlopen(req, timeout=120)
            status, bruto, tipo = r.status, r.read(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            status, bruto, tipo = e.code, e.read(), e.headers.get("Content-Type", "")
        return status, (json.loads(bruto.decode("utf-8")) if tipo.startswith("application/json") else bruto)

    def get(self, caminho, **k):
        return self.pedir("GET", caminho, **k)

    def post(self, caminho, corpo=None, **k):
        return self.pedir("POST", caminho, corpo, **k)

    def delete(self, caminho, **k):
        return self.pedir("DELETE", caminho, **k)

    def enviar_arquivo(self, caminho: Path, rota="/api/documentos", nome=None, cabecalhos=None):
        cab = {"X-Nome-Arquivo": quote(nome or Path(caminho).name)}
        cab.update(cabecalhos or {})
        return self.post(rota, Path(caminho).read_bytes(), cabecalhos=cab)

    def esperar(self, id_: str, *situacoes: str, prazo: float = 90.0) -> dict:
        fim = time.monotonic() + prazo
        while True:
            status, d = self.get(f"/api/documentos/{id_}")
            assert status == 200, d
            if d["situacao"] in situacoes:
                return d
            assert time.monotonic() < fim, f"documento ficou em {d['situacao']}: {d.get('erro')}"
            time.sleep(0.1)

    def log_texto(self) -> str:
        return (self.pasta / "estado" / "logs" / "servidor.log").read_text(encoding="utf-8")
