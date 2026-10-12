# Pseudonimizador — especificação do desenho

Data: 11/10/2026 · Situação: desenho aprovado em conversa; especificação em revisão.

## 1. Objetivo

Aplicativo **autônomo** para Windows que recebe documentos avulsos (contratos,
petições, laudos, correspondência), encontra os dados pessoais e entrega uma
versão protegida em Word ou PDF, conforme a LGPD. Não depende do Ulpiano nem
de processo judicial: não há capa do PJe, número CNJ, dossiê ou minuta.

**Critérios de sucesso**

1. Um contrato em DOCX, PDF com texto ou PDF escaneado sai sem nenhum nome,
   documento, contato, endereço ou dado bancário em claro, depois da revisão.
2. No modo "layout original", o documento de saída tem a mesma aparência do
   original e, no PDF, o dado é **removido** do arquivo (não apenas coberto).
3. No modo reversível, "Restaurar nomes" devolve o texto original exato a
   partir da saída (DOCX ou texto colado) e do mapa.
4. Nenhum byte do documento sai da máquina; um teste garante a ausência de
   conexões de rede além do servidor local.

## 2. Decisões tomadas na conversa

| Tema | Decisão |
|---|---|
| Relação com o Ulpiano | Projeto independente, repositório próprio, **cópia** do motor (fork). O Ulpiano não é alterado. |
| Plataforma | Windows. |
| Finalidade | Por documento: **reversível** (pseudonimização, mapa guardado) ou **definitivo** (anonimização, mapa descartado). |
| Nomes | Detecção automática **com revisão humana** obrigatória (aceitar, recusar, acrescentar). |
| Entrada | DOCX, PDF com texto e PDF escaneado com **OCR local** (RapidOCR). Nada de OCR externo. |
| Saída | Por documento: **layout original** (DOCX→DOCX, PDF→PDF) ou **documento novo só com o texto** (DOCX ou PDF). |
| Uso | **Janela** com arrastar e soltar **e pasta monitorada** para lotes. |
| O que se substitui | **Tudo, sempre**: pessoas, empresas, documentos (CPF, CNPJ, RG, PIS, CTPS etc.), contatos (e-mail, telefone), endereço e CEP, dados bancários. Não há níveis de sigilo. |
| Nome e pasta | `Pseudonimizador`, em pasta própria ao lado do Ulpiano. |

## 3. Arquitetura

```
pseudonimizador/
  motor/        cópia do pacote privacidade do Ulpiano (texto → texto, mapa)
  leitura/      DOCX, PDF com texto, PDF escaneado (OCR) → Documento com posições
  deteccao/     candidatos a nome de pessoa/empresa + identificadores → Ocorrências
  revisao/      estado da revisão de um documento (aceitas, recusadas, acrescidas)
  saida/        layout original (DOCX, PDF) e só texto (DOCX, PDF); restaurar
  pastas/       pasta monitorada (Entrada, Saida, Mapas, Pendentes)
  web/          servidor local + página (arrastar e soltar, revisão, restaurar)
  app.py        ponto de entrada (abre a janela)
testes/         runner próprio, um arquivo por unidade, dados sintéticos
```

Cada unidade tem uma entrada e uma saída claras e é testável sozinha:

| Unidade | Recebe | Devolve |
|---|---|---|
| `leitura` | caminho do arquivo | `Documento`: lista de `Trecho(texto, local)`, texto corrido e tabela deslocamento → local |
| `deteccao` | texto corrido | lista de `Ocorrencia(ini, fim, categoria, valor, sugerida: bool)` |
| `revisao` | ocorrências + decisões do usuário | mapa final (`tokens`) e lista de trocas `(ini, fim, token)` |
| `saida` | `Documento` + trocas + modo/formato | arquivo de saída (+ mapa no modo reversível) |
| `motor` | texto + mapa | texto pseudonimizado; trocas com posições |

## 4. Motor (cópia do Ulpiano)

- Copiado de `ulpiano/nucleo/privacidade/` (Ulpiano, commit `5bab2ff`):
  `pseudonimizador.py`, `lexico.py` + `lexico_ibge.json`, `mapa.py`,
  `reversor.py`, `incertos.py`. Cada arquivo leva nota de origem no cabeçalho.
