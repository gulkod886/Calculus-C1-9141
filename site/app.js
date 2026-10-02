(function () {
  'use strict';

  const BANK = window.BANK || { categories: [], questions: [] };
  const catName = Object.fromEntries(BANK.categories.map(c => [c.id, c.name]));
  const $ = id => document.getElementById(id);

  const EMPTY = () => ({ year: '', type: '', semester: '', moed: '', text: '', cats: new Set(), all: false });
  const state = EMPTY();

  // ------------------------------------------------------------ helpers

  const uniq = arr => [...new Set(arr.filter(Boolean))];
  
  const examLabel = q => q.exam;

  // UI strings; the page language (<html lang>) picks the set.
  const EN = document.documentElement.lang === 'en';
  const T = EN ? {
    question: (part, num, pts) => (part ? `Part ${part} · ` : '') + `Question ${num}` + (pts ? ` (${pts} pts)` : ''),
    catTitle: 'Show all questions in this category',
    hint: n => 'Show hint' + (n > 1 ? ` (${n} hints)` : ''),
    moreHint: (i, n) => `Next hint (${i}/${n})`,
    hintLabel: i => 'Hint' + (i ? ' ' + i : ''),
    officialNote: 'Based on a solution attached to the exam, expanded and checked.',
    showSol: 'Show solution', hideSol: 'Hide solution',
    count: (n, e) => `${n} question${n === 1 ? '' : 's'}<span class="count-of"> from ${e} exam${e === 1 ? '' : 's'}</span>`,
    none: 'No results',
    active: n => n === 1 ? '1 active filter' : `${n} active filters`,
    emptyBank: 'The bank is empty. Run <code>python3 scripts/build.py</code> after adding questions.',
    noMatch: 'No questions match the filter.',
  } : {
    question: (part, num, pts) => (part ? `חלק ${part}' · ` : '') + `שאלה ${num}` + (pts ? ` (${pts} נק')` : ''),
    catTitle: 'הצגת כל השאלות בקטגוריה',
    hint: n => n === 1 ? 'הצגת רמז' : `הצגת רמז (${n} רמזים)`,
    moreHint: (i, n) => `רמז נוסף (${i}/${n})`,
    hintLabel: i => 'רמז' + (i ? ' ' + i : ''),
    officialNote: 'מבוסס על פתרון שצורף לבחינה, בהרחבה ולאחר בדיקה.',
    showSol: 'הצגת פתרון', hideSol: 'הסתרת פתרון',
    count: (n, e) => `${n} שאלות<span class="count-of"> מתוך ${e} בחינות</span>`,
    none: 'אין תוצאות',
    active: n => n === 1 ? 'מסנן פעיל אחד' : `${n} מסננים פעילים`,
    emptyBank: 'המאגר עדיין ריק. הריצו <code>python3 scripts/build.py</code> לאחר הוספת שאלות.',
    noMatch: 'לא נמצאו שאלות התואמות את הסינון.',
  };

  function plainText(htmlStr) {
    const d = document.createElement('div');
    d.innerHTML = htmlStr;
    return d.textContent.toLowerCase();
  }
  const searchIndex = new Map(BANK.questions.map(q => [q.id, plainText(q.question)]));

  function typeset(el) {
    if (window.MathJax && MathJax.typesetPromise) {
      MathJax.typesetPromise([el]).catch(err => console.error(err));
    } else {
      // MathJax not loaded yet: retry once it is.
      document.addEventListener('mathjax-ready', () => typeset(el), { once: true });
    }
  }

  // ------------------------------------------------------------ URL state

  function readHash() {
    const p = new URLSearchParams(location.hash.slice(1));
    state.year = p.get('year') || '';
    state.type = p.get('type') || '';
    state.semester = p.get('semester') || '';
    state.moed = p.get('moed') || '';
    state.text = p.get('q') || '';
    state.cats = new Set((p.get('cat') || '').split(',').filter(c => catName[c]));
    state.all = p.get('all') === '1';
  }

  function writeHash() {
    const p = new URLSearchParams();
    if (state.year) p.set('year', state.year);
    if (state.type) p.set('type', state.type);
    if (state.semester) p.set('semester', state.semester);
    if (state.moed) p.set('moed', state.moed);
    if (state.text) p.set('q', state.text);
    if (state.cats.size) p.set('cat', [...state.cats].join(','));
    if (state.all) p.set('all', '1');
    const h = p.toString();
    history.replaceState(null, '', h ? '#' + h : location.pathname + location.search);
  }

  // ------------------------------------------------------------ filters UI

  function fillSelect(sel, values) {
    for (const v of values) sel.add(new Option(v, v));
  }

  function buildFilters() {
    const qs = BANK.questions;
    const yv = Object.fromEntries(qs.map(q => [q.year, q.yearValue]));
    fillSelect($('f-year'), uniq(qs.map(q => q.year)).sort((a, b) => yv[b] - yv[a]));
    fillSelect($('f-type'), uniq(qs.map(q => q.type)));
    fillSelect($('f-semester'), uniq(qs.map(q => q.semester)).sort());
    const mo = ['א', 'ב', 'ג', 'מיוחד', 'לדוגמה', 'A', 'B', 'C', 'Special', 'Sample'];
    fillSelect($('f-moed'), uniq(qs.map(q => q.moed)).sort((a, b) => mo.indexOf(a) - mo.indexOf(b)));
    if (!uniq(qs.map(q => q.semester)).length) $('f-semester').closest('label').hidden = true;

    const counts = {};
    qs.forEach(q => q.categories.forEach(c => { counts[c] = (counts[c] || 0) + 1; }));
    const box = $('f-cats');
    for (const c of BANK.categories) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'chip';
      b.dataset.cat = c.id;
      b.innerHTML = `${c.name}<span class="n">${counts[c.id] || 0}</span>`;
      b.addEventListener('click', () => toggleCat(c.id));
      box.appendChild(b);
    }

    $('f-year').addEventListener('change', e => { state.year = e.target.value; update(); });
    $('f-type').addEventListener('change', e => { state.type = e.target.value; update(); });
    $('f-semester').addEventListener('change', e => { state.semester = e.target.value; update(); });
    $('f-moed').addEventListener('change', e => { state.moed = e.target.value; update(); });
    $('f-all').addEventListener('change', e => { state.all = e.target.checked; update(); });
    let t;
    $('f-text').addEventListener('input', e => {
      clearTimeout(t);
      t = setTimeout(() => { state.text = e.target.value.trim(); update(); }, 200);
    });
    $('reset').addEventListener('click', () => {
      Object.assign(state, EMPTY());
      update();
    });
    $('close-filters').addEventListener('click', () => {
      $('filters').open = false;
      $('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  function toggleCat(id) {
    state.cats.has(id) ? state.cats.delete(id) : state.cats.add(id);
    update();
  }

  function syncControls() {
    $('f-year').value = state.year;
    $('f-type').value = state.type;
    $('f-semester').value = state.semester;
    $('f-moed').value = state.moed;
    if (document.activeElement !== $('f-text')) $('f-text').value = state.text;
    $('f-all').checked = state.all;
    document.querySelectorAll('#f-cats .chip').forEach(b =>
      b.setAttribute('aria-pressed', state.cats.has(b.dataset.cat)));
  }

  // ------------------------------------------------------------ filtering

  function matches(q) {
    if (state.year && q.year !== state.year) return false;
    if (state.type && q.type !== state.type) return false;
    if (state.semester && q.semester !== state.semester) return false;
    if (state.moed && q.moed !== state.moed) return false;
    if (state.cats.size) {
      const has = c => q.categories.includes(c);
      const sel = [...state.cats];
      if (state.all ? !sel.every(has) : !sel.some(has)) return false;
    }
    if (state.text && !searchIndex.get(q.id).includes(state.text.toLowerCase())) return false;
    return true;
  }

  // ------------------------------------------------------------ rendering

  function renderQuestion(q) {
    const node = $('tpl-question').content.firstElementChild.cloneNode(true);
    node.id = 'q-' + q.id.replace(/[^\w-]/g, '_');
    node.querySelector('.q-num').textContent = T.question(q.part, q.number, q.points);
    node.querySelector('.q-src').textContent = q.src;

    const cats = node.querySelector('.q-cats');
    for (const c of q.categories) {
      const tag = document.createElement('button');
      tag.type = 'button';
      tag.className = 'tag';
      tag.textContent = catName[c] || c;
      tag.title = T.catTitle;
      tag.addEventListener('click', () => {
        Object.assign(state, EMPTY(), { cats: new Set([c]) });
        update();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
      cats.appendChild(tag);
    }

    node.querySelector('.q-body').innerHTML = q.question;

    // Hints: revealed one at a time.
    const hintBtn = node.querySelector('.hint-btn');
    const hintsBox = node.querySelector('.q-hints');
    let shown = 0;
    const setHintLabel = () => {
      hintBtn.hidden = shown >= q.hints.length;
      hintBtn.textContent = shown === 0 ? T.hint(q.hints.length) : T.moreHint(shown + 1, q.hints.length);
    };
    setHintLabel();
    hintBtn.addEventListener('click', () => {
      const div = document.createElement('div');
      div.className = 'hint';
      div.innerHTML = `<b>${T.hintLabel(q.hints.length > 1 ? shown + 1 : 0)}</b>` + q.hints[shown];
      hintsBox.appendChild(div);
      typeset(div);
      shown++;
      setHintLabel();
    });

    // Solution: rendered lazily on first reveal.
    const solBtn = node.querySelector('.sol-btn');
    const sol = node.querySelector('.q-solution');
    let rendered = false;
    solBtn.addEventListener('click', () => {
      if (!rendered) {
        const body = sol.querySelector('.sol-body');
        body.innerHTML = q.solution;
        rendered = true;
        if (q.officialSolution) {
          const note = document.createElement('p');
          note.className = 'sol-note';
          note.textContent = T.officialNote;
          body.prepend(note);
        }
        sol.hidden = false;
        typeset(body);
      } else {
        sol.hidden = !sol.hidden;
      }
      solBtn.textContent = sol.hidden ? T.showSol : T.hideSol;
    });

    return node;
  }

  function render() {
    const list = BANK.questions.filter(matches);
    const box = $('results');
    box.innerHTML = '';

    const exams = new Set(list.map(examLabel));
    $('count').innerHTML = list.length ? T.count(list.length, exams.size) : T.none;
    const nActive = ['year', 'type', 'semester', 'moed', 'text'].filter(k => state[k]).length + state.cats.size;
    $('active').hidden = !nActive;
    $('active').textContent = T.active(nActive);

    if (!BANK.questions.length) {
      box.innerHTML = `<p class="empty">${T.emptyBank}</p>`;
      return;
    }
    if (!list.length) {
      box.innerHTML = `<p class="empty">${T.noMatch}</p>`;
      return;
    }

    // Questions are pre-sorted by the build (oldest year first, exams in order within a year);
    // show newest year first, keeping the build order inside each year.
    const groups = new Map();
    for (const q of list) {
      const k = examLabel(q);
      if (!groups.has(k)) groups.set(k, []);
      groups.get(k).push(q);
    }
    const frag = document.createDocumentFragment();
    const ordered = [...groups.values()].map((qs, i) => ({ qs, i }))
      .sort((a, b) => (b.qs[0].yearValue - a.qs[0].yearValue) || (a.i - b.i));
    for (const { qs } of ordered) {
      qs.forEach(q => frag.appendChild(renderQuestion(q)));
    }
    box.appendChild(frag);
    typeset(box);
  }

  function update() {
    writeHash();
    syncControls();
    render();
  }

  // ------------------------------------------------------------ init

  function init() {
    buildFilters();
    readHash();
    syncControls();
    render();
    window.addEventListener('hashchange', () => { readHash(); syncControls(); render(); });
  }

  // MathJax loads with defer before us, but its startup is async.
  const waitMathJax = setInterval(() => {
    if (window.MathJax && MathJax.typesetPromise) {
      clearInterval(waitMathJax);
      document.dispatchEvent(new Event('mathjax-ready'));
    }
  }, 100);

  init();
})();
