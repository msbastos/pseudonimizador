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

Baixe `Pseudonimizador-Setup.exe` (cerca de 111 MB) na página de Releases do
repositório (`https://github.com/msbastos/pseudonimizador/releases/latest`) e
execute-o. Requisitos: Windows 10 (1809 ou mais novo) ou Windows 11, 64 bits;
instala só para o seu usuário, sem administrador e sem internet.

- O instalador não é assinado digitalmente, então o Windows mostra o aviso
  do SmartScreen ("O Windows protegeu o computador"): clique em
  **Mais informações** e em **Executar assim mesmo**. Para conferir o arquivo,
  compare `certutil -hashfile Pseudonimizador-Setup.exe SHA256` com o
  `SHA256SUMS.txt` publicado junto.
- A única pergunta é a **Pasta dos arquivos** (padrão
  `Documentos\Pseudonimizador`), onde ficam `Entrada`, `Saida` e `Mapas`. O
  instalador recusa uma pasta dentro da pasta do programa ou da pasta de
  configurações.
- Desinstalar (Configurações › Aplicativos) remove o programa e pergunta se
  apaga também as configurações (a resposta padrão é não); a pasta dos
  arquivos, com os mapas, nunca é apagada.

## Instalação para desenvolvimento

    py -3.14 -m venv .venv
    .venv\Scripts\python -m pip install -r requirements.txt

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
- **Encerrar** (no menu) fecha o servidor assim que terminar o que está fazendo e descarta os
  documentos ainda não gerados (em revisão ou com erro); sem uso por 30 minutos ele também se
  encerra, mas só se não houver nada pendente nem em revisão. Abrir o atalho de novo com o app aberto só abre outra janela. Se o app aberto for de outra versão e houver documento em andamento
  (lendo, em revisão, gerando ou com erro), ele não é trocado: feche o aplicativo pelo menu Encerrar para atualizar.

Estado, configuração e log ficam em `%LOCALAPPDATA%\Pseudonimizador` (`config.json`,
`logs\servidor.log` — sem valores nem nomes de arquivo). Os mapas são dado pessoal: ficam em
`Mapas\`, separados da saída.

## Uso pela linha de comando

1. Detectar e gerar o arquivo de revisão (contém os dados em claro — guarde com cuidado):

       .venv\Scripts\python -X utf8 -m pseudonimizador detectar contrato.pdf --revisao revisao.json

2. Editar `revisao.json`: `"aceito": false` deixa um item em claro; em
   `"acrescentar"`, inclua `{"valor": "...", "categoria": "pessoa"}` para o que escapou.

3. Gerar (layout original ou só texto; reversível ou definitivo):

       .venv\Scripts\python -X utf8 -m pseudonimizador gerar contrato.pdf --revisao revisao.json --formato layout --modo reversivel --saida Saida --mapas Mapas

4. Restaurar os nomes de um DOCX reversível:

       .venv\Scripts\python -X utf8 -m pseudonimizador restaurar "Saida\contrato - pseudonimizado.docx" --saida restaurado.docx --mapas Mapas

   Para texto colado (um `.txt` com os tókens), informe o mapa explicitamente:

       .venv\Scripts\python -X utf8 -m pseudonimizador restaurar --texto texto.txt --mapa Mapas\MAPA.json

## Montar o instalador

Para o mantenedor: `.venv\Scripts\python -X utf8 empacotamento/construir.py`
monta `buildpp` (Python 3.14 embarcável, bibliotecas do `requirements.lock`
com hashes, CRT do Visual C++ app-local, código pelo manifesto), roda a fumaça
no Python embarcado e compila `dist\Pseudonimizador-Setup.exe` com o Inno
Setup 6. Pré-requisitos, aceitação no Windows Sandbox e conferência
pré-publicação: `empacotamento/README.md`.

## Testes

    .venv\Scripts\python -X utf8 testes/executar_todos.py