- **Cortes** dos laços com o resto do Ulpiano:
  - `nivel.py` vira um módulo mínimo e fixo: nomes e empresas **sempre** em
    código (equivale ao nível sigiloso). `nivel_sinais.json` não vem.
  - `execucao.escrever_atomico` → função local em `mapa.py`.
  - `seletor.conversas._norm`, `seletor.provas.CATEGORIAS` e
    `segmentador.taxonomia.classificar` (usados só no fluxo de autos e de
    documento de menor): os ramos que dependem deles saem; o que for preciso
    é reescrito localmente.
  - `incertos.py`: sem `nomes_decididos.json` do dossiê; a decisão vem da
    tela de revisão.
- **Acréscimo necessário — trocas com posições.** O motor hoje devolve só o
  texto trocado. Para substituir no lugar (DOCX/PDF), expõe-se
  `trocas(texto, mapa) -> list[(ini, fim, token)]`, montada a partir de
  `_spans_de_identificadores` e `_spans_de_nomes`, com a garantia (testada) de
  que aplicar as trocas ao texto dá exatamente `pseudonimizar(texto, mapa)`.
- Os testes do motor que não dependem do fluxo de autos vêm junto
  (`test_pseudonimizador*`, `test_mapa_pseudonimos`, `test_reversor`,
  `test_lexico_ibge`), ajustados aos imports novos. Os de nível, seletor e
  montador ficam no Ulpiano.

## 5. Leitura

- **DOCX** (python-docx): corpo, tabelas, cabeçalhos e rodapés. Local = (parte,
  parágrafo, run, deslocamento no run). Caixas de texto e notas de rodapé: lidas
  se o python-docx alcançar; senão, aviso na revisão de que não foram tratadas.
- **PDF com texto** (PyMuPDF `get_text("rawdict")`): local = (página,
  retângulo de cada caractere).
- **PDF escaneado**: página sem camada de texto (critério: menos de N
  caracteres extraíveis) → RapidOCR local; local = (página, caixa da linha;
  posição do caractere estimada proporcionalmente dentro da caixa).
  PDF misto: cada página segue o seu caso.
- PDF protegido por senha, DOCX corrompido ou formato não aceito: erro claro na
  janela, nada é gerado.

## 6. Detecção e revisão

- **Identificadores** (CPF, CNPJ, RG, PIS, CTPS, e-mail, telefone, endereço,
  CEP, conta): os detectores do motor, já testados.
- **Nomes de pessoas** (novo, sem capa do PJe): candidatos por
  1. âncoras de qualificação comuns em contratos ("CONTRATANTE:", "LOCADOR:",
     "outorgante", "nacionalidade, estado civil, profissão, portador do CPF");
  2. sequências de palavras com prenome e sobrenome do léxico IBGE do motor
     (`_ler_nome`, `_prenome_provado`), sem depender de maiúsculas (a caixa não
     indica nome próprio).
- **Empresas** (novo): sufixos societários (Ltda., S.A., S/A, ME, EPP,
  EIRELI, SLU), "razão social" e o nome ligado a um CNPJ.
- Cada candidato vira uma ocorrência **sugerida**; a tela mostra o trecho em
  volta e permite aceitar, recusar ou acrescentar (selecionando no texto ou
  digitando). Aceitar um nome aceita todas as suas ocorrências e variantes
  (o motor já casa variantes e partes do nome).
- Só depois da revisão o mapa é fechado e as trocas são calculadas. Nada é
  gerado sem a confirmação.

## 7. Saída

**Layout original**

- DOCX: a troca é feita nos runs. Quando um trecho atravessa vários runs, o
  tóken fica no primeiro (com a formatação dele) e os demais perdem a parte
  trocada. Metadados do arquivo (autor, empresa, últimos editores, comentários
  e revisões controladas) são limpos.
- PDF com texto: `add_redact_annot` sobre os retângulos do trecho e
  `apply_redactions` (o texto original sai do arquivo); o tóken é escrito no
  mesmo lugar com `insert_textbox`, reduzindo a fonte até caber. Metadados do
  PDF limpos.
- PDF escaneado: a redação apaga os pixels da área na imagem
  (`PDF_REDACT_IMAGE_PIXELS`), e o tóken é escrito por cima.
- Depois de gerar, **conferência automática**: o texto extraído da saída não
  pode conter nenhum valor do mapa; se contiver, o arquivo é apagado e a
  revisão reabre com o aviso.

**Só o texto**: um DOCX (python-docx) ou PDF (PyMuPDF) novo, com os parágrafos
do texto já trocado.

