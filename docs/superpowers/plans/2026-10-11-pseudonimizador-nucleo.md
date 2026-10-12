# Pseudonimizador — Plano 1: núcleo (motor, leitura, detecção, revisão, saídas, restauração e linha de comando)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Biblioteca e linha de comando que recebem um DOCX ou PDF (com texto ou escaneado), detectam os dados pessoais, aplicam a revisão e geram a saída protegida (layout original ou só texto, DOCX ou PDF, reversível ou definitiva), com conferência automática e restauração.

**Architecture:** O motor de pseudonimização é copiado do Ulpiano (texto → texto, com mapa de tókens) e ganha a função `trocas`, que devolve as substituições com posição no texto original. Os leitores transformam cada arquivo em um `Documento` (texto corrido + origem de cada caractere: run do DOCX ou retângulo do PDF); a detecção e a revisão trabalham só sobre o texto; as saídas usam as origens para trocar no lugar. A janela e a pasta monitorada ficam para o Plano 2, que usa esta biblioteca.

**Tech Stack:** Python 3.14 (Windows), PyMuPDF 1.28.0, python-docx 1.2.0, RapidOCR 3.9.2 + onnxruntime 1.24.4 (CPU), sem pytest (runner próprio).

**Spec:** `docs/superpowers/specs/2026-10-11-pseudonimizador-design.md`

## Global Constraints

- Repositório: `C:\Users\<usuário>\Claude\Pseudonimizador` (esta pasta). O Ulpiano fica na pasta irmã `../AplicativosMauricio` e **não é alterado** (só lido, para copiar o motor).
- Python do projeto: ambiente virtual `.venv` criado com `py -3.14 -m venv .venv`. Todos os comandos usam `PY=.venv/Scripts/python` e `-X utf8`, por exemplo `$PY -X utf8 testes/test_x.py`.
- Dependências fixas: `pymupdf==1.28.0`, `python-docx==1.2.0`, `rapidocr==3.9.2`, `onnxruntime==1.24.4`. Nenhuma outra sem pedir.
- Licença: todo `.py` rastreado começa com estas duas linhas, exatamente:
  `# SPDX-License-Identifier: AGPL-3.0-only`
  `# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.`
- Autoria: o nome do autor (Juiz do Trabalho Maurício Schmidt Bastos) aparece só em `CREDITOS.md` e `README.md`. Se algum código de `ulpiano/ocr/` do Ulpiano for copiado, `CREDITOS.md` tem de citar Jorge Alberto Araujo (este plano não copia nada de lá).
- Sem dado real: testes e docs usam só os dados sintéticos de `testes/fabrica.py`. Nenhum caminho da máquina (`C:\Users\<nome>`), nome de usuário ou e-mail pessoal em arquivo rastreado.
- Nenhuma conexão de rede além de `127.0.0.1`/`::1` em código ou teste.
- Logs e mensagens de exceção que forem gravados em arquivo nunca levam valores do documento. (Exceções mostradas na tela local podem citar o valor.)
- Comentários, mensagens e commits em português. TDD: teste vermelho primeiro, pelo motivo certo.
- Scripts com barra invertida: escreva o arquivo com a ferramenta Write, não com heredoc no Bash.
- Um commit por tarefa, terminando com a linha `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Nunca `git push` (não há remoto).

## Review Focus

1. **PDF com página girada (90°)**: a redação tem de cair sobre o nome, não ao lado; o texto original não pode sobrar. Teste em Task 10 (`test_pagina_girada_sem_vazamento`).
2. **DOCX com nome em caixa de texto, hyperlink ou revisão controlada**: tem de ser trocado como no corpo. Testes em Task 4 e Task 9.
3. **DOCX com nome em nota de rodapé** (que o python-docx não alcança): a geração tem de **falhar com aviso**, nunca sair com o nome. Teste em Task 11 (`test_nota_de_rodape_bloqueia`).
4. **Saída com nome de arquivo já existente**: não sobrescreve; ganha sufixo " (2)". Teste em Task 11 (`test_nao_sobrescreve`).
5. **Arquivo inválido** (PDF com senha, DOCX corrompido, extensão não aceita): erro claro `ErroDeLeitura`, nada gerado. Teste em Task 6 (`test_erros_de_leitura`).

---

## Estrutura de arquivos

```
.gitignore  requirements.txt  LICENSE  CREDITOS.md  README.md
pseudonimizador/
  __init__.py            VERSAO
  __main__.py            linha de comando (Task 13)
  motor/                 cópia do Ulpiano (Task 2) + trocas.py (Task 3)
    __init__.py pseudonimizador.py lexico.py lexico_ibge.json mapa.py
    reversor.py incertos.py nivel.py nivel_sinais.json trocas.py
  leitura/
    __init__.py          ler(caminho) -> Documento (Task 6)
    modelo.py            Documento, OrigemDocx, OrigemPdf, ErroDeLeitura (Task 4)
    docx_.py             preparar, paragrafos, runs_do_paragrafo, ler_docx (Task 4)
    pdf_.py              ler_pdf (Task 5)
    ocr.py               ocr_pagina (Task 6)
  deteccao/
    __init__.py          Ocorrencia, detectar (Task 7)
    candidatos.py        pessoas e empresas (Task 7)
  revisao.py             Item, Revisao, Resultado (Task 8)
  saida/
    __init__.py          gerar, Gerado (Task 11)
    texto.py             só texto: DOCX e PDF (Task 9)
    docx_layout.py       (Task 9)
    pdf_layout.py        (Task 10)
    conferencia.py       (Task 11)
    mapas.py             (Task 11)
  restaurar.py           (Task 12)
testes/
  _base.py _runner.py executar_todos.py fabrica.py
  test_licenca.py test_sem_dados_reais.py test_sem_rede.py
  test_motor_*.py (cópias, Task 2) test_trocas.py test_leitura_docx.py
  test_leitura_pdf.py test_leitura_ocr.py test_deteccao.py test_revisao.py
  test_saida_texto.py test_saida_docx.py test_saida_pdf.py test_gerar.py
  test_restaurar.py test_cli.py test_ponta_a_ponta.py
```

---

### Task 1: Esqueleto do repositório, testes e guardas

**Files:**
- Create: `.gitignore`, `requirements.txt`, `LICENSE` (cópia do Ulpiano), `CREDITOS.md`, `README.md`, `pseudonimizador/__init__.py`
- Create: `testes/_base.py`, `testes/_runner.py`, `testes/executar_todos.py`, `testes/test_licenca.py`, `testes/test_sem_dados_reais.py`

**Interfaces:**
- Produces: `pseudonimizador.VERSAO: str`; `testes/_base.py` (põe a raiz no `sys.path`, importado no topo de cada teste com `import _base  # noqa: F401`); `testes/_runner.rodar(globals())` (chamado no fim de cada teste).

- [ ] **Step 1: Criar o ambiente e as dependências**

`requirements.txt`:
```
pymupdf==1.28.0
python-docx==1.2.0
rapidocr==3.9.2
onnxruntime==1.24.4
```
`.gitignore`:
```
.venv/
__pycache__/
*.pyc
saida_testes/
*.tmp
```
Run:
```bash
py -3.14 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp ../AplicativosMauricio/LICENSE LICENSE
```
Expected: instalação sem erro; `LICENSE` começa com "GNU AFFERO GENERAL PUBLIC LICENSE".

- [ ] **Step 2: Escrever os testes de guarda (vermelhos)**

`testes/_base.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Importado no topo de cada teste: põe a raiz do projeto no sys.path."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
```
`testes/_runner.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Runner dos testes (sem pytest). No fim de cada testes/test_*.py:

    if __name__ == "__main__":
        from _runner import rodar
        rodar(globals())

Roda toda função test_* em ordem alfabética, imprime ok/FALHA e sai com 1
se houver falha (é o que testes/executar_todos.py lê)."""
import os
import sys


def rodar(globais: dict) -> None:
    os.environ.setdefault("PSEUDONIMIZADOR_TESTE", "1")
    testes = [(n, f) for n, f in sorted(globais.items()) if n.startswith("test_") and callable(f)]
    falhas = 0
    for nome, fn in testes:
        try:
            fn()
            print(f"ok    {nome}")
        except AssertionError as e:
            falhas += 1
            print(f"FALHA {nome}\n      {e}")
        except Exception as e:  # noqa: BLE001
            falhas += 1
            print(f"FALHA {nome}\n      {e!r}")
    print(f"\n{len(testes) - falhas}/{len(testes)} passaram, {falhas} falha(s)")
    sys.exit(1 if falhas else 0)
```
`testes/executar_todos.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Roda a suíte inteira, cada arquivo no seu processo, em paralelo.
Arquivo marcado com "# executar_todos: sozinho" nas 15 primeiras linhas roda
depois, sozinho. PSEUDONIMIZADOR_TESTES_TRABALHOS=1 roda tudo em série."""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
MARCA_SOZINHO = "# executar_todos: sozinho"


def _rodar(arq: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-X", "utf8", str(arq)], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def _sozinho(arq: Path) -> bool:
    with open(arq, encoding="utf-8", errors="replace") as f:
        return any(l.startswith(MARCA_SOZINHO) for l, _ in zip(f, range(15)))


def _trabalhos() -> int:
    try:
        return max(1, int(os.environ["PSEUDONIMIZADOR_TESTES_TRABALHOS"]))
    except (KeyError, ValueError):
        return min(8, os.cpu_count() or 2)


def main() -> int:
    arquivos = sorted(RAIZ.glob("test_*.py"))
    os.environ["PSEUDONIMIZADOR_TESTE"] = "1"
    comuns = [a for a in arquivos if not _sozinho(a)]
    resultados = {}
    with ThreadPoolExecutor(max_workers=_trabalhos()) as pool:
        resultados.update(zip(comuns, pool.map(_rodar, comuns)))
    for arq in arquivos:
        if arq not in resultados:
            resultados[arq] = _rodar(arq)
    falharam = []
    for arq in arquivos:
        proc = resultados[arq]
        situacao = "ok   " if proc.returncode == 0 else "FALHA"
        print(f"{situacao} {arq.name}")
        if proc.returncode != 0:
            falharam.append(arq.name)
            for linha in (proc.stdout + proc.stderr).splitlines():
                if linha.startswith(("FALHA", "      ", "Traceback", "  File", "    ")) or "Error" in linha:
                    print(f"      {linha}")
    print(f"\n{len(arquivos) - len(falharam)}/{len(arquivos)} arquivos passaram")
    return 1 if falharam else 0


if __name__ == "__main__":
    sys.exit(main())
```
`testes/test_licenca.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Guarda de licença e autoria: cabeçalho SPDX em todo .py, LICENSE e CREDITOS."""
import _base  # noqa: F401
import subprocess
from _base import RAIZ

L1 = "# SPDX-License-Identifier: AGPL-3.0-only"
L2 = "# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md."


def _arquivos_do_projeto() -> list[str]:
    saida = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                           cwd=RAIZ, capture_output=True, text=True, encoding="utf-8").stdout
    return [l for l in saida.splitlines() if l.strip()]


def test_todo_py_tem_cabecalho_spdx():
    sem = []
    for rel in _arquivos_do_projeto():
        if rel.endswith(".py"):
            linhas = (RAIZ / rel).read_text(encoding="utf-8").splitlines()[:2]
            if linhas != [L1, L2]:
                sem.append(rel)
    assert not sem, f"sem cabeçalho SPDX: {sem}"


def test_licenca_e_creditos():
    assert (RAIZ / "LICENSE").read_text(encoding="utf-8").lstrip().startswith("GNU AFFERO GENERAL PUBLIC LICENSE")
    creditos = (RAIZ / "CREDITOS.md").read_text(encoding="utf-8")
    assert "Maurício Schmidt Bastos" in creditos and "Ulpiano" in creditos


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
`testes/test_sem_dados_reais.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Guarda: nenhum caminho da máquina, nome de usuário ou e-mail pessoal em
arquivo do projeto. Os dados de teste são os sintéticos de testes/fabrica.py."""
import _base  # noqa: F401
import getpass
import os
import re
from _base import RAIZ
from test_licenca import _arquivos_do_projeto

RE_CAMINHO = re.compile(r"(?i)\b[a-z]:[\\/]+users[\\/]+(?!<)[^\\/\s]+")
RE_EMAIL = re.compile(r"[\w.+-]+@([\w-]+\.)+[a-z]{2,}", re.I)
DOMINIOS_PERMITIDOS = ("exemplo.com.br", "example.com", "anthropic.com")
BINARIOS = (".json", ".png", ".jpg", ".pdf", ".docx", ".onnx")


def _usuarios() -> set[str]:
    nomes = {os.environ.get("USERNAME", ""), os.environ.get("USER", "")}
    try:
        nomes.add(getpass.getuser())
    except Exception:  # noqa: BLE001
        pass
    return {n.lower() for n in nomes if len(n) >= 3}


def test_sem_caminho_usuario_ou_email():
    achados = []
    usuarios = _usuarios()
    for rel in _arquivos_do_projeto():
        if rel.lower().endswith(BINARIOS) or rel == "LICENSE":
            continue
        texto = (RAIZ / rel).read_text(encoding="utf-8", errors="replace")
        if RE_CAMINHO.search(texto):
            achados.append(f"{rel}: caminho da máquina")
        for m in RE_EMAIL.finditer(texto):
            if not m.group(0).lower().endswith(DOMINIOS_PERMITIDOS):
                achados.append(f"{rel}: e-mail {m.group(0)}")
        baixo = texto.lower()
        for u in usuarios:
            if re.search(r"(?<![a-z0-9])" + re.escape(u) + r"(?![a-z0-9])", baixo):
                achados.append(f"{rel}: nome de usuário")
    assert not achados, "\n".join(achados)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `.venv/Scripts/python -X utf8 testes/test_licenca.py`
Expected: FALHA em `test_licenca_e_creditos` (CREDITOS.md não existe).

- [ ] **Step 4: Criar CREDITOS, README e o pacote**

`CREDITOS.md`:
```markdown
# Créditos e autoria

O **Pseudonimizador** foi desenvolvido e é mantido pelo **Juiz do Trabalho
Maurício Schmidt Bastos (TRT4)**.

## Origem do motor

O motor de pseudonimização (`pseudonimizador/motor/`) é cópia do pacote
`ulpiano/nucleo/privacidade/` do **Ulpiano**, do mesmo autor (commit `5bab2ff`,
11/10/2026), licenciado sob AGPL-3.0-only. As alterações feitas na cópia estão
descritas no cabeçalho de cada arquivo e no histórico deste repositório.
```
`README.md`:
```markdown
# Pseudonimizador

Aplicativo para Windows que protege dados pessoais em documentos avulsos
(contratos, petições, laudos), conforme a LGPD. Recebe DOCX, PDF com texto ou
PDF escaneado, encontra nomes, documentos, contatos, endereços e dados
bancários, deixa você revisar e gera a versão protegida em Word ou PDF —
reversível (pseudonimização, com mapa guardado à parte) ou definitiva
(anonimização). Tudo roda no próprio computador.

Autoria: Juiz do Trabalho Maurício Schmidt Bastos (TRT4). Ver `CREDITOS.md`.
Licença: AGPL-3.0-only.

## Instalação

    py -3.14 -m venv .venv
    .venv\Scripts\python -m pip install -r requirements.txt

## Uso pela linha de comando

    .venv\Scripts\python -X utf8 -m pseudonimizador --help

## Testes

    .venv\Scripts\python -X utf8 testes/executar_todos.py
```
`pseudonimizador/__init__.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Pseudonimizador: proteção de dados pessoais em documentos avulsos (LGPD)."""
VERSAO = "0.1.0"
```

- [ ] **Step 5: Rodar a suíte e ver passar**

Run: `.venv/Scripts/python -X utf8 testes/executar_todos.py`
Expected: `2/2 arquivos passaram`.

- [ ] **Step 6: Commit**

```bash
git add .gitignore requirements.txt LICENSE CREDITOS.md README.md pseudonimizador testes
git commit -m "Esqueleto do Pseudonimizador: pacote, runner de testes e guardas de licença e de dados reais

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Cópia do motor do Ulpiano, sem os laços com o resto do Ulpiano

