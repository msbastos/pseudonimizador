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
import shutil
import socket
import sys
import threading
import time
import zipfile
from dataclasses import asdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Iterator
from urllib.parse import unquote, urlsplit

from docx.opc.exceptions import PackageNotFoundError
from lxml import etree

from .. import VERSAO
from ..estado import Config, abrir_log, carregar, gravar, preparar_pastas, validar
from ..restaurar import TokenOrfao, id_do_mapa, restaurar_docx, restaurar_texto
from ..saida import _destino, mapas
from .pasta_monitorada import Vigia
from .registro import DocumentoInexistente, Registro, validar_nome_upload

PASTA_ESTATICO = Path(__file__).resolve().parent / "estatico"
ESTATICOS = {"index.html": "text/html; charset=utf-8", "app.js": "text/javascript; charset=utf-8",
             "app.css": "text/css; charset=utf-8"}
CABECALHOS = {"Content-Security-Policy": "default-src 'self'", "X-Content-Type-Options": "nosniff",
              "Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
LIMITE_JSON = 2 * 1024 * 1024
LIMITE_ARQUIVO = 100 * 1024 * 1024
RE_ID = r"[0-9a-f]{16}"
ERROS_DE_DOCX = (zipfile.BadZipFile, KeyError, ValueError, etree.XMLSyntaxError, PackageNotFoundError)
ROTAS: list[tuple[str, str]] = [
    ("GET", r"/api/estado"),
    ("POST", r"/api/encerrar"),
    ("GET", r"/api/documentos"),
    ("POST", r"/api/documentos"),
    ("GET", rf"/api/documentos/{RE_ID}"),
    ("DELETE", rf"/api/documentos/{RE_ID}"),
    ("POST", rf"/api/documentos/{RE_ID}/decisao"),
    ("POST", rf"/api/documentos/{RE_ID}/acrescentar"),
    ("POST", rf"/api/documentos/{RE_ID}/gerar"),
    ("POST", rf"/api/documentos/{RE_ID}/abrir"),
    ("GET", r"/api/config"),
    ("POST", r"/api/config"),
    ("GET", r"/api/mapas"),
    ("POST", r"/api/restaurar/docx"),
    ("POST", r"/api/restaurar/texto"),
]


def _iguais(a, b: str) -> bool:
    """Comparação em tempo constante sobre bytes UTF-8: hmac.compare_digest
    levanta TypeError para str não ASCII."""
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    return hmac.compare_digest(a.encode("utf-8", "surrogatepass"), b.encode("utf-8", "surrogatepass"))


class ErroDaApi(Exception):
    def __init__(self, status: int, erro: str, mensagem: str, **extra):
        super().__init__(mensagem)
        self.status, self.erro, self.mensagem, self.extra = status, erro, mensagem, extra


def listar_mapas(pasta_mapas: Path) -> list[dict]:
    """Só id e data, nunca o conteúdo. A data vem do próprio id
    (AAAAMMDD-HHMMSS-xxxx, saida.mapas.novo_id); fora do padrão, do mtime."""
    saida = []
    for arq in sorted(Path(pasta_mapas).glob("*.json"), reverse=True):
        m = re.match(r"(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})", arq.stem)
        if m:
            data = f"{m[3]}/{m[2]}/{m[1]} {m[4]}:{m[5]}"
        else:
            data = datetime.fromtimestamp(arq.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
        saida.append({"id": arq.stem, "data": data})
    return saida


def _abrir_no_windows(caminho: Path) -> None:
    """Abre o arquivo ou a pasta no programa associado (só fora dos testes)."""
    if os.environ.get("PSEUDONIMIZADOR_TESTE"):
        raise RuntimeError("os.startfile desligado nos testes")
    os.startfile(str(caminho))  # noqa: S606


class Aplicacao:
    def __init__(self, pasta_estado: Path, *, config: Config | None = None, inatividade_s: float = 1800.0, vigia_pasta_s: float = 2.0,
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
        self.trava_config = threading.Lock()      # gravar + aplicar a configuração, um POST por vez
        self.porta = 0
        self.servidor = None
        self.inatividade_s = inatividade_s
        self._ultimo = time.monotonic()
        self.encerrar_pedido = False
        self.abrir_no_windows = abrir_no_windows or _abrir_no_windows
        self.vigia = Vigia(self.registro, self.config.entrada, self.config.processados, self.log,
                           intervalo_s=vigia_pasta_s)
        self.registro.apos_gerar = self.vigia.processado
        self.vigia.iniciar()

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
        return any(_iguais(token, t) for t in tokens)

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
        self.vigia.trocar(nova.entrada, nova.processados)

    def encerrar(self) -> None:
        self.vigia.parar()
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
        if self.headers.get("Content-Length") is None:
            raise ErroDaApi(400, "corpo", "tamanho do arquivo não informado")
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
            if not _iguais(segredo, app.segredo):
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
        """Os blocos da API."""
        return (self._api_documentos, self._api_restaurar, self._api_config)

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

    # --- documentos ----------------------------------------------------------
    def _api_documentos(self, metodo: str, caminho: str) -> bool:
        reg = self.app.registro
        if caminho == "/api/documentos":
            if metodo == "GET":
                self._json(200, {"documentos": reg.lista()})
                return True
            if metodo == "POST":
                nome = unquote(self.headers.get("X-Nome-Arquivo") or "")
                if not nome.strip():
                    raise ErroDaApi(400, "nome", "falta o cabeçalho X-Nome-Arquivo")
                if Path(nome.replace("\\", "/").rstrip(" .")).suffix.lower() not in (".docx", ".pdf"):
                    raise ErroDaApi(415, "formato", "só arquivos .docx ou .pdf")
                tamanho, pedacos = self._corpo_bruto(LIMITE_ARQUIVO)
                if tamanho == 0:
                    raise ErroDaApi(400, "corpo", "arquivo vazio")
                try:
                    doc = reg.registrar_upload(nome, pedacos)
                except ValueError as e:        # formato já conferido acima: sobra o nome com caracteres proibidos
                    raise ErroDaApi(400, "nome", str(e)) from None
                except RuntimeError as e:      # o programa está encerrando
                    raise ErroDaApi(503, "encerrando", str(e)) from None
                self._json(202, {"id": doc.id, "nome": doc.nome, "situacao": doc.situacao})
                return True
            return False
        m = re.fullmatch(rf"/api/documentos/({RE_ID})(?:/(decisao|acrescentar|gerar|abrir))?", caminho)
        if not m:
            return False
        id_, acao = m.group(1), m.group(2)
        try:
            if acao is None and metodo == "GET":
                self._json(200, reg.detalhe(id_))
                return True
            if acao is None and metodo == "DELETE":
                reg.descartar(id_)
                self._json(200, {"ok": True})
                return True
            if metodo != "POST" or acao is None:
                raise ErroDaApi(405, "metodo", "método não permitido")
            corpo = self._corpo_json()
            if acao == "decisao":
                aceito = corpo.get("aceito")
                if not isinstance(aceito, bool):
                    raise ErroDaApi(400, "corpo", "aceito deve ser true ou false")
                reg.decidir(id_, str(corpo.get("categoria") or ""), str(corpo.get("valor") or ""), aceito)
                self._json(200, {"ok": True})
                return True
            if acao == "acrescentar":
                item = reg.acrescentar(id_, str(corpo.get("valor") or ""), str(corpo.get("categoria") or "pessoa"))
                self._json(200, {"ok": True, "item": item})
                return True
            return self._acao_de_geracao(id_, acao, corpo)
        except DocumentoInexistente:
            raise ErroDaApi(404, "documento", "documento não encontrado") from None
        except LookupError as e:
            raise ErroDaApi(404, "item", str(e)) from None
        except ValueError as e:
            raise ErroDaApi(409, "valor", str(e)) from None
        except RuntimeError as e:
            raise ErroDaApi(409, "situacao", str(e)) from None

    def _acao_de_geracao(self, id_: str, acao: str, corpo: dict) -> bool:
        reg, cfg = self.app.registro, self.app.config
        if acao == "gerar":
            formato = str(corpo.get("formato") or cfg.formato)
            tipo = str(corpo.get("tipo") or cfg.tipo)
            modo = str(corpo.get("modo") or cfg.modo)
            reg.pedir_geracao(id_, formato=formato, tipo=tipo, modo=modo, pasta_saida=cfg.saida, pasta_mapas=cfg.mapas)
            self._json(202, {"ok": True, "situacao": "gerando"})
            return True
        if acao == "abrir":
            alvo = corpo.get("alvo")
            if alvo not in ("arquivo", "pasta"):
                raise ErroDaApi(400, "corpo", "alvo: arquivo ou pasta")
            d = reg.obter(id_)
            if d.situacao != "pronto" or not d.resultado:
                raise ErroDaApi(409, "situacao", "o documento ainda não foi gerado")
            saida = Path(d.resultado["saida"])
            try:
                self.app.abrir_no_windows(saida if alvo == "arquivo" else saida.parent)
            except OSError:
                raise ErroDaApi(409, "arquivo", "não foi possível abrir: o arquivo ou a pasta não existe mais "
                                                "(foi apagado ou movido depois da geração)") from None
            self.app.log.info("documento %s: abrir %s", id_, alvo)
            self._json(200, {"ok": True})
            return True
        return False

    # --- configuração --------------------------------------------------------
    def _config_publica(self) -> dict:
        c = self.app.config
        return {**asdict(c), "pastas": c.pastas()}

    def _api_config(self, metodo: str, caminho: str) -> bool:
        if caminho != "/api/config":
            return False
        if metodo == "GET":
            self._json(200, self._config_publica())
            return True
        if metodo == "POST":
            try:
                nova = validar(self._corpo_json())
            except ValueError as e:
                raise ErroDaApi(400, "config", str(e)) from None
            try:
                preparar_pastas(nova)
            except (OSError, ValueError) as e:
                raise ErroDaApi(400, "config", f"não foi possível criar as pastas: {getattr(e, 'strerror', None) or e}") from None
            with self.app.trava_config:
                try:
                    gravar(self.app.pasta_estado, nova)
                except OSError:
                    raise ErroDaApi(409, "config", "não foi possível gravar as configurações") from None
                self.app.aplicar_config(nova)
            self.app.log.info("configuração gravada (%s, %s, %s)", nova.formato, nova.tipo, nova.modo)
            self._json(200, self._config_publica())
            return True
        return False

    # --- restaurar -----------------------------------------------------------
    def _mapa_escolhido(self, id_mapa) -> dict:
        if not isinstance(id_mapa, str) or not re.fullmatch(r"[0-9A-Za-z_-]{1,80}", id_mapa):
            raise ErroDaApi(400, "mapa", "escolha um mapa da lista")
        caminho = mapas.achar(self.app.config.mapas, id_mapa)
        if caminho is None:
            raise ErroDaApi(404, "mapa", "mapa não encontrado")
        return self._mapa_valido(caminho)

    def _mapa_valido(self, caminho: Path) -> dict:
        try:
            mapa = mapas.carregar(caminho)
        except (OSError, ValueError):
            mapa = None
        if not isinstance(mapa, dict) or not isinstance(mapa.get("tokens"), dict):
            raise ErroDaApi(409, "mapa", "o mapa escolhido está corrompido")
        return mapa

    def _api_restaurar(self, metodo: str, caminho: str) -> bool:
        cfg = self.app.config
        if (metodo, caminho) == ("GET", "/api/mapas"):
            self._json(200, {"mapas": listar_mapas(cfg.mapas)})
            return True
        if (metodo, caminho) == ("POST", "/api/restaurar/texto"):
            corpo = self._corpo_json()
            texto = corpo.get("texto")
            if not isinstance(texto, str) or not texto.strip():
                raise ErroDaApi(400, "corpo", "cole o texto com os tókens")
            mapa = self._mapa_escolhido(corpo.get("mapa"))
            try:
                restaurado = restaurar_texto(texto, mapa)
            except TokenOrfao as e:
                raise ErroDaApi(409, "orfao", str(e)) from None
            self.app.log.info("restauração de texto colado")
            self._json(200, {"texto": restaurado})
            return True
        if (metodo, caminho) == ("POST", "/api/restaurar/docx"):
            nome = unquote(self.headers.get("X-Nome-Arquivo") or "")
            if not nome.strip():
                raise ErroDaApi(400, "nome", "falta o cabeçalho X-Nome-Arquivo")
            if Path(nome.replace("\\", "/").rstrip(" .")).suffix.lower() != ".docx":
                raise ErroDaApi(415, "formato", "só arquivos .docx")
            try:
                nome = validar_nome_upload(nome, (".docx",))
            except ValueError as e:
                raise ErroDaApi(400, "nome", str(e)) from None
            id_mapa = self.headers.get("X-Mapa") or ""
            tamanho, pedacos = self._corpo_bruto(LIMITE_ARQUIVO)
            if tamanho == 0:
                raise ErroDaApi(400, "corpo", "arquivo vazio")
            pasta = self.app.pasta_estado / "tmp" / f"restaurar-{secrets.token_hex(4)}"
            pasta.mkdir(parents=True)
            try:
                origem = pasta / nome
                with open(origem, "wb") as f:
                    for pedaco in pedacos:
                        f.write(pedaco)
                if id_mapa:
                    mapa = self._mapa_escolhido(id_mapa)
                else:
                    try:
                        ident = id_do_mapa(origem)
                    except ERROS_DE_DOCX:
                        raise ErroDaApi(409, "arquivo", "o arquivo não é um DOCX válido") from None
                    achado = mapas.achar(cfg.mapas, ident) if ident else None
                    mapa = self._mapa_valido(achado) if achado else None
                if mapa is None:
                    raise ErroDaApi(409, "mapa", "Mapa não encontrado para este arquivo; escolha um da lista.")
                cfg.saida.mkdir(parents=True, exist_ok=True)
                destino = _destino(cfg.saida, f"{origem.stem} - restaurado", ".docx")
                try:
                    n = restaurar_docx(origem, destino, mapa)
                except TokenOrfao as e:
                    raise ErroDaApi(409, "orfao", str(e)) from None
                except ERROS_DE_DOCX:
                    raise ErroDaApi(409, "arquivo", "o arquivo não é um DOCX válido") from None
                except OSError:
                    raise ErroDaApi(409, "arquivo", "não foi possível gravar o arquivo restaurado") from None
            finally:
                shutil.rmtree(pasta, ignore_errors=True)
            self.app.log.info("restauração de DOCX: %d troca(s)", n)
            self._json(200, {"ok": True, "saida_nome": destino.name, "trocas": n})
            return True
        return False


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
