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

  // --- i18n -----------------------------------------------------------------
  // Detecta idioma a partir da URL (/cravo/en/..., /cravo/fr/..., /cravo/es/...).
  // Default = pt. Funciona em produção (/cravo/...) e em dev (sem /cravo/).
  function detectLang() {
    const p = window.location.pathname;
    const prod = p.match(/\/cravo\/(en|fr|es)\//i);
    if (prod) return prod[1].toLowerCase();
    const dev = p.match(/^\/(en|fr|es)\//i);
    if (dev) return dev[1].toLowerCase();
    // <html lang="..."> como fallback
    const htmlLang = (document.documentElement.lang || '').toLowerCase().slice(0, 2);
    if (['en', 'fr', 'es'].indexOf(htmlLang) !== -1) return htmlLang;
    return 'pt';
  }
  const LANG = detectLang();

  const I18N = {
    pt: {
      botName: 'Mestre do Cravo',
      botSubtitle: 'guiado pelos 4 tratados (1565-1724)',
      welcomeLead: '<strong>Olá!</strong> Sou um guia pelos quatro tratados do site (Sancta Maria, Frescobaldi, Couperin e Rameau). Escolha um tópico para começar — ou faça sua pergunta lá embaixo.',
      placeholder: 'Pergunte sobre dedilhado, ornamentos, Couperin, Rameau...',
      send: 'Enviar',
      disclaimer: 'Respostas geradas por IA com base nos 4 tratados (UFRJ 2013).',
      yourConversations: 'Suas conversas',
      newConversation: '+ Nova conversa',
      newConversationShort: 'Nova conversa',
      noConversations: 'Nenhuma conversa salva ainda.',
      labelOpenChat: 'Abrir chat com o Mestre do Cravo',
      labelClose: 'Fechar',
      labelExpand: 'Expandir',
      labelCollapse: 'Voltar ao tamanho normal',
      labelFullscreen: 'Tela cheia',
      labelExitFullscreen: 'Sair da tela cheia',
      labelHistoryBtn: 'Conversas salvas',
      labelNewBtn: 'Nova conversa',
      labelToggleShow: 'Mostrar mensagens',
      labelToggleHide: 'Recolher mensagens',
      labelLoad: 'Carregar conversa',
      labelExport: 'Baixar como PDF',
      labelExportAria: 'Baixar conversa em PDF',
      labelDelete: 'Excluir conversa',
      confirmDelete: 'Excluir a conversa "{title}"?\nEsta ação não pode ser desfeita.',
      msgUser: 'Você',
      msgAssistant: 'Mestre do Cravo',
      msgAssistantShort: 'Mestre',
      msgUserAvatar: 'V',
      msgAssistantAvatar: 'C',
      msgCount: 'msg',
      today: 'hoje, ',
      yesterday: 'ontem',
      newConvTitle: 'Nova conversa',
      errorNetwork: 'Erro de rede: HTTP {status}',
      errorEmpty: 'Resposta vazia. Tente novamente.',
      errorBackend: 'Não consegui falar com o servidor. Verifique se o backend está ativo em {api}',
      errorServer: 'Erro do servidor.',
      pdfHeader: 'Conversa com o Mestre do Cravo · {date}',
      pdfFooter: 'Tratados do Cravo · UFRJ 2013 · routepesquisa.com.br/cravo',
      errorPopup: 'Não consegui abrir a janela de impressão. Permita pop-ups deste site para baixar a conversa em PDF.',
    },
    en: {
      botName: 'Harpsichord Master',
      botSubtitle: 'guided by the 4 treatises (1565-1724)',
      welcomeLead: '<strong>Hello!</strong> I am a guide through the four treatises on this site (Sancta Maria, Frescobaldi, Couperin and Rameau). Choose a topic to begin — or ask your question below.',
      placeholder: 'Ask about fingering, ornaments, Couperin, Rameau...',
      send: 'Send',
      disclaimer: 'AI-generated answers based on the 4 treatises (UFRJ 2013).',
      yourConversations: 'Your conversations',
      newConversation: '+ New conversation',
      newConversationShort: 'New conversation',
      noConversations: 'No saved conversations yet.',
      labelOpenChat: 'Open chat with the Harpsichord Master',
      labelClose: 'Close',
      labelExpand: 'Expand',
      labelCollapse: 'Back to normal size',
      labelFullscreen: 'Fullscreen',
      labelExitFullscreen: 'Exit fullscreen',
      labelHistoryBtn: 'Saved conversations',
      labelNewBtn: 'New conversation',
      labelToggleShow: 'Show messages',
      labelToggleHide: 'Hide messages',
      labelLoad: 'Load conversation',
      labelExport: 'Download as PDF',
      labelExportAria: 'Download conversation as PDF',
      labelDelete: 'Delete conversation',
      confirmDelete: 'Delete the conversation "{title}"?\nThis action cannot be undone.',
      msgUser: 'You',
      msgAssistant: 'Harpsichord Master',
      msgAssistantShort: 'Master',
      msgUserAvatar: 'Y',
      msgAssistantAvatar: 'H',
      msgCount: 'msg',
      today: 'today, ',
      yesterday: 'yesterday',
      newConvTitle: 'New conversation',
      errorNetwork: 'Network error: HTTP {status}',
      errorEmpty: 'Empty response. Please try again.',
      errorBackend: 'Could not reach the server. Check that the backend is running at {api}',
      errorServer: 'Server error.',
      pdfHeader: 'Conversation with the Harpsichord Master · {date}',
      pdfFooter: 'Harpsichord Treatises · UFRJ 2013 · routepesquisa.com.br/cravo',
      errorPopup: 'Could not open the print window. Please allow pop-ups for this site to download the conversation as PDF.',
    },
    fr: {
      botName: 'Maître du Clavecin',
      botSubtitle: 'guidé par les 4 traités (1565-1724)',
      welcomeLead: '<strong>Bonjour !</strong> Je suis un guide à travers les quatre traités du site (Sancta Maria, Frescobaldi, Couperin et Rameau). Choisissez un sujet pour commencer — ou posez votre question ci-dessous.',
      placeholder: 'Posez vos questions sur le doigté, les ornements, Couperin, Rameau...',
      send: 'Envoyer',
      disclaimer: 'Réponses générées par IA d\'après les 4 traités (UFRJ 2013).',
      yourConversations: 'Vos conversations',
      newConversation: '+ Nouvelle conversation',
      newConversationShort: 'Nouvelle conversation',
      noConversations: 'Aucune conversation enregistrée pour l\'instant.',
      labelOpenChat: 'Ouvrir le chat avec le Maître du Clavecin',
      labelClose: 'Fermer',
      labelExpand: 'Agrandir',
      labelCollapse: 'Retour à la taille normale',
      labelFullscreen: 'Plein écran',
      labelExitFullscreen: 'Quitter le plein écran',
      labelHistoryBtn: 'Conversations enregistrées',
      labelNewBtn: 'Nouvelle conversation',
      labelToggleShow: 'Afficher les messages',
      labelToggleHide: 'Masquer les messages',
      labelLoad: 'Charger la conversation',
      labelExport: 'Télécharger en PDF',
      labelExportAria: 'Télécharger la conversation en PDF',
      labelDelete: 'Supprimer la conversation',
      confirmDelete: 'Supprimer la conversation « {title} » ?\nCette action est irréversible.',
      msgUser: 'Vous',
      msgAssistant: 'Maître du Clavecin',
      msgAssistantShort: 'Maître',
      msgUserAvatar: 'V',
      msgAssistantAvatar: 'M',
      msgCount: 'msg',
      today: 'aujourd\'hui, ',
      yesterday: 'hier',
      newConvTitle: 'Nouvelle conversation',
      errorNetwork: 'Erreur réseau : HTTP {status}',
      errorEmpty: 'Réponse vide. Veuillez réessayer.',
      errorBackend: 'Impossible de joindre le serveur. Vérifiez que le backend tourne sur {api}',
      errorServer: 'Erreur du serveur.',
      pdfHeader: 'Conversation avec le Maître du Clavecin · {date}',
      pdfFooter: 'Traités du Clavecin · UFRJ 2013 · routepesquisa.com.br/cravo',
      errorPopup: 'Impossible d\'ouvrir la fenêtre d\'impression. Veuillez autoriser les pop-ups sur ce site pour télécharger la conversation en PDF.',
    },
    es: {
      botName: 'Maestro del Clave',
      botSubtitle: 'guiado por los 4 tratados (1565-1724)',
      welcomeLead: '<strong>¡Hola!</strong> Soy un guía a través de los cuatro tratados del sitio (Sancta Maria, Frescobaldi, Couperin y Rameau). Elija un tema para empezar — o haga su pregunta abajo.',
      placeholder: 'Pregunte sobre digitación, ornamentos, Couperin, Rameau...',
      send: 'Enviar',
      disclaimer: 'Respuestas generadas por IA basadas en los 4 tratados (UFRJ 2013).',
      yourConversations: 'Sus conversaciones',
      newConversation: '+ Nueva conversación',
      newConversationShort: 'Nueva conversación',
      noConversations: 'Aún no hay conversaciones guardadas.',
      labelOpenChat: 'Abrir chat con el Maestro del Clave',
      labelClose: 'Cerrar',
      labelExpand: 'Expandir',
      labelCollapse: 'Volver al tamaño normal',
      labelFullscreen: 'Pantalla completa',
      labelExitFullscreen: 'Salir de pantalla completa',
      labelHistoryBtn: 'Conversaciones guardadas',
      labelNewBtn: 'Nueva conversación',
      labelToggleShow: 'Mostrar mensajes',
      labelToggleHide: 'Ocultar mensajes',
      labelLoad: 'Cargar conversación',
      labelExport: 'Descargar como PDF',
      labelExportAria: 'Descargar conversación en PDF',
      labelDelete: 'Eliminar conversación',
      confirmDelete: '¿Eliminar la conversación "{title}"?\nEsta acción no se puede deshacer.',
      msgUser: 'Tú',
      msgAssistant: 'Maestro del Clave',
      msgAssistantShort: 'Maestro',
      msgUserAvatar: 'T',
      msgAssistantAvatar: 'M',
      msgCount: 'msg',
      today: 'hoy, ',
      yesterday: 'ayer',
      newConvTitle: 'Nueva conversación',
      errorNetwork: 'Error de red: HTTP {status}',
      errorEmpty: 'Respuesta vacía. Inténtelo de nuevo.',
      errorBackend: 'No se pudo contactar al servidor. Compruebe que el backend está activo en {api}',
      errorServer: 'Error del servidor.',
      pdfHeader: 'Conversación con el Maestro del Clave · {date}',
      pdfFooter: 'Tratados del Clave · UFRJ 2013 · routepesquisa.com.br/cravo',
      errorPopup: 'No se pudo abrir la ventana de impresión. Permita las ventanas emergentes de este sitio para descargar la conversación en PDF.',
    },
  };

  const T = I18N[LANG] || I18N.pt;
  function tt(key, vars) {
    let s = T[key] || I18N.pt[key] || key;
    if (vars) for (const k in vars) s = s.replace('{' + k + '}', vars[k]);
    return s;
  }

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
    if (!firstUser) return tt('newConvTitle');
    let t = firstUser.content.replace(/\s+/g, ' ').trim();
    if (t.length > 50) t = t.slice(0, 50) + '…';
    return t;
  }

  function fmtDate(ts) {
    const d = new Date(ts);
    const today = new Date();
    const sameDay = d.toDateString() === today.toDateString();
    const dateLocale = { pt: 'pt-BR', en: 'en-US', fr: 'fr-FR', es: 'es-ES' }[LANG] || 'pt-BR';
    if (sameDay) {
      return tt('today') + d.toLocaleTimeString(dateLocale, { hour: '2-digit', minute: '2-digit' });
    }
    const yesterday = new Date(today.getTime() - 86400000);
    if (d.toDateString() === yesterday.toDateString()) return tt('yesterday');
    return d.toLocaleDateString(dateLocale, { day: '2-digit', month: 'short' });
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

  // Em produção o site fica em /cravo/... (IIS aceita /cravo/ ou /CRAVO/, daí o
  // teste case-insensitive). Em dev (localhost:8181) é servido a partir de /.
  // Adicionalmente: se o usuário está numa página em /cravo/{lang}/ (ou /{lang}/
  // em dev), prefixamos o href com o mesmo idioma para preservar contexto.
  function fixSiteHref(href) {
    if (!/^\/cravo\//i.test(href)) return href;
    const pathname = window.location.pathname;
    const inProd = /\/cravo\//i.test(pathname);

    // Detecta idioma do path atual
    const prodLang = pathname.match(/\/cravo\/(en|fr|es)\//i);
    const devLang = !inProd && pathname.match(/^\/(en|fr|es)\//i);
    const langPrefix = prodLang ? prodLang[1].toLowerCase()
                                : (devLang ? devLang[1].toLowerCase() : null);

    if (inProd) {
      const cravoCase = pathname.match(/\/(cravo)\//i)[1];
      let result = href;
      if (cravoCase !== 'cravo') {
        result = result.replace(/^\/cravo\//i, '/' + cravoCase + '/');
      }
      if (langPrefix) {
        // Insere /lang/ logo após /cravo/, mas só se o href ainda não tem
        const langRe = new RegExp('^/' + cravoCase + '/(en|fr|es)/', 'i');
        if (!langRe.test(result)) {
          result = result.replace('/' + cravoCase + '/', '/' + cravoCase + '/' + langPrefix + '/');
        }
      }
      return result;
    }
    // Dev local: strip /cravo/, prefixa /lang/ se aplicável
    let result = href.replace(/^\/cravo\//i, '/');
    if (langPrefix && !/^\/(en|fr|es)\//i.test(result)) {
      result = '/' + langPrefix + result;
    }
    return result;
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
      const role = m.role === 'user' ? tt('msgUser') : tt('msgAssistant');
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
          '<p class="meta">' + escapeHtml(tt('pdfHeader', { date: date })) + '</p>' +
        '</header>' +
        messagesHtml +
        '<footer class="doc">' + escapeHtml(tt('pdfFooter')) + '</footer>' +
        '<script>window.addEventListener("load",function(){setTimeout(function(){window.print();},400);});<\/script>' +
      '</body></html>';

    const win = window.open('', '_blank', 'width=820,height=900');
    if (!win) {
      alert(tt('errorPopup'));
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
    fab.setAttribute('aria-label', tt('labelOpenChat'));
    fab.title = tt('labelOpenChat');
    fab.innerHTML = '<span aria-hidden="true">✦</span><span class="badge-dot" aria-hidden="true"></span>';
    document.body.appendChild(fab);

    const overlay = document.createElement('div');
    overlay.className = 'cravo-chat-overlay';
    overlay.innerHTML =
      '<div class="cravo-chat-panel" role="dialog" aria-label="' + escapeHtml(tt('botName')) + '">' +
        '<div class="cravo-chat-header">' +
          '<div class="avatar" aria-hidden="true">' + escapeHtml(tt('msgAssistantAvatar')) + '</div>' +
          '<div class="info">' +
            '<h3>' + escapeHtml(tt('botName')) + '</h3>' +
            '<span class="subtitle">' + escapeHtml(tt('botSubtitle')) + '</span>' +
          '</div>' +
          '<div class="btn-group">' +
            '<button class="header-btn history-btn" aria-label="' + escapeHtml(tt('labelHistoryBtn')) + '" title="' + escapeHtml(tt('labelHistoryBtn')) + '">' +
              '<svg viewBox="0 0 16 16" aria-hidden="true">' +
                '<path d="M3 4h10M3 8h10M3 12h10"/>' +
              '</svg>' +
            '</button>' +
            '<button class="header-btn new-btn" aria-label="' + escapeHtml(tt('labelNewBtn')) + '" title="' + escapeHtml(tt('labelNewBtn')) + '">' +
              '<svg viewBox="0 0 16 16" aria-hidden="true">' +
                '<path d="M8 3v10M3 8h10"/>' +
              '</svg>' +
            '</button>' +
            '<button class="header-btn expand-btn" aria-label="' + escapeHtml(tt('labelExpand')) + '" title="' + escapeHtml(tt('labelExpand')) + '">' +
              '<svg viewBox="0 0 16 16" aria-hidden="true">' +
                '<path d="M3 6V3h3M13 6V3h-3M3 10v3h3M13 10v3h-3"/>' +
              '</svg>' +
            '</button>' +
            '<button class="header-btn fullscreen-btn" aria-label="' + escapeHtml(tt('labelFullscreen')) + '" title="' + escapeHtml(tt('labelFullscreen')) + '">' +
              '<svg viewBox="0 0 16 16" aria-hidden="true">' +
                '<path d="M2 2h4M2 2v4M14 2h-4M14 2v4M2 14h4M2 14v-4M14 14h-4M14 14v-4"/>' +
              '</svg>' +
            '</button>' +
            '<button class="header-btn close-btn" aria-label="' + escapeHtml(tt('labelClose')) + '" title="' + escapeHtml(tt('labelClose')) + '">×</button>' +
          '</div>' +
        '</div>' +
        '<div class="cravo-chat-drawer" id="cravoChatDrawer" hidden>' +
          '<div class="drawer-header">' +
            '<h4>' + escapeHtml(tt('yourConversations')) + '</h4>' +
            '<button class="drawer-new" type="button">' + escapeHtml(tt('newConversation')) + '</button>' +
          '</div>' +
          '<ul class="drawer-list" id="cravoChatList"></ul>' +
          '<p class="drawer-empty" hidden>' + escapeHtml(tt('noConversations')) + '</p>' +
        '</div>' +
        '<div class="cravo-chat-body" id="cravoChatBody"></div>' +
        '<div class="cravo-chat-footer">' +
          '<form class="cravo-chat-form" id="cravoChatForm">' +
            '<textarea class="cravo-chat-input" id="cravoChatInput" ' +
              'placeholder="' + escapeHtml(tt('placeholder')) + '" ' +
              'rows="1"></textarea>' +
            '<button type="submit" class="cravo-chat-send" id="cravoChatSend">' + escapeHtml(tt('send')) + '</button>' +
          '</form>' +
          '<p class="cravo-chat-disclaimer">' + escapeHtml(tt('disclaimer')) + '</p>' +
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
    lead.innerHTML = tt('welcomeLead');
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
    const avatar = role === 'user' ? tt('msgUserAvatar') : tt('msgAssistantAvatar');
    msg.innerHTML =
      '<div class="avatar" aria-hidden="true">' + escapeHtml(avatar) + '</div>' +
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
          '<button class="item-toggle" type="button" title="' + escapeHtml(tt('labelToggleShow')) + '" aria-label="' + escapeHtml(tt('labelToggleShow')) + '" aria-expanded="false">' +
            '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 4l4 4-4 4"/></svg>' +
          '</button>' +
          '<button class="item-load" type="button" title="' + escapeHtml(tt('labelLoad')) + '">' +
            '<span class="item-title">' + escapeHtml(title) + '</span>' +
            '<span class="item-meta">' + escapeHtml(fmtDate(s.updatedAt)) + ' · ' + s.messages.length + ' ' + escapeHtml(tt('msgCount')) + '</span>' +
          '</button>' +
          '<button class="item-action item-export" type="button" title="' + escapeHtml(tt('labelExport')) + '" aria-label="' + escapeHtml(tt('labelExportAria')) + '">' +
            '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2v9M5 8l3 3 3-3M3 13h10"/></svg>' +
          '</button>' +
          '<button class="item-action item-delete" type="button" title="' + escapeHtml(tt('labelDelete')) + '" aria-label="' + escapeHtml(tt('labelDelete')) + '">' +
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
        toggleBtn.title = expanded ? tt('labelToggleHide') : tt('labelToggleShow');
        preview.hidden = !expanded;
        if (expanded && !preview.dataset.rendered) {
          preview.innerHTML = s.messages.map(function (m) {
            const role = m.role === 'user' ? tt('msgUser') : tt('msgAssistantShort');
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
        if (!confirm(tt('confirmDelete', { title: title }))) return;
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
        body: JSON.stringify({ question: text, history: sentHistory, lang: LANG }),
      });

      if (!resp.ok) {
        typing.remove();
        appendError(ui, tt('errorNetwork', { status: resp.status }));
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
            appendError(ui, evt.message || tt('errorServer'));
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
        appendError(ui, tt('errorEmpty'));
      }
    } catch (e) {
      typing.remove();
      appendError(ui, tt('errorBackend', { api: API_BASE }));
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
      ui.expandBtn.title = size === 'expanded' ? tt('labelCollapse') : tt('labelExpand');
      ui.expandBtn.setAttribute('aria-label', ui.expandBtn.title);
    }
    if (ui.fullscreenBtn) {
      ui.fullscreenBtn.title = size === 'fullscreen' ? tt('labelExitFullscreen') : tt('labelFullscreen');
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
      const resp = await fetch(API_BASE + '/api/topics?lang=' + LANG);
      if (resp.ok) topics = await resp.json();
    } catch (e) {
      // Fallback minimal por idioma
      const fb = {
        pt: [
          { icon: '📖', label: 'Os 4 tratados', sample_question: 'Qual a diferença entre Couperin e Rameau?' },
          { icon: '✋', label: 'Postura', sample_question: 'Como me sentar ao cravo?' },
        ],
        en: [
          { icon: '📖', label: 'The 4 treatises', sample_question: 'What is the difference between Couperin and Rameau?' },
          { icon: '✋', label: 'Posture', sample_question: 'How should I sit at the harpsichord?' },
        ],
        fr: [
          { icon: '📖', label: 'Les 4 traités', sample_question: 'Quelle est la différence entre Couperin et Rameau ?' },
          { icon: '✋', label: 'Posture', sample_question: 'Comment dois-je m\'asseoir au clavecin ?' },
        ],
        es: [
          { icon: '📖', label: 'Los 4 tratados', sample_question: '¿Cuál es la diferencia entre Couperin y Rameau?' },
          { icon: '✋', label: 'Postura', sample_question: '¿Cómo debo sentarme al clave?' },
        ],
      };
      topics = fb[LANG] || fb.pt;
    }
  }

  // --- Init -----------------------------------------------------------------
  // --- Language switcher ----------------------------------------------------
  // Mapeia o pathname atual para a versão equivalente em outro idioma.
  function buildLangUrl(targetLang) {
    const path = window.location.pathname;
    // Detecta /cravo/{lang}/... ou /cravo/... ou /{lang}/... ou /...
    const prodMatch = path.match(/^(\/cravo)\/(en|fr|es)\/(.*)$/i);
    if (prodMatch) {
      const cravoCase = prodMatch[1];
      if (targetLang === 'pt') return cravoCase + '/' + prodMatch[3];
      return cravoCase + '/' + targetLang + '/' + prodMatch[3];
    }
    const prodPt = path.match(/^(\/cravo)\/(.*)$/i);
    if (prodPt) {
      if (targetLang === 'pt') return path;
      return prodPt[1] + '/' + targetLang + '/' + prodPt[2];
    }
    // Dev (sem /cravo/)
    const devMatch = path.match(/^\/(en|fr|es)\/(.*)$/i);
    if (devMatch) {
      if (targetLang === 'pt') return '/' + devMatch[2];
      return '/' + targetLang + '/' + devMatch[2];
    }
    if (targetLang === 'pt') return path;
    return '/' + targetLang + path;
  }

  function addLangSwitcher() {
    if (document.querySelector('.cravo-lang-switcher')) return;
    const nav = document.querySelector('.nav-links');
    const themeBtn = document.querySelector('.theme-toggle');
    if (!nav && !themeBtn) return;

    const langs = [
      { code: 'pt', label: 'PT' },
      { code: 'en', label: 'EN' },
      { code: 'fr', label: 'FR' },
      { code: 'es', label: 'ES' },
    ];

    const wrap = document.createElement('div');
    wrap.className = 'cravo-lang-switcher';
    wrap.setAttribute('role', 'group');
    wrap.setAttribute('aria-label', 'Language / Idioma / Langue / Idioma');
    langs.forEach(function (l) {
      const a = document.createElement('a');
      a.href = buildLangUrl(l.code);
      a.className = 'lang-btn' + (l.code === LANG ? ' active' : '');
      a.textContent = l.label;
      a.title = ({ pt: 'Português', en: 'English', fr: 'Français', es: 'Español' })[l.code];
      a.lang = l.code;
      wrap.appendChild(a);
    });

    // Inserir antes do theme-toggle se existir, senão no fim da nav
    if (themeBtn && themeBtn.parentNode) {
      themeBtn.parentNode.insertBefore(wrap, themeBtn);
    } else if (nav) {
      nav.parentNode.insertBefore(wrap, nav.nextSibling);
    }
  }

  async function init() {
    if (document.querySelector('.cravo-chat-fab')) return;

    addLangSwitcher();

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
