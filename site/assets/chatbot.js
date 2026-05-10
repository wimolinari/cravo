/* =========================================================================
   Chatbot do Cravo - frontend
   - Mini-renderizador de Markdown (sem lib externa) com suporte a tabelas.
   - Streaming SSE (POST + ReadableStream).
   - Topicos iniciais carregados de /api/topics.
   - Painel redimensionavel: normal (620x820), expandido, tela cheia.
   - Multiplas conversas salvas em localStorage com gerenciador integrado.
   ======================================================================= */

(function () {
  'use strict';

  // --- Config ---------------------------------------------------------------
  const meta = document.querySelector('meta[name="cravo-chat-api"]');
  const API_BASE = (meta && meta.content) || 'http://127.0.0.1:8000';

  const STORE_KEY = 'cravoChatStore';      // { sessions: [...], activeId }
  const LEGACY_KEY = 'cravoChatHistory';   // antiga sessionStorage
  const SIZE_KEY = 'cravoChatSize';
  const MAX_HISTORY = 10;                  // pares user/assistant enviados ao backend
  const MAX_SESSIONS = 30;                 // limite de conversas guardadas

  // --- Estado ---------------------------------------------------------------
  let topics = [];
  let store = { sessions: [], activeId: null };
  let isStreaming = false;

  // --- Storage --------------------------------------------------------------
  function loadStore() {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && Array.isArray(parsed.sessions)) {
          store = parsed;
          return;
        }
      }
    } catch (e) { /* ignore */ }

    // Migração da antiga sessionStorage
    try {
      const legacy = sessionStorage.getItem(LEGACY_KEY);
      if (legacy) {
        const msgs = JSON.parse(legacy);
        if (Array.isArray(msgs) && msgs.length > 0) {
          const session = newSession(msgs);
          store = { sessions: [session], activeId: session.id };
          saveStore();
          sessionStorage.removeItem(LEGACY_KEY);
          return;
        }
      }
    } catch (e) { /* ignore */ }

    store = { sessions: [], activeId: null };
  }

  function saveStore() {
    try {
      // Limita número de sessões — drop mais antigas
      if (store.sessions.length > MAX_SESSIONS) {
        store.sessions.sort(function (a, b) { return b.updatedAt - a.updatedAt; });
        store.sessions = store.sessions.slice(0, MAX_SESSIONS);
      }
      localStorage.setItem(STORE_KEY, JSON.stringify(store));
    } catch (e) {
      console.warn('[cravo-chat] não consegui salvar:', e);
    }
  }

  function newSession(messages) {
    return {
      id: 'c_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      title: '',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messages: messages || [],
    };
  }

  function activeSession() {
    if (!store.activeId) return null;
    return store.sessions.find(function (s) { return s.id === store.activeId; }) || null;
  }

  function ensureActive() {
    let s = activeSession();
    if (!s) {
      s = newSession();
      store.sessions.unshift(s);
      store.activeId = s.id;
      saveStore();
    }
    return s;
  }

  function setActive(id) {
    store.activeId = id;
    saveStore();
  }

  function deleteSession(id) {
    store.sessions = store.sessions.filter(function (s) { return s.id !== id; });
    if (store.activeId === id) store.activeId = null;
    saveStore();
  }

  function deriveTitle(messages) {
    const firstUser = messages.find(function (m) { return m.role === 'user'; });
    if (!firstUser) return 'Nova conversa';
    let t = firstUser.content.replace(/\s+/g, ' ').trim();
    if (t.length > 50) t = t.slice(0, 50) + '…';
    return t;
  }

  function fmtDate(ts) {
    const d = new Date(ts);
    const today = new Date();
    const sameDay = d.toDateString() === today.toDateString();
    if (sameDay) {
      return 'hoje, ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    }
    const yesterday = new Date(today.getTime() - 86400000);
    if (d.toDateString() === yesterday.toDateString()) return 'ontem';
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
  }

  // --- Util: mini-Markdown --------------------------------------------------
  function escapeHtml(s) {
    return s
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Em produção o site fica em /cravo/... mas em dev (localhost:8181) ele é
  // servido a partir de /. O modelo gera sempre URLs com /cravo/. Aqui
  // ajustamos pra funcionar nos dois ambientes.
  function fixSiteHref(href) {
    if (!/^\/cravo\//.test(href)) return href;
    if (window.location.pathname.indexOf('/cravo/') !== -1) return href; // produção
    return href.replace(/^\/cravo\//, '/'); // dev local
  }

  // Imagens (jpg/png/gif/webp/svg) e PDFs sempre abrem em nova aba para que o
  // usuário não perca a conversa. Páginas HTML do site continuam abrindo na
  // mesma aba (navegação natural).
  const IMAGE_OR_FILE_RE = /\.(jpe?g|png|gif|webp|svg|pdf)(\?|#|$)/i;

  function renderInline(s) {
    return s
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (_, t, u) {
        const ext = /^https?:\/\//.test(u);
        const isFile = IMAGE_OR_FILE_RE.test(u);
        const tgt = (ext || isFile) ? ' target="_blank" rel="noopener"' : '';
        const href = ext ? u : fixSiteHref(u);
        return '<a href="' + href + '"' + tgt + '>' + t + '</a>';
      });
  }

  function renderMarkdown(md) {
    const codeSpans = [];
    md = md.replace(/`([^`]+)`/g, function (_, c) {
      codeSpans.push(c);
      return 'CODESPAN' + (codeSpans.length - 1) + '';
    });

    md = escapeHtml(md);

    md = md.replace(/CODESPAN(\d+)/g, function (_, i) {
      return '<code>' + escapeHtml(codeSpans[+i]) + '</code>';
    });

    // Tabelas GFM
    md = md.replace(/(?:^|\n)((?:\|[^\n]+\|\s*\n?){2,})/g, function (match, block) {
      const lines = block.trim().split(/\n/).map(function (l) { return l.trim(); });
      if (lines.length < 2) return match;
      const sep = lines[1];
      if (!/^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$/.test(sep)) return match;

      function splitRow(row) {
        return row.replace(/^\||\|$/g, '').split('|').map(function (c) { return c.trim(); });
      }

      const head = splitRow(lines[0]);
      const body = lines.slice(2).map(splitRow);

      const thead = '<thead><tr>' +
        head.map(function (c) { return '<th>' + renderInline(c) + '</th>'; }).join('') +
        '</tr></thead>';
      const tbody = '<tbody>' +
        body.map(function (row) {
          return '<tr>' + row.map(function (c) {
            return '<td>' + (renderInline(c) || '&nbsp;') + '</td>';
          }).join('') + '</tr>';
        }).join('') +
        '</tbody>';

      return '\n\n<div class="table-wrap"><table>' + thead + tbody + '</table></div>\n\n';
    });

    md = md.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    md = md.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    md = md.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    md = renderInline(md);

    md = md.replace(/(?:^|\n)((?:[-*] .+\n?)+)/g, function (m, block) {
      const items = block.trim().split(/\n/)
        .map(function (l) { return l.replace(/^[-*]\s+/, ''); })
        .map(function (l) { return '<li>' + l + '</li>'; })
        .join('');
      return '\n<ul>' + items + '</ul>';
    });

    md = md.replace(/(?:^|\n)((?:\d+\. .+\n?)+)/g, function (m, block) {
      const items = block.trim().split(/\n/)
        .map(function (l) { return l.replace(/^\d+\.\s+/, ''); })
        .map(function (l) { return '<li>' + l + '</li>'; })
        .join('');
      return '\n<ol>' + items + '</ol>';
    });

    const blocks = md.split(/\n{2,}/).map(function (b) {
      b = b.trim();
      if (!b) return '';
      if (/^<(h\d|ul|ol|li|p|blockquote|pre|div|table)/.test(b)) return b;
      return '<p>' + b.replace(/\n/g, '<br>') + '</p>';
    });

    return blocks.filter(Boolean).join('\n');
  }

  // --- Export PDF -----------------------------------------------------------
  // Abre uma janela com o conteúdo formatado e dispara o print dialog do
  // navegador. O usuário escolhe "Salvar como PDF" no destino. Não precisa
  // de lib externa (jsPDF/pdfmake = ~250KB).
  function exportSessionPdf(session) {
    const title = session.title || deriveTitle(session.messages) || 'Conversa';
    const date = new Date(session.createdAt).toLocaleString('pt-BR');

    const messagesHtml = session.messages.map(function (m) {
      const role = m.role === 'user' ? 'Você' : 'Mestre do Cravo';
      const content = m.role === 'user'
        ? '<p>' + escapeHtml(m.content).replace(/\n/g, '<br>') + '</p>'
        : renderMarkdown(m.content);
      return (
        '<section class="msg ' + m.role + '">' +
          '<h3>' + role + '</h3>' +
          '<div class="content">' + content + '</div>' +
        '</section>'
      );
    }).join('');

    const css = '' +
      '@page { margin: 2cm 1.8cm; }' +
      'html, body { background: #fff; }' +
      'body { font-family: "EB Garamond", Georgia, "Times New Roman", serif; font-size: 11.5pt; line-height: 1.55; color: #2c1810; max-width: 100%; margin: 0; padding: 0; }' +
      'header.doc { border-bottom: 2px solid #b8860b; padding-bottom: 10pt; margin-bottom: 16pt; }' +
      'header.doc h1 { font-family: "Cormorant Garamond", Georgia, serif; font-size: 22pt; color: #6b1d2c; margin: 0 0 4pt 0; font-weight: 600; line-height: 1.15; }' +
      'header.doc .meta { font-size: 10pt; color: #8a7560; font-style: italic; margin: 0; }' +
      'section.msg { margin: 0 0 12pt 0; padding: 8pt 11pt; border-radius: 3px; page-break-inside: avoid; }' +
      'section.msg.user { background: #efe6d2; border-left: 3px solid #d4a73d; }' +
      'section.msg.assistant { background: #fdfaf2; border-left: 3px solid #6b1d2c; }' +
      'section.msg h3 { font-family: "Cormorant Garamond", Georgia, serif; font-size: 10.5pt; color: #6b1d2c; text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 5pt 0; font-weight: 600; }' +
      'section.msg .content p { margin: 0 0 5pt 0; }' +
      'section.msg .content p:last-child { margin-bottom: 0; }' +
      'section.msg .content strong { color: #6b1d2c; }' +
      'section.msg .content em { color: #5b4636; }' +
      'section.msg .content a { color: #6b1d2c; text-decoration: underline; }' +
      'section.msg .content ul, section.msg .content ol { margin: 4pt 0; padding-left: 18pt; }' +
      'section.msg .content li { margin: 2pt 0; }' +
      'section.msg .content h2, section.msg .content h3, section.msg .content h1 { font-family: "Cormorant Garamond", serif; color: #6b1d2c; margin: 6pt 0 3pt 0; font-size: 12pt; border: none; padding: 0; }' +
      'section.msg .content code { font-family: "Courier New", monospace; font-size: 9.5pt; background: #f7f1e3; padding: 1pt 3pt; border-radius: 2px; color: #6b1d2c; }' +
      '.table-wrap { overflow: visible; margin: 6pt 0; border: 1px solid #d4c4a8; border-radius: 3px; }' +
      'table { width: 100%; border-collapse: collapse; font-size: 10pt; page-break-inside: avoid; }' +
      'thead { background: #efe6d2; border-bottom: 1.5pt solid #b8860b; }' +
      'th { font-family: "Cormorant Garamond", serif; font-weight: 600; color: #6b1d2c; text-transform: uppercase; letter-spacing: 0.04em; text-align: left; padding: 5pt 7pt; font-size: 9.5pt; }' +
      'td { padding: 4pt 7pt; border-top: 1px solid #d4c4a8; vertical-align: top; }' +
      'td:first-child { font-weight: 600; color: #5b4636; background: #f7f1e3; font-family: "Cormorant Garamond", serif; }' +
      'footer.doc { margin-top: 18pt; padding-top: 8pt; border-top: 1px solid #d4c4a8; font-size: 9pt; color: #8a7560; font-style: italic; text-align: center; }';

    const html =
      '<!doctype html><html lang="pt-BR"><head>' +
      '<meta charset="utf-8">' +
      '<title>' + escapeHtml(title) + ' · Tratados do Cravo</title>' +
      '<style>' + css + '</style>' +
      '</head><body>' +
        '<header class="doc">' +
          '<h1>' + escapeHtml(title) + '</h1>' +
          '<p class="meta">Conversa com o Mestre do Cravo · ' + escapeHtml(date) + '</p>' +
        '</header>' +
        messagesHtml +
        '<footer class="doc">Tratados do Cravo · UFRJ 2013 · routepesquisa.com.br/cravo</footer>' +
        '<script>window.addEventListener("load",function(){setTimeout(function(){window.print();},400);});<\/script>' +
      '</body></html>';

    const win = window.open('', '_blank', 'width=820,height=900');
    if (!win) {
      alert('Não consegui abrir a janela de impressão. Permita pop-ups deste site para baixar a conversa em PDF.');
      return;
    }
    win.document.open();
    win.document.write(html);
    win.document.close();
  }

  // --- DOM template ---------------------------------------------------------
  function buildUI() {
    const fab = document.createElement('button');
    fab.className = 'cravo-chat-fab';
    fab.setAttribute('aria-label', 'Abrir chat com o Mestre do Cravo');
    fab.title = 'Pergunte ao Mestre do Cravo';
    fab.innerHTML = '<span aria-hidden="true">✦</span><span class="badge-dot" aria-hidden="true"></span>';
    document.body.appendChild(fab);

    const overlay = document.createElement('div');
    overlay.className = 'cravo-chat-overlay';
    overlay.innerHTML =
      '<div class="cravo-chat-panel" role="dialog" aria-label="Chat com o Mestre do Cravo">' +
        '<div class="cravo-chat-header">' +
          '<div class="avatar" aria-hidden="true">C</div>' +
          '<div class="info">' +
            '<h3>Mestre do Cravo</h3>' +
            '<span class="subtitle">guiado pelos 4 tratados (1565-1724)</span>' +
          '</div>' +
          '<div class="btn-group">' +
            '<button class="header-btn history-btn" aria-label="Conversas salvas" title="Conversas salvas">' +
              '<svg viewBox="0 0 16 16" aria-hidden="true">' +
                '<path d="M3 4h10M3 8h10M3 12h10"/>' +
              '</svg>' +
            '</button>' +
            '<button class="header-btn new-btn" aria-label="Nova conversa" title="Nova conversa">' +
              '<svg viewBox="0 0 16 16" aria-hidden="true">' +
                '<path d="M8 3v10M3 8h10"/>' +
              '</svg>' +
            '</button>' +
            '<button class="header-btn expand-btn" aria-label="Expandir chat" title="Expandir">' +
              '<svg viewBox="0 0 16 16" aria-hidden="true">' +
                '<path d="M3 6V3h3M13 6V3h-3M3 10v3h3M13 10v3h-3"/>' +
              '</svg>' +
            '</button>' +
            '<button class="header-btn fullscreen-btn" aria-label="Tela cheia" title="Tela cheia">' +
              '<svg viewBox="0 0 16 16" aria-hidden="true">' +
                '<path d="M2 2h4M2 2v4M14 2h-4M14 2v4M2 14h4M2 14v-4M14 14h-4M14 14v-4"/>' +
              '</svg>' +
            '</button>' +
            '<button class="header-btn close-btn" aria-label="Fechar chat" title="Fechar">×</button>' +
          '</div>' +
        '</div>' +
        '<div class="cravo-chat-drawer" id="cravoChatDrawer" hidden>' +
          '<div class="drawer-header">' +
            '<h4>Suas conversas</h4>' +
            '<button class="drawer-new" type="button">+ Nova conversa</button>' +
          '</div>' +
          '<ul class="drawer-list" id="cravoChatList"></ul>' +
          '<p class="drawer-empty" hidden>Nenhuma conversa salva ainda.</p>' +
        '</div>' +
        '<div class="cravo-chat-body" id="cravoChatBody"></div>' +
        '<div class="cravo-chat-footer">' +
          '<form class="cravo-chat-form" id="cravoChatForm">' +
            '<textarea class="cravo-chat-input" id="cravoChatInput" ' +
              'placeholder="Pergunte sobre dedilhado, ornamentos, Couperin, Rameau..." ' +
              'rows="1"></textarea>' +
            '<button type="submit" class="cravo-chat-send" id="cravoChatSend">Enviar</button>' +
          '</form>' +
          '<p class="cravo-chat-disclaimer">Respostas geradas por IA com base nos 4 tratados (UFRJ 2013).</p>' +
        '</div>' +
      '</div>';
    document.body.appendChild(overlay);

    return {
      fab: fab,
      overlay: overlay,
      panel: overlay.querySelector('.cravo-chat-panel'),
      body: overlay.querySelector('#cravoChatBody'),
      form: overlay.querySelector('#cravoChatForm'),
      input: overlay.querySelector('#cravoChatInput'),
      sendBtn: overlay.querySelector('#cravoChatSend'),
      closeBtn: overlay.querySelector('.close-btn'),
      expandBtn: overlay.querySelector('.expand-btn'),
      fullscreenBtn: overlay.querySelector('.fullscreen-btn'),
      historyBtn: overlay.querySelector('.history-btn'),
      newBtn: overlay.querySelector('.new-btn'),
      drawer: overlay.querySelector('#cravoChatDrawer'),
      list: overlay.querySelector('#cravoChatList'),
      drawerNew: overlay.querySelector('.drawer-new'),
      drawerEmpty: overlay.querySelector('.drawer-empty'),
    };
  }

  // --- Welcome screen -------------------------------------------------------
  function renderWelcome(ui) {
    const wrap = document.createElement('div');
    wrap.className = 'cravo-chat-welcome';

    const lead = document.createElement('p');
    lead.className = 'lead';
    lead.innerHTML =
      '<strong>Olá!</strong> Sou um guia pelos quatro tratados do site (Sancta Maria, Frescobaldi, Couperin e Rameau). Escolha um tópico para começar — ou faça sua pergunta lá embaixo.';
    wrap.appendChild(lead);

    const grid = document.createElement('div');
    grid.className = 'cravo-chat-topics';

    topics.forEach(function (t) {
      const card = document.createElement('button');
      card.className = 'cravo-topic-card';
      card.type = 'button';
      card.innerHTML =
        '<span class="icon" aria-hidden="true">' + t.icon + '</span>' +
        '<span class="label">' + escapeHtml(t.label) + '</span>' +
        '<span class="sample">' + escapeHtml(t.sample_question) + '</span>';
      card.addEventListener('click', function () {
        ui.input.value = t.sample_question;
        sendMessage(ui);
      });
      grid.appendChild(card);
    });
    wrap.appendChild(grid);

    ui.body.innerHTML = '';
    ui.body.appendChild(wrap);
  }

  // --- Mensagens ------------------------------------------------------------
  function renderMessage(role, contentHtml) {
    const msg = document.createElement('div');
    msg.className = 'cravo-msg ' + role;
    msg.innerHTML =
      '<div class="avatar" aria-hidden="true">' + (role === 'user' ? 'V' : 'C') + '</div>' +
      '<div class="bubble">' + contentHtml + '</div>';
    return msg;
  }

  function appendMessage(ui, role, markdown) {
    const welcome = ui.body.querySelector('.cravo-chat-welcome');
    if (welcome) welcome.remove();

    const html = role === 'user' ? '<p>' + escapeHtml(markdown) + '</p>' : renderMarkdown(markdown);
    const node = renderMessage(role, html);
    ui.body.appendChild(node);
    ui.body.scrollTop = ui.body.scrollHeight;
    return node;
  }

  function appendTyping(ui) {
    const welcome = ui.body.querySelector('.cravo-chat-welcome');
    if (welcome) welcome.remove();

    const node = renderMessage(
      'assistant',
      '<span class="cravo-typing"><span></span><span></span><span></span></span>'
    );
    ui.body.appendChild(node);
    ui.body.scrollTop = ui.body.scrollHeight;
    return node;
  }

  function appendError(ui, text) {
    const err = document.createElement('div');
    err.className = 'cravo-chat-error';
    err.textContent = text;
    ui.body.appendChild(err);
    ui.body.scrollTop = ui.body.scrollHeight;
  }

  // --- Drawer (gerenciador de conversas) ------------------------------------
  function renderDrawer(ui) {
    ui.list.innerHTML = '';
    const sessions = store.sessions
      .filter(function (s) { return s.messages.length > 0; })
      .sort(function (a, b) { return b.updatedAt - a.updatedAt; });

    if (sessions.length === 0) {
      ui.drawerEmpty.hidden = false;
      return;
    }
    ui.drawerEmpty.hidden = true;

    sessions.forEach(function (s) {
      const li = document.createElement('li');
      li.className = 'drawer-item' + (s.id === store.activeId ? ' active' : '');
      const title = s.title || deriveTitle(s.messages);
      li.innerHTML =
        '<div class="item-row">' +
          '<button class="item-toggle" type="button" title="Mostrar mensagens" aria-label="Mostrar mensagens" aria-expanded="false">' +
            '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 4l4 4-4 4"/></svg>' +
          '</button>' +
          '<button class="item-load" type="button" title="Carregar conversa">' +
            '<span class="item-title">' + escapeHtml(title) + '</span>' +
            '<span class="item-meta">' + escapeHtml(fmtDate(s.updatedAt)) + ' · ' + s.messages.length + ' msg</span>' +
          '</button>' +
          '<button class="item-action item-export" type="button" title="Baixar como PDF" aria-label="Baixar conversa em PDF">' +
            '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2v9M5 8l3 3 3-3M3 13h10"/></svg>' +
          '</button>' +
          '<button class="item-action item-delete" type="button" title="Excluir conversa" aria-label="Excluir conversa">' +
            '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 5h8M6 5V3h4v2M5 5l1 9h4l1-9M7 7v5M9 7v5"/></svg>' +
          '</button>' +
        '</div>' +
        '<div class="item-preview" hidden></div>';

      const toggleBtn = li.querySelector('.item-toggle');
      const preview = li.querySelector('.item-preview');

      toggleBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        const expanded = li.classList.toggle('expanded');
        toggleBtn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        toggleBtn.title = expanded ? 'Recolher mensagens' : 'Mostrar mensagens';
        preview.hidden = !expanded;
        if (expanded && !preview.dataset.rendered) {
          preview.innerHTML = s.messages.map(function (m) {
            const role = m.role === 'user' ? 'Você' : 'Mestre';
            const html = m.role === 'user'
              ? '<p>' + escapeHtml(m.content) + '</p>'
              : renderMarkdown(m.content);
            return '<div class="prev-msg ' + m.role + '">' +
                     '<span class="prev-role">' + role + '</span>' +
                     '<div class="prev-content">' + html + '</div>' +
                   '</div>';
          }).join('');
          preview.dataset.rendered = '1';
        }
      });

      li.querySelector('.item-load').addEventListener('click', function () {
        if (isStreaming) return;
        loadSession(ui, s.id);
        toggleDrawer(ui, false);
      });
      li.querySelector('.item-export').addEventListener('click', function (e) {
        e.stopPropagation();
        exportSessionPdf(s);
      });
      li.querySelector('.item-delete').addEventListener('click', function (e) {
        e.stopPropagation();
        if (!confirm('Excluir a conversa "' + title + '"?\nEsta ação não pode ser desfeita.')) return;
        const wasActive = s.id === store.activeId;
        deleteSession(s.id);
        renderDrawer(ui);
        if (wasActive) {
          startNewConversation(ui);
        }
      });
      ui.list.appendChild(li);
    });
  }

  function toggleDrawer(ui, force) {
    const open = typeof force === 'boolean' ? force : ui.drawer.hidden;
    if (open) {
      renderDrawer(ui);
      ui.drawer.hidden = false;
      ui.historyBtn.classList.add('active');
      ui.panel.classList.add('drawer-open');
    } else {
      ui.drawer.hidden = true;
      ui.historyBtn.classList.remove('active');
      ui.panel.classList.remove('drawer-open');
    }
  }

  function loadSession(ui, id) {
    setActive(id);
    const s = activeSession();
    ui.body.innerHTML = '';
    if (!s || s.messages.length === 0) {
      renderWelcome(ui);
      return;
    }
    s.messages.forEach(function (m) { appendMessage(ui, m.role, m.content); });
  }

  function startNewConversation(ui) {
    if (isStreaming) return;
    // Se a sessão atual estiver vazia, reaproveita
    const cur = activeSession();
    if (cur && cur.messages.length === 0) {
      ui.body.innerHTML = '';
      renderWelcome(ui);
      return;
    }
    const s = newSession();
    store.sessions.unshift(s);
    store.activeId = s.id;
    saveStore();
    ui.body.innerHTML = '';
    renderWelcome(ui);
  }

  // --- Streaming ------------------------------------------------------------
  async function sendMessage(ui) {
    if (isStreaming) return;
    const text = ui.input.value.trim();
    if (!text) return;

    isStreaming = true;
    ui.sendBtn.disabled = true;
    ui.input.disabled = true;

    const session = ensureActive();
    // Histórico enviado ao backend = últimas N mensagens da sessão atual
    const sentHistory = session.messages.slice(-MAX_HISTORY * 2).map(function (m) {
      return { role: m.role, content: m.content };
    });

    appendMessage(ui, 'user', text);
    session.messages.push({ role: 'user', content: text });
    if (!session.title && session.messages.length > 0) {
      session.title = deriveTitle(session.messages);
    }
    session.updatedAt = Date.now();
    saveStore();

    ui.input.value = '';
    autoresize(ui.input);

    const typing = appendTyping(ui);
    let assistantText = '';
    let assistantNode = null;

    try {
      const resp = await fetch(API_BASE + '/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, history: sentHistory }),
      });

      if (!resp.ok) {
        typing.remove();
        appendError(ui, 'Erro de rede: HTTP ' + resp.status);
        return;
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;
        buffer += decoder.decode(chunk.value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const payload = line.slice(6).trim();
          if (!payload) continue;
          let evt;
          try { evt = JSON.parse(payload); } catch (e) { continue; }

          if (evt.error) {
            typing.remove();
            appendError(ui, evt.message || 'Erro do servidor.');
            return;
          }
          if (evt.text) {
            if (assistantNode === null) {
              typing.remove();
              assistantText = evt.text;
              assistantNode = appendMessage(ui, 'assistant', assistantText);
            } else {
              assistantText += evt.text;
              assistantNode.querySelector('.bubble').innerHTML = renderMarkdown(assistantText);
              ui.body.scrollTop = ui.body.scrollHeight;
            }
          }
        }
      }

      if (assistantText) {
        session.messages.push({ role: 'assistant', content: assistantText });
        session.updatedAt = Date.now();
        saveStore();
      } else {
        typing.remove();
        appendError(ui, 'Resposta vazia. Tente novamente.');
      }
    } catch (e) {
      typing.remove();
      appendError(
        ui,
        'Não consegui falar com o servidor. Verifique se o backend está ativo em ' + API_BASE
      );
      console.error('[cravo-chat]', e);
    } finally {
      isStreaming = false;
      ui.sendBtn.disabled = false;
      ui.input.disabled = false;
      ui.input.focus();
    }
  }

  function autoresize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  }

  // --- Sizing controls ------------------------------------------------------
  function applySize(ui, size) {
    ui.panel.classList.remove('expanded', 'fullscreen');
    if (size === 'expanded') ui.panel.classList.add('expanded');
    if (size === 'fullscreen') ui.panel.classList.add('fullscreen');
    try { localStorage.setItem(SIZE_KEY, size); } catch (e) { /* ignore */ }
    updateSizeButtons(ui, size);
  }

  function updateSizeButtons(ui, size) {
    [ui.expandBtn, ui.fullscreenBtn].forEach(function (b) {
      if (b) b.classList.remove('active');
    });
    if (size === 'expanded' && ui.expandBtn) ui.expandBtn.classList.add('active');
    if (size === 'fullscreen' && ui.fullscreenBtn) ui.fullscreenBtn.classList.add('active');
    if (ui.expandBtn) {
      ui.expandBtn.title = size === 'expanded' ? 'Voltar ao tamanho normal' : 'Expandir';
      ui.expandBtn.setAttribute('aria-label', ui.expandBtn.title);
    }
    if (ui.fullscreenBtn) {
      ui.fullscreenBtn.title = size === 'fullscreen' ? 'Sair da tela cheia' : 'Tela cheia';
      ui.fullscreenBtn.setAttribute('aria-label', ui.fullscreenBtn.title);
    }
  }

  function currentSize(ui) {
    if (ui.panel.classList.contains('fullscreen')) return 'fullscreen';
    if (ui.panel.classList.contains('expanded')) return 'expanded';
    return 'normal';
  }

  // --- Topics fetch ---------------------------------------------------------
  async function loadTopics() {
    try {
      const resp = await fetch(API_BASE + '/api/topics');
      if (resp.ok) topics = await resp.json();
    } catch (e) {
      topics = [
        { icon: '📖', label: 'Os 4 tratados', sample_question: 'Qual a diferença entre Couperin e Rameau?' },
        { icon: '✋', label: 'Postura', sample_question: 'Como me sentar ao cravo?' },
      ];
    }
  }

  // --- Init -----------------------------------------------------------------
  async function init() {
    if (document.querySelector('.cravo-chat-fab')) return;

    const ui = buildUI();

    let savedSize = 'normal';
    try { savedSize = localStorage.getItem(SIZE_KEY) || 'normal'; } catch (e) { /* */ }
    applySize(ui, savedSize);

    loadStore();
    await loadTopics();

    function open() {
      ui.overlay.classList.add('open');
      // Garante que o body do chat tenha a sessão ativa renderizada (para
      // quando o usuário fechar o drawer e voltar para a conversa).
      const s = activeSession();
      if (!s || s.messages.length === 0) {
        if (ui.body.children.length === 0) renderWelcome(ui);
      } else if (ui.body.children.length === 0) {
        s.messages.forEach(function (m) { appendMessage(ui, m.role, m.content); });
      }

      // Comportamento padrão: se já existem conversas anteriores, abre o
      // drawer com a lista (cada item colapsado). O usuário escolhe qual
      // continuar ou clica em "+ Nova". Sem histórico, vai direto pro chat.
      const hasHistory = store.sessions.some(function (x) { return x.messages.length > 0; });
      if (hasHistory) {
        toggleDrawer(ui, true);
      } else {
        toggleDrawer(ui, false);
        setTimeout(function () { ui.input.focus(); }, 100);
      }
    }
    function close() {
      ui.overlay.classList.remove('open');
      toggleDrawer(ui, false);
    }

    ui.fab.addEventListener('click', open);
    ui.closeBtn.addEventListener('click', close);
    ui.overlay.addEventListener('click', function (e) {
      if (e.target === ui.overlay) close();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && ui.overlay.classList.contains('open')) {
        if (!ui.drawer.hidden) toggleDrawer(ui, false);
        else close();
      }
    });

    ui.expandBtn.addEventListener('click', function () {
      const cur = currentSize(ui);
      applySize(ui, cur === 'expanded' ? 'normal' : 'expanded');
    });
    ui.fullscreenBtn.addEventListener('click', function () {
      const cur = currentSize(ui);
      applySize(ui, cur === 'fullscreen' ? 'normal' : 'fullscreen');
    });

    ui.historyBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      toggleDrawer(ui);
    });
    ui.newBtn.addEventListener('click', function () {
      startNewConversation(ui);
      toggleDrawer(ui, false);
    });
    ui.drawerNew.addEventListener('click', function () {
      startNewConversation(ui);
      toggleDrawer(ui, false);
    });
    // Click fora do drawer fecha
    ui.panel.addEventListener('click', function (e) {
      if (ui.drawer.hidden) return;
      if (ui.drawer.contains(e.target)) return;
      if (ui.historyBtn.contains(e.target)) return;
      toggleDrawer(ui, false);
    });

    ui.form.addEventListener('submit', function (e) {
      e.preventDefault();
      sendMessage(ui);
    });
    ui.input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(ui);
      }
    });
    ui.input.addEventListener('input', function () { autoresize(ui.input); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
