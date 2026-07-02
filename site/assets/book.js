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

  function stopAudio() {
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
      audio.onended = null;
      audio = null;
    }
    $('btnFullAudio')?.classList.remove('playing');
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
    audio.play().catch(() => {});
    $('btnFullAudio')?.classList.add('playing');
  }

  function speak(text) {
    window.speechSynthesis?.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'en-US';
    u.rate = 0.82;
    window.speechSynthesis?.speak(u);
  }

  function renderExtendText(lines) {
    $('extendText').innerHTML = lines
      .map(
        (l, i) => `
        <div class="text-line">
          <div class="text-line-row">
            <div class="en">${esc(l.en)}</div>
            <button class="btn-speak" data-idx="${i}" aria-label="朗读">${SPEAKER_SVG}</button>
          </div>
          <div class="zh">${esc(l.zh || '')}</div>
        </div>`
      )
      .join('');

    $('extendText').querySelectorAll('.btn-speak').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        $('extendText').querySelectorAll('.btn-speak').forEach((b) => b.classList.remove('playing'));
        btn.classList.add('playing');
        speak(lines[+btn.dataset.idx].en);
        setTimeout(() => btn.classList.remove('playing'), 2000);
      });
    });
  }

  function renderGuides(guides) {
    $('guideCard').innerHTML = guides
      .map(
        (g, i) => `
        <div class="guide-item">
          <span class="guide-step">${esc(g.step)}</span>
          <div class="guide-action">${esc(g.action)}</div>
          <div class="guide-say-en" data-idx="${i}">${esc(g.en)}</div>
          <div class="guide-say-zh">${esc(g.zh || '')}</div>
          <div class="guide-note">${esc(g.note || '')}</div>
        </div>`
      )
      .join('');

    $('guideCard').querySelectorAll('.guide-say-en').forEach((el) => {
      el.addEventListener('click', () => {
        $('guideCard').querySelectorAll('.guide-say-en').forEach((x) => x.classList.remove('active'));
        el.classList.add('active');
        speak(guides[+el.dataset.idx].en);
      });
    });
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
    renderExtendText(p.extendText || []);
    renderGuides(p.guides || []);
    renderVocab(p.vocab || []);
    $('scrollBody').scrollTop = 0;
    const extendScroll = $('extendScroll');
    if (extendScroll) extendScroll.scrollTop = 0;
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
