/* ============================================================
   NEXO — Demo interativa v2
   Login por perfil (RBAC), persistência local, código de barras,
   lotes/validade, pedidos, recibo, auditoria.
   ============================================================ */
(function () {
  'use strict';

  var STORAGE_KEY = 'nexoDemoStateV2';
  var ROLE_LABEL = { superadmin: 'Super Admin', admin: 'Administrador', funcionario: 'Funcionário', cliente: 'Cliente' };
  var STAFF = ['admin', 'superadmin'];

  /* ---------- Dados padrão ---------- */
  function dias(n) {
    var d = new Date();
    d.setDate(d.getDate() + n);
    return d.toISOString().slice(0, 10);
  }

  function defaultState() {
    return {
      sessionUserId: null,
      proximaVenda: 126,
      proximoPedido: 1,
      users: [
        { id: 1, nome: 'João Silva', email: 'admin@nexoerp.com', senha: 'demo123', telefone: '(11) 90000-0001', perfil: 'admin', ativo: true },
        { id: 2, nome: 'Carlos Almeida', email: 'caixa@nexoerp.com', senha: 'demo123', telefone: '(11) 90000-0002', perfil: 'funcionario', ativo: true },
        { id: 3, nome: 'Maria Oliveira', email: 'cliente@nexoerp.com', senha: 'demo123', telefone: '(11) 90000-0003', perfil: 'cliente', ativo: true },
        { id: 4, nome: 'Super Admin', email: 'super@nexoerp.com', senha: 'demo123', telefone: '', perfil: 'superadmin', ativo: true }
      ],
      produtos: [
        { id: 1, nome: 'Arroz Tipo 1 — 5kg', sku: 'ARZ001', codigoBarras: '7891234567890', cat: 'Alimentos', custo: 20.00, venda: 28.00, estoque: 35, min: 10, status: 'Ativo', lote: { numero: 'L-2026-01', validade: dias(180) } },
        { id: 2, nome: 'Feijão Carioca — 1kg', sku: 'FEJ001', codigoBarras: '7891234567891', cat: 'Alimentos', custo: 6.50, venda: 9.80, estoque: 2, min: 10, status: 'Ativo', lote: { numero: 'L-2026-03', validade: dias(210) } },
        { id: 3, nome: 'Café Torrado — 500g', sku: 'CAF002', codigoBarras: '7891234567892', cat: 'Alimentos', custo: 12.00, venda: 18.90, estoque: 4, min: 8, status: 'Ativo', lote: { numero: 'L-2026-07', validade: dias(20) } },
        { id: 4, nome: 'Açúcar Refinado — 1kg', sku: 'ACU001', codigoBarras: '7891234567893', cat: 'Alimentos', custo: 3.80, venda: 5.50, estoque: 42, min: 15, status: 'Ativo', lote: { numero: 'L-2026-02', validade: dias(400) } },
        { id: 5, nome: 'Refrigerante Cola — 2L', sku: 'BEB001', codigoBarras: '7891234567894', cat: 'Bebidas', custo: 7.20, venda: 10.50, estoque: 48, min: 12, status: 'Ativo', lote: { numero: 'L-2026-04', validade: dias(90) } },
        { id: 6, nome: 'Água Mineral — 1,5L', sku: 'BEB002', codigoBarras: '7891234567895', cat: 'Bebidas', custo: 2.10, venda: 3.50, estoque: 120, min: 30, status: 'Ativo', lote: null },
        { id: 7, nome: 'Suco Integral Uva — 1L', sku: 'BEB003', codigoBarras: '7891234567896', cat: 'Bebidas', custo: 9.90, venda: 14.90, estoque: 0, min: 6, status: 'Ativo', lote: { numero: 'L-2026-05', validade: dias(60) } },
        { id: 8, nome: 'Sabonete Neutro — 90g', sku: 'HIG001', codigoBarras: '7891234567897', cat: 'Higiene', custo: 2.40, venda: 4.20, estoque: 85, min: 20, status: 'Ativo', lote: { numero: 'L-2026-06', validade: dias(540) } },
        { id: 9, nome: 'Shampoo Uso Diário — 350ml', sku: 'HIG002', codigoBarras: '7891234567898', cat: 'Higiene', custo: 8.90, venda: 15.90, estoque: 18, min: 8, status: 'Ativo', lote: { numero: 'L-2026-08', validade: dias(300) } },
        { id: 10, nome: 'Detergente Neutro — 500ml', sku: 'LIM001', codigoBarras: '7891234567899', cat: 'Limpeza', custo: 2.90, venda: 4.80, estoque: 60, min: 15, status: 'Ativo', lote: null },
        { id: 11, nome: 'Sabão em Pó — 800g', sku: 'LIM002', codigoBarras: '7891234567900', cat: 'Limpeza', custo: 11.50, venda: 17.90, estoque: 22, min: 10, status: 'Inativo', lote: null }
      ],
      movimentacoes: [
        { data: '08/09 08:30', produto: 'Arroz Tipo 1 — 5kg', tipo: 'ENTRADA', qtd: 50, motivo: 'Compra', usuario: 'João Silva' },
        { data: '08/09 10:15', produto: 'Arroz Tipo 1 — 5kg', tipo: 'SAÍDA', qtd: 2, motivo: 'Venda #000123', usuario: 'Carlos Almeida' },
        { data: '08/09 11:02', produto: 'Água Mineral — 1,5L', tipo: 'ENTRADA', qtd: 120, motivo: 'Compra', usuario: 'João Silva' },
        { data: '08/09 14:30', produto: 'Café Torrado — 500g', tipo: 'SAÍDA', qtd: 5, motivo: 'Venda #000124', usuario: 'Carlos Almeida' },
        { data: '08/09 15:12', produto: 'Feijão Carioca — 1kg', tipo: 'SAÍDA', qtd: 8, motivo: 'Venda #000125', usuario: 'Carlos Almeida' }
      ],
      vendas: [
        { id: 123, cliente: 'João da Silva', itens: [{ produtoId: 1, nome: 'Arroz Tipo 1 — 5kg', qtd: 2, preco: 28.00 }], pagamento: 'Pix', usuario: 'Carlos Almeida', status: 'Ativa', dataHora: '08/09 10:15' },
        { id: 124, cliente: 'Consumidor final', itens: [{ produtoId: 3, nome: 'Café Torrado — 500g', qtd: 5, preco: 18.90 }], pagamento: 'Cartão de crédito', usuario: 'Carlos Almeida', status: 'Ativa', dataHora: '08/09 14:30' },
        { id: 125, cliente: 'Maria Oliveira', itens: [{ produtoId: 2, nome: 'Feijão Carioca — 1kg', qtd: 8, preco: 9.80 }], pagamento: 'Dinheiro', usuario: 'Carlos Almeida', status: 'Cancelada', dataHora: '08/09 15:12' }
      ],
      pedidos: [],
      auditoria: [
        { data: '08/09 07:58', usuario: 'João Silva', acao: 'LOGIN', detalhe: 'Login no sistema' },
        { data: '08/09 10:15', usuario: 'Carlos Almeida', acao: 'CRIAR_VENDA', detalhe: 'Venda #000123 — R$ 56,00' },
        { data: '08/09 16:40', usuario: 'João Silva', acao: 'ALTERAR_PERMISSAO', detalhe: 'Perfil de Carlos Almeida verificado' }
      ]
    };
  }

  var state = load();
  function load() {
    try {
      var s = localStorage.getItem(STORAGE_KEY);
      if (s) return JSON.parse(s);
    } catch (e) { /* ignora */ }
    var d = defaultState();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(d));
    return d;
  }
  function persist() { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }

  /* ---------- Helpers ---------- */
  function $(sel) { return document.querySelector(sel); }
  function fmt(v) { return 'R$ ' + v.toFixed(2).replace('.', ','); }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function agora() { var d = new Date(); return pad(d.getDate()) + '/' + pad(d.getMonth() + 1) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()); }
  function hojePrefixo() { var d = new Date(); return pad(d.getDate()) + '/' + pad(d.getMonth() + 1); }
  function diasAte(iso) { return Math.ceil((new Date(iso) - new Date()) / 86400000); }
  function findProd(id) {
    for (var i = 0; i < state.produtos.length; i++) if (state.produtos[i].id === id) return state.produtos[i];
    return null;
  }
  function currentUser() {
    for (var i = 0; i < state.users.length; i++) if (state.users[i].id === state.sessionUserId) return state.users[i];
    return null;
  }
  function isStaff() { var u = currentUser(); return u && STAFF.indexOf(u.perfil) > -1; }
  function audit(acao, detalhe) {
    var u = currentUser();
    state.auditoria.push({ data: agora(), usuario: u ? u.nome : 'Sistema', acao: acao, detalhe: detalhe });
  }
  function toast(msg, type) {
    var box = $('#demoToast');
    var el = document.createElement('div');
    el.className = 'toast-msg ' + (type || 'ok');
    el.textContent = msg;
    box.appendChild(el);
    setTimeout(function () { el.classList.add('out'); setTimeout(function () { el.remove(); }, 320); }, 3600);
  }
  function totalVenda(v) {
    return v.itens.reduce(function (a, it) { return a + it.qtd * it.preco; }, 0);
  }

  /* ---------- Login / Sessão ---------- */
  function doLogin(email, senha) {
    var user = null;
    for (var i = 0; i < state.users.length; i++) {
      if (state.users[i].email === email && state.users[i].senha === senha) user = state.users[i];
    }
    var err = $('#loginError');
    if (!user) { err.textContent = 'E-mail ou senha inválidos.'; err.classList.add('show'); return; }
    if (!user.ativo) { err.textContent = 'Usuário inativo. Contate o administrador.'; err.classList.add('show'); return; }
    err.classList.remove('show');
    state.sessionUserId = user.id;
    audit('LOGIN', 'Login no sistema');
    persist();
    enterApp();
    toast('Bem-vindo(a), ' + user.nome.split(' ')[0] + '! Área do ' + ROLE_LABEL[user.perfil] + '.');
  }

  function enterApp() {
    var u = currentUser();
    $('#loginScreen').style.display = 'none';
    $('#appShell').style.display = 'grid';
    $('#userName').textContent = u.nome;
    $('#userRole').textContent = ROLE_LABEL[u.perfil] + (isStaff() ? '' : ' · Loja Nexo');
    $('#userInitials').textContent = u.nome.split(' ').map(function (p) { return p[0]; }).slice(0, 2).join('').toUpperCase();
    $('#vitrineNome').textContent = u.nome.split(' ')[0];
    applyRoleVisibility();
    renderMenu();
    renderAll();
  }

  function applyRoleVisibility() {
    var u = currentUser();
    if (!u) return;
    document.querySelectorAll('[data-roles]').forEach(function (el) {
      var ok = el.getAttribute('data-roles').split(' ').indexOf(u.perfil) > -1;
      el.style.display = ok ? '' : 'none';
    });
  }

  $('#loginForm').addEventListener('submit', function (e) {
    e.preventDefault();
    doLogin($('#loginEmail').value.trim().toLowerCase(), $('#loginSenha').value);
  });
  document.querySelectorAll('.login-chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      $('#loginEmail').value = chip.getAttribute('data-email');
      $('#loginSenha').value = chip.getAttribute('data-senha');
      doLogin(chip.getAttribute('data-email'), chip.getAttribute('data-senha'));
    });
  });
  $('#btnLogout').addEventListener('click', function () {
    audit('LOGOUT', 'Saída do sistema');
    state.sessionUserId = null;
    persist();
    location.reload();
  });
  $('#btnRestore').addEventListener('click', function () {
    if (confirm('Restaurar os dados de exemplo? Suas alterações locais serão apagadas.')) {
      localStorage.removeItem(STORAGE_KEY);
      location.reload();
    }
  });

  /* ---------- Navegação ---------- */
  function renderMenu() {
    var u = currentUser();
    var primeiro = null;
    document.querySelectorAll('.demo-nav-btn').forEach(function (btn) {
      var ok = btn.getAttribute('data-roles').split(' ').indexOf(u.perfil) > -1;
      btn.style.display = ok ? 'flex' : 'none';
      if (ok && !primeiro) primeiro = btn;
    });
    if (primeiro) primeiro.click();
  }

  document.querySelectorAll('.demo-nav-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.demo-nav-btn').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      document.querySelectorAll('.pane').forEach(function (p) { p.classList.remove('active'); });
      var pane = $('#pane-' + btn.getAttribute('data-pane'));
      pane.classList.add('active');
      $('#demoTitle').textContent = btn.getAttribute('data-title');
      $('#demoSubtitle').textContent = btn.getAttribute('data-sub');
      if (btn.getAttribute('data-pane') === 'dashboard') renderDashboardCharts();
      if (btn.getAttribute('data-pane') === 'relatorios') { renderRelatorios(); initTopChart(); }
    });
  });

  /* ---------- Dashboard ---------- */
  var salesChart = null, stockChart = null, topChart = null;

  function renderDashboard() {
    var ativos = state.produtos.filter(function (p) { return p.status === 'Ativo'; }).length;
    var estoqueTotal = state.produtos.reduce(function (a, p) { return a + p.estoque; }, 0);
    var vendasAtivas = state.vendas.filter(function (v) { return v.status === 'Ativa'; });
    var vendasHoje = vendasAtivas.reduce(function (a, v) { return a + totalVenda(v); }, 0);
    var valorEstoque = state.produtos.reduce(function (a, p) { return a + p.estoque * p.custo; }, 0);

    $('#kpiProdutos').textContent = state.produtos.length;
    $('#kpiAtivos').textContent = ativos + ' ativos';
    $('#kpiEstoque').textContent = estoqueTotal.toLocaleString('pt-BR');
    $('#kpiVendas').textContent = fmt(vendasHoje);
    $('#kpiValorEstoque').textContent = fmt(valorEstoque);
    $('#kpiBaixo').textContent = state.produtos.filter(function (p) { return p.status === 'Ativo' && p.estoque > 0 && p.estoque <= p.min; }).length;
    $('#kpiZerado').textContent = state.produtos.filter(function (p) { return p.estoque === 0; }).length;

    /* Alertas de estoque */
    var lowBox = $('#lowStockList');
    lowBox.innerHTML = '';
    var baixos = state.produtos.filter(function (p) { return p.status === 'Ativo' && p.estoque <= p.min; });
    if (!baixos.length) lowBox.innerHTML = '<p style="color:var(--muted);font-size:.85rem;">Nenhum produto abaixo do estoque mínimo.</p>';
    baixos.forEach(function (p) {
      var div = document.createElement('div');
      div.className = 'low-stock-item';
      div.innerHTML = '<div><strong>' + esc(p.nome) + '</strong><small>Mínimo: ' + p.min + ' un.</small></div>' +
        '<span class="badge ' + (p.estoque === 0 ? 'low' : 'warn') + '">' + p.estoque + ' un.</span>';
      lowBox.appendChild(div);
    });

    /* Validade próxima */
    var expBox = $('#expiryList');
    expBox.innerHTML = '';
    var vencendo = state.produtos.filter(function (p) { return p.lote && p.lote.validade && diasAte(p.lote.validade) <= 30; });
    if (!vencendo.length) expBox.innerHTML = '<p style="color:var(--muted);font-size:.85rem;">Nenhum lote vencendo em 30 dias.</p>';
    vencendo.forEach(function (p) {
      var d = diasAte(p.lote.validade);
      var div = document.createElement('div');
      div.className = 'low-stock-item';
      div.innerHTML = '<div><strong>' + esc(p.nome) + '</strong><small>Lote ' + esc(p.lote.numero) + ' · ' + p.lote.validade.split('-').reverse().join('/') + '</small></div>' +
        '<span class="badge ' + (d <= 7 ? 'low' : 'warn') + '">' + (d < 0 ? 'vencido' : d + ' dias') + '</span>';
      expBox.appendChild(div);
    });

    /* Últimas vendas */
    var lastBox = $('#lastSales');
    lastBox.innerHTML = '';
    state.vendas.slice(-5).reverse().forEach(function (v) {
      var tr = document.createElement('tr');
      tr.innerHTML = '<td><strong>#' + v.id + '</strong></td>' +
        '<td>' + esc(v.cliente) + '</td>' +
        '<td>' + esc(v.pagamento) + '</td>' +
        '<td>' + fmt(totalVenda(v)) + '</td>' +
        '<td><span class="badge ' + (v.status === 'Ativa' ? 'ok' : 'low') + '">' + v.status + '</span></td>';
      lastBox.appendChild(tr);
    });
  }

  function renderDashboardCharts() {
    if (typeof Chart === 'undefined') return;
    if (salesChart) salesChart.destroy();
    salesChart = new Chart($('#salesChart'), {
      type: 'line',
      data: {
        labels: ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
        datasets: [{
          label: 'Vendas (R$)',
          data: [1450, 1980, 1230, 2310, 2680, 3120, 2450],
          borderColor: '#2563eb', backgroundColor: 'rgba(37, 99, 235, .10)',
          fill: true, tension: .42, pointRadius: 4, pointBackgroundColor: '#2563eb'
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { grid: { color: '#eef2f9' }, ticks: { callback: function (v) { return 'R$ ' + v; } } },
          x: { grid: { display: false } }
        }
      }
    });

    if (stockChart) stockChart.destroy();
    var porCat = {};
    state.produtos.forEach(function (p) { porCat[p.cat] = (porCat[p.cat] || 0) + p.estoque; });
    stockChart = new Chart($('#stockChart'), {
      type: 'doughnut',
      data: {
        labels: Object.keys(porCat),
        datasets: [{
          data: Object.keys(porCat).map(function (k) { return porCat[k]; }),
          backgroundColor: ['#2563eb', '#0d9488', '#7c3aed', '#f59e0b', '#ef4444'],
          borderWidth: 3, borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '68%',
        plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } } }
      }
    });
  }

  /* ---------- Produtos ---------- */
  function badgeEstoque(p) {
    if (p.status === 'Inativo') return '<span class="badge neutral">Inativo</span>';
    if (p.estoque === 0) return '<span class="badge low">Sem estoque</span>';
    if (p.estoque <= p.min) return '<span class="badge warn">Estoque baixo</span>';
    return '<span class="badge ok">Em dia</span>';
  }

  function renderProdutos(filtro) {
    var u = currentUser();
    var admin = u && STAFF.indexOf(u.perfil) > -1 && u.perfil !== 'funcionario';
    var tbody = $('#produtosBody');
    tbody.innerHTML = '';
    var termo = (filtro || '').toLowerCase();
    state.produtos
      .filter(function (p) {
        return !termo || p.nome.toLowerCase().indexOf(termo) > -1 || p.sku.toLowerCase().indexOf(termo) > -1 ||
          (p.codigoBarras && p.codigoBarras.indexOf(termo) > -1);
      })
      .forEach(function (p) {
        var validade = p.lote ? esc(p.lote.numero) + ' · ' + p.lote.validade.split('-').reverse().join('/') : '—';
        var tr = document.createElement('tr');
        tr.innerHTML =
          '<td><strong>' + esc(p.nome) + '</strong><br><small style="color:var(--muted)">' + p.sku + ' · ' + esc(p.codigoBarras) + '</small></td>' +
          '<td>' + esc(p.cat) + '</td>' +
          (admin ? '<td>' + fmt(p.custo) + '</td>' : '') +
          '<td><strong>' + fmt(p.venda) + '</strong></td>' +
          '<td>' + p.estoque + ' un.</td>' +
          '<td>' + p.min + ' un.</td>' +
          '<td><small>' + validade + '</small></td>' +
          '<td>' + badgeEstoque(p) + '</td>';
        tbody.appendChild(tr);
      });
    if (!tbody.children.length) tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:26px;">Nenhum produto encontrado.</td></tr>';
  }

  $('#searchProduto').addEventListener('input', function (e) { renderProdutos(e.target.value); });

  /* ---------- Movimentações ---------- */
  function renderMovs() {
    var tbody = $('#movsBody');
    tbody.innerHTML = '';
    state.movimentacoes.slice().reverse().forEach(function (m) {
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + m.data + '</td>' +
        '<td><strong>' + esc(m.produto) + '</strong></td>' +
        '<td><span class="' + (m.tipo === 'ENTRADA' ? 'tag-in' : 'tag-out') + '">' + m.tipo + '</span></td>' +
        '<td>' + (m.tipo === 'ENTRADA' ? '+' : '−') + m.qtd + '</td>' +
        '<td>' + esc(m.motivo) + '</td>' +
        '<td>' + esc(m.usuario) + '</td>';
      tbody.appendChild(tr);
    });
  }

  $('#formMov').addEventListener('submit', function (e) {
    e.preventDefault();
    var u = currentUser();
    if (!u || STAFF.indexOf(u.perfil) === -1) { toast('Ajuste manual restrito ao administrador.', 'err'); return; }
    var p = findProd(parseInt($('#movProduto').value, 10));
    var qtd = parseInt($('#movQtd').value, 10);
    var motivo = $('#movMotivo').value;
    if (!p || !qtd || qtd <= 0) { toast('Informe produto e quantidade válidos.', 'err'); return; }
    if (p.status !== 'Ativo') { toast('Produto inativo não pode ser movimentado.', 'err'); return; }

    var saida = /danificado|perda|fornecedor/i.test(motivo);
    var tipo = saida ? 'SAÍDA' : 'ENTRADA';
    if (tipo === 'SAÍDA' && qtd > p.estoque) { toast('Estoque insuficiente para ' + p.nome + ' (disp.: ' + p.estoque + ').', 'err'); return; }

    p.estoque += tipo === 'ENTRADA' ? qtd : -qtd;
    state.movimentacoes.push({ data: agora(), produto: p.nome, tipo: tipo, qtd: qtd, motivo: motivo, usuario: u.nome });
    audit(tipo + '_ESTOQUE', tipo + ' ' + qtd + ' un. de "' + p.nome + '" — ' + motivo);
    $('#movQtd').value = '';
    persist();
    toast(tipo === 'ENTRADA' ? 'Entrada registrada: +' + qtd + ' un. de ' + p.nome : 'Saída registrada: −' + qtd + ' un. de ' + p.nome);
    renderAll();
  });

  /* ---------- Vendas ---------- */
  function renderVendas() {
    var u = currentUser();
    var podeCancelar = u && STAFF.indexOf(u.perfil) > -1;
    var tbody = $('#vendasBody');
    tbody.innerHTML = '';
    state.vendas.slice().reverse().forEach(function (v) {
      var resumo = v.itens.map(function (it) { return it.qtd + 'x ' + it.nome; }).join(', ');
      var acao = '';
      if (v.status === 'Ativa') {
        acao = podeCancelar
          ? '<button class="btn btn-outline btn-sm btn-cancel" data-id="' + v.id + '">Cancelar</button>'
          : '<span class="lock-hint" title="Somente o administrador pode cancelar">🔒 admin</span>';
      } else {
        acao = '<button class="btn btn-outline btn-sm btn-view" data-id="' + v.id + '">Detalhes</button>';
      }
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td><strong>#' + v.id + '</strong></td>' +
        '<td>' + v.dataHora + '</td>' +
        '<td>' + esc(v.cliente) + '</td>' +
        '<td>' + esc(resumo) + '</td>' +
        '<td>' + esc(v.pagamento) + '</td>' +
        '<td><strong>' + fmt(totalVenda(v)) + '</strong></td>' +
        '<td>' + esc(v.usuario) + '</td>' +
        '<td><span class="badge ' + (v.status === 'Ativa' ? 'ok' : 'low') + '">' + v.status + '</span></td>' +
        '<td>' + acao + '</td>';
      tbody.appendChild(tr);
    });
  }

  /* Código de barras */
  $('#vendaBarcode').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); buscarPorBarras(); }
  });
  $('#vendaBarcode').addEventListener('input', function () {
    if (this.value.length >= 8) buscarPorBarras();
  });
  function buscarPorBarras() {
    var cb = $('#vendaBarcode').value.trim();
    if (!cb) return;
    var p = null;
    for (var i = 0; i < state.produtos.length; i++) {
      if (state.produtos[i].codigoBarras === cb) p = state.produtos[i];
    }
    if (p) {
      $('#vendaProduto').value = String(p.id);
      toast('Produto localizado: ' + p.nome);
      $('#vendaQtd').focus();
    } else {
      toast('Código de barras não encontrado: ' + cb, 'err');
    }
    $('#vendaBarcode').value = '';
  }

  $('#formVenda').addEventListener('submit', function (e) {
    e.preventDefault();
    var u = currentUser();
    var p = findProd(parseInt($('#vendaProduto').value, 10));
    var qtd = parseInt($('#vendaQtd').value, 10);
    var pag = $('#vendaPagamento').value;
    var cliente = $('#vendaCliente').value.trim() || 'Consumidor final';

    if (!p || !qtd || qtd <= 0) { toast('Selecione o produto e informe a quantidade.', 'err'); return; }
    if (p.status !== 'Ativo') { toast('Produto inativo não pode ser vendido.', 'err'); return; }
    if (qtd > p.estoque) { toast('Estoque insuficiente: apenas ' + p.estoque + ' un. de ' + p.nome + '.', 'err'); return; }

    p.estoque -= qtd;
    var venda = {
      id: state.proximaVenda++,
      cliente: cliente,
      itens: [{ produtoId: p.id, nome: p.nome, qtd: qtd, preco: p.venda }],
      pagamento: pag,
      usuario: u.nome,
      status: 'Ativa',
      dataHora: agora()
    };
    state.vendas.push(venda);
    state.movimentacoes.push({ data: agora(), produto: p.nome, tipo: 'SAÍDA', qtd: qtd, motivo: 'Venda #' + venda.id, usuario: u.nome });
    audit('CRIAR_VENDA', 'Venda #' + venda.id + ' — ' + fmt(totalVenda(venda)) + ' (' + pag + ')');

    $('#vendaQtd').value = '';
    $('#vendaCliente').value = '';
    persist();
    renderAll();
    mostrarRecibo(venda);
  });

  function mostrarRecibo(v) {
    var linhas = v.itens.map(function (it) {
      return '<div class="r-row"><span>' + it.qtd + 'x ' + esc(it.nome) + '</span><span>' + fmt(it.qtd * it.preco) + '</span></div>';
    }).join('');
    $('#receiptBody').innerHTML =
      '<div class="r-head"><strong>NEXO MERCEARIA</strong>CNPJ 00.000.000/0001-00<br>Cupom não-fiscal · Venda #' + v.id + '</div>' +
      '<div class="r-row"><span>' + v.dataHora + '</span><span>Operador: ' + esc(v.usuario.split(' ')[0]) + '</span></div>' +
      '<div class="r-row"><span>Cliente: ' + esc(v.cliente) + '</span></div>' +
      linhas +
      '<div class="r-total r-row"><span>TOTAL</span><span>' + fmt(totalVenda(v)) + '</span></div>' +
      '<div class="r-row"><span>Pagamento</span><span>' + esc(v.pagamento) + '</span></div>' +
      '<div class="r-foot">Estoque atualizado automaticamente.<br>Obrigado pela preferência!</div>';
    $('#receiptModal').classList.add('open');
  }
  $('#receiptClose').addEventListener('click', function () { $('#receiptModal').classList.remove('open'); });

  /* ---------- Pedidos ---------- */
  function renderPedidos() {
    var u = currentUser();
    var tbody = $('#pedidosBody');
    tbody.innerHTML = '';
    var lista = state.pedidos.slice().reverse();
    if (u.perfil === 'cliente') lista = lista.filter(function (p) { return p.cliente === u.nome; });

    if (!lista.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:26px;">Nenhum pedido registrado ainda.</td></tr>';
    }

    lista.forEach(function (p) {
      var total = p.itens.reduce(function (a, it) { return a + it.qtd * it.preco; }, 0);
      var resumo = p.itens.map(function (it) { return it.qtd + 'x ' + it.nome; }).join(', ');
      var acoes = '';
      if (p.status === 'ABERTO') {
        if (isStaff()) acoes += '<button class="btn btn-primary btn-sm btn-convert" data-id="' + p.id + '">Converter em venda</button> ';
        if (isStaff() || (u.perfil === 'cliente' && p.cliente === u.nome)) {
          acoes += '<button class="btn btn-outline btn-sm btn-cancel-ped" data-id="' + p.id + '">Cancelar</button>';
        }
      } else if (p.vendaId) {
        acoes = '<small style="color:var(--muted)">venda #' + p.vendaId + '</small>';
      }
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td><strong>#' + p.id + '</strong></td>' +
        '<td>' + p.data + '</td>' +
        '<td>' + esc(p.cliente) + '</td>' +
        '<td>' + esc(resumo) + '</td>' +
        '<td><strong>' + fmt(total) + '</strong></td>' +
        '<td><span class="badge ' + (p.status === 'ABERTO' ? 'info' : p.status === 'CONVERTIDO' ? 'ok' : 'low') + '">' + p.status + '</span></td>' +
        '<td>' + acoes + '</td>';
      tbody.appendChild(tr);
    });

    $('#pedidosHint').textContent = u.perfil === 'cliente'
      ? 'Acompanhe seus pedidos enviados à loja'
      : 'Pedidos abertos podem ser convertidos em venda (estoque é validado na conversão)';
  }

  function criarPedido(produtoId, qtd) {
    var u = currentUser();
    var p = findProd(produtoId);
    if (!p) return;
    var pedido = {
      id: state.proximoPedido++,
      data: agora(),
      cliente: u.nome,
      itens: [{ produtoId: p.id, nome: p.nome, qtd: qtd, preco: p.venda }],
      status: 'ABERTO',
      vendaId: null
    };
    state.pedidos.push(pedido);
    audit('CRIAR_PEDIDO', 'Pedido #' + pedido.id + ' de ' + u.nome + ' — ' + qtd + 'x ' + p.nome);
    persist();
    toast('Pedido #' + pedido.id + ' enviado para a loja!');
    renderAll();
  }

  function converterPedido(id) {
    var u = currentUser();
    var pedido = null;
    for (var i = 0; i < state.pedidos.length; i++) if (state.pedidos[i].id === id) pedido = state.pedidos[i];
    if (!pedido || pedido.status !== 'ABERTO') return;

    for (var j = 0; j < pedido.itens.length; j++) {
      var it = pedido.itens[j];
      var p = findProd(it.produtoId);
      if (!p || p.status !== 'Ativo') { toast('Produto "' + it.nome + '" indisponível.', 'err'); return; }
      if (p.estoque < it.qtd) { toast('Estoque insuficiente para "' + p.nome + '" (disp.: ' + p.estoque + ').', 'err'); return; }
    }

    var venda = {
      id: state.proximaVenda++,
      cliente: pedido.cliente,
      itens: pedido.itens.map(function (it) { return { produtoId: it.produtoId, nome: it.nome, qtd: it.qtd, preco: it.preco }; }),
      pagamento: 'A combinar',
      usuario: u.nome,
      status: 'Ativa',
      dataHora: agora()
    };
    pedido.itens.forEach(function (it) {
      var p = findProd(it.produtoId);
      p.estoque -= it.qtd;
      state.movimentacoes.push({ data: agora(), produto: p.nome, tipo: 'SAÍDA', qtd: it.qtd, motivo: 'Venda #' + venda.id + ' (pedido #' + pedido.id + ')', usuario: u.nome });
    });
    state.vendas.push(venda);
    pedido.status = 'CONVERTIDO';
    pedido.vendaId = venda.id;
    audit('CONVERTER_PEDIDO', 'Pedido #' + pedido.id + ' convertido na venda #' + venda.id);
    persist();
    toast('Pedido #' + pedido.id + ' convertido na venda #' + venda.id + ' — estoque baixado.');
    renderAll();
  }

  function cancelarPedido(id) {
    var u = currentUser();
    var pedido = null;
    for (var i = 0; i < state.pedidos.length; i++) if (state.pedidos[i].id === id) pedido = state.pedidos[i];
    if (!pedido || pedido.status !== 'ABERTO') return;
    if (!isStaff() && pedido.cliente !== u.nome) { toast('Você só pode cancelar os seus próprios pedidos.', 'err'); return; }
    pedido.status = 'CANCELADO';
    audit('CANCELAR_PEDIDO', 'Pedido #' + pedido.id + ' cancelado');
    persist();
    toast('Pedido #' + pedido.id + ' cancelado.');
    renderAll();
  }

  /* ---------- Vitrine (cliente) ---------- */
  function renderVitrine() {
    var u = currentUser();
    var grid = $('#vitrineGrid');
    grid.innerHTML = '';
    state.produtos.filter(function (p) { return p.status === 'Ativo'; }).forEach(function (p) {
      var card = document.createElement('div');
      card.className = 'vitrine-card';
      card.innerHTML =
        '<span class="cat">' + esc(p.cat) + '</span>' +
        '<h3>' + esc(p.nome) + '</h3>' +
        '<span class="preco">' + fmt(p.venda) + '</span>' +
        '<span class="est">' + (p.estoque > 0 ? p.estoque + ' un. disponíveis' : 'temporariamente indisponível') + '</span>' +
        '<div class="row">' +
        '<input type="number" min="1" value="1" id="qty-' + p.id + '" ' + (p.estoque === 0 ? 'disabled' : '') + '>' +
        '<button class="btn btn-primary btn-sm btn-pedir" data-id="' + p.id + '" style="flex:1;" ' + (p.estoque === 0 ? 'disabled' : '') + '>Adicionar ao pedido</button>' +
        '</div>';
      grid.appendChild(card);
    });
    var meus = state.pedidos.filter(function (p) { return p.cliente === u.nome; });
    $('#vitrinePedidosCount').textContent = meus.length + (meus.length === 1 ? ' pedido enviado' : ' pedidos enviados');
  }

  /* ---------- Clientes ---------- */
  function renderClientes() {
    var tbody = $('#clientesBody');
    tbody.innerHTML = '';
    state.users.filter(function (u) { return u.perfil === 'cliente'; }).forEach(function (u) {
      var compras = state.vendas.filter(function (v) { return v.status === 'Ativa' && v.cliente === u.nome; });
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td><strong>' + esc(u.nome) + '</strong></td>' +
        '<td>' + esc(u.email) + '</td>' +
        '<td>' + esc(u.telefone || '—') + '</td>' +
        '<td><span class="badge info">Cliente</span></td>' +
        '<td>' + compras.length + ' compra(s)</td>';
      tbody.appendChild(tr);
    });
  }

  /* ---------- Relatórios ---------- */
  function renderRelatorios() {
    var ativas = state.vendas.filter(function (v) { return v.status === 'Ativa'; });
    var fat = ativas.reduce(function (a, v) { return a + totalVenda(v); }, 0);
    $('#relVendasCount').textContent = ativas.length;
    $('#relFaturamento').textContent = fmt(fat);
    $('#relTicket').textContent = fmt(ativas.length ? fat / ativas.length : 0);
    $('#relBaixo').textContent = state.produtos.filter(function (p) { return p.status === 'Ativo' && p.estoque > 0 && p.estoque <= p.min; }).length;
    $('#relMovs').textContent = state.movimentacoes.filter(function (m) { return m.data.indexOf(hojePrefixo()) === 0; }).length;
  }

  function initTopChart() {
    if (typeof Chart === 'undefined') return;
    var agg = {};
    state.vendas.filter(function (v) { return v.status === 'Ativa'; }).forEach(function (v) {
      v.itens.forEach(function (it) { agg[it.nome] = (agg[it.nome] || 0) + it.qtd; });
    });
    var nomes = Object.keys(agg).sort(function (a, b) { return agg[b] - agg[a]; }).slice(0, 6);
    if (topChart) topChart.destroy();
    topChart = new Chart($('#topChart'), {
      type: 'bar',
      data: {
        labels: nomes,
        datasets: [{
          data: nomes.map(function (n) { return agg[n]; }),
          backgroundColor: ['#2563eb', '#0d9488', '#7c3aed', '#f59e0b', '#ef4444', '#64748b'],
          borderRadius: 8
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { grid: { color: '#eef2f9' }, ticks: { stepSize: 1 } }, x: { grid: { display: false } } }
      }
    });
  }

  /* ---------- Auditoria ---------- */
  function renderAuditoria() {
    var tbody = $('#auditoriaBody');
    tbody.innerHTML = '';
    state.auditoria.slice().reverse().slice(0, 120).forEach(function (a) {
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + a.data + '</td>' +
        '<td>' + esc(a.usuario) + '</td>' +
        '<td><span class="badge neutral">' + esc(a.acao) + '</span></td>' +
        '<td>' + esc(a.detalhe) + '</td>';
      tbody.appendChild(tr);
    });
  }

  /* ---------- Usuários / RBAC ---------- */
  function renderUsuarios() {
    var u = currentUser();
    var tbody = $('#usuariosBody');
    tbody.innerHTML = '';
    state.users.forEach(function (user) {
      var opcoes = ['superadmin', 'admin', 'funcionario', 'cliente'].map(function (r) {
        return '<option value="' + r + '"' + (user.perfil === r ? ' selected' : '') + '>' + ROLE_LABEL[r] + '</option>';
      }).join('');
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td><strong>' + esc(user.nome) + '</strong>' + (user.id === u.id ? ' <small style="color:var(--muted)">(você)</small>' : '') + '</td>' +
        '<td>' + esc(user.email) + '</td>' +
        '<td><select class="role-select" data-id="' + user.id + '">' + opcoes + '</select></td>' +
        '<td><input type="checkbox" class="ativo-toggle" data-id="' + user.id + '"' + (user.ativo ? ' checked' : '') + '></td>';
      tbody.appendChild(tr);
    });
  }

  $('#usuariosBody').addEventListener('change', function (e) {
    var u = currentUser();
    if (e.target.classList.contains('role-select')) {
      var id = parseInt(e.target.getAttribute('data-id'), 10);
      var alvo = null;
      for (var i = 0; i < state.users.length; i++) if (state.users[i].id === id) alvo = state.users[i];
      if (!alvo) return;
      if (id === u.id && STAFF.indexOf(e.target.value) === -1) {
        e.target.value = alvo.perfil;
        toast('Você não pode remover o próprio acesso administrativo.', 'err');
        return;
      }
      var antes = alvo.perfil;
      alvo.perfil = e.target.value;
      audit('ALTERAR_PERMISSAO', 'Perfil de ' + alvo.nome + ': ' + ROLE_LABEL[antes] + ' → ' + ROLE_LABEL[alvo.perfil]);
      persist();
      toast('Perfil de ' + alvo.nome + ' atualizado para ' + ROLE_LABEL[alvo.perfil] + '.');
      renderAll();
    }
    if (e.target.classList.contains('ativo-toggle')) {
      var id2 = parseInt(e.target.getAttribute('data-id'), 10);
      var alvo2 = null;
      for (var j = 0; j < state.users.length; j++) if (state.users[j].id === id2) alvo2 = state.users[j];
      if (!alvo2) return;
      if (id2 === u.id && !e.target.checked) {
        e.target.checked = true;
        toast('Você não pode desativar a si mesmo.', 'err');
        return;
      }
      alvo2.ativo = e.target.checked;
      audit(e.target.checked ? 'ATIVAR_USUARIO' : 'DESATIVAR_USUARIO', alvo2.nome + ' (' + alvo2.email + ')');
      persist();
      toast(alvo2.nome + (e.target.checked ? ' reativado.' : ' desativado.'));
    }
  });

  /* ---------- Ações delegadas (cancelar venda / converter pedido / vitrine / detalhes) ---------- */
  document.addEventListener('click', function (e) {
    var u = currentUser();
    if (!u) return;

    var pedir = e.target.closest('.btn-pedir');
    if (pedir) {
      var pid = parseInt(pedir.getAttribute('data-id'), 10);
      var q = parseInt($('#qty-' + pid).value, 10) || 1;
      criarPedido(pid, q);
      return;
    }

    var conv = e.target.closest('.btn-convert');
    if (conv) { converterPedido(parseInt(conv.getAttribute('data-id'), 10)); return; }

    var cancP = e.target.closest('.btn-cancel-ped');
    if (cancP) { cancelarPedido(parseInt(cancP.getAttribute('data-id'), 10)); return; }

    var btn = e.target.closest('.btn-cancel');
    if (btn) {
      if (!isStaff()) { toast('Somente o administrador pode cancelar vendas.', 'err'); return; }
      var id = parseInt(btn.getAttribute('data-id'), 10);
      var v = null;
      for (var i = 0; i < state.vendas.length; i++) if (state.vendas[i].id === id) v = state.vendas[i];
      if (!v) return;
      if (v.status === 'Cancelada') { toast('Venda já está cancelada.', 'err'); return; }
      v.status = 'Cancelada';
      v.itens.forEach(function (it) {
        var p = findProd(it.produtoId);
        if (p) {
          p.estoque += it.qtd;
          state.movimentacoes.push({ data: agora(), produto: p.nome, tipo: 'ENTRADA', qtd: it.qtd, motivo: 'Cancelamento venda #' + id, usuario: u.nome });
        }
      });
      audit('CANCELAR_VENDA', 'Venda #' + id + ' cancelada — itens devolvidos ao estoque');
      persist();
      toast('Venda #' + id + ' cancelada — estoque restaurado.');
      renderAll();
      return;
    }

    var view = e.target.closest('.btn-view');
    if (view) {
      var vid = parseInt(view.getAttribute('data-id'), 10);
      var vv = null;
      for (var k = 0; k < state.vendas.length; k++) if (state.vendas[k].id === vid) vv = state.vendas[k];
      if (!vv) return;
      $('#modalTitle').textContent = 'Venda #' + vid + ' · ' + vv.status;
      $('#modalSub').textContent = vv.cliente + ' · ' + vv.pagamento + ' · operador ' + vv.usuario;
      $('#modalBody').innerHTML =
        '<table class="demo-table"><thead><tr><th>Produto</th><th>Qtd</th><th>Valor</th></tr></thead><tbody>' +
        vv.itens.map(function (it) {
          return '<tr><td>' + esc(it.nome) + '</td><td>' + it.qtd + '</td><td>' + fmt(it.qtd * it.preco) + '</td></tr>';
        }).join('') + '</tbody></table>';
      $('#modalFoot').innerHTML = '<span>Total</span><strong>' + fmt(totalVenda(vv)) + '</strong>';
      $('#demoModal').classList.add('open');
    }
  });

  $('#modalClose').addEventListener('click', function () { $('#demoModal').classList.remove('open'); });
  $('#demoModal').addEventListener('click', function (e) { if (e.target === this) this.classList.remove('open'); });

  /* ---------- Selects dinâmicos ---------- */
  function fillSelects() {
    var opts = state.produtos
      .filter(function (p) { return p.status === 'Ativo'; })
      .map(function (p) { return '<option value="' + p.id + '">' + esc(p.nome) + ' (disp.: ' + p.estoque + ')</option>'; })
      .join('');
    $('#movProduto').innerHTML = opts;
    $('#vendaProduto').innerHTML = opts;
  }

  /* ---------- Refresh global ---------- */
  function renderAll() {
    fillSelects();
    renderDashboard();
    renderProdutos($('#searchProduto').value);
    renderMovs();
    renderVendas();
    renderPedidos();
    renderClientes();
    renderAuditoria();
    renderUsuarios();
    renderVitrine();
    renderRelatorios();
    applyRoleVisibility();
  }

  /* ---------- Boot ---------- */
  if (state.sessionUserId && currentUser() && currentUser().ativo) {
    enterApp();
  } else {
    state.sessionUserId = null;
    $('#loginScreen').style.display = 'grid';
    $('#appShell').style.display = 'none';
  }
})();
