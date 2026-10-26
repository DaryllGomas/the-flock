/* The Flock: public page.
   Local files only. Everything from the data files goes into the page with textContent / text nodes,
   never as HTML, and the markdown renderer builds DOM nodes, so nothing in the data can run as code. */
(() => {
  'use strict';

  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const TABS = ['portfolio', 'research', 'changes', 'help'];
  const TITLES = {
    portfolio: 'The Flock · A portfolio for everybody',
    research: 'Research · The Flock',
    changes: 'Changes · The Flock',
    help: 'Help · The Flock',
  };
  const BUCKET_LABEL = { core: 'Core', tilt: 'Tilts', bills: 'T-bills' };
  const BUCKET_CHIP = { core: 'Core', tilt: 'Tilt', bills: 'T-bills' };
  // The only outbound link the page may ever contain.
  const SWARM = /^https:\/\/swarm\.bigpicsolutions\.com(\/[^\s]*)?$/;

  const $ = (id) => document.getElementById(id);

  /* ---------------------------------------------------------------- small helpers */
  function el(tag, cls, text) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function icon(name) {
    const t = $('tpl-' + name);
    return t.content.firstElementChild.cloneNode(true);
  }
  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
    return node;
  }
  function parseISO(s) {
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s || '');
    return m ? { y: +m[1], mo: +m[2], d: +m[3] } : null;
  }
  function fmtDate(s) {
    const p = parseISO(s);
    return p ? `${MONTHS[p.mo - 1]} ${p.d}, ${p.y}` : String(s || '');
  }
  function pct(w) {
    const v = Math.round(w * 1000) / 10;
    return (Number.isInteger(v) ? String(v) : v.toFixed(1)) + '%';
  }
  function money(n) {
    return '$' + Number(n).toLocaleString('en-US');
  }
  function cap(s) {
    return s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s;
  }
  function lowerFirst(s) {
    return /^[A-Z][a-z]/.test(s) ? s.charAt(0).toLowerCase() + s.slice(1) : s;
  }
  function upperFirst(s) {
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
  }
  function firstSentence(t) {
    const m = /^(.+?[.!?])(\s|$)/.exec(t);
    return m ? m[1] : t;
  }
  // One tidy line for the row: the first sentence, cut at its first natural break when it is long.
  // The full text is always in the expanded panel.
  function rowLine(t) {
    const s = firstSentence(t);
    if (s.length <= 70) return s;
    const m = /^(.{25,95}?)(?::|;|\),)\s/.exec(s);
    if (!m) return s;
    return m[1] + (s.charAt(m[1].length) === ')' ? ')' : '') + '.';
  }
  function joinNames(list) {
    if (list.length <= 1) return list.join('');
    return list.slice(0, -1).join(', ') + ' and ' + list[list.length - 1];
  }
  async function getJSON(path) {
    const r = await fetch(path, { cache: 'no-cache' });
    if (!r.ok) throw new Error(path + ' ' + r.status);
    return r.json();
  }
  async function getText(path) {
    const r = await fetch(path, { cache: 'no-cache' });
    if (!r.ok) throw new Error(path + ' ' + r.status);
    return r.text();
  }
  function failed(container, what) {
    const p = el('p', 'loading', `We couldn't load ${what} just now. Please refresh the page.`);
    p.setAttribute('role', 'alert');
    clear(container).append(p);
  }

  /* ---------------------------------------------------------------- tabs (hash routing) */
  const main = $('main');
  function currentTab() {
    const h = location.hash.replace(/^#/, '');
    return TABS.includes(h) ? h : 'portfolio';
  }
  function showTab(initial) {
    const t = currentTab();
    for (const id of TABS) $('tab-' + id).hidden = id !== t;
    document.querySelectorAll('[data-tab]').forEach((a) => {
      if (a.dataset.tab === t) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    document.title = TITLES[t];
    if (!initial) {
      window.scrollTo(0, 0);
      main.focus({ preventScroll: true });
    }
  }
  window.addEventListener('hashchange', () => showTab(false));
  showTab(true);

  /* ---------------------------------------------------------------- portfolio card */
  function bucketOf(h) {
    return h.tier === 'core' ? 'core' : h.tier === 'regime' ? 'bills' : 'tilt';
  }
  function draftLabel(h) {
    const date = fmtDate(h.as_of);
    const m = /^(\w+)\s+(v[\d.]+)/i.exec(h.status || '');
    if (m) return `${cap(m[1])} ${m[2].toLowerCase()} · ${date}`;
    return h.status ? `${h.status} · ${date}` : date;
  }

  function buildRow(h) {
    const b = bucketOf(h);
    const whyFull = (h.why || '').trim();
    const whyShort = (h.line || '').trim() || rowLine(whyFull);
    const research = (h.theses || []).map((t) => String(t).replace(/^Research:\s*/i, '')).join(' · ');

    const li = el('li');
    const d = el('details', 'row');
    const s = el('summary');

    const dot = el('span', 'dot ' + b);
    dot.setAttribute('aria-hidden', 'true');

    const txt = el('div', 'txt');
    const top = el('div', 'top');
    top.append(el('span', 'vh', BUCKET_CHIP[b] + ': '), el('span', 'nm', h.name || h.ticker), el('span', 'tk', h.ticker || ''));
    txt.append(top, el('div', 'why', whyShort));

    s.append(dot, txt, el('span', 'w', pct(h.weight)), icon('chevron'));

    const more = el('div', 'more');
    const chip = el('p');
    const chipEl = el('span', 'chip');
    const chipDot = el('span', 'dot ' + b);
    chipDot.setAttribute('aria-hidden', 'true');
    chipEl.append(chipDot, el('span', null, BUCKET_CHIP[b] + ' · ' + pct(h.weight) + ' of the model'));
    chip.append(chipEl);
    more.append(chip);

    if (whyFull && whyFull !== whyShort) {
      const p = el('p');
      p.append(el('strong', null, 'Why:'), ' ' + whyFull);
      more.append(p);
    }
    const risk = el('p');
    risk.append(
      el('strong', null, 'Risk:'),
      ' ' + ((h.risk || '').trim() || 'It moves with the whole US stock market, up and down.')
    );
    more.append(risk);
    const res = el('p');
    res.append(
      el('strong', null, 'Research:'),
      ' ' + (research || 'The foundation of the model, not a separate research call.')
    );
    more.append(res);

    d.append(s, more);
    li.append(d);
    return li;
  }

  function renderPortfolio(hold, rules) {
    const list = (hold.holdings || []).map((h, i) => ({ h, i }));
    list.sort((a, b) => (b.h.weight - a.h.weight) || (a.i - b.i));
    const rows = list.map((x) => x.h);
    const n = rows.length;

    const sums = { core: 0, tilt: 0, bills: 0 };
    let total = 0;
    for (const h of rows) {
      sums[bucketOf(h)] += h.weight;
      total += h.weight;
    }
    const notional = rules && rules.notional_usd ? rules.notional_usd : 100000;

    $('pf-draft').textContent = draftLabel(hold);
    $('pf-amount').textContent = money(notional);
    $('pf-sub').textContent = `Starting paper model · ${n} holding${n === 1 ? '' : 's'}`;
    $('pf-count').textContent = `All ${n} holdings`;

    const legend = clear($('pf-legend'));
    const bar = clear($('pf-bar'));
    const spoken = [];
    for (const k of ['core', 'tilt', 'bills']) {
      if (sums[k] <= 0 && k !== 'core') continue;
      const li = el('li');
      const dot = el('span', 'dot ' + k);
      dot.setAttribute('aria-hidden', 'true');
      li.append(dot, BUCKET_LABEL[k], el('b', null, pct(sums[k])));
      legend.append(li);

      const seg = el('span', 'seg ' + k, sums[k] >= 0.06 ? pct(sums[k]) : '');
      seg.style.width = (sums[k] / (total || 1)) * 100 + '%';
      seg.title = `${BUCKET_LABEL[k]} ${pct(sums[k])}`;
      bar.append(seg);
      spoken.push(`${BUCKET_LABEL[k]} ${pct(sums[k])}`);
    }
    bar.setAttribute('aria-label', 'Allocation: ' + spoken.join(', '));

    const ul = clear($('pf-rows'));
    for (const h of rows) ul.append(buildRow(h));
    const hint = clear($('pf-hint'));
    hint.append('Tap for the risk and details', icon('chevron-down'));
    $('pf-foot').textContent = `Each percentage is a share of the model, not a recommendation. Weights total ${pct(total)}.`;
  }

  /* ---------------------------------------------------------------- side cards */
  function sortedChanges(ch) {
    return (ch.changes || []).slice().sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')));
  }

  function renderChanged(ch) {
    const items = sortedChanges(ch);
    const body = clear($('changed-body'));
    if (!items.length) {
      $('changed-date').textContent = '';
      body.append(el('p', 'muted small', 'Nothing has changed yet.'));
      return;
    }
    const c = items[0];
    $('changed-date').textContent = fmtDate(c.date);
    const row = el('div', 'change-item');
    const box = el('span', 'icon-box');
    box.setAttribute('aria-hidden', 'true');
    box.append(icon('arrow-up-right'));
    const txt = el('div');
    txt.append(el('h3', null, c.title || ''), el('p', null, c.detail || ''));
    row.append(box, txt);
    body.append(row);
    if (String(c.status || '').toLowerCase() === 'draft') {
      body.append(el('p', 'note', 'Draft only · No paper trades executed or changes logged yet.'));
    }
    if (items.length > 1) {
      const a = el('a', 'more-link');
      a.href = '#changes';
      a.append('All changes', icon('arrow-right'));
      body.append(a);
    }
  }

  function renderTrack(rules) {
    const bench = rules && rules.benchmark ? rules.benchmark : 'VTI';
    const notional = rules && rules.notional_usd ? rules.notional_usd : 100000;
    $('track-lede').textContent = `The Flock compared with the whole US market fund (${bench}).`;
    $('track-sub').textContent = `Both start at ${money(notional)} on the same date.`;
    const ic = icon('arrow-up-right');
    ic.setAttribute('width', '22');
    ic.setAttribute('height', '22');
    clear($('track-icon')).append(ic);
  }

  function outlookDate(w) {
    const re = /\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2})\b/;
    const m = re.exec(w.lead || '') || re.exec(w.detail || '');
    return m ? `Outlook to ${m[1]} ${m[2]}` : `As of ${fmtDate(w.as_of)}`;
  }

  function renderWeek(week, bodyId, dateId, big) {
    const body = clear($(bodyId));
    $(dateId).textContent = big ? `As of ${fmtDate(week.as_of)} · ${outlookDate(week)}` : outlookDate(week);

    body.append(el('p', 'week-title', week.title || ''));
    if (week.lead) body.append(el('p', 'week-lead', week.lead));
    if (week.detail) body.append(el('p', 'week-detail', week.detail));

    const paths = week.paths || [];
    const total = paths.reduce((a, p) => a + (Number(p.p) || 0), 0) || 1;
    const bar = el('div', 'path-bar');
    bar.setAttribute('role', 'img');
    bar.setAttribute('aria-label', 'Three possible paths: ' + paths.map((p) => `${p.name} ${p.p}%`).join(', '));
    paths.forEach((p, i) => {
      const seg = el('span', 'p' + (i % 3), `${p.p}%`);
      seg.style.width = (Number(p.p) / total) * 100 + '%';
      bar.append(seg);
    });
    body.append(bar);

    if (big) {
      const ul = el('ul', 'path-list');
      paths.forEach((p, i) => {
        const li = el('li');
        const sw = el('span', 'sw p' + (i % 3));
        sw.setAttribute('aria-hidden', 'true');
        const t = el('div');
        t.append(el('b', null, p.name), el('span', 'pl', p.plain || ''));
        li.append(sw, t, el('span', 'pp', `${p.p}%`));
        ul.append(li);
      });
      body.append(ul);
    } else {
      const labels = el('div', 'path-labels');
      paths.forEach((p, i) => {
        const d = el('div');
        d.append(el('b', null, p.name), el('span', null, p.plain || ''));
        // first two labels sit under their segments; the last is right-aligned, as in the mockup
        if (i < paths.length - 1) d.style.flex = `${(Number(p.p) / total) * 100} 1 0`;
        else d.style.flex = '1 1 0';
        d.style.minWidth = i === paths.length - 1 ? '6.2rem' : '0';
        labels.append(d);
      });
      body.append(labels);
    }

    const foot = el('div', 'week-foot');
    foot.append(el('p', 'muted tiny', week.footnote || ''));
    if (!big) {
      const a = el('a', 'more-link');
      a.href = '#research';
      a.append('Read the research', icon('arrow-right'));
      foot.append(a);
    }
    body.append(foot);
  }

  function renderAvoid(hold) {
    const ul = clear($('avoid-list'));
    const nh = hold.not_held || [];
    const li = (lead, rest) => {
      const x = el('li');
      x.append(el('strong', null, lead), ' ' + rest);
      return x;
    };
    for (const it of nh.filter((x) => x.tier === 'avoid')) {
      const why = String(it.why || '').replace(/^Not held:\s*/i, '');
      ul.append(li(`Not holding ${lowerFirst(it.name)}:`, why));
    }
    // watch items that share the same sentence are grouped into one line
    const groups = new Map();
    for (const it of nh.filter((x) => x.tier === 'watch')) {
      const k = it.why || '';
      if (!groups.has(k)) groups.set(k, []);
      groups.get(k).push(it.name);
    }
    for (const [why, names] of groups) {
      const joined = joinNames(names.map((nm, i) => (i === 0 ? upperFirst(nm) : lowerFirst(nm))));
      ul.append(li('Watching:', `${joined}. ${why}`));
    }
    if (!ul.children.length) ul.append(el('li', 'muted', 'Nothing on the list right now.'));
  }

  /* ---------------------------------------------------------------- changes tab */
  function renderChangesTab(ch) {
    const ol = clear($('changes-list'));
    const items = sortedChanges(ch);
    if (!items.length) ol.append(el('li', 'muted', 'No changes yet.'));
    for (const c of items) {
      const li = el('li');
      const when = el('div', 'when');
      const draft = String(c.status || '').toLowerCase() === 'draft';
      when.append(el('span', null, fmtDate(c.date)), el('span', 'status ' + (draft ? 'draft' : 'done'), draft ? 'Draft' : cap(c.status || 'logged')));
      li.append(when, el('h4', null, c.title || ''), el('p', null, c.detail || ''));
      if (draft) li.append(el('p', 'note', 'Draft only · No paper trades executed or changes logged yet.'));
      ol.append(li);
    }
  }

  function renderLedger(text) {
    const body = clear($('ledger-body'));
    const lines = text.replace(/\r\n?/g, '\n').split('\n');
    const intro = [];
    for (const l of lines) {
      if (/^\s*\|/.test(l)) break;
      if (/^#/.test(l)) continue;
      intro.push(l);
    }
    body.append(md(intro.join('\n')));
    const tbl = lines.filter((l) => /^\s*\|/.test(l));
    const dated = tbl.slice(2).filter((l) => /^\s*\|\s*\d{4}-\d{2}-\d{2}/.test(l));
    if (!dated.length) {
      body.append(el('p', null, 'No paper trades have been logged yet. A change in the list above is only a proposal until a dated trade appears here.'));
    } else {
      body.append(md([tbl[0], tbl[1], ...dated].join('\n')));
    }
  }

  /* ---------------------------------------------------------------- safe markdown renderer
     Builds DOM nodes from text, so nothing is ever interpreted as HTML ("escape everything first"
     is true by construction). Supports headings, bold, italic, code, lists, quotes, tables, rules
     and links; a link is only made for the one allowed address (Swarm AI), otherwise just its text. */
  const INLINE_SRC =
    '(`+)([^`]+?)\\1' + // 1,2 code
    '|\\*\\*(.+?)\\*\\*' + // 3 bold
    '|\\[([^\\]]+)\\]\\(([^)\\s]+)\\)' + // 4,5 link
    '|(?<![\\w*])\\*(?![\\s*])(.+?)(?<![\\s*])\\*(?![\\w*])' + // 6 italic (*)
    '|(?<!\\w)_(?![\\s_])(.+?)(?<![\\s_])_(?!\\w)'; // 7 italic (_)

  function appendText(parent, s) {
    const parts = s.split('\n');
    parts.forEach((part, i) => {
      if (i > 0) parent.append(document.createElement('br'));
      if (part) parent.append(part);
    });
  }
  function inline(text, parent) {
    const re = new RegExp(INLINE_SRC, 'g');
    let last = 0;
    let m;
    while ((m = re.exec(text))) {
      if (m.index > last) appendText(parent, text.slice(last, m.index));
      if (m[2] !== undefined) {
        parent.append(el('code', null, m[2]));
      } else if (m[3] !== undefined) {
        const s = document.createElement('strong');
        inline(m[3], s);
        parent.append(s);
      } else if (m[4] !== undefined) {
        if (SWARM.test(m[5])) {
          const a = document.createElement('a');
          a.href = m[5];
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
          inline(m[4], a);
          parent.append(a);
        } else {
          inline(m[4], parent);
        }
      } else if (m[6] !== undefined || m[7] !== undefined) {
        const e = document.createElement('em');
        inline(m[6] !== undefined ? m[6] : m[7], e);
        parent.append(e);
      }
      last = re.lastIndex;
    }
    if (last < text.length) appendText(parent, text.slice(last));
  }

  function splitRow(s) {
    s = s.trim();
    if (s.startsWith('|')) s = s.slice(1);
    if (s.endsWith('|') && !s.endsWith('\\|')) s = s.slice(0, -1);
    return s
      .replace(/\\\|/g, '\u0001')
      .split('|')
      .map((c) => c.replace(/\u0001/g, '|').trim());
  }
  const isBlank = (s) => /^\s*$/.test(s);
  const isTableSep = (s) => /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$/.test(s) && s.includes('-');
  const isHr = (s) => /^\s*([-*_])(\s*\1){2,}\s*$/.test(s);
  const isHeading = (s) => /^#{1,6}\s+\S/.test(s);
  const isQuote = (s) => /^\s*>/.test(s);
  const isUl = (s) => /^\s*[-*+]\s+\S/.test(s);
  const isOl = (s) => /^\s*\d+[.)]\s+\S/.test(s);
  const isTableStart = (lines, i) => /^\s*\|/.test(lines[i]) && i + 1 < lines.length && isTableSep(lines[i + 1]);
  const startsBlock = (lines, i) =>
    isBlank(lines[i]) || isHeading(lines[i]) || isHr(lines[i]) || isQuote(lines[i]) || isUl(lines[i]) || isOl(lines[i]) || isTableStart(lines, i);

  function md(src, opts) {
    opts = opts || {};
    const frag = document.createDocumentFragment();
    const lines = String(src).replace(/\r\n?/g, '\n').replace(/<!--[\s\S]*?-->/g, '').split('\n');
    let skipH1 = !!opts.skipFirstH1;
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      if (isBlank(line)) { i++; continue; }

      let m;
      if ((m = /^(#{1,6})\s+(.+?)\s*#*\s*$/.exec(line))) {
        i++;
        if (m[1].length === 1 && skipH1) { skipH1 = false; continue; }
        const h = document.createElement('h' + Math.min(6, m[1].length + 2));
        inline(m[2], h);
        frag.append(h);
        continue;
      }
      if (isHr(line)) { frag.append(document.createElement('hr')); i++; continue; }

      if (isQuote(line)) {
        const q = [];
        while (i < lines.length && isQuote(lines[i])) { q.push(lines[i].replace(/^\s*>\s?/, '')); i++; }
        const bq = document.createElement('blockquote');
        bq.append(md(q.join('\n')));
        frag.append(bq);
        continue;
      }

      if (isTableStart(lines, i)) {
        const head = splitRow(lines[i]);
        i += 2;
        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const trh = document.createElement('tr');
        for (const c of head) { const th = document.createElement('th'); th.scope = 'col'; inline(c, th); trh.append(th); }
        thead.append(trh);
        const tbody = document.createElement('tbody');
        while (i < lines.length && /^\s*\|/.test(lines[i])) {
          const cells = splitRow(lines[i]);
          const tr = document.createElement('tr');
          for (let k = 0; k < head.length; k++) { const td = document.createElement('td'); inline(cells[k] || '', td); tr.append(td); }
          tbody.append(tr);
          i++;
        }
        table.append(thead, tbody);
        const wrap = el('div', 'table-wrap');
        wrap.tabIndex = 0;
        wrap.setAttribute('role', 'region');
        wrap.setAttribute('aria-label', 'Table (scrolls sideways on small screens)');
        wrap.append(table);
        frag.append(wrap);
        continue;
      }

      if (isUl(line) || isOl(line)) {
        const ordered = isOl(line);
        const list = document.createElement(ordered ? 'ol' : 'ul');
        const marker = ordered ? /^\s*\d+[.)]\s+/ : /^\s*[-*+]\s+/;
        while (i < lines.length && (ordered ? isOl(lines[i]) : isUl(lines[i])) && !/^\s{2,}/.test(lines[i])) {
          let text = lines[i].replace(marker, '');
          i++;
          const nested = [];
          while (i < lines.length && /^\s{2,}\S/.test(lines[i])) { nested.push(lines[i].replace(/^\s{2}/, '')); i++; }
          const li = document.createElement('li');
          while (nested.length && !isUl(nested[0]) && !isOl(nested[0])) text += ' ' + nested.shift().trim();
          inline(text, li);
          if (nested.length) li.append(md(nested.join('\n')));
          list.append(li);
          // a single blank line between items keeps the same list going
          if (i < lines.length && isBlank(lines[i]) && i + 1 < lines.length && (ordered ? isOl(lines[i + 1]) : isUl(lines[i + 1]))) i++;
        }
        frag.append(list);
        continue;
      }

      // paragraph: a line that opens with **bold** after another line starts a new line (the thesis uses that for labels)
      let text = line.trim();
      i++;
      while (i < lines.length && !startsBlock(lines, i)) {
        const t = lines[i].trim();
        text += (t.startsWith('**') ? '\n' : ' ') + t;
        i++;
      }
      const p = document.createElement('p');
      inline(text, p);
      frag.append(p);
    }
    return frag;
  }

  /* ---------------------------------------------------------------- load everything */
  async function init() {
    const names = ['holdings', 'changes', 'week', 'rules', 'thesis', 'scam', 'ledger'];
    const results = await Promise.allSettled([
      getJSON('data/holdings.json'),
      getJSON('data/changes.json'),
      getJSON('data/this-week.json'),
      getJSON('data/rules.json'),
      getText('data/THESIS.md'),
      getText('data/scam-signs.md'),
      getText('data/ledger.md'),
    ]);
    const d = {};
    results.forEach((r, i) => { d[names[i]] = r.status === 'fulfilled' ? r.value : null; });
    const run = (fn, onFail) => {
      try { fn(); } catch (e) { onFail(); }
    };

    if (d.holdings) {
      run(() => renderPortfolio(d.holdings, d.rules), () => failed($('pf-rows'), 'the holdings'));
      run(() => renderAvoid(d.holdings), () => failed($('avoid-list'), 'this list'));
    } else {
      failed($('pf-rows'), 'the holdings');
      failed($('avoid-list'), 'this list');
    }
    renderTrack(d.rules);

    if (d.changes) {
      run(() => renderChanged(d.changes), () => failed($('changed-body'), 'the latest change'));
      run(() => renderChangesTab(d.changes), () => failed($('changes-list'), 'the changes'));
    } else {
      failed($('changed-body'), 'the latest change');
      failed($('changes-list'), 'the changes');
    }

    if (d.week) {
      run(() => renderWeek(d.week, 'week-body', 'week-date', false), () => failed($('week-body'), 'this week'));
      run(() => renderWeek(d.week, 'week-big-body', 'week-big-date', true), () => failed($('week-big-body'), 'this week'));
    } else {
      failed($('week-body'), 'this week');
      failed($('week-big-body'), 'this week');
    }

    if (d.thesis != null) clear($('thesis-body')).append(md(d.thesis, { skipFirstH1: true }));
    else failed($('thesis-body'), 'the research');
    if (d.scam != null) clear($('scam-body')).append(md(d.scam, { skipFirstH1: true }));
    else failed($('scam-body'), 'this page');
    if (d.ledger != null) run(() => renderLedger(d.ledger), () => failed($('ledger-body'), 'the ledger'));
    else failed($('ledger-body'), 'the ledger');
  }

  init();
})();