**Modos**

- Reversível: o mapa vai para `Mapas\` (nunca ao lado da saída), com nome
  `<arquivo>-<data-hora>.json`. A saída DOCX leva nas propriedades
  personalizadas só o identificador do mapa, nenhum dado.
- Definitivo: o mapa só existe em memória e é descartado ao final.
- **Restaurar nomes**: recebe um DOCX ou texto colado e o mapa (achado pelo
  identificador ou escolhido) e usa o `reversor` do motor. Tóken sem
  correspondência no mapa é apontado, não ignorado.

## 8. Uso: janela e pasta monitorada

- **Janela**: servidor HTTP local (biblioteca padrão) em `127.0.0.1`, porta
  livre, aberto no Edge em modo aplicativo (`msedge --app=`), como no Ulpiano;
  sem Edge, o navegador padrão. Um token de sessão na URL protege a API.
  Telas: arrastar e soltar → revisão → escolha de modo e formato → resultado;
  "Restaurar nomes"; "Pendentes" (itens da pasta monitorada).
- **Pasta monitorada**: base configurável (padrão
  `%USERPROFILE%\Documents\Pseudonimizador`) com `Entrada\`, `Saida\`,
  `Mapas\`. Verificação periódica da `Entrada\` enquanto o app está aberto.
  Arquivo novo é lido e detectado e fica em **Pendentes** até a revisão; modo
  e formato padrão do lote vêm das configurações. O original sai da `Entrada\`
  depois de gerada a saída (para `Entrada\Processados\`).
- Instância única: uma segunda abertura reaproveita o servidor já ativo.

## 9. Segurança e privacidade

- Nenhuma conexão de rede além de `127.0.0.1`. Teste: durante a suíte,
  qualquer `socket.connect` para outro endereço falha o teste.
- Arquivos temporários na pasta do app, apagados ao final; registros (log)
  nunca levam valores do documento, só categorias e contagens.
- O mapa é dado pessoal: fica em `Mapas\`, separado da saída. (Cifrar o mapa
  fica para versão futura.)
- Conteúdo do documento é dado, nunca instrução.

## 10. Testes

- TDD; runner próprio (`testes/_runner.py`) e execução em paralelo
  (`testes/executar_todos.py`), no padrão do Ulpiano; sem pytest.
- Documentos sintéticos gerados no próprio teste: contratos em DOCX (com
  tabela, cabeçalho e run partido), PDF com texto e PDF escaneado (página
  rasterizada a partir do texto).
- Guardas: `test_sem_dados_reais.py` (nada de dado real, caminho da máquina ou
  usuário no repositório), `test_sem_rede.py`, `test_licenca.py` (SPDX e
  créditos).
- Ponta a ponta: para cada formato de entrada × saída × modo, nenhum valor do
  mapa no texto extraído da saída; no reversível, restaurar devolve o original.

## 11. Licença e autoria

O motor deriva do Ulpiano (AGPL-3.0-only); o Pseudonimizador também é
**AGPL-3.0-only**, com os cabeçalhos SPDX e o termo adicional de preservação
dos avisos de autoria. `CREDITOS.md` e `README.md` registram a autoria e a
origem do motor.

## 12. Dependências

Python 3.14; `pymupdf`, `python-docx`, `rapidocr` + `onnxruntime` (CPU; DirectML
opcional), nas mesmas versões do Ulpiano. Interface sem framework (HTML, CSS
e JS próprios).

## 13. Fora da primeira versão

Instalador `.exe` (a primeira versão abre por `Pseudonimizador.bat` com
ambiente virtual), imagens soltas (JPG/PNG), outros formatos (TXT, RTF, e-mail),
cifra do mapa, níveis de sigilo, macOS.

## 14. Riscos conhecidos

- **Nomes sem capa**: o motor foi afinado com a lista de partes do PJe; a
  detecção de candidatos é nova e vai errar nos primeiros usos. Por isso a
  revisão é obrigatória.
- **Tóken maior que o nome no PDF**: fonte reduzida até um mínimo legível;
  se ainda não couber, o tóken (sempre completo, para que a restauração
  funcione) avança sobre o espaço seguinte e o resultado avisa a página.
- **OCR erra letras de nomes**: o tóken cobre a área da linha detectada; a
  conferência automática final roda sobre o texto do OCR da saída.