**Files:**
- Create: `pseudonimizador/motor/{__init__,pseudonimizador,lexico,mapa,reversor,incertos,nivel}.py`, `lexico_ibge.json`, `nivel_sinais.json` (cópias)
- Modify (na cópia): `motor/mapa.py` (+`escrever_atomico`, +`novo_mapa`), `motor/nivel.py`, `motor/incertos.py`, `motor/pseudonimizador.py` (`_passa_nos_vetos_do_rotulo`)
- Create: `testes/test_motor_*.py` (cópias dos testes do motor), `testes/test_motor_independente.py`

> Desvio consciente da spec §4: `nivel.py` e `nivel_sinais.json` vêm junto (em vez de "módulo mínimo"), porque `incertos.sensivel_ou_endereco` e várias funções do motor leem `SINAIS` e `tokens_vigiados`. O efeito pedido pela spec é obtido fixando `do_mapa` em `"sigiloso"`: nomes **e** empresas sempre em código.

**Interfaces:**
- Produces: `pseudonimizador.motor.pseudonimizador.pseudonimizar(texto: str, mapa: dict, conversa: bool = False) -> str`; `motor.mapa.token_para(mapa, prefixo, categoria, valor, papel=None) -> str`; `motor.mapa.normalizar(s) -> str`; `motor.mapa.novo_mapa() -> dict` (`{"schema_version": 1, "nivel": "sigiloso", "criado_em": ISO, "tokens": {}}`); `motor.mapa.escrever_atomico(caminho: Path, texto: str) -> None`; `motor.reversor.despseudonimizar_texto(texto, mapa) -> str`, `motor.reversor.despseudonimizar_docx(caminho: Path, mapa) -> int`, `motor.reversor.TokenOrfao`.

- [ ] **Step 1: Escrever o teste de independência (vermelho)**

`testes/test_motor_independente.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""O motor copiado não depende de nada do Ulpiano e troca tudo, sempre."""
import _base  # noqa: F401
import re
from _base import RAIZ


def test_nenhum_import_fora_do_motor():
    for arq in (RAIZ / "pseudonimizador" / "motor").glob("*.py"):
        texto = arq.read_text(encoding="utf-8")
        assert not re.search(r"^\s*from\s+\.\.", texto, re.M), f"{arq.name} importa de fora do motor"
        assert not re.search(r"^\s*(from|import)\s+ulpiano\b", texto, re.M), f"{arq.name} importa o Ulpiano"


def test_nomes_e_empresas_sempre_em_codigo():
    from pseudonimizador.motor import mapa as M
    from pseudonimizador.motor.pseudonimizador import pseudonimizar
    mapa = M.novo_mapa()
    M.token_para(mapa, "PESSOA", "pessoa", "Maria Aparecida Pereira")
    M.token_para(mapa, "EMPRESA", "pj", "Exemplo Comércio de Tecidos Ltda.")
    saida = pseudonimizar("Maria Aparecida Pereira assina por Exemplo Comércio de Tecidos Ltda.", mapa)
    assert "Maria" not in saida and "Exemplo" not in saida, saida
    assert "[[PESSOA_1]]" in saida and "[[EMPRESA_1]]" in saida, saida


def test_escrever_atomico(tmp=RAIZ / "saida_testes" / "atomico.json"):
    from pseudonimizador.motor.mapa import escrever_atomico
    escrever_atomico(tmp, '{"a": 1}')
    assert tmp.read_text(encoding="utf-8") == '{"a": 1}'
    assert not tmp.with_suffix(".json.tmp").exists()


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
Run: `.venv/Scripts/python -X utf8 testes/test_motor_independente.py`
Expected: FALHA (`ModuleNotFoundError: pseudonimizador.motor`).

- [ ] **Step 2: Copiar os arquivos**

```bash
mkdir -p pseudonimizador/motor
U=../AplicativosMauricio/ulpiano/nucleo/privacidade
cp $U/__init__.py $U/pseudonimizador.py $U/lexico.py $U/lexico_ibge.json $U/mapa.py \
   $U/reversor.py $U/incertos.py $U/nivel.py $U/nivel_sinais.json pseudonimizador/motor/
```
Em cada `.py` copiado, logo depois das duas linhas SPDX, acrescente a linha:
```python
# Origem: Ulpiano, ulpiano/nucleo/privacidade/<arquivo>.py, commit 5bab2ff (11/10/2026); alterações descritas abaixo.
```
(substitua `<arquivo>` pelo nome). Se `__init__.py` não tiver as linhas SPDX, ponha-as.

- [ ] **Step 3: Cortar os laços**

Em `motor/mapa.py`, acrescente ao fim:
```python
def escrever_atomico(caminho: Path, texto: str) -> None:
    """Grava num .tmp ao lado e troca de uma vez (os.replace): nunca deixa o
    arquivo pela metade. Substitui ulpiano.nucleo.execucao.escrever_atomico."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(caminho.suffix + ".tmp")
    tmp.write_text(texto, encoding="utf-8")
    os.replace(tmp, caminho)


def novo_mapa() -> dict:
    """Mapa vazio de um documento avulso: sempre no nível que troca nomes e empresas."""
    return {"schema_version": SCHEMA_VERSION, "nivel": "sigiloso",
            "criado_em": datetime.now().isoformat(timespec="seconds"), "tokens": {}}
```
Em `motor/nivel.py`:
- em `do_mapa`, troque o corpo por `return SIGILOSO` e a docstring por `"""Documento avulso: sempre sigiloso (nomes e empresas em código; spec §2)."""`;
- em `_atestado_do_seletor`, troque o bloco `try: ... except ...` inteiro por `return False` (não há seletor fora do Ulpiano);
- em `_gravar`, troque `from ..execucao import escrever_atomico` por `from .mapa import escrever_atomico`.

Em `motor/incertos.py`, em `_gravar_pedido`, troque `from ..execucao import escrever_atomico` por `from .mapa import escrever_atomico`.

Em `motor/pseudonimizador.py`, em `_passa_nos_vetos_do_rotulo`, apague as duas linhas:
```python
    from ..segmentador.taxonomia import classificar   # import tardio: so' a montagem do documento de menor chega aqui
    if classificar(nome)[2] == "tabela":
        return False
```
(são três linhas: o import, o `if` e o `return False`).

Run: `grep -n "from \.\." pseudonimizador/motor/*.py`
Expected: nenhuma linha.

- [ ] **Step 4: Rodar o teste de independência**

Run: `.venv/Scripts/python -X utf8 testes/test_motor_independente.py`
Expected: `3/3 passaram`.

- [ ] **Step 5: Copiar os testes do motor**

```bash
T=../AplicativosMauricio/testes
for f in $T/test_pseudonimizador*.py $T/test_mapa_pseudonimos.py $T/test_reversor.py $T/test_lexico_ibge.py; do
  b=$(basename $f .py); cp "$f" "testes/test_motor_${b#test_}.py"
done
rm testes/test_motor_pseudonimizador_nivel.py
sed -i 's/ulpiano\.nucleo\.privacidade/pseudonimizador.motor/g' testes/test_motor_*.py
```
Em cada arquivo copiado: garanta as duas linhas SPDX no topo; se ele monta o `sys.path` à mão, mantenha (a estrutura `testes/` + raiz é a mesma); se importa `_runner`, funciona igual. Se algum usa arquivo auxiliar do Ulpiano (por exemplo `cnj_sinteticos.txt`), copie o auxiliar para `testes/`.

- [ ] **Step 6: Rodar os testes copiados e tratar as falhas**

Run: `for f in testes/test_motor_*.py; do .venv/Scripts/python -X utf8 $f | tail -1; done`

Se um arquivo inteiro falha já no import (por exemplo `from ulpiano.nucleo.execucao import ...` ou `from pseudonimizador.motor.nivel import decidir`, que fica sem uso aqui), tire o import e as funções que dependem dele; se o arquivo inteiro for sobre aquilo, apague o arquivo e anote.

Para cada falha, leia a mensagem e classifique:
- **por causa do nível fixo** (o teste espera nome ou empresa em claro nos níveis público/protegido): apague a função de teste e anote o nome dela;
- **por depender de algo do Ulpiano que saiu** (seletor, montador, taxonomia, dossiê): apague a função e anote;
- **qualquer outro motivo**: pare e relate — é defeito da cópia.

Expected ao final: todos os `test_motor_*.py` com 0 falha.

- [ ] **Step 7: Suíte e commit**

Run: `.venv/Scripts/python -X utf8 testes/executar_todos.py` → tudo ok.
Se `test_sem_dados_reais` acusar um e-mail de exemplo no código copiado, acrescente o domínio a `DOMINIOS_PERMITIDOS` **só se for claramente fictício** (por exemplo `exemplo.com`); qualquer outro achado: pare e relate.
```bash
git add pseudonimizador/motor testes
git commit -m "Motor de pseudonimização copiado do Ulpiano (5bab2ff), sem laços com o Ulpiano

Nível fixo em sigiloso (nomes e empresas sempre em código); gravação atômica
local; sem seletor nem taxonomia. Testes do motor copiados; removidos os que
dependiam de nível ou do fluxo de autos: <lista anotada no Step 6>.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Trocas com posição no texto original

**Files:**
- Modify: `pseudonimizador/motor/pseudonimizador.py` (dividir `_pseudonimizar` em `_spans_finais` + montagem)
- Create: `pseudonimizador/motor/trocas.py`
- Test: `testes/test_trocas.py`

**Interfaces:**
- Consumes: `motor.pseudonimizador.pseudonimizar`, `texto_limpo`, `RE_INVISIVEIS`, `_RE_SEPARADOR_INVISIVEL`, `RE_CITACAO_DE_DOCUMENTO`, `_copia_com_nomes`.
- Produces: `motor.trocas.Troca(NamedTuple: ini: int, fim: int, token: str)`; `motor.trocas.limpar_com_indices(texto: str) -> tuple[str, list[int], list[int]]` (texto limpo e, para cada caractere dele, início e fim no original); `motor.trocas.trocas(texto: str, mapa: dict, conversa: bool = False) -> list[Troca]` (posições no texto **original**, ordenadas, sem sobreposição); `motor.trocas.aplicar_trocas(texto: str, trocas: list[Troca]) -> str`.

- [ ] **Step 1: Teste vermelho**

`testes/test_trocas.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import unicodedata
from pseudonimizador.motor import mapa as M
from pseudonimizador.motor.pseudonimizador import pseudonimizar, texto_limpo
from pseudonimizador.motor.trocas import Troca, aplicar_trocas, limpar_com_indices, trocas

TEXTO = ("LOCADOR: Maria Aparecida Pereira, CPF 111.444.777-35, residente na Rua das Acácias, 120, "
         "telefone (51) 99876-5432, e-mail contato@exemplo.com.br.\n"
         "LOCATÁRIA: Exemplo Comércio de Tecidos Ltda., CNPJ 11.222.333/0001-81.")


def _mapa():
    mapa = M.novo_mapa()
    M.token_para(mapa, "PESSOA", "pessoa", "Maria Aparecida Pereira")
    M.token_para(mapa, "EMPRESA", "pj", "Exemplo Comércio de Tecidos Ltda.")
    return mapa


def test_aplicar_trocas_da_o_mesmo_que_pseudonimizar():
    t = trocas(TEXTO, _mapa())
    assert aplicar_trocas(TEXTO, t) == pseudonimizar(TEXTO, _mapa())
    assert all(isinstance(x, Troca) for x in t)
    assert [x.ini for x in t] == sorted(x.ini for x in t)


def test_posicoes_apontam_o_trecho_original():
    t = trocas(TEXTO, _mapa())
    trechos = {TEXTO[x.ini:x.fim] for x in t}
    assert "Maria Aparecida Pereira" in trechos
    assert "111.444.777-35" in trechos


def test_texto_decomposto_e_hifen_condicional():
    original = unicodedata.normalize("NFD", "Assina João Carlos Souza e MA\u00adRIA APARECIDA PEREIRA.")
    mapa = M.novo_mapa()
    M.token_para(mapa, "PESSOA", "pessoa", "João Carlos Souza")
    M.token_para(mapa, "PESSOA", "pessoa", "Maria Aparecida Pereira")
    t = trocas(original, mapa)
    assert texto_limpo(aplicar_trocas(original, t)) == pseudonimizar(original, mapa)
    assert all(original[x.ini:x.fim].strip() for x in t)


def test_limpar_com_indices():
    original = "e\u0301 a\u200bb"
    limpo, ini, fim = limpar_com_indices(original)
    assert limpo == texto_limpo(original)
    assert len(limpo) == len(ini) == len(fim)
    assert (ini[0], fim[0]) == (0, 2)        # "é" composto vem dos dois caracteres


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
Run: `.venv/Scripts/python -X utf8 testes/test_trocas.py` → FALHA (`No module named ...trocas`).

- [ ] **Step 2: Dividir `_pseudonimizar` no motor**

Em `motor/pseudonimizador.py`, substitua a função `_pseudonimizar` inteira (no fim do arquivo) por:
```python
def _spans_finais(texto: str, mapa: dict, texto_dos_nomes: str | None = None,
                  conversa: bool = False) -> list[tuple[int, int, str]]:
    """Os trechos que _pseudonimizar troca, já ordenados e sem sobreposição
    (Pseudonimizador, 11/10/2026: separado da montagem para que a troca no
    lugar — DOCX, PDF — use as mesmas posições)."""
    urls = _urls(texto)
    spans_nomes = (_spans_de_nomes(texto_dos_nomes, mapa, original=texto, urls=urls)
                   if texto_dos_nomes is not None else _spans_de_nomes(texto, mapa, urls=urls))
    # a URL tokenizada leva junto o nome que estiver dentro dela
    spans_url = _spans_de_urls(texto, mapa, urls, spans_nomes)
    tomados_por_url = [(ini, fim) for ini, fim, _ in spans_url]
    spans_nomes = [s for s in spans_nomes if _livre(s[0], s[1], tomados_por_url)]
    spans_pj = []
    if nivel_mod.empresas_em_codigo(nivel_mod.do_mapa(mapa)):
        spans_pj = _spans_de_pj(texto, mapa, tomados_por_url, spans_nomes)
        # a denominacao que contem o nome do dono leva o nome junto (vira inteira o codigo da empresa)
        spans_nomes = [s for s in spans_nomes
                       if not any(p0 <= s[0] and s[1] <= p1 for p0, p1, _ in spans_pj)]
    spans_ident = _spans_de_identificadores(texto, mapa, conversa)
    tomados_por_nome = [(ini, fim) for ini, fim, _ in spans_nomes + spans_url + spans_pj]
    spans_ident = [s for s in spans_ident
                   if _livre(s[0], s[1], tomados_por_nome)]
    spans = spans_nomes + spans_url + spans_pj + spans_ident
    spans.sort(key=lambda s: s[0])
    finais: list[tuple[int, int, str]] = []
    fim_do_ultimo = -1
    for ini, fim, tok in spans:
        if ini < fim_do_ultimo:
            continue  # sobreposicao residual: fica o que comeca antes
        finais.append((ini, fim, tok))
        fim_do_ultimo = fim
    return finais


def _pseudonimizar(texto: str, mapa: dict, texto_dos_nomes: str | None = None, conversa: bool = False) -> str:
    partes: list[str] = []
    pos = 0
    for ini, fim, tok in _spans_finais(texto, mapa, texto_dos_nomes, conversa):
        partes.append(texto[pos:ini])
        partes.append(tok)
        pos = fim
    partes.append(texto[pos:])
    return "".join(partes)
```
Run: `for f in testes/test_motor_*.py; do .venv/Scripts/python -X utf8 $f | tail -1; done` → todos sem falha (refatoração pura).

- [ ] **Step 3: Escrever `motor/trocas.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Trocas com posição no texto ORIGINAL (spec §4): o motor trabalha sobre o
texto limpo (NFC, sem invisíveis); aqui se guarda, para cada caractere do
texto limpo, de onde ele veio, e as trocas voltam para as posições originais."""
from __future__ import annotations

