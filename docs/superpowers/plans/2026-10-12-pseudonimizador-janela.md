# Pseudonimizador — Plano 2: janela local, pasta monitorada, instância única, restaurar e lançador

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Janela do Pseudonimizador (servidor HTTP local + página própria aberta no Edge em modo aplicativo) com arrastar e soltar, revisão, geração, resultado, restauração de nomes e configurações; pasta monitorada `Entrada\` para lotes; instância única; `python -m pseudonimizador` sem subcomando e `Pseudonimizador.bat` abrem a janela.

**Architecture:** Um `ThreadingHTTPServer` da biblioteca padrão em `127.0.0.1`, porta livre, protegido por token de sessão (`X-Token`), conferência de `Host` e CSP. A página (HTML/CSS/JS próprios, sem nada externo) conversa só com `/api/...`. Um registro em memória guarda os documentos (`id` → situação, `Revisao`, resultado) e **uma única fila de trabalho** (uma thread) faz leitura/OCR e geração, chamando a biblioteca do Plano 1 (`leitura.ler`, `revisao.Revisao`, `saida.gerar`, `restaurar`). Uma thread varre a `Entrada\` a cada 2 s. O módulo `web/abrir.py` cuida do mutex nomeado, do `instancia.json`, do Edge e do erro sob `pythonw`.

**Tech Stack:** Python 3.14 (Windows), biblioteca padrão (`http.server`, `urllib`, `ctypes`, `winreg`), PyMuPDF 1.28.0, python-docx 1.2.0, RapidOCR 3.9.2 (via Plano 1). Sem framework web, sem pytest (runner próprio).

**Spec:** `docs/superpowers/specs/2026-10-11-pseudonimizador-design.md` (§8 janela e pasta monitorada; §9 segurança). Decisões vinculantes deste plano: servidor da biblioteca padrão em 127.0.0.1 porta 0; token no fragmento `#t=` e no cabeçalho `X-Token` (`hmac.compare_digest`); `Host` conferido; `Content-Security-Policy: default-src 'self'`; `X-Content-Type-Options: nosniff`; upload cru com `X-Nome-Arquivo` (sem multipart), limite 100 MB, só `.docx`/`.pdf`; uma fila de trabalho; pasta de estado `%LOCALAPPDATA%\Pseudonimizador` (ou `PSEUDONIMIZADOR_ESTADO`); mutex `Pseudonimizador-Servidor` + `instancia.json`; encerramento por menu ou 30 min ociosos; logs sem valores e sem nomes de arquivo.

## Global Constraints

- Repositório: `C:\Users\<usuário>\Claude\Pseudonimizador` (esta pasta). O Ulpiano fica na pasta irmã `../AplicativosMauricio` e **não é alterado** (só lido como referência de padrões; nunca ler `mapa_pseudonimos.json` nem nada do drive `E:`).
- Python do projeto: `.venv` criado com `py -3.14 -m venv .venv`. Todos os comandos usam `PY=.venv/Scripts/python` e `-X utf8`, por exemplo `$PY -X utf8 testes/test_x.py`.
- Dependências fixas: `pymupdf==1.28.0`, `python-docx==1.2.0`, `rapidocr==3.9.2`, `onnxruntime==1.24.4`. Nenhuma outra sem pedir. A janela usa só a biblioteca padrão.
- Licença: todo `.py` rastreado começa com estas duas linhas, exatamente:
  `# SPDX-License-Identifier: AGPL-3.0-only`
  `# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.`
  Os estáticos (`.html`, `.js`, `.css`) e o `.bat` não levam cabeçalho (regra do Plano 1: só `.py`).
- Autoria: o nome do autor aparece só em `CREDITOS.md` e `README.md`.
- Sem dado real: testes e docs usam só os dados sintéticos de `testes/fabrica.py`. Nenhum caminho da máquina (`C:\Users\<nome>`), nome de usuário ou e-mail pessoal em arquivo rastreado (`test_sem_dados_reais.py` varre docs também).
- Nenhuma conexão de rede além de `127.0.0.1`/`::1`/`localhost` em código ou teste. O servidor escuta só em `127.0.0.1`.
- Logs (`logs\servidor.log`) nunca levam valores do documento **nem nomes de arquivo** (o nome pode ser o de uma pessoa): só ids, categorias, contagens e tipos de exceção. Mensagens de erro mostradas na tela local podem citar o valor.
- Os testes nunca abrem navegador nem chamam `os.startfile`: o lançamento do Edge e a abertura no Windows são funções injetáveis, substituídas nos testes. O servidor dos testes sobe de verdade em porta 0 e é consultado com `urllib.request` (e `http.client` só onde é preciso mandar um cabeçalho sem corpo).
- Arquivo de teste que use porta fixa ou pasta compartilhada leva `# executar_todos: sozinho` nas 15 primeiras linhas (neste plano: `test_web_abrir.py`).
- Comentários, mensagens e commits em português. TDD: teste vermelho primeiro, pelo motivo certo.
- Scripts com barra invertida: escreva o arquivo com a ferramenta Write, não com heredoc no Bash.
- Nunca matar processo pelo nome (`taskkill /IM python.exe` derruba processo alheio): só o PID que o próprio teste iniciou, e de preferência por `/api/encerrar`.
- Um commit por tarefa, terminando com a linha `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Nunca `git push`.

## Review Focus

1. **Arquivo enorme (acima de 100 MB) ou de outro formato arrastado à janela**: resposta clara (413/415) antes de ler o corpo, nada gravado em `tmp\`. Teste em Task 4 (`test_upload_grande_ou_de_outro_formato_e_recusado`).
2. **Segunda abertura com o app já aberto** (clique duplo no atalho de novo): nova janela na instância viva com token novo, sem segundo servidor; instância de outra versão é substituída quando ociosa. Teste em Task 10 (`test_segunda_abertura_reaproveita_a_instancia`, `test_instancia_de_outra_versao_e_substituida`).
3. **Arquivo ainda sendo copiado para `Entrada\`**: só vira documento quando tamanho e mtime ficam iguais em duas varreduras seguidas; `~$`, ocultos e `Processados\` ignorados. Teste em Task 9 (`test_arquivo_so_entra_quando_estavel`).
4. **Geração que falha com `VazamentoDetectado`**: situação `erro` com a lista dos valores **só na tela**; nada no log; a revisão continua aberta e pode gerar de novo. Teste em Task 5 (`test_vazamento_vira_erro_na_tela_e_nao_no_log`).
5. **Fechar/encerrar no meio do OCR**: a fila termina o trabalho em curso (nunca o mata), descarta os pendentes, apaga `tmp\`; o servidor só sai quando ocioso. Testes em Task 2 (`test_encerrar_espera_a_leitura_em_curso`) e Task 3 (`test_encerrar_espera_o_trabalho_em_curso`).

---

## Estrutura de arquivos

```
pseudonimizador/
  __init__.py              VERSAO -> "0.2.0" (Task 10)
  __main__.py              sem subcomando abre a janela (Task 10)
  estado.py                pasta de estado, config.json, log (Task 1)
  leitura/ocr.py           trava em volta do RapidOCR (Task 2)
  web/
    __init__.py            (Task 2)
    registro.py            Fila (uma thread), Doc, Registro (Task 2)
    servidor.py            ErroDaApi, Aplicacao, Manipulador, Servidor, ROTAS (Task 3; rotas nas Tasks 4-7)
    pasta_monitorada.py    Vigia da Entrada\ (Task 9)
    abrir.py               Mutex, instancia.json, Edge, abrir(), principal() (Task 10)
    estatico/
      index.html app.css app.js   (Task 8)
Pseudonimizador.bat        (Task 10)
README.md                  seção "Uso pela janela" (Task 10)
testes/
  _web.py                  ServidorDeTeste (Task 3)
  test_estado.py           (Task 1)
  test_web_registro.py     (Task 2)
  test_web_servidor.py     (Task 3)
  test_web_documentos.py   (Task 4)
  test_web_gerar.py        (Task 5)
  test_web_restaurar.py    (Task 6)
  test_web_config.py       (Task 7)
  test_web_estaticos.py    (Task 8)
  test_pasta_monitorada.py (Task 9)
  test_web_abrir.py        (Task 10, sozinho)
  test_sem_rede.py         ganha o fluxo pela janela (Task 5)
  test_cli.py              ganha o teste do "sem subcomando" (Task 10)
```

Contrato da API (o que a página usa; detalhes em cada tarefa):

| Método e rota | Corpo / cabeçalhos | Resposta |
|---|---|---|
| `GET /api/estado` | — | `{versao, ocupado, pastas}` |
| `POST /api/encerrar` | — | `{ok}` (sai quando ocioso) |
| `POST /abrir`, `POST /encerrar` | `{segredo}` (outro processo local, sem token) | `{token}` / `{ok}` |
| `GET /api/config` · `POST /api/config` | `{pasta_base, pasta_saida, pasta_mapas, formato, tipo, modo}` | a config + `pastas` |
| `POST /api/documentos` | corpo cru + `X-Nome-Arquivo` (URL-encoded) | 202 `{id, nome, situacao}` |
| `GET /api/documentos` | — | `{documentos: [{id, nome, origem, situacao, avisos, erro, revisavel}]}` |
| `GET /api/documentos/{id}` | — | resumo + `avisos[]`, `itens[]`, `resultado`, `erro` |
| `POST .../{id}/decisao` | `{categoria, valor, aceito}` | `{ok}` |
| `POST .../{id}/acrescentar` | `{valor, categoria}` | `{ok, item}` |
| `POST .../{id}/gerar` | `{formato, tipo, modo}` (vazios = padrões da config) | 202 `{ok, situacao}` |
| `POST .../{id}/abrir` | `{alvo: "arquivo" \| "pasta"}` | `{ok}` |
| `DELETE /api/documentos/{id}` | — | `{ok}` |
| `GET /api/mapas` | — | `{mapas: [{id, data}]}` |
| `POST /api/restaurar/docx` | corpo cru + `X-Nome-Arquivo` (+ `X-Mapa` opcional) | `{ok, saida_nome, trocas}`; 409 `mapa` / `orfao` |
| `POST /api/restaurar/texto` | `{texto, mapa}` | `{texto}`; 409 `orfao` |

Erros sempre `{"erro": "<código>", "mensagem": "<frase em português>"}`. Situações de um documento: `lendo`, `revisao`, `gerando`, `pronto`, `erro`.

---

### Task 1: Pasta de estado, configuração e log

**Files:**
- Create: `pseudonimizador/estado.py`
- Test: `testes/test_estado.py`

**Interfaces:**
- Consumes: `pseudonimizador.motor.mapa.escrever_atomico(caminho: Path, texto: str) -> None`.
- Produces: `pasta_estado() -> Path`; `pasta_base_padrao() -> Path`; `Config` (dataclass: `pasta_base: str`, `pasta_saida: str = ""`, `pasta_mapas: str = ""`, `formato = "layout"`, `tipo = "docx"`, `modo = "reversivel"`; propriedades `entrada`, `processados`, `saida`, `mapas: Path`; `pastas() -> dict[str, str]`); `validar(dados: dict) -> Config` (ValueError); `carregar(pasta_estado: Path) -> Config`; `gravar(pasta_estado: Path, config: Config) -> None`; `preparar_pastas(config: Config) -> None`; `abrir_log(pasta_estado: Path) -> logging.Logger`; constantes `FORMATOS`, `TIPOS`, `MODOS`, `ARQUIVO_CONFIG`.

- [ ] **Step 1: Escrever o teste (vermelho)**

`testes/test_estado.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Pasta de estado, config.json e log do servidor."""
import _base  # noqa: F401
import json
import os
from pathlib import Path

import fabrica as F
from pseudonimizador import estado
from pseudonimizador.estado import Config, abrir_log, carregar, gravar, preparar_pastas, validar


def test_pasta_estado_pela_variavel_de_ambiente():
    pasta = F.pasta_temporaria("estado_env")
    os.environ["PSEUDONIMIZADOR_ESTADO"] = str(pasta)
    try:
        assert estado.pasta_estado() == pasta
    finally:
        del os.environ["PSEUDONIMIZADOR_ESTADO"]
    padrao = estado.pasta_estado()
    assert padrao.name == "Pseudonimizador" and padrao.is_absolute()


def test_config_padrao_gravar_carregar_e_pastas():
    pasta = F.pasta_temporaria("estado_cfg")
    cfg = carregar(pasta)
    assert cfg == Config(pasta_base=str(estado.pasta_base_padrao()))
    nova = Config(pasta_base=str(pasta / "Base"), formato="texto", tipo="pdf", modo="definitivo")
    gravar(pasta, nova)
    assert json.loads((pasta / "config.json").read_text(encoding="utf-8"))["modo"] == "definitivo"
    assert carregar(pasta) == nova
    preparar_pastas(nova)
    for sub in ("Entrada", "Entrada/Processados", "Saida", "Mapas"):
        assert (pasta / "Base" / sub).is_dir()
    assert nova.pastas() == {"entrada": str(pasta / "Base" / "Entrada"), "saida": str(pasta / "Base" / "Saida"),
                             "mapas": str(pasta / "Base" / "Mapas"),
                             "processados": str(pasta / "Base" / "Entrada" / "Processados")}


def test_validar_recusa_o_que_a_tela_nao_pode_gravar():
    base = str(Path(F.pasta_temporaria("estado_val")) / "Base")
    assert validar({"pasta_base": base}).modo == "reversivel"
    casos = [
        ({}, "pasta base"),
        ({"pasta_base": "Base"}, "caminho completo"),
        ({"pasta_base": base, "modo": "talvez"}, "modo"),
        ({"pasta_base": base, "formato": "foto"}, "formato"),
        ({"pasta_base": base, "tipo": "txt"}, "tipo"),
        ({"pasta_base": base, "pasta_mapas": base + "\\Saida\\M"}, "mapas"),
        ({"pasta_base": base, "pasta_saida": base + "\\Mapas"}, "mapas"),
        ({"pasta_base": base, "pasta_saida": base + "\\Entrada"}, "Entrada"),
        ({"pasta_base": base, "pasta_saida": "Saida"}, "caminho completo"),
    ]
    for dados, trecho in casos:
        try:
            validar(dados)
        except ValueError as e:
            assert trecho in str(e), (dados, str(e))
        else:
            raise AssertionError(f"deveria recusar {dados}")


def test_config_ilegivel_vira_bak_e_volta_ao_padrao():
    pasta = F.pasta_temporaria("estado_bak")
    (pasta / "config.json").write_text("{{{", encoding="utf-8")
    assert carregar(pasta).pasta_base == str(estado.pasta_base_padrao())
    assert (pasta / "config.json.bak").is_file() and not (pasta / "config.json").exists()


def test_log_grava_na_pasta_de_estado():
    pasta = F.pasta_temporaria("estado_log")
    log = abrir_log(pasta)
    log.info("evento %d", 7)
    for h in list(log.handlers):
        h.close()
    texto = (pasta / "logs" / "servidor.log").read_text(encoding="utf-8")
    assert "evento 7" in texto and "INFO" in texto


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `$PY -X utf8 testes/test_estado.py`
Expected: FALHA em todos, `ModuleNotFoundError: No module named 'pseudonimizador.estado'`.

- [ ] **Step 3: Implementar `pseudonimizador/estado.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Pasta de estado do aplicativo (%LOCALAPPDATA%\\Pseudonimizador, ou a
variável PSEUDONIMIZADOR_ESTADO), a configuração (config.json) e o log do
servidor. Nada aqui lê ou grava conteúdo de documento."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .motor.mapa import escrever_atomico

ARQUIVO_CONFIG = "config.json"
FORMATOS = ("layout", "texto")
TIPOS = ("docx", "pdf")
MODOS = ("reversivel", "definitivo")


def pasta_estado() -> Path:
    env = os.environ.get("PSEUDONIMIZADOR_ESTADO")
    if env:
        return Path(env)
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "Pseudonimizador"


def pasta_base_padrao() -> Path:
    return Path(os.environ.get("USERPROFILE") or Path.home()) / "Documents" / "Pseudonimizador"


@dataclass
class Config:
    pasta_base: str
    pasta_saida: str = ""        # vazio: <pasta_base>\Saida
    pasta_mapas: str = ""        # vazio: <pasta_base>\Mapas
    formato: str = "layout"      # padrões do lote (pasta Entrada)
    tipo: str = "docx"           # só para formato "texto"
    modo: str = "reversivel"

    @property
    def entrada(self) -> Path:
        return Path(self.pasta_base) / "Entrada"

    @property
    def processados(self) -> Path:
        return self.entrada / "Processados"

    @property
    def saida(self) -> Path:
        return Path(self.pasta_saida) if self.pasta_saida else Path(self.pasta_base) / "Saida"

    @property
    def mapas(self) -> Path:
        return Path(self.pasta_mapas) if self.pasta_mapas else Path(self.pasta_base) / "Mapas"

    def pastas(self) -> dict[str, str]:
        return {"entrada": str(self.entrada), "saida": str(self.saida), "mapas": str(self.mapas),
                "processados": str(self.processados)}


def validar(dados: dict) -> Config:
    """Config a partir de um dicionário (o JSON do disco ou o corpo da tela).
    ValueError com a frase para o usuário. As regras que o `gerar` já aplica
    (mapas nunca na saída nem dentro dela, e vice-versa) são recusadas aqui,
    antes de gravar."""
    if not isinstance(dados, dict):
        raise ValueError("configuração inválida")
    base = str(dados.get("pasta_base") or "").strip()
    if not base:
        raise ValueError("informe a pasta base")
    if not Path(base).is_absolute():
        raise ValueError("pasta base: informe o caminho completo")
    cfg = Config(pasta_base=base,
                 pasta_saida=str(dados.get("pasta_saida") or "").strip(),
                 pasta_mapas=str(dados.get("pasta_mapas") or "").strip(),
                 formato=str(dados.get("formato") or "layout"),
                 tipo=str(dados.get("tipo") or "docx"),
                 modo=str(dados.get("modo") or "reversivel"))
    for campo, aceitos in (("formato", FORMATOS), ("tipo", TIPOS), ("modo", MODOS)):
        if getattr(cfg, campo) not in aceitos:
            raise ValueError(f"{campo} inválido: escolha entre {', '.join(aceitos)}")
    for campo, rotulo in (("pasta_saida", "pasta de saída"), ("pasta_mapas", "pasta dos mapas")):
        valor = getattr(cfg, campo)
        if valor and not Path(valor).is_absolute():
            raise ValueError(f"{rotulo}: informe o caminho completo")
    s, m, e = cfg.saida.resolve(), cfg.mapas.resolve(), cfg.entrada.resolve()
    if s == m or s in m.parents or m in s.parents:
        raise ValueError("a pasta dos mapas não pode ser a da saída nem ficar dentro dela (ou vice-versa)")
    if e in (s, m):
        raise ValueError("a saída e os mapas não podem ser a pasta Entrada")
    return cfg


def carregar(pasta_estado: Path) -> Config:
    """A config gravada; sem arquivo, a padrão. Arquivo ilegível vira
    config.json.bak (nada bloqueia a abertura) e volta-se à padrão."""
    arquivo = Path(pasta_estado) / ARQUIVO_CONFIG
    padrao = Config(pasta_base=str(pasta_base_padrao()))
    if not arquivo.is_file():
        return padrao
    try:
        return validar(json.loads(arquivo.read_text(encoding="utf-8")))
    except (ValueError, OSError):
        try:
            os.replace(arquivo, arquivo.with_suffix(".json.bak"))
        except OSError:
            pass
        return padrao


def gravar(pasta_estado: Path, config: Config) -> None:
    escrever_atomico(Path(pasta_estado) / ARQUIVO_CONFIG, json.dumps(asdict(config), ensure_ascii=False, indent=1))


def preparar_pastas(config: Config) -> None:
    for pasta in (config.entrada, config.processados, config.saida, config.mapas):
        pasta.mkdir(parents=True, exist_ok=True)


def abrir_log(pasta_estado: Path) -> logging.Logger:
    """Logger próprio (não o do registro global: cada Aplicacao tem o seu e o
    fecha ao encerrar). Quem escreve nele nunca passa valor nem nome de arquivo."""
    pasta = Path(pasta_estado) / "logs"
    pasta.mkdir(parents=True, exist_ok=True)
    log = logging.Logger("pseudonimizador.servidor", logging.INFO)
    h = logging.FileHandler(pasta / "servidor.log", encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(h)
    return log
```

- [ ] **Step 4: Rodar e ver passar**

Run: `$PY -X utf8 testes/test_estado.py`
Expected: `5/5 passaram`.

- [ ] **Step 5: Commit**

```bash
git add pseudonimizador/estado.py testes/test_estado.py
git commit -m "Pasta de estado, config.json validado e log do servidor

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Registro de documentos e fila única de trabalho (+ trava do OCR)

**Files:**
- Create: `pseudonimizador/web/__init__.py`, `pseudonimizador/web/registro.py`
- Modify: `pseudonimizador/leitura/ocr.py` (trava em volta do RapidOCR)
- Test: `testes/test_web_registro.py`

**Interfaces:**
- Consumes: `leitura.ler(caminho) -> Documento` (`.texto`, `.avisos`, `.caminho`), `leitura.ErroDeLeitura`; `revisao.Revisao(documento)` (`.itens: list[Item]`, `.aceitar(chave)`, `.recusar(chave)`, `.acrescentar(valor, categoria) -> Item`, `.contexto(ini, fim) -> str`, `.fechar() -> Resultado`, `.documento`), `revisao.PREFIXOS`; `motor.mapa.normalizar`; `saida.gerar(documento, resultado, *, formato, modo, pasta_saida, pasta_mapas, tipo=None) -> Gerado(saida, mapa, avisos)`, `saida.VazamentoDetectado` (`.valores`); `estado.FORMATOS/TIPOS/MODOS`.
- Produces: `Fila(log)` (`enfileirar(fn)`, `ocupada() -> bool`, `encerrar(timeout=None) -> bool`); `Doc` (dataclass: `id, nome, origem, caminho, pasta_tmp, situacao, revisao, avisos, resultado, erro, descartado`); `Registro(pasta_tmp, log, *, fila=None, ler=..., gerar=..., apos_gerar=None)` com `registrar_upload(nome, pedacos) -> Doc`, `registrar_arquivo(caminho, origem="pasta") -> Doc`, `obter(id) -> Doc` (KeyError), `lista() -> list[dict]`, `detalhe(id) -> dict`, `decidir(id, categoria, valor, aceito)` (LookupError se o item não existe; RuntimeError fora da revisão), `acrescentar(id, valor, categoria) -> dict` (ValueError), `pedir_geracao(id, *, formato, tipo, modo, pasta_saida, pasta_mapas)`, `descartar(id) -> Doc`, `ocupado() -> bool`, `encerrar(timeout=None) -> bool`, atributo `apos_gerar: Callable[[Doc], None] | None`; constantes `SITUACOES`, `CATEGORIAS`, `ORIGENS`.

- [ ] **Step 1: Escrever o teste (vermelho)**

`testes/test_web_registro.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Registro em memória dos documentos e a fila única de trabalho."""
import _base  # noqa: F401
import threading
import time

