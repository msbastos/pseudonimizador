# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Servidor HTTP local da janela: só 127.0.0.1, porta livre, token de
sessão no cabeçalho X-Token (hmac.compare_digest), Host conferido (DNS
rebinding), sem CORS, CSP default-src 'self'. As rotas da API estão em
ROTAS (o teste dos estáticos confere o app.js contra elas). Nada de valor
nem nome de arquivo no log."""
from __future__ import annotations

import hmac
import json
import os
import re
import secrets
import socket
import sys
import threading
import time
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Iterator
from urllib.parse import urlsplit

from .. import VERSAO
from ..estado import Config, abrir_log, carregar, preparar_pastas
from .registro import Registro

PASTA_ESTATICO = Path(__file__).resolve().parent / "estatico"
ESTATICOS = {"index.html": "text/html; charset=utf-8", "app.js": "text/javascript; charset=utf-8",
             "app.css": "text/css; charset=utf-8"}
CABECALHOS = {"Content-Security-Policy": "default-src 'self'", "X-Content-Type-Options": "nosniff",
              "Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
LIMITE_JSON = 2 * 1024 * 1024
LIMITE_ARQUIVO = 100 * 1024 * 1024
RE_ID = r"[0-9a-f]{16}"
ROTAS: list[tuple[str, str]] = [
    ("GET", r"/api/estado"),
    ("POST", r"/api/encerrar"),
]


class ErroDaApi(Exception):
    def __init__(self, status: int, erro: str, mensagem: str, **extra):
        super().__init__(mensagem)
        self.status, self.erro, self.mensagem, self.extra = status, erro, mensagem, extra


def _abrir_no_windows(caminho: Path) -> None:
    """Abre o arquivo ou a pasta no programa associado (só fora dos testes)."""
    if os.environ.get("PSEUDONIMIZADOR_TESTE"):
        raise RuntimeError("os.startfile desligado nos testes")
    os.startfile(str(caminho))  # noqa: S606


class Aplicacao:
    def __init__(self, pasta_estado: Path, *, config: Config | None = None, inatividade_s: float = 1800.0,
                 abrir_no_windows: Callable[[Path], None] | None = None,
                 ler: Callable | None = None, gerar: Callable | None = None):
        self.pasta_estado = Path(pasta_estado)
        self.pasta_estado.mkdir(parents=True, exist_ok=True)
        self.log = abrir_log(self.pasta_estado)
        self.config = config or carregar(self.pasta_estado)
        preparar_pastas(self.config)
        extras = {k: v for k, v in (("ler", ler), ("gerar", gerar)) if v is not None}
        self.registro = Registro(self.pasta_estado / "tmp", self.log, **extras)
        self.segredo = secrets.token_urlsafe(32)        # 256 bits: só outro processo local o lê (instancia.json)
        self._tokens: list[str] = []
        self._trava = threading.Lock()
        self.porta = 0
        self.servidor = None
        self.inatividade_s = inatividade_s
        self._ultimo = time.monotonic()
        self.encerrar_pedido = False
        self.abrir_no_windows = abrir_no_windows or _abrir_no_windows

    # --- sessão --------------------------------------------------------------
    def emitir_token(self) -> str:
        token = secrets.token_urlsafe(32)
        with self._trava:
            self._tokens.append(token)
        return token

    def token_valido(self, token) -> bool:
        if not isinstance(token, str) or not token:
            return False
        with self._trava:
            tokens = list(self._tokens)
        return any(hmac.compare_digest(token, t) for t in tokens)

    def hosts(self) -> set[str]:
        return {f"127.0.0.1:{self.porta}", f"localhost:{self.porta}"}

    # --- vida ----------------------------------------------------------------
    def batimento(self) -> None:
        self._ultimo = time.monotonic()

    def ocioso(self) -> bool:
        return not self.registro.ocupado()

    def deve_encerrar(self) -> bool:
        return self.ocioso() and (self.encerrar_pedido or time.monotonic() - self._ultimo > self.inatividade_s)

    def pedir_encerramento(self) -> None:
        self.encerrar_pedido = True

    def aplicar_config(self, nova: Config) -> None:
        self.config = nova

    def encerrar(self) -> None:
        self.registro.encerrar(timeout=600)
        for h in list(self.log.handlers):
            h.close()
            self.log.removeHandler(h)


class Manipulador(BaseHTTPRequestHandler):
    server_version = "Pseudonimizador"
    sys_version = ""
    protocol_version = "HTTP/1.0"
    timeout = 120                      # conexão que nunca fecha não prende uma thread para sempre

    @property
    def app(self) -> Aplicacao:
        return self.server.app

    def log_message(self, formato, *args) -> None:
        pass                           # o padrão escreve em stderr com o caminho inteiro

    def log_request(self, code="-", size="-") -> None:
        try:
            numero = int(code)
        except (TypeError, ValueError):
            numero = 0
        if numero >= 400:
            self.app.log.info("%s %s -> %s", self.command, urlsplit(self.path).path, numero)

    # --- respostas -----------------------------------------------------------
    def _enviar(self, status: int, corpo: bytes, tipo: str) -> None:
        self.send_response(status)
        for chave, valor in CABECALHOS.items():
            self.send_header(chave, valor)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, status: int, dados: dict) -> None:
        self._enviar(status, json.dumps(dados, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _tamanho_anunciado(self, limite: int) -> int:
        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise ErroDaApi(400, "corpo", "Content-Length inválido") from None
        if tamanho < 0:
            raise ErroDaApi(400, "corpo", "Content-Length inválido")
        if tamanho > limite:
            raise ErroDaApi(413, "corpo", f"pedido maior que {limite // (1024 * 1024)} MB")
        return tamanho

    def _corpo_json(self, limite: int = LIMITE_JSON) -> dict:
        tamanho = self._tamanho_anunciado(limite)
        if tamanho == 0:
            return {}
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            raise ErroDaApi(400, "corpo", "só JSON")
        try:
            dados = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise ErroDaApi(400, "corpo", "JSON inválido") from None
        if not isinstance(dados, dict):
            raise ErroDaApi(400, "corpo", "JSON inválido")
        return dados

    def _corpo_bruto(self, limite: int = LIMITE_ARQUIVO) -> tuple[int, Iterator[bytes]]:
        """O corpo cru em pedaços; a recusa por tamanho acontece ANTES de ler."""
        tamanho = self._tamanho_anunciado(limite)

        def pedacos():
            restante = tamanho
            while restante > 0:
                bloco = self.rfile.read(min(65536, restante))
                if not bloco:
                    raise ErroDaApi(400, "corpo", "o envio foi interrompido")
                restante -= len(bloco)
                yield bloco
        return tamanho, pedacos()

    # --- métodos -------------------------------------------------------------
    def do_GET(self) -> None:
        self._tratar("GET")

    def do_POST(self) -> None:
        self._tratar("POST")

    def do_DELETE(self) -> None:
        self._tratar("DELETE")

    def _recusar_metodo(self) -> None:
        self._json(405, {"erro": "metodo", "mensagem": "método não permitido"})

    do_PUT = do_PATCH = do_OPTIONS = do_HEAD = _recusar_metodo

    def _tratar(self, metodo: str) -> None:
        try:
            self._rotear(metodo)
        except ErroDaApi as e:
            self._json(e.status, {**e.extra, "erro": e.erro, "mensagem": e.mensagem})
        except Exception as e:  # noqa: BLE001 — só o tipo vai ao log (o traceback poderia levar nomes)
            self.app.log.error("erro interno em %s %s: %s", metodo, urlsplit(self.path).path, type(e).__name__)
            self._json(500, {"erro": "interno", "mensagem": "Algo deu errado. Veja o log e recarregue a página (F5)."})

    def _rotear(self, metodo: str) -> None:
        app = self.app
        caminho = urlsplit(self.path).path
        if self.headers.get("Host") not in app.hosts():
            raise ErroDaApi(403, "host", "Host inesperado")
        if metodo == "GET" and caminho == "/":
            self._estatico("index.html")
            return
        if metodo == "GET" and caminho.startswith("/estatico/"):
            self._estatico(caminho[len("/estatico/"):])
            return
        if metodo == "POST" and caminho in ("/abrir", "/encerrar"):
            # vem de outro processo local (a segunda abertura), com o segredo do instancia.json
            segredo = self._corpo_json().get("segredo")
            if not isinstance(segredo, str) or not hmac.compare_digest(segredo, app.segredo):
                raise ErroDaApi(403, "segredo", "segredo de abertura inválido")
            if caminho == "/abrir":
                app.batimento()
                self.app.log.info("segunda abertura: token emitido")
                self._json(200, {"token": app.emitir_token()})
            else:
                app.pedir_encerramento()
                self.app.log.info("encerramento pedido por outra instância")
                self._json(200, {"ok": True})
            return
        if not caminho.startswith("/api/"):
            raise ErroDaApi(404, "nao_encontrado", "não encontrado")
        if not app.token_valido(self.headers.get("X-Token")):
            raise ErroDaApi(403, "token", "sem token de sessão — abra o Pseudonimizador pelo atalho")
        app.batimento()
        self._api(metodo, caminho)

    def _estatico(self, nome: str) -> None:
        if nome not in ESTATICOS or not (PASTA_ESTATICO / nome).is_file():
            raise ErroDaApi(404, "nao_encontrado", "não encontrado")
        self._enviar(200, (PASTA_ESTATICO / nome).read_bytes(), ESTATICOS[nome])

    def _tratadores(self) -> tuple:
        """Os blocos da API (as Tasks 4, 6 e 7 acrescentam os seus)."""
        return ()

    def _api(self, metodo: str, caminho: str) -> None:
        if (metodo, caminho) == ("GET", "/api/estado"):
            self._json(200, {"versao": VERSAO, "ocupado": self.app.registro.ocupado(), "pastas": self.app.config.pastas()})
            return
        if (metodo, caminho) == ("POST", "/api/encerrar"):
            self.app.pedir_encerramento()
            self.app.log.info("encerramento pedido pela janela")
            self._json(200, {"ok": True})
            return
        for tratar in self._tratadores():
            if tratar(metodo, caminho):
                return
        if any(re.fullmatch(padrao, caminho) for _, padrao in ROTAS):
            raise ErroDaApi(405, "metodo", "método não permitido")
        raise ErroDaApi(404, "nao_encontrado", "rota desconhecida")


class Servidor(ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True
    block_on_close = False

    def __init__(self, app: Aplicacao, porta: int = 0):
        self.app = app
        self.encerrado = False
        super().__init__(("127.0.0.1", porta), Manipulador)
        app.porta = self.server_address[1]
        app.servidor = self

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def handle_error(self, request, client_address) -> None:
        self.app.log.error("erro na conexão: %s", sys.exc_info()[0].__name__ if sys.exc_info()[0] else "?")

    def shutdown(self) -> None:
        self.encerrado = True
        super().shutdown()

    def url(self, token: str) -> str:
        return f"http://127.0.0.1:{self.app.porta}/#t={token}"

    def vigiar(self, intervalo_s: float = 2.0) -> threading.Thread:
        """Encerra quando app.deve_encerrar() (ocioso e: pedido de encerrar ou
        30 min sem pedidos). shutdown() roda noutra thread: de dentro do
        serve_forever travaria."""
        def laco():
            while True:
                time.sleep(intervalo_s)
                if self.encerrado:
                    return
                if self.app.deve_encerrar():
                    self.app.log.info("encerrando (%s)", "pedido" if self.app.encerrar_pedido else "inatividade")
                    threading.Thread(target=self.shutdown, daemon=True).start()
                    return
        t = threading.Thread(target=laco, name="pseudonimizador-vigia", daemon=True)
        t.start()
        return t
