(() => {
  const root = document.getElementById('salMarketing');
  if (!root) return;

  const launcher = document.getElementById('salMarketingLauncher');
  const close = document.getElementById('salMarketingClose');
  const tabs = [...root.querySelectorAll('[data-marketing-tab]')];
  const panels = [...root.querySelectorAll('.sal-marketing-content')];
  const smallScreen = window.matchMedia('(max-width: 1199.98px)');

  function setOpen(open) {
    root.classList.toggle('is-expanded', open);
    root.classList.toggle('is-collapsed', !open);
    launcher.setAttribute('aria-expanded', String(open));
    if (open) close.focus(); else launcher.focus();
  }

  // Compact by default on tablets and phones, expanded on desktop.
  if (smallScreen.matches) root.classList.add('is-collapsed');
  launcher.setAttribute('aria-expanded', String(!smallScreen.matches));
  launcher.addEventListener('click', () => setOpen(true));
  close.addEventListener('click', () => setOpen(false));
  root.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !root.classList.contains('is-collapsed')) setOpen(false);
  });

  tabs.forEach(tab => tab.addEventListener('click', () => {
    const selected = tab.dataset.marketingTab;
    tabs.forEach(t => {
      const active = t === tab;
      t.classList.toggle('is-active', active);
      t.setAttribute('aria-selected', String(active));
      t.tabIndex = active ? 0 : -1;
    });
    panels.forEach(panel => { panel.hidden = panel.id !== (selected === 'promotions' ? 'salPromoContent' : 'salNoveltyContent'); });
  }));

  root.querySelectorAll('.sal-marketing-content').forEach(panel => {
    const slides = [...panel.querySelectorAll('.sal-marketing-slide')];
    const counter = panel.querySelector('[data-marketing-count]');
    let current = 0;
    function show(index) {
      if (!slides.length) return;
      current = (index + slides.length) % slides.length;
      slides.forEach((slide, i) => { slide.hidden = i !== current; slide.classList.toggle('is-current', i === current); });
      if (counter) counter.textContent = `${current + 1} / ${slides.length}`;
    }
    panel.querySelector('[data-marketing-prev]')?.addEventListener('click', () => show(current - 1));
    panel.querySelector('[data-marketing-next]')?.addEventListener('click', () => show(current + 1));
  });
})();