import unicodedata
from typing import NamedTuple

from .pseudonimizador import (RE_CITACAO_DE_DOCUMENTO, RE_INVISIVEIS, _RE_SEPARADOR_INVISIVEL,
                              _copia_com_nomes, _spans_finais, texto_limpo)


class Troca(NamedTuple):
    ini: int
    fim: int
    token: str


def _nfc_rastreado(s: str, ini: list[int], fim: list[int]):
    """NFC grupo a grupo (caractere-base + combinantes); cada caractere
    resultante herda o início do primeiro e o fim do último do grupo."""
    out: list[str] = []
    oi: list[int] = []
    of: list[int] = []
    j, n = 0, len(s)
    while j < n:
        k = j + 1
        while k < n and unicodedata.combining(s[k]):
            k += 1
        grupo = unicodedata.normalize("NFC", s[j:k])
        out.append(grupo)
        oi.extend([ini[j]] * len(grupo))
        of.extend([fim[k - 1]] * len(grupo))
        j = k
    return "".join(out), oi, of


def _sub_rastreado(regex, repl: str, s: str, ini: list[int], fim: list[int]):
    """regex.sub(repl, s) guardando a origem: o trecho trocado por `repl`
    (um caractere ou nada) herda o início e o fim do trecho."""
    out: list[str] = []
    oi: list[int] = []
    of: list[int] = []
    pos = 0
    for m in regex.finditer(s):
        a, b = m.span()
        if a == b:
            continue
        out.append(s[pos:a]); oi.extend(ini[pos:a]); of.extend(fim[pos:a])
        if repl:
            out.append(repl); oi.append(ini[a]); of.append(fim[b - 1])
        pos = b
    out.append(s[pos:]); oi.extend(ini[pos:]); of.extend(fim[pos:])
    return "".join(out), oi, of


def limpar_com_indices(texto: str) -> tuple[str, list[int], list[int]]:
    """O mesmo que texto_limpo(texto), com a origem de cada caractere."""
    ini = list(range(len(texto)))
    fim = [i + 1 for i in ini]
    s, ini, fim = _nfc_rastreado(texto, ini, fim)
    s, ini, fim = _sub_rastreado(_RE_SEPARADOR_INVISIVEL, " ", s, ini, fim)
    s, ini, fim = _sub_rastreado(RE_INVISIVEIS, "", s, ini, fim)
    s, ini, fim = _nfc_rastreado(s, ini, fim)
    if s != texto_limpo(texto):
        raise ValueError("a normalização por grupo divergiu da do texto inteiro")
    return s, ini, fim


def trocas(texto: str, mapa: dict, conversa: bool = False) -> list[Troca]:
    limpo, ini, fim = limpar_com_indices(texto)
    citacoes = [m.span() for m in RE_CITACAO_DE_DOCUMENTO.finditer(limpo)]
    copia = _copia_com_nomes(limpo, mapa, citacoes) if citacoes else None
    return [Troca(ini[a], fim[b - 1], tok) for a, b, tok in _spans_finais(limpo, mapa, copia, conversa)]


def aplicar_trocas(texto: str, lista: list[Troca]) -> str:
    partes: list[str] = []
    pos = 0
    for t in sorted(lista):
        partes.append(texto[pos:t.ini])
        partes.append(t.token)
        pos = t.fim
    partes.append(texto[pos:])
    return "".join(partes)
```

- [ ] **Step 4: Rodar**

Run: `.venv/Scripts/python -X utf8 testes/test_trocas.py` → `4/4 passaram`.

- [ ] **Step 5: Commit**

```bash
git add pseudonimizador/motor testes/test_trocas.py
git commit -m "Motor: trocas com posição no texto original (para trocar no lugar em DOCX e PDF)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Modelo do documento, fábrica de documentos sintéticos e leitura de DOCX

**Files:**
- Create: `pseudonimizador/leitura/__init__.py` (vazio por ora, só cabeçalho), `leitura/modelo.py`, `leitura/docx_.py`
- Create: `testes/fabrica.py`
- Test: `testes/test_leitura_docx.py`

**Interfaces:**
- Produces:
  - `leitura.modelo.ErroDeLeitura(Exception)`
  - `leitura.modelo.OrigemDocx(frozen dataclass: paragrafo: int, run: int, pos: int)`
  - `leitura.modelo.OrigemPdf(frozen dataclass: pagina: int, rect: tuple[float, float, float, float], ocr: bool)`
  - `leitura.modelo.Documento(dataclass: caminho: Path, tipo: str, texto: str, origens: list[OrigemDocx | OrigemPdf | None], avisos: list[str] = [], paginas_ocr: list[int] = [])` — `tipo` ∈ `{"docx", "pdf_texto", "pdf_ocr", "pdf_misto"}`; `len(origens) == len(texto)`; separadores sintéticos têm origem `None`.
  - `leitura.docx_.preparar(doc) -> None` (aceita revisões controladas, tira marcas de comentário); `leitura.docx_.paragrafos(doc) -> list[Paragraph]` (ordem fixa: corpo com tabelas, caixas de texto do corpo, cabeçalhos/rodapés definidos); `leitura.docx_.runs_do_paragrafo(par) -> list[Run]` (inclui runs de hyperlink); `leitura.docx_.ler_docx(caminho: Path) -> Documento`.
  - `testes/fabrica.py`: constantes `PESSOA_1`, `PESSOA_2`, `EMPRESA`, `CPF`, `CNPJ`, `EMAIL`, `TELEFONE`, `ENDERECO`, `LINHAS_CONTRATO: list[str]`; funções `contrato_docx(caminho) -> Path`, `contrato_pdf(caminho, girar: int = 0) -> Path`, `contrato_escaneado(caminho) -> Path`, `pasta_temporaria(nome) -> Path`.

- [ ] **Step 1: Fábrica de documentos sintéticos**

`testes/fabrica.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Documentos SINTÉTICOS para os testes (nomes, números e endereço inventados;
o CPF e o CNPJ são os exemplos clássicos de dígito verificador válido)."""
import _base  # noqa: F401
import shutil
from pathlib import Path

from _base import RAIZ

PESSOA_1 = "Maria Aparecida Pereira"
PESSOA_2 = "João Carlos Souza"
EMPRESA = "Exemplo Comércio de Tecidos Ltda."
CPF = "111.444.777-35"
CNPJ = "11.222.333/0001-81"
EMAIL = "contato@exemplo.com.br"
TELEFONE = "(51) 99876-5432"
ENDERECO = "Rua das Acácias, 120"

LINHAS_CONTRATO = [
    "CONTRATO DE LOCAÇÃO RESIDENCIAL",
    f"LOCADOR: {PESSOA_1}, brasileira, casada, portadora do CPF {CPF}, residente na {ENDERECO}, "
    f"telefone {TELEFONE}, e-mail {EMAIL}.",
    f"LOCATÁRIA: {EMPRESA}, inscrita no CNPJ {CNPJ}, representada por {PESSOA_2}.",
    "Cláusula 1ª. O aluguel mensal é de R$ 1.500,00, com vencimento no dia 10.",
    "Cláusula 2ª. O prazo da locação é de 30 meses.",
    "Porto Alegre, 11 de outubro de 2026.",
    f"{PESSOA_1} — {PESSOA_2}",
]


def pasta_temporaria(nome: str) -> Path:
    pasta = RAIZ / "saida_testes" / nome
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True)
    return pasta


def contrato_docx(caminho: Path) -> Path:
    """Contrato com: nome partido entre dois runs (o segundo em negrito), tabela,
    cabeçalho, hyperlink, caixa de texto, revisão controlada, comentário e autor
    nos metadados."""
    import docx
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls
    d = docx.Document()
    d.core_properties.author = "Autor Original Sintético"
    d.core_properties.last_modified_by = "Editor Sintético"
    d.sections[0].header.paragraphs[0].text = f"Contrato — {PESSOA_1}"
    d.add_paragraph(LINHAS_CONTRATO[0])
    p = d.add_paragraph("LOCADOR: Maria Apa")
    p.add_run("recida Pereira").bold = True
    p.add_run(LINHAS_CONTRATO[1][len("LOCADOR: " + PESSOA_1):])
    for linha in LINHAS_CONTRATO[2:]:
        d.add_paragraph(linha)
    tabela = d.add_table(rows=1, cols=2)
    tabela.cell(0, 0).text = "Locador"
    tabela.cell(0, 1).text = PESSOA_1
    # hyperlink com o e-mail
    ph = d.add_paragraph("Contato: ")
    ph._p.append(parse_xml(
        f'<w:hyperlink {nsdecls("w")}><w:r><w:t>{EMAIL}</w:t></w:r></w:hyperlink>'))
    # revisão controlada: inserção com o nome da segunda pessoa
    pr = d.add_paragraph("Testemunha: ")
    pr._p.append(parse_xml(
        f'<w:ins {nsdecls("w")} w:id="1" w:author="Revisor" w:date="2026-10-11T00:00:00Z">'
        f'<w:r><w:t>{PESSOA_2}</w:t></w:r></w:ins>'))
    # caixa de texto (só o conteúdo txbx; basta para o Word e para o leitor)
    pc = d.add_paragraph()
    pc._p.append(parse_xml(
        f'<w:r {nsdecls("w", "wps", "mc")}><mc:AlternateContent><mc:Choice Requires="wps">'
        f'<w:drawing><wps:txbx><w:txbxContent><w:p><w:r><w:t>Fiadora: {PESSOA_1}</w:t></w:r></w:p>'
        f'</w:txbxContent></wps:txbx></w:drawing></mc:Choice></mc:AlternateContent></w:r>'))
    d.add_comment(d.paragraphs[1].runs[0], text="Conferir o CPF", author="Comentarista Sintético")
    caminho = Path(caminho)
    d.save(str(caminho))
    return caminho


def _pdf_de_linhas(pagina, tamanho: float = 11):
    import fitz
    area = pagina.rect + (56, 56, -56, -56)
    pagina.insert_textbox(area, "\n\n".join(LINHAS_CONTRATO), fontsize=tamanho, fontname="helv")


def contrato_pdf(caminho: Path, girar: int = 0) -> Path:
    import fitz
    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)
    _pdf_de_linhas(pagina)
    if girar:
        pagina.set_rotation(girar)
    doc.set_metadata({"author": "Autor Original Sintético", "title": f"Contrato {PESSOA_1}"})
    caminho = Path(caminho)
    doc.save(str(caminho))
    return caminho


def contrato_escaneado(caminho: Path) -> Path:
    """Página só com imagem (sem camada de texto), como um papel digitalizado."""
    import fitz
    fonte = fitz.open()
    pagina = fonte.new_page(width=595, height=842)
    _pdf_de_linhas(pagina, tamanho=14)
    pix = pagina.get_pixmap(dpi=200)
    doc = fitz.open()
    nova = doc.new_page(width=595, height=842)
    nova.insert_image(nova.rect, pixmap=pix)
    caminho = Path(caminho)
    doc.save(str(caminho))
    return caminho
```
> Se `d.add_comment` não existir na versão instalada do python-docx, remova essa linha e anote no commit; o teste de comentário da Task 9 passa a construir o comentário à mão com `parse_xml`.

- [ ] **Step 2: Teste vermelho**

`testes/test_leitura_docx.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fabrica as F
from pseudonimizador.leitura.docx_ import ler_docx
from pseudonimizador.leitura.modelo import OrigemDocx


def _doc():
    return ler_docx(F.contrato_docx(F.pasta_temporaria("leitura_docx") / "c.docx"))


def test_texto_inclui_corpo_tabela_cabecalho_hyperlink_insercao_e_caixa():
    d = _doc()
    assert d.tipo == "docx"
    assert "LOCADOR: Maria Aparecida Pereira, brasileira" in d.texto       # nome partido entre runs
    assert d.texto.count(F.PESSOA_1) >= 5   # parágrafo, assinatura, tabela, cabeçalho, caixa de texto
    assert F.EMAIL in d.texto                                               # hyperlink
    assert "Testemunha: " + F.PESSOA_2 in d.texto                           # revisão aceita
    assert "Fiadora: " + F.PESSOA_1 in d.texto                              # caixa de texto


def test_origens_alinhadas_ao_texto():
    d = _doc()
    assert len(d.origens) == len(d.texto)
    i = d.texto.index("recida Pereira")
    o = d.origens[i]
    assert isinstance(o, OrigemDocx) and o.run == 1 and o.pos == 0
    assert all(d.origens[k] is None for k, c in enumerate(d.texto) if c == "\n")


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
Run: `.venv/Scripts/python -X utf8 testes/test_leitura_docx.py` → FALHA (módulo inexistente).

- [ ] **Step 3: `leitura/modelo.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""O documento lido: texto corrido e, para cada caractere, de onde ele veio."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class ErroDeLeitura(Exception):
    """Arquivo que não pode ser lido (formato, senha, arquivo corrompido)."""


@dataclass(frozen=True)
class OrigemDocx:
    paragrafo: int     # índice em leitura.docx_.paragrafos(doc)
    run: int           # índice em leitura.docx_.runs_do_paragrafo(par)
    pos: int           # posição do caractere em run.text


@dataclass(frozen=True)
class OrigemPdf:
    pagina: int
    rect: tuple[float, float, float, float]   # no sistema de coordenadas de page.get_text / add_redact_annot
    ocr: bool


@dataclass
class Documento:
    caminho: Path
    tipo: str                                  # docx | pdf_texto | pdf_ocr | pdf_misto
    texto: str
    origens: list = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    paginas_ocr: list[int] = field(default_factory=list)
