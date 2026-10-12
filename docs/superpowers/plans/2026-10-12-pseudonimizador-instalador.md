# Pseudonimizador — Plano 3: instalador para Windows (Pseudonimizador-Setup.exe)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Um único `dist\Pseudonimizador-Setup.exe` (Inno Setup 6, sem administrador) que leva o Python 3.14 embarcável, as bibliotecas de um lock com hashes e o CRT do Visual C++; o instalador pergunta só a "Pasta dos arquivos", chama `python -m pseudonimizador configurar --pasta-base <pasta>` e cria os atalhos; a desinstalação nunca toca a pasta dos arquivos. Fecha com as notas da release `v0.2.0` e um script de conferência pré-publicação (a publicação em si — `gh repo create`, `push`, `release` — fica fora deste plano e é feita pelo controlador).

**Architecture:** `empacotamento/` é um pacote de mantenedor adaptado do empacotamento do Ulpiano (mesmo autor): `manifesto.py` (lista fechada do que viaja), `gerar_lock.py` (rede: PyPI), `construir.py` (rede: python.org; monta `build\app` e compila `dist\`), `fumaca.py` (conferência pós-montagem, rodada PELO Python embarcado, de outra pasta e com a rede bloqueada), `pseudonimizador.iss` (Inno Setup, com a página da pasta e a pergunta da desinstalação em Pascal), `sandbox.wsb.modelo` (aceitação manual no Windows Sandbox) e `verificar_publicacao.py` (suíte, guarda, varredura do histórico, e-mails dos commits, `dist\`). Todo comando externo é injetável; os testes nunca baixam nada nem compilam o Setup.

**Tech Stack:** Python 3.14 x64 (venv `.venv`), Inno Setup 6 (`ISCC.exe`), Python embeddable 3.14 x64 de python.org, pip com `--require-hashes`, CRT do Visual Studio 18 (`Microsoft.VC145.CRT`), Windows Sandbox. Sem pytest (runner próprio `testes/_runner.py`).

**Spec:** `docs/superpowers/specs/2026-10-12-pseudonimizador-instalador-design.md` (§2 montagem, §3 instalador, §4 publicação). Referência adaptada (só leitura): `../AplicativosMauricio/empacotamento/` e `../AplicativosMauricio/testes/test_empacotamento.py`. Decisões vinculantes deste plano, além da spec: a página da pasta é pulada na atualização por cima (se `%LOCALAPPDATA%\Pseudonimizador\config.json` existe) e `configurar` preserva os outros campos da config existente; o `.wsb` gerado tem GPU virtual ligada e **rede desligada** (prova o critério 2 da spec); o `.iss` é gravado em UTF-8 **com BOM** (o ISCC lê assim os acentos); o ícone próprio é gerado por script (`gerar_icone.py`) e o `.ico` resultante é rastreado.

## Global Constraints

- Repositório: `C:\Users\<usuário>\Claude\Pseudonimizador` (esta pasta, ramo `main`, suíte 43/43 verde). O Ulpiano fica na pasta irmã `../AplicativosMauricio` e **não é alterado**: só `empacotamento/` e `testes/test_empacotamento.py` são lidos como referência. Nunca ler `../AplicativosMauricio/empacotamento/publicacao.toml`, nada de `build/`, `dist/`, `_cache/` (além dos nomes) e nada do drive `E:`.
- Python do projeto: `.venv` (Python 3.14 x64). Todos os comandos usam `PY=.venv/Scripts/python` e `-X utf8`, por exemplo `$PY -X utf8 testes/test_empacotamento.py`.
- Dependências do app: `pymupdf==1.28.0`, `python-docx==1.2.0`, `rapidocr==3.9.2`, `onnxruntime==1.24.4` (`requirements.txt` **não muda**). O pacote instalado leva `opencv-python-headless` no lugar de `opencv-python` e fica sem `sympy`/`mpmath` (spec §2); se a fumaça da Task 5 falhar sem eles, a redução é desfeita e registrada (passo próprio da Task 5).
- **Rede só nos scripts de montagem** (`gerar_lock.py` → PyPI; `construir.py` → python.org e PyPI). Nunca no app, nunca nos testes: os testes de `construir.py` e `gerar_lock.py` substituem `baixar`/`executar` por funções falsas. A fumaça pós-montagem bloqueia `socket` como `testes/test_sem_rede.py`.
- Licença: todo `.py` rastreado (inclusive em `empacotamento/`) começa com estas duas linhas, exatamente (sem linha `# -*- coding` antes — o Ulpiano a tem; aqui `test_licenca.py` recusa):
  `# SPDX-License-Identifier: AGPL-3.0-only`
  `# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.`
  `.iss`, `.toml`, `.modelo`, `.md`, `.ico` não levam cabeçalho.
- Autoria: o nome do autor aparece só em `CREDITOS.md` e `README.md`. O empacotamento do Ulpiano é creditado em `CREDITOS.md` (Task 7).
- Sem dado real: nenhum caminho da máquina (`C:\Users\<nome>` — nem mesmo o do Sandbox, `WDAGUtilityAccount`), nome de usuário ou e-mail pessoal em arquivo rastreado; e-mails sintéticos só `@exemplo.com.br`, `@example.com`, `noreply@anthropic.com` ou `<n>+<x>@users.noreply.github.com`. `test_sem_dados_reais.py` varre docs e `.iss`/`.toml` também. Strings que precisam "parecer" dado pessoal nos testes são montadas em tempo de execução por concatenação (ver Task 8).
- `build/`, `dist/`, `empacotamento/_cache/` e `empacotamento/termos_proibidos.txt` no `.gitignore` (Task 1). O `Setup.exe` nunca entra no git.
- Arquivo de teste lento ou que use pasta/porta compartilhada leva `# executar_todos: sozinho` nas 15 primeiras linhas (neste plano: `testes/test_empacotamento.py`, porque, quando `build\app` existe, ele roda a fumaça de verdade com OCR no Python embarcado).
- Comentários, mensagens e commits em português. TDD: teste vermelho primeiro, pelo motivo certo; depois o mínimo.
- Scripts com barra invertida (todo `.py` deste plano, o `.iss`, o `.modelo`): escreva o arquivo com a ferramenta Write, não com heredoc no Bash.
- Nunca matar processo pelo nome (`taskkill /IM python.exe` derruba processo alheio): só o PID que o próprio teste iniciou.
- Um commit por tarefa, terminando com a linha `Co-Authored-By: <modelo que implementa> <noreply@anthropic.com>` (por exemplo `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`). **Nunca `git push`**, nunca `gh repo create`, nunca `gh release`.

## Review Focus

1. **Pasta dos arquivos inválida ou sem permissão de escrita** (caminho relativo, unidade inexistente, pasta só leitura): `configurar` sai com 2 e mensagem `erro:` sem traceback, a config anterior não muda, e o instalador mostra a mensagem e termina a instalação (o app abre e a pasta se escolhe em Configurações). Testes: Task 2 (`test_configurar_preserva_os_outros_campos_e_recusa_caminho_relativo`) e Task 6 (`test_iss_pagina_da_pasta_chama_configurar_e_avisa_se_falhar`).
2. **Atualização por cima com config existente** (o usuário já escolheu outra pasta base e padrões do lote): a página da pasta não aparece, `configurar` não roda, a config fica intacta; e `InstallDelete` limpa só `python` e `pseudonimizador`, nunca `%LOCALAPPDATA%`. Testes: Task 6 (`test_iss_pula_a_pagina_da_pasta_na_atualizacao`, `test_iss_instalacao_nova_limpa_so_as_pastas_do_programa`).
3. **Zip do Python ou wheel adulterado/corrompido** (hash diferente do `python-embarcavel.toml` ou do `requirements.lock`): o build para, o arquivo do cache é apagado, nada vai para `build\app`. Testes: Task 4 (`test_download_com_hash_errado_e_recusado_e_o_arquivo_removido`) e Task 3 (`test_pip_instala_do_lock_com_hashes_sem_dependencias`).
4. **Algo que nunca pode viajar no pacote** (testes, `saida_testes\`, `docs/superpowers`, `config.json`, uma pasta `Mapas\` esquecida na raiz, `termos_proibidos.txt`): o manifesto o exclui ou o acusa e a montagem falha. Teste: Task 1 (`test_manifesto_acusa_o_que_nao_pode_viajar`, `test_manifesto_do_repositorio_real_e_limpo`).
5. **Desinstalação silenciosa ou com "Não"** (padrão): `%LOCALAPPDATA%\Pseudonimizador` fica; `[UninstallDelete]` só tem `{app}`; a pasta dos arquivos nunca aparece em lugar nenhum do `.iss`. Teste: Task 6 (`test_iss_pergunta_de_apagar_dados_padrao_nao_e_silencio_respeitado`).
6. **`termos_proibidos.txt` ausente** na máquina que publica: `verificar_publicacao.py` roda só com os padrões embutidos (e-mail fora dos domínios permitidos, `C:\Users\<nome>`) e avisa que a lista local não existe, sem falhar por isso. Teste: Task 8 (`test_termos_ausentes_usa_so_os_padroes_embutidos`).

---

## Estrutura de arquivos

```
.gitignore                         + build/ dist/ empacotamento/_cache/ empacotamento/termos_proibidos.txt (Task 1)
empacotamento/
  __init__.py                      vazio com cabeçalho SPDX (Task 1)
  manifesto.py                     arquivos_do_pacote(raiz), problemas(relativos) (Task 1)
  gerar_lock.py                    requirements.lock com --hash, headless no lugar do opencv, sem sympy (Task 3)
  python-embarcavel.toml           versao, url, sha256 do Python 3.14.x embeddable (Task 3)
  construir.py                     montar(), fumacar(), gerar_wsb(), main() (Task 4)
  fumaca.py                        roda NO Python embarcado: importa, lê DOCX/PDF/OCR, gera, restaura, sem rede (Task 5)
  gerar_icone.py + pseudonimizador.ico   ícone do Setup e dos atalhos (Task 6)
  pseudonimizador.iss              Inno Setup (UTF-8 com BOM) (Task 6)
  sandbox.wsb.modelo               Windows Sandbox: dist\ só leitura, rede desligada, abre o Setup (Task 6)
  README.md                        roteiro do mantenedor + checklist de aceitação no Sandbox (Task 6)
  verificar_publicacao.py          conferência pré-publicação (Task 8)
requirements.lock                  gerado (Task 3)
pseudonimizador/__main__.py        subcomando configurar --pasta-base (Task 2)
README.md                          "Instalação" (usuário) e "Montar o instalador" (mantenedor) (Task 7)
CREDITOS.md                        crédito do empacotamento do Ulpiano (Task 7)
docs/release-notes/v0.2.0.md       notas da release (Task 7)
testes/
  test_sem_dados_reais.py          + users.noreply.github.com; .ico/.whl/.zip/.exe binários (Task 1)
  test_cli.py                      + testes do configurar (Task 2)
  test_empacotamento.py            manifesto, lock, construir, fumaça, iss, wsb, ícone, README (Tasks 1, 3-7; sozinho)
  test_verificar_publicacao.py     (Task 8)
```

Contratos entre tarefas (nomes exatos; cada tarefa só vê a si mesma):

| Módulo | Produz |
|---|---|
| `empacotamento.manifesto` | `arquivos_do_pacote(raiz: Path) -> list[Path]`; `problemas(relativos: list[Path]) -> list[str]` |
| `empacotamento.gerar_lock` | `EXCLUIDOS`; `nome_e_versao(wheel: Path) -> tuple[str, str]`; `filtrar(wheels, excluidos=EXCLUIDOS) -> list[Path]`; `linhas_do_lock(wheels) -> list[str]`; `problemas_do_lock(nomes: set[str]) -> list[str]`; `main(argv=None, *, baixar=_baixar_padrao) -> int` |
| `empacotamento.construir` | `SERIE = "3.14"`; `CRT`, `CRT_OBRIGATORIAS`, `ISCC_PADRAO`, `FUMACA`; `ler_python_embarcavel(toml) -> dict`; `conteudo_pth() -> str`; `argumentos_pip(lock, destino) -> list[str]`; `nomes_do_crt()`; `localizar_crt(candidatos) -> Path|None`; `candidatos_crt(sistema=False) -> list[Path]`; `localizar_iscc(explicito: Path|None) -> Path|None`; `argumentos_iscc(iscc, iss, *, versao, origem, saida) -> list[str]`; `_baixar_padrao(url, destino, sha256) -> Path`; `_executar_padrao(args, **kw) -> int`; `montar(raiz, build, *, executar, baixar, crt=None, fumaca=True, crt_do_sistema=False) -> Path`; `fumacar(app, *, executar)`; `gerar_wsb(modelo, dist) -> str`; `main(argv=None) -> int` |
| `pseudonimizador.__main__` | subcomando `configurar --pasta-base PASTA` (0 ok; 2 erro) |
| `empacotamento.verificar_publicacao` | `email_permitido(email) -> bool`; `carregar_termos(caminho) -> list[str]`; `varrer(texto, termos) -> list[str]`; `emails_fora_do_github(linhas) -> list[str]`; `conferir_dist(dist) -> list[str]`; `main(argv=None, *, executar=subprocess.run) -> int` |

---

### Task 1: Guardas, `.gitignore` e o manifesto do pacote

**Files:**
- Modify: `.gitignore`
- Modify: `testes/test_sem_dados_reais.py:10-11`
- Create: `empacotamento/__init__.py`, `empacotamento/manifesto.py`
- Test: `testes/test_empacotamento.py`

**Interfaces:**
- Consumes: nada.
- Produces: `empacotamento.manifesto.arquivos_do_pacote(raiz: Path) -> list[Path]` (relativos, ordenados, só existentes); `empacotamento.manifesto.problemas(relativos: list[Path]) -> list[str]` (vazio = ok).

- [ ] **Step 1: `.gitignore` e a guarda de dados reais**

Acrescente ao fim de `.gitignore`:
```
build/
dist/
empacotamento/_cache/
empacotamento/termos_proibidos.txt
```

Em `testes/test_sem_dados_reais.py`, troque as duas constantes:
```python
DOMINIOS_PERMITIDOS = ("exemplo.com.br", "example.com", "anthropic.com", "users.noreply.github.com")
BINARIOS = (".json", ".png", ".jpg", ".pdf", ".docx", ".onnx", ".ico", ".whl", ".zip", ".exe")
```

Run: `.venv/Scripts/python -X utf8 testes/test_sem_dados_reais.py`
Expected: `1/1 passaram`.

- [ ] **Step 2: Escrever o teste do manifesto (vermelho)**

`testes/test_empacotamento.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
# executar_todos: sozinho
"""Empacotamento: manifesto, lock, montagem (comandos externos falsos), fumaça,
pseudonimizador.iss, .wsb, ícone e roteiro. Nada aqui baixa nem compila.
Roda sozinho porque, quando build/app existe, a fumaça de verdade faz OCR."""
import _base  # noqa: F401
import tempfile
from pathlib import Path

from _base import RAIZ
from empacotamento import manifesto


def _arvore(tmp: Path, caminhos: list[str]) -> Path:
    for c in caminhos:
        p = tmp / c
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")
    return tmp


def test_manifesto_leva_o_aplicativo_e_deixa_o_que_e_do_mantenedor():
    with tempfile.TemporaryDirectory() as d:
        raiz = _arvore(Path(d), [
            "LICENSE", "CREDITOS.md", "README.md", "Pseudonimizador.bat", "requirements.txt", "requirements.lock",
            "pseudonimizador/__init__.py", "pseudonimizador/motor/lexico_ibge.json",
            "pseudonimizador/web/estatico/app.js", "pseudonimizador/__pycache__/x.pyc",
            "testes/test_x.py", "saida_testes/cli/contrato.docx", "docs/superpowers/plans/p.md",
            "docs/release-notes/v0.2.0.md", ".git/HEAD", ".claude/settings.json",
            "empacotamento/construir.py", "empacotamento/termos_proibidos.txt", "build/app/x", "dist/x.exe",
            "pseudonimizador/config.json", "pseudonimizador/instancia.json", "pseudonimizador/x.log"])
        rel = {p.as_posix() for p in manifesto.arquivos_do_pacote(raiz)}
    assert {"LICENSE", "CREDITOS.md", "README.md", "pseudonimizador/__init__.py",
            "pseudonimizador/motor/lexico_ibge.json", "pseudonimizador/web/estatico/app.js"} <= rel
    for fora in ("Pseudonimizador.bat", "requirements.txt", "requirements.lock", "pseudonimizador/__pycache__/x.pyc",
                 "testes/test_x.py", "saida_testes/cli/contrato.docx", "docs/superpowers/plans/p.md",
                 "docs/release-notes/v0.2.0.md", ".git/HEAD", ".claude/settings.json", "empacotamento/construir.py",
                 "empacotamento/termos_proibidos.txt", "build/app/x", "dist/x.exe", "pseudonimizador/config.json",
                 "pseudonimizador/instancia.json", "pseudonimizador/x.log"):
        assert fora not in rel, fora


def test_manifesto_acusa_o_que_nao_pode_viajar():
    probs = manifesto.problemas([Path("pseudonimizador/a.py"), Path("docs/superpowers/x.md"),
                                 Path("saida_testes/a/b.docx"), Path("Mapas/MAPA-1.json"),
                                 Path("empacotamento/termos_proibidos.txt"), Path("pseudonimizador/config.json")])
    assert len(probs) == 5, probs
    assert manifesto.problemas([Path("pseudonimizador/motor/mapa.py"), Path("LICENSE")]) == []   # "mapa.py" é código


def test_manifesto_do_repositorio_real_e_limpo():
    rel = manifesto.arquivos_do_pacote(RAIZ)
    assert Path("pseudonimizador/__init__.py") in rel and Path("LICENSE") in rel and Path("CREDITOS.md") in rel
    assert Path("pseudonimizador/motor/lexico_ibge.json") in rel
    assert manifesto.problemas(rel) == []
    assert not any(p.parts[0] in ("testes", "saida_testes", "docs", "empacotamento") for p in rel)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```

- [ ] **Step 3: Rodar para ver falhar**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py`
Expected: `ModuleNotFoundError: No module named 'empacotamento'`.

- [ ] **Step 4: Criar o pacote e o manifesto**

`empacotamento/__init__.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Montagem do Pseudonimizador-Setup.exe (só o mantenedor usa). Adaptado do
empacotamento do Ulpiano, do mesmo autor (ver CREDITOS.md)."""
```

`empacotamento/manifesto.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""O que entra no pacote instalado em {app} (spec §2): o código (pseudonimizador/,
com os .json do léxico e os estáticos da janela), LICENSE, CREDITOS.md e README.md.
Não entra: testes, saída de testes, docs, .bat, requirements, empacotamento,
caches, config/instância/log de uma execução, qualquer mapa ou documento."""
from __future__ import annotations

from pathlib import Path

# (pasta ou arquivo relativo à raiz, recursivo?)
INCLUIR: tuple[tuple[str, bool], ...] = (("LICENSE", False), ("CREDITOS.md", False), ("README.md", False),
                                         ("pseudonimizador", True))
PASTAS_EXCLUIDAS = frozenset({"__pycache__", ".git", ".claude", "testes", "saida_testes"})
SUFIXOS_EXCLUIDOS = frozenset({".pyc", ".pyo", ".bat", ".log", ".pdf", ".docx", ".tmp", ".bak"})
NOMES_EXCLUIDOS = frozenset({"config.json", "instancia.json", ".env"})
# o que, se aparecer na lista final, é erro da montagem (nunca viaja); comparado ao caminho POSIX com "/" nas pontas
PROIBIDOS_NO_CAMINHO = ("/superpowers/", "/saida_testes/", "/Mapas/", "/Entrada/", "/Saida/", "/termos_proibidos.txt",
                        "/config.json", "/instancia.json", "/revisao.json")


def _aceito(rel: Path) -> bool:
    if any(parte in PASTAS_EXCLUIDAS for parte in rel.parts[:-1]):
        return False
    return rel.suffix.lower() not in SUFIXOS_EXCLUIDOS and rel.name not in NOMES_EXCLUIDOS


def arquivos_do_pacote(raiz: Path) -> list[Path]:
    """Caminhos relativos a `raiz`, ordenados, só os que existem."""
    raiz = Path(raiz)
    achados: set[Path] = set()
    for entrada, recursivo in INCLUIR:
        alvo = raiz / entrada
        if not alvo.exists():
            continue
        if alvo.is_file():
            achados.add(Path(entrada))
            continue
        for p in (alvo.rglob("*") if recursivo else alvo.glob("*")):
            if p.is_file():
                rel = p.relative_to(raiz)
                if _aceito(rel):
                    achados.add(rel)
    return sorted(achados, key=lambda p: p.as_posix())


def problemas(relativos: list[Path]) -> list[str]:
    """Uma mensagem por arquivo que nunca pode viajar (lista vazia = ok)."""
    saida = []
    for rel in relativos:
        texto = "/" + Path(rel).as_posix()
        for proibido in PROIBIDOS_NO_CAMINHO:
            if proibido in texto:
                saida.append(f"não pode entrar no pacote: {texto[1:]} (contém '{proibido.strip('/')}')")
                break
    return saida
```

- [ ] **Step 5: Rodar os testes**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py && .venv/Scripts/python -X utf8 testes/test_licenca.py && .venv/Scripts/python -X utf8 testes/test_sem_dados_reais.py`
Expected: `3/3 passaram`, `4/4 passaram`, `1/1 passaram`.

- [ ] **Step 6: Commit**

```bash
git add .gitignore testes/test_sem_dados_reais.py empacotamento/__init__.py empacotamento/manifesto.py testes/test_empacotamento.py
git commit -m "Empacotamento: manifesto do pacote, .gitignore de build/dist e guarda com o e-mail privado do GitHub

Co-Authored-By: <modelo que implementa> <noreply@anthropic.com>"
```

---

### Task 2: Subcomando `configurar --pasta-base` na CLI

**Files:**
- Modify: `pseudonimizador/__main__.py` (docstring, `_configurar`, parser, despacho)
- Test: `testes/test_cli.py`

**Interfaces:**
- Consumes: `pseudonimizador.estado.pasta_estado() -> Path`, `carregar(pasta_estado) -> Config`, `validar(dados: dict) -> Config` (ValueError), `gravar(pasta_estado, config)`, `preparar_pastas(config)`.
- Produces: `python -X utf8 -m pseudonimizador configurar --pasta-base PASTA` — grava `config.json` em `estado.pasta_estado()` (preservando os outros campos da config existente), cria `Entrada\`, `Entrada\Processados\`, `Saida\`, `Mapas\`; sai 0; erro de validação/escrita sai 2 com `erro: ...` em stderr. O instalador (Task 6) chama exatamente isso.

- [ ] **Step 1: Escrever os testes (vermelho)**

Em `testes/test_cli.py`, acrescente `import os` aos imports e, antes do bloco `if __name__`:
```python
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
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `.venv/Scripts/python -X utf8 testes/test_cli.py`
Expected: as duas novas FALHAM (`returncode == 2` com "invalid choice: 'configurar'").

- [ ] **Step 3: Implementar**

Em `pseudonimizador/__main__.py`: na docstring, acrescente a linha
```
  configurar --pasta-base PASTA         grava a pasta dos arquivos e cria Entrada, Saida e Mapas (o instalador usa)
```
Acrescente, depois de `_restaurar`:
```python
def _configurar(a) -> int:
    """Grava a pasta dos arquivos na config (mantendo os outros campos, se já havia
    config) e cria as pastas. O instalador chama isto ao terminar."""
    from dataclasses import asdict
    from . import estado
    pasta = estado.pasta_estado()
    dados = asdict(estado.carregar(pasta))
    dados["pasta_base"] = str(a.pasta_base)
    cfg = estado.validar(dados)
    pasta.mkdir(parents=True, exist_ok=True)
    estado.gravar(pasta, cfg)
    estado.preparar_pastas(cfg)
    print(f"pasta dos arquivos: {cfg.pasta_base}")
    return 0
```
No `main`, depois do parser `r` (restaurar):
```python
    c = sub.add_parser("configurar", help="grava a pasta dos arquivos (o instalador usa)")
    c.add_argument("--pasta-base", type=Path, required=True)
```
e no despacho troque o dicionário por:
```python
        return {"detectar": _detectar, "gerar": _gerar, "restaurar": _restaurar,
                "configurar": _configurar}[a.comando](a)
```

- [ ] **Step 4: Rodar os testes**

Run: `.venv/Scripts/python -X utf8 testes/test_cli.py`
Expected: `8/8 passaram`.

- [ ] **Step 5: Commit**

```bash
git add pseudonimizador/__main__.py testes/test_cli.py
git commit -m "CLI: subcomando configurar --pasta-base (grava a config e cria as pastas; o instalador usa)

Co-Authored-By: <modelo que implementa> <noreply@anthropic.com>"
```

---

### Task 3: `gerar_lock.py`, `requirements.lock` e `python-embarcavel.toml`

**Files:**
- Create: `empacotamento/gerar_lock.py`, `empacotamento/python-embarcavel.toml`, `requirements.lock` (gerado)
- Test: `testes/test_empacotamento.py`

**Interfaces:**
- Consumes: `requirements.txt`.
- Produces: `empacotamento.gerar_lock.EXCLUIDOS`, `nome_e_versao(wheel) -> (nome, versao)`, `filtrar(wheels, excluidos=EXCLUIDOS) -> list[Path]`, `linhas_do_lock(wheels) -> list[str]`, `problemas_do_lock(nomes: set[str]) -> list[str]`, `main(argv=None, *, baixar=_baixar_padrao) -> int` onde `baixar(destino: Path, argumentos: list[str]) -> None` roda `pip download` com esses argumentos; `requirements.lock` (instalado pela Task 4 com `--no-deps --require-hashes`); `python-embarcavel.toml` com `versao`, `url`, `sha256`.

- [ ] **Step 1: Escrever os testes (vermelho)**

Acrescente a `testes/test_empacotamento.py` (antes do `if __name__`):
```python
from empacotamento import gerar_lock  # noqa: E402


def test_lock_troca_o_opencv_pelo_headless_e_tira_o_sympy():
    wheels = [Path(n) for n in ("opencv_python-5.0.0.93-cp37-abi3-win_amd64.whl",
                                "opencv_python_headless-5.0.0.93-cp37-abi3-win_amd64.whl",
                                "sympy-1.14.0-py3-none-any.whl", "mpmath-1.3.0-py3-none-any.whl",
                                "onnxruntime-1.24.4-cp314-cp314-win_amd64.whl", "numpy-2.5.4-cp314-cp314-win_amd64.whl")]
    assert gerar_lock.nome_e_versao(wheels[0]) == ("opencv-python", "5.0.0.93")
    restantes = [w.name for w in gerar_lock.filtrar(wheels)]
    assert "opencv_python-5.0.0.93-cp37-abi3-win_amd64.whl" not in restantes
    assert not any(w.startswith(("sympy-", "mpmath-")) for w in restantes)
    assert "opencv_python_headless-5.0.0.93-cp37-abi3-win_amd64.whl" in restantes and len(restantes) == 3
    assert gerar_lock.problemas_do_lock({"onnxruntime", "opencv-python-headless"}) == []
    assert gerar_lock.problemas_do_lock({"onnxruntime", "opencv-python"})            # faltou o headless, sobrou o cheio
    assert gerar_lock.problemas_do_lock({"onnxruntime", "opencv-python-headless", "sympy"})


def test_lock_tem_hash_por_wheel_e_e_gerado_sem_rede_com_baixar_falso():
    import hashlib
    with tempfile.TemporaryDirectory() as d:
        a = Path(d) / "numpy-2.5.4-cp314-cp314-win_amd64.whl"
        a.write_bytes(b"roda falsa")
        linhas = gerar_lock.linhas_do_lock([a])
        assert linhas[0] == "numpy==2.5.4 \\" and linhas[1] == f"    --hash=sha256:{hashlib.sha256(b'roda falsa').hexdigest()}"
        raiz = Path(d) / "repo"
        raiz.mkdir()
        (raiz / "requirements.txt").write_text("rapidocr==3.9.2\n", encoding="utf-8")
        chamadas = []

        def baixar(destino, argumentos):
            chamadas.append(argumentos)
            if "-r" in argumentos:
                for n in ("opencv_python-5.0.0.93-cp37-abi3-win_amd64.whl", "rapidocr-3.9.2-py3-none-any.whl",
                          "onnxruntime-1.24.4-cp314-cp314-win_amd64.whl", "sympy-1.14.0-py3-none-any.whl"):
                    (destino / n).write_bytes(b"x")
            else:
                (destino / "opencv_python_headless-5.0.0.93-cp37-abi3-win_amd64.whl").write_bytes(b"y")
        assert gerar_lock.main(["--raiz", str(raiz)], baixar=baixar) == 0
        texto = (raiz / "requirements.lock").read_text(encoding="utf-8")
    assert "opencv-python-headless==5.0.0.93" in texto and "opencv-python==" not in texto and "sympy" not in texto
    assert texto.count("--hash=sha256:") == 3 and "NÃO editar" in texto
    assert chamadas[1][:2] == ["--no-deps", "opencv-python-headless==5.0.0.93"]   # a mesma versão do wheel cheio


def test_requirements_lock_do_repositorio_esta_coerente():
    texto = (RAIZ / "requirements.lock").read_text(encoding="utf-8")
    pacotes = [l.split("==")[0] for l in texto.splitlines() if "==" in l]
    assert {"pymupdf", "python-docx", "rapidocr", "onnxruntime", "numpy", "opencv-python-headless"} <= set(pacotes)
    assert len(pacotes) == texto.count("--hash=sha256:"), "todo pacote do lock leva o seu hash"
    assert "opencv-python==" not in texto
    # Se a Task 5 desfizer a redução (fumaça falhou sem sympy), retire a linha abaixo e diga o motivo no commit.
    assert "sympy" not in texto


def test_python_embarcavel_tem_versao_url_e_hash():
    from empacotamento import construir
    d = construir.ler_python_embarcavel(RAIZ / "empacotamento" / "python-embarcavel.toml")
    assert d["versao"].startswith("3.14.") and d["url"] == f"https://www.python.org/ftp/python/{d['versao']}/python-{d['versao']}-embed-amd64.zip"
    assert len(d["sha256"]) == 64 and int(d["sha256"], 16) > 0 and d["sha256"] != "0" * 64
```
(`test_python_embarcavel_tem_versao_url_e_hash` só passa na Task 4, quando `construir.ler_python_embarcavel` existir; deixe-o vermelho por esse motivo até lá.)

- [ ] **Step 2: Rodar para ver falhar**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py`
Expected: `ImportError: cannot import name 'gerar_lock'`.

- [ ] **Step 3: Escrever `gerar_lock.py`**

`empacotamento/gerar_lock.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Gera requirements.lock (com --hash=sha256) para Python 3.14 x64 Windows.

Uso (na raiz do repositório, com internet — este é um dos dois únicos scripts
do projeto que usam a rede; o app e os testes nunca):
    .venv\\Scripts\\python -X utf8 empacotamento/gerar_lock.py

1. pip download de requirements.txt (só wheels, para o interpretador que roda);
2. tira o opencv-python (o rapidocr o declara) e baixa, na MESMA versão,
   o opencv-python-headless (sem GUI: menos 30 MB); tira sympy e mpmath
   (dependência declarada do onnxruntime que o OCR não usa ao rodar) —
   spec §2; a fumaça da montagem prova que o OCR funciona sem eles;
3. escreve requirements.lock: nome==versao --hash=sha256:... (instalado com
   --no-deps --require-hashes, por isso a lista é fechada).
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RE_WHEEL = re.compile(r"^(?P<nome>[^-]+)-(?P<versao>[^-]+)-.+\.whl$")
EXCLUIDOS = frozenset({"opencv-python", "sympy", "mpmath"})
SUBSTITUTO = "opencv-python-headless"


def nome_e_versao(wheel: Path) -> tuple[str, str]:
    m = RE_WHEEL.match(Path(wheel).name)
    if m is None:
        raise SystemExit(f"nome de wheel inesperado: {Path(wheel).name}")
    return m.group("nome").lower().replace("_", "-"), m.group("versao")


def filtrar(wheels: list[Path], excluidos: frozenset[str] = EXCLUIDOS) -> list[Path]:
    return [w for w in wheels if nome_e_versao(w)[0] not in excluidos]


def linhas_do_lock(wheels: list[Path]) -> list[str]:
    linhas = []
    for w in sorted(wheels, key=lambda p: p.name.lower()):
        nome, versao = nome_e_versao(w)
        linhas.append(f"{nome}=={versao} \\")
        linhas.append(f"    --hash=sha256:{hashlib.sha256(Path(w).read_bytes()).hexdigest()}")
    return linhas


def problemas_do_lock(nomes: set[str]) -> list[str]:
    probs = []
    if SUBSTITUTO not in nomes:
        probs.append(f"o lock não tem {SUBSTITUTO}")
    for n in sorted(nomes & EXCLUIDOS):
        probs.append(f"o lock ainda tem {n}")
    return probs


def _baixar_padrao(destino: Path, argumentos: list[str]) -> None:
    subprocess.run([sys.executable, "-m", "pip", "download", "-q", "-d", str(destino), "--only-binary=:all:",
                    *argumentos], check=True)


def main(argv=None, *, baixar=_baixar_padrao) -> int:
    ap = argparse.ArgumentParser(description="gera requirements.lock com hashes para o Python embarcado")
    ap.add_argument("--raiz", type=Path, default=RAIZ)
    args = ap.parse_args(argv)
    x64 = struct.calcsize("P") == 8
    if sys.version_info[:2] != (3, 14) or sys.platform != "win32" or not x64:
        print(f"Rode com o Python 3.14 x64 do Windows (este é {sys.version.split()[0]} em {sys.platform}).")
        return 2
    with tempfile.TemporaryDirectory() as td:
        pasta = Path(td)
        baixar(pasta, ["-r", str(args.raiz / "requirements.txt")])
        wheels = sorted(pasta.glob("*.whl"))
        versoes = dict(nome_e_versao(w) for w in wheels)
        if "opencv-python" in versoes and SUBSTITUTO not in versoes:
            baixar(pasta, ["--no-deps", f"{SUBSTITUTO}=={versoes['opencv-python']}"])
            wheels = sorted(pasta.glob("*.whl"))
        wheels = filtrar(wheels)
        if probs := problemas_do_lock({nome_e_versao(w)[0] for w in wheels}):
            print("\n".join(probs))
            return 2
        linhas = ["# Gerado por empacotamento/gerar_lock.py — NÃO editar à mão.",
                  "# Python 3.14 x64 Windows. Instalar com:",
                  "#   python -m pip install --no-deps --require-hashes -r requirements.lock",
                  ""] + linhas_do_lock(wheels)
        (args.raiz / "requirements.lock").write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")
        print(f"requirements.lock: {len(wheels)} pacotes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Gerar o lock de verdade (rede: PyPI)**

Run: `.venv/Scripts/python -X utf8 empacotamento/gerar_lock.py`
Expected: `requirements.lock: N pacotes` (N em torno de 22). Abra `requirements.lock` e confira: tem `opencv-python-headless==5.0.0.93` (a mesma versão do `opencv-python` do `.venv`), não tem `opencv-python==`, `sympy` nem `mpmath`; todo wheel é `cp314` ou `py3-none-any`/`abi3`. Se o PyPI não tiver `opencv-python-headless` nessa versão exata, o `pip download` falha: anote a versão que existe e rode de novo com `requirements.txt` intocado — o script baixa a mesma versão do wheel cheio; nesse caso raro, pinne o `opencv-python` em `requirements.txt` numa versão que tenha o headless correspondente e registre no commit.

- [ ] **Step 5: `python-embarcavel.toml` — procurar a versão atual na python.org**

Abra `https://www.python.org/downloads/windows/`, localize a última versão **3.14.x** e o link "Windows embeddable package (64-bit)" (`python-3.14.x-embed-amd64.zip`). Pegue o SHA-256 na página da release (`https://www.python.org/downloads/release/python-314x/`, tabela "Files"); se a tabela só mostrar MD5, baixe o zip para `empacotamento/_cache/` (ignorado pelo git) e calcule `certutil -hashfile empacotamento\_cache\python-3.14.x-embed-amd64.zip SHA256`, anotando no comentário do `.toml` que o hash veio do download por HTTPS. Escreva `empacotamento/python-embarcavel.toml` com os valores encontrados (abaixo, `3.14.x` e o hash são os que você achou — não deixe o texto literal):
```toml
# empacotamento/python-embarcavel.toml — o Python que viaja no instalador (spec §2).
# Troque os três campos juntos; o sha256 é o publicado em python.org para
# "Windows embeddable package (64-bit)" (ou calculado do download por HTTPS,
# anotando aqui a data). construir.py recusa o zip se não bater.
versao = "3.14.x"
url = "https://www.python.org/ftp/python/3.14.x/python-3.14.x-embed-amd64.zip"
sha256 = "<64 hexadecimais>"
```

- [ ] **Step 6: Rodar os testes**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py`
Expected: tudo passa, menos `test_python_embarcavel_tem_versao_url_e_hash` (falha por `cannot import name 'construir'` — vem na Task 4).

- [ ] **Step 7: Commit**

```bash
git add empacotamento/gerar_lock.py empacotamento/python-embarcavel.toml requirements.lock testes/test_empacotamento.py
git commit -m "Empacotamento: requirements.lock com hashes (headless no lugar do opencv, sem sympy) e o Python 3.14 embarcável

Co-Authored-By: <modelo que implementa> <noreply@anthropic.com>"
```

---

### Task 4: `construir.py` — a montagem de `build\app` (comandos injetáveis)

**Files:**
- Create: `empacotamento/construir.py`
- Test: `testes/test_empacotamento.py`

**Interfaces:**
- Consumes: `empacotamento.manifesto.arquivos_do_pacote`, `problemas`; `requirements.lock`; `python-embarcavel.toml`; `pseudonimizador.VERSAO`.
- Produces: tudo listado na tabela de contratos para `empacotamento.construir`. `montar()` deixa `build\app\python\` (Python embarcado + `python314._pth` + `Lib\site-packages` + DLLs do CRT), `build\app\pseudonimizador\`, `LICENSE`, `CREDITOS.md`, `README.md`, `pseudonimizador.ico` e, com `fumaca=True`, roda `fumacar()` (Task 5). `main()` compila com o ISCC e escreve `dist\Pseudonimizador-Setup.exe`, `dist\SHA256SUMS.txt`, `dist\Pseudonimizador-Sandbox.wsb` (o `.iss`, o `.modelo` e o `.ico` vêm na Task 6; até lá `main()` só funciona com `--so-montar`).

- [ ] **Step 1: Escrever os testes (vermelho)**

Acrescente a `testes/test_empacotamento.py`:
```python
import io  # noqa: E402
import sys  # noqa: E402
import zipfile  # noqa: E402

from empacotamento import construir  # noqa: E402


def _zip_python_falso() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("python.exe", b"MZ")
        z.writestr("pythonw.exe", b"MZ")
        z.writestr("python314.dll", b"MZ")
        z.writestr("python314._pth", "python314.zip\n.\n#import site\n")
    return buf.getvalue()


def _repo_falso(tmp: Path, *, icone: bool = True) -> Path:
    raiz = tmp / "repo"
    for c in ("LICENSE", "CREDITOS.md", "README.md", "pseudonimizador/__init__.py", "pseudonimizador/web/estatico/app.js",
              "requirements.lock", "testes/test_x.py", "saida_testes/x.docx"):
        (raiz / c).parent.mkdir(parents=True, exist_ok=True)
        (raiz / c).write_text("x", encoding="utf-8")
    (raiz / "pseudonimizador" / "__init__.py").write_text('VERSAO = "0.2.0"\n', encoding="utf-8")
    (raiz / "empacotamento").mkdir()
    (raiz / "empacotamento" / "python-embarcavel.toml").write_text(
        'versao = "3.14.0"\nurl = "https://www.python.org/ftp/python/3.14.0/python-3.14.0-embed-amd64.zip"\n'
        'sha256 = "' + "0" * 64 + '"\n', encoding="utf-8")
    if icone:
        (raiz / "empacotamento" / "pseudonimizador.ico").write_bytes(b"\x00\x00\x01\x00")
    return raiz


def test_pth_poe_o_app_e_o_site_packages_no_caminho():
    linhas = construir.conteudo_pth().splitlines()
    assert linhas == ["python314.zip", ".", "..", "Lib\\site-packages"]
    assert "import site" not in construir.conteudo_pth()   # senão entra o site-packages do usuário no sys.path


def test_pip_instala_do_lock_com_hashes_sem_dependencias():
    args = construir.argumentos_pip(Path("requirements.lock"), Path("build/app/python/Lib/site-packages"))
    assert args[:4] == [sys.executable, "-m", "pip", "install"]
    for flag in ("--no-deps", "--require-hashes", "--only-binary=:all:", "--python-version", "3.14", "--platform",
                 "win_amd64", "--implementation", "cp", "--abi", "cp314", "--target"):
        assert flag in args, flag
    assert args[args.index("-r") + 1] == "requirements.lock"


def test_crt_app_local_tem_as_dlls_do_onnxruntime():
    with tempfile.TemporaryDirectory() as d:
        assert {"msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll", "msvcp140_1.dll"} <= set(construir.nomes_do_crt())
        vazia, cheia = Path(d) / "a", Path(d) / "b"
        cheia.mkdir()
        for n in construir.nomes_do_crt():
            (cheia / n).write_bytes(b"MZ")
        assert construir.localizar_crt([vazia, cheia]) == cheia and construir.localizar_crt([vazia]) is None


def test_crt_do_system32_so_com_a_flag_explicita():
    assert not any(p.name.lower() == "system32" for p in construir.candidatos_crt())
    assert construir.candidatos_crt(sistema=True)[-1].name.lower() == "system32"
    with tempfile.TemporaryDirectory() as d:
        raiz = _repo_falso(Path(d))
        original = construir.candidatos_crt
        construir.candidatos_crt = lambda sistema=False: []
        try:
            construir.montar(raiz, Path(d) / "build", executar=lambda *a, **k: 0,
                             baixar=lambda url, destino, sha: (destino.write_bytes(_zip_python_falso()), destino)[1],
                             fumaca=False)
        except SystemExit as e:
            assert "--crt" in str(e) and "--crt-do-sistema" in str(e) and "não publique" in str(e), e
        else:
            raise AssertionError("sem CRT e sem a flag deveria falhar")
        finally:
            construir.candidatos_crt = original


def test_montagem_com_comandos_falsos_produz_a_arvore():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        raiz = _repo_falso(tmp)
        crt = tmp / "crt"
        crt.mkdir()
        for n in construir.nomes_do_crt():
            (crt / n).write_bytes(b"MZ")
        chamadas = []

        def executar(args, **kw):
            chamadas.append(list(args))
            if "pip" in args:
                Path(args[args.index("--target") + 1]).mkdir(parents=True, exist_ok=True)
            return 0

        def baixar(url, destino, sha256):
            assert url.endswith("python-3.14.0-embed-amd64.zip") and destino.name == "python-3.14.0-embed-amd64.zip"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(_zip_python_falso())
            return destino
        app = construir.montar(raiz, tmp / "build", executar=executar, baixar=baixar, crt=crt, fumaca=False)
        assert app == tmp / "build" / "app"
        assert (app / "python" / "python.exe").is_file() and (app / "python" / "msvcp140.dll").is_file()
        assert (app / "python" / "python314._pth").read_text(encoding="utf-8") == construir.conteudo_pth()
        assert (app / "python" / "Lib" / "site-packages").is_dir()
        assert (app / "pseudonimizador" / "__init__.py").is_file() and (app / "LICENSE").is_file()
        assert (app / "pseudonimizador.ico").is_file()
        assert not (app / "requirements.lock").exists() and not (app / "testes").exists()
        assert sum("pip" in c for c in chamadas) == 1 and not any("fumaca" in " ".join(c) for c in chamadas)


class _RespostaFalsa:
    def __init__(self, dados: bytes):
        self._dados = dados

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._dados


def _com_urlopen_falso(resposta: bytes, fn):
    chamadas = []
    original = construir.urllib.request.urlopen

    def falso(url, timeout=None):
        chamadas.append(url)
        return _RespostaFalsa(resposta)
    construir.urllib.request.urlopen = falso
    try:
        fn(chamadas)
    finally:
        construir.urllib.request.urlopen = original


def test_download_com_hash_errado_e_recusado_e_o_arquivo_removido():
    import hashlib
    with tempfile.TemporaryDirectory() as d:
        destino = Path(d) / "_cache" / "python.zip"
        esperado = hashlib.sha256(b"o zip oficial").hexdigest()

        def corpo(chamadas):
            try:
                construir._baixar_padrao("https://www.python.org/x/python.zip", destino, esperado)
            except SystemExit as e:
                assert "não bate" in str(e) and esperado in str(e)
            else:
                raise AssertionError("hash errado deveria dar SystemExit")
            assert chamadas == ["https://www.python.org/x/python.zip"] and not destino.exists()
        _com_urlopen_falso(b"zip adulterado", corpo)


def test_cache_com_o_hash_certo_nao_baixa_de_novo():
    import hashlib
    with tempfile.TemporaryDirectory() as d:
        destino = Path(d) / "python.zip"
        destino.write_bytes(b"o zip oficial")
        esperado = hashlib.sha256(b"o zip oficial").hexdigest()

        def corpo(chamadas):
            assert construir._baixar_padrao("https://www.python.org/x/python.zip", destino, esperado) == destino
            assert chamadas == []
        _com_urlopen_falso(b"nao deveria ser lido", corpo)


def test_python_embarcavel_sem_sha256_e_recusado():
    with tempfile.TemporaryDirectory() as d:
        toml = Path(d) / "python-embarcavel.toml"
        toml.write_text('versao = "3.14.0"\nurl = "https://www.python.org/ftp/python/3.14.0/x.zip"\n', encoding="utf-8")
        try:
            construir.ler_python_embarcavel(toml)
        except ValueError as e:
            assert "sha256" in str(e)
        else:
            raise AssertionError("sem sha256 deveria dar ValueError")


def test_argumentos_do_iscc_e_localizacao():
    args = construir.argumentos_iscc(Path("C:/Inno/ISCC.exe"), Path("empacotamento/pseudonimizador.iss"),
                                     versao="0.2.0", origem=Path("build/app"), saida=Path("dist"))
    assert args[0].endswith("ISCC.exe") and "/DVersao=0.2.0" in args and args[-1].endswith("pseudonimizador.iss")
    assert any(a.startswith("/DOrigem=") for a in args) and any(a.startswith("/O") for a in args)
    with tempfile.TemporaryDirectory() as d:
        falso = Path(d) / "ISCC.exe"
        falso.write_bytes(b"MZ")
        assert construir.localizar_iscc(falso) == falso
        assert construir.localizar_iscc(Path(d) / "nao-existe.exe") is None
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py`
Expected: `ImportError: cannot import name 'construir'`.

- [ ] **Step 3: Escrever `construir.py`**

`empacotamento/construir.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Monta build/app e compila dist/Pseudonimizador-Setup.exe (spec §2).

Uso (na raiz, com o .venv do Python 3.14 x64 e o Inno Setup 6 instalados):
    .venv\\Scripts\\python -X utf8 empacotamento/construir.py             # monta e compila
    .venv\\Scripts\\python -X utf8 empacotamento/construir.py --so-montar  # para antes do ISCC

Este é um dos dois únicos scripts do projeto que usam a rede (python.org e
PyPI); o app e os testes nunca. Passos: 1) baixa (ou usa de
empacotamento/_cache) o Python embarcável e confere o sha256; 2) descompacta
em build/app/python e escreve o ._pth (o app e o site-packages no caminho,
sem "import site"); 3) pip --no-deps --require-hashes do requirements.lock
para Lib/site-packages; 4) copia as DLLs do runtime do Visual C++
(app-local: sem vc_redist, sem administrador; nunca do System32 num build
publicado); 5) copia o código pelo manifesto e o ícone; 6) fumaça: o Python
embarcado, a partir de OUTRA pasta e com a rede bloqueada, importa tudo, lê
DOCX/PDF/OCR, gera e restaura (empacotamento/fumaca.py); 7) ISCC com
/DVersao e /DOrigem; escreve dist/SHA256SUMS.txt e o .wsb do Sandbox.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tomllib
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

