/* ============================================================
   Teclado SVG interativo
   Renderiza um teclado de cravo (uma oitava) e destaca dedos
   sobre teclas conforme o atributo data-keys e data-fingers.

   Marcação no HTML:
   <div class="keyboard-card" data-keys="C,D,E,F,G" data-fingers="1,2,3,4,5">
     <h4>Posição da Primeira Lição</h4>
   </div>

   Notas: C, D, E, F, G, A, B (apenas brancas)
          C#, D#, F#, G#, A# (pretas)
   ============================================================ */

(function () {
  const WHITE_KEYS = ['C', 'D', 'E', 'F', 'G', 'A', 'B'];
  const BLACK_KEYS = { 'C#': 0, 'D#': 1, 'F#': 3, 'G#': 4, 'A#': 5 };

  function createKeyboard(card) {
    const keys = (card.dataset.keys || '').split(',').map(s => s.trim()).filter(Boolean);
    const fingers = (card.dataset.fingers || '').split(',').map(s => s.trim()).filter(Boolean);
    const octaves = parseInt(card.dataset.octaves || '1', 10);
    const startOctave = parseInt(card.dataset.startoctave || '4', 10);

    const whiteW = 36;
    const whiteH = 130;
    const blackW = 22;
    const blackH = 80;
    const totalWhite = WHITE_KEYS.length * octaves;
    const width = totalWhite * whiteW + 4;
    const height = whiteH + 30;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'keyboard-svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('width', Math.min(width, 600));
    svg.setAttribute('height', height);

    // White keys
    for (let oct = 0; oct < octaves; oct++) {
      for (let i = 0; i < WHITE_KEYS.length; i++) {
        const note = WHITE_KEYS[i] + (startOctave + oct);
        const x = (oct * WHITE_KEYS.length + i) * whiteW + 2;
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', 2);
        rect.setAttribute('width', whiteW - 1);
        rect.setAttribute('height', whiteH);
        rect.setAttribute('rx', 2);
        rect.setAttribute('class', 'key-white');
        rect.dataset.note = note;
        svg.appendChild(rect);

        // Note label below
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', x + whiteW / 2);
        label.setAttribute('y', whiteH + 22);
        label.setAttribute('text-anchor', 'middle');
        label.setAttribute('font-size', 10);
        label.setAttribute('fill', 'currentColor');
        label.setAttribute('opacity', 0.5);
        label.textContent = WHITE_KEYS[i];
        svg.appendChild(label);
      }
    }

    // Black keys (in front)
    for (let oct = 0; oct < octaves; oct++) {
      Object.entries(BLACK_KEYS).forEach(([nm, idx]) => {
        const note = nm + (startOctave + oct);
        const x = (oct * WHITE_KEYS.length + idx) * whiteW + whiteW - blackW / 2 + 2;
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', 2);
        rect.setAttribute('width', blackW);
        rect.setAttribute('height', blackH);
        rect.setAttribute('rx', 2);
        rect.setAttribute('class', 'key-black');
        rect.dataset.note = note;
        svg.appendChild(rect);
      });
    }

    // Apply highlighted keys with finger circles
    keys.forEach((noteSpec, idx) => {
      const note = /\d/.test(noteSpec) ? noteSpec : noteSpec + startOctave;
      const target = svg.querySelector(`[data-note="${note}"]`);
      if (!target) return;
      const finger = fingers[idx];

      const cx = parseFloat(target.getAttribute('x')) + parseFloat(target.getAttribute('width')) / 2;
      const isBlack = target.dataset.note && BLACK_KEYS.hasOwnProperty(target.dataset.note.replace(/\d/g, ''));
      const cy = isBlack ? blackH - 16 : whiteH - 18;
      const r = isBlack ? 9 : 13;

      // Circle indicator
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', cx);
      circle.setAttribute('cy', cy);
      circle.setAttribute('r', r);
      circle.setAttribute('class', finger === '1' ? 'finger-circle thumb' : 'finger-circle');
      svg.appendChild(circle);

      if (finger) {
        const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        txt.setAttribute('x', cx);
        txt.setAttribute('y', cy + 4);
        txt.setAttribute('class', finger === '1' ? 'finger-num thumb-num' : 'finger-num');
        txt.textContent = finger;
        svg.appendChild(txt);
      }
    });

    // Insert before legend if any, else append
    const legend = card.querySelector('.keyboard-legend');
    if (legend) card.insertBefore(svg, legend);
    else card.appendChild(svg);

    // Default legend if not present
    if (!legend) {
      const lg = document.createElement('div');
      lg.className = 'keyboard-legend';
      lg.innerHTML = '<span><span class="swatch thumb"></span> Polegar (1)</span>'
        + '<span><span class="swatch regular"></span> Dedos 2-5</span>';
      card.appendChild(lg);
    }
  }

  function init() {
    document.querySelectorAll('.keyboard-card[data-keys]').forEach(createKeyboard);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

/* ============================================================
   TOC sticky — destacar seção visível
   ============================================================ */
(function () {
  const tocLinks = document.querySelectorAll('.toc-sticky a[href^="#"]');
  if (!tocLinks.length) return;

  const sections = Array.from(tocLinks).map(a => {
    const id = a.getAttribute('href').slice(1);
    const el = document.getElementById(id);
    return { link: a, el };
  }).filter(s => s.el);

  function update() {
    const scrollY = window.scrollY + 120;
    let active = null;
    sections.forEach(s => {
      const top = s.el.getBoundingClientRect().top + window.scrollY;
      if (top <= scrollY) active = s;
    });
    sections.forEach(s => s.link.classList.toggle('active', s === active));
  }

  window.addEventListener('scroll', update, { passive: true });
  update();
})();