```

- [ ] **Step 4: `leitura/docx_.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Leitura de DOCX. `preparar`, `paragrafos` e `runs_do_paragrafo` são usados
também pela saída: a mesma ordem garante que as origens apontem o mesmo run."""
from __future__ import annotations

import zipfile
from pathlib import Path

from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from .modelo import Documento, ErroDeLeitura, OrigemDocx


def _raizes(doc) -> list:
    """O corpo e cada cabeçalho/rodapé que tem definição própria (sem criar nenhum)."""
    raizes = [doc.element.body]
    vistos = set()
    for secao in doc.sections:
        for hf in (secao.header, secao.first_page_header, secao.even_page_header,
                   secao.footer, secao.first_page_footer, secao.even_page_footer):
            if hf._has_definition and id(hf._element) not in vistos:
                vistos.add(id(hf._element))
                raizes.append(hf._element)
    return raizes


def _desembrulhar(el) -> None:
    pai = el.getparent()
    i = pai.index(el)
    for filho in list(el):
        pai.insert(i, filho)
        i += 1
    pai.remove(el)


def preparar(doc) -> None:
    """Aceita as revisões controladas (inserção fica, exclusão sai) e tira as
    marcas de comentário do texto: o que sobra é o que o leitor e a saída veem."""
    for raiz in _raizes(doc):
        for el in raiz.xpath(".//w:del | .//w:moveFrom"):
            el.getparent().remove(el)
        for el in raiz.xpath(".//w:ins | .//w:moveTo"):
            _desembrulhar(el)
        for el in raiz.xpath(".//w:commentRangeStart | .//w:commentRangeEnd | .//w:commentReference"):
            el.getparent().remove(el)


def _blocos(pai, elemento, vistos: set):
    for filho in elemento.iterchildren():
        if filho.tag == qn("w:p"):
            yield Paragraph(filho, pai)
        elif filho.tag == qn("w:tbl"):
            for linha in Table(filho, pai).rows:
                for celula in linha.cells:
                    if id(celula._tc) in vistos:      # célula mesclada aparece repetida
                        continue
                    vistos.add(id(celula._tc))
                    yield from _blocos(celula, celula._tc, vistos)
        elif filho.tag == qn("w:sdt"):
            conteudo = filho.find(qn("w:sdtContent"))
            if conteudo is not None:
                yield from _blocos(pai, conteudo, vistos)


def paragrafos(doc) -> list[Paragraph]:
    saida: list[Paragraph] = []
    for raiz in _raizes(doc):
        vistos: set = set()
        saida.extend(_blocos(doc.part, raiz, vistos))
        for caixa in raiz.xpath(".//w:txbxContent"):
            saida.extend(_blocos(doc.part, caixa, vistos))
    return saida


def runs_do_paragrafo(par: Paragraph) -> list[Run]:
    runs: list[Run] = []
    for item in par.iter_inner_content():
        if isinstance(item, Run):
            runs.append(item)
        else:                                   # Hyperlink
            runs.extend(item.runs)
    return runs


def _abrir(caminho: Path):
    import docx
    try:
        return docx.Document(str(caminho))
    except (zipfile.BadZipFile, KeyError, ValueError, OSError) as e:
        raise ErroDeLeitura(f"não foi possível abrir o DOCX: {Path(caminho).name}") from e


def _avisos(caminho: Path) -> list[str]:
    with zipfile.ZipFile(caminho) as z:
        nomes = set(z.namelist())
    avisos = []
    if "word/footnotes.xml" in nomes or "word/endnotes.xml" in nomes:
        avisos.append("o documento tem notas de rodapé ou de fim, que não são tratadas; "
                      "se houver dado pessoal nelas, a geração será bloqueada")
    return avisos


def ler_docx(caminho: Path) -> Documento:
    caminho = Path(caminho)
    doc = _abrir(caminho)
    preparar(doc)
    partes: list[str] = []
    origens: list = []
    for i, par in enumerate(paragrafos(doc)):
        for j, run in enumerate(runs_do_paragrafo(par)):
            t = run.text
            partes.append(t)
            origens.extend(OrigemDocx(i, j, k) for k in range(len(t)))
        partes.append("\n")
        origens.append(None)
    return Documento(caminho=caminho, tipo="docx", texto="".join(partes), origens=origens,
                     avisos=_avisos(caminho))
```

- [ ] **Step 5: Rodar**

Run: `.venv/Scripts/python -X utf8 testes/test_leitura_docx.py` → `2/2 passaram`.
Se `test_texto_inclui...` falhar só na caixa de texto, confira com `print(d.texto)` se o XML da fábrica gerou `w:txbxContent`; o leitor não muda.

- [ ] **Step 6: Commit**

```bash
git add pseudonimizador/leitura testes/fabrica.py testes/test_leitura_docx.py
git commit -m "Leitura de DOCX com origem de cada caractere; fábrica de documentos sintéticos

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Leitura de PDF com texto

**Files:**
- Create: `pseudonimizador/leitura/pdf_.py`
- Test: `testes/test_leitura_pdf.py`

**Interfaces:**
- Consumes: `leitura.modelo.*`.
- Produces: `leitura.pdf_.ler_pdf(caminho: Path, ocr=None) -> Documento`; `leitura.pdf_.MIN_CARACTERES = 20`; `leitura.pdf_.FLAGS`. O parâmetro `ocr` é uma função `(pagina) -> list[tuple[str, fitz.Rect]]` usada nas páginas sem texto (a Task 6 liga o OCR de verdade). Sem `ocr`, página sem texto com imagem gera aviso e fica fora do texto.

- [ ] **Step 1: Teste vermelho**

`testes/test_leitura_pdf.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fabrica as F
from pseudonimizador.leitura.modelo import OrigemPdf
from pseudonimizador.leitura.pdf_ import ler_pdf


def test_pdf_com_texto():
    d = ler_pdf(F.contrato_pdf(F.pasta_temporaria("leitura_pdf") / "c.pdf"))
    assert d.tipo == "pdf_texto" and d.paginas_ocr == []
    assert F.PESSOA_1 in d.texto and F.CPF in d.texto and "LOCATÁRIA" in d.texto
    assert len(d.origens) == len(d.texto)
    o = d.origens[d.texto.index(F.CPF)]
    assert isinstance(o, OrigemPdf) and o.pagina == 0 and not o.ocr
    x0, y0, x1, y1 = o.rect
    assert x1 > x0 and y1 > y0


def test_escaneado_sem_ocr_gera_aviso():
    d = ler_pdf(F.contrato_escaneado(F.pasta_temporaria("leitura_pdf2") / "e.pdf"))
    assert d.texto.strip() == ""
    assert any("sem texto" in a for a in d.avisos)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
Run → FALHA (módulo inexistente).

- [ ] **Step 2: `leitura/pdf_.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Leitura de PDF: caractere a caractere, com o retângulo de cada um. Linhas
do mesmo bloco se juntam com espaço (o nome quebrado no fim da linha continua
um nome); blocos se separam com quebra de linha."""
from __future__ import annotations

from pathlib import Path

import fitz

from .modelo import Documento, ErroDeLeitura, OrigemPdf

MIN_CARACTERES = 20
# sem TEXT_PRESERVE_LIGATURES: a ligadura "ﬁ" vira "f" + "i"
FLAGS = fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_MEDIABOX_CLIP


def _abrir(caminho: Path):
    try:
        pdf = fitz.open(str(caminho))
    except Exception as e:  # noqa: BLE001 — o PyMuPDF levanta tipos variados
        raise ErroDeLeitura(f"não foi possível abrir o PDF: {Path(caminho).name}") from e
    if pdf.needs_pass:
        pdf.close()
        raise ErroDeLeitura(f"o PDF está protegido por senha: {Path(caminho).name}")
    return pdf


def _caracteres(pagina, n: int, partes: list[str], origens: list) -> None:
    for bloco in pagina.get_text("rawdict", flags=FLAGS)["blocks"]:
        if bloco.get("type") != 0:
            continue
        for k, linha in enumerate(bloco["lines"]):
            if k:
                partes.append(" "); origens.append(None)
            for span in linha["spans"]:
                for ch in span["chars"]:
                    partes.append(ch["c"])
                    origens.append(OrigemPdf(n, tuple(ch["bbox"]), False))
        partes.append("\n"); origens.append(None)


def _linhas_ocr(n: int, linhas, partes: list[str], origens: list) -> None:
    """Cada linha do OCR: a posição de cada caractere é estimada dividindo a
    caixa da linha em partes iguais."""
    for texto, rect in linhas:
        if not texto:
            continue
        largura = (rect.x1 - rect.x0) / len(texto)
        for i, c in enumerate(texto):
            partes.append(c)
            origens.append(OrigemPdf(n, (rect.x0 + largura * i, rect.y0, rect.x0 + largura * (i + 1), rect.y1), True))
        partes.append("\n"); origens.append(None)


def ler_pdf(caminho: Path, ocr=None) -> Documento:
    caminho = Path(caminho)
    pdf = _abrir(caminho)
    partes: list[str] = []
    origens: list = []
    avisos: list[str] = []
    paginas_ocr: list[int] = []
    com_texto = 0
    try:
        for n, pagina in enumerate(pdf):
            if len(pagina.get_text("text", flags=FLAGS).strip()) >= MIN_CARACTERES:
                _caracteres(pagina, n, partes, origens)
                com_texto += 1
            elif pagina.get_images():
                if ocr is None:
                    avisos.append(f"página {n + 1} sem texto (imagem) não foi lida")
                    continue
                _linhas_ocr(n, ocr(pagina), partes, origens)
                paginas_ocr.append(n)
    finally:
        pdf.close()
    tipo = "pdf_texto" if not paginas_ocr else ("pdf_ocr" if not com_texto else "pdf_misto")
    return Documento(caminho=caminho, tipo=tipo, texto="".join(partes), origens=origens,
                     avisos=avisos, paginas_ocr=paginas_ocr)
```

- [ ] **Step 3: Rodar** → `2/2 passaram`.

- [ ] **Step 4: Commit**

```bash
git add pseudonimizador/leitura/pdf_.py testes/test_leitura_pdf.py
git commit -m "Leitura de PDF com texto, caractere a caractere com o retângulo de cada um

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: OCR local e o ponto de entrada `ler`

**Files:**
- Create: `pseudonimizador/leitura/ocr.py`
- Modify: `pseudonimizador/leitura/__init__.py`
- Test: `testes/test_leitura_ocr.py`

**Interfaces:**
- Consumes: `leitura.pdf_.ler_pdf(caminho, ocr=...)`, `leitura.docx_.ler_docx`.
- Produces: `leitura.ocr.ocr_pagina(pagina: fitz.Page, dpi: int = 200) -> list[tuple[str, fitz.Rect]]` (retângulos no sistema de `page.get_text`); `leitura.ler(caminho: Path) -> Documento` (DOCX ou PDF, OCR ligado; outros formatos → `ErroDeLeitura`); reexporta `Documento`, `ErroDeLeitura`.

- [ ] **Step 1: Teste vermelho**

`testes/test_leitura_ocr.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fabrica as F
from pseudonimizador.leitura import ErroDeLeitura, ler
from pseudonimizador.motor.mapa import normalizar


def test_escaneado_lido_por_ocr():
    d = ler(F.contrato_escaneado(F.pasta_temporaria("ocr") / "e.pdf"))
    assert d.tipo == "pdf_ocr" and d.paginas_ocr == [0]
    n = normalizar(d.texto)
    for esperado in ("locador", "maria aparecida pereira", "111.444.777-35", "clausula"):
        assert esperado in n, f"OCR não leu {esperado!r}: {d.texto[:300]!r}"
    o = d.origens[d.texto.index("1")]
    assert o.ocr and o.pagina == 0


def test_erros_de_leitura():
    import fitz
    pasta = F.pasta_temporaria("erros")
    (pasta / "x.txt").write_text("texto", encoding="utf-8")
    (pasta / "quebrado.docx").write_bytes(b"isto nao e um zip")
    doc = fitz.open(); doc.new_page()
    doc.save(str(pasta / "senha.pdf"), encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="dono", user_pw="usuario")
    for nome, trecho in (("x.txt", "formato"), ("quebrado.docx", "DOCX"), ("senha.pdf", "senha")):
        try:
            ler(pasta / nome)
        except ErroDeLeitura as e:
            assert trecho in str(e), str(e)
        else:
            raise AssertionError(f"{nome} deveria falhar")


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
Run → FALHA (`cannot import name 'ler'`).

- [ ] **Step 2: `leitura/ocr.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""OCR local (RapidOCR, modelos embutidos no pacote): nada sai da máquina."""
from __future__ import annotations

from functools import lru_cache

import fitz
import numpy as np


@lru_cache(maxsize=1)
def _motor():
    from rapidocr import RapidOCR
    return RapidOCR()


def ocr_pagina(pagina, dpi: int = 200) -> list[tuple[str, "fitz.Rect"]]:
    pix = pagina.get_pixmap(dpi=dpi, colorspace=fitz.csRGB, alpha=False)
    imagem = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    resultado = _motor()(imagem)
    if resultado is None or resultado.boxes is None:
        return []
    escala = 72 / dpi
    linhas = []
    for caixa, texto in zip(resultado.boxes, resultado.txts):
        xs = [float(p[0]) for p in caixa]
        ys = [float(p[1]) for p in caixa]
        # a imagem é a página como aparece (girada); volta ao sistema não girado
        rect = fitz.Rect(min(xs), min(ys), max(xs), max(ys)) * escala * pagina.derotation_matrix
        linhas.append((str(texto), rect))
    linhas.sort(key=lambda l: (round(l[1].y0 / 5), l[1].x0))
    return linhas
```

- [ ] **Step 3: `leitura/__init__.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Ponto de entrada da leitura: DOCX, PDF com texto e PDF escaneado."""
from __future__ import annotations

from pathlib import Path

from .modelo import Documento, ErroDeLeitura, OrigemDocx, OrigemPdf  # noqa: F401

ACEITOS = (".docx", ".pdf")


def ler(caminho: Path) -> Documento:
    caminho = Path(caminho)
    sufixo = caminho.suffix.lower()
    if sufixo == ".docx":
        from .docx_ import ler_docx
        return ler_docx(caminho)
    if sufixo == ".pdf":
        from .ocr import ocr_pagina
        from .pdf_ import ler_pdf
        return ler_pdf(caminho, ocr=ocr_pagina)
    raise ErroDeLeitura(f"formato não aceito: {sufixo or '(sem extensão)'} (aceitos: .docx, .pdf)")
```

- [ ] **Step 4: Rodar** → `2/2 passaram`. Se o OCR ler o CPF com outro separador, mantenha o teste: a fonte de 14 pt a 200 dpi deve dar leitura exata; se não der, aumente para 300 dpi em `ocr_pagina` e na fábrica.

- [ ] **Step 5: Commit**

```bash
git add pseudonimizador/leitura testes/test_leitura_ocr.py
git commit -m "OCR local (RapidOCR) nas páginas sem texto e ponto de entrada ler(); erros de leitura claros

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Detecção — identificadores, pessoas e empresas

**Files:**
- Create: `pseudonimizador/deteccao/__init__.py`, `pseudonimizador/deteccao/candidatos.py`
- Test: `testes/test_deteccao.py`

**Interfaces:**
- Consumes: `motor.trocas.limpar_com_indices`; `motor.pseudonimizador._spans_de_identificadores`, `RE_CNPJ`, `RE_SUFIXO_PJ`, `CONECTIVOS`, `_NUNCA_NOME`, `_prenome_provado`, `eh_pessoa_fisica`; `motor.lexico.SOBRENOMES`, `frequencia_de_sobrenome`; `motor.mapa.novo_mapa`, `normalizar`.
- Produces: `deteccao.Ocorrencia(frozen dataclass: ini: int, fim: int, categoria: str, valor: str)` (posições no texto original; `categoria` ∈ `{"pessoa", "empresa"}` ∪ categorias do motor: `cpf`, `cnpj`, `pis`, `rg`, `ctps`, `email`, `telefone`, `endereco`, `conta`, `url`…); `deteccao.detectar(texto: str) -> list[Ocorrencia]` (ordenadas, sem sobreposição); `deteccao.candidatos.pessoas_e_empresas(limpo: str) -> list[tuple[int, int, str]]` (posições no texto limpo; categoria `pessoa`/`empresa`).

- [ ] **Step 1: Teste vermelho**

