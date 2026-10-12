'use strict';
(function () {
  const TOKEN = new URLSearchParams(location.hash.replace(/^#/, '')).get('t') || '';
  const $ = (id) => document.getElementById(id);
  const SITUACOES = { lendo: 'lendo…', revisao: 'aguardando revisão', gerando: 'gerando…', pronto: 'pronto', erro: 'erro' };
  const CATEGORIAS = { pessoa: 'Pessoa', empresa: 'Empresa', cpf: 'CPF', cnpj: 'CNPJ', rg: 'RG', pis: 'PIS', ctps: 'CTPS',
    email: 'E-mail', telefone: 'Telefone', endereco: 'Endereço', conta: 'Conta bancária', url: 'Endereço web', outro: 'Outro' };
  const LIMITE = 100 * 1024 * 1024;   // o mesmo limite do servidor; conferido aqui para o aviso aparecer sem enviar
  let config = null;
  let atual = null;              // id do documento em revisão/resultado
  let docRevisado = null;        // documento cujas opções de geração já foram preenchidas
  let assinatura = '';           // JSON da última lista desenhada: sem mudança, sem redesenhar
  let sequencia = 0;             // só a resposta mais recente da lista é desenhada
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
    let r;
    try { r = await fetch(caminho, opcoes); } catch (e) {
      const falha = new Error('Não foi possível falar com o Pseudonimizador. Ele pode ter sido encerrado; abra-o de novo pelo atalho.');
      falha.rede = true;
      throw falha;
    }
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
    if (tela !== 'documentos') esperandoGeracao = false;
    if (tela !== 'restaurar') {
      for (const id of ['rest-texto', 'rest-texto-saida', 'rest-arquivo']) $(id).value = '';
      $('rest-docx-resultado').textContent = '';
    }
    if (tela === 'documentos') { assinatura = ''; atualizarLista(); }
    if (tela === 'restaurar') carregarMapas();
    if (tela === 'configuracoes') preencherConfig();
  }

  function botao(rotulo, acao, classe, id) {
    const b = document.createElement('button');
    if (id) { b.dataset.id = id; b.dataset.acao = rotulo; }
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
      if (arq.name.length > 150) { mensagem('Nome de arquivo longo demais (máximo 150 caracteres): ' + arq.name, true); continue; }
      if (arq.size > LIMITE) { mensagem('Arquivo maior que 100 MB: ' + arq.name, true); continue; }
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
    if (d.revisavel && (d.situacao === 'revisao' || d.situacao === 'erro')) acoes.append(botao('Revisar', () => abrirRevisao(d.id), '', d.id));
    if (d.situacao === 'pronto') acoes.append(botao('Resultado', () => abrirResultado(d.id), '', d.id));
    acoes.append(botao('Descartar', () => descartar(d.id), 'secundario', d.id));
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
    const minha = ++sequencia;
    try { dados = await api('GET', '/api/documentos'); } catch (e) { if (minha === sequencia) mensagem(e.message, true); return; }
    if (minha !== sequencia) return;      // chegou uma resposta mais nova: esta é velha
    const nova = JSON.stringify(dados.documentos);
    if (nova !== assinatura) {
      assinatura = nova;
      const foco = document.activeElement;
      const lembrado = foco && foco.dataset && foco.dataset.id ? [foco.dataset.id, foco.dataset.acao] : null;
      const janela = $('lista-janela');
      const pasta = $('lista-pasta');
      janela.replaceChildren();
      pasta.replaceChildren();
      for (const d of dados.documentos) (d.origem === 'pasta' ? pasta : janela).append(linhaDocumento(d));
      if (!janela.children.length) janela.append(vazio('Nenhum documento enviado.'));
      if (!pasta.children.length) pasta.append(vazio('Nada pendente.'));
      if (lembrado) {
        for (const b of document.querySelectorAll('#tela-documentos button[data-id]')) {
          if (b.dataset.id === lembrado[0] && b.dataset.acao === lembrado[1]) { b.focus(); break; }
        }
      }
    }
    if (atual && esperandoGeracao) {
      const d = dados.documentos.find((x) => x.id === atual);
      if (d && d.situacao === 'pronto') { esperandoGeracao = false; abrirResultado(atual); }
      if (d && d.situacao === 'erro') { esperandoGeracao = false; abrirRevisao(atual); }
    }
  }

  async function descartar(id) {
    if (!window.confirm('Descartar este documento?')) return;
    try { await api('DELETE', '/api/documentos/' + id); } catch (e) { mensagem(e.message, true); }
    if (atual === id) { atual = null; esperandoGeracao = false; }
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
    const outro = docRevisado !== id;
    docRevisado = id;
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
    if (config && outro) { marcar('formato', config.formato); marcar('tipo', config.tipo); marcar('modo', config.modo); }
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
      mostrar('documentos');
      esperandoGeracao = true;
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
    if (arq.size > LIMITE) { $('rest-docx-resultado').textContent = 'Arquivo maior que 100 MB: ' + arq.name; return; }
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
      $('aviso-pastas').hidden = true;       // salvar exige criar as pastas: elas existem agora
      mensagem('Configuração salva.');
    } catch (e) { mensagem(e.message, true); }
  });

  // --- Zona de arrastar e soltar, menu, encerrar ---------------------------
  const zona = $('zona');
  zona.addEventListener('dragover', (ev) => { ev.preventDefault(); zona.classList.add('ativa'); });
  zona.addEventListener('dragleave', () => zona.classList.remove('ativa'));
  zona.addEventListener('drop', (ev) => { ev.preventDefault(); zona.classList.remove('ativa'); enviar(Array.from(ev.dataTransfer.files)); });
  zona.addEventListener('click', (ev) => { if (ev.target.tagName !== 'LABEL') $('arquivos').click(); });
  zona.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); $('arquivos').click(); } });
  $('arquivos').addEventListener('change', () => {
    const escolhidos = Array.from($('arquivos').files);      // a FileList é viva: copiar antes de limpar o campo
    $('arquivos').value = '';
    enviar(escolhidos);
  });
  // um arquivo solto fora da zona não pode ser aberto pelo navegador no lugar da janela
  window.addEventListener('dragover', (ev) => ev.preventDefault());
  window.addEventListener('drop', (ev) => ev.preventDefault());
  for (const b of document.querySelectorAll('nav [data-tela]')) b.addEventListener('click', () => mostrar(b.dataset.tela));
  $('encerrar').addEventListener('click', async () => {
    if (!window.confirm('Encerrar o Pseudonimizador? Documentos ainda não gerados serão descartados.')) return;
    let fechou = false;
    try { await api('POST', '/api/encerrar'); } catch (e) {
      if (!e.rede) { mensagem(e.message, true); return; }
      fechou = true;          // a conexão caiu logo depois do pedido: o aplicativo já saiu
    }
    window.clearInterval(relogio);
    const p = document.createElement('p');
    p.className = 'mensagem';
    p.textContent = fechou ? 'O aplicativo foi encerrado. Pode fechar esta janela.'
      : 'O Pseudonimizador vai se encerrar assim que terminar o que está fazendo. Pode fechar esta janela.';
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
  const relogio = window.setInterval(() => { if (TOKEN && !$('tela-documentos').hidden) atualizarLista(); }, 2000);
  if (!TOKEN) mensagem('Abra o Pseudonimizador pelo atalho: sem o endereço de sessão a janela não funciona.', true);
  function aplicarEstado(e) {
    $('versao').textContent = e.versao;
    $('aviso-pastas').hidden = e.pastas_disponiveis !== false;
  }
  api('GET', '/api/estado').then(aplicarEstado).catch(() => {});
  // batimento: mantém a sessão viva em qualquer tela (a inatividade conta pedidos à API)
  window.setInterval(() => { if (TOKEN) api('GET', '/api/estado').then(aplicarEstado).catch(() => {}); }, 60000);
  carregarConfig().then(() => mostrar('documentos'));
})();
