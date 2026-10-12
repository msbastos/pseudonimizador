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