`testes/test_deteccao.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fabrica as F
from pseudonimizador.deteccao import detectar

TEXTO = "\n".join(F.LINHAS_CONTRATO)


def _por_categoria(texto):
    achados = {}
    for o in detectar(texto):
        achados.setdefault(o.categoria, set()).add(o.valor)
    return achados


def test_contrato_completo():
    a = _por_categoria(TEXTO)
    assert F.PESSOA_1 in a["pessoa"] and F.PESSOA_2 in a["pessoa"], a
    assert F.EMPRESA in a["empresa"], a
    assert F.CPF in a["cpf"] and F.CNPJ in a["cnpj"], a
    assert F.EMAIL in a["email"], a
    assert any(F.TELEFONE in v for v in a["telefone"]), a
    assert any("Acácias" in v for v in a["endereco"]), a


def test_sem_falso_positivo_nas_clausulas():
    a = _por_categoria("Cláusula 1ª. O aluguel mensal é de R$ 1.500,00.\nPorto Alegre, 11 de outubro de 2026.")
    assert not a.get("pessoa") and not a.get("empresa"), a


def test_nome_fora_do_lexico_pela_ancora_e_pela_qualificacao():
    a = _por_categoria("CONTRATANTE: Xandrelo Quintebor Vasques, brasileiro, solteiro.\n"
                       "e Ylmara Torquesi Bento, portadora do RG 1234567.")
    assert "Xandrelo Quintebor Vasques" in a["pessoa"], a
    assert "Ylmara Torquesi Bento" in a["pessoa"], a


def test_caixa_nao_decide():
    a = _por_categoria("assinado por maria aparecida pereira em 2026.")
    assert "maria aparecida pereira" in a["pessoa"], a


def test_ocorrencias_ordenadas_sem_sobreposicao():
    oc = detectar(TEXTO)
    for x, y in zip(oc, oc[1:]):
        assert x.fim <= y.ini, (x, y)
    assert all(TEXTO[o.ini:o.fim] == o.valor for o in oc)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
Run → FALHA (módulo inexistente).

- [ ] **Step 2: `deteccao/candidatos.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Candidatos a nome de pessoa e de empresa num documento avulso (sem capa do
PJe): âncoras de qualificação de contrato, a qualificação depois do nome, o
léxico de prenomes e sobrenomes do motor e os sufixos societários. Tudo é
sugestão: a revisão humana decide (spec §6). A caixa não decide nada."""
from __future__ import annotations

import re

from ..motor.lexico import SOBRENOMES, frequencia_de_sobrenome
from ..motor.mapa import normalizar
from ..motor.pseudonimizador import CONECTIVOS, RE_SUFIXO_PJ, _NUNCA_NOME, _prenome_provado

RE_PALAVRA = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*")
RE_SO_ESPACO = re.compile(r"[ \t\u00a0]{1,3}")

RE_ANCORA = re.compile(
    r"(?i)\b(?:contratante|contratad[ao]|locador[a]?|locat[áa]ri[ao]|outorgante|outorgad[ao]|"
    r"comprador[a]?|vendedor[a]?|promitentes?\s+(?:comprador|vendedor)[a]?|fiador[a]?|cedente|"
    r"cession[áa]ri[ao]|empregador[a]?|empregad[ao]|testemunhas?|representante\s+legal|s[óo]ci[ao]|"
    r"procurador[a]?|interveniente|devedor[a]?|credor[a]?)\s*(?:\d+\s*)?[:\-–—]\s*"
    r"|(?i:\brepresentad[ao]\s+(?:neste\s+ato\s+)?por\s+)"
    r"|(?i:\b(?:raz[ãa]o\s+social|denominad[ao])\s*:?\s+)")
RE_QUALIFICACAO = re.compile(
    r"(?i),\s*(?:brasileir[oa]|estrangeir[oa]|nacionalidade|portador[a]?|inscrit[oa]|CPF|CNPJ|RG|"
    r"estado\s+civil|solteir[oa]|casad[oa]|divorciad[oa]|vi[úu]v[oa]|maior|menor)\b")
RE_SUFIXO = re.compile(r"(?<!\w)(?:ltda\.?|s\.\s?a\.?|s/a|eireli|epp|ME|SLU)(?!\w)", re.I)
_SUFIXO_EXIGE_DUAS = {"me", "epp", "slu"}

_PARADAS = {"brasileiro", "brasileira", "estrangeiro", "estrangeira", "portador", "portadora",
            "inscrito", "inscrita", "residente", "domiciliado", "domiciliada", "casado", "casada",
            "solteiro", "solteira", "nacionalidade", "neste", "ato", "doravante", "pessoa", "empresa",
            "sociedade", "com", "sede", "cpf", "cnpj", "rg", "denominado", "denominada", "representado",
            "representada", "que", "para", "por", "pelo", "pela", "o", "a", "os", "as", "sr", "sra",
            "senhor", "senhora", "entre", "em", "no", "na", "ao", "firma", "razao", "social"}
MAX_PALAVRAS = 8


def _sobrenome(n: str) -> bool:
    return (n in SOBRENOMES or frequencia_de_sobrenome(n) > 0) and n not in _NUNCA_NOME and n not in CONECTIVOS


def _significativas(nome: str) -> int:
    return sum(1 for w in nome.split() if normalizar(w) not in CONECTIVOS)


def _ler_adiante(s: str, pos: int) -> tuple[int, int] | None:
    """Palavras a partir de `pos`, separadas por espaço simples, até pontuação,
    quebra de linha ou palavra de parada. Tira conectivos do fim."""
    palavras = []
    i = pos
    while len(palavras) < MAX_PALAVRAS:
        m = RE_PALAVRA.match(s, i)
        if not m or normalizar(m.group()) in _PARADAS:
            break
        palavras.append(m)
        prox = RE_SO_ESPACO.match(s, m.end())
        if not prox:
            break
        i = prox.end()
    while palavras and normalizar(palavras[-1].group()) in CONECTIVOS:
        palavras.pop()
    if not palavras:
        return None
    ini, fim = palavras[0].start(), palavras[-1].end()
    # sufixo societário logo depois ("... Tecidos Ltda.") faz parte do nome
    suf = re.compile(r"\s*" + RE_SUFIXO.pattern, re.I).match(s, fim)
    if suf:
        fim = suf.end()
    return (ini, fim) if _significativas(s[ini:fim]) >= 2 else None


def _ler_atras(s: str, pos: int) -> tuple[int, int] | None:
    """Palavras imediatamente antes de `pos`, de trás para a frente, até
    pontuação ou palavra de parada. Tira conectivos do começo."""
    palavras = [m for m in RE_PALAVRA.finditer(s, max(0, pos - 200), pos)]
    escolhidas = []
    fim_esperado = pos
    for m in reversed(palavras):
        if not RE_SO_ESPACO.fullmatch(s[m.end():fim_esperado]) and m.end() != fim_esperado:
            break
        if normalizar(m.group()) in _PARADAS or len(escolhidas) >= MAX_PALAVRAS:
            break
        escolhidas.insert(0, m)
        fim_esperado = m.start()
    while escolhidas and normalizar(escolhidas[0].group()) in CONECTIVOS:
        escolhidas.pop(0)
    if not escolhidas:
        return None
    ini, fim = escolhidas[0].start(), escolhidas[-1].end()
    return (ini, fim) if _significativas(s[ini:fim]) >= 2 else None


def _categoria(nome: str, contexto: str = "") -> str:
    return "empresa" if RE_SUFIXO_PJ.search(nome) or RE_SUFIXO.search(nome) or "cnpj" in contexto.lower() \
        else "pessoa"


def _por_ancora(s: str) -> list[tuple[int, int, str]]:
    achados = []
    for m in RE_ANCORA.finditer(s):
        span = _ler_adiante(s, m.end())
        if span:
            achados.append((*span, _categoria(s[span[0]:span[1]])))
    return achados


def _por_qualificacao(s: str) -> list[tuple[int, int, str]]:
    achados = []
    for m in RE_QUALIFICACAO.finditer(s):
        fim_nome = m.start()
        # "Ltda., inscrita": o sufixo com ponto antes da vírgula
        suf = None
        for sm in RE_SUFIXO.finditer(s, max(0, fim_nome - 8), fim_nome):
            if sm.end() == fim_nome:
                suf = sm
        span = _ler_atras(s, suf.start() if suf else fim_nome)
        if span:
            fim = suf.end() if suf else span[1]
            achados.append((span[0], fim, _categoria(s[span[0]:fim], m.group())))
    return achados


def _por_lexico(s: str) -> list[tuple[int, int, str]]:
    palavras = list(RE_PALAVRA.finditer(s))
    achados = []
    i = 0
    while i < len(palavras):
        if not _prenome_provado(palavras[i].group()):
            i += 1
            continue
        j, ultimo, tem_sobrenome = i, None, False
        while j + 1 < len(palavras) and RE_SO_ESPACO.fullmatch(s[palavras[j].end():palavras[j + 1].start()]):
            w = palavras[j + 1].group()
            n = normalizar(w)
            if n in CONECTIVOS:
                j += 1
                continue
            if _sobrenome(n) or _prenome_provado(w):
                j += 1
                ultimo = j
                tem_sobrenome = tem_sobrenome or _sobrenome(n)
                continue
            break
        if ultimo is not None and tem_sobrenome:
            achados.append((palavras[i].start(), palavras[ultimo].end(), "pessoa"))
            i = ultimo + 1
        else:
            i += 1
    return achados


def _por_sufixo(s: str) -> list[tuple[int, int, str]]:
    achados = []
    for m in RE_SUFIXO.finditer(s):
        span = _ler_atras(s, m.start())
        if not span:
            continue
        if normalizar(m.group()).strip(".") in _SUFIXO_EXIGE_DUAS and _significativas(s[span[0]:span[1]]) < 2:
            continue
        achados.append((span[0], m.end(), "empresa"))
    return achados


def pessoas_e_empresas(limpo: str) -> list[tuple[int, int, str]]:
    todos = _por_ancora(limpo) + _por_qualificacao(limpo) + _por_sufixo(limpo) + _por_lexico(limpo)
    # o mais longo primeiro; empresa vence pessoa no mesmo trecho
    todos.sort(key=lambda a: (a[0], -(a[1] - a[0]), a[2] != "empresa"))
    escolhidos: list[tuple[int, int, str]] = []
    for a in todos:
        if all(a[1] <= b[0] or a[0] >= b[1] for b in escolhidos):
            escolhidos.append(a)
    return sorted(escolhidos)
```

- [ ] **Step 3: `deteccao/__init__.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Detecção: os identificadores do motor (CPF, CNPJ, e-mail, telefone,
endereço…) e os candidatos a pessoa e empresa, com posição no texto original."""
from __future__ import annotations

from dataclasses import dataclass

from ..motor.mapa import novo_mapa
from ..motor.pseudonimizador import RE_CNPJ, _spans_de_identificadores
from ..motor.trocas import limpar_com_indices
from .candidatos import pessoas_e_empresas


@dataclass(frozen=True)
class Ocorrencia:
    ini: int
    fim: int
    categoria: str
    valor: str


def _identificadores(limpo: str) -> list[tuple[int, int, str]]:
    rascunho = novo_mapa()
    achados = [(a, b, rascunho["tokens"][tok]["categoria"])
               for a, b, tok in _spans_de_identificadores(limpo, rascunho)]
    achados += [(m.start(), m.end(), "cnpj") for m in RE_CNPJ.finditer(limpo)]
    return achados


def detectar(texto: str) -> list[Ocorrencia]:
    limpo, ini, fim = limpar_com_indices(texto)
    nomes = pessoas_e_empresas(limpo)
    # nomes primeiro (como no motor): identificador que cruza um nome cede
    candidatos = nomes + [i for i in _identificadores(limpo)
                          if all(i[1] <= n[0] or i[0] >= n[1] for n in nomes)]
    candidatos.sort(key=lambda a: (a[0], -(a[1] - a[0])))
    saida: list[Ocorrencia] = []
    for a, b, cat in candidatos:
        o_ini, o_fim = ini[a], fim[b - 1]
        if saida and o_ini < saida[-1].fim:
            continue
        saida.append(Ocorrencia(o_ini, o_fim, cat, texto[o_ini:o_fim]))
    return saida
```

- [ ] **Step 4: Rodar**

Run: `.venv/Scripts/python -X utf8 testes/test_deteccao.py` → `5/5 passaram`.
Se `test_sem_falso_positivo_nas_clausulas` acusar "Porto Alegre" como pessoa, confira `_prenome_provado("Porto")`; o ajuste é acrescentar a palavra a `_PARADAS`, nunca exigir maiúscula.

- [ ] **Step 5: Commit**

```bash
git add pseudonimizador/deteccao testes/test_deteccao.py
git commit -m "Detecção de identificadores e de candidatos a pessoa e empresa em documento avulso

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Revisão — itens, decisões e fechamento (mapa + trocas)

**Files:**
- Create: `pseudonimizador/revisao.py`
- Test: `testes/test_revisao.py`

**Interfaces:**
- Consumes: `leitura.Documento`; `deteccao.detectar`, `Ocorrencia`; `motor.mapa.novo_mapa`, `token_para`, `normalizar`; `motor.trocas.trocas`, `Troca`.
- Produces:
  - `revisao.Item(dataclass: categoria: str, valor: str, ocorrencias: list[tuple[int, int]], aceito: bool = True, acrescido: bool = False)` com propriedade `chave -> tuple[str, str]` = `(categoria, normalizar(valor))`.
  - `revisao.Resultado(dataclass: mapa: dict, trocas: list[Troca])`.
  - `revisao.Revisao(documento)`: atributos `documento`, `itens: list[Item]`; métodos `item(chave) -> Item`, `aceitar(chave)`, `recusar(chave)`, `acrescentar(valor: str, categoria: str = "pessoa") -> Item` (`ValueError` se o valor não aparece no texto), `contexto(ini: int, fim: int, largura: int = 60) -> str`, `fechar() -> Resultado`.
  - `revisao.PREFIXOS: dict[str, str]` (categoria → prefixo do tóken).

- [ ] **Step 1: Teste vermelho**

`testes/test_revisao.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
from pathlib import Path

import fabrica as F
from pseudonimizador.leitura import Documento
from pseudonimizador.motor.mapa import normalizar
from pseudonimizador.motor.trocas import aplicar_trocas
from pseudonimizador.revisao import Revisao

TEXTO = "\n".join(F.LINHAS_CONTRATO) + "\nObservação: a senhora Pereira assinou.\n"


def _rev():
    return Revisao(Documento(Path("x.docx"), "docx", TEXTO, [None] * len(TEXTO)))


def test_tudo_aceito_por_padrao_e_nada_em_claro():
    r = _rev()
    res = r.fechar()
    saida = aplicar_trocas(TEXTO, res.trocas)
    for valor in (F.PESSOA_1, F.PESSOA_2, F.EMPRESA, F.CPF, F.CNPJ, F.EMAIL):
        assert valor not in saida, (valor, saida)
    assert "Cláusula 1ª" in saida


def test_recusar_identificador_deixa_em_claro():
    r = _rev()
    r.recusar(("email", normalizar(F.EMAIL)))
    saida = aplicar_trocas(TEXTO, r.fechar().trocas)
    assert F.EMAIL in saida and F.CPF not in saida


def test_recusar_pessoa_deixa_em_claro():
    r = _rev()
    r.recusar(("pessoa", normalizar(F.PESSOA_2)))
    saida = aplicar_trocas(TEXTO, r.fechar().trocas)
    assert F.PESSOA_2 in saida and F.PESSOA_1 not in saida


def test_acrescentar_nome_que_escapou():
    r = _rev()
    item = r.acrescentar("senhora Pereira", "outro")
    assert item.acrescido and item.ocorrencias
    saida = aplicar_trocas(TEXTO, r.fechar().trocas)
    assert "senhora Pereira" not in saida
    try:
        r.acrescentar("Nome Que Não Existe", "pessoa")
    except ValueError:
        pass
    else:
        raise AssertionError("deveria recusar valor ausente")


def test_mapa_so_com_tokens_usados_e_contexto():
    r = _rev()
    res = r.fechar()
    usados = {t.token for t in res.trocas}
    assert set(res.mapa["tokens"]) == usados
    i = TEXTO.index(F.CPF)
    assert F.CPF in r.contexto(i, i + len(F.CPF))


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
Run → FALHA (módulo inexistente).

- [ ] **Step 2: `revisao.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Revisão de um documento: os itens detectados (agrupados por categoria e
valor), as decisões do usuário e o fechamento em mapa + trocas (spec §6).
Tudo começa aceito: recusar é o gesto consciente."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .deteccao import detectar
from .motor.mapa import normalizar, novo_mapa, token_para
from .motor.trocas import Troca, trocas

PREFIXOS = {"pessoa": "PESSOA", "empresa": "EMPRESA", "cpf": "CPF", "cnpj": "CNPJ", "pis": "PIS",
            "rg": "RG", "ctps": "CTPS", "email": "EMAIL", "telefone": "TEL", "endereco": "ENDERECO",
            "conta": "CONTA", "url": "URL", "outro": "DADO"}
_CATEGORIA_NO_MAPA = {"empresa": "pj"}      # o motor chama empresa de "pj"


@dataclass
class Item:
    categoria: str
    valor: str
    ocorrencias: list[tuple[int, int]] = field(default_factory=list)
    aceito: bool = True
    acrescido: bool = False

    @property
    def chave(self) -> tuple[str, str]:
        return (self.categoria, normalizar(self.valor))


@dataclass
class Resultado:
    mapa: dict
    trocas: list[Troca]


