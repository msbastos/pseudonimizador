# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Pasta monitorada: a Entrada\\ é varrida a cada 2 s enquanto o app está
aberto. Arquivo .docx/.pdf com tamanho e mtime iguais em duas varreduras
seguidas (acabou de ser copiado) vira documento de origem "pasta" e aparece
em Pendentes. Ocultos, temporários do Office (~$...) e a subpasta
Processados são ignorados. Depois de gerar, o original vai para
Entrada\\Processados. Erro de leitura: o original fica, e só é relido se
mudar (tamanho + mtime). Nada de nome de arquivo no log."""
from __future__ import annotations

import logging
import os
import shutil
import threading
from pathlib import Path

from ..saida import _destino       # a mesma regra " (2)" da saída
from .registro import Doc, Registro

ACEITOS = (".docx", ".pdf")
FILE_ATTRIBUTE_HIDDEN = 2


def _oculto(caminho: Path) -> bool:
    if caminho.name.startswith((".", "~$")):
        return True
    try:
        return bool(os.stat(caminho).st_file_attributes & FILE_ATTRIBUTE_HIDDEN)
    except (AttributeError, OSError):
        return False


class Vigia:
    def __init__(self, registro: Registro, pasta_entrada: Path, pasta_processados: Path,
                 log: logging.Logger, intervalo_s: float = 2.0):
        self.registro = registro
        self.log = log
        self.intervalo_s = intervalo_s
        self._trava = threading.Lock()
        self._parar = threading.Event()
        self._thread: threading.Thread | None = None
        self._vistos: dict[Path, tuple[int, float]] = {}        # última assinatura vista
        self._registrados: dict[Path, tuple[int, float]] = {}   # já virou documento (ou falhou)
        self._a_mover: list[Doc] = []                           # gerados, mas o original estava preso
        self.trocar(pasta_entrada, pasta_processados)

    def trocar(self, pasta_entrada: Path, pasta_processados: Path) -> None:
        with self._trava:
            self.pasta_entrada = Path(pasta_entrada)
            self.pasta_processados = Path(pasta_processados)
            self._vistos.clear()
            self._registrados.clear()
            self._a_mover.clear()

    def iniciar(self) -> None:
        self._parar.clear()
        self._thread = threading.Thread(target=self._laco, name="pseudonimizador-vigia-pasta", daemon=True)
        self._thread.start()

    def parar(self) -> None:
        self._parar.set()
        if self._thread is not None:
            self._thread.join(5)

    def _laco(self) -> None:
        while not self._parar.wait(self.intervalo_s):
            try:
                self.varrer()
            except Exception as e:  # noqa: BLE001 — a vigia nunca morre calada
                self.log.error("pasta monitorada: falha na varredura (%s)", type(e).__name__)

    def varrer(self) -> list[Doc]:
        """Uma varredura; devolve os documentos registrados nela."""
        novos: list[Doc] = []
        for doc in self._a_mover_agora():
            self.processado(doc)                     # tenta de novo o que estava preso
        with self._trava:
            pasta = self.pasta_entrada
            try:
                entradas = [c for c in pasta.iterdir() if c.is_file()]
            except OSError:
                return novos
            atuais: set[Path] = set()
            for c in entradas:
                if c.suffix.lower() not in ACEITOS or _oculto(c):
                    continue
                try:
                    st = c.stat()
                except OSError:
                    continue
                assinatura = (st.st_size, st.st_mtime)
                atuais.add(c)
                if self._registrados.get(c) == assinatura:
                    continue
                if self._vistos.get(c) != assinatura:
                    self._vistos[c] = assinatura           # primeira vez, ou ainda mudando
                    continue
                if st.st_size == 0:
                    continue
                try:
                    doc = self.registro.registrar_arquivo(c, "pasta")
                except RuntimeError:                 # o programa está encerrando
                    return novos
                self._registrados[c] = assinatura
                novos.append(doc)
                self.log.info("pasta monitorada: documento %s registrado", doc.id)
            for c in list(self._vistos):
                if c not in atuais:
                    self._vistos.pop(c, None)
                    self._registrados.pop(c, None)
        return novos

    def _a_mover_agora(self) -> list[Doc]:
        with self._trava:
            docs, self._a_mover = self._a_mover, []
        return docs

    def processado(self, doc: Doc) -> None:
        """Depois de gerar: o original vai para Processados (colisão → " (2)").
        Documento descartado no meio não move nada; arquivo preso fica para a
        próxima varredura; arquivo que já não existe é esquecido."""
        if doc.origem != "pasta" or doc.descartado:
            return
        with self._trava:
            processados = self.pasta_processados
            if doc.caminho.parent != self.pasta_entrada:      # pasta trocada desde então
                return
        try:
            if not doc.caminho.exists():
                self._esquecer(doc)
                return
            processados.mkdir(parents=True, exist_ok=True)
            destino = _destino(processados, doc.caminho.stem, doc.caminho.suffix)
            shutil.move(str(doc.caminho), str(destino))
        except OSError as e:
            with self._trava:
                self._a_mover.append(doc)
            self.log.warning("pasta monitorada: documento %s não foi movido, nova tentativa (%s)",
                             doc.id, type(e).__name__)
            return
        self._esquecer(doc)
        self.log.info("pasta monitorada: documento %s movido para Processados", doc.id)

    def _esquecer(self, doc: Doc) -> None:
        with self._trava:
            self._registrados.pop(doc.caminho, None)
            self._vistos.pop(doc.caminho, None)
