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

Produz, em `dist\`: `Pseudonimizador-Setup.exe` e `SHA256SUMS.txt`; o
`Pseudonimizador-Sandbox.wsb` (mapeia `dist\` em só leitura, GPU virtual
ligada, **rede desligada**, e abre o Setup ao entrar no Sandbox) sai em
`build\`, porque leva o caminho desta máquina.

- Só a árvore do aplicativo, sem compilar: `--so-montar` (sai em `build\app`).
- A fumaça (`fumaca.py`) roda no Python embarcado, de outra pasta e com a
  rede bloqueada: importa tudo, lê DOCX, PDF com texto e PDF escaneado
  (OCR), gera e restaura. Se falhar, o build para.
- O ícone vem de `gerar_icone.py` (arte sintética, sem arquivo externo);
  o `.ico` gerado é rastreado.

### Trocar a versão do Python embarcável

Em `python-embarcavel.toml`, troque os três campos juntos (`versao`, `url`,
`sha256` do "Windows embeddable package (64-bit)"). Quando python.org não
publica o SHA-256 desse zip, calcule-o do próprio download por HTTPS
(`certutil -hashfile <zip> SHA256`): é confiança no primeiro uso (TOFU), como
registram o comentário do `.toml` e as notas da release. O `construir.py`
recusa o zip se o hash ou o tamanho não baterem. Se a série (3.14) mudar,
regenere o lock.

### Regenerar o `requirements.lock`

    .venv\Scripts\python -X utf8 empacotamento/gerar_lock.py

### Redução de tamanho

O pacote leva `opencv-python-headless` no lugar do `opencv-python` (sem a
GUI do OpenCV) e não leva `sympy`/`mpmath` (dependência declarada do
`onnxruntime` que o OCR não usa ao rodar). A fumaça prova que o OCR funciona
assim. Estado: mantida; `build\app` com 343 MB sem compressão; `Pseudonimizador-Setup.exe` com 105 MB (build de 12/10/2026, sem .pyc nem lançadores: ver a guarda de identidade do `construir.py`).

## 3. Aceitação no Windows Sandbox (manual)

Duplo clique em `build\Pseudonimizador-Sandbox.wsb`. Dentro do Sandbox não há
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