def _buscar(texto: str, valor: str) -> list[tuple[int, int]]:
    """Ocorrências literais do valor, sem diferenciar maiúsculas e com
    qualquer espaço entre as palavras."""
    partes = valor.split()
    if not partes:
        return []
    padrao = r"(?<!\w)" + r"\s+".join(re.escape(p) for p in partes) + r"(?!\w)"
    return [m.span() for m in re.finditer(padrao, texto, re.I)]


class Revisao:
    def __init__(self, documento):
        self.documento = documento
        self.itens: list[Item] = []
        por_chave: dict[tuple[str, str], Item] = {}
        for o in detectar(documento.texto):
            novo = Item(o.categoria, o.valor)
            item = por_chave.setdefault(novo.chave, novo)
            if item is novo:
                self.itens.append(item)
            item.ocorrencias.append((o.ini, o.fim))
        for item in self.itens:                      # também as ocorrências sem âncora
            for span in _buscar(documento.texto, item.valor):
                if span not in item.ocorrencias:
                    item.ocorrencias.append(span)
            item.ocorrencias.sort()

    def item(self, chave: tuple[str, str]) -> Item:
        for it in self.itens:
            if it.chave == chave:
                return it
        raise KeyError(chave)

    def aceitar(self, chave) -> None:
        self.item(chave).aceito = True

    def recusar(self, chave) -> None:
        self.item(chave).aceito = False

    def acrescentar(self, valor: str, categoria: str = "pessoa") -> Item:
        valor = valor.strip()
        ocorrencias = _buscar(self.documento.texto, valor)
        if not ocorrencias:
            raise ValueError(f"não encontrado no documento: {valor!r}")
        item = Item(categoria, valor, ocorrencias, aceito=True, acrescido=True)
        self.itens.append(item)
        return item

    def contexto(self, ini: int, fim: int, largura: int = 60) -> str:
        t = self.documento.texto
        return t[max(0, ini - largura):fim + largura].replace("\n", " ")

    def _token(self, mapa: dict, item: Item) -> str:
        return token_para(mapa, PREFIXOS.get(item.categoria, item.categoria.upper()),
                          _CATEGORIA_NO_MAPA.get(item.categoria, item.categoria), item.valor)

    def fechar(self) -> Resultado:
        texto = self.documento.texto
        mapa = novo_mapa()
        aceitos = [it for it in self.itens if it.aceito]
        recusados = {(_CATEGORIA_NO_MAPA.get(it.categoria, it.categoria), normalizar(it.valor))
                     for it in self.itens if not it.aceito}
        for it in aceitos:
            if it.categoria in ("pessoa", "empresa"):
                self._token(mapa, it)
        lista = [t for t in trocas(texto, mapa)
                 if (mapa["tokens"][t.token]["categoria"], normalizar(mapa["tokens"][t.token]["valor"]))
                 not in recusados]
        # rede de segurança: toda ocorrência aceita que o motor não cobriu
        for it in aceitos:
            for a, b in it.ocorrencias:
                if all(b <= t.ini or a >= t.fim for t in lista):
                    lista.append(Troca(a, b, self._token(mapa, it)))
        lista.sort()
        usados = {t.token for t in lista}
        mapa["tokens"] = {tok: info for tok, info in mapa["tokens"].items() if tok in usados}
        return Resultado(mapa, lista)
```

- [ ] **Step 3: Rodar** → `5/5 passaram`.

- [ ] **Step 4: Commit**

```bash
git add pseudonimizador/revisao.py testes/test_revisao.py
git commit -m "Revisão: itens detectados, aceitar/recusar/acrescentar e fechamento em mapa e trocas

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Saídas "só texto" e "layout original" em DOCX

**Files:**
- Create: `pseudonimizador/saida/__init__.py` (só cabeçalho por ora), `saida/texto.py`, `saida/docx_layout.py`
- Test: `testes/test_saida_texto.py`, `testes/test_saida_docx.py`

**Interfaces:**
- Consumes: `leitura.Documento`, `leitura.docx_.preparar/paragrafos/runs_do_paragrafo`, `leitura.modelo.OrigemDocx`, `motor.trocas.Troca/aplicar_trocas`, `revisao.Revisao`.
- Produces: `saida.texto.gerar_docx_texto(texto: str, destino: Path) -> None`; `saida.texto.gerar_pdf_texto(texto: str, destino: Path) -> None`; `saida.docx_layout.gerar_docx_layout(documento, trocas: list[Troca], destino: Path, identificador: str = "") -> None`; `saida.docx_layout.limpar_metadados_docx(doc, identificador: str = "") -> None`.

- [ ] **Step 1: Testes vermelhos**

`testes/test_saida_texto.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import docx
import fitz
import fabrica as F
from pseudonimizador.saida.texto import gerar_docx_texto, gerar_pdf_texto

TEXTO = "Primeira linha com [[PESSOA_1]].\nCláusula 2ª — acentuação: ação, côncavo."


def test_docx_texto():
    destino = F.pasta_temporaria("saida_texto") / "t.docx"
    gerar_docx_texto(TEXTO, destino)
    d = docx.Document(str(destino))
    assert [p.text for p in d.paragraphs] == TEXTO.split("\n")
    assert d.core_properties.author == ""


def test_pdf_texto():
    destino = F.pasta_temporaria("saida_texto2") / "t.pdf"
    gerar_pdf_texto(TEXTO, destino)
    with fitz.open(str(destino)) as pdf:
        extraido = "".join(p.get_text() for p in pdf)
        assert "[[PESSOA_1]]" in extraido and "côncavo" in extraido
        assert not (pdf.metadata.get("author") or "")


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
`testes/test_saida_docx.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import zipfile

import docx
import fabrica as F
from pseudonimizador.leitura import ler
from pseudonimizador.revisao import Revisao
from pseudonimizador.saida.docx_layout import gerar_docx_layout


def _gerar():
    pasta = F.pasta_temporaria("saida_docx")
    doc = ler(F.contrato_docx(pasta / "c.docx"))
    res = Revisao(doc).fechar()
    destino = pasta / "c - pseudonimizado.docx"
    gerar_docx_layout(doc, res.trocas, destino, identificador="pseudonimizador:teste")
    return destino, res


def test_nada_em_claro_em_nenhuma_parte_do_arquivo():
    destino, _ = _gerar()
    with zipfile.ZipFile(destino) as z:
        bruto = " ".join(z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.endswith(".xml"))
    for valor in (F.PESSOA_1, F.PESSOA_2, F.CPF, F.EMAIL, "Autor Original", "Editor Sintético",
                  "Comentarista Sintético", "Conferir o CPF", "Revisor"):
        assert valor not in bruto, valor


def test_layout_preservado_e_tokens_no_lugar():
    destino, res = _gerar()
    d = ler(destino)
    assert "LOCADOR: [[PESSOA_1]], brasileira" in d.texto
    assert "Cláusula 1ª. O aluguel mensal" in d.texto
    original = docx.Document(str(destino))
    p = original.paragraphs[1]
    assert p.runs[0].text == "LOCADOR: [[PESSOA_1]]" and p.runs[1].text == "" and p.runs[1].bold
    assert original.core_properties.identifier == "pseudonimizador:teste"


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
Run ambos → FALHA (módulos inexistentes).

- [ ] **Step 2: `saida/texto.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Saída "só o texto": um documento novo e limpo, um parágrafo por linha."""
from __future__ import annotations

import html
import os
from pathlib import Path

import fitz


def gerar_docx_texto(texto: str, destino: Path) -> None:
    import docx
    from .docx_layout import limpar_metadados_docx
    d = docx.Document()
    for linha in texto.split("\n"):
        d.add_paragraph(linha)
    limpar_metadados_docx(d)
    tmp = Path(destino).with_suffix(".docx.tmp")
    d.save(str(tmp))
    os.replace(tmp, destino)


def gerar_pdf_texto(texto: str, destino: Path) -> None:
    corpo = "".join(f"<p>{html.escape(l) or '&nbsp;'}</p>" for l in texto.split("\n"))
    story = fitz.Story(html=corpo, user_css="p{font-family:sans-serif;font-size:11pt;margin:0 0 6pt 0}")
    tmp = Path(destino).with_suffix(".pdf.tmp")
    escritor = fitz.DocumentWriter(str(tmp))
    pagina = fitz.paper_rect("a4")
    area = pagina + (56, 56, -56, -56)
    mais = True
    while mais:
        dispositivo = escritor.begin_page(pagina)
        mais, _ = story.place(area)
        story.draw(dispositivo)
        escritor.end_page()
    escritor.close()
    with fitz.open(str(tmp)) as pdf:
        pdf.set_metadata({})
        pdf.save(str(destino), garbage=4, deflate=True)
    os.remove(tmp)
```

- [ ] **Step 3: `saida/docx_layout.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Saída DOCX no layout original: a troca é feita nos runs. Trecho que
atravessa runs: o tóken fica no primeiro (com a formatação dele) e os demais
perdem a parte trocada. Metadados, comentários e revisões saem (spec §7)."""
from __future__ import annotations

import os
from collections import defaultdict
from itertools import groupby
from pathlib import Path

from docx.opc.constants import RELATIONSHIP_TYPE as RT

from ..leitura.docx_ import paragrafos, preparar, runs_do_paragrafo

_RELS_DE_COMENTARIO = ("/comments", "/commentsExtended", "/commentsIds", "/commentsExtensible", "/people")


def limpar_metadados_docx(doc, identificador: str = "") -> None:
    cp = doc.core_properties
    for campo in ("author", "last_modified_by", "comments", "title", "subject", "keywords",
                  "category", "content_status"):
        setattr(cp, campo, "")
    cp.identifier = identificador
    cp.revision = 1
    for rid, rel in list(doc.part.rels.items()):
        if rel.reltype.endswith(_RELS_DE_COMENTARIO):
            doc.part.drop_rel(rid)
    pacote = doc.part.package
    for rid, rel in list(pacote.rels.items()):
        if rel.reltype in (RT.EXTENDED_PROPERTIES, RT.CUSTOM_PROPERTIES):
            pacote.rels._rels.pop(rid)       # sem API pública; o teste confere que sumiu


def gerar_docx_layout(documento, trocas, destino: Path, identificador: str = "") -> None:
    import docx
    doc = docx.Document(str(documento.caminho))
    preparar(doc)
    runs = [runs_do_paragrafo(p) for p in paragrafos(doc)]
    edicoes: dict[tuple[int, int], list[tuple[int, int, str]]] = defaultdict(list)
    for t in trocas:
        origens = [o for o in documento.origens[t.ini:t.fim] if o is not None]
        for k, (chave, grupo) in enumerate(groupby(origens, key=lambda o: (o.paragrafo, o.run))):
            g = list(grupo)
            edicoes[chave].append((g[0].pos, g[-1].pos + 1, t.token if k == 0 else ""))
    for (p, r), lista in edicoes.items():
        run = runs[p][r]
        s = run.text
        for a, b, novo in sorted(lista, reverse=True):
            s = s[:a] + novo + s[b:]
        run.text = s
    limpar_metadados_docx(doc, identificador)
    tmp = Path(destino).with_suffix(".docx.tmp")
    doc.save(str(tmp))
    os.replace(tmp, destino)
```

- [ ] **Step 4: Rodar**

Run: `.venv/Scripts/python -X utf8 testes/test_saida_texto.py` e `.venv/Scripts/python -X utf8 testes/test_saida_docx.py` → todos passam.
Se `"Comentarista Sintético"` sobrar no zip, o `drop_rel` não removeu a parte: confira `doc.part.rels` depois de `limpar_metadados_docx` e remova também pelo `_rels` do part.

- [ ] **Step 5: Commit**

```bash
git add pseudonimizador/saida testes/test_saida_texto.py testes/test_saida_docx.py
git commit -m "Saídas só texto (DOCX e PDF) e DOCX no layout original, sem metadados nem comentários

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Saída PDF no layout original (texto e escaneado)

**Files:**
- Create: `pseudonimizador/saida/pdf_layout.py`
- Test: `testes/test_saida_pdf.py`

**Interfaces:**
- Consumes: `leitura.Documento`, `leitura.modelo.OrigemPdf`, `motor.trocas.Troca`.
- Produces: `saida.pdf_layout.gerar_pdf_layout(documento, trocas: list[Troca], destino: Path) -> list[str]` (avisos, por exemplo "página 2: código maior que o espaço"); `saida.pdf_layout.FONTE_MINIMA = 4.0`.

- [ ] **Step 1: Teste vermelho**

`testes/test_saida_pdf.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fitz
import fabrica as F
from pseudonimizador.leitura import ler
from pseudonimizador.leitura.ocr import ocr_pagina
from pseudonimizador.motor.mapa import normalizar
from pseudonimizador.revisao import Revisao
from pseudonimizador.saida.pdf_layout import gerar_pdf_layout


def _gerar(origem, nome):
    doc = ler(origem)
    res = Revisao(doc).fechar()
    destino = origem.with_name(nome)
    avisos = gerar_pdf_layout(doc, res.trocas, destino)
    return destino, avisos


def _texto(caminho):
    with fitz.open(str(caminho)) as pdf:
        return "".join(p.get_text() for p in pdf), pdf.metadata


def test_pdf_texto_redigido():
    pasta = F.pasta_temporaria("saida_pdf")
    destino, _ = _gerar(F.contrato_pdf(pasta / "c.pdf"), "c - pseudonimizado.pdf")
    texto, meta = _texto(destino)
    for valor in (F.PESSOA_1, F.PESSOA_2, F.CPF, F.EMAIL, F.CNPJ):
        assert valor not in texto, valor
    assert "[[PESSOA_1]]" in texto.replace("\n", "")
    assert "LOCADOR" in texto and "Cláusula 1ª" in texto       # vizinhos intactos
    assert not (meta.get("author") or "") and not (meta.get("title") or "")


def test_pagina_girada_sem_vazamento():
    pasta = F.pasta_temporaria("saida_pdf_girada")
    destino, _ = _gerar(F.contrato_pdf(pasta / "g.pdf", girar=90), "g - pseudonimizado.pdf")
    texto, _ = _texto(destino)
    assert F.PESSOA_1 not in texto and F.CPF not in texto
    assert "LOCADOR" in texto and "[[PESSOA_1]]" in texto.replace("\n", "")


def test_escaneado_pixels_apagados():
    pasta = F.pasta_temporaria("saida_pdf_ocr")
    destino, _ = _gerar(F.contrato_escaneado(pasta / "e.pdf"), "e - pseudonimizado.pdf")
    with fitz.open(str(destino)) as pdf:
        lido = normalizar(" ".join(t for t, _ in ocr_pagina(pdf[0])))
    assert "maria aparecida pereira" not in lido and "111.444.777-35" not in lido, lido
    assert "locador" in lido


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
Run → FALHA (módulo inexistente).

