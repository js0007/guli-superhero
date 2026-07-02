/* 古力小超人 · 妈妈版带读 — 共用阅读器 */
const BookApp = (() => {
  let bookTitle = '';
  let pages = [];
  let current = 0;
  let audio = null;
  const $ = (id) => document.getElementById(id);

  const SPEAKER_SVG =
    '<svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>';

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function setFullAudioState(state) {
    const btn = $('btnFullAudio');
    const txt = $('btnFullAudioText');
    if (!btn || !txt) return;
    btn.classList.remove('playing', 'error');
    if (state === 'playing') {
      btn.classList.add('playing');
      txt.textContent = '播放中...';
    } else if (state === 'error') {
      btn.classList.add('error');
      txt.textContent = '音频不可用';
    } else {
      txt.textContent = '整页原音';
    }
  }

  function stopAudio() {
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
      audio.onended = null;
      audio = null;
    }
    setFullAudioState('idle');
  }

  function playFull(onEnd) {
    if (audio && !audio.paused) {
      stopAudio();
      return;
    }
    stopAudio();
    audio = new Audio(`audio/Pg-${pages[current].id}.m4a`);
    audio.onended = () => {
      stopAudio();
      if (onEnd) onEnd();
    };
    audio.onerror = () => {
      stopAudio();
      setFullAudioState('error');
    };
    setFullAudioState('playing');
    audio.play().catch(() => {
      stopAudio();
      setFullAudioState('error');
    });
  }

  function speak(text) {
    window.speechSynthesis?.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'en-US';
    u.rate = 0.82;
    window.speechSynthesis?.speak(u);
  }

  function normalize(s) {
    return String(s || '')
      .toLowerCase()
      .replace(/[“”"]/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function buildFlow(page) {
    if (Array.isArray(page.flow) && page.flow.length) return page.flow;
    const extend = page.extendText || [];
    const guides = page.guides || [];
    const guideMap = new Map(guides.map((g) => [normalize(g.en), g]));
    const flow = [];

    extend.forEach((x, i) => {
      const k = normalize(x.en);
      const g = guideMap.get(k);
      flow.push({
        step: g?.step || '',
        sayEn: x.en || '',
        sayZh: x.zh || g?.zh || '',
        coach: g?.action || '',
        next: i < extend.length - 1 ? (extend[i + 1].en || '') : '',
      });
    });

    // 极少数 guide 句子不在 extend 中，兜底补到末尾，但不加“补充”标签
    const existed = new Set(flow.map((f) => normalize(f.sayEn)));
    guides.forEach((g) => {
      const k = normalize(g.en);
      if (!k || existed.has(k)) return;
      flow.push({
        step: g.step || '',
        sayEn: g.en || '',
        sayZh: g.zh || '',
        coach: g.action || '',
        next: '',
      });
    });
    return flow;
  }

  function renderFlow(page) {
    const flow = buildFlow(page);
    const coreCount = 5;
    const list = $('flowList');
    const btn = $('flowMoreBtn');
    let expanded = false;

    function draw() {
      const visible = expanded ? flow : flow.slice(0, coreCount);
      list.innerHTML = visible
        .map(
          (f, i) => `
          <div class="flow-card">
            ${f.step ? `<span class="flow-step">${esc(f.step)}</span>` : ''}
            <div class="flow-say-row">
              <div class="flow-say-en">${esc(f.sayEn || '')}</div>
              <button class="btn-speak" data-idx="${i}" aria-label="朗读">${SPEAKER_SVG}</button>
            </div>
            <div class="flow-say-zh">${esc(f.sayZh || '')}</div>
            ${f.coach ? `<div class="flow-coach">${esc(f.coach)}</div>` : ''}
            ${f.next ? `<div class="flow-next">${esc(f.next)}</div>` : ''}
          </div>`
        )
        .join('');

      list.querySelectorAll('.btn-speak').forEach((sBtn) => {
        sBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          list.querySelectorAll('.btn-speak').forEach((b) => b.classList.remove('playing'));
          sBtn.classList.add('playing');
          const idx = +sBtn.dataset.idx;
          speak(visible[idx].sayEn);
          setTimeout(() => sBtn.classList.remove('playing'), 2000);
        });
      });
      if (btn) {
        const hasMore = flow.length > coreCount;
        btn.hidden = !hasMore;
        if (hasMore) btn.textContent = expanded ? '收起补充句子' : `展开更多句子（+${flow.length - coreCount}）`;
      }
    }

    if (btn) {
      btn.onclick = () => {
        expanded = !expanded;
        draw();
      };
    }
    draw();
  }

  function renderVocab(vocab) {
    $('vocabRow').innerHTML = vocab
      .map(
        (v) => `
        <span class="vocab-pill" data-word="${esc(v.w)}">
          <span class="w">${esc(v.w)}</span><span class="ipa">${esc(v.ipa || '')}</span><span class="cn">${esc(v.cn || '')}</span>
        </span>`
      )
      .join('');
    $('vocabRow').querySelectorAll('.vocab-pill').forEach((el) => {
      el.addEventListener('click', () => speak(el.dataset.word));
    });
  }

  function renderPage(idx) {
    current = idx;
    const p = pages[idx];
    $('topTitle').textContent = `${bookTitle} · Page ${p.id}`;
    $('thumbImg').src = `images/${p.id}.jpg`;
    $('thumbBadge').textContent = `Page ${p.id}`;
    $('spreadBadge').textContent = p.id;
    $('pageNum').textContent = `${idx + 1} / ${pages.length}`;
    $('btnPrev').disabled = idx === 0;
    $('btnNext').disabled = idx === pages.length - 1;
    renderFlow(p);
    renderVocab(p.vocab || []);
    $('scrollBody').scrollTop = 0;
    stopAudio();
  }

  async function init() {
    const app = $('app');
    app?.classList.add('loading');
    try {
      const res = await fetch('content.json');
      if (!res.ok) throw new Error('content.json');
      const data = await res.json();
      bookTitle = data.book || document.title;
      pages = data.pages || [];
      document.title = `${bookTitle} · 妈妈版精读小抄`;
      $('btnFullAudio')?.addEventListener('click', () => playFull());
      $('btnPrev')?.addEventListener('click', () => {
        if (current > 0) renderPage(current - 1);
      });
      $('btnNext')?.addEventListener('click', () => {
        if (current < pages.length - 1) renderPage(current + 1);
      });
      renderPage(0);
    } catch (e) {
      $('topTitle').textContent = '加载失败';
      console.error(e);
    } finally {
      app?.classList.remove('loading');
    }
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', () => BookApp.init());
