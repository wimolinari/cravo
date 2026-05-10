/* ============================================================
   Video Picker — combo (select) que carrega iframe do YouTube inline
   sem abrir nova aba. Click-to-load: o iframe só carrega quando
   o usuário escolhe um vídeo (privacy + performance).

   Marcação:
   <div class="video-picker" data-videos='[
     {"id":"VIDEO_ID","title":"Skip Sempé — Toccata IX","performer":"Skip Sempé","year":"2008","duration":"5:42"},
     ...
   ]'>
     <h5>Sugestões de gravação</h5>
   </div>

   Os atributos data-videos são preenchidos via JS no init das páginas
   ou inline na marcação. JSON ou referência ao window.VIDEOS_DB.
   ============================================================ */

(function () {
  function buildPicker(picker) {
    let videos = [];
    try {
      videos = JSON.parse(picker.dataset.videos || '[]');
    } catch (e) {
      console.warn('Invalid video list', e);
      return;
    }
    if (!videos.length) return;

    const intro = picker.dataset.intro || 'Escolha uma gravação para ouvir aqui mesmo:';

    // Build select
    const select = document.createElement('select');
    select.setAttribute('aria-label', 'Selecione uma gravação');
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = '— escolha uma gravação —';
    select.appendChild(placeholder);

    videos.forEach((v, idx) => {
      const opt = document.createElement('option');
      opt.value = String(idx);
      const parts = [v.performer || '', v.title || ''].filter(Boolean);
      const meta = [v.year, v.duration].filter(Boolean).join(' · ');
      opt.textContent = parts.join(' — ') + (meta ? '  (' + meta + ')' : '');
      select.appendChild(opt);
    });

    // Intro paragraph
    if (!picker.querySelector('.picker-intro')) {
      const p = document.createElement('p');
      p.className = 'picker-intro';
      p.textContent = intro;
      picker.appendChild(p);
    }

    picker.appendChild(select);

    // Close button (initially hidden)
    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'picker-close';
    closeBtn.textContent = '× fechar vídeo';

    // Frame container
    const frame = document.createElement('div');
    frame.className = 'picker-frame';

    const meta = document.createElement('div');
    meta.className = 'picker-meta';

    picker.appendChild(closeBtn);
    picker.appendChild(frame);
    picker.appendChild(meta);

    function load(idx) {
      const v = videos[idx];
      if (!v || !v.id) return;
      // Use youtube-nocookie for privacy
      const src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(v.id) + '?rel=0&modestbranding=1';
      frame.innerHTML = '<iframe src="' + src + '" title="' + (v.title || '') + '" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>';
      frame.classList.add('loaded');
      const watchUrl = 'https://www.youtube.com/watch?v=' + encodeURIComponent(v.id);
      meta.innerHTML = '<strong>' + (v.performer || 'Intérprete') + '</strong>'
        + (v.title ? ' — ' + v.title : '')
        + (v.year ? ' · ' + v.year : '')
        + (v.duration ? ' · ' + v.duration : '')
        + (v.note ? '<br><span style="font-size:0.82rem;color:var(--ink-mute);">' + v.note + '</span>' : '')
        + ' · <a href="' + watchUrl + '" target="_blank" rel="noopener">abrir no YouTube</a>';
      meta.classList.add('loaded');
      closeBtn.classList.add('loaded');
    }

    function unload() {
      frame.innerHTML = '';
      frame.classList.remove('loaded');
      meta.classList.remove('loaded');
      closeBtn.classList.remove('loaded');
      select.value = '';
    }

    select.addEventListener('change', () => {
      const idx = parseInt(select.value, 10);
      if (isNaN(idx)) unload();
      else load(idx);
    });
    closeBtn.addEventListener('click', unload);
  }

  function init() {
    document.querySelectorAll('.video-picker').forEach(buildPicker);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