- [ ] **Step 2: `saida/pdf_layout.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Saída PDF no layout original: redação real (o texto sai do arquivo; na
página escaneada, os pixels da área são apagados) e o tóken escrito no mesmo
lugar, com a fonte reduzida até caber (spec §7 e §14)."""
from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path

import fitz

FONTE_MINIMA = 4.0


def _linhas(origens: list) -> list[list]:
    """Agrupa os caracteres de um trecho por página e linha (mesma altura)."""
    grupos: list[list] = []
    for o in origens:
        if grupos:
            u = grupos[-1][-1]
            altura = u.rect[3] - u.rect[1]
            if o.pagina == u.pagina and abs(o.rect[1] - u.rect[1]) < altura / 2:
                grupos[-1].append(o)
                continue
        grupos.append([o])
    return grupos


def _retangulos(grupo: list) -> tuple[fitz.Rect, fitz.Rect]:
    """(área da redação, área do tóken). Na página com texto, a redação é
    estreitada nas pontas para não levar a letra vizinha (a letra do trecho
    sai inteira mesmo assim, porque a redação remove o caractere). Na página
    escaneada, cobre a caixa toda com folga: é ela que apaga os pixels."""
    caixa = fitz.Rect(grupo[0].rect)
    for o in grupo[1:]:
        caixa |= fitz.Rect(o.rect)
    if grupo[0].ocr:
        return caixa + (-1, -1, 1, 1), caixa
    w0 = grupo[0].rect[2] - grupo[0].rect[0]
    w1 = grupo[-1].rect[2] - grupo[-1].rect[0]
    alto = caixa.height
    redacao = fitz.Rect(caixa.x0 + 0.2 * w0, caixa.y0 + 0.2 * alto, caixa.x1 - 0.2 * w1, caixa.y1 - 0.2 * alto)
    return redacao, caixa


def _escrever(pagina, area: fitz.Rect, token: str, n: int) -> str | None:
    tamanho = max(FONTE_MINIMA, area.height * 0.8)
    while tamanho >= FONTE_MINIMA:
        if pagina.insert_textbox(area, token, fontsize=tamanho, fontname="helv") >= 0:
            return None
        tamanho -= 0.5
    # não coube: o tóken vai inteiro (a restauração depende dele), avançando à direita
    pagina.insert_text((area.x0, area.y1 - 1), token, fontsize=FONTE_MINIMA, fontname="helv")
    return f"página {n + 1}: código maior que o espaço do original"


def gerar_pdf_layout(documento, trocas, destino: Path) -> list[str]:
    por_pagina: dict[int, list[tuple[fitz.Rect, fitz.Rect, str]]] = defaultdict(list)
    for t in trocas:
        origens = [o for o in documento.origens[t.ini:t.fim] if o is not None]
        for k, grupo in enumerate(_linhas(origens)):
            redacao, area = _retangulos(grupo)
            por_pagina[grupo[0].pagina].append((redacao, area, t.token if k == 0 else ""))
    avisos: list[str] = []
    pdf = fitz.open(str(documento.caminho))
    try:
        for n, itens in sorted(por_pagina.items()):
            pagina = pdf[n]
            for redacao, _, _ in itens:
                pagina.add_redact_annot(redacao, fill=(1, 1, 1))
            pagina.apply_redactions(images=fitz.PDF_REDACT_IMAGE_PIXELS,
                                    graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                                    text=fitz.PDF_REDACT_TEXT_REMOVE)
            for _, area, token in itens:
                if token and (aviso := _escrever(pagina, area, token, n)):
                    avisos.append(aviso)
        pdf.set_metadata({})
        pdf.del_xml_metadata()
        tmp = Path(destino).with_suffix(".pdf.tmp")
        pdf.save(str(tmp), garbage=4, deflate=True)
    finally:
        pdf.close()
    os.replace(tmp, destino)
    return avisos
```

- [ ] **Step 3: Rodar**

Run: `.venv/Scripts/python -X utf8 testes/test_saida_pdf.py`
Expected: `3/3 passaram`.
Se `test_pagina_girada_sem_vazamento` falhar (nome sobrando ou "LOCADOR" sumindo), os retângulos de `get_text` e os de `add_redact_annot` estão em sistemas diferentes na página girada: converta a redação e a área com `rect * pagina.rotation_matrix` (ou `derotation_matrix`; teste os dois) em `gerar_pdf_layout`, só quando `pagina.rotation != 0`. Se o tóken sair ilegível no escaneado, mantenha; a conferência é sobre ausência do dado.

- [ ] **Step 4: Commit**

```bash
git add pseudonimizador/saida/pdf_layout.py testes/test_saida_pdf.py
git commit -m "Saída PDF no layout original com redação real (texto e página escaneada)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Conferência automática, mapas e a função `gerar`

**Files:**
- Create: `pseudonimizador/saida/conferencia.py`, `pseudonimizador/saida/mapas.py`
- Modify: `pseudonimizador/saida/__init__.py`
- Test: `testes/test_gerar.py`

**Interfaces:**
- Consumes: Tasks 4–10.
- Produces:
  - `saida.conferencia.VazamentoDetectado(RuntimeError)` com atributo `valores: list[str]`; `saida.conferencia.valores_vigiados(mapa) -> list[str]`; `saida.conferencia.conferir(caminho: Path, mapa: dict, paginas_ocr: list[int] = ()) -> list[str]` (valores achados em claro).
  - `saida.mapas.gravar(pasta_mapas: Path, nome_base: str, mapa: dict) -> tuple[str, Path]` (id e caminho; grava `mapa["id"]`); `saida.mapas.carregar(caminho: Path) -> dict`; `saida.mapas.achar(pasta_mapas: Path, identificador: str) -> Path | None`; `saida.mapas.novo_id(nome_base: str) -> str`.
  - `saida.Gerado(dataclass: saida: Path, mapa: Path | None, avisos: list[str])`; `saida.gerar(documento, resultado, *, formato: str, modo: str, pasta_saida: Path, pasta_mapas: Path, tipo: str | None = None) -> Gerado` — `formato` ∈ `{"layout", "texto"}`; `modo` ∈ `{"reversivel", "definitivo"}`; `tipo` ∈ `{"docx", "pdf"}` (obrigatório em "texto"; em "layout" segue a entrada).

- [ ] **Step 1: Teste vermelho**

`testes/test_gerar.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import json
import zipfile

import fabrica as F
from pseudonimizador.leitura import ler
from pseudonimizador.revisao import Revisao
from pseudonimizador.saida import gerar
from pseudonimizador.saida.conferencia import VazamentoDetectado


def _preparar(nome):
    pasta = F.pasta_temporaria(nome)
    doc = ler(F.contrato_docx(pasta / "contrato.docx"))
    return pasta, doc, Revisao(doc).fechar()


def test_reversivel_grava_mapa_separado_e_identificador():
    pasta, doc, res = _preparar("gerar_rev")
    g = gerar(doc, res, formato="layout", modo="reversivel", pasta_saida=pasta / "Saida", pasta_mapas=pasta / "Mapas")
    assert g.saida.name == "contrato - pseudonimizado.docx" and g.saida.parent.name == "Saida"
    assert g.mapa and g.mapa.parent.name == "Mapas"
    mapa = json.loads(g.mapa.read_text(encoding="utf-8"))
    import docx
    assert docx.Document(str(g.saida)).core_properties.identifier == "pseudonimizador:" + mapa["id"]


def test_definitivo_sem_mapa():
    pasta, doc, res = _preparar("gerar_def")
    g = gerar(doc, res, formato="texto", tipo="pdf", modo="definitivo",
              pasta_saida=pasta / "Saida", pasta_mapas=pasta / "Mapas")
    assert g.mapa is None and g.saida.name == "contrato - anonimizado.pdf"
    assert not (pasta / "Mapas").exists() or not any((pasta / "Mapas").iterdir())


