'use strict';
const qs = s => document.querySelector(s);
const all = s => [...document.querySelectorAll(s)];
const diagnosis = [
  {accuracy:'64.91', recall:'94.12%', falseAlarms:18, misses:2, correct:37, matrix:[5,18,2,32]},
  {accuracy:'85.96', recall:'82.35%', falseAlarms:2, misses:6, correct:49, matrix:[21,2,6,28]}
];
function setCondition(index) {
  const d = diagnosis[index];
  all('[data-condition]').forEach(b => b.setAttribute('aria-pressed', String(Number(b.dataset.condition) === index)));
  qs('#accuracy').textContent = d.accuracy;
  qs('#recall').textContent = d.recall;
  qs('#false-alarms').textContent = d.falseAlarms;
  qs('#misses').textContent = d.misses;
  qs('#correct').textContent = d.correct + ' / 57';
  all('[data-cell]').forEach((el,i) => el.textContent = d.matrix[i]);
}
all('[data-condition]').forEach(b => b.addEventListener('click', () => setCondition(Number(b.dataset.condition))));
const modal = qs('#figure-modal');
let lastFocus;
all('[data-zoom]').forEach(button => button.addEventListener('click', () => {
  lastFocus = button;
  const img = button.querySelector('img');
  qs('#expanded-figure').src = img.src;
  qs('#expanded-figure').alt = img.alt;
  qs('#figure-description').textContent = img.alt;
  modal.showModal();
}));
qs('#close-figure').addEventListener('click', () => modal.close());
modal.addEventListener('click', e => {
  if (e.target !== modal) return;
  const r = modal.getBoundingClientRect();
  if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) modal.close();
});
modal.addEventListener('close', () => lastFocus?.focus());
let activeId = 'takeaways';
const sections = all('[data-toc]');
const tocLinks = all('.toc a[href^="#"]');
function reading() {
  const total = document.documentElement.scrollHeight - innerHeight;
  qs('#reading-progress').style.width = (total > 0 ? Math.min(100,scrollY / total * 100) : 0) + '%';
  let active = sections[0];
  const mobile = matchMedia('(max-width:800px)').matches;
  for (const section of sections) {
    if (section.getBoundingClientRect().top <= (mobile ? 165 : 120)) active = section;
  }
  activeId = active?.id || 'takeaways';
  let tocId = activeId;
  const activeLink = tocLinks.find(a => a.hash === '#' + activeId);
  if (!activeLink || (mobile && activeLink.classList.contains('subsection'))) {
    let parent = document.getElementById(activeId).closest('section');
    while (parent && !tocLinks.some(a => (!mobile || !a.classList.contains('subsection')) && a.hash === '#' + parent.id)) {
      parent = parent.parentElement?.closest('section');
    }
    tocId = parent?.id || activeId;
  }
  tocLinks.forEach(a => {
    const selected = a.hash === '#' + tocId;
    const changed = selected && a.getAttribute('aria-current') !== 'location';
    a.classList.toggle('active', selected);
    if (selected) a.setAttribute('aria-current','location');
    else a.removeAttribute('aria-current');
    if (changed) {
      const container = mobile ? qs('.toc nav') : qs('.toc');
      if (mobile) container.scrollLeft = Math.max(0, a.offsetLeft - (container.clientWidth - a.offsetWidth) / 2);
      else {
        const r = a.getBoundingClientRect(), c = container.getBoundingClientRect();
        if (r.top < c.top || r.bottom > c.bottom) container.scrollTop += r.top - c.top - container.clientHeight / 2;
      }
    }
  });
  all('[data-language-link]').forEach(a => {
    const url = new URL(a.getAttribute('href'), location.href);
    url.hash = scrollY < 120 ? '' : activeId;
    a.href = url.href;
  });
}
let scheduled = false;
addEventListener('scroll', () => {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(() => { reading(); scheduled = false; });
}, {passive:true});
addEventListener('resize', reading);
addEventListener('load', reading);
all('details').forEach(d => d.addEventListener('toggle',reading));
reading();
all('video').forEach(v => v.addEventListener('play', () => all('video').filter(x => x !== v).forEach(x => x.pause())));
