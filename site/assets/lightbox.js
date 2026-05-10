/* ============================================================
   Lightbox para imagens de partituras — com ZOOM e PAN
   Marcação:
   <figure class="score-figure" data-src="..." data-caption="..." data-source="...">
     <img src="..." alt="...">
     <figcaption>...</figcaption>
   </figure>

   Funcionalidade:
   - Click → abre em tela cheia
   - + / − / 100% / mouse wheel → zoom (50% a 400%)
   - Click-and-drag → pan quando ampliada
   - ← / → ou Esc → navegar/fechar
   - F → fullscreen
   ============================================================ */

(function () {
  let figures = [];
  let current = -1;
  let overlay, imgEl, captionEl, zoom = 1.0;
  let panX = 0, panY = 0, isDragging = false, dragStartX = 0, dragStartY = 0;

  function ensureOverlay() {
    if (overlay) return overlay;
    overlay = document.createElement('div');
    overlay.className = 'lightbox';
    overlay.innerHTML = ''
      + '<button class="lightbox-close" aria-label="Fechar">×</button>'
      + '<button class="lightbox-prev" aria-label="Anterior">‹</button>'
      + '<button class="lightbox-next" aria-label="Próxima">›</button>'
      + '<div class="lightbox-zoom-controls">'
      + '  <button class="lb-zoom-out" aria-label="Diminuir zoom" title="Diminuir (−)">−</button>'
      + '  <button class="lb-zoom-reset" aria-label="100%" title="Reiniciar (0)">100%</button>'
      + '  <button class="lb-zoom-in" aria-label="Aumentar zoom" title="Aumentar (+)">+</button>'
      + '  <button class="lb-fullscreen" aria-label="Tela cheia" title="Tela cheia (F)">⛶</button>'
      + '</div>'
      + '<div class="lightbox-content">'
      + '  <div class="lightbox-img-wrap">'
      + '    <img alt="" draggable="false">'
      + '  </div>'
      + '  <div class="lightbox-caption"></div>'
      + '</div>';
    document.body.appendChild(overlay);

    imgEl = overlay.querySelector('img');
    captionEl = overlay.querySelector('.lightbox-caption');
    const imgWrap = overlay.querySelector('.lightbox-img-wrap');

    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) close();
    });
    overlay.querySelector('.lightbox-close').addEventListener('click', (e) => { e.stopPropagation(); close(); });
    overlay.querySelector('.lightbox-prev').addEventListener('click', (e) => { e.stopPropagation(); navigate(-1); });
    overlay.querySelector('.lightbox-next').addEventListener('click', (e) => { e.stopPropagation(); navigate(1); });

    overlay.querySelector('.lb-zoom-in').addEventListener('click', (e) => { e.stopPropagation(); setZoom(zoom + 0.25); });
    overlay.querySelector('.lb-zoom-out').addEventListener('click', (e) => { e.stopPropagation(); setZoom(zoom - 0.25); });
    overlay.querySelector('.lb-zoom-reset').addEventListener('click', (e) => { e.stopPropagation(); setZoom(1.0); panX = panY = 0; applyTransform(); });
    overlay.querySelector('.lb-fullscreen').addEventListener('click', (e) => {
      e.stopPropagation();
      if (!document.fullscreenElement) overlay.requestFullscreen?.();
      else document.exitFullscreen?.();
    });

    // Wheel zoom centered on cursor
    imgWrap.addEventListener('wheel', (e) => {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.15 : -0.15;
      setZoom(zoom + delta);
    }, { passive: false });

    // Drag-to-pan when zoomed
    imgWrap.addEventListener('mousedown', (e) => {
      if (zoom <= 1.05) return;
      isDragging = true;
      dragStartX = e.clientX - panX;
      dragStartY = e.clientY - panY;
      imgWrap.style.cursor = 'grabbing';
      e.preventDefault();
    });
    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      panX = e.clientX - dragStartX;
      panY = e.clientY - dragStartY;
      applyTransform();
    });
    window.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        imgWrap.style.cursor = zoom > 1.05 ? 'grab' : 'default';
      }
    });

    // Touch pinch-zoom + pan
    let touchStartDist = 0, touchStartZoom = 1.0;
    let touchStartX = 0, touchStartY = 0;
    imgWrap.addEventListener('touchstart', (e) => {
      if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        touchStartDist = Math.hypot(dx, dy);
        touchStartZoom = zoom;
      } else if (e.touches.length === 1 && zoom > 1.05) {
        touchStartX = e.touches[0].clientX - panX;
        touchStartY = e.touches[0].clientY - panY;
      }
    }, { passive: true });
    imgWrap.addEventListener('touchmove', (e) => {
      if (e.touches.length === 2) {
        e.preventDefault();
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const dist = Math.hypot(dx, dy);
        setZoom(touchStartZoom * (dist / touchStartDist));
      } else if (e.touches.length === 1 && zoom > 1.05) {
        e.preventDefault();
        panX = e.touches[0].clientX - touchStartX;
        panY = e.touches[0].clientY - touchStartY;
        applyTransform();
      }
    }, { passive: false });

    // Double-click to toggle 1x ↔ 2x
    imgWrap.addEventListener('dblclick', (e) => {
      e.preventDefault();
      if (zoom > 1.05) { setZoom(1.0); panX = panY = 0; applyTransform(); }
      else setZoom(2.0);
    });

    return overlay;
  }

  function setZoom(z) {
    zoom = Math.max(0.5, Math.min(z, 4.0));
    applyTransform();
    overlay.querySelector('.lb-zoom-reset').textContent = Math.round(zoom * 100) + '%';
    const wrap = overlay.querySelector('.lightbox-img-wrap');
    wrap.style.cursor = zoom > 1.05 ? 'grab' : 'default';
    if (zoom <= 1.05) { panX = panY = 0; applyTransform(); }
  }

  function applyTransform() {
    if (!imgEl) return;
    imgEl.style.transform = 'translate(' + panX + 'px, ' + panY + 'px) scale(' + zoom + ')';
  }

  function show(idx) {
    ensureOverlay();
    current = idx;
    const fig = figures[current];
    const src = fig.dataset.src || fig.querySelector('img')?.src;
    if (!src) return;
    imgEl.src = src;
    imgEl.alt = fig.dataset.caption || '';
    const caption = fig.dataset.caption || fig.querySelector('figcaption')?.textContent || '';
    const source = fig.dataset.source || '';
    captionEl.innerHTML = (source ? '<strong>' + source + '</strong> · ' : '') + caption
      + '<div style="margin-top:0.4rem;font-size:0.78rem;color:rgba(247,241,227,0.6);">'
      + '🖱️ scroll para zoom · arrastar para deslocar · duplo clique para ampliar · ← → para navegar'
      + '</div>';
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
    setZoom(1.0); panX = panY = 0; applyTransform();
  }

  function close() {
    if (!overlay) return;
    overlay.classList.remove('open');
    document.body.style.overflow = '';
    if (document.fullscreenElement) document.exitFullscreen?.();
  }

  function navigate(delta) {
    let next = (current + delta + figures.length) % figures.length;
    show(next);
  }

  function init() {
    figures = Array.from(document.querySelectorAll('.score-figure, .score-inline'));
    figures.forEach((fig, idx) => {
      fig.addEventListener('click', () => show(idx));
      fig.setAttribute('tabindex', '0');
      fig.setAttribute('role', 'button');
      fig.setAttribute('aria-label', 'Ampliar imagem: ' + (fig.dataset.caption || 'partitura'));
      fig.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); show(idx); }
      });
    });

    document.addEventListener('keydown', (e) => {
      if (!overlay || !overlay.classList.contains('open')) return;
      if (e.target.matches('input,textarea,select')) return;
      if (e.key === 'Escape') close();
      else if (e.key === 'ArrowLeft') navigate(-1);
      else if (e.key === 'ArrowRight') navigate(1);
      else if (e.key === '+' || e.key === '=') { setZoom(zoom + 0.25); e.preventDefault(); }
      else if (e.key === '-') { setZoom(zoom - 0.25); e.preventDefault(); }
      else if (e.key === '0') { setZoom(1.0); panX = panY = 0; applyTransform(); e.preventDefault(); }
      else if (e.key.toLowerCase() === 'f') {
        if (!document.fullscreenElement) overlay.requestFullscreen?.();
        else document.exitFullscreen?.();
        e.preventDefault();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