def test_nao_sobrescreve():
    pasta, doc, res = _preparar("gerar_dup")
    a = gerar(doc, res, formato="layout", modo="definitivo", pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    b = gerar(doc, res, formato="layout", modo="definitivo", pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    assert a.saida != b.saida and b.saida.name == "contrato - anonimizado (2).docx"


def test_nota_de_rodape_bloqueia():
    pasta, doc, res = _preparar("gerar_nota")
    # injeta uma nota de rodapé com o nome no DOCX de entrada
    com_nota = pasta / "com_nota.docx"
    with zipfile.ZipFile(doc.caminho) as z, zipfile.ZipFile(com_nota, "w") as w:
        for item in z.infolist():
            w.writestr(item, z.read(item.filename))
        w.writestr("word/footnotes.xml",
                   '<?xml version="1.0"?><w:footnotes xmlns:w="http://schemas.openxmlformats.org/'
                   f'wordprocessingml/2006/main"><w:footnote w:id="1"><w:p><w:r><w:t>{F.PESSOA_1}</w:t>'
                   '</w:r></w:p></w:footnote></w:footnotes>')
    doc2 = ler(com_nota)
    assert any("notas de rodapé" in a for a in doc2.avisos)
    try:
        gerar(doc2, Revisao(doc2).fechar(), formato="layout", modo="reversivel",
              pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    except VazamentoDetectado as e:
        assert F.PESSOA_1 in e.valores
    else:
        raise AssertionError("deveria bloquear")
    assert not (pasta / "S").exists() or not any((pasta / "S").iterdir())
    assert not (pasta / "M").exists() or not any((pasta / "M").iterdir())


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
> Nota: o `footnotes.xml` injetado não está ligado por relação; o python-docx o ignora e o zip o leva junto na saída (o layout copia o pacote). A conferência lê **todo** XML do zip — é isso que o teste exige. Se o python-docx descartar a parte não referenciada ao salvar, o teste passará sem bloquear: nesse caso, ligue a parte com uma relação em `word/_rels/document.xml.rels` na injeção (tipo `http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes`) e o `[Content_Types].xml` (`application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml`).

Run → FALHA (`cannot import name 'gerar'`).

- [ ] **Step 2: `saida/conferencia.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Conferência depois de gerar: nenhum valor do mapa pode aparecer no arquivo
de saída — em nenhuma parte dele (spec §7)."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

from ..motor.mapa import normalizar


class VazamentoDetectado(RuntimeError):
    def __init__(self, valores: list[str]):
        super().__init__(f"{len(valores)} dado(s) continuariam visíveis na saída; nada foi gerado")
        self.valores = valores


def valores_vigiados(mapa: dict) -> list[str]:
    """Identificadores e nomes com 2+ palavras (o prenome solto pode ser
    palavra comum em outro lugar do texto)."""
    vigiados = []
    for info in mapa.get("tokens", {}).values():
        valor = str(info.get("valor") or "").strip()
        if info.get("categoria") in ("pessoa", "pj") and len(valor.split()) < 2:
            continue
        if len(normalizar(valor)) >= 4:
            vigiados.append(valor)
    return vigiados


def _texto_docx(caminho: Path) -> str:
    with zipfile.ZipFile(caminho) as z:
        partes = [re.sub(r"<[^>]+>", "", z.read(n).decode("utf-8", "replace"))
                  for n in z.namelist() if n.endswith((".xml", ".rels"))]
    return " ".join(partes)


def _texto_pdf(caminho: Path, paginas_ocr) -> str:
    import fitz
    from ..leitura.ocr import ocr_pagina
    partes = []
    with fitz.open(str(caminho)) as pdf:
        partes.extend(str(v) for v in pdf.metadata.values() if v)
        for n, pagina in enumerate(pdf):
            partes.append(pagina.get_text())
            if n in paginas_ocr:
                partes.extend(t for t, _ in ocr_pagina(pagina))
    return " ".join(partes)


def conferir(caminho: Path, mapa: dict, paginas_ocr=()) -> list[str]:
    caminho = Path(caminho)
    bruto = _texto_docx(caminho) if caminho.suffix.lower() == ".docx" else _texto_pdf(caminho, set(paginas_ocr))
    texto = normalizar(bruto)
    return [v for v in valores_vigiados(mapa)
            if re.search(r"(?<!\w)" + re.escape(normalizar(v)) + r"(?!\w)", texto)]
```

- [ ] **Step 3: `saida/mapas.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Mapas do modo reversível: sempre em pasta própria, nunca ao lado da saída."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from ..motor.mapa import escrever_atomico


def novo_id(nome_base: str) -> str:
    seguro = re.sub(r"[^\w\-]+", "_", nome_base).strip("_")[:60] or "documento"
    return f"{seguro}-{datetime.now():%Y%m%d-%H%M%S-%f}"


def gravar(pasta_mapas: Path, nome_base: str, mapa: dict, identificador: str | None = None) -> tuple[str, Path]:
    identificador = identificador or novo_id(nome_base)
    mapa["id"] = identificador
    caminho = Path(pasta_mapas) / f"{identificador}.json"
    escrever_atomico(caminho, json.dumps(mapa, ensure_ascii=False, indent=1))
    return identificador, caminho


def carregar(caminho: Path) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def achar(pasta_mapas: Path, identificador: str) -> Path | None:
    caminho = Path(pasta_mapas) / f"{identificador}.json"
    return caminho if caminho.is_file() else None
```

- [ ] **Step 4: `saida/__init__.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Geração da saída: formato (layout original ou só texto), tipo (DOCX ou
PDF) e modo (reversível ou definitivo), com conferência ao final."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..motor.trocas import aplicar_trocas
from . import mapas
from .conferencia import VazamentoDetectado, conferir  # noqa: F401

PREFIXO_ID = "pseudonimizador:"


@dataclass
class Gerado:
    saida: Path
    mapa: Path | None
    avisos: list[str] = field(default_factory=list)


def _destino(pasta: Path, base: str, sufixo: str) -> Path:
    candidato = pasta / f"{base}{sufixo}"
    n = 2
    while candidato.exists():
        candidato = pasta / f"{base} ({n}){sufixo}"
        n += 1
    return candidato


def gerar(documento, resultado, *, formato: str, modo: str, pasta_saida: Path, pasta_mapas: Path,
          tipo: str | None = None) -> Gerado:
    if formato not in ("layout", "texto") or modo not in ("reversivel", "definitivo"):
        raise ValueError(f"formato/modo inválido: {formato}/{modo}")
    entrada = "docx" if documento.tipo == "docx" else "pdf"
    tipo = entrada if formato == "layout" else tipo
    if tipo not in ("docx", "pdf"):
        raise ValueError("no formato 'texto', escolha o tipo: docx ou pdf")
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    rotulo = "pseudonimizado" if modo == "reversivel" else "anonimizado"
    destino = _destino(pasta_saida, f"{Path(documento.caminho).stem} - {rotulo}", f".{tipo}")
    identificador = mapas.novo_id(Path(documento.caminho).stem) if modo == "reversivel" else ""
    avisos = list(documento.avisos)

    if formato == "texto":
        from .texto import gerar_docx_texto, gerar_pdf_texto
        texto = aplicar_trocas(documento.texto, resultado.trocas)
        (gerar_docx_texto if tipo == "docx" else gerar_pdf_texto)(texto, destino)
        paginas_ocr: list[int] = []
    elif tipo == "docx":
        from .docx_layout import gerar_docx_layout
        gerar_docx_layout(documento, resultado.trocas, destino,
                          identificador=PREFIXO_ID + identificador if identificador else "")
        paginas_ocr = []
    else:
        from .pdf_layout import gerar_pdf_layout
        avisos += gerar_pdf_layout(documento, resultado.trocas, destino)
        paginas_ocr = documento.paginas_ocr

    vazados = conferir(destino, resultado.mapa, paginas_ocr)
    if vazados:
        destino.unlink(missing_ok=True)
        raise VazamentoDetectado(vazados)

    caminho_mapa = None
    if modo == "reversivel":
        _, caminho_mapa = mapas.gravar(pasta_mapas, Path(documento.caminho).stem, resultado.mapa, identificador)
    return Gerado(destino, caminho_mapa, avisos)
```

- [ ] **Step 5: Rodar**

Run: `.venv/Scripts/python -X utf8 testes/test_gerar.py` → `4/4 passaram`. Rode também `test_saida_docx.py`, `test_saida_pdf.py`, `test_saida_texto.py` (não podem quebrar).

- [ ] **Step 6: Commit**

```bash
git add pseudonimizador/saida testes/test_gerar.py
git commit -m "Geração com conferência automática (bloqueia se algum dado ficar visível) e mapas em pasta própria

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: Restaurar nomes

**Files:**
- Create: `pseudonimizador/restaurar.py`
- Test: `testes/test_restaurar.py`

**Interfaces:**
- Consumes: `motor.reversor.despseudonimizar_texto`, `despseudonimizar_docx`, `TokenOrfao`; `saida.mapas.achar/carregar`; `saida.PREFIXO_ID`.
- Produces: `restaurar.restaurar_texto(texto: str, mapa: dict) -> str`; `restaurar.restaurar_docx(origem: Path, destino: Path, mapa: dict) -> int`; `restaurar.id_do_mapa(caminho_docx: Path) -> str | None`; `restaurar.mapa_do_docx(caminho_docx: Path, pasta_mapas: Path) -> dict | None`; reexporta `TokenOrfao`.

- [ ] **Step 1: Teste vermelho**

`testes/test_restaurar.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fabrica as F
from pseudonimizador.leitura import ler
from pseudonimizador.motor.trocas import aplicar_trocas
from pseudonimizador.restaurar import TokenOrfao, mapa_do_docx, restaurar_docx, restaurar_texto
from pseudonimizador.revisao import Revisao
from pseudonimizador.saida import gerar


def test_restaurar_docx_devolve_o_texto_original():
    pasta = F.pasta_temporaria("restaurar")
    doc = ler(F.contrato_docx(pasta / "contrato.docx"))
    g = gerar(doc, Revisao(doc).fechar(), formato="layout", modo="reversivel",
              pasta_saida=pasta / "Saida", pasta_mapas=pasta / "Mapas")
    mapa = mapa_do_docx(g.saida, pasta / "Mapas")
    assert mapa is not None
    destino = pasta / "restaurado.docx"
    assert restaurar_docx(g.saida, destino, mapa) > 0
    assert ler(destino).texto == doc.texto


def test_restaurar_texto_e_token_orfao():
    pasta = F.pasta_temporaria("restaurar2")
    doc = ler(F.contrato_docx(pasta / "contrato.docx"))
    res = Revisao(doc).fechar()
    protegido = aplicar_trocas(doc.texto, res.trocas)
    assert restaurar_texto(protegido, res.mapa) == doc.texto
    try:
        restaurar_texto("resposta citando [[PESSOA_99]]", res.mapa)
    except TokenOrfao as e:
        assert "[[PESSOA_99]]" in str(e)
    else:
        raise AssertionError("tóken órfão deveria ser apontado")


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
Run → FALHA.

- [ ] **Step 2: `restaurar.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Restaurar nomes (modo reversível): DOCX ou texto colado + o mapa. Tóken
sem correspondência no mapa é apontado (TokenOrfao), nunca ignorado."""
from __future__ import annotations

import shutil
from pathlib import Path

from .motor.reversor import TokenOrfao, despseudonimizar_docx, despseudonimizar_texto  # noqa: F401
from .saida import PREFIXO_ID, mapas


def restaurar_texto(texto: str, mapa: dict) -> str:
    return despseudonimizar_texto(texto, mapa)


def restaurar_docx(origem: Path, destino: Path, mapa: dict) -> int:
    origem, destino = Path(origem), Path(destino)
    if origem.resolve() != destino.resolve():
        shutil.copyfile(origem, destino)
    try:
        return despseudonimizar_docx(destino, mapa)
    except Exception:
        if origem.resolve() != destino.resolve():
            destino.unlink(missing_ok=True)
        raise


def id_do_mapa(caminho_docx: Path) -> str | None:
    import docx
    ident = docx.Document(str(caminho_docx)).core_properties.identifier or ""
    return ident[len(PREFIXO_ID):] if ident.startswith(PREFIXO_ID) else None


def mapa_do_docx(caminho_docx: Path, pasta_mapas: Path) -> dict | None:
    ident = id_do_mapa(caminho_docx)
    caminho = mapas.achar(pasta_mapas, ident) if ident else None
    return mapas.carregar(caminho) if caminho else None
```

- [ ] **Step 3: Rodar** → `2/2 passaram`. Se `ler(destino).texto == doc.texto` falhar só por invisíveis ou NFC, compare com `texto_limpo` dos dois lados e relate a diferença antes de afrouxar o teste.

- [ ] **Step 4: Commit**

```bash
git add pseudonimizador/restaurar.py testes/test_restaurar.py
git commit -m "Restaurar nomes a partir do DOCX ou do texto colado, com o mapa achado pelo identificador

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 13: Linha de comando, ponta a ponta e guarda de rede

**Files:**
- Create: `pseudonimizador/__main__.py`
- Test: `testes/test_cli.py`, `testes/test_ponta_a_ponta.py`, `testes/test_sem_rede.py`
- Modify: `README.md` (seção de uso)

**Interfaces:**
- Consumes: tudo acima.
- Produces: `python -m pseudonimizador detectar ARQ --revisao R.json`; `python -m pseudonimizador gerar ARQ [--revisao R.json] --formato layout|texto [--tipo docx|pdf] --modo reversivel|definitivo --saida PASTA --mapas PASTA`; `python -m pseudonimizador restaurar (ARQ.docx --saida DESTINO.docx | --texto ARQ.txt) (--mapa M.json | --mapas PASTA)`. Códigos de saída: 0 ok, 2 erro de leitura/argumento, 3 vazamento bloqueado, 4 tóken órfão. JSON da revisão: `{"arquivo": str, "itens": [{"categoria", "valor", "aceito", "exemplo"}], "acrescentar": [{"valor", "categoria"}]}`.

- [ ] **Step 1: Testes vermelhos**

`testes/test_cli.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import json
import subprocess
import sys

import fabrica as F
from _base import RAIZ


def _cli(*args):
    return subprocess.run([sys.executable, "-X", "utf8", "-m", "pseudonimizador", *map(str, args)],
                          cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")


def test_detectar_editar_gerar_restaurar():
    pasta = F.pasta_temporaria("cli")
    arq = F.contrato_docx(pasta / "contrato.docx")
    rev = pasta / "revisao.json"
    p = _cli("detectar", arq, "--revisao", rev)
    assert p.returncode == 0, p.stderr
    dados = json.loads(rev.read_text(encoding="utf-8"))
    for item in dados["itens"]:
        if item["categoria"] == "email":
            item["aceito"] = False
    dados["acrescentar"] = [{"valor": "Porto Alegre", "categoria": "outro"}]
    rev.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    p = _cli("gerar", arq, "--revisao", rev, "--formato", "layout", "--modo", "reversivel",
             "--saida", pasta / "Saida", "--mapas", pasta / "Mapas")
    assert p.returncode == 0, p.stderr
    saida = pasta / "Saida" / "contrato - pseudonimizado.docx"
    from pseudonimizador.leitura import ler
    texto = ler(saida).texto
    assert F.EMAIL in texto and "Porto Alegre" not in texto and F.PESSOA_1 not in texto
    p = _cli("restaurar", saida, "--saida", pasta / "restaurado.docx", "--mapas", pasta / "Mapas")
    assert p.returncode == 0, p.stderr
    assert "Porto Alegre" in ler(pasta / "restaurado.docx").texto


def test_erro_de_leitura_codigo_2():
    pasta = F.pasta_temporaria("cli2")
    (pasta / "x.txt").write_text("a", encoding="utf-8")
    p = _cli("detectar", pasta / "x.txt", "--revisao", pasta / "r.json")
    assert p.returncode == 2 and "formato não aceito" in p.stderr


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
`testes/test_ponta_a_ponta.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Toda combinação entrada × formato × tipo × modo: nada em claro; no
reversível com saída DOCX, restaurar devolve o original."""
import _base  # noqa: F401
import fabrica as F
from pseudonimizador.leitura import ler
from pseudonimizador.restaurar import mapa_do_docx, restaurar_docx
from pseudonimizador.revisao import Revisao
from pseudonimizador.saida import gerar

COMBINACOES = [("layout", None), ("texto", "docx"), ("texto", "pdf")]


def _entradas(pasta):
    return {"docx": F.contrato_docx(pasta / "c_docx.docx"),
            "pdf": F.contrato_pdf(pasta / "c_pdf.pdf"),
            "escaneado": F.contrato_escaneado(pasta / "c_esc.pdf")}


def test_matriz_completa():
    pasta = F.pasta_temporaria("ponta")
    falhas = []
    for nome, arq in _entradas(pasta).items():
        doc = ler(arq)
        res = Revisao(doc).fechar()
        for formato, tipo in COMBINACOES:
            for modo in ("reversivel", "definitivo"):
                rotulo = f"{nome}/{formato}/{tipo}/{modo}"
                try:
                    g = gerar(doc, res, formato=formato, tipo=tipo, modo=modo,
                              pasta_saida=pasta / "Saida", pasta_mapas=pasta / "Mapas")
                except Exception as e:  # noqa: BLE001
                    falhas.append(f"{rotulo}: {e!r}")
                    continue
                if (modo == "reversivel") != (g.mapa is not None):
                    falhas.append(f"{rotulo}: mapa inesperado")
                if modo == "reversivel" and g.saida.suffix == ".docx" and nome == "docx" and formato == "layout":
                    restaurado = g.saida.with_name(g.saida.stem + " restaurado.docx")
                    restaurar_docx(g.saida, restaurado, mapa_do_docx(g.saida, pasta / "Mapas"))
                    if ler(restaurado).texto != doc.texto:
                        falhas.append(f"{rotulo}: restauração diferente do original")
    assert not falhas, "\n".join(falhas)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
`testes/test_sem_rede.py`:
```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Nenhuma conexão de rede fora de 127.0.0.1/::1 durante o fluxo inteiro,
inclusive o OCR (spec §9)."""
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


def test_fluxo_completo_sem_rede():
    socket.socket.connect = _connect
    socket.create_connection = _create
    socket.getaddrinfo = _getaddrinfo
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
        socket.socket.connect = _connect_original
        socket.create_connection = _create_original
        socket.getaddrinfo = _getaddrinfo_original
    assert not _tentativas, f"tentativas de rede: {_tentativas}"


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
```
Run: os três → `test_cli` FALHA (sem `__main__`); `test_ponta_a_ponta` e `test_sem_rede` devem **passar** já (usam só a biblioteca) — se algum falhar, é defeito das tasks anteriores: corrija antes de seguir.

- [ ] **Step 2: `pseudonimizador/__main__.py`**

```python
# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Linha de comando do Pseudonimizador (a janela vem no Plano 2).

  detectar  ARQ --revisao R.json        detecta e grava a revisão para editar
  gerar     ARQ [--revisao R.json] ...  aplica a revisão e gera a saída
  restaurar ARQ.docx|--texto T.txt ...  devolve os nomes (modo reversível)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import VERSAO


def _revisao(arq: Path):
    from .leitura import ler
    from .revisao import Revisao
    return Revisao(ler(arq))


def _detectar(a) -> int:
    rev = _revisao(a.arquivo)
    dados = {"arquivo": str(a.arquivo), "acrescentar": [],
             "itens": [{"categoria": it.categoria, "valor": it.valor, "aceito": it.aceito,
                        "exemplo": rev.contexto(*it.ocorrencias[0])} for it in rev.itens]}
    Path(a.revisao).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(rev.itens)} item(ns) detectado(s); revise {a.revisao} e rode 'gerar'.")
    print("Atenção: o arquivo de revisão contém os dados em claro; guarde-o com cuidado.")
    for aviso in rev.documento.avisos:
        print(f"aviso: {aviso}")
    return 0


def _gerar(a) -> int:
    from .motor.mapa import normalizar
    from .saida import gerar
    rev = _revisao(a.arquivo)
    if a.revisao:
        dados = json.loads(Path(a.revisao).read_text(encoding="utf-8"))
        decisoes = {(i["categoria"], normalizar(i["valor"])): bool(i["aceito"]) for i in dados.get("itens", [])}
        for it in rev.itens:
            if it.chave in decisoes:
                it.aceito = decisoes[it.chave]
        for extra in dados.get("acrescentar", []):
            rev.acrescentar(extra["valor"], extra.get("categoria", "pessoa"))
    g = gerar(rev.documento, rev.fechar(), formato=a.formato, tipo=a.tipo, modo=a.modo,
              pasta_saida=Path(a.saida), pasta_mapas=Path(a.mapas))
    print(f"saída: {g.saida}")
    if g.mapa:
        print(f"mapa (guarde à parte): {g.mapa}")
    for aviso in g.avisos:
        print(f"aviso: {aviso}")
    return 0


def _restaurar(a) -> int:
    from .restaurar import mapa_do_docx, restaurar_docx, restaurar_texto
    from .saida import mapas
    if a.mapa:
        mapa = mapas.carregar(a.mapa)
    elif a.texto:
        raise ValueError("para texto colado, informe --mapa")
    else:
        mapa = mapa_do_docx(a.arquivo, Path(a.mapas))
        if mapa is None:
            raise ValueError("mapa não encontrado para este DOCX; informe --mapa")
    if a.texto:
        print(restaurar_texto(Path(a.texto).read_text(encoding="utf-8"), mapa))
    else:
        n = restaurar_docx(a.arquivo, Path(a.saida), mapa)
        print(f"{n} troca(s); restaurado: {a.saida}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="pseudonimizador", description=f"Pseudonimizador {VERSAO}")
    sub = p.add_subparsers(dest="comando", required=True)
    d = sub.add_parser("detectar")
    d.add_argument("arquivo", type=Path)
    d.add_argument("--revisao", type=Path, required=True)
    g = sub.add_parser("gerar")
    g.add_argument("arquivo", type=Path)
    g.add_argument("--revisao", type=Path)
    g.add_argument("--formato", choices=("layout", "texto"), required=True)
    g.add_argument("--tipo", choices=("docx", "pdf"))
    g.add_argument("--modo", choices=("reversivel", "definitivo"), required=True)
    g.add_argument("--saida", type=Path, required=True)
    g.add_argument("--mapas", type=Path, required=True)
    r = sub.add_parser("restaurar")
    r.add_argument("arquivo", type=Path, nargs="?")
    r.add_argument("--texto", type=Path)
    r.add_argument("--saida", type=Path)
    r.add_argument("--mapa", type=Path)
    r.add_argument("--mapas", type=Path, default=Path("Mapas"))
    a = p.parse_args(argv)

    from .leitura import ErroDeLeitura
    from .restaurar import TokenOrfao
    from .saida import VazamentoDetectado
    try:
        return {"detectar": _detectar, "gerar": _gerar, "restaurar": _restaurar}[a.comando](a)
    except (ErroDeLeitura, ValueError, KeyError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    except VazamentoDetectado as e:
        print(f"erro: {e}:", file=sys.stderr)
        for v in e.valores:
            print(f"  - {v}", file=sys.stderr)
        return 3
    except TokenOrfao as e:
        print(f"erro: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Rodar**

Run: `.venv/Scripts/python -X utf8 testes/test_cli.py` → `2/2 passaram`.

- [ ] **Step 4: README — seção de uso**

Troque a seção "Uso pela linha de comando" do `README.md` por:
```markdown
## Uso pela linha de comando

1. Detectar e gerar o arquivo de revisão (contém os dados em claro — guarde com cuidado):

       .venv\Scripts\python -X utf8 -m pseudonimizador detectar contrato.pdf --revisao revisao.json

2. Editar `revisao.json`: `"aceito": false` deixa um item em claro; em
   `"acrescentar"`, inclua `{"valor": "...", "categoria": "pessoa"}` para o que escapou.

3. Gerar (layout original ou só texto; reversível ou definitivo):

       .venv\Scripts\python -X utf8 -m pseudonimizador gerar contrato.pdf --revisao revisao.json --formato layout --modo reversivel --saida Saida --mapas Mapas

4. Restaurar os nomes de um DOCX reversível:

       .venv\Scripts\python -X utf8 -m pseudonimizador restaurar "Saida\contrato - pseudonimizado.docx" --saida restaurado.docx --mapas Mapas
```

- [ ] **Step 5: Suíte inteira e guardas**

Run:
```bash
.venv/Scripts/python -X utf8 testes/executar_todos.py
.venv/Scripts/python -W error -m compileall -q pseudonimizador testes
```
Expected: todos os arquivos passam; `compileall` sem aviso.

- [ ] **Step 6: Commit**

```bash
git add pseudonimizador/__main__.py testes/test_cli.py testes/test_ponta_a_ponta.py testes/test_sem_rede.py README.md
git commit -m "Linha de comando (detectar, gerar, restaurar), teste ponta a ponta e guarda de rede

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Depois deste plano

O **Plano 2** (janela local com arrastar e soltar e tela de revisão, pasta
monitorada `Entrada\ Saida\ Mapas\`, instância única, `Pseudonimizador.bat`)
será escrito sobre as interfaces deste: `leitura.ler`, `revisao.Revisao`
(`itens`, `aceitar`, `recusar`, `acrescentar`, `contexto`, `fechar`),
`saida.gerar`, `restaurar.*`.
