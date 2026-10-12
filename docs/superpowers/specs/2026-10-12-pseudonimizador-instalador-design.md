# Pseudonimizador — instalador para Windows e publicação

Data: 12/10/2026 · Situação: desenho aprovado em conversa.

## 1. Objetivo

Um único `Pseudonimizador-Setup.exe` que roda num Windows 10 (1809+) ou 11 de
64 bits sem nada instalado (sem Python, sem Visual C++ Redistributable, sem
administrador). O usuário executa o instalador, indica a pasta dos arquivos e
usa o app pelo atalho. Publicação num repositório público
`github.com/msbastos/pseudonimizador`, com o instalador anexado à Release
`v0.2.0`.

**Critérios de sucesso**

1. Num Windows limpo (Windows Sandbox), sem administrador: instala, abre a
   janela pelo atalho, lê DOCX, PDF com texto e PDF escaneado (OCR), gera a
   saída, restaura, encerra; desinstala sem apagar a pasta dos arquivos.
2. Nenhuma conexão de rede em nenhum desses passos.
3. O instalador e o `SHA256SUMS.txt` publicados numa Release do repositório
   público; o executável fica fora do git.

## 2. Montagem (script `empacotamento/construir.py`)

Padrão adaptado do empacotamento do Ulpiano (mesmo autor; crédito em
`CREDITOS.md`):

- **Python embarcável** 3.14 x64 de python.org, baixado e conferido por SHA-256
  (versão, URL e hash em `empacotamento/python-embarcavel.toml`); `._pth` com a
  pasta do app no caminho, sem `import site`.
- **Bibliotecas** de um `requirements.lock` com `--hash=sha256`, instaladas com
  `pip --no-deps --require-hashes --only-binary=:all: --platform win_amd64
  --target`. Redução de tamanho: `opencv-python-headless` em vez de
  `opencv-python`; sem SymPy (dependência declarada do onnxruntime que o OCR não
  usa ao rodar). Se a conferência (abaixo) falhar sem elas, a redução é
  desfeita e registrada.
- **CRT do Visual C++** copiado app-local da pasta Redist do Visual Studio
  (`--crt PASTA`; o script acha a pasta padrão se existir). Nunca do System32
  num build publicado.
- **Código do app** a partir de um manifesto (lista fechada: `pseudonimizador/`
  sem testes nem caches, `LICENSE`, `CREDITOS.md`, `README.md`).
- **Conferência pós-montagem** com o Python empacotado, a partir de outra pasta
  e com a rede bloqueada: importa tudo, lê um DOCX e um PDF sintéticos, faz OCR
  de uma página escaneada sintética, gera e confere a saída.
- **Inno Setup 6** (`ISCC.exe`, achado no local padrão ou por `--iscc`) compila
  `empacotamento/pseudonimizador.iss`; saídas em `dist/`:
  `Pseudonimizador-Setup.exe`, `SHA256SUMS.txt` e um `.wsb` para o Sandbox.
- `build/` e `dist/` no `.gitignore`.

## 3. Instalador (`pseudonimizador.iss`)

- `PrivilegesRequired=lowest`; pasta `{localappdata}\Programs\Pseudonimizador`
  (sem página de pasta do programa); só x64; `MinVersion=10.0.17763`;
  português do Brasil; ícone próprio; versão da `VERSAO` do pacote.
- `AppMutex=Pseudonimizador-Servidor` (o instalador não roda com o app aberto).
- **Página única de escolha:** "Pasta dos arquivos" (padrão
  `{userdocs}\Pseudonimizador`), explicando que lá ficam `Entrada`, `Saida` e
  `Mapas`. Após instalar, o instalador chama o próprio app
  (`pythonw -X utf8 -m pseudonimizador configurar --pasta-base <pasta>`), que
  valida e grava `config.json` e cria as pastas. Novo subcomando `configurar`
  na CLI.
- Atalhos: menu Iniciar e Área de Trabalho (opcional), para
  `{app}\python\pythonw.exe -X utf8 -m pseudonimizador`, pasta de trabalho
  `{app}`. Opção "Abrir o Pseudonimizador" ao terminar.
- Atualização por cima: `InstallDelete` só das pastas do programa (`python`,
  `pseudonimizador`).
- Desinstalação: remove `{app}`; pergunta (padrão Não) se apaga também as
  configurações em `%LOCALAPPDATA%\Pseudonimizador`; **nunca** apaga a pasta dos
  arquivos nem os mapas.

## 4. Publicação

- Antes de publicar: suíte verde; guarda de dados reais; varredura do histórico
  inteiro (`git log --all -p`) por e-mail pessoal, caminhos da máquina e nomes
  do relato real; autor e responsável de todos os commits com o e-mail privado
  do GitHub (já reescrito).
- `gh repo create msbastos/pseudonimizador --public` com descrição em
  português; `git push -u origin main`.
- `gh release create v0.2.0` com o `Setup.exe` e o `SHA256SUMS.txt`, notas em
  português (o que é, requisitos, aviso do SmartScreen por não ser assinado,
  como conferir o SHA-256).
- README: seção "Instalação" para o usuário final (baixar da Release, aviso do
  SmartScreen, escolher a pasta) e "Montar o instalador" para o mantenedor.

## 5. Fora deste trabalho

Assinatura digital do executável, atualização automática, instalação para todos
os usuários, macOS.
