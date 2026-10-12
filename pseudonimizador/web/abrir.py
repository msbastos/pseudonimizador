# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Abrir a janela do Pseudonimizador.

Instância única: mutex nomeado "Pseudonimizador-Servidor" (o sistema o
libera quando o processo morre) + estado\\instancia.json (pid, porta,
segredo de abertura de 256 bits, versão). A segunda abertura acha a
instância viva, pede um token novo em POST /abrir com o segredo e abre
outra janela; instância de outra versão recebe POST /encerrar e a nova
sobe quando ela sair. Janela = Edge em modo aplicativo (msedge --app=URL),
achado pelo App Paths do registro ou pelas pastas de programa; sem Edge, o
navegador padrão. Sob pythonw, sys.stdout/stderr None viram devnull e o
erro de abertura aparece numa caixa de mensagem do Windows. Mutex, pasta,
janela e aplicação são injetáveis (os testes nunca abrem navegador)."""
from __future__ import annotations

import http.client
import json
import os
import subprocess
import sys
import time
import traceback
import webbrowser
from pathlib import Path
from typing import Callable

from .. import VERSAO
from ..estado import pasta_estado as _pasta_estado_padrao
from ..motor.mapa import escrever_atomico

NOME_MUTEX = "Pseudonimizador-Servidor"
ARQUIVO_INSTANCIA = "instancia.json"
ERROR_ALREADY_EXISTS = 183
STILL_ACTIVE = 259
TITULO_ERRO = "Pseudonimizador — erro ao abrir"


class ErroAbertura(RuntimeError):
    """A abertura não pode seguir; a mensagem vai para o usuário."""


class Mutex:
    """Mutex nomeado só como marcador de existência (sem espera)."""

    def __init__(self, nome: str):
        self._handle = None
        self.ja_existia = False
        if sys.platform != "win32":
            return
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
        k32.CreateMutexW.restype = wintypes.HANDLE
        k32.CloseHandle.argtypes = (wintypes.HANDLE,)
        k32.CloseHandle.restype = wintypes.BOOL
        self._k32 = k32
        self._handle = k32.CreateMutexW(None, False, nome)
        self.ja_existia = ctypes.get_last_error() == ERROR_ALREADY_EXISTS
        if not self._handle:
            raise ctypes.WinError(ctypes.get_last_error())

    def fechar(self) -> None:
        if self._handle:
            self._k32.CloseHandle(self._handle)
            self._handle = None


def processo_vivo(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        k32.GetExitCodeProcess.restype = wintypes.BOOL
        k32.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = k32.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            codigo = wintypes.DWORD()
            return bool(k32.GetExitCodeProcess(handle, ctypes.byref(codigo))) and codigo.value == STILL_ACTIVE
        finally:
            k32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def ler_instancia(pasta_estado: Path) -> dict | None:
    try:
        dados = json.loads((Path(pasta_estado) / ARQUIVO_INSTANCIA).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dados if isinstance(dados, dict) else None


def gravar_instancia(pasta_estado: Path, porta: int, segredo: str, versao: str = VERSAO) -> None:
    escrever_atomico(Path(pasta_estado) / ARQUIVO_INSTANCIA, json.dumps(
        {"pid": os.getpid(), "porta": int(porta), "segredo": segredo, "versao": versao}))


def apagar_instancia_se_nossa(pasta_estado: Path, porta: int | None = None) -> None:
    dados = ler_instancia(pasta_estado)
    if dados and dados.get("pid") == os.getpid() and (porta is None or dados.get("porta") == porta):
        try:
            (Path(pasta_estado) / ARQUIVO_INSTANCIA).unlink()
        except OSError:
            pass


def _pedir(porta: int, caminho: str, segredo: str, timeout: float = 5.0) -> dict | None:
    try:
        con = http.client.HTTPConnection("127.0.0.1", int(porta), timeout=timeout)
        con.request("POST", caminho, body=json.dumps({"segredo": segredo}).encode("utf-8"),
                    headers={"Content-Type": "application/json"})
        r = con.getresponse()
        dados = json.loads(r.read().decode("utf-8") or "{}")
        con.close()
    except (OSError, ValueError, http.client.HTTPException):
        return None
    return dados if r.status == 200 and isinstance(dados, dict) else None


def pedir_token(porta: int, segredo: str) -> str | None:
    """Token novo da instância viva (POST /abrir com o segredo)."""
    dados = _pedir(porta, "/abrir", segredo)
    return dados.get("token") if dados else None


def pedir_encerramento(porta: int, segredo: str) -> bool:
    """Pede à instância viva (de outra versão) que se encerre. False se ela
    recusou (409: há documentos em andamento) ou não respondeu; nesse caso
    ela não guarda pedido nenhum e segue viva."""
    dados = _pedir(porta, "/encerrar", segredo)
    return bool(dados and dados.get("ok"))


def _saiu(pasta_estado: Path, inst: dict, prazo: float, espera: float = 0.1) -> bool:
    fim = time.monotonic() + prazo
    while True:
        atual = ler_instancia(pasta_estado)
        if atual is None or atual.get("porta") != inst.get("porta") or not processo_vivo(int(inst.get("pid", 0))):
            return True
        if time.monotonic() >= fim:
            return False
        time.sleep(espera)


def localizar_edge(*, registro: bool = True) -> Path | None:
    """msedge.exe: App Paths (HKCU, depois HKLM), depois as pastas de
    programa pelas variáveis de ambiente (nunca caminho de usuário fixo)."""
    candidatos: list[Path] = []
    if registro and sys.platform == "win32":
        import winreg
        chave = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"
        for raiz in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(raiz, chave) as k:
                    valor, _tipo = winreg.QueryValueEx(k, "")
                candidatos.append(Path(str(valor).strip('"')))
            except OSError:
                continue
    for var in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if base:
            candidatos.append(Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe")
    return next((c for c in candidatos if c.is_file()), None)


def abrir_janela_web(url: str, *, localizar: Callable[[], Path | None] = localizar_edge,
                     lancar: Callable = subprocess.Popen, navegador: Callable[[str], bool] = webbrowser.open) -> str:
    """'edge' (janela --app, só do Pseudonimizador) ou 'navegador' (o padrão)."""
    edge = localizar()
    if edge is not None:
        lancar([str(edge), f"--app={url}"], close_fds=True)
        return "edge"
    navegador(url)
    return "navegador"


def _criar_app_padrao(pasta_estado: Path):
    from .servidor import Aplicacao
    return Aplicacao(pasta_estado)


def abrir(*, pasta_estado: Path | None = None, nome_mutex: str = NOME_MUTEX,
          abrir_janela: Callable[[str], object] = abrir_janela_web, criar_app: Callable | None = None,
          versao: str = VERSAO, tentativas: int = 5, espera_s: float = 1.0, vigia_s: float = 2.0,
          espera_encerrar_s: float = 15.0) -> int:
    """Abre uma janela no Pseudonimizador vivo, ou sobe o servidor e fica
    nele (serve_forever) até a vigia encerrar (menu Encerrar ou 30 min
    ociosos). A instância viva de OUTRA versão é substituída quando ociosa."""
    from .servidor import Servidor
    pasta = Path(pasta_estado or _pasta_estado_padrao())
    pasta.mkdir(parents=True, exist_ok=True)
    mutex = Mutex(nome_mutex)
    try:
        if mutex.ja_existia:
            substituir = False
            for _ in range(max(1, tentativas)):
                inst = ler_instancia(pasta)
                if inst and processo_vivo(int(inst.get("pid", 0))):
                    porta, segredo = int(inst.get("porta", 0)), str(inst.get("segredo", ""))
                    if inst.get("versao") != versao and pedir_encerramento(porta, segredo) and \
                            _saiu(pasta, inst, espera_encerrar_s):
                        substituir = True            # a velha saiu: a nova sobe abaixo
                        break
                    token = pedir_token(porta, segredo)
                    if token:
                        abrir_janela(f"http://127.0.0.1:{porta}/#t={token}")
                        return 0
                time.sleep(espera_s)
            if not substituir:
                raise ErroAbertura("Outro Pseudonimizador está abrindo ou fechando. Espere alguns segundos e abra de novo.")
        app = (criar_app or _criar_app_padrao)(pasta)
        try:
            servidor = Servidor(app, 0)
            gravar_instancia(pasta, app.porta, app.segredo, versao)
        except BaseException:
            app.encerrar()
            raise
        try:
            app.log.info("servidor no ar (versão %s)", versao)
            abrir_janela(servidor.url(app.emitir_token()))
            servidor.vigiar(vigia_s)
            servidor.serve_forever(poll_interval=0.5)
        finally:
            servidor.server_close()
            app.encerrar()
            apagar_instancia_se_nossa(pasta, app.porta)
        return 0
    finally:
        mutex.fechar()


def _caixa_do_windows(texto: str, titulo: str) -> None:
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, texto[:3000], titulo, 0x10)


def avisar_erro(texto: str, caixa: Callable[[str, str], None] | None = None) -> None:
    """Caixa de mensagem do Windows (sob pythonw não há console)."""
    if caixa is None and sys.platform == "win32":
        caixa = _caixa_do_windows
    if caixa is not None:
        try:
            caixa(texto, TITULO_ERRO)
            return
        except (AttributeError, OSError):
            pass
    if sys.stderr is not None:
        print(texto, file=sys.stderr)


def _garantir_saidas() -> None:
    """Sob pythonw, sys.stdout/sys.stderr são None: uma biblioteca que
    escreva neles derrubaria a thread."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def principal() -> int:
    _garantir_saidas()
    try:
        return abrir()
    except ErroAbertura as e:
        avisar_erro(str(e))
        return 2
    except Exception as e:  # noqa: BLE001 — sob pythonw, sem isto a janela "não abre" muda
        avisar_erro(f"O Pseudonimizador não pôde abrir:\n\n{e!r}\n\nSe for biblioteca faltando, refaça a instalação "
                    f"(seção Instalação do README.md).\n\n" + traceback.format_exc()[-1500:])
        return 2
