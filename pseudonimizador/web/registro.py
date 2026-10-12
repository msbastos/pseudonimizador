# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Registro em memória dos documentos da janela e da pasta monitorada, e a
fila única de trabalho (uma thread) que lê — inclusive o OCR — e gera.
Nada daqui vai ao log com valor ou nome de arquivo: só ids, categorias,
contagens e tipos de exceção."""
from __future__ import annotations

import logging
import queue
import secrets
import shutil
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from ..estado import FORMATOS, MODOS, TIPOS
from ..leitura import ErroDeLeitura
from ..leitura import ler as _ler_padrao
from ..motor.mapa import normalizar
from ..revisao import PREFIXOS, Item, Revisao
from ..saida import VazamentoDetectado
from ..saida import gerar as _gerar_padrao

SITUACOES = ("lendo", "revisao", "gerando", "pronto", "erro")
CATEGORIAS = tuple(PREFIXOS)
ORIGENS = ("janela", "pasta")
ACEITOS = (".docx", ".pdf")
_PROIBIDOS = set('<>:"|?*')      # inclui o ":" dos fluxos alternativos do NTFS
LIMITE_NOME = 150
_RESERVADOS = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$",
               *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


class DocumentoInexistente(LookupError):
    """Id que não está (ou já não está) no registro."""


class Fila:
    """Uma thread, um trabalho por vez (o RapidOCR não é thread-safe)."""

    def __init__(self, log: logging.Logger):
        self._log = log
        self._fila: queue.Queue = queue.Queue()
        self._trava = threading.Lock()
        self._pendentes = 0
        self._encerrando = False
        self._thread = threading.Thread(target=self._laco, name="pseudonimizador-fila", daemon=True)
        self._thread.start()

    def enfileirar(self, trabalho: Callable[[], None]) -> None:
        with self._trava:
            self._pendentes += 1
        self._fila.put(trabalho)

    def ocupada(self) -> bool:
        with self._trava:
            return self._pendentes > 0

    def encerrar(self, timeout: float | None = None) -> bool:
        """Nenhum trabalho novo começa; o que está em curso termina (nunca é
        morto). Devolve True se a thread saiu dentro do prazo."""
        self._encerrando = True
        self._fila.put(None)
        self._thread.join(timeout)
        return not self._thread.is_alive()

    def _laco(self) -> None:
        while True:
            trabalho = self._fila.get()
            if trabalho is None:
                return
            try:
                if not self._encerrando:
                    trabalho()
            except Exception as e:  # noqa: BLE001 — a fila nunca morre; só o tipo vai ao log
                self._log.error("trabalho da fila falhou: %s", type(e).__name__)
            finally:
                with self._trava:
                    self._pendentes -= 1


@dataclass
class Doc:
    id: str
    nome: str                      # só para a tela; nunca para o log
    origem: str                    # janela | pasta
    caminho: Path
    pasta_tmp: Path | None = None  # tmp\<id> (só origem "janela")
    situacao: str = "lendo"
    revisao: Revisao | None = None
    avisos: list[str] = field(default_factory=list)
    resultado: dict | None = None  # {"saida": str, "mapa": str | None, "avisos": [...]}
    erro: dict | None = None       # {"mensagem": str, "valores": [...]} (só para a tela)
    descartado: bool = False


class Registro:
    def __init__(self, pasta_tmp: Path, log: logging.Logger, *, fila: Fila | None = None,
                 ler: Callable = _ler_padrao, gerar: Callable = _gerar_padrao,
                 apos_gerar: Callable[[Doc], None] | None = None):
        self.pasta_tmp = Path(pasta_tmp)
        self.pasta_tmp.mkdir(parents=True, exist_ok=True)
        self._log = log
        self.fila = fila or Fila(log)
        self._ler = ler
        self._gerar = gerar
        self.apos_gerar = apos_gerar     # a pasta monitorada move o original (Task 9)
        self._docs: dict[str, Doc] = {}
        self._trava = threading.RLock()
        self._tmp_pendentes: set[Path] = set()   # tmp que não deu para apagar ainda
        self._encerrado = False
        for resto in self.pasta_tmp.iterdir():   # sobras de uma execução que caiu
            self._apagar_pasta(resto)

    # --- entrada -------------------------------------------------------------
    def registrar_upload(self, nome: str, pedacos: Iterable[bytes]) -> Doc:
        nome = Path(str(nome).replace("\\", "/")).name
        if not nome or nome in (".", "..") or Path(nome).suffix.lower() not in ACEITOS:
            raise ValueError("só arquivos .docx ou .pdf")
        if any(c in _PROIBIDOS or ord(c) < 32 for c in nome):
            raise ValueError("nome de arquivo com caracteres não permitidos")
        if len(nome) > LIMITE_NOME:
            raise ValueError(f"nome de arquivo longo demais (máximo {LIMITE_NOME} caracteres)")
        if nome[-1] in ". " or nome.split(".", 1)[0].rstrip(" ").upper() in _RESERVADOS:
            raise ValueError("nome de arquivo não permitido no Windows")
        id_ = secrets.token_hex(8)
        with self._trava:
            if self._encerrado:
                raise RuntimeError("o programa está encerrando")
            pasta = self.pasta_tmp / id_
            pasta.mkdir(parents=True)
        caminho = pasta / nome
        try:
            with open(caminho, "wb") as f:
                for pedaco in pedacos:
                    f.write(pedaco)
        except OSError:
            shutil.rmtree(pasta, ignore_errors=True)
            raise ValueError("não foi possível gravar o arquivo") from None
        except BaseException:
            shutil.rmtree(pasta, ignore_errors=True)
            raise
        return self._registrar(Doc(id_, nome, "janela", caminho, pasta))

    def registrar_arquivo(self, caminho: Path, origem: str = "pasta") -> Doc:
        if origem not in ORIGENS:
            raise ValueError("origem inválida")
        caminho = Path(caminho)
        if self._encerrado:
            raise RuntimeError("o programa está encerrando")
        return self._registrar(Doc(secrets.token_hex(8), caminho.name, origem, caminho))

    def _registrar(self, doc: Doc) -> Doc:
        with self._trava:
            self._docs[doc.id] = doc
        self._log.info("documento %s registrado (origem %s)", doc.id, doc.origem)
        self.fila.enfileirar(lambda: self._ler_doc(doc))
        return doc

    def _ler_doc(self, doc: Doc) -> None:
        try:
            self._ler_doc_interno(doc)
        finally:
            if doc.descartado:
                self._apagar_tmp(doc)

    def _ler_doc_interno(self, doc: Doc) -> None:
        if doc.descartado:
            return
        try:
            documento = self._ler(doc.caminho)
            rev = Revisao(documento)
        except ErroDeLeitura as e:
            self._falhar(doc, str(e), "leitura recusada")
            return
        except Exception as e:  # noqa: BLE001
            self._log.error("documento %s: falha na leitura (%s)", doc.id, type(e).__name__)
            self._falhar(doc, "Não foi possível ler o documento. Veja o log do servidor.", None)
            return
        with self._trava:
            if doc.descartado:
                return
            doc.revisao, doc.avisos, doc.situacao = rev, list(documento.avisos), "revisao"
        self._log.info("documento %s lido: %d item(ns), %d aviso(s)", doc.id, len(rev.itens), len(doc.avisos))

    def _falhar(self, doc: Doc, mensagem: str, motivo: str | None) -> None:
        with self._trava:
            doc.erro = {"mensagem": mensagem, "valores": []}
            doc.situacao = "erro"
        if motivo:
            self._log.info("documento %s: %s", doc.id, motivo)

    # --- consulta ------------------------------------------------------------
    def obter(self, id_: str) -> Doc:
        with self._trava:
            try:
                return self._docs[id_]
            except KeyError:
                raise DocumentoInexistente(id_) from None

    def _resumo(self, d: Doc) -> dict:
        return {"id": d.id, "nome": d.nome, "origem": d.origem, "situacao": d.situacao,
                "avisos": len(d.avisos), "erro": d.erro["mensagem"] if d.erro else None,
                "revisavel": d.revisao is not None}

    def lista(self) -> list[dict]:
        with self._trava:
            return [self._resumo(d) for d in self._docs.values() if not d.descartado]

    def _item(self, d: Doc, it: Item) -> dict:
        return {"categoria": it.categoria, "valor": it.valor, "aceito": it.aceito, "acrescido": it.acrescido,
                "ocorrencias": len(it.ocorrencias),
                "contextos": [d.revisao.contexto(a, b) for a, b in it.ocorrencias[:3]]}

    def detalhe(self, id_: str) -> dict:
        with self._trava:
            return self._detalhe(self.obter(id_))

    def _detalhe(self, d: Doc) -> dict:
        r = self._resumo(d)
        r["avisos"] = list(d.avisos)
        r["itens"] = [self._item(d, it) for it in d.revisao.itens] if d.revisao else []
        r["erro"] = dict(d.erro) if d.erro else None
        r["resultado"] = None
        if d.resultado:
            r["resultado"] = {"saida_nome": Path(d.resultado["saida"]).name,
                              "mapa_nome": Path(d.resultado["mapa"]).name if d.resultado["mapa"] else None,
                              "avisos": list(d.resultado["avisos"])}
        return r

    # --- revisão -------------------------------------------------------------
    def _em_revisao(self, id_: str) -> Doc:
        """Chamar com a trava tomada: a checagem e a mudança andam juntas."""
        d = self.obter(id_)
        if d.revisao is None or d.situacao not in ("revisao", "erro"):
            raise RuntimeError("o documento não está em revisão (ou já está sendo gerado)")
        return d

    def decidir(self, id_: str, categoria: str, valor: str, aceito: bool) -> None:
        chave = (str(categoria), normalizar(str(valor)))
        with self._trava:
            d = self._em_revisao(id_)
            try:
                (d.revisao.aceitar if aceito else d.revisao.recusar)(chave)
            except KeyError:
                raise LookupError("item não encontrado") from None
        self._log.info("documento %s: %s (%s)", id_, "aceito" if aceito else "recusado", categoria)

    def acrescentar(self, id_: str, valor: str, categoria: str = "pessoa") -> dict:
        with self._trava:
            d = self._em_revisao(id_)
            if categoria not in CATEGORIAS:
                raise ValueError("categoria inválida")
            item = d.revisao.acrescentar(str(valor), categoria)     # ValueError se não está no documento
            self._log.info("documento %s: acrescido (%s, %d ocorrência(s))", id_, categoria, len(item.ocorrencias))
            return self._item(d, item)

    # --- geração -------------------------------------------------------------
    def pedir_geracao(self, id_: str, *, formato: str, tipo: str | None, modo: str,
                      pasta_saida: Path, pasta_mapas: Path) -> None:
        if formato not in FORMATOS or modo not in MODOS:
            raise ValueError("formato ou modo inválido")
        if formato == "texto" and tipo not in TIPOS:
            raise ValueError("no formato 'texto', escolha o tipo: docx ou pdf")
        with self._trava:
            d = self._em_revisao(id_)
            d.situacao, d.erro = "gerando", None
        self.fila.enfileirar(lambda: self._gerar_doc(d, formato, tipo, modo, Path(pasta_saida), Path(pasta_mapas)))

    def _gerar_doc(self, d: Doc, formato, tipo, modo, pasta_saida: Path, pasta_mapas: Path) -> None:
        if d.descartado:
            return
        try:
            with self._trava:
                resultado = d.revisao.fechar()
            g = self._gerar(d.revisao.documento, resultado, formato=formato, tipo=tipo, modo=modo,
                            pasta_saida=pasta_saida, pasta_mapas=pasta_mapas)
        except VazamentoDetectado as e:
            self._erro(d, str(e), list(e.valores))
            self._log.warning("documento %s: vazamento detectado (%d valor(es)); nada gerado", d.id, len(e.valores))
            return
        except (ValueError, OSError) as e:
            self._erro(d, str(e), [])
            self._log.warning("documento %s: geração recusada (%s)", d.id, type(e).__name__)
            return
        except Exception as e:  # noqa: BLE001
            self._erro(d, "Falha ao gerar. Veja o log do servidor.", [])
            self._log.error("documento %s: falha na geração (%s)", d.id, type(e).__name__)
            return
        with self._trava:
            descartado = d.descartado
            if not descartado:
                d.resultado = {"saida": str(g.saida), "mapa": str(g.mapa) if g.mapa else None,
                               "avisos": list(g.avisos)}
                d.situacao = "pronto"
        if descartado:                       # a saída pertence a um trabalho descartado
            for arq in (g.saida, g.mapa):
                if arq is not None:
                    try:
                        Path(arq).unlink(missing_ok=True)
                    except OSError:
                        self._log.warning("documento %s: não deu para apagar uma saída descartada", d.id)
            self._apagar_tmp(d)
            return
        self._log.info("documento %s: gerado (%s, %s, %d aviso(s))", d.id, formato, modo, len(g.avisos))
        self._apagar_tmp(d)
        if self.apos_gerar is not None:
            try:
                self.apos_gerar(d)
            except Exception as e:  # noqa: BLE001
                self._log.error("documento %s: pós-geração falhou (%s)", d.id, type(e).__name__)

    def _erro(self, d: Doc, mensagem: str, valores: list) -> None:
        with self._trava:
            d.erro, d.situacao = {"mensagem": mensagem, "valores": valores}, "erro"
        if d.descartado:
            self._apagar_tmp(d)

    # --- saída ---------------------------------------------------------------
    def descartar(self, id_: str) -> Doc:
        with self._trava:
            d = self._docs.pop(id_, None)
            if d is None:
                raise DocumentoInexistente(id_)
            d.descartado = True
        self._apagar_tmp(d)            # se a leitura segura o arquivo, _ler_doc apaga depois
        self._log.info("documento %s descartado", id_)
        return d

    def _apagar_tmp(self, d: Doc) -> None:
        if d.pasta_tmp is not None:
            self._apagar_pasta(d.pasta_tmp)

    def _apagar_pasta(self, pasta: Path) -> None:
        """Apaga; se não der (arquivo preso no Windows), fica na lista de
        pendentes, que o encerrar varre de novo."""
        try:
            if pasta.is_dir() and not pasta.is_symlink():
                shutil.rmtree(pasta)
            else:
                pasta.unlink(missing_ok=True)
        except OSError:
            pass
        with self._trava:
            if pasta.exists():
                self._tmp_pendentes.add(pasta)
            else:
                self._tmp_pendentes.discard(pasta)

    def ocupado(self) -> bool:
        with self._trava:
            em_curso = any(d.situacao in ("lendo", "gerando") for d in self._docs.values())
        return em_curso or self.fila.ocupada()

    def encerrar(self, timeout: float | None = None) -> bool:
        with self._trava:
            self._encerrado = True
        ok = self.fila.encerrar(timeout)
        with self._trava:
            docs = list(self._docs.values())
            pendentes = list(self._tmp_pendentes)
        for d in docs:
            self._apagar_tmp(d)
        for pasta in pendentes:
            self._apagar_pasta(pasta)
        return ok