import fabrica as F
from pseudonimizador.estado import abrir_log
from pseudonimizador.leitura import ler
from pseudonimizador.web.registro import Fila, Registro


def _esperar(condicao, prazo=60.0):
    fim = time.monotonic() + prazo
    while not condicao():
        assert time.monotonic() < fim, "esperou demais"
        time.sleep(0.05)


def test_fila_um_trabalho_de_cada_vez_e_encerrar_descarta_os_pendentes():
    pasta = F.pasta_temporaria("registro_fila")
    fila = Fila(abrir_log(pasta))
    marcas = []

    def trabalho(n):
        def f():
            marcas.append(f"ini{n}")
            time.sleep(0.2)
            marcas.append(f"fim{n}")
        return f
    fila.enfileirar(trabalho(1))
    fila.enfileirar(trabalho(2))
    assert fila.ocupada()
    _esperar(lambda: len(marcas) == 4)
    assert marcas == ["ini1", "fim1", "ini2", "fim2"] and not fila.ocupada()
    marcas.clear()
    fila.enfileirar(trabalho(3))
    fila.enfileirar(trabalho(4))
    _esperar(lambda: "ini3" in marcas)
    assert fila.encerrar(timeout=5)
    assert marcas == ["ini3", "fim3"] and not fila.ocupada()


def test_registrar_upload_ler_decidir_acrescentar_gerar():
    pasta = F.pasta_temporaria("registro_fluxo")
    reg = Registro(pasta / "tmp", abrir_log(pasta))
    original = F.contrato_docx(pasta / "contrato.docx").read_bytes()
    doc = reg.registrar_upload("contrato.docx", [original[:100], original[100:]])
    assert doc.situacao == "lendo" and doc.origem == "janela" and (pasta / "tmp" / doc.id / "contrato.docx").is_file()
    _esperar(lambda: doc.situacao != "lendo")
    assert doc.situacao == "revisao", doc.erro
    d = reg.detalhe(doc.id)
    assert d["revisavel"] and {it["valor"] for it in d["itens"]} >= {F.PESSOA_1, F.CPF, F.EMAIL}
    item = next(it for it in d["itens"] if it["valor"] == F.EMAIL)
    assert item["aceito"] and item["ocorrencias"] >= 1 and 1 <= len(item["contextos"]) <= 3
    reg.decidir(doc.id, "email", F.EMAIL, False)
    assert not next(it for it in reg.detalhe(doc.id)["itens"] if it["valor"] == F.EMAIL)["aceito"]
    extra = reg.acrescentar(doc.id, "Porto Alegre", "outro")
    assert extra["acrescido"] and extra["ocorrencias"] == 1
    try:
        reg.acrescentar(doc.id, "texto que não está no documento", "outro")
    except ValueError:
        pass
    else:
        raise AssertionError("acrescentar o que não existe deveria falhar")
    try:
        reg.decidir(doc.id, "pessoa", "Ninguém Assim", True)
    except LookupError:
        pass
    else:
        raise AssertionError("decisão sobre item inexistente deveria falhar")
    reg.pedir_geracao(doc.id, formato="layout", tipo=None, modo="reversivel",
                      pasta_saida=pasta / "Saida", pasta_mapas=pasta / "Mapas")
    assert doc.situacao == "gerando"
    _esperar(lambda: doc.situacao != "gerando")
    assert doc.situacao == "pronto", doc.erro
    r = reg.detalhe(doc.id)["resultado"]
    assert r["saida_nome"] == "contrato - pseudonimizado.docx" and r["mapa_nome"].endswith(".json")
    texto = ler(pasta / "Saida" / r["saida_nome"]).texto
    assert F.EMAIL in texto and "Porto Alegre" not in texto and F.PESSOA_1 not in texto
    assert not (pasta / "tmp" / doc.id).exists()        # o tmp vai embora depois de gerar
    assert [x["id"] for x in reg.lista()] == [doc.id]
    reg.descartar(doc.id)
    assert reg.lista() == []
    assert reg.encerrar(timeout=5)