SERIE = "3.14"
CRT = ("msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll", "msvcp140_atomic_wait.dll", "msvcp140_codecvt_ids.dll",
       "concrt140.dll", "vcruntime140.dll", "vcruntime140_1.dll", "vccorlib140.dll")
CRT_OBRIGATORIAS = ("msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll")
ISCC_PADRAO = (Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
               Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe")
FUMACA = Path(__file__).resolve().parent / "fumaca.py"
NOME_SETUP = "Pseudonimizador-Setup.exe"


def ler_python_embarcavel(toml: Path) -> dict:
    d = tomllib.loads(Path(toml).read_text(encoding="utf-8"))
    for k in ("versao", "url", "sha256"):
        if not d.get(k):
            raise ValueError(f"python-embarcavel.toml sem '{k}'")
    return {"versao": d["versao"], "url": d["url"], "sha256": d["sha256"].lower()}


def conteudo_pth() -> str:
    # ".." é {app}: `-m pseudonimizador` funciona de qualquer pasta de trabalho. Sem "import site": ele poria o
    # site-packages DO USUÁRIO (%APPDATA%\Python\...) e seus .pth no sys.path.
    return "python314.zip\n.\n..\nLib\\site-packages\n"


def argumentos_pip(lock: Path, destino: Path) -> list[str]:
    return [sys.executable, "-m", "pip", "install", "--no-deps", "--require-hashes", "--only-binary=:all:",
            "--python-version", SERIE, "--platform", "win_amd64", "--implementation", "cp", "--abi", "cp314",
            "--upgrade", "--target", str(destino), "-r", str(lock)]


def nomes_do_crt() -> tuple[str, ...]:
    return CRT


def localizar_crt(candidatos: list[Path]) -> Path | None:
    for pasta in candidatos:
        if pasta and all((Path(pasta) / n).is_file() for n in CRT_OBRIGATORIAS):
            return Path(pasta)
    return None


def candidatos_crt(sistema: bool = False) -> list[Path]:
    """Onde procurar o CRT redistribuível (Visual Studio 2022/18: Microsoft.VC14x.CRT). O System32 só entra com
    a flag explícita (--crt-do-sistema): as DLLs dele são da versão do Windows da máquina, não as do redistribuível."""
    achados: list[Path] = []
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if base:
            achados += sorted(Path(base).glob("Microsoft Visual Studio/*/*/VC/Redist/MSVC/*/x64/Microsoft.VC14?.CRT"),
                              reverse=True)
    if sistema:
        achados.append(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32")
    return achados


def localizar_iscc(explicito: Path | None) -> Path | None:
    if explicito is not None:
        return Path(explicito) if Path(explicito).is_file() else None
    return next((p for p in ISCC_PADRAO if p.is_file()), None)


def argumentos_iscc(iscc: Path, iss: Path, *, versao: str, origem: Path, saida: Path) -> list[str]:
    return [str(iscc), f"/DVersao={versao}", f"/DOrigem={origem}", f"/O{saida}", str(iss)]


def _baixar_padrao(url: str, destino: Path, sha256: str) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    if not destino.is_file() or hashlib.sha256(destino.read_bytes()).hexdigest() != sha256:
        print(f"baixando {url}")
        with urllib.request.urlopen(url, timeout=120) as r:
            destino.write_bytes(r.read())
    real = hashlib.sha256(destino.read_bytes()).hexdigest()
    if real != sha256:
        destino.unlink(missing_ok=True)
        raise SystemExit(f"sha256 do Python embarcável não bate: esperado {sha256}, veio {real}")
    return destino


def _executar_padrao(args, **kw) -> int:
    print("  >", " ".join(str(a) for a in args))
    return subprocess.run(args, check=False, **kw).returncode


def montar(raiz: Path, build: Path, *, executar=_executar_padrao, baixar=_baixar_padrao, crt: Path | None = None,
           fumaca: bool = True, crt_do_sistema: bool = False) -> Path:
    from empacotamento import manifesto
    raiz, build = Path(raiz), Path(build)
    app = build / "app"
    if app.exists():
        shutil.rmtree(app)
    (app / "python").mkdir(parents=True)
    # 1-2: o Python embarcável
    py = ler_python_embarcavel(raiz / "empacotamento" / "python-embarcavel.toml")
    zip_local = baixar(py["url"], raiz / "empacotamento" / "_cache" / Path(py["url"]).name, py["sha256"])
    with zipfile.ZipFile(zip_local) as z:
        z.extractall(app / "python")
    (app / "python" / "python314._pth").write_text(conteudo_pth(), encoding="utf-8")
    # 3: as bibliotecas, do lock
    if executar(argumentos_pip(raiz / "requirements.lock", app / "python" / "Lib" / "site-packages")) != 0:
        raise SystemExit("pip falhou")
    # 4: o runtime do Visual C++ (app-local)
    pasta_crt = crt or localizar_crt(candidatos_crt(sistema=crt_do_sistema))
    if pasta_crt is None:
        raise SystemExit("não achei as DLLs do redistribuível do Visual C++ (msvcp140.dll e companhia); passe "
                         "--crt PASTA ou, só num build de teste, --crt-do-sistema (usa o System32: não publique)")
    if not crt and crt_do_sistema and Path(pasta_crt).name.lower() == "system32":
        print("AVISO: CRT do System32, só para teste; não publique este instalador.")
    for n in CRT:
        if (Path(pasta_crt) / n).is_file():
            shutil.copy2(Path(pasta_crt) / n, app / "python" / n)
    # 5: o código, pelo manifesto, e o ícone
    rel = manifesto.arquivos_do_pacote(raiz)
    if problemas := manifesto.problemas(rel):
        raise SystemExit("\n".join(problemas))
    for r in rel:
        (app / r).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raiz / r, app / r)
    shutil.copy2(raiz / "empacotamento" / "pseudonimizador.ico", app / "pseudonimizador.ico")
    # 6: fumaça
    if fumaca:
        fumacar(app, executar=executar)
    return app


def fumacar(app: Path, *, executar=_executar_padrao) -> None:
    """O Python embarcado, a partir de OUTRA pasta de trabalho (build/), roda empacotamento/fumaca.py."""
    rc = executar([str(app / "python" / "python.exe"), "-X", "utf8", str(FUMACA)], cwd=str(Path(app).parent))
    if rc != 0:
        raise SystemExit("fumaça falhou: o Python embarcado não fez o que o Pseudonimizador faz (importar, ler DOCX/PDF, "
                         "OCR, gerar, restaurar); veja a linha FALHA acima e confira o requirements.lock")


def gerar_wsb(modelo: Path, dist: Path) -> str:
    """Config do Windows Sandbox: mapeia dist/ (só leitura) e abre o Setup. {DIST} vem do modelo."""
    return Path(modelo).read_text(encoding="utf-8").replace("{DIST}", str(Path(dist).resolve()))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="monta build/app e compila dist/Pseudonimizador-Setup.exe")
    ap.add_argument("--so-montar", action="store_true")
    ap.add_argument("--crt", type=Path, help="pasta com msvcp140.dll e companhia")
    ap.add_argument("--iscc", type=Path, help="caminho do ISCC.exe")
    ap.add_argument("--crt-do-sistema", action="store_true",
                    help="build de teste: aceita as DLLs do System32 como CRT (não publique)")
    args = ap.parse_args(argv)
    if sys.version_info[:2] != (3, 14) or sys.platform != "win32":
        print("Rode com o Python 3.14 x64 do Windows (o mesmo do requirements.lock).")
        return 2
    from pseudonimizador import VERSAO
    build, dist = RAIZ / "build", RAIZ / "dist"
    app = montar(RAIZ, build, crt=args.crt, crt_do_sistema=args.crt_do_sistema)
    if args.so_montar:
        print(f"montado em {app}")
        return 0
    iscc = localizar_iscc(args.iscc)
    if iscc is None:
        print("ISCC.exe não encontrado: instale o Inno Setup 6 ou passe --iscc.")
        return 2
    dist.mkdir(exist_ok=True)
    rc = _executar_padrao(argumentos_iscc(iscc, RAIZ / "empacotamento" / "pseudonimizador.iss", versao=VERSAO,
                                          origem=app, saida=dist))
    if rc != 0:
        return rc
    setup = dist / NOME_SETUP
    (dist / "SHA256SUMS.txt").write_text(f"{hashlib.sha256(setup.read_bytes()).hexdigest()}  {setup.name}\n",
                                         encoding="utf-8")
    (dist / "Pseudonimizador-Sandbox.wsb").write_text(
        gerar_wsb(RAIZ / "empacotamento" / "sandbox.wsb.modelo", dist), encoding="utf-8")
    print(f"pronto: {setup} ({setup.stat().st_size // 1_000_000} MB), SHA256SUMS.txt e Pseudonimizador-Sandbox.wsb em {dist}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Rodar os testes**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py`
Expected: todos passam (inclusive `test_python_embarcavel_tem_versao_url_e_hash` da Task 3).

- [ ] **Step 5: Commit**

```bash
git add empacotamento/construir.py testes/test_empacotamento.py
git commit -m "Empacotamento: construir.py monta build/app (Python embarcado com hash, lock, CRT app-local, manifesto)

Co-Authored-By: <modelo que implementa> <noreply@anthropic.com>"
```

---

### Task 5: `fumaca.py` e a primeira montagem de verdade (decide a redução de tamanho)

**Files:**
- Create: `empacotamento/fumaca.py`
- Test: `testes/test_empacotamento.py`
- Possibly modify (só se a fumaça falhar sem sympy/headless): `empacotamento/gerar_lock.py`, `requirements.lock`, `testes/test_empacotamento.py`

**Interfaces:**
- Consumes: `construir.fumacar(app, *, executar)` (Task 4) chama `python.exe -X utf8 empacotamento/fumaca.py` com `cwd=build`; a biblioteca do app: `pseudonimizador.leitura.ler(Path) -> Documento` (`.texto`, `.avisos`), `pseudonimizador.revisao.Revisao(doc)` (`.itens`, `.fechar()`), `pseudonimizador.saida.gerar(doc, revisao_fechada, *, formato, modo, pasta_saida, pasta_mapas)` (→ `.saida`, `.mapa`, `.avisos`), `pseudonimizador.restaurar.mapa_do_docx(arquivo, pasta_mapas)`, `restaurar_docx(arquivo, saida, mapa) -> int`.
- Produces: `empacotamento/fumaca.py` (sai 0 se todas as verificações passam; 1 e a lista `FALHA` se alguma falha; `VERIFICACOES` nomeia cada uma).

- [ ] **Step 1: Escrever os testes (vermelho)**

Acrescente a `testes/test_empacotamento.py`:
```python
def test_fumaca_roda_o_script_no_python_embarcado_de_outra_pasta():
    chamadas = []

    def executar(args, **kw):
        chamadas.append((list(args), kw))
        return 0
    app = Path("X") / "app"
    construir.fumacar(app, executar=executar)
    assert len(chamadas) == 1
    args, kw = chamadas[0]
    assert args[0].endswith("python.exe") and args[1:3] == ["-X", "utf8"] and args[-1].endswith("fumaca.py")
    assert Path(args[-1]).is_file() and kw["cwd"] == str(app.parent)
    try:
        construir.fumacar(app, executar=lambda *a, **k: 1)
    except SystemExit as e:
        assert "OCR" in str(e) and "requirements.lock" in str(e)
    else:
        raise AssertionError("fumaça que falha tem de derrubar o build")


def test_fumaca_cobre_importacoes_docx_pdf_ocr_restauracao_e_rede():
    import ast
    fonte = (RAIZ / "empacotamento" / "fumaca.py").read_text(encoding="utf-8")
    ast.parse(fonte)
    lista = fonte.split("VERIFICACOES = (")[1]
    for nome in ("importacoes", "codigo_do_pacote", "docx_pseudonimizar_e_restaurar", "pdf_com_texto",
                 "pdf_escaneado_ocr", "rede_bloqueada"):
        assert f"def {nome}()" in fonte and nome in lista, nome
    assert "socket" in fonte and "127.0.0.1" in fonte


def test_fumaca_roda_de_verdade_no_python_embarcado_quando_ha_build():
    """Só se build/app existir (montagem local): o script de verdade, no Python embarcado, passa."""
    import subprocess
    py = RAIZ / "build" / "app" / "python" / "python.exe"
    if not py.is_file():
        return
    r = subprocess.run([str(py), "-X", "utf8", str(construir.FUMACA)], cwd=str(RAIZ / "build"),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, (r.stdout[-800:], r.stderr[-800:])
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py`
Expected: as duas primeiras FALHAM (`fumaca.py` não existe); a terceira passa em silêncio (sem build).

- [ ] **Step 3: Escrever `fumaca.py`**

`empacotamento/fumaca.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Fumaça da montagem: roda NO PYTHON EMBARCADO (build/app/python/python.exe), a
partir de OUTRA pasta (build/), com a rede bloqueada e só com dados sintéticos,
o que o Pseudonimizador faz de verdade: importa tudo, lê DOCX, PDF com texto e
PDF escaneado (OCR), gera a saída reversível e restaura. Importar não basta: o
pacote sem sympy e com opencv-python-headless (spec §2) só é aceito se isto
passar. Sai com 0 se tudo passa; 1 e a lista FALHA se algo falha."""
from __future__ import annotations

import socket
import sys
import tempfile
import traceback
import warnings
from pathlib import Path

warnings.simplefilter("ignore")
LOCAIS = {"127.0.0.1", "::1", "localhost"}
PESSOA = "Maria Aparecida Pereira"            # sintético (o mesmo de testes/fabrica.py)
CPF = "111.444.777-35"
LINHAS = ["CONTRATO DE LOCAÇÃO RESIDENCIAL",
          f"LOCADOR: {PESSOA}, portadora do CPF {CPF}, residente na Rua das Acácias, 120.",
          "Cláusula 1ª. O aluguel mensal é de R$ 1.500,00.", "Porto Alegre, 11 de outubro de 2026."]
_tentativas: list[str] = []


def _bloquear_rede():
    def host(e):
        return e[0] if isinstance(e, tuple) else str(e)
    conn, cria, gai = socket.socket.connect, socket.create_connection, socket.getaddrinfo

    def connect(self, e):
        if host(e) not in LOCAIS:
            _tentativas.append(host(e))
            raise OSError("rede bloqueada na fumaça")
        return conn(self, e)

    def create(e, *a, **k):
        if host(e) not in LOCAIS:
            _tentativas.append(host(e))
            raise OSError("rede bloqueada na fumaça")
        return cria(e, *a, **k)

    def getaddrinfo(h, *a, **k):
        if h is not None and h not in LOCAIS:
            _tentativas.append(str(h))
            raise OSError("rede bloqueada na fumaça")
        return gai(h, *a, **k)
    socket.socket.connect, socket.create_connection, socket.getaddrinfo = connect, create, getaddrinfo


def _docx(caminho: Path) -> Path:
    import docx
    d = docx.Document()
    for l in LINHAS:
        d.add_paragraph(l)
    d.save(str(caminho))
    return caminho


def _pdf(caminho: Path) -> Path:
    import pymupdf
    d = pymupdf.open()
    p = d.new_page()
    for i, l in enumerate(LINHAS):
        p.insert_text((72, 100 + 20 * i), l, fontsize=11)
    d.save(str(caminho))
    d.close()
    return caminho


def _pdf_escaneado(caminho: Path) -> Path:
    """A mesma página, mas só como imagem (sem camada de texto): obriga o OCR."""
    import pymupdf
    origem = pymupdf.open()
    p = origem.new_page()
    for i, l in enumerate(LINHAS):
        p.insert_text((72, 100 + 20 * i), l, fontsize=14)
    pix = p.get_pixmap(dpi=200)
    d = pymupdf.open()
    pagina = d.new_page(width=p.rect.width, height=p.rect.height)
    pagina.insert_image(pagina.rect, pixmap=pix)
    d.save(str(caminho))
    d.close()
    origem.close()
    return caminho


def _gerar(arquivo: Path, pasta: Path):
    from pseudonimizador.leitura import ler
    from pseudonimizador.revisao import Revisao
    from pseudonimizador.saida import gerar
    doc = ler(arquivo)
    g = gerar(doc, Revisao(doc).fechar(), formato="layout", modo="reversivel",
              pasta_saida=pasta / "Saida", pasta_mapas=pasta / "Mapas")
    assert Path(g.saida).is_file(), g.saida
    return doc, g


def importacoes():
    import cv2, docx, fitz, numpy, onnxruntime, pyclipper, pymupdf, rapidocr, shapely  # noqa: F401,E401
    import pseudonimizador
    from pseudonimizador import deteccao, estado, leitura, motor, restaurar, revisao, saida, web  # noqa: F401
    from pseudonimizador.web import abrir, pasta_monitorada, registro, servidor  # noqa: F401
    assert "CPUExecutionProvider" in onnxruntime.get_available_providers()
    assert pseudonimizador.VERSAO


def codigo_do_pacote():
    """O que importou é o de build/app (o ".." do ._pth), não o do repositório nem o site-packages do usuário."""
    import pseudonimizador
    raiz = Path(pseudonimizador.__file__).resolve().parents[1]
    assert raiz.name == "app" and (raiz / "python" / "python314._pth").is_file(), raiz
    assert not any("APPDATA" in p.upper() or "site-packages" in p and "app" not in p for p in sys.path), sys.path


def docx_pseudonimizar_e_restaurar():
    from pseudonimizador.leitura import ler
    from pseudonimizador.restaurar import mapa_do_docx, restaurar_docx
    with tempfile.TemporaryDirectory() as td:
        pasta = Path(td)
        _, g = _gerar(_docx(pasta / "contrato.docx"), pasta)
        texto = ler(Path(g.saida)).texto
        assert PESSOA not in texto and CPF not in texto and "[[" in texto, texto[:200]
        mapa = mapa_do_docx(Path(g.saida), pasta / "Mapas")
        assert mapa is not None
        n = restaurar_docx(Path(g.saida), pasta / "restaurado.docx", mapa)
        assert n >= 1 and PESSOA in ler(pasta / "restaurado.docx").texto


def pdf_com_texto():
    from pseudonimizador.leitura import ler
    with tempfile.TemporaryDirectory() as td:
        pasta = Path(td)
        doc, g = _gerar(_pdf(pasta / "contrato.pdf"), pasta)
        assert PESSOA in doc.texto
        assert PESSOA not in ler(Path(g.saida)).texto


def pdf_escaneado_ocr():
    with tempfile.TemporaryDirectory() as td:
        pasta = Path(td)
        doc, g = _gerar(_pdf_escaneado(pasta / "escaneado.pdf"), pasta)
        assert "Maria" in doc.texto and "Pereira" in doc.texto, doc.texto[:200]   # o OCR leu a imagem
        assert Path(g.saida).stat().st_size > 0


def rede_bloqueada():
    assert not _tentativas, f"tentativas de rede durante a fumaça: {_tentativas}"


VERIFICACOES = (importacoes, codigo_do_pacote, docx_pseudonimizar_e_restaurar, pdf_com_texto, pdf_escaneado_ocr,
                rede_bloqueada)


def main() -> int:
    _bloquear_rede()
    falhas = []
    for verificacao in VERIFICACOES:
        try:
            verificacao()
            print(f"  ok     {verificacao.__name__}")
        except BaseException as e:  # noqa: BLE001 — lista tudo o que falha, não só a primeira
            falhas.append(verificacao.__name__)
            print(f"  FALHA  {verificacao.__name__}: {e!r}")
            traceback.print_exc(limit=3)
    if falhas:
        print("fumaça falhou em: " + ", ".join(falhas))
        return 1
    print(f"fumaça: {len(VERIFICACOES)} verificações passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Rodar os testes de estrutura**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py`
Expected: todos passam.

- [ ] **Step 5: Montar de verdade (rede: python.org e PyPI) — sem o Inno Setup ainda**

Run: `.venv/Scripts/python -X utf8 empacotamento/construir.py --so-montar`
Expected: baixa o zip (fica em `empacotamento/_cache/`), instala o lock em `build\app\python\Lib\site-packages`, copia o CRT de `C:\Program Files\Microsoft Visual Studio\18\Community\VC\Redist\MSVC\<ver>\x64\Microsoft.VC145.CRT` (se não achar, passe `--crt "<essa pasta>"`), copia o código... e **falha em "pseudonimizador.ico"**, que só existe na Task 6. Para esta rodada, gere um ícone provisório: `.venv/Scripts/python -c "open('empacotamento/pseudonimizador.ico','wb').write(b'')"` NÃO serve ao ISCC, mas serve ao `shutil.copy2`; a Task 6 o substitui pelo de verdade. Rode de novo o `--so-montar`. Esperado no fim: `  ok     importacoes` … `fumaça: 6 verificações passaram` e `montado em ...\build\app`.

- [ ] **Step 6: Decidir a redução de tamanho (spec §2)**

Se a fumaça passou: a redução fica. Anote o tamanho de `build\app` (`du -sh build/app` no Bash) para o README da Task 6.

Se `importacoes` ou `pdf_escaneado_ocr` falharam com `ModuleNotFoundError: sympy` (ou `mpmath`): em `gerar_lock.py` troque `EXCLUIDOS = frozenset({"opencv-python", "sympy", "mpmath"})` por `EXCLUIDOS = frozenset({"opencv-python"})` e, em `problemas_do_lock`, nada muda; regenere com `.venv/Scripts/python -X utf8 empacotamento/gerar_lock.py`; em `testes/test_empacotamento.py` retire `assert "sympy" not in texto` de `test_requirements_lock_do_repositorio_esta_coerente` e ajuste `test_lock_troca_o_opencv_pelo_headless_e_tira_o_sympy` (o headless continua; `len(restantes) == 5`); repita o Step 5. Se a falha for do `cv2` headless (erro ao importar `cv2` ou no OCR com `cv2.error`), troque `SUBSTITUTO`/o filtro para manter o `opencv-python` (retire-o de `EXCLUIDOS` e troque `problemas_do_lock` para exigir `opencv-python`), regenere, ajuste os testes e repita. Em qualquer dos dois casos, registre a decisão e o erro exato no corpo do commit e no `empacotamento/README.md` (Task 6, seção "Redução de tamanho").

- [ ] **Step 7: Rodar a suíte do empacotamento com o build presente**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py`
Expected: todos passam, agora com `test_fumaca_roda_de_verdade_no_python_embarcado_quando_ha_build` rodando de fato (uns 20–40 s).

- [ ] **Step 8: Commit** (o `.ico` provisório **não** entra; `build/` e `_cache/` estão ignorados)

```bash
git add empacotamento/fumaca.py testes/test_empacotamento.py
git commit -m "Empacotamento: fumaça no Python embarcado (importa, DOCX, PDF, OCR, restaura, sem rede); montagem conferida

Co-Authored-By: <modelo que implementa> <noreply@anthropic.com>"
```
(Se a Task 5 desfez a redução, inclua `empacotamento/gerar_lock.py requirements.lock` no `git add` e diga no corpo da mensagem qual verificação falhou e com que erro.)

---

### Task 6: Ícone, `pseudonimizador.iss`, Sandbox e o build completo

**Files:**
- Create: `empacotamento/gerar_icone.py`, `empacotamento/pseudonimizador.ico`, `empacotamento/pseudonimizador.iss`, `empacotamento/sandbox.wsb.modelo`, `empacotamento/README.md`
- Test: `testes/test_empacotamento.py`

**Interfaces:**
- Consumes: `construir.main()` (Task 4: `argumentos_iscc` passa `/DVersao`, `/DOrigem`, `/O`), `construir.gerar_wsb(modelo, dist)`, `pseudonimizador.web.abrir.NOME_MUTEX` (`"Pseudonimizador-Servidor"`), o subcomando `configurar --pasta-base` (Task 2).
- Produces: `dist\Pseudonimizador-Setup.exe`, `dist\SHA256SUMS.txt`, `dist\Pseudonimizador-Sandbox.wsb`; o roteiro do mantenedor com o checklist de aceitação (manual, feito pelo usuário).

- [ ] **Step 1: Escrever os testes (vermelho)**

Acrescente a `testes/test_empacotamento.py`:
```python
def _iss() -> str:
    bruto = (RAIZ / "empacotamento" / "pseudonimizador.iss").read_bytes()
    assert bruto.startswith(b"\xef\xbb\xbf"), "o .iss precisa de BOM UTF-8 (o ISCC lê os acentos assim)"
    return bruto.decode("utf-8-sig")


def _secao(iss: str, nome: str) -> list[str]:
    corpo = iss.split(f"[{nome}]")[1].split("\n[")[0]
    return [l.strip() for l in corpo.splitlines() if l.strip() and not l.strip().startswith(";")]


def test_icone_e_um_ico_valido_com_varios_tamanhos():
    import struct
    dados = (RAIZ / "empacotamento" / "pseudonimizador.ico").read_bytes()
    reservado, tipo, n = struct.unpack("<HHH", dados[:6])
    assert (reservado, tipo) == (0, 1) and n >= 3
    for i in range(n):
        _, _, _, _, _, _, tam, desl = struct.unpack("<BBBBHHII", dados[6 + 16 * i:22 + 16 * i])
        assert 0 < tam and desl + tam <= len(dados)


def test_iss_instala_sem_administrador_so_x64_e_fecha_o_app_aberto():
    from pseudonimizador.web import abrir
    iss = _iss()
    for exigido in ("PrivilegesRequired=lowest", "DefaultDirName={localappdata}\\Programs\\Pseudonimizador",
                    "DisableDirPage=yes", "DisableProgramGroupPage=yes", "ArchitecturesAllowed=x64compatible",
                    "ArchitecturesInstallIn64BitMode=x64compatible", "MinVersion=10.0.17763",
                    f"AppMutex={abrir.NOME_MUTEX}", "CloseApplications=yes", "OutputBaseFilename=Pseudonimizador-Setup",
                    "SetupIconFile=pseudonimizador.ico", "Languages\\BrazilianPortuguese.isl", "AppVersion={#Versao}",
                    '#error Passe /DVersao', 'Parameters: "-X utf8 -m pseudonimizador"', 'WorkingDir: "{app}"',
                    "python\\pythonw.exe", "{userdesktop}\\Pseudonimizador", "Tasks: atalho",
                    "Flags: postinstall nowait skipifsilent"):
        assert exigido in iss, exigido
    for proibido in ("{pf}", "{commonpf", "{commonappdata}", "runascurrentuser", "PrivilegesRequired=admin",
                     "C:\\Users", "DirectML", "claude", "Mistral", "agendado"):
        assert proibido not in iss, proibido


def test_iss_pagina_da_pasta_chama_configurar_e_avisa_se_falhar():
    iss = _iss()
    assert "CreateInputDirPage(" in iss and "{userdocs}\\Pseudonimizador" in iss
    assert "'Entrada'" not in iss and "Entrada" in iss and "Saida" in iss and "Mapas" in iss   # a explicação da página
    passo = iss.split("procedure CurStepChanged")[1].split("\nend;")[0]
    assert "configurar --pasta-base" in passo and "SW_HIDE" in passo and "ewWaitUntilTerminated" in passo
    assert "python\\python.exe" in passo and "RemoveBackslashUnlessRoot" in passo    # aspas: "C:\x\" quebraria
    assert "Codigo <> 0" in passo and "ConfigFalhou := True" in passo and "SuppressibleMsgBox" in passo
    assert "  MsgBox(" not in passo                              # silencioso nunca trava numa caixa
    fim = iss.split("procedure CurPageChanged")[1].split("\nend;")[0]
    assert "ConfigFalhou" in fim and "Configurações" in fim and "AdjustLabelHeight" in fim


def test_iss_pula_a_pagina_da_pasta_na_atualizacao():
    iss = _iss()
    pular = iss.split("function ShouldSkipPage")[1].split("\nend;")[0]
    assert "PaginaPasta.ID" in pular and "ConfigExiste" in pular
    assert "{localappdata}\\Pseudonimizador\\config.json" in iss
    passo = iss.split("procedure CurStepChanged")[1].split("\nend;")[0]
    assert "if ConfigExiste then exit" in passo                  # config existente nunca é sobrescrita pelo Setup


def test_iss_instalacao_nova_limpa_so_as_pastas_do_programa():
    iss = _iss()
    assert _secao(iss, "InstallDelete") == ['Type: filesandordirs; Name: "{app}\\python"',
                                            'Type: filesandordirs; Name: "{app}\\pseudonimizador"']
    assert iss.index("[InstallDelete]") < iss.index("[Files]")


def test_iss_pergunta_de_apagar_dados_padrao_nao_e_silencio_respeitado():
    iss = _iss()
    assert _secao(iss, "UninstallDelete") == ['Type: filesandordirs; Name: "{app}"']
    assert "[UninstallRun]" not in iss and "function InitializeUninstall" not in iss
    codigo = iss.split("procedure CurUninstallStepChanged")[1]
    assert "UninstallSilent" in codigo and "MB_DEFBUTTON2" in codigo and "MB_YESNO" in codigo
    assert "ApagarDadosResposta := False" in codigo.split("UninstallSilent")[1].split("else")[0]
    assert "DelTree(ExpandConstant('{localappdata}\\Pseudonimizador')" in codigo
    assert "nunca é apagada" in codigo and "userdocs" not in codigo and "pasta_base" not in codigo


def test_wsb_do_sandbox_mapeia_o_dist_so_leitura_sem_rede_e_abre_o_setup():
    modelo = RAIZ / "empacotamento" / "sandbox.wsb.modelo"
    with tempfile.TemporaryDirectory() as d:
        texto = construir.gerar_wsb(modelo, Path(d) / "dist")
    assert str((Path(d) / "dist").resolve()) in texto and "{DIST}" not in texto
    assert "<ReadOnly>true</ReadOnly>" in texto and "<Networking>Disable</Networking>" in texto
    assert "<VGpu>Enable</VGpu>" in texto and "Pseudonimizador-Setup.exe" in texto
    assert "C:\\Users" not in modelo.read_text(encoding="utf-8")        # nem o usuário padrão do Sandbox
    assert "<SandboxFolder>" not in texto                                  # sem SandboxFolder, cai na Área de Trabalho


def test_roteiro_do_mantenedor_cobre_montagem_aceitacao_e_limites():
    texto = (RAIZ / "empacotamento" / "README.md").read_text(encoding="utf-8")
    for exigido in ("construir.py", "--so-montar", "--crt", "--iscc", "gerar_lock.py", "python-embarcavel.toml",
                    "Pseudonimizador-Sandbox.wsb", "SHA256SUMS.txt", "Pseudonimizador-Setup.exe", "SmartScreen",
                    "Redução de tamanho", "Aceitação no Windows Sandbox", "Instala sem pedir administrador",
                    "Pasta dos arquivos", "DOCX", "PDF com texto", "PDF escaneado", "Restaurar", "Encerrar",
                    "Desinstalar", "nunca apaga", "Atualização por cima", "verificar_publicacao.py"):
        assert exigido in texto, exigido
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py`
Expected: os oito novos FALHAM (`.ico` vazio/`.iss`/`.modelo`/`README.md` ausentes).

- [ ] **Step 3: O ícone**

`empacotamento/gerar_icone.py` (roda no `.venv`, que tem Pillow via rapidocr; o `.ico` gerado é rastreado):
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Gera empacotamento/pseudonimizador.ico (16, 32, 48 e 256 px): um quadrado
azul-escuro arredondado com duas tarjas brancas — o dado coberto. Uso:
    .venv\\Scripts\\python -X utf8 empacotamento/gerar_icone.py"""
from __future__ import annotations

import sys
from pathlib import Path

DESTINO = Path(__file__).resolve().parent / "pseudonimizador.ico"
AZUL = (31, 58, 95, 255)


def desenhar(tamanho: int):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, tamanho - 1, tamanho - 1), radius=tamanho // 5, fill=AZUL)
    m, alt = tamanho // 5, max(2, tamanho // 9)
    d.rounded_rectangle((m, tamanho * 0.36, tamanho - m, tamanho * 0.36 + alt), radius=alt // 2, fill="white")
    d.rounded_rectangle((m, tamanho * 0.58, tamanho * 0.62, tamanho * 0.58 + alt), radius=alt // 2, fill="white")
    return img


def main() -> int:
    desenhar(256).save(DESTINO, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    print(f"ícone: {DESTINO} ({DESTINO.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Run: `.venv/Scripts/python -X utf8 empacotamento/gerar_icone.py`
Expected: `ícone: ...pseudonimizador.ico (N bytes)` e `test_icone_e_um_ico_valido_com_varios_tamanhos` passa.

- [ ] **Step 4: O `.iss`** (Write; depois o passo do BOM)

`empacotamento/pseudonimizador.iss`:
```
; empacotamento/pseudonimizador.iss — Pseudonimizador-Setup.exe (spec §3). Compilado por construir.py
; com /DVersao e /DOrigem. Sem administrador; só x64; português do Brasil.
; SPDX-License-Identifier: AGPL-3.0-only
#ifndef Versao
  #error Passe /DVersao=x.y.z (construir.py faz isso)
#endif
#ifndef Origem
  #define Origem "..\build\app"
#endif

[Setup]
AppId={{7D2B9C1E-5F3A-4B86-9E0C-2A6D4F8B1C57}
AppName=Pseudonimizador
AppVersion={#Versao}
AppVerName=Pseudonimizador {#Versao}
AppPublisher=Pseudonimizador — proteção de dados pessoais em documentos
VersionInfoVersion={#Versao}.0
DefaultDirName={localappdata}\Programs\Pseudonimizador
DisableDirPage=yes
DefaultGroupName=Pseudonimizador
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
AppMutex=Pseudonimizador-Servidor
CloseApplications=yes
OutputDir=..\dist
OutputBaseFilename=Pseudonimizador-Setup
SetupIconFile=pseudonimizador.ico
UninstallDisplayIcon={app}\pseudonimizador.ico
UninstallDisplayName=Pseudonimizador
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=no

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Messages]
pt.WelcomeLabel2=O Pseudonimizador protege dados pessoais em documentos (DOCX e PDF) sem que nada saia do seu computador.%n%nEle será instalado só para você, sem precisar de administrador, e não baixa nada da internet.
pt.FinishedLabel=O Pseudonimizador está instalado. Abra-o pelo atalho e arraste um documento para a janela.

[Tasks]
Name: "atalho"; Description: "Criar um atalho na Área de Trabalho"; GroupDescription: "Atalhos:"

[InstallDelete]
; atualizar por cima não deixa arquivo velho (um módulo que sumiu, um .dist-info antigo). Só as pastas do
; programa; nunca {app} inteiro nem os dados em {localappdata}.
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\pseudonimizador"

[Files]
Source: "{#Origem}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Pseudonimizador"; Filename: "{app}\python\pythonw.exe"; Parameters: "-X utf8 -m pseudonimizador"; WorkingDir: "{app}"; IconFilename: "{app}\pseudonimizador.ico"; Comment: "Proteção de dados pessoais em documentos"
Name: "{group}\Desinstalar o Pseudonimizador"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Pseudonimizador"; Filename: "{app}\python\pythonw.exe"; Parameters: "-X utf8 -m pseudonimizador"; WorkingDir: "{app}"; IconFilename: "{app}\pseudonimizador.ico"; Tasks: atalho

[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: "-X utf8 -m pseudonimizador"; WorkingDir: "{app}"; Description: "Abrir o Pseudonimizador agora"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
; o que o programa criou em {app} depois da instalação (__pycache__). Os dados do usuário ({localappdata})
; só saem pela pergunta do Pascal; a pasta dos arquivos (Entrada, Saida, Mapas) NUNCA entra aqui.
Type: filesandordirs; Name: "{app}"

[Code]
var
  PaginaPasta: TInputDirWizardPage;
  ConfigFalhou, ApagarDadosResposta: Boolean;

function ConfigExiste: Boolean;
begin
  Result := FileExists(ExpandConstant('{localappdata}\Pseudonimizador\config.json'));
end;

procedure InitializeWizard;
begin
  PaginaPasta := CreateInputDirPage(wpWelcome, 'Pasta dos arquivos',
    'Onde ficam os documentos que você protege',
    'Nessa pasta o Pseudonimizador cria Entrada (documentos para processar em lote), Saida (os documentos protegidos) e Mapas (os mapas que permitem restaurar os nomes — guarde-os com cuidado). Dá para mudar depois, nas Configurações.',
    False, '');
  PaginaPasta.Add('');
  PaginaPasta.Values[0] := ExpandConstant('{userdocs}\Pseudonimizador');
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  // atualização por cima: a pasta já está no config.json e não é perguntada de novo
  Result := (PageID = PaginaPasta.ID) and ConfigExiste;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = PaginaPasta.ID) and (Trim(PaginaPasta.Values[0]) = '') then
  begin
    MsgBox('Informe a pasta dos arquivos.', mbInformation, MB_OK);
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Codigo: Integer;
  Pasta: String;
begin
  if CurStep <> ssPostInstall then exit;
  if ConfigExiste then exit;
  // sem a barra final: "C:\x\" dentro de aspas viraria uma aspa escapada
  Pasta := RemoveBackslashUnlessRoot(Trim(PaginaPasta.Values[0]));
  if (not Exec(ExpandConstant('{app}\python\python.exe'),
      '-X utf8 -m pseudonimizador configurar --pasta-base "' + Pasta + '"',
      ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, Codigo)) or (Codigo <> 0) then
  begin
    ConfigFalhou := True;
    SuppressibleMsgBox('Não foi possível preparar a pasta dos arquivos (' + Pasta + '). ' +
      'O programa foi instalado; ao abrir, escolha a pasta em Configurações.', mbInformation, MB_OK, IDOK);
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
var
  AlturaAntes: Integer;
begin
  if (CurPageID <> wpFinished) or (not ConfigFalhou) then exit;
  WizardForm.FinishedLabel.Caption := WizardForm.FinishedLabel.Caption + #13#10#13#10 +
    'A pasta dos arquivos não pôde ser preparada: escolha-a em Configurações ao abrir o programa.';
  // o texto mudou: reajusta a altura do rótulo e desloca a lista de "Executar" para não cortar nada
  AlturaAntes := WizardForm.FinishedLabel.Height;
  WizardForm.AdjustLabelHeight(WizardForm.FinishedLabel);
  WizardForm.RunList.Top := WizardForm.RunList.Top + (WizardForm.FinishedLabel.Height - AlturaAntes);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  // A pergunta vem depois do "Deseja remover completamente?" do próprio Inno. O padrão é NÃO
  // (MB_DEFBUTTON2) e a desinstalação silenciosa nunca apaga os dados (MsgBox comum não é suprimido
  // por /SUPPRESSMSGBOXES e o DelTree não passa pela Lixeira).
  if CurUninstallStep = usUninstall then
  begin
    if UninstallSilent then
      ApagarDadosResposta := False
    else
      ApagarDadosResposta := (MsgBox('Apagar também as configurações e os registros do Pseudonimizador neste computador (a pasta Pseudonimizador em AppData\Local)?' + #13#10#13#10 +
        'A pasta dos arquivos (Entrada, Saida e Mapas) nunca é apagada.', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES);
  end;
  if (CurUninstallStep = usPostUninstall) and ApagarDadosResposta then
    DelTree(ExpandConstant('{localappdata}\Pseudonimizador'), True, True, True);
end;
```

Depois de gravar, ponha o BOM (o Write não o põe):
```
.venv/Scripts/python -c "p='empacotamento/pseudonimizador.iss'; b=open(p,'rb').read(); open(p,'wb').write(b if b.startswith(b'\xef\xbb\xbf') else b'\xef\xbb\xbf'+b)"
```

- [ ] **Step 5: O modelo do Sandbox**

`empacotamento/sandbox.wsb.modelo` (sem `SandboxFolder`: a pasta mapeada cai na Área de Trabalho do usuário do Sandbox, sem citar caminho de usuário; `cmd /c start` expande `%USERPROFILE%`):
```xml
<Configuration>
  <VGpu>Enable</VGpu>
  <Networking>Disable</Networking>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>{DIST}</HostFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>cmd /c start "" "%USERPROFILE%\Desktop\dist\Pseudonimizador-Setup.exe"</Command>
  </LogonCommand>
</Configuration>
```

- [ ] **Step 6: O roteiro do mantenedor**

`empacotamento/README.md`:
```markdown
# Empacotamento — roteiro do mantenedor

Como montar, aceitar e preparar a publicação do `Pseudonimizador-Setup.exe`.
O usuário final lê a seção "Instalação" do `README.md` da raiz. Padrão
adaptado do empacotamento do Ulpiano, do mesmo autor (`CREDITOS.md`).

## 1. Pré-requisitos (só na máquina que monta)

- O `.venv` do projeto (Python 3.14 x64): o mesmo do `requirements.lock`.
- **Inno Setup 6** (`winget install JRSoftware.InnoSetup`); o `construir.py`
  acha o `ISCC.exe` em `%LOCALAPPDATA%\Programs\Inno Setup 6` ou em
  `Program Files (x86)`; fora daí, passe `--iscc CAMINHO`.
- **DLLs do CRT do Visual C++** (`msvcp140.dll` e companhia), que o
  `onnxruntime` pede. O script procura a pasta `Redist\MSVC\<versão>\x64\
  Microsoft.VC14x.CRT` do Visual Studio instalado; fora daí, `--crt PASTA`.
  As DLLs do `System32` só entram com `--crt-do-sistema`: **vale só para
  teste** — não publique um instalador montado com elas.
- **Windows Sandbox** ligado (Recursos do Windows), para a aceitação.
- Internet: `gerar_lock.py` (PyPI) e `construir.py` (python.org e PyPI)
  são os únicos scripts do projeto que usam a rede.

## 2. Montar

    .venv\Scripts\python -X utf8 empacotamento/construir.py

Produz, em `dist\`: `Pseudonimizador-Setup.exe`, `SHA256SUMS.txt` e
`Pseudonimizador-Sandbox.wsb` (mapeia `dist\` em só leitura, GPU virtual
ligada, **rede desligada**, e abre o Setup ao entrar no Sandbox).

- Só a árvore do aplicativo, sem compilar: `--so-montar` (sai em `build\app`).
- A fumaça (`fumaca.py`) roda no Python embarcado, de outra pasta e com a
  rede bloqueada: importa tudo, lê DOCX, PDF com texto e PDF escaneado
  (OCR), gera e restaura. Se falhar, o build para.

### Trocar a versão do Python embarcável

Em `python-embarcavel.toml`, troque os três campos juntos (`versao`, `url`,
`sha256` publicado em python.org para "Windows embeddable package (64-bit)").
O `construir.py` recusa o zip se o hash não bater. Se a série (3.14) mudar,
regenere o lock.

### Regenerar o `requirements.lock`

    .venv\Scripts\python -X utf8 empacotamento/gerar_lock.py

### Redução de tamanho

O pacote leva `opencv-python-headless` no lugar do `opencv-python` (sem a
GUI do OpenCV) e não leva `sympy`/`mpmath` (dependência declarada do
`onnxruntime` que o OCR não usa ao rodar). A fumaça prova que o OCR funciona
assim. Estado: <preenchido na Task 5: "mantida; build\app com N MB" ou
"desfeita em <data>: <verificação> falhou com <erro>">.

## 3. Aceitação no Windows Sandbox (manual)

Duplo clique em `dist\Pseudonimizador-Sandbox.wsb`. Dentro do Sandbox não há
rede: tudo o que funcionar ali funciona sem internet (critério 2 da spec).
Marque cada item; anote data e resultado na tabela do fim.

- [ ] Instala sem pedir administrador; o SmartScreen aparece ("Mais
  informações" → "Executar assim mesmo"); a página "Pasta dos arquivos" vem
  com `Documentos\Pseudonimizador`; aceitar.
- [ ] Ao terminar, `Documentos\Pseudonimizador` tem `Entrada`, `Saida` e
  `Mapas`; "Abrir o Pseudonimizador agora" abre a janela pelo Edge.
- [ ] Atalho do menu Iniciar abre a janela de novo (só outra janela, sem
  segundo servidor).
- [ ] DOCX: arrastar um `.docx` sintético (copiar de `saida_testes\cli\` do
  host para a Área de Trabalho do Sandbox antes), revisar, Gerar; a saída
  aparece em `Saida`.
- [ ] PDF com texto: o mesmo com um `.pdf` sintético.
- [ ] PDF escaneado: um PDF só de imagem é lido por OCR (demora alguns
  segundos) e gera.
- [ ] Restaurar: o DOCX gerado volta com os nomes pelo menu Restaurar.
- [ ] Encerrar pelo menu fecha o servidor.
- [ ] Atualização por cima: rodar o Setup de novo com o app aberto (ele pede
  para fechar); a página da pasta **não** aparece; a config continua.
- [ ] Desinstalar: a pergunta sobre configurações vem com o padrão "Não";
  "Não" preserva `%LOCALAPPDATA%\Pseudonimizador`; `Documentos\
  Pseudonimizador` (com `Mapas`) fica nos dois casos — o desinstalador
  nunca apaga a pasta dos arquivos.

| Item | Data | Resultado |
|---|---|---|
| (cada item acima) | | PENDENTE |

## 4. Antes de publicar

    .venv\Scripts\python -X utf8 empacotamento/verificar_publicacao.py

Roda a suíte, a guarda de dados reais, varre o histórico inteiro
(`git log --all -p`) por e-mail pessoal, caminho de máquina e os termos de
`empacotamento/termos_proibidos.txt` (local, ignorado pelo git; pode não
existir), confere que todos os commits têm o e-mail privado do GitHub e que
`dist\` tem o `Setup.exe` com o `SHA256SUMS.txt` batendo. As notas da release
ficam em `docs/release-notes/`.

## 5. Sem assinatura: o SmartScreen

O instalador **não é assinado**. O Windows mostra "O Windows protegeu o
computador" no primeiro uso: "Mais informações" → "Executar assim mesmo". O
`SHA256SUMS.txt` publicado junto permite conferir o arquivo
(`certutil -hashfile Pseudonimizador-Setup.exe SHA256`).
```

- [ ] **Step 7: Rodar os testes**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py`
Expected: todos passam (o teste do README exige `verificar_publicacao.py` só como texto).

- [ ] **Step 8: O build completo (ISCC)**

Run: `.venv/Scripts/python -X utf8 empacotamento/construir.py`
Expected: fumaça ok, ISCC compila (alguns minutos com `lzma2/ultra64`), `pronto: ...\dist\Pseudonimizador-Setup.exe (N MB), SHA256SUMS.txt e Pseudonimizador-Sandbox.wsb em ...\dist`. Confira `git status`: nada de `build/`, `dist/`, `_cache/` aparece. Anote N MB na seção "Redução de tamanho" do `empacotamento/README.md`.

- [ ] **Step 9: Entregar o checklist ao usuário**

A aceitação no Sandbox é manual: informe ao controlador que `dist\Pseudonimizador-Sandbox.wsb` está pronto e aponte a seção 3 do `empacotamento/README.md`. O implementador **não** roda o Sandbox. Se o usuário relatar falha num item, corrija no ramo e repita o Step 8 antes da Task 8.

- [ ] **Step 10: Commit**

```bash
git add empacotamento/gerar_icone.py empacotamento/pseudonimizador.ico empacotamento/pseudonimizador.iss empacotamento/sandbox.wsb.modelo empacotamento/README.md testes/test_empacotamento.py
git commit -m "Instalador: pseudonimizador.iss (página da pasta, configurar, desinstalação que preserva os arquivos), ícone, Sandbox e roteiro

Co-Authored-By: <modelo que implementa> <noreply@anthropic.com>"
```

---

### Task 7: README (usuário e mantenedor), CREDITOS e notas da release

**Files:**
- Modify: `README.md` (seção "Instalação"; nova "Montar o instalador")
- Modify: `CREDITOS.md`
- Create: `docs/release-notes/v0.2.0.md`
- Test: `testes/test_empacotamento.py`

**Interfaces:**
- Consumes: nomes dos artefatos (`Pseudonimizador-Setup.exe`, `SHA256SUMS.txt`), `pseudonimizador.VERSAO == "0.2.0"`.
- Produces: texto que o controlador cola na release.

- [ ] **Step 1: Escrever os testes (vermelho)**

Acrescente a `testes/test_empacotamento.py`:
```python
def test_readme_tem_instalacao_do_usuario_e_montagem_do_mantenedor():
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    for exigido in ("## Instalação", "Releases", "Pseudonimizador-Setup.exe", "SmartScreen", "Mais informações",
                    "Executar assim mesmo", "Pasta dos arquivos", "Windows 10", "sem administrador",
                    "## Instalação para desenvolvimento", "## Montar o instalador", "empacotamento/construir.py",
                    "empacotamento/README.md"):
        assert exigido in texto, exigido


def test_creditos_citam_o_empacotamento_do_ulpiano():
    texto = (RAIZ / "CREDITOS.md").read_text(encoding="utf-8")
    assert "## Empacotamento" in texto and "Ulpiano" in texto and "empacotamento/" in texto


def test_notas_da_release_cobrem_requisitos_smartscreen_hash_e_limites():
    from pseudonimizador import VERSAO
    arquivo = RAIZ / "docs" / "release-notes" / f"v{VERSAO}.md"
    texto = arquivo.read_text(encoding="utf-8")
    for exigido in (f"v{VERSAO}", "Windows 10", "1809", "Windows 11", "64 bits", "administrador", "SmartScreen",
                    "Executar assim mesmo", "SHA-256", "certutil", "SHA256SUMS.txt", "Limitações", "3%",
                    "Praça", "Vila", "assinado", "nada sai do computador"):
        assert exigido in texto, exigido
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py`
Expected: os três novos FALHAM.

- [ ] **Step 3: README.md**

Substitua a seção `## Instalação` atual (as duas linhas do venv) por:
```markdown
## Instalação

Baixe `Pseudonimizador-Setup.exe` na página de Releases do repositório
(`https://github.com/msbastos/pseudonimizador/releases/latest`) e execute-o.
Requisitos: Windows 10 (1809 ou mais novo) ou Windows 11, 64 bits; instala
só para o seu usuário, sem administrador e sem internet.

- O instalador não é assinado digitalmente, então o Windows mostra o aviso
  do SmartScreen ("O Windows protegeu o computador"): clique em **Mais
  informações** e em **Executar assim mesmo**. Para conferir o arquivo,
  compare `certutil -hashfile Pseudonimizador-Setup.exe SHA256` com o
  `SHA256SUMS.txt` publicado junto.
- A única pergunta é a **Pasta dos arquivos** (padrão
  `Documentos\Pseudonimizador`), onde ficam `Entrada`, `Saida` e `Mapas`.
- Desinstalar (Configurações › Aplicativos) remove o programa e pergunta se
  apaga também as configurações; a pasta dos arquivos nunca é apagada.

## Instalação para desenvolvimento

    py -3.14 -m venv .venv
    .venv\Scripts\python -m pip install -r requirements.txt
```
E acrescente, antes de `## Testes`:
```markdown
## Montar o instalador

Para o mantenedor: `.venv\Scripts\python -X utf8 empacotamento/construir.py`
monta `build\app` (Python 3.14 embarcável, bibliotecas do `requirements.lock`
com hashes, CRT do Visual C++ app-local, código pelo manifesto), roda a fumaça
no Python embarcado e compila `dist\Pseudonimizador-Setup.exe` com o Inno
Setup 6. Pré-requisitos, aceitação no Windows Sandbox e conferência
pré-publicação: `empacotamento/README.md`.
```

- [ ] **Step 4: CREDITOS.md**

Acrescente ao fim:
```markdown

## Empacotamento

O instalador (`empacotamento/`: montagem com Python embarcável, lock com
hashes, CRT app-local, fumaça no Python embarcado, script do Inno Setup,
Sandbox e conferência pré-publicação) é adaptação do empacotamento do
**Ulpiano**, do mesmo autor, licenciado sob AGPL-3.0-only. O que é do Ulpiano
(Claude Code, DirectML, verificação de versão, tarefa agendada, skills) ficou
de fora.
```

- [ ] **Step 5: Notas da release**

`docs/release-notes/v0.2.0.md`:
```markdown
# Pseudonimizador v0.2.0 — primeiro instalador para Windows

## O que é

Aplicativo para Windows que protege dados pessoais em documentos avulsos
(contratos, petições, laudos), conforme a LGPD: recebe DOCX, PDF com texto ou
PDF escaneado, encontra nomes, documentos, contatos, endereços e dados
bancários, deixa você revisar e gera a versão protegida em Word ou PDF —
reversível (com mapa guardado à parte) ou definitiva. Tudo roda no próprio
computador: nada sai do computador, nem para o OCR.

## Requisitos

- Windows 10 (versão 1809 ou mais nova) ou Windows 11, 64 bits.
- Não precisa de administrador nem de internet: o instalador traz o Python
  e tudo o mais; instala só para o seu usuário.

## Instalar

1. Baixe `Pseudonimizador-Setup.exe` (abaixo) e execute-o.
2. O instalador não é assinado digitalmente, então o Windows mostra o
   SmartScreen ("O Windows protegeu o computador"): clique em **Mais
   informações** e em **Executar assim mesmo**.
3. Escolha a **Pasta dos arquivos** (padrão `Documentos\Pseudonimizador`).

### Conferir o arquivo (SHA-256)

No PowerShell ou no Prompt, na pasta do download:

    certutil -hashfile Pseudonimizador-Setup.exe SHA256

O resultado deve ser igual ao de `SHA256SUMS.txt`, publicado junto.

## Limitações conhecidas

- Imagens pequenas (menos de 3% da área da página) não passam pelo OCR:
  um carimbo ou uma assinatura digitalizada podem ficar sem leitura.
- Em endereços com "Praça" ou "Vila", o número do imóvel pode não ser
  reconhecido como parte do endereço.
- O instalador não é assinado: o aviso do SmartScreen aparece a cada versão.
- Só Windows 64 bits; não há versão para macOS.

## Desinstalar

Configurações › Aplicativos › Pseudonimizador. O desinstalador pergunta se
apaga também as configurações (padrão: não); a pasta dos arquivos — com os
mapas — nunca é apagada.
```

- [ ] **Step 6: Rodar os testes e as guardas**

Run: `.venv/Scripts/python -X utf8 testes/test_empacotamento.py && .venv/Scripts/python -X utf8 testes/test_sem_dados_reais.py && .venv/Scripts/python -X utf8 testes/test_licenca.py`
Expected: tudo passa.

- [ ] **Step 7: Commit**

```bash
git add README.md CREDITOS.md docs/release-notes/v0.2.0.md testes/test_empacotamento.py
git commit -m "Docs: Instalação para o usuário, Montar o instalador, crédito do empacotamento do Ulpiano e notas da v0.2.0

Co-Authored-By: <modelo que implementa> <noreply@anthropic.com>"
```

---

### Task 8: `verificar_publicacao.py` — conferência pré-publicação

**Files:**
- Create: `empacotamento/verificar_publicacao.py`
- Test: `testes/test_verificar_publicacao.py`

**Interfaces:**
- Consumes: `testes/executar_todos.py`, `testes/test_sem_dados_reais.py`, `git`, `dist\`.
- Produces: `email_permitido(email: str) -> bool`; `carregar_termos(caminho: Path) -> list[str]`; `varrer(texto: str, termos: list[str]) -> list[str]`; `emails_fora_do_github(linhas: str) -> list[str]`; `conferir_dist(dist: Path) -> list[str]`; `main(argv=None, *, executar=subprocess.run) -> int` (0 = pode publicar; 1 = há pendências, listadas). Flag `--sem-suite` pula a suíte (só para iterar; a conferência final roda sem ela).

- [ ] **Step 1: Escrever os testes (vermelho)**

`testes/test_verificar_publicacao.py` (as strings que parecem dado pessoal são montadas por concatenação para que nem este arquivo nem o histórico as contenham prontas):
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Conferência pré-publicação: varredura do histórico, e-mails dos commits, dist/."""
import _base  # noqa: F401
import hashlib
import tempfile
from pathlib import Path

from empacotamento import verificar_publicacao as V

EMAIL_PESSOAL = "alguem@" + "provedor-qualquer" + ".net"          # montado em partes: nunca aparece pronto no repositório
CAMINHO_MAQUINA = "\\".join(("C:", "Users", "fulano"))
GITHUB = "1+a@" + "users.noreply.github.com"            # idem: a guarda só conhece os domínios de exemplo


def test_email_permitido_so_os_dominios_de_placeholder_e_do_github():
    assert V.email_permitido(GITHUB)
    assert V.email_permitido("noreply@anthropic.com") and V.email_permitido("contato@exemplo.com.br")
    assert V.email_permitido("a@example.com") and V.email_permitido("x@sub.exemplo.com.br")
    assert not V.email_permitido(EMAIL_PESSOAL)


def test_varrer_acha_email_caminho_e_termos_sem_repetir():
    texto = (f"+Author: Fulano <{EMAIL_PESSOAL}>\n+caminho {CAMINHO_MAQUINA}\\x.txt\n"
             f"+de novo {CAMINHO_MAQUINA}\\y.txt\n+ok contato@exemplo.com.br e C:\\Users\\<usuário>\\z\n"
             "+relato: Beltrano Qualquer\n")
    achados = V.varrer(texto, ["Beltrano Qualquer", "Sicrano"])
    assert f"e-mail: {EMAIL_PESSOAL}" in achados and f"caminho: {CAMINHO_MAQUINA}" in achados
    assert "termo: Beltrano Qualquer" in achados and not any("Sicrano" in a for a in achados)
    assert len(achados) == 3, achados                               # o caminho repetido conta uma vez; <usuário> não conta
    assert V.varrer("+nada aqui\n", []) == []


def test_termos_ausentes_usa_so_os_padroes_embutidos():
    with tempfile.TemporaryDirectory() as d:
        assert V.carregar_termos(Path(d) / "nao-existe.txt") == []
        arq = Path(d) / "termos.txt"
        arq.write_text("# comentário\nBeltrano Qualquer\n\n  Sicrano  \n", encoding="utf-8")
        assert V.carregar_termos(arq) == ["Beltrano Qualquer", "Sicrano"]
    assert V.varrer(f"+{EMAIL_PESSOAL}\n", []) == [f"e-mail: {EMAIL_PESSOAL}"]


def test_emails_dos_commits_todos_do_github():
    ok = f"abc1234 {GITHUB} {GITHUB}\n"
    assert V.emails_fora_do_github(ok) == []
    ruim = ok + f"def5678 {EMAIL_PESSOAL} {GITHUB}\n"
    assert V.emails_fora_do_github(ruim) == [f"def5678: {EMAIL_PESSOAL}"]


def test_conferir_dist_exige_setup_e_sha256sums_batendo():
    with tempfile.TemporaryDirectory() as d:
        dist = Path(d)
        assert any("Pseudonimizador-Setup.exe" in p for p in V.conferir_dist(dist))
        setup = dist / "Pseudonimizador-Setup.exe"
        setup.write_bytes(b"MZ setup")
        assert any("SHA256SUMS.txt" in p for p in V.conferir_dist(dist))
        (dist / "SHA256SUMS.txt").write_text("0" * 64 + "  Pseudonimizador-Setup.exe\n", encoding="utf-8")
        assert any("não bate" in p for p in V.conferir_dist(dist))
        (dist / "SHA256SUMS.txt").write_text(f"{hashlib.sha256(b'MZ setup').hexdigest()}  Pseudonimizador-Setup.exe\n",
                                             encoding="utf-8")
        assert V.conferir_dist(dist) == []


def test_main_com_comandos_falsos_lista_as_pendencias_e_sai_1():
    class R:
        def __init__(self, rc, out=""):
            self.returncode, self.stdout, self.stderr = rc, out, ""
    with tempfile.TemporaryDirectory() as d:
        dist = Path(d) / "dist"
        dist.mkdir()
        chamadas = []

        def executar(args, **kw):
            chamadas.append(list(args))
            if "--format=%h %ae %ce" in args:
                return R(0, f"abc1234 {GITHUB} {GITHUB}\n")
            if "-p" in args:
                return R(0, f"+texto com {CAMINHO_MAQUINA}\n")
            return R(0)
        rc = V.main(["--dist", str(dist), "--termos", str(Path(d) / "nao-existe.txt")], executar=executar)
    assert rc == 1
    assert any("executar_todos.py" in " ".join(c) for c in chamadas)
    assert any("test_sem_dados_reais.py" in " ".join(c) for c in chamadas)
    assert any(c[:3] == ["git", "log", "--all"] for c in chamadas)


def test_main_tudo_limpo_sai_0():
    class R:
        def __init__(self, rc, out=""):
            self.returncode, self.stdout, self.stderr = rc, out, ""
    with tempfile.TemporaryDirectory() as d:
        dist = Path(d) / "dist"
        dist.mkdir()
        (dist / "Pseudonimizador-Setup.exe").write_bytes(b"MZ")
        (dist / "SHA256SUMS.txt").write_text(f"{hashlib.sha256(b'MZ').hexdigest()}  Pseudonimizador-Setup.exe\n",
                                             encoding="utf-8")

        def executar(args, **kw):
            if "--format=%h %ae %ce" in args:
                return R(0, f"abc1234 {GITHUB} {GITHUB}\n")
            return R(0, "+tudo limpo\n")
        assert V.main(["--dist", str(dist), "--termos", str(Path(d) / "x.txt"), "--sem-suite"], executar=executar) == 0


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `.venv/Scripts/python -X utf8 testes/test_verificar_publicacao.py`
Expected: `ImportError: cannot import name 'verificar_publicacao'`.

- [ ] **Step 3: Escrever o script**

`empacotamento/verificar_publicacao.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Conferência antes de publicar (spec §4). Não publica nada: só diz se pode.

    .venv\\Scripts\\python -X utf8 empacotamento/verificar_publicacao.py [--sem-suite]

1. a suíte inteira (testes/executar_todos.py) e a guarda test_sem_dados_reais.py;
2. varredura do histórico INTEIRO (git log --all -p) por e-mail fora dos domínios
   de placeholder, caminho de máquina (C:\\Users\\<nome>) e os termos de
   empacotamento/termos_proibidos.txt (lista local, ignorada pelo git, um termo
   por linha; se não existir, só os padrões embutidos valem);
3. autor e responsável de todo commit com o e-mail privado do GitHub;
4. dist\\ com Pseudonimizador-Setup.exe e SHA256SUMS.txt batendo.
Sai com 0 se tudo passa; 1 e a lista das pendências se não."""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOME_SETUP = "Pseudonimizador-Setup.exe"
RE_EMAIL = re.compile(r"[\w.+-]+@([\w-]+\.)+[a-z]{2,}", re.I)
RE_CAMINHO = re.compile(r"(?i)\b[a-z]:[\\/]+users[\\/]+(?!<)[^\\/\s\"'<>|]+")
DOMINIOS_PERMITIDOS = ("users.noreply.github.com", "anthropic.com")
TRECHOS_PERMITIDOS = ("exemplo", "example")


def email_permitido(email: str) -> bool:
    dominio = email.lower().rsplit("@", 1)[-1]
    return dominio.endswith(DOMINIOS_PERMITIDOS) or any(t in dominio for t in TRECHOS_PERMITIDOS)


def carregar_termos(caminho: Path) -> list[str]:
    if not Path(caminho).is_file():
        return []
    linhas = Path(caminho).read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in linhas if l.strip() and not l.strip().startswith("#")]


def varrer(texto: str, termos: list[str]) -> list[str]:
    achados: list[str] = []
    for m in RE_EMAIL.finditer(texto):
        if not email_permitido(m.group(0)):
            achados.append(f"e-mail: {m.group(0)}")
    for m in RE_CAMINHO.finditer(texto):
        achados.append(f"caminho: {m.group(0)}")
    for t in termos:
        if t in texto:
            achados.append(f"termo: {t}")
    return list(dict.fromkeys(achados))


def emails_fora_do_github(linhas: str) -> list[str]:
    fora = []
    for linha in linhas.splitlines():
        partes = linha.split()
        if len(partes) < 3:
            continue
        for email in partes[1:3]:
            if not email.lower().endswith("@users.noreply.github.com"):
                fora.append(f"{partes[0]}: {email}")
    return fora


def conferir_dist(dist: Path) -> list[str]:
    dist = Path(dist)
    setup, sums = dist / NOME_SETUP, dist / "SHA256SUMS.txt"
    if not setup.is_file():
        return [f"dist sem {NOME_SETUP}: rode empacotamento/construir.py"]
    if not sums.is_file():
        return ["dist sem SHA256SUMS.txt"]
    esperado = next((l.split()[0] for l in sums.read_text(encoding="utf-8").splitlines() if NOME_SETUP in l), "")
    real = hashlib.sha256(setup.read_bytes()).hexdigest()
    return [] if esperado == real else [f"SHA256SUMS.txt não bate com {NOME_SETUP} (esperado {esperado}, real {real})"]


def main(argv=None, *, executar=subprocess.run) -> int:
    ap = argparse.ArgumentParser(description="conferência antes de publicar; não publica nada")
    ap.add_argument("--dist", type=Path, default=RAIZ / "dist")
    ap.add_argument("--termos", type=Path, default=RAIZ / "empacotamento" / "termos_proibidos.txt")
    ap.add_argument("--sem-suite", action="store_true", help="pula a suíte (só para iterar)")
    args = ap.parse_args(argv)
    pendencias: list[str] = []
    kw = dict(cwd=str(RAIZ), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not args.sem_suite:
        print("1. suíte inteira")
        if executar([sys.executable, "-X", "utf8", str(RAIZ / "testes" / "executar_todos.py")], **kw).returncode != 0:
            pendencias.append("a suíte falhou (rode testes/executar_todos.py)")
    print("1b. guarda de dados reais")
    if executar([sys.executable, "-X", "utf8", str(RAIZ / "testes" / "test_sem_dados_reais.py")], **kw).returncode != 0:
        pendencias.append("test_sem_dados_reais.py falhou")
    print("2. histórico inteiro (git log --all -p)")
    termos = carregar_termos(args.termos)
    if not termos:
        print(f"   (sem {args.termos.name}: só os padrões embutidos)")
    log = executar(["git", "log", "--all", "-p", "--no-color"], **kw)
    if log.returncode != 0:
        pendencias.append("git log --all -p falhou")
    else:
        pendencias += [f"histórico: {a}" for a in varrer(log.stdout, termos)]
    print("3. e-mails dos commits")
    ids = executar(["git", "log", "--all", "--format=%h %ae %ce"], **kw)
    if ids.returncode != 0:
        pendencias.append("git log --format falhou")
    else:
        pendencias += [f"commit sem o e-mail privado do GitHub — {f}" for f in emails_fora_do_github(ids.stdout)]
    print("4. dist")
    pendencias += conferir_dist(args.dist)
    if pendencias:
        print("\nNÃO publique ainda:")
        for p in pendencias:
            print(f"  - {p}")
        return 1
    print("\nPode publicar: suíte verde, histórico limpo, commits com o e-mail do GitHub, dist conferido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Rodar os testes**

Run: `.venv/Scripts/python -X utf8 testes/test_verificar_publicacao.py && .venv/Scripts/python -X utf8 testes/test_sem_dados_reais.py && .venv/Scripts/python -X utf8 testes/test_licenca.py`
Expected: `7/7 passaram`, `1/1`, `4/4`.

- [ ] **Step 5: Rodar a conferência de verdade**

Run: `.venv/Scripts/python -X utf8 empacotamento/verificar_publicacao.py`
Expected: `Pode publicar: ...` (uns 2 min). Se listar pendências de "histórico:", **não** reescreva o histórico (regra: nunca reescrever histórico; repositório ainda não publicado, mas a decisão é do usuário): relate ao controlador os achados exatos. Um achado comum e inofensivo: o próprio `python-embarcavel.toml`/`README` não têm e-mail; se o `CREDITOS.md` ou os commits antigos mostrarem algo, relate.

- [ ] **Step 6: Suíte inteira e compileall**

Run: `.venv/Scripts/python -X utf8 testes/executar_todos.py && .venv/Scripts/python -W error -m compileall -q pseudonimizador empacotamento testes`
Expected: `N/N arquivos passaram` (45 arquivos: os 43 + `test_empacotamento.py` + `test_verificar_publicacao.py`) e nenhum aviso.

- [ ] **Step 7: Commit**

```bash
git add empacotamento/verificar_publicacao.py testes/test_verificar_publicacao.py
git commit -m "Empacotamento: verificar_publicacao.py (suíte, guarda, histórico inteiro, e-mails dos commits, dist)

Co-Authored-By: <modelo que implementa> <noreply@anthropic.com>"
```

Entrega ao controlador: `dist\Pseudonimizador-Setup.exe` + `dist\SHA256SUMS.txt` (fora do git), `docs/release-notes/v0.2.0.md` (corpo da release), o checklist do Sandbox em `empacotamento/README.md` §3 (manual) e a saída de `verificar_publicacao.py`. A publicação (`gh repo create msbastos/pseudonimizador --public`, `git push -u origin main`, `gh release create v0.2.0 dist\Pseudonimizador-Setup.exe dist\SHA256SUMS.txt --notes-file docs/release-notes/v0.2.0.md`) **não faz parte deste plano**.

---

## Auto-revisão (feita ao escrever o plano)

- **Cobertura da spec:** §2 Python embarcável com hash (Task 3/4), lock com hashes e `--no-deps --require-hashes --only-binary --platform --target` (Task 3/4), headless e sem SymPy com reversão registrada (Task 3/5), CRT app-local nunca do System32 (Task 4), manifesto fechado (Task 1), conferência pós-montagem de outra pasta sem rede com DOCX/PDF/OCR (Task 5), ISCC e saídas em `dist/` com `.wsb` (Task 4/6), `.gitignore` (Task 1). §3 `PrivilegesRequired=lowest`, pasta fixa, x64, `MinVersion`, pt-BR, ícone, versão, `AppMutex`, página única da pasta com `{userdocs}\Pseudonimizador` e chamada ao `configurar`, atalhos, "Abrir" ao terminar, `InstallDelete` só do programa, desinstalação com pergunta padrão Não e sem tocar a pasta dos arquivos (Task 6; a spec diz `pythonw` para o `configurar` — o plano usa `python.exe` com `SW_HIDE` e `ewWaitUntilTerminated`, porque só assim o instalador lê o código de saída; o resultado visual é o mesmo: janela escondida). §4 suíte, guarda, varredura do histórico, e-mails dos commits (Task 8), README (Task 7), notas (Task 7); `gh`/`push`/`release` deliberadamente fora.
- **Placeholders:** os únicos valores "a preencher" são a versão/hash do Python (Task 3, Step 5: procurados na python.org) e o estado da redução de tamanho no README (Task 5/6), ambos com instrução exata; o `<modelo que implementa>` no trailer é do controlador.
- **Consistência de nomes:** `construir.montar/fumacar/gerar_wsb/localizar_iscc/argumentos_iscc/FUMACA/NOME_SETUP`, `manifesto.arquivos_do_pacote/problemas`, `gerar_lock.filtrar/linhas_do_lock/problemas_do_lock/nome_e_versao`, `verificar_publicacao.varrer/carregar_termos/email_permitido/emails_fora_do_github/conferir_dist` são os mesmos nos testes e nas implementações; o `.iss` usa `PaginaPasta`, `ConfigExiste`, `ConfigFalhou`, `ApagarDadosResposta`, conferidos pelos testes da Task 6.
- **Review Focus:** cada um dos seis itens aponta o teste que o cobre (Tasks 1, 2, 3/4, 6, 8).
