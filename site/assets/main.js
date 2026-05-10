/* Theme toggle + persistence */
(function () {
  const KEY = 'cravo-theme';
  const root = document.documentElement;

  function apply(theme) {
    if (theme === 'dark') root.setAttribute('data-theme', 'dark');
    else root.removeAttribute('data-theme');
  }

  function init() {
    let stored = null;
    try { stored = localStorage.getItem(KEY); } catch (e) {}
    if (stored) apply(stored);
    else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      apply('dark');
    }

    document.querySelectorAll('.theme-toggle').forEach(btn => {
      btn.addEventListener('click', () => {
        const isDark = root.getAttribute('data-theme') === 'dark';
        const next = isDark ? 'light' : 'dark';
        apply(next);
        try { localStorage.setItem(KEY, next); } catch (e) {}
        btn.textContent = next === 'dark' ? '☀ Claro' : '☾ Escuro';
      });
      const isDark = root.getAttribute('data-theme') === 'dark';
      btn.textContent = isDark ? '☀ Claro' : '☾ Escuro';
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

/* Search filter for theme/treatise cards */
(function () {
  const input = document.querySelector('[data-search]');
  if (!input) return;
  const targetSelector = input.dataset.search;
  const items = document.querySelectorAll(targetSelector);

  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    items.forEach(item => {
      const txt = item.textContent.toLowerCase();
      item.style.display = (!q || txt.includes(q)) ? '' : 'none';
    });
  });
})();

/* Mobile nav toggle (hamburger) */
(function () {
  function init() {
    const navWrap = document.querySelector('.nav-wrap');
    const navLinks = document.querySelector('.nav-links');
    if (!navWrap || !navLinks) return;
    if (navWrap.querySelector('.nav-toggle')) return;

    const btn = document.createElement('button');
    btn.className = 'nav-toggle';
    btn.type = 'button';
    btn.setAttribute('aria-label', 'Abrir menu');
    btn.setAttribute('aria-expanded', 'false');
    btn.innerHTML = '<span style="font-size:1.1rem;">☰</span> <span style="font-size:0.85rem;">Menu</span>';

    // Insert toggle just before nav-links
    navWrap.insertBefore(btn, navLinks);

    btn.addEventListener('click', () => {
      const open = navLinks.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.firstElementChild.textContent = open ? '✕' : '☰';
    });

    // Close menu when a link is clicked (on mobile)
    navLinks.addEventListener('click', (e) => {
      if (e.target.tagName === 'A' && navLinks.classList.contains('open')) {
        navLinks.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
        btn.firstElementChild.textContent = '☰';
      }
    });

    // Close on resize back to desktop
    window.addEventListener('resize', () => {
      if (window.innerWidth > 900 && navLinks.classList.contains('open')) {
        navLinks.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
        btn.firstElementChild.textContent = '☰';
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
