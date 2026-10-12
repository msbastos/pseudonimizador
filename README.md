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

1. Detectar e gerar o arquivo de revisão (contém os dados em claro — guarde com cuidado):

       .venv\Scripts\python -X utf8 -m pseudonimizador detectar contrato.pdf --revisao revisao.json

2. Editar `revisao.json`: `"aceito": false` deixa um item em claro; em
   `"acrescentar"`, inclua `{"valor": "...", "categoria": "pessoa"}` para o que escapou.

3. Gerar (layout original ou só texto; reversível ou definitivo):

       .venv\Scripts\python -X utf8 -m pseudonimizador gerar contrato.pdf --revisao revisao.json --formato layout --modo reversivel --saida Saida --mapas Mapas

4. Restaurar os nomes de um DOCX reversível:

       .venv\Scripts\python -X utf8 -m pseudonimizador restaurar "Saida\contrato - pseudonimizado.docx" --saida restaurado.docx --mapas Mapas

## Testes

    .venv\Scripts\python -X utf8 testes/executar_todos.py