def test_erro_de_leitura_vira_situacao_erro_sem_revisao():
    pasta = F.pasta_temporaria("registro_erro")
    reg = Registro(pasta / "tmp", abrir_log(pasta))
    doc = reg.registrar_upload("x.docx", [b"isto nao e um docx"])
    _esperar(lambda: doc.situacao != "lendo")
    assert doc.situacao == "erro" and doc.erro["mensagem"] and doc.erro["valores"] == []
    assert not reg.detalhe(doc.id)["revisavel"] and reg.detalhe(doc.id)["itens"] == []
    for nome in ("notas.txt", "", "..", "sub\\..\\x.exe"):
        try:
            reg.registrar_upload(nome, [b"a"])
        except ValueError:
            pass
        else:
            raise AssertionError(f"deveria recusar {nome!r}")
    try:
        reg.pedir_geracao(doc.id, formato="layout", tipo=None, modo="definitivo",
                          pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    except RuntimeError:
        pass
    else:
        raise AssertionError("gerar sem revisão deveria falhar")
    assert reg.encerrar(timeout=5)


def test_descartar_durante_a_leitura_apaga_o_tmp_depois():
    pasta = F.pasta_temporaria("registro_descartar")
    comecou = threading.Event()

    def ler_lento(caminho):
        comecou.set()
        time.sleep(0.5)
        return ler(caminho)
    reg = Registro(pasta / "tmp", abrir_log(pasta), ler=ler_lento)
    doc = reg.registrar_upload("contrato.docx", [F.contrato_docx(pasta / "c.docx").read_bytes()])
    assert comecou.wait(10)
    reg.descartar(doc.id)
    assert reg.lista() == []
    _esperar(lambda: not reg.fila.ocupada())
    _esperar(lambda: not (pasta / "tmp" / doc.id).exists(), prazo=5)
    assert reg.encerrar(timeout=5)


def test_encerrar_espera_a_leitura_em_curso():
    """Fechar no meio do OCR: o trabalho em curso termina (nunca é morto),
    os pendentes são descartados e o tmp some."""
    pasta = F.pasta_temporaria("registro_encerrar")
    marcas = []

    def ler_lento(caminho):
        marcas.append("ini")
        time.sleep(0.5)
        marcas.append("fim")
        return ler(caminho)
    reg = Registro(pasta / "tmp", abrir_log(pasta), ler=ler_lento)
    corpo = F.contrato_docx(pasta / "c.docx").read_bytes()
    a = reg.registrar_upload("a.docx", [corpo])
    b = reg.registrar_upload("b.docx", [corpo])
    _esperar(lambda: "ini" in marcas)
    assert reg.encerrar(timeout=10)
    assert marcas == ["ini", "fim"] and a.situacao == "revisao" and b.situacao == "lendo"
    assert not (pasta / "tmp" / a.id).exists() and not (pasta / "tmp" / b.id).exists()


def test_ocr_serializado_pela_trava():
    import fitz
    from pseudonimizador.leitura import ocr
    assert isinstance(ocr._TRAVA, type(threading.Lock()))

    class MotorFalso:
        def __call__(self, imagem):
            assert ocr._TRAVA.locked(), "o OCR rodou fora da trava"
            return None
    original = ocr._motor
    ocr._motor = lambda: MotorFalso()
    try:
        doc = fitz.open()
        pagina = doc.new_page(width=50, height=50)
        pix = pagina.get_pixmap(colorspace=fitz.csRGB, alpha=False)
        assert ocr.ocr_pixmap(pix) == []
        assert ocr.ocr_pagina(pagina) == []
    finally:
        ocr._motor = original


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `$PY -X utf8 testes/test_web_registro.py`
Expected: `ModuleNotFoundError: No module named 'pseudonimizador.web'`.

- [ ] **Step 3: Trava no OCR**

Em `pseudonimizador/leitura/ocr.py`, logo após `import numpy as np`:
```python
import threading

_TRAVA = threading.Lock()   # o RapidOCR não é thread-safe: uma leitura por vez
```
E troque as duas chamadas `resultado = _motor()(imagem)` por:
```python
    with _TRAVA:
        resultado = _motor()(imagem)
```

- [ ] **Step 4: Implementar o registro**

`pseudonimizador/web/__init__.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Janela do Pseudonimizador: servidor local, registro de documentos, pasta
monitorada e abertura (instância única, Edge em modo aplicativo)."""
```

`pseudonimizador/web/registro.py`:
```python
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
        self._trava = threading.Lock()

    # --- entrada -------------------------------------------------------------
    def registrar_upload(self, nome: str, pedacos: Iterable[bytes]) -> Doc:
        nome = Path(str(nome).replace("\\", "/")).name
        if not nome or nome in (".", "..") or Path(nome).suffix.lower() not in ACEITOS:
            raise ValueError("só arquivos .docx ou .pdf")
        id_ = secrets.token_hex(8)
        pasta = self.pasta_tmp / id_
        pasta.mkdir(parents=True)
        caminho = pasta / nome
        try:
            with open(caminho, "wb") as f:
                for pedaco in pedacos:
                    f.write(pedaco)
        except BaseException:
            shutil.rmtree(pasta, ignore_errors=True)
            raise
        return self._registrar(Doc(id_, nome, "janela", caminho, pasta))

    def registrar_arquivo(self, caminho: Path, origem: str = "pasta") -> Doc:
        if origem not in ORIGENS:
            raise ValueError("origem inválida")
        caminho = Path(caminho)
        return self._registrar(Doc(secrets.token_hex(8), caminho.name, origem, caminho))

    def _registrar(self, doc: Doc) -> Doc:
        with self._trava:
            self._docs[doc.id] = doc
        self._log.info("documento %s registrado (origem %s)", doc.id, doc.origem)
        self.fila.enfileirar(lambda: self._ler_doc(doc))
        return doc

    def _ler_doc(self, doc: Doc) -> None:
        if doc.descartado:
            self._apagar_tmp(doc)
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
        if doc.descartado:
            self._apagar_tmp(doc)
            return
        doc.revisao, doc.avisos, doc.situacao = rev, list(documento.avisos), "revisao"
        self._log.info("documento %s lido: %d item(ns), %d aviso(s)", doc.id, len(rev.itens), len(doc.avisos))

    def _falhar(self, doc: Doc, mensagem: str, motivo: str | None) -> None:
        doc.erro = {"mensagem": mensagem, "valores": []}
        doc.situacao = "erro"
        if motivo:
            self._log.info("documento %s: %s", doc.id, motivo)

    # --- consulta ------------------------------------------------------------
    def obter(self, id_: str) -> Doc:
        with self._trava:
            return self._docs[id_]

    def _resumo(self, d: Doc) -> dict:
        return {"id": d.id, "nome": d.nome, "origem": d.origem, "situacao": d.situacao,
                "avisos": len(d.avisos), "erro": d.erro["mensagem"] if d.erro else None,
                "revisavel": d.revisao is not None}

    def lista(self) -> list[dict]:
        with self._trava:
            docs = [d for d in self._docs.values() if not d.descartado]
        return [self._resumo(d) for d in docs]

    def _item(self, d: Doc, it: Item) -> dict:
        return {"categoria": it.categoria, "valor": it.valor, "aceito": it.aceito, "acrescido": it.acrescido,
                "ocorrencias": len(it.ocorrencias),
                "contextos": [d.revisao.contexto(a, b) for a, b in it.ocorrencias[:3]]}

    def detalhe(self, id_: str) -> dict:
        d = self.obter(id_)
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
        d = self.obter(id_)
        if d.revisao is None or d.situacao not in ("revisao", "erro"):
            raise RuntimeError("o documento não está em revisão")
        return d

    def decidir(self, id_: str, categoria: str, valor: str, aceito: bool) -> None:
        d = self._em_revisao(id_)
        chave = (str(categoria), normalizar(str(valor)))
        try:
            (d.revisao.aceitar if aceito else d.revisao.recusar)(chave)
        except KeyError:
            raise LookupError("item não encontrado") from None
        self._log.info("documento %s: %s (%s)", id_, "aceito" if aceito else "recusado", categoria)

    def acrescentar(self, id_: str, valor: str, categoria: str = "pessoa") -> dict:
        d = self._em_revisao(id_)
        if categoria not in CATEGORIAS:
            raise ValueError("categoria inválida")
        item = d.revisao.acrescentar(str(valor), categoria)     # ValueError se não está no documento
        self._log.info("documento %s: acrescido (%s, %d ocorrência(s))", id_, categoria, len(item.ocorrencias))
        return self._item(d, item)

    # --- geração -------------------------------------------------------------
    def pedir_geracao(self, id_: str, *, formato: str, tipo: str | None, modo: str,
                      pasta_saida: Path, pasta_mapas: Path) -> None:
        d = self._em_revisao(id_)
        if formato not in FORMATOS or modo not in MODOS:
            raise ValueError("formato ou modo inválido")
        if formato == "texto" and tipo not in TIPOS:
            raise ValueError("no formato 'texto', escolha o tipo: docx ou pdf")
        d.situacao, d.erro = "gerando", None
        self.fila.enfileirar(lambda: self._gerar_doc(d, formato, tipo, modo, Path(pasta_saida), Path(pasta_mapas)))

    def _gerar_doc(self, d: Doc, formato, tipo, modo, pasta_saida: Path, pasta_mapas: Path) -> None:
        if d.descartado:
            return
        try:
            g = self._gerar(d.revisao.documento, d.revisao.fechar(), formato=formato, tipo=tipo, modo=modo,
                            pasta_saida=pasta_saida, pasta_mapas=pasta_mapas)
        except VazamentoDetectado as e:
            d.erro, d.situacao = {"mensagem": str(e), "valores": list(e.valores)}, "erro"
            self._log.warning("documento %s: vazamento detectado (%d valor(es)); nada gerado", d.id, len(e.valores))
            return
        except (ValueError, OSError) as e:
            d.erro, d.situacao = {"mensagem": str(e), "valores": []}, "erro"
            self._log.warning("documento %s: geração recusada (%s)", d.id, type(e).__name__)
            return
        except Exception as e:  # noqa: BLE001
            d.erro, d.situacao = {"mensagem": "Falha ao gerar. Veja o log do servidor.", "valores": []}, "erro"
            self._log.error("documento %s: falha na geração (%s)", d.id, type(e).__name__)
            return
        d.resultado = {"saida": str(g.saida), "mapa": str(g.mapa) if g.mapa else None, "avisos": list(g.avisos)}
        d.situacao = "pronto"
        self._log.info("documento %s: gerado (%s, %s, %d aviso(s))", d.id, formato, modo, len(g.avisos))
        self._apagar_tmp(d)
        if self.apos_gerar is not None:
            try:
                self.apos_gerar(d)
            except Exception as e:  # noqa: BLE001
                self._log.error("documento %s: pós-geração falhou (%s)", d.id, type(e).__name__)

    # --- saída ---------------------------------------------------------------
    def descartar(self, id_: str) -> Doc:
        with self._trava:
            d = self._docs.pop(id_)
        d.descartado = True
        self._apagar_tmp(d)            # se a leitura segura o arquivo, _ler_doc apaga depois
        self._log.info("documento %s descartado", id_)
        return d

    def _apagar_tmp(self, d: Doc) -> None:
        if d.pasta_tmp is not None:
            shutil.rmtree(d.pasta_tmp, ignore_errors=True)

    def ocupado(self) -> bool:
        with self._trava:
            em_curso = any(d.situacao in ("lendo", "gerando") for d in self._docs.values())
        return em_curso or self.fila.ocupada()

    def encerrar(self, timeout: float | None = None) -> bool:
        ok = self.fila.encerrar(timeout)
        with self._trava:
            docs = list(self._docs.values())
        for d in docs:
            self._apagar_tmp(d)
        return ok
```

- [ ] **Step 5: Rodar e ver passar**

Run: `$PY -X utf8 testes/test_web_registro.py && $PY -X utf8 testes/test_leitura_ocr.py`
Expected: `6/6 passaram`; o teste do OCR continua verde.

- [ ] **Step 6: Commit**

```bash
git add pseudonimizador/web/__init__.py pseudonimizador/web/registro.py pseudonimizador/leitura/ocr.py testes/test_web_registro.py
git commit -m "Janela: registro de documentos e fila única de trabalho; trava no OCR

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---
### Task 3: Servidor HTTP local (token, Host, CSP, estáticos, estado, encerramento) e helper de teste

**Files:**
- Create: `pseudonimizador/web/servidor.py`, `testes/_web.py`
- Test: `testes/test_web_servidor.py`

**Interfaces:**
- Consumes: `estado.Config`, `estado.carregar/gravar/preparar_pastas/validar/abrir_log`; `web.registro.Registro`; `pseudonimizador.VERSAO`.
- Produces: `ErroDaApi(status, erro, mensagem, **extra)`; `Aplicacao(pasta_estado, *, config=None, inatividade_s=1800.0, abrir_no_windows=None, ler=None, gerar=None)` com `porta`, `segredo`, `config`, `registro`, `log`, `servidor`, `emitir_token() -> str`, `token_valido(t) -> bool`, `hosts() -> set[str]`, `batimento()`, `deve_encerrar() -> bool`, `pedir_encerramento()`, `aplicar_config(nova)`, `encerrar()`, `abrir_no_windows(caminho)`; `Manipulador` (com `_tratadores()` que as Tasks 4, 6 e 7 estendem; `_corpo_json(limite)`, `_corpo_bruto(limite) -> (tamanho, iterador)`, `_json(status, dados)`); `Servidor(app, porta=0)` (`vigiar(intervalo_s=2.0)`, `url(token)`, `encerrado`); constantes `ROTAS` (lista de `(metodo, regex)`), `ESTATICOS`, `PASTA_ESTATICO`, `LIMITE_JSON`, `LIMITE_ARQUIVO`, `RE_ID`, `CABECALHOS`.
- `testes/_web.py`: `ServidorDeTeste(nome, *, inatividade_s=1800.0, vigia_s=0.2, **kw_aplicacao)` (contexto; `pasta`, `app`, `servidor`, `porta`, `token`; `pedir(metodo, caminho, corpo=None, cabecalhos=None, token=True, host=None) -> (status, dados)`; `get`, `post`, `delete`, `enviar_arquivo(caminho, rota="/api/documentos", nome=None, cabecalhos=None)`, `esperar(id, *situacoes, prazo=90.0) -> dict`, `log_texto() -> str`).

- [ ] **Step 1: Escrever o helper e o teste (vermelho)**

`testes/_web.py`:
```python
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
```

`testes/test_web_servidor.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Servidor local: token, Host, cabeçalhos de segurança, estáticos, estado,
abertura por segredo e encerramento."""
import _base  # noqa: F401
import time
import urllib.request

from _web import ServidorDeTeste
from pseudonimizador import VERSAO


def test_estado_exige_token_e_host_certos():
    with ServidorDeTeste("web_srv") as s:
        status, r = s.get("/api/estado")
        assert status == 200 and r["versao"] == VERSAO and r["ocupado"] is False and r["pastas"]["entrada"].endswith("Entrada")
        assert s.get("/api/estado", token=False)[0] == 403
        assert s.get("/api/estado", token="x" * 43)[0] == 403
        status, r = s.get("/api/estado", host=f"exemplo.com.br:{s.porta}")
        assert status == 403 and r["erro"] == "host"
        assert s.get("/api/estado", host=f"localhost:{s.porta}")[0] == 200
        assert s.get("/api/nao_existe")[0] == 404
        assert s.pedir("PUT", "/api/estado")[0] == 405
        req = urllib.request.Request(f"http://127.0.0.1:{s.porta}/api/estado", headers={"X-Token": s.token})
        with urllib.request.urlopen(req, timeout=10) as resp:
            assert resp.headers["Content-Security-Policy"] == "default-src 'self'"
            assert resp.headers["X-Content-Type-Options"] == "nosniff"
            assert resp.headers["Cache-Control"] == "no-store"
            assert "Access-Control-Allow-Origin" not in resp.headers


def test_estaticos_so_da_lista_fechada():
    with ServidorDeTeste("web_srv2") as s:
        assert s.get("/estatico/outro.js", token=False)[0] == 404
        assert s.get("/estatico/../servidor.py", token=False)[0] == 404
        assert s.get("/qualquer", token=False)[0] == 404
        status, corpo = s.get("/estatico/app.js", token=False)
        assert status in (200, 404)           # o arquivo chega na Task 8; aqui só a lista fechada


def test_abrir_com_segredo_emite_token_novo():
    with ServidorDeTeste("web_srv3") as s:
        status, r = s.post("/abrir", {"segredo": "errado"}, token=False)
        assert status == 403
        status, r = s.post("/abrir", {"segredo": s.app.segredo}, token=False)
        assert status == 200 and r["token"] and r["token"] != s.token
        assert s.get("/api/estado", token=r["token"])[0] == 200
        assert s.post("/abrir", b"nao e json", token=False)[0] == 400


def test_encerrar_espera_o_trabalho_em_curso():
    with ServidorDeTeste("web_srv4", vigia_s=0.1) as s:
        marcas = []

        def lento():
            marcas.append("ini")
            time.sleep(0.8)
            marcas.append("fim")
        s.app.registro.fila.enfileirar(lento)
        time.sleep(0.1)
        status, r = s.post("/api/encerrar")
        assert status == 200 and r["ok"]
        time.sleep(0.3)
        assert s.thread.is_alive() and marcas == ["ini"]      # ocupado: ainda não saiu
        s.thread.join(5)
        assert not s.thread.is_alive() and marcas == ["ini", "fim"] and s.servidor.encerrado


def test_encerrar_por_segredo_e_por_inatividade():
    with ServidorDeTeste("web_srv5", vigia_s=0.1) as s:
        assert s.post("/encerrar", {"segredo": "errado"}, token=False)[0] == 403
        status, r = s.post("/encerrar", {"segredo": s.app.segredo}, token=False)
        assert status == 200 and r["ok"]
        s.thread.join(5)
        assert not s.thread.is_alive()
    with ServidorDeTeste("web_srv6", inatividade_s=0.3, vigia_s=0.1) as s:
        s.thread.join(5)
        assert not s.thread.is_alive() and s.servidor.encerrado
    assert "inatividade" in s.log_texto()


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `$PY -X utf8 testes/test_web_servidor.py`
Expected: `ModuleNotFoundError: No module named 'pseudonimizador.web.servidor'`.

- [ ] **Step 3: Implementar `pseudonimizador/web/servidor.py`**

```python
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
```

- [ ] **Step 4: Rodar e ver passar**

Run: `$PY -X utf8 testes/test_web_servidor.py`
Expected: `5/5 passaram`.

- [ ] **Step 5: Commit**

```bash
git add pseudonimizador/web/servidor.py testes/_web.py testes/test_web_servidor.py
git commit -m "Janela: servidor local com token, Host, CSP, estáticos e encerramento

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---
### Task 4: API de documentos (upload cru, lista, detalhe, decisão, acrescentar, descartar)

**Files:**
- Modify: `pseudonimizador/web/servidor.py` (`ROTAS`, `_tratadores`, novo `_api_documentos`)
- Test: `testes/test_web_documentos.py`

**Interfaces:**
- Consumes: `Registro.registrar_upload/lista/detalhe/decidir/acrescentar/descartar`; `Manipulador._corpo_bruto/_corpo_json/_json`; `ErroDaApi`.
- Produces: rotas `GET|POST /api/documentos`, `GET|DELETE /api/documentos/{id}`, `POST /api/documentos/{id}/decisao|acrescentar`; método `Manipulador._api_documentos(metodo, caminho) -> bool` (as ações `gerar` e `abrir` entram na Task 5 no mesmo método).

- [ ] **Step 1: Escrever o teste (vermelho)**

`testes/test_web_documentos.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""API de documentos: upload cru, lista, detalhe, decisão, acrescentar e descartar."""
import _base  # noqa: F401
import http.client

import fabrica as F
from _web import ServidorDeTeste


def test_upload_lista_detalhe_decisao_acrescentar_descartar():
    with ServidorDeTeste("web_docs") as s:
        arq = F.contrato_docx(s.pasta / "contrato.docx")
        status, r = s.enviar_arquivo(arq)
        assert status == 202 and r["situacao"] == "lendo" and r["nome"] == "contrato.docx", r
        id_ = r["id"]
        d = s.esperar(id_, "revisao")
        assert d["origem"] == "janela" and d["revisavel"] and isinstance(d["avisos"], list)
        valores = {it["valor"] for it in d["itens"]}
        assert F.PESSOA_1 in valores and F.CPF in valores
        item = next(it for it in d["itens"] if it["valor"] == F.EMAIL)
        assert item["aceito"] and item["ocorrencias"] >= 1 and 1 <= len(item["contextos"]) <= 3
        assert s.post(f"/api/documentos/{id_}/decisao", {"categoria": "email", "valor": F.EMAIL, "aceito": False})[0] == 200
        status, d = s.get(f"/api/documentos/{id_}")
        assert not next(it for it in d["itens"] if it["valor"] == F.EMAIL)["aceito"]
        status, e = s.post(f"/api/documentos/{id_}/decisao", {"categoria": "email", "valor": F.EMAIL, "aceito": "sim"})
        assert status == 400 and e["erro"] == "corpo"
        status, e = s.post(f"/api/documentos/{id_}/decisao", {"categoria": "pessoa", "valor": "Ninguém Assim", "aceito": True})
        assert status == 404 and e["erro"] == "item"
        status, a = s.post(f"/api/documentos/{id_}/acrescentar", {"valor": "Porto Alegre", "categoria": "outro"})
        assert status == 200 and a["item"]["acrescido"] and a["item"]["ocorrencias"] == 1
        status, e = s.post(f"/api/documentos/{id_}/acrescentar", {"valor": "texto que não existe", "categoria": "outro"})
        assert status == 409 and "não encontrado" in e["mensagem"]
        status, e = s.post(f"/api/documentos/{id_}/acrescentar", {"valor": "Porto Alegre", "categoria": "x"})
        assert status == 409
        status, lista = s.get("/api/documentos")
        assert [x["id"] for x in lista["documentos"]] == [id_] and lista["documentos"][0]["situacao"] == "revisao"
        assert (s.pasta / "estado" / "tmp" / id_ / "contrato.docx").is_file()
        assert s.delete(f"/api/documentos/{id_}")[0] == 200
        assert not (s.pasta / "estado" / "tmp" / id_).exists()
        assert s.get(f"/api/documentos/{id_}")[0] == 404
        assert s.delete(f"/api/documentos/{id_}")[0] == 404
        assert s.get("/api/documentos")[1]["documentos"] == []


def test_upload_grande_ou_de_outro_formato_e_recusado():
    """Review Focus 1: arquivo enorme ou de outro formato arrastado à janela."""
    with ServidorDeTeste("web_docs2") as s:
        status, r = s.pedir("POST", "/api/documentos", b"abc", {"X-Nome-Arquivo": "notas.txt"})
        assert status == 415 and r["erro"] == "formato"
        status, r = s.pedir("POST", "/api/documentos", b"", {"X-Nome-Arquivo": "a.docx"})
        assert status == 400
        status, r = s.pedir("POST", "/api/documentos", b"abc")
        assert status == 400 and r["erro"] == "nome"
        # 101 MB anunciados, corpo nunca enviado: a recusa vem antes de ler
        con = http.client.HTTPConnection("127.0.0.1", s.porta, timeout=30)
        con.putrequest("POST", "/api/documentos")
        con.putheader("X-Token", s.token)
        con.putheader("X-Nome-Arquivo", "grande.pdf")
        con.putheader("Content-Length", str(101 * 1024 * 1024))
        con.endheaders()
        resp = con.getresponse()
        assert resp.status == 413
        con.close()
        assert not any((s.pasta / "estado" / "tmp").iterdir())
        # nome com pasta e codificado: fica só o nome do arquivo
        status, r = s.enviar_arquivo(F.contrato_docx(s.pasta / "c.docx"), nome="..\\..\\Contrato Ação.docx")
        assert status == 202 and r["nome"] == "Contrato Ação.docx"
        s.esperar(r["id"], "revisao", "erro")


def test_log_nunca_leva_nome_de_arquivo_nem_valores():
    with ServidorDeTeste("web_docs3") as s:
        arq = F.contrato_docx(s.pasta / f"{F.PESSOA_2}.docx")
        status, r = s.enviar_arquivo(arq)
        s.esperar(r["id"], "revisao")
        s.post(f"/api/documentos/{r['id']}/decisao", {"categoria": "cpf", "valor": F.CPF, "aceito": False})
        s.post(f"/api/documentos/{r['id']}/acrescentar", {"valor": "Porto Alegre", "categoria": "outro"})
        s.delete(f"/api/documentos/{r['id']}")
    log = s.log_texto()
    assert r["id"] in log and "registrado" in log and "descartado" in log
    for proibido in (F.PESSOA_1, F.PESSOA_2, "Souza", F.CPF, F.EMAIL, "Porto Alegre", ".docx"):
        assert proibido not in log, proibido


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `$PY -X utf8 testes/test_web_documentos.py`
Expected: FALHA — `POST /api/documentos` responde 404 (`rota desconhecida`).

- [ ] **Step 3: Implementar as rotas**

Em `pseudonimizador/web/servidor.py`, acrescente ao import `from urllib.parse import unquote, urlsplit` e estenda `ROTAS`:
```python
ROTAS: list[tuple[str, str]] = [
    ("GET", r"/api/estado"),
    ("POST", r"/api/encerrar"),
    ("GET", r"/api/documentos"),
    ("POST", r"/api/documentos"),
    ("GET", rf"/api/documentos/{RE_ID}"),
    ("DELETE", rf"/api/documentos/{RE_ID}"),
    ("POST", rf"/api/documentos/{RE_ID}/decisao"),
    ("POST", rf"/api/documentos/{RE_ID}/acrescentar"),
]
```
Troque `_tratadores` por:
```python
    def _tratadores(self) -> tuple:
        """Os blocos da API (as Tasks 6 e 7 acrescentam os seus)."""
        return (self._api_documentos,)
```
E acrescente ao `Manipulador`, depois de `_api`:
```python
    # --- documentos ----------------------------------------------------------
    def _api_documentos(self, metodo: str, caminho: str) -> bool:
        reg = self.app.registro
        if caminho == "/api/documentos":
            if metodo == "GET":
                self._json(200, {"documentos": reg.lista()})
                return True
            if metodo == "POST":
                nome = unquote(self.headers.get("X-Nome-Arquivo") or "").strip()
                if not nome:
                    raise ErroDaApi(400, "nome", "falta o cabeçalho X-Nome-Arquivo")
                if Path(nome.replace("\\", "/")).suffix.lower() not in (".docx", ".pdf"):
                    raise ErroDaApi(415, "formato", "só arquivos .docx ou .pdf")
                tamanho, pedacos = self._corpo_bruto(LIMITE_ARQUIVO)
                if tamanho == 0:
                    raise ErroDaApi(400, "corpo", "arquivo vazio")
                try:
                    doc = reg.registrar_upload(nome, pedacos)
                except ValueError as e:
                    raise ErroDaApi(415, "formato", str(e)) from None
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
            if metodo != "POST":
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
        except KeyError:
            raise ErroDaApi(404, "documento", "documento não encontrado") from None
        except LookupError as e:
            raise ErroDaApi(404, "item", str(e)) from None
        except ValueError as e:
            raise ErroDaApi(409, "valor", str(e)) from None
        except RuntimeError as e:
            raise ErroDaApi(409, "situacao", str(e)) from None

    def _acao_de_geracao(self, id_: str, acao: str, corpo: dict) -> bool:
        """gerar e abrir: Task 5."""
        return False
```

- [ ] **Step 4: Rodar e ver passar**

Run: `$PY -X utf8 testes/test_web_documentos.py && $PY -X utf8 testes/test_web_servidor.py`
Expected: `3/3 passaram` e `5/5 passaram`.

- [ ] **Step 5: Commit**

```bash
git add pseudonimizador/web/servidor.py testes/test_web_documentos.py
git commit -m "Janela: API de documentos (upload cru até 100 MB, revisão, descarte); log sem nomes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Gerar, resultado, abrir no Windows, vazamento na tela; a janela sem rede

**Files:**
- Modify: `pseudonimizador/web/servidor.py` (`ROTAS`, `_acao_de_geracao`)
- Modify: `testes/test_sem_rede.py` (fluxo pela janela)
- Test: `testes/test_web_gerar.py`

**Interfaces:**
- Consumes: `Registro.pedir_geracao/obter`, `Aplicacao.config` (`.saida`, `.mapas`, `.formato`, `.tipo`, `.modo`), `Aplicacao.abrir_no_windows`.
- Produces: rotas `POST /api/documentos/{id}/gerar` (202) e `POST /api/documentos/{id}/abrir`.

- [ ] **Step 1: Escrever o teste (vermelho)**

`testes/test_web_gerar.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Gerar pela janela, resultado, abrir arquivo/pasta (injetado) e o vazamento na tela."""
import _base  # noqa: F401
from pathlib import Path

import fabrica as F
from _web import ServidorDeTeste
from pseudonimizador.leitura import ler
from pseudonimizador.saida import VazamentoDetectado


def _enviar_e_revisar(s, nome="contrato.docx"):
    status, r = s.enviar_arquivo(F.contrato_docx(s.pasta / nome))
    assert status == 202, r
    s.esperar(r["id"], "revisao")
    return r["id"]


def test_gerar_resultado_e_abrir():
    abertos = []
    with ServidorDeTeste("web_gerar", abrir_no_windows=abertos.append) as s:
        id_ = _enviar_e_revisar(s)
        status, e = s.post(f"/api/documentos/{id_}/abrir", {"alvo": "arquivo"})
        assert status == 409 and e["erro"] == "situacao"
        status, g = s.post(f"/api/documentos/{id_}/gerar", {"formato": "layout", "modo": "reversivel"})
        assert status == 202 and g["situacao"] == "gerando", g
        d = s.esperar(id_, "pronto", "erro")
        assert d["situacao"] == "pronto", d["erro"]
        r = d["resultado"]
        assert r["saida_nome"] == "contrato - pseudonimizado.docx" and r["mapa_nome"].endswith(".json")
        saida = s.pasta / "Base" / "Saida" / r["saida_nome"]
        assert saida.is_file() and (s.pasta / "Base" / "Mapas" / r["mapa_nome"]).is_file()
        assert F.PESSOA_1 not in ler(saida).texto
        assert not (s.pasta / "estado" / "tmp" / id_).exists()
        assert s.post(f"/api/documentos/{id_}/abrir", {"alvo": "arquivo"})[0] == 200
        assert s.post(f"/api/documentos/{id_}/abrir", {"alvo": "pasta"})[0] == 200
        assert abertos == [saida, saida.parent]
        assert s.post(f"/api/documentos/{id_}/abrir", {"alvo": "outro"})[0] == 400
        assert s.post(f"/api/documentos/{id_}/gerar", {"formato": "layout", "modo": "reversivel"})[0] == 409
        assert s.post(f"/api/documentos/{id_}/decisao", {"categoria": "cpf", "valor": F.CPF, "aceito": False})[0] == 409


def test_gerar_com_padroes_da_config_e_valores_invalidos():
    with ServidorDeTeste("web_gerar2") as s:
        id_ = _enviar_e_revisar(s)
        status, e = s.post(f"/api/documentos/{id_}/gerar", {"formato": "foto", "modo": "reversivel"})
        assert status == 409 and e["erro"] == "valor"
        status, e = s.post(f"/api/documentos/{id_}/gerar", {"formato": "texto", "tipo": "txt", "modo": "definitivo"})
        assert status == 409
        assert s.post("/api/documentos/0000000000000000/gerar", {})[0] == 404
        status, g = s.post(f"/api/documentos/{id_}/gerar", {})      # vazio: os padrões da config (layout, reversível)
        assert status == 202
        d = s.esperar(id_, "pronto", "erro")
        assert d["situacao"] == "pronto" and d["resultado"]["saida_nome"] == "contrato - pseudonimizado.docx"


def test_vazamento_vira_erro_na_tela_e_nao_no_log():
    """Review Focus 4: VazamentoDetectado -> situação erro com os valores só na
    tela; a revisão continua aberta e pode gerar de novo."""
    def gerar_vazando(*a, **k):
        raise VazamentoDetectado([F.PESSOA_1, F.CPF])
    with ServidorDeTeste("web_vaza", gerar=gerar_vazando) as s:
        id_ = _enviar_e_revisar(s)
        assert s.post(f"/api/documentos/{id_}/gerar", {"formato": "layout", "modo": "definitivo"})[0] == 202
        d = s.esperar(id_, "pronto", "erro")
        assert d["situacao"] == "erro" and d["erro"]["valores"] == [F.PESSOA_1, F.CPF] and d["revisavel"]
        assert d["itens"] and d["resultado"] is None
        assert s.get("/api/documentos")[1]["documentos"][0]["erro"].startswith("2 dado(s)")
        assert s.post(f"/api/documentos/{id_}/decisao", {"categoria": "cpf", "valor": F.CPF, "aceito": False})[0] == 200
        assert s.post(f"/api/documentos/{id_}/gerar", {"formato": "layout", "modo": "definitivo"})[0] == 202
        s.esperar(id_, "pronto", "erro")
    log = s.log_texto()
    assert "vazamento detectado (2 valor(es))" in log
    assert F.PESSOA_1 not in log and F.CPF not in log and "contrato" not in log


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `$PY -X utf8 testes/test_web_gerar.py`
Expected: FALHA — `gerar` responde 404 (`_acao_de_geracao` devolve False).

- [ ] **Step 3: Implementar gerar e abrir**

Em `pseudonimizador/web/servidor.py`, acrescente a `ROTAS`:
```python
    ("POST", rf"/api/documentos/{RE_ID}/gerar"),
    ("POST", rf"/api/documentos/{RE_ID}/abrir"),
```
E substitua `_acao_de_geracao`:
```python
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
            self.app.abrir_no_windows(saida if alvo == "arquivo" else saida.parent)
            self.app.log.info("documento %s: abrir %s", id_, alvo)
            self._json(200, {"ok": True})
            return True
        return False
```

- [ ] **Step 4: Rodar e ver passar**

Run: `$PY -X utf8 testes/test_web_gerar.py`
Expected: `3/3 passaram`.

- [ ] **Step 5: Estender a guarda de rede ao servidor (vermelho primeiro pela ausência do teste)**

Substitua `testes/test_sem_rede.py` por:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Nenhuma conexão de rede fora de 127.0.0.1/::1 durante o fluxo inteiro,
inclusive o OCR e a janela (servidor local) (spec §9)."""
import _base  # noqa: F401
import socket

LOCAIS = {"127.0.0.1", "::1", "localhost"}
_tentativas: list[str] = []
_connect_original = socket.socket.connect
_create_original = socket.create_connection
_getaddrinfo_original = socket.getaddrinfo


def _host(endereco):
    return endereco[0] if isinstance(endereco, tuple) else str(endereco)


def _connect(self, endereco):
    if _host(endereco) not in LOCAIS:
        _tentativas.append(_host(endereco))
        raise OSError("rede bloqueada no teste")
    return _connect_original(self, endereco)


def _create(endereco, *a, **k):
    if _host(endereco) not in LOCAIS:
        _tentativas.append(_host(endereco))
        raise OSError("rede bloqueada no teste")
    return _create_original(endereco, *a, **k)


def _getaddrinfo(host, *a, **k):
    if host not in LOCAIS and host is not None:
        _tentativas.append(str(host))
        raise OSError("rede bloqueada no teste")
    return _getaddrinfo_original(host, *a, **k)


def _bloquear():
    _tentativas.clear()
    socket.socket.connect = _connect
    socket.create_connection = _create
    socket.getaddrinfo = _getaddrinfo


def _liberar():
    socket.socket.connect = _connect_original
    socket.create_connection = _create_original
    socket.getaddrinfo = _getaddrinfo_original


def test_fluxo_completo_sem_rede():
    _bloquear()
    try:
        import fabrica as F
        from pseudonimizador.leitura import ler
        from pseudonimizador.revisao import Revisao
        from pseudonimizador.saida import gerar
        pasta = F.pasta_temporaria("sem_rede")
        for arq in (F.contrato_docx(pasta / "a.docx"), F.contrato_escaneado(pasta / "b.pdf")):
            doc = ler(arq)
            gerar(doc, Revisao(doc).fechar(), formato="layout", modo="reversivel",
                  pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    finally:
        _liberar()
    assert not _tentativas, f"tentativas de rede: {_tentativas}"


def test_janela_sem_rede():
    """O mesmo fluxo pela janela: upload, leitura com OCR, geração — só loopback."""
    _bloquear()
    try:
        import fabrica as F
        from _web import ServidorDeTeste
        with ServidorDeTeste("sem_rede_web") as s:
            status, r = s.enviar_arquivo(F.contrato_escaneado(s.pasta / "b.pdf"))
            assert status == 202, r
            s.esperar(r["id"], "revisao")
            assert s.post(f"/api/documentos/{r['id']}/gerar", {"formato": "layout", "modo": "reversivel"})[0] == 202
            d = s.esperar(r["id"], "pronto", "erro")
            assert d["situacao"] == "pronto", d["erro"]
    finally:
        _liberar()
    assert not _tentativas, f"tentativas de rede: {_tentativas}"


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
Run: `$PY -X utf8 testes/test_sem_rede.py`
Expected: `2/2 passaram`.

- [ ] **Step 6: Commit**

```bash
git add pseudonimizador/web/servidor.py testes/test_web_gerar.py testes/test_sem_rede.py
git commit -m "Janela: gerar, resultado, abrir no Windows (injetável) e vazamento só na tela; guarda de rede cobre o servidor

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---
### Task 6: Restaurar nomes pela janela (DOCX e texto colado) e lista de mapas

**Files:**
- Modify: `pseudonimizador/web/servidor.py` (`ROTAS`, `_tratadores`, `listar_mapas`, `_api_restaurar`, `_mapa_escolhido`)
- Test: `testes/test_web_restaurar.py`

**Interfaces:**
- Consumes: `restaurar.restaurar_texto(texto, mapa) -> str`, `restaurar.restaurar_docx(origem, destino, mapa) -> int`, `restaurar.mapa_do_docx(caminho, pasta_mapas) -> dict | None`, `restaurar.TokenOrfao`; `saida.mapas.achar(pasta, id) -> Path | None`, `saida.mapas.carregar(caminho) -> dict`; `saida._destino(pasta, base, sufixo) -> Path` (a mesma regra " (2)" da saída).
- Produces: `listar_mapas(pasta_mapas: Path) -> list[dict]` (`{id, data}`); rotas `GET /api/mapas`, `POST /api/restaurar/docx`, `POST /api/restaurar/texto`.

- [ ] **Step 1: Escrever o teste (vermelho)**

`testes/test_web_restaurar.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Restaurar pela janela: DOCX (mapa pelo identificador ou escolhido) e texto colado."""
import _base  # noqa: F401
import fabrica as F
from _web import ServidorDeTeste
from pseudonimizador.leitura import ler
from pseudonimizador.motor.trocas import aplicar_trocas
from pseudonimizador.revisao import Revisao
from pseudonimizador.saida import gerar


def _gerado(s):
    doc = ler(F.contrato_docx(s.pasta / "contrato.docx"))
    res = Revisao(doc).fechar()
    g = gerar(doc, res, formato="layout", modo="reversivel",
              pasta_saida=s.pasta / "Base" / "Saida", pasta_mapas=s.pasta / "Base" / "Mapas")
    return doc, res, g


def test_restaurar_docx_pela_janela():
    import docx
    with ServidorDeTeste("web_rest") as s:
        doc, res, g = _gerado(s)
        status, m = s.get("/api/mapas")
        assert status == 200 and [x["id"] for x in m["mapas"]] == [g.mapa.stem]
        assert len(m["mapas"][0]["data"]) == 16 and set(m["mapas"][0]) == {"id", "data"}
        status, r = s.enviar_arquivo(g.saida, rota="/api/restaurar/docx")
        assert status == 200 and r["trocas"] > 0 and r["saida_nome"] == "contrato - pseudonimizado - restaurado.docx", r
        assert ler(s.pasta / "Base" / "Saida" / r["saida_nome"]).texto == doc.texto
        status, r2 = s.enviar_arquivo(g.saida, rota="/api/restaurar/docx")
        assert r2["saida_nome"] == "contrato - pseudonimizado - restaurado (2).docx"
        # DOCX sem identificador: pede o mapa; com X-Mapa, restaura
        sem_id = s.pasta / "sem_id.docx"
        d2 = docx.Document(str(g.saida))
        d2.core_properties.identifier = ""
        d2.save(str(sem_id))
        status, r3 = s.enviar_arquivo(sem_id, rota="/api/restaurar/docx")
        assert status == 409 and r3["erro"] == "mapa"
        status, r4 = s.enviar_arquivo(sem_id, rota="/api/restaurar/docx", cabecalhos={"X-Mapa": g.mapa.stem})
        assert status == 200 and r4["saida_nome"] == "sem_id - restaurado.docx"
        status, r5 = s.enviar_arquivo(sem_id, rota="/api/restaurar/docx", cabecalhos={"X-Mapa": "nao-existe"})
        assert status == 404 and r5["erro"] == "mapa"
        assert s.enviar_arquivo(sem_id, rota="/api/restaurar/docx", cabecalhos={"X-Mapa": "../x"})[0] == 400
        assert s.enviar_arquivo(g.mapa, rota="/api/restaurar/docx")[0] == 415
        quebrado = s.pasta / "quebrado.docx"
        quebrado.write_bytes(b"nao e docx")
        status, r6 = s.enviar_arquivo(quebrado, rota="/api/restaurar/docx")
        assert status == 409 and r6["erro"] == "arquivo"
        assert not list((s.pasta / "estado" / "tmp").iterdir())
    log = s.log_texto()
    assert "restaura" in log and F.PESSOA_1 not in log and "contrato" not in log


def test_restaurar_texto_e_token_orfao():
    with ServidorDeTeste("web_rest2") as s:
        doc, res, g = _gerado(s)
        protegido = aplicar_trocas(doc.texto, res.trocas)
        status, r = s.post("/api/restaurar/texto", {"texto": protegido, "mapa": g.mapa.stem})
        assert status == 200 and r["texto"] == doc.texto
        status, e = s.post("/api/restaurar/texto", {"texto": "resposta citando [[PESSOA_99]]", "mapa": g.mapa.stem})
        assert status == 409 and e["erro"] == "orfao" and "[[PESSOA_99]]" in e["mensagem"]
        assert s.post("/api/restaurar/texto", {"texto": protegido})[0] == 400
        assert s.post("/api/restaurar/texto", {"texto": "   ", "mapa": g.mapa.stem})[0] == 400
        assert s.post("/api/restaurar/texto", {"texto": protegido, "mapa": "nao-existe"})[0] == 404


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `$PY -X utf8 testes/test_web_restaurar.py`
Expected: FALHA — `GET /api/mapas` responde 404.

- [ ] **Step 3: Implementar**

Em `pseudonimizador/web/servidor.py`, imports novos:
```python
import shutil
from datetime import datetime

from ..restaurar import TokenOrfao, mapa_do_docx, restaurar_docx, restaurar_texto
from ..saida import _destino, mapas
```
`ROTAS` ganha:
```python
    ("GET", r"/api/mapas"),
    ("POST", r"/api/restaurar/docx"),
    ("POST", r"/api/restaurar/texto"),
```
Função de módulo (antes de `class ErroDaApi`):
```python
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
```
`_tratadores`:
```python
    def _tratadores(self) -> tuple:
        """Os blocos da API (a Task 7 acrescenta o da configuração)."""
        return (self._api_documentos, self._api_restaurar)
```
E, no `Manipulador`:
```python
    # --- restaurar -----------------------------------------------------------
    def _mapa_escolhido(self, id_mapa) -> dict:
        if not isinstance(id_mapa, str) or not re.fullmatch(r"[0-9A-Za-z_-]{1,80}", id_mapa):
            raise ErroDaApi(400, "mapa", "escolha um mapa da lista")
        caminho = mapas.achar(self.app.config.mapas, id_mapa)
        if caminho is None:
            raise ErroDaApi(404, "mapa", "mapa não encontrado")
        return mapas.carregar(caminho)

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
            nome = Path(unquote(self.headers.get("X-Nome-Arquivo") or "").replace("\\", "/")).name
            if not nome or nome in (".", ".."):
                raise ErroDaApi(400, "nome", "falta o cabeçalho X-Nome-Arquivo")
            if not nome.lower().endswith(".docx"):
                raise ErroDaApi(415, "formato", "só arquivos .docx")
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
                        mapa = mapa_do_docx(origem, cfg.mapas)
                    except Exception:  # noqa: BLE001 — zip/XML inválido
                        raise ErroDaApi(409, "arquivo", "o arquivo não é um DOCX válido") from None
                if mapa is None:
                    raise ErroDaApi(409, "mapa", "Mapa não encontrado para este arquivo; escolha um da lista.")
                cfg.saida.mkdir(parents=True, exist_ok=True)
                destino = _destino(cfg.saida, f"{origem.stem} - restaurado", ".docx")
                try:
                    n = restaurar_docx(origem, destino, mapa)
                except TokenOrfao as e:
                    raise ErroDaApi(409, "orfao", str(e)) from None
                except Exception:  # noqa: BLE001
                    raise ErroDaApi(409, "arquivo", "o arquivo não é um DOCX válido") from None
            finally:
                shutil.rmtree(pasta, ignore_errors=True)
            self.app.log.info("restauração de DOCX: %d troca(s)", n)
            self._json(200, {"ok": True, "saida_nome": destino.name, "trocas": n})
            return True
        return False
```

- [ ] **Step 4: Rodar e ver passar**

Run: `$PY -X utf8 testes/test_web_restaurar.py`
Expected: `2/2 passaram`.

- [ ] **Step 5: Commit**

```bash
git add pseudonimizador/web/servidor.py testes/test_web_restaurar.py
git commit -m "Janela: restaurar nomes (DOCX pelo identificador ou mapa escolhido; texto colado) e lista de mapas

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Configurações pela janela

**Files:**
- Modify: `pseudonimizador/web/servidor.py` (`ROTAS`, `_tratadores`, `_api_config`, `_config_publica`)
- Test: `testes/test_web_config.py`

**Interfaces:**
- Consumes: `estado.validar/gravar/preparar_pastas`, `Aplicacao.aplicar_config(nova)`.
- Produces: `GET /api/config` e `POST /api/config` → `{pasta_base, pasta_saida, pasta_mapas, formato, tipo, modo, pastas: {entrada, saida, mapas, processados}}`; 400 `config` com a frase da validação.

- [ ] **Step 1: Escrever o teste (vermelho)**

`testes/test_web_config.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Configurações pela janela: ler, gravar, validar antes de gravar, e o gerar usa o novo."""
import _base  # noqa: F401
import json

import fabrica as F
from _web import ServidorDeTeste


def test_config_ler_gravar_validar_e_usar():
    with ServidorDeTeste("web_config") as s:
        status, c = s.get("/api/config")
        assert status == 200 and c["pasta_base"] == str(s.pasta / "Base") and c["formato"] == "layout"
        assert c["pastas"]["entrada"] == str(s.pasta / "Base" / "Entrada") and c["pasta_saida"] == ""
        nova = {"pasta_base": str(s.pasta / "Base2"), "formato": "texto", "tipo": "pdf", "modo": "definitivo"}
        status, c = s.post("/api/config", nova)
        assert status == 200 and c["modo"] == "definitivo" and c["pastas"]["saida"] == str(s.pasta / "Base2" / "Saida")
        for sub in ("Entrada", "Saida", "Mapas", "Entrada/Processados"):
            assert (s.pasta / "Base2" / sub).is_dir()
        gravado = json.loads((s.pasta / "estado" / "config.json").read_text(encoding="utf-8"))
        assert gravado["pasta_base"] == str(s.pasta / "Base2") and gravado["tipo"] == "pdf"
        # mapas dentro da saída: recusado ANTES de gravar
        status, e = s.post("/api/config", {**nova, "pasta_mapas": str(s.pasta / "Base2" / "Saida" / "M")})
        assert status == 400 and e["erro"] == "config" and "mapas" in e["mensagem"]
        assert s.get("/api/config")[1]["pasta_mapas"] == ""
        assert s.post("/api/config", {**nova, "pasta_base": "Base3"})[0] == 400
        assert s.post("/api/config", {**nova, "modo": "talvez"})[0] == 400
        assert s.post("/api/config", b"x")[0] == 400
        # o gerar com corpo vazio passa a usar os padrões e as pastas novas
        status, r = s.enviar_arquivo(F.contrato_docx(s.pasta / "contrato.docx"))
        s.esperar(r["id"], "revisao")
        assert s.post(f"/api/documentos/{r['id']}/gerar", {})[0] == 202
        d = s.esperar(r["id"], "pronto", "erro")
        assert d["situacao"] == "pronto", d["erro"]
        assert d["resultado"]["saida_nome"] == "contrato - anonimizado.pdf" and d["resultado"]["mapa_nome"] is None
        assert (s.pasta / "Base2" / "Saida" / "contrato - anonimizado.pdf").is_file()
    assert s.pasta.name not in s.log_texto()       # o caminho não vai ao log


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `$PY -X utf8 testes/test_web_config.py`
Expected: FALHA — `GET /api/config` responde 404.

- [ ] **Step 3: Implementar**

Em `pseudonimizador/web/servidor.py`: o import de `estado` passa a `from ..estado import Config, abrir_log, carregar, gravar, preparar_pastas, validar`; `ROTAS` ganha `("GET", r"/api/config")` e `("POST", r"/api/config")`; `_tratadores` passa a devolver `(self._api_documentos, self._api_restaurar, self._api_config)`; e no `Manipulador`:
```python
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
            except OSError as e:
                raise ErroDaApi(400, "config", f"não foi possível criar as pastas: {e.strerror or e}") from None
            gravar(self.app.pasta_estado, nova)
            self.app.aplicar_config(nova)
            self.app.log.info("configuração gravada (%s, %s, %s)", nova.formato, nova.tipo, nova.modo)
            self._json(200, self._config_publica())
            return True
        return False
```

- [ ] **Step 4: Rodar e ver passar**

Run: `$PY -X utf8 testes/test_web_config.py && $PY -X utf8 testes/test_web_servidor.py`
Expected: `1/1 passaram` e `5/5 passaram`.

- [ ] **Step 5: Commit**

```bash
git add pseudonimizador/web/servidor.py testes/test_web_config.py
git commit -m "Janela: configurações (pasta base, saída, mapas e padrões do lote) validadas antes de gravar

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---
### Task 8: Página da janela (HTML, CSS e JS próprios; telas Documentos/Pendentes, Revisão, Resultado, Restaurar, Configurações)

**Files:**
- Create: `pseudonimizador/web/estatico/index.html`, `pseudonimizador/web/estatico/app.css`, `pseudonimizador/web/estatico/app.js`
- Test: `testes/test_web_estaticos.py`

**Interfaces:**
- Consumes: todo o contrato da API (tabela no início do plano) e `servidor.ROTAS`, `servidor.ESTATICOS`, `servidor.PASTA_ESTATICO`.
- Produces: a página servida em `/` (e `/estatico/app.js`, `/estatico/app.css`). Com `Content-Security-Policy: default-src 'self'` nada pode ser inline: sem `<script>` com conteúdo, sem `on*=`, sem `style=`. O token vem do fragmento `#t=` e vai em `X-Token`; a navegação entre telas não mexe no fragmento.

- [ ] **Step 1: Escrever o teste (vermelho)**

`testes/test_web_estaticos.py`:
```python
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
    ids = re.findall(r'<(?:input|select|textarea)[^>]*\sid="([^"]+)"', html)
    assert ids
    for id_ in ids:
        assert f'for="{id_}"' in html, f"campo sem <label for>: {id_}"


def test_rotas_do_app_js_existem_no_servidor():
    js = _ler("app.js")
    js = re.sub(r"'\s*\+\s*\w+\s*\+\s*'", "0" * 16, js)        # '/api/documentos/' + id + '/gerar'
    js = re.sub(r"'\s*\+\s*\w+\b", "0" * 16 + "'", js)           # '/api/documentos/' + id
    rotas = set(re.findall(r"'(/api/[^']*)'", js))
    assert {"/api/documentos", "/api/config", "/api/mapas", "/api/encerrar"} <= rotas
    padroes = [p for _, p in ROTAS]
    for rota in rotas:
        assert any(re.fullmatch(p, rota) for p in padroes), f"rota do app.js sem servidor: {rota}"


def test_servidor_entrega_a_pagina():
    with ServidorDeTeste("web_estaticos") as s:
        status, corpo = s.get("/", token=False)
        assert status == 200 and b"<title>Pseudonimizador</title>" in corpo
        status, corpo = s.get("/estatico/app.js", token=False)
        assert status == 200 and b"X-Token" in corpo
        assert s.get("/estatico/app.css", token=False)[0] == 200


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `$PY -X utf8 testes/test_web_estaticos.py`
Expected: FALHA — `FileNotFoundError` em `index.html`.

- [ ] **Step 3: Escrever `index.html`**

`pseudonimizador/web/estatico/index.html`:
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pseudonimizador</title>
<link rel="stylesheet" href="/estatico/app.css">
</head>
<body>
<header class="topo">
  <h1>Pseudonimizador</h1>
  <nav aria-label="Telas">
    <button type="button" data-tela="documentos" aria-current="page">Documentos</button>
    <button type="button" data-tela="restaurar">Restaurar nomes</button>
    <button type="button" data-tela="configuracoes">Configurações</button>
    <button type="button" id="encerrar" class="secundario">Encerrar</button>
  </nav>
</header>
<p id="mensagem" class="mensagem" role="status" aria-live="polite" hidden></p>
<main>

<section id="tela-documentos" aria-labelledby="h-documentos">
  <h2 id="h-documentos">Documentos</h2>
  <div id="zona" class="zona" tabindex="0" role="button" aria-describedby="zona-ajuda">
    <p>Arraste aqui um DOCX ou PDF, ou <label for="arquivos" class="ligacao">escolha os arquivos</label>.</p>
    <p id="zona-ajuda" class="ajuda">Até 100 MB por arquivo. Tudo é processado neste computador; nada sai dele.</p>
    <input type="file" id="arquivos" class="oculto" accept=".docx,.pdf" multiple>
  </div>
  <h3>Enviados pela janela</h3>
  <ul id="lista-janela" class="lista"></ul>
  <h3>Pendentes (pasta Entrada)</h3>
  <p class="ajuda">Arquivos colocados em <code id="pasta-entrada"></code> aparecem aqui para revisão; depois de gerados, o original vai para Entrada\Processados.</p>
  <ul id="lista-pasta" class="lista"></ul>
</section>

<section id="tela-revisao" hidden aria-labelledby="h-revisao">
  <h2 id="h-revisao">Revisão: <span id="rev-nome"></span></h2>
  <ul id="rev-avisos" class="avisos"></ul>
  <div id="rev-erro" class="erro" hidden>
    <p id="rev-erro-mensagem"></p>
    <ul id="rev-erro-valores"></ul>
  </div>
  <p class="ajuda">Tudo começa marcado para substituir. Desmarque o que deve ficar em claro. Aceitar um nome aceita todas as suas ocorrências e variantes.</p>
  <table class="itens">
    <caption>Dados encontrados</caption>
    <thead><tr><th scope="col">Substituir</th><th scope="col">Categoria</th><th scope="col">Valor</th><th scope="col">Ocorrências</th><th scope="col">Trechos</th></tr></thead>
    <tbody id="rev-itens"></tbody>
  </table>
  <form id="form-acrescentar" class="linha">
    <label for="acr-valor">Acrescentar o que escapou</label>
    <input id="acr-valor" type="text" required autocomplete="off" placeholder="texto exatamente como está no documento">
    <label for="acr-categoria">Categoria</label>
    <select id="acr-categoria"></select>
    <button type="submit">Acrescentar</button>
  </form>
  <form id="form-gerar">
    <fieldset>
      <legend>Formato</legend>
      <label><input type="radio" name="formato" value="layout" checked> Layout original (DOCX→DOCX, PDF→PDF)</label>
      <label><input type="radio" name="formato" value="texto"> Documento novo só com o texto</label>
    </fieldset>
    <fieldset id="campo-tipo">
      <legend>Tipo do documento novo</legend>
      <label><input type="radio" name="tipo" value="docx" checked> Word (DOCX)</label>
      <label><input type="radio" name="tipo" value="pdf"> PDF</label>
    </fieldset>
    <fieldset>
      <legend>Modo</legend>
      <label><input type="radio" name="modo" value="reversivel" checked> Reversível (pseudonimização; o mapa fica na pasta Mapas)</label>
      <label><input type="radio" name="modo" value="definitivo"> Definitivo (anonimização; sem mapa)</label>
    </fieldset>
    <p class="linha">
      <button type="submit" id="botao-gerar">Gerar</button>
      <button type="button" id="rev-voltar" class="secundario">Voltar</button>
    </p>
  </form>
</section>

<section id="tela-resultado" hidden aria-labelledby="h-resultado">
  <h2 id="h-resultado">Pronto</h2>
  <p>Arquivo gerado: <strong id="res-saida"></strong></p>
  <p id="res-mapa-linha" hidden>Mapa (guarde à parte; é dado pessoal): <code id="res-mapa"></code></p>
  <ul id="res-avisos" class="avisos"></ul>
  <p class="linha">
    <button type="button" id="res-abrir-arquivo">Abrir arquivo</button>
    <button type="button" id="res-abrir-pasta">Abrir pasta de saída</button>
    <button type="button" id="res-voltar" class="secundario">Voltar aos documentos</button>
  </p>
</section>

<section id="tela-restaurar" hidden aria-labelledby="h-restaurar">
  <h2 id="h-restaurar">Restaurar nomes</h2>
  <form id="form-rest-docx">
    <h3>A partir de um DOCX pseudonimizado</h3>
    <label for="rest-arquivo">Arquivo DOCX</label>
    <input id="rest-arquivo" type="file" accept=".docx" required>
    <label for="rest-mapa-docx">Mapa (só se o arquivo não indicar o seu)</label>
    <select id="rest-mapa-docx"></select>
    <p class="linha"><button type="submit">Restaurar DOCX</button></p>
    <p id="rest-docx-resultado" role="status" aria-live="polite"></p>
  </form>
  <form id="form-rest-texto">
    <h3>A partir de texto colado</h3>
    <label for="rest-texto">Texto com os tókens [[...]]</label>
    <textarea id="rest-texto" rows="8" required></textarea>
    <label for="rest-mapa-texto">Mapa</label>
    <select id="rest-mapa-texto" required></select>
    <p class="linha"><button type="submit">Restaurar texto</button></p>
    <label for="rest-texto-saida">Texto restaurado</label>
    <textarea id="rest-texto-saida" rows="8" readonly></textarea>
  </form>
</section>

<section id="tela-configuracoes" hidden aria-labelledby="h-config">
  <h2 id="h-config">Configurações</h2>
  <form id="form-config">
    <label for="cfg-base">Pasta base (Entrada, Saida e Mapas ficam dentro dela)</label>
    <input id="cfg-base" type="text" required>
    <label for="cfg-saida">Pasta de saída (vazio: Saida dentro da base)</label>
    <input id="cfg-saida" type="text">
    <label for="cfg-mapas">Pasta dos mapas (vazio: Mapas dentro da base; nunca dentro da saída)</label>
    <input id="cfg-mapas" type="text">
    <fieldset>
      <legend>Padrões do lote (pasta Entrada)</legend>
      <label for="cfg-formato">Formato</label>
      <select id="cfg-formato"><option value="layout">Layout original</option><option value="texto">Só o texto</option></select>
      <label for="cfg-tipo">Tipo (só para "só o texto")</label>
      <select id="cfg-tipo"><option value="docx">Word (DOCX)</option><option value="pdf">PDF</option></select>
      <label for="cfg-modo">Modo</label>
      <select id="cfg-modo"><option value="reversivel">Reversível</option><option value="definitivo">Definitivo</option></select>
    </fieldset>
    <p class="linha"><button type="submit">Salvar</button></p>
  </form>
</section>

</main>
<footer class="rodape"><small>Pseudonimizador <span id="versao"></span> · tudo roda neste computador.</small></footer>
<script src="/estatico/app.js"></script>
</body>
</html>
```

- [ ] **Step 4: Escrever `app.css`**

`pseudonimizador/web/estatico/app.css`:
```css
:root { --tinta: #1b1b1b; --fundo: #ffffff; --borda: #b9b9b9; --realce: #0b5fa5; --erro: #a40000; --ok: #1e6b2e; --suave: #f3f5f7; }
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--fundo); color: var(--tinta); font: 16px/1.45 system-ui, "Segoe UI", sans-serif; }
main { max-width: 64rem; margin: 0 auto; padding: 0 1rem 2rem; }
.topo { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; padding: .75rem 1rem; border-bottom: 1px solid var(--borda); background: var(--suave); }
.topo h1 { font-size: 1.25rem; margin: 0; }
nav button { margin-right: .25rem; }
nav button[aria-current="page"] { background: var(--realce); color: #fff; border-color: var(--realce); }
h2 { font-size: 1.2rem; margin: 1.25rem 0 .5rem; }
h3 { font-size: 1rem; margin: 1.25rem 0 .25rem; }
button { font: inherit; padding: .4rem .9rem; border: 1px solid var(--borda); border-radius: .3rem; background: #fff; color: var(--tinta); cursor: pointer; }
button:hover, button:focus-visible { border-color: var(--realce); outline: 2px solid var(--realce); outline-offset: 1px; }
button[type="submit"], #botao-gerar { background: var(--realce); color: #fff; border-color: var(--realce); }
button.secundario { background: #fff; color: var(--tinta); }
button:disabled { opacity: .5; cursor: default; }
input[type="text"], select, textarea { font: inherit; width: 100%; padding: .4rem; border: 1px solid var(--borda); border-radius: .3rem; margin: .15rem 0 .75rem; }
label { display: block; font-weight: 600; margin-top: .5rem; }
fieldset label { font-weight: 400; margin: .2rem 0; }
fieldset { border: 1px solid var(--borda); border-radius: .3rem; margin: .75rem 0; }
fieldset:disabled { opacity: .5; }
.linha { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; }
.linha label { margin-top: 0; }
.linha input[type="text"] { width: auto; flex: 1 1 18rem; margin: 0; }
.linha select { width: auto; margin: 0; }
.ajuda { color: #555; font-size: .92rem; }
.ligacao { display: inline; color: var(--realce); text-decoration: underline; cursor: pointer; font-weight: 600; }
.oculto { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.zona { border: 2px dashed var(--borda); border-radius: .5rem; padding: 1.5rem; text-align: center; background: var(--suave); }
.zona.ativa, .zona:focus-visible { border-color: var(--realce); outline: none; background: #e8f1fa; }
.lista { list-style: none; padding: 0; margin: 0; }
.lista li { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; padding: .5rem .25rem; border-bottom: 1px solid var(--borda); }
.lista li .acoes { margin-left: auto; display: flex; gap: .4rem; }
.lista li p.erro { flex-basis: 100%; margin: 0; }
.situacao { padding: .05rem .5rem; border-radius: 1rem; background: var(--suave); font-size: .9rem; }
.situacao.pronto { background: #e3f3e6; color: var(--ok); }
.situacao.erro { background: #fbe4e4; color: var(--erro); }
.situacao.lendo, .situacao.gerando { background: #fff4d6; }
.mensagem { margin: .5rem auto 0; max-width: 64rem; padding: .5rem 1rem; border-left: 4px solid var(--ok); background: var(--suave); }
.mensagem.erro, .erro { border-left: 4px solid var(--erro); color: var(--erro); padding-left: .75rem; }
.avisos { color: #7a4b00; }
.avisos:empty { display: none; }
table.itens { width: 100%; border-collapse: collapse; margin: .5rem 0 1rem; }
table.itens caption { text-align: left; font-weight: 600; padding: .25rem 0; }
table.itens th, table.itens td { border-bottom: 1px solid var(--borda); padding: .35rem .5rem; text-align: left; vertical-align: top; }
table.itens input[type="checkbox"] { width: 1.1rem; height: 1.1rem; }
.contexto { margin: .2rem 0; font-size: .9rem; color: #444; }
code { background: var(--suave); padding: 0 .25rem; }
.rodape { text-align: center; color: #666; padding: 1rem; border-top: 1px solid var(--borda); }
```

- [ ] **Step 5: Escrever `app.js`**

`pseudonimizador/web/estatico/app.js`:
```javascript
'use strict';
(function () {
  const TOKEN = new URLSearchParams(location.hash.replace(/^#/, '')).get('t') || '';
  const $ = (id) => document.getElementById(id);
  const SITUACOES = { lendo: 'lendo…', revisao: 'aguardando revisão', gerando: 'gerando…', pronto: 'pronto', erro: 'erro' };
  const CATEGORIAS = { pessoa: 'Pessoa', empresa: 'Empresa', cpf: 'CPF', cnpj: 'CNPJ', rg: 'RG', pis: 'PIS', ctps: 'CTPS',
    email: 'E-mail', telefone: 'Telefone', endereco: 'Endereço', conta: 'Conta bancária', url: 'Endereço web', outro: 'Outro' };
  let config = null;
  let atual = null;              // id do documento em revisão/resultado
  let esperandoGeracao = false;  // depois de "Gerar": abre o resultado sozinho quando ficar pronto

  function mensagem(texto, erro) {
    const m = $('mensagem');
    m.textContent = texto || '';
    m.hidden = !texto;
    m.classList.toggle('erro', !!erro);
  }

  async function api(metodo, caminho, corpo, cabecalhos) {
    const opcoes = { method: metodo, headers: Object.assign({ 'X-Token': TOKEN }, cabecalhos || {}) };
    if (corpo instanceof Blob) {
      opcoes.headers['Content-Type'] = 'application/octet-stream';
      opcoes.body = corpo;
    } else if (corpo !== undefined) {
      opcoes.headers['Content-Type'] = 'application/json';
      opcoes.body = JSON.stringify(corpo);
    }
    const r = await fetch(caminho, opcoes);
    let dados = {};
    try { dados = await r.json(); } catch (e) { dados = {}; }
    if (!r.ok) {
      const erro = new Error(dados.mensagem || ('erro ' + r.status));
      erro.codigo = dados.erro;
      throw erro;
    }
    return dados;
  }

  function mostrar(tela) {
    for (const s of document.querySelectorAll('main > section')) s.hidden = s.id !== 'tela-' + tela;
    for (const b of document.querySelectorAll('nav [data-tela]')) {
      if (b.dataset.tela === tela) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
    }
    mensagem('');
    if (tela === 'documentos') atualizarLista();
    if (tela === 'restaurar') carregarMapas();
    if (tela === 'configuracoes') preencherConfig();
  }

  function botao(rotulo, acao, classe) {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = rotulo;
    if (classe) b.className = classe;
    b.addEventListener('click', acao);
    return b;
  }

  function lista(ul, itens) {
    ul.replaceChildren();
    for (const t of itens || []) {
      const li = document.createElement('li');
      li.textContent = t;
      ul.append(li);
    }
  }

  // --- Documentos e Pendentes ---------------------------------------------
  async function enviar(arquivos) {
    for (const arq of arquivos) {
      if (!/\.(docx|pdf)$/i.test(arq.name)) { mensagem('Só arquivos .docx ou .pdf: ' + arq.name, true); continue; }
      if (arq.size > 100 * 1024 * 1024) { mensagem('Arquivo maior que 100 MB: ' + arq.name, true); continue; }
      try {
        await api('POST', '/api/documentos', arq, { 'X-Nome-Arquivo': encodeURIComponent(arq.name) });
      } catch (e) { mensagem(e.message, true); }
    }
    atualizarLista();
  }

  function linhaDocumento(d) {
    const li = document.createElement('li');
    const nome = document.createElement('strong');
    nome.textContent = d.nome;
    const sit = document.createElement('span');
    sit.className = 'situacao ' + d.situacao;
    sit.textContent = SITUACOES[d.situacao] || d.situacao;
    li.append(nome, sit);
    if (d.avisos) {
      const a = document.createElement('span');
      a.className = 'ajuda';
      a.textContent = d.avisos + ' aviso(s)';
      li.append(a);
    }
    const acoes = document.createElement('span');
    acoes.className = 'acoes';
    if (d.revisavel && (d.situacao === 'revisao' || d.situacao === 'erro')) acoes.append(botao('Revisar', () => abrirRevisao(d.id)));
    if (d.situacao === 'pronto') acoes.append(botao('Resultado', () => abrirResultado(d.id)));
    acoes.append(botao('Descartar', () => descartar(d.id), 'secundario'));
    li.append(acoes);
    if (d.erro) {
      const e = document.createElement('p');
      e.className = 'erro';
      e.textContent = d.erro;
      li.append(e);
    }
    return li;
  }

  function vazio(texto) {
    const li = document.createElement('li');
    li.className = 'ajuda';
    li.textContent = texto;
    return li;
  }

  async function atualizarLista() {
    let dados;
    try { dados = await api('GET', '/api/documentos'); } catch (e) { mensagem(e.message, true); return; }
    const janela = $('lista-janela');
    const pasta = $('lista-pasta');
    janela.replaceChildren();
    pasta.replaceChildren();
    for (const d of dados.documentos) (d.origem === 'pasta' ? pasta : janela).append(linhaDocumento(d));
    if (!janela.children.length) janela.append(vazio('Nenhum documento enviado.'));
    if (!pasta.children.length) pasta.append(vazio('Nada pendente.'));
    if (atual && esperandoGeracao) {
      const d = dados.documentos.find((x) => x.id === atual);
      if (d && d.situacao === 'pronto') { esperandoGeracao = false; abrirResultado(atual); }
      if (d && d.situacao === 'erro') { esperandoGeracao = false; abrirRevisao(atual); }
    }
  }

  async function descartar(id) {
    if (!window.confirm('Descartar este documento?')) return;
    try { await api('DELETE', '/api/documentos/' + id); } catch (e) { mensagem(e.message, true); }
    if (atual === id) atual = null;
    atualizarLista();
  }

  // --- Revisão -------------------------------------------------------------
  function linhaItem(it) {
    const tr = document.createElement('tr');
    const tdMarca = document.createElement('td');
    const caixa = document.createElement('input');
    caixa.type = 'checkbox';
    caixa.checked = it.aceito;
    caixa.setAttribute('aria-label', 'Substituir ' + it.valor);
    caixa.addEventListener('change', async () => {
      try {
        await api('POST', '/api/documentos/' + atual + '/decisao', { categoria: it.categoria, valor: it.valor, aceito: caixa.checked });
      } catch (e) { caixa.checked = !caixa.checked; mensagem(e.message, true); }
    });
    tdMarca.append(caixa);
    const tdCat = document.createElement('td');
    tdCat.textContent = (CATEGORIAS[it.categoria] || it.categoria) + (it.acrescido ? ' (acrescido)' : '');
    const tdValor = document.createElement('td');
    tdValor.textContent = it.valor;
    const tdN = document.createElement('td');
    tdN.textContent = String(it.ocorrencias);
    const tdTrechos = document.createElement('td');
    const det = document.createElement('details');
    const sum = document.createElement('summary');
    sum.textContent = 'ver';
    det.append(sum);
    for (const c of it.contextos) {
      const p = document.createElement('p');
      p.className = 'contexto';
      p.textContent = '…' + c + '…';
      det.append(p);
    }
    tdTrechos.append(det);
    tr.append(tdMarca, tdCat, tdValor, tdN, tdTrechos);
    return tr;
  }

  function marcar(nome, valor) {
    const r = document.querySelector('#form-gerar input[name="' + nome + '"][value="' + valor + '"]');
    if (r) r.checked = true;
  }

  function valorMarcado(nome) {
    const r = document.querySelector('#form-gerar input[name="' + nome + '"]:checked');
    return r ? r.value : '';
  }

  function atualizarTipo() { $('campo-tipo').disabled = valorMarcado('formato') !== 'texto'; }

  async function abrirRevisao(id) {
    let d;
    try { d = await api('GET', '/api/documentos/' + id); } catch (e) { mensagem(e.message, true); return; }
    atual = id;
    $('rev-nome').textContent = d.nome;
    lista($('rev-avisos'), d.avisos);
    $('rev-erro').hidden = !d.erro;
    if (d.erro) {
      $('rev-erro-mensagem').textContent = d.erro.mensagem;
      lista($('rev-erro-valores'), d.erro.valores);
    }
    const corpo = $('rev-itens');
    corpo.replaceChildren();
    for (const it of d.itens) corpo.append(linhaItem(it));
    if (!d.itens.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 5;
      td.textContent = 'Nenhum dado encontrado. Acrescente abaixo o que deve ser protegido.';
      tr.append(td);
      corpo.append(tr);
    }
    if (config) { marcar('formato', config.formato); marcar('tipo', config.tipo); marcar('modo', config.modo); }
    atualizarTipo();
    $('botao-gerar').disabled = false;
    mostrar('revisao');
  }

  $('form-acrescentar').addEventListener('submit', async (ev) => {
    ev.preventDefault();
    try {
      await api('POST', '/api/documentos/' + atual + '/acrescentar', { valor: $('acr-valor').value, categoria: $('acr-categoria').value });
      $('acr-valor').value = '';
      await abrirRevisao(atual);
      mensagem('Acrescentado.');
    } catch (e) { mensagem(e.message, true); }
  });

  $('form-gerar').addEventListener('change', atualizarTipo);
  $('form-gerar').addEventListener('submit', async (ev) => {
    ev.preventDefault();
    $('botao-gerar').disabled = true;
    try {
      await api('POST', '/api/documentos/' + atual + '/gerar', { formato: valorMarcado('formato'), tipo: valorMarcado('tipo'), modo: valorMarcado('modo') });
      esperandoGeracao = true;
      mostrar('documentos');
      mensagem('Gerando… o resultado abre sozinho quando ficar pronto.');
    } catch (e) { $('botao-gerar').disabled = false; mensagem(e.message, true); }
  });
  $('rev-voltar').addEventListener('click', () => mostrar('documentos'));

  // --- Resultado -----------------------------------------------------------
  async function abrirResultado(id) {
    let d;
    try { d = await api('GET', '/api/documentos/' + id); } catch (e) { mensagem(e.message, true); return; }
    if (!d.resultado) { mensagem('O documento ainda não foi gerado.', true); return; }
    atual = id;
    $('res-saida').textContent = d.resultado.saida_nome;
    $('res-mapa-linha').hidden = !d.resultado.mapa_nome;
    $('res-mapa').textContent = d.resultado.mapa_nome || '';
    lista($('res-avisos'), d.resultado.avisos);
    mostrar('resultado');
  }

  async function abrirNoWindows(alvo) {
    try { await api('POST', '/api/documentos/' + atual + '/abrir', { alvo: alvo }); } catch (e) { mensagem(e.message, true); }
  }
  $('res-abrir-arquivo').addEventListener('click', () => abrirNoWindows('arquivo'));
  $('res-abrir-pasta').addEventListener('click', () => abrirNoWindows('pasta'));
  $('res-voltar').addEventListener('click', () => mostrar('documentos'));

  // --- Restaurar -----------------------------------------------------------
  async function carregarMapas() {
    let dados;
    try { dados = await api('GET', '/api/mapas'); } catch (e) { mensagem(e.message, true); return; }
    const alvos = [['rest-mapa-docx', 'Automático (pelo identificador do arquivo)'], ['rest-mapa-texto', 'Escolha o mapa']];
    for (const [id, primeiro] of alvos) {
      const sel = $(id);
      sel.replaceChildren();
      const o = document.createElement('option');
      o.value = '';
      o.textContent = primeiro;
      sel.append(o);
      for (const m of dados.mapas) {
        const op = document.createElement('option');
        op.value = m.id;
        op.textContent = m.data + ' — ' + m.id;
        sel.append(op);
      }
    }
  }

  $('form-rest-docx').addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const arq = $('rest-arquivo').files[0];
    if (!arq) return;
    const cabecalhos = { 'X-Nome-Arquivo': encodeURIComponent(arq.name) };
    const mapa = $('rest-mapa-docx').value;
    if (mapa) cabecalhos['X-Mapa'] = mapa;
    const saida = $('rest-docx-resultado');
    saida.textContent = 'Restaurando…';
    try {
      const r = await api('POST', '/api/restaurar/docx', arq, cabecalhos);
      saida.textContent = 'Restaurado na pasta de saída: ' + r.saida_nome + ' (' + r.trocas + ' troca(s)).';
    } catch (e) {
      saida.textContent = e.message + (e.codigo === 'mapa' ? ' Escolha o mapa acima e tente de novo.' : '');
    }
  });

  $('form-rest-texto').addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const mapa = $('rest-mapa-texto').value;
    if (!mapa) { mensagem('Escolha o mapa.', true); return; }
    try {
      const r = await api('POST', '/api/restaurar/texto', { texto: $('rest-texto').value, mapa: mapa });
      $('rest-texto-saida').value = r.texto;
      mensagem('Texto restaurado.');
    } catch (e) { mensagem(e.message, true); }
  });

  // --- Configurações -------------------------------------------------------
  async function carregarConfig() {
    try {
      config = await api('GET', '/api/config');
      $('pasta-entrada').textContent = config.pastas.entrada;
    } catch (e) { mensagem(e.message, true); }
  }

  function preencherConfig() {
    if (!config) return;
    $('cfg-base').value = config.pasta_base;
    $('cfg-saida').value = config.pasta_saida;
    $('cfg-mapas').value = config.pasta_mapas;
    $('cfg-formato').value = config.formato;
    $('cfg-tipo').value = config.tipo;
    $('cfg-modo').value = config.modo;
  }

  $('form-config').addEventListener('submit', async (ev) => {
    ev.preventDefault();
    try {
      config = await api('POST', '/api/config', {
        pasta_base: $('cfg-base').value, pasta_saida: $('cfg-saida').value, pasta_mapas: $('cfg-mapas').value,
        formato: $('cfg-formato').value, tipo: $('cfg-tipo').value, modo: $('cfg-modo').value });
      $('pasta-entrada').textContent = config.pastas.entrada;
      mensagem('Configuração salva.');
    } catch (e) { mensagem(e.message, true); }
  });

  // --- Zona de arrastar e soltar, menu, encerrar ---------------------------
  const zona = $('zona');
  zona.addEventListener('dragover', (ev) => { ev.preventDefault(); zona.classList.add('ativa'); });
  zona.addEventListener('dragleave', () => zona.classList.remove('ativa'));
  zona.addEventListener('drop', (ev) => { ev.preventDefault(); zona.classList.remove('ativa'); enviar(ev.dataTransfer.files); });
  zona.addEventListener('click', (ev) => { if (ev.target.tagName !== 'LABEL') $('arquivos').click(); });
  zona.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); $('arquivos').click(); } });
  $('arquivos').addEventListener('change', () => { enviar($('arquivos').files); $('arquivos').value = ''; });
  for (const b of document.querySelectorAll('nav [data-tela]')) b.addEventListener('click', () => mostrar(b.dataset.tela));
  $('encerrar').addEventListener('click', async () => {
    if (!window.confirm('Encerrar o Pseudonimizador? Documentos ainda não gerados serão descartados.')) return;
    try { await api('POST', '/api/encerrar'); } catch (e) { mensagem(e.message, true); return; }
    window.clearInterval(relogio);
    const p = document.createElement('p');
    p.className = 'mensagem';
    p.textContent = 'O Pseudonimizador vai se encerrar assim que terminar o que está fazendo. Pode fechar esta janela.';
    document.body.replaceChildren(p);
  });

  // --- Início --------------------------------------------------------------
  const selCategoria = $('acr-categoria');
  for (const [valor, rotulo] of Object.entries(CATEGORIAS)) {
    const o = document.createElement('option');
    o.value = valor;
    o.textContent = rotulo;
    selCategoria.append(o);
  }
  const relogio = window.setInterval(() => { if (!$('tela-documentos').hidden) atualizarLista(); }, 2000);
  if (!TOKEN) mensagem('Abra o Pseudonimizador pelo atalho: sem o endereço de sessão a janela não funciona.', true);
  api('GET', '/api/estado').then((e) => { $('versao').textContent = e.versao; }).catch(() => {});
  carregarConfig().then(() => mostrar('documentos'));
})();
```

- [ ] **Step 6: Rodar e ver passar**

Run: `$PY -X utf8 testes/test_web_estaticos.py && $PY -X utf8 testes/test_web_servidor.py`
Expected: `4/4 passaram`; `5/5 passaram`.

- [ ] **Step 7: Commit**

```bash
git add pseudonimizador/web/estatico testes/test_web_estaticos.py
git commit -m "Janela: página própria (Documentos/Pendentes, Revisão, Resultado, Restaurar, Configurações), sem nada inline nem externo

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---
### Task 9: Pasta monitorada (`Entrada\` → Pendentes → `Entrada\Processados\`)

**Files:**
- Create: `pseudonimizador/web/pasta_monitorada.py`
- Modify: `pseudonimizador/web/servidor.py` (`Aplicacao.__init__`, `aplicar_config`, `encerrar`)
- Test: `testes/test_pasta_monitorada.py`

**Interfaces:**
- Consumes: `Registro.registrar_arquivo(caminho, "pasta") -> Doc`, `Registro.apos_gerar`, `Doc.origem/caminho/id`; `saida._destino`.
- Produces: `Vigia(registro, pasta_entrada, pasta_processados, log, intervalo_s=2.0)` com `varrer() -> list[Doc]` (uma varredura síncrona; é o que os testes chamam), `iniciar()`, `parar()`, `trocar(pasta_entrada, pasta_processados)`, `processado(doc)`; `Aplicacao` ganha `vigia` e o parâmetro `vigia_pasta_s=2.0`.

- [ ] **Step 1: Escrever o teste (vermelho)**

`testes/test_pasta_monitorada.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Pasta monitorada: arquivo estável vira Pendente; ocultos, ~$ e Processados
ignorados; depois de gerar o original vai para Processados; erro não reprocessa."""
import _base  # noqa: F401
import os
import time

import fabrica as F
from _web import ServidorDeTeste
from pseudonimizador.estado import abrir_log
from pseudonimizador.web.pasta_monitorada import Vigia
from pseudonimizador.web.registro import Registro


def _esperar(condicao, prazo=60.0):
    fim = time.monotonic() + prazo
    while not condicao():
        assert time.monotonic() < fim, "esperou demais"
        time.sleep(0.05)


def _vigia(nome):
    pasta = F.pasta_temporaria(nome)
    log = abrir_log(pasta)
    reg = Registro(pasta / "tmp", log)
    entrada = pasta / "Entrada"
    entrada.mkdir()
    v = Vigia(reg, entrada, entrada / "Processados", log, intervalo_s=0.05)
    reg.apos_gerar = v.processado
    return pasta, reg, entrada, v


def test_arquivo_so_entra_quando_estavel():
    """Review Focus 3: arquivo ainda sendo copiado para a Entrada."""
    pasta, reg, entrada, v = _vigia("pasta_estavel")
    corpo = F.contrato_docx(pasta / "c.docx").read_bytes()
    alvo = entrada / "contrato.docx"
    with open(alvo, "wb") as f:
        f.write(corpo[:200])
        f.flush()
        assert v.varrer() == []                 # primeira vez: só anota
        f.write(corpo[200:])
        f.flush()
        os.utime(alvo, None)
    assert v.varrer() == []                     # mudou desde a última varredura
    novos = v.varrer()                          # igual em duas seguidas: entra
    assert len(novos) == 1 and novos[0].origem == "pasta" and novos[0].nome == "contrato.docx"
    assert v.varrer() == []                     # não entra duas vezes
    _esperar(lambda: novos[0].situacao != "lendo")
    assert novos[0].situacao == "revisao" and reg.lista()[0]["origem"] == "pasta"
    assert reg.encerrar(timeout=5)


def test_ignora_ocultos_temporarios_vazios_e_processados():
    pasta, reg, entrada, v = _vigia("pasta_ignora")
    corpo = F.contrato_docx(pasta / "c.docx").read_bytes()
    (entrada / "~$contrato.docx").write_bytes(corpo)
    (entrada / ".escondido.docx").write_bytes(corpo)
    (entrada / "notas.txt").write_bytes(b"x")
    (entrada / "vazio.pdf").write_bytes(b"")
    (entrada / "Processados").mkdir()
    (entrada / "Processados" / "antigo.docx").write_bytes(corpo)
    (entrada / "outra_pasta").mkdir()
    oculto = entrada / "atributo.docx"
    oculto.write_bytes(corpo)
    os.system(f'attrib +h "{oculto}"')
    assert v.varrer() == [] and v.varrer() == []
    assert reg.lista() == []
    assert reg.encerrar(timeout=5)


def test_depois_de_gerar_o_original_vai_para_processados():
    with ServidorDeTeste("pasta_gerar", vigia_pasta_s=0.05) as s:
        entrada = s.pasta / "Base" / "Entrada"
        F.contrato_docx(entrada / "lote.docx")
        F.contrato_docx(entrada / "Processados" / "lote.docx")      # colisão: o novo ganha " (2)"
        _esperar(lambda: s.get("/api/documentos")[1]["documentos"] != [])
        d = s.get("/api/documentos")[1]["documentos"][0]
        assert d["origem"] == "pasta" and d["nome"] == "lote.docx"
        s.esperar(d["id"], "revisao")
        assert s.post(f"/api/documentos/{d['id']}/gerar", {})[0] == 202
        r = s.esperar(d["id"], "pronto", "erro")
        assert r["situacao"] == "pronto", r["erro"]
        assert (s.pasta / "Base" / "Saida" / "lote - pseudonimizado.docx").is_file()
        assert not (entrada / "lote.docx").exists()
        assert (entrada / "Processados" / "lote (2).docx").is_file()
        # posto de novo na Entrada (é outro arquivo): entra de novo
        F.contrato_docx(entrada / "lote.docx")
        _esperar(lambda: len(s.get("/api/documentos")[1]["documentos"]) == 2)
    log = s.log_texto()
    assert "pasta monitorada" in log and "lote" not in log


def test_erro_de_leitura_fica_na_entrada_sem_reprocessar():
    pasta, reg, entrada, v = _vigia("pasta_erro")
    ruim = entrada / "ruim.docx"
    ruim.write_bytes(b"nao e docx")
    assert v.varrer() == []
    novos = v.varrer()
    assert len(novos) == 1
    _esperar(lambda: novos[0].situacao != "lendo")
    assert novos[0].situacao == "erro" and ruim.exists()
    assert v.varrer() == [] and v.varrer() == []            # não reprocessa até mudar
    ruim.write_bytes(F.contrato_docx(pasta / "c.docx").read_bytes())
    os.utime(ruim, (time.time() + 5, time.time() + 5))
    assert v.varrer() == []
    assert len(v.varrer()) == 1                              # mudou: entra de novo
    assert reg.encerrar(timeout=5)


def test_trocar_de_pasta_e_parar():
    pasta, reg, entrada, v = _vigia("pasta_trocar")
    nova = pasta / "Entrada2"
    nova.mkdir()
    F.contrato_docx(nova / "x.docx")
    v.trocar(nova, nova / "Processados")
    v.iniciar()
    _esperar(lambda: reg.lista() != [], prazo=10)
    assert reg.lista()[0]["nome"] == "x.docx"
    v.parar()
    assert reg.encerrar(timeout=5)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `$PY -X utf8 testes/test_pasta_monitorada.py`
Expected: `ModuleNotFoundError: No module named 'pseudonimizador.web.pasta_monitorada'`.

- [ ] **Step 3: Implementar `pseudonimizador/web/pasta_monitorada.py`**

```python
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
        self.trocar(pasta_entrada, pasta_processados)

    def trocar(self, pasta_entrada: Path, pasta_processados: Path) -> None:
        with self._trava:
            self.pasta_entrada = Path(pasta_entrada)
            self.pasta_processados = Path(pasta_processados)
            self._vistos.clear()
            self._registrados.clear()

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
                doc = self.registro.registrar_arquivo(c, "pasta")
                self._registrados[c] = assinatura
                novos.append(doc)
                self.log.info("pasta monitorada: documento %s registrado", doc.id)
            for c in list(self._vistos):
                if c not in atuais:
                    self._vistos.pop(c, None)
                    self._registrados.pop(c, None)
        return novos

    def processado(self, doc: Doc) -> None:
        """Depois de gerar: o original vai para Processados (colisão → " (2)")."""
        if doc.origem != "pasta":
            return
        with self._trava:
            processados = self.pasta_processados
        try:
            processados.mkdir(parents=True, exist_ok=True)
            destino = _destino(processados, doc.caminho.stem, doc.caminho.suffix)
            shutil.move(str(doc.caminho), str(destino))
        except OSError as e:
            self.log.warning("pasta monitorada: documento %s não foi movido (%s)", doc.id, type(e).__name__)
            return
        with self._trava:
            self._registrados.pop(doc.caminho, None)
            self._vistos.pop(doc.caminho, None)
        self.log.info("pasta monitorada: documento %s movido para Processados", doc.id)
```

- [ ] **Step 4: Ligar a vigia à `Aplicacao`**

Em `pseudonimizador/web/servidor.py`, import `from .pasta_monitorada import Vigia`; a assinatura de `Aplicacao.__init__` ganha `vigia_pasta_s: float = 2.0` (depois de `inatividade_s`), e no fim do `__init__`:
```python
        self.vigia = Vigia(self.registro, self.config.entrada, self.config.processados, self.log, intervalo_s=vigia_pasta_s)
        self.registro.apos_gerar = self.vigia.processado
        self.vigia.iniciar()
```
`aplicar_config` passa a:
```python
    def aplicar_config(self, nova: Config) -> None:
        self.config = nova
        self.vigia.trocar(nova.entrada, nova.processados)
```
E `encerrar` começa com `self.vigia.parar()` antes de `self.registro.encerrar(timeout=600)`.

- [ ] **Step 5: Rodar e ver passar**

Run: `$PY -X utf8 testes/test_pasta_monitorada.py && $PY -X utf8 testes/test_web_config.py`
Expected: `5/5 passaram`; `1/1 passaram`.

- [ ] **Step 6: Commit**

```bash
git add pseudonimizador/web/pasta_monitorada.py pseudonimizador/web/servidor.py testes/test_pasta_monitorada.py
git commit -m "Pasta monitorada: Entrada varrida a cada 2 s, arquivo estável vira Pendente, original vai a Processados após gerar

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---
### Task 10: Abrir a janela — instância única, Edge em modo aplicativo, `python -m pseudonimizador`, `Pseudonimizador.bat`, README

**Files:**
- Create: `pseudonimizador/web/abrir.py`, `Pseudonimizador.bat`
- Modify: `pseudonimizador/__main__.py` (sem subcomando → janela), `pseudonimizador/__init__.py` (`VERSAO = "0.2.0"`), `README.md` (seção "Uso pela janela")
- Test: `testes/test_web_abrir.py` (sozinho), `testes/test_cli.py` (um teste novo)

**Interfaces:**
- Consumes: `web.servidor.Aplicacao`, `web.servidor.Servidor` (`vigiar`, `url`, `serve_forever`, `server_close`), `Aplicacao.porta/segredo/emitir_token/encerrar/log`; `estado.pasta_estado()`; `motor.mapa.escrever_atomico`; `pseudonimizador.VERSAO`.
- Produces: `Mutex(nome)` (`.ja_existia`, `.fechar()`); `processo_vivo(pid) -> bool`; `ler_instancia(pasta) -> dict | None`; `gravar_instancia(pasta, porta, segredo, versao)`; `apagar_instancia_se_nossa(pasta, porta)`; `pedir_token(porta, segredo) -> str | None`; `pedir_encerramento(porta, segredo) -> bool`; `localizar_edge(*, registro=True) -> Path | None`; `abrir_janela_web(url, *, localizar, lancar, navegador) -> str`; `abrir(*, pasta_estado=None, nome_mutex=NOME_MUTEX, abrir_janela=abrir_janela_web, criar_app=None, versao=VERSAO, tentativas=5, espera_s=1.0, vigia_s=2.0, espera_encerrar_s=15.0) -> int`; `avisar_erro(texto, caixa=None)`; `principal() -> int`; `ErroAbertura`.

- [ ] **Step 1: Escrever os testes (vermelhos)**

`testes/test_web_abrir.py`:
```python
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


def test_instancia_de_outra_versao_e_substituida():
    pasta = F.pasta_temporaria("abrir_versao") / "estado"
    nome = f"Pseudonimizador-Teste-{secrets.token_hex(4)}"
    urls = []
    t = threading.Thread(target=A.abrir, kwargs=dict(pasta_estado=pasta, nome_mutex=nome, abrir_janela=urls.append,
                                                     criar_app=_criar_app(60.0), vigia_s=0.1, versao="0.0.1"), daemon=True)
    t.start()
    _esperar(lambda: len(urls) == 1)
    porta_velha = A.ler_instancia(pasta)["porta"]
    # a abertura da versão nova pede à velha que se encerre e sobe no lugar; a nova sai por inatividade
    codigo = A.abrir(pasta_estado=pasta, nome_mutex=nome, abrir_janela=urls.append, criar_app=_criar_app(0.5),
                     vigia_s=0.1, versao=VERSAO)
    assert codigo == 0 and len(urls) == 2
    t.join(5)
    assert not t.is_alive() and A.ler_instancia(pasta) is None
    assert porta_velha > 0


def test_instancia_morta_no_json_nao_bloqueia():
    pasta = F.pasta_temporaria("abrir_morto") / "estado"
    pasta.mkdir(parents=True)
    (pasta / "instancia.json").write_text(json.dumps({"pid": 0, "porta": 1, "segredo": "x", "versao": VERSAO}), encoding="utf-8")
    urls = []
    nome = f"Pseudonimizador-Teste-{secrets.token_hex(4)}"
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
```

Em `testes/test_cli.py`, acrescente antes do bloco `if __name__ == "__main__":`:
```python
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
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `$PY -X utf8 testes/test_web_abrir.py; $PY -X utf8 testes/test_cli.py`
Expected: `ModuleNotFoundError: No module named 'pseudonimizador.web.abrir'`; no CLI, `test_sem_subcomando_abre_a_janela` FALHA (argparse exige o subcomando).

- [ ] **Step 3: Implementar `pseudonimizador/web/abrir.py`**

```python
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
    """Pede à instância viva (de outra versão) que se encerre quando ociosa."""
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
        servidor = Servidor(app, 0)
        gravar_instancia(pasta, app.porta, app.segredo, versao)
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
```

- [ ] **Step 4: Linha de comando sem subcomando, versão, `.bat` e README**

Em `pseudonimizador/__init__.py`: `VERSAO = "0.2.0"`.

Em `pseudonimizador/__main__.py`: a docstring passa a
```python
"""Linha de comando do Pseudonimizador. Sem subcomando, abre a janela.

  (nada)                                abre a janela (servidor local + Edge)
  detectar  ARQ --revisao R.json        detecta e grava a revisão para editar
  gerar     ARQ [--revisao R.json] ...  aplica a revisão e gera a saída
  restaurar ARQ.docx|--texto T.txt ...  devolve os nomes (modo reversível)
"""
```
e em `main`:
```python
    p = argparse.ArgumentParser(prog="pseudonimizador", description=f"Pseudonimizador {VERSAO} — sem subcomando, abre a janela")
    sub = p.add_subparsers(dest="comando", required=False)
```
e, logo depois de `a = p.parse_args(argv)`:
```python
    if a.comando is None:
        from .web import abrir
        return abrir.principal()
```

`Pseudonimizador.bat` (na raiz do repositório; CRLF):
```bat
@echo off
rem Abre a janela do Pseudonimizador sem console. Requer o ambiente .venv (README, "Instalacao").
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Ambiente nao encontrado. Siga a secao "Instalacao" do README.md.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" -X utf8 -m pseudonimizador
```

`README.md`: entre "Instalação" e "Uso pela linha de comando", acrescente:
```markdown
## Uso pela janela

Clique duas vezes em `Pseudonimizador.bat` (ou rode `.venv\Scripts\python -X utf8 -m pseudonimizador`
sem argumentos). A janela abre no Edge em modo aplicativo (sem Edge, no navegador padrão); o
servidor fica só em `127.0.0.1`, numa porta livre, e nada sai do computador.

- **Documentos**: arraste um DOCX ou PDF (até 100 MB) ou escolha os arquivos. Depois da leitura
  (com OCR local, se a página for imagem) o documento fica "aguardando revisão".
- **Revisão**: tudo começa marcado para substituir; desmarque o que deve ficar em claro e acrescente
  o que escapou. Escolha formato (layout original ou só o texto), tipo e modo (reversível ou
  definitivo) e clique em Gerar. Se algum dado continuaria visível na saída, nada é gerado e a
  revisão reabre com a lista.
- **Resultado**: nome do arquivo gerado, avisos, "Abrir arquivo" e "Abrir pasta de saída".
- **Pendentes (pasta Entrada)**: arquivos copiados para `Documents\Pseudonimizador\Entrada`
  (ou a pasta base das Configurações) entram sozinhos na lista; depois de gerados, o original vai
  para `Entrada\Processados`. Os padrões do lote vêm das Configurações.
- **Restaurar nomes**: um DOCX pseudonimizado (o mapa é achado pelo identificador gravado nele) ou
  texto colado com os tókens `[[...]]` e o mapa escolhido na lista.
- **Configurações**: pasta base (com `Entrada`, `Saida` e `Mapas`), pastas de saída e de mapas
  (nunca uma dentro da outra) e os padrões do lote.
- **Encerrar** (no menu) fecha o servidor assim que terminar o que está fazendo; sem uso por 30
  minutos ele também se encerra. Abrir o atalho de novo com o app aberto só abre outra janela.

Estado, configuração e log ficam em `%LOCALAPPDATA%\Pseudonimizador` (`config.json`,
`logs\servidor.log` — sem valores nem nomes de arquivo). Os mapas são dado pessoal: ficam em
`Mapas\`, separados da saída.
```

- [ ] **Step 5: Rodar e ver passar**

Run: `$PY -X utf8 testes/test_web_abrir.py && $PY -X utf8 testes/test_cli.py`
Expected: `7/7 passaram`; `6/6 passaram`.

- [ ] **Step 6: Suíte inteira e guardas**

Run: `$PY -X utf8 testes/executar_todos.py`
Expected: todos os arquivos `ok` (os 33 do Plano 1 + os 10 novos), `test_web_abrir.py` rodando sozinho no fim; `test_licenca`, `test_sem_dados_reais` e `test_sem_rede` verdes. Depois: `$PY -W error -m compileall -q pseudonimizador testes` sem saída.

- [ ] **Step 7: Commit**

```bash
git add pseudonimizador/web/abrir.py pseudonimizador/__main__.py pseudonimizador/__init__.py Pseudonimizador.bat README.md testes/test_web_abrir.py testes/test_cli.py
git commit -m "Abrir a janela: instância única (mutex + instancia.json), Edge em modo aplicativo, pythonw com caixa de erro, Pseudonimizador.bat e README (0.2.0)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Verificação manual opcional (fora dos testes)

Depois da Task 10, com a suíte verde, abra `Pseudonimizador.bat` nesta máquina e confira no Edge (ou no navegador embutido do Claude, apontado para a URL com `#t=` que o `instancia.json` não traz — copie-a do atalho/Edge):

1. Arraste um DOCX sintético (gere um com `testes/fabrica.py`: `F.contrato_docx(Path("saida_testes/manual.docx"))`) — a linha aparece "lendo…" e passa a "aguardando revisão" sem recarregar a página.
2. Revisão: desmarcar o e-mail, acrescentar "Porto Alegre" (categoria Outro), gerar em layout reversível — a tela volta a Documentos e abre o Resultado sozinha; "Abrir pasta de saída" abre o Explorer.
3. Copiar um PDF escaneado sintético para `Entrada\` — aparece em Pendentes em até 4 s; gerar com os padrões; o original vai para `Entrada\Processados`.
4. Restaurar: enviar o DOCX gerado — "Restaurado na pasta de saída"; colar o texto com tókens e escolher o mapa.
5. Configurações: pôr a pasta dos mapas dentro da saída — recusa com a frase; corrigir — "Configuração salva" e `config.json` atualizado.
6. Clicar duas vezes no `.bat` de novo — só outra janela abre; `logs\servidor.log` registra "segunda abertura" e nenhum nome de arquivo. Encerrar pelo menu — a janela avisa e o processo sai; `instancia.json` some.

Nenhum dado real nesta verificação: só os documentos sintéticos de `testes/fabrica.py`.
