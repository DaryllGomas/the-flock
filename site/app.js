/* The Flock: public page.
   Local files only. Everything from the data files goes into the page with textContent / text nodes,
   never as HTML, and the markdown renderer builds DOM nodes, so nothing in the data can run as code. */
(() => {
  'use strict';

  // The page works as plain HTML without this script; the class lets the stylesheet hide the
  // "Loading…" placeholders for visitors who run no JavaScript.
  document.documentElement.classList.remove('no-js');

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
  const REQUEST_TIMEOUT_MS = 8000; // one stalled file must not hold up the rest of the page
  const FAIL_TEXT = "Couldn't load this part. Try again later.";

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
  // One request, one timeout. The timer also covers reading the body, so a stalled download aborts too.
  async function load(path, kind) {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), REQUEST_TIMEOUT_MS);
    try {
      const r = await fetch(path, { cache: 'no-cache', signal: ctl.signal });
      if (!r.ok) throw new Error(path + ' ' + r.status);
      return await (kind === 'json' ? r.json() : r.text());
    } finally {
      clearTimeout(timer);
    }
  }
  // A calm per-section message in place of the "Loading…" line; the rest of the page is untouched.
  function failed(container) {
    const p = el(container.tagName === 'P' ? 'span' : 'p', 'fail', FAIL_TEXT);
    p.setAttribute('role', 'status');
    if (container.tagName === 'UL' || container.tagName === 'OL') {
      const li = el('li');
      li.append(p);
      clear(container).append(li);
    } else {
      clear(container).append(p);
    }
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

  function renderPortfolio(hold) {
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
    $('pf-draft').textContent = draftLabel(hold);
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
     and links. A link becomes a real <a> only for an absolute https:// address;
     any other address (javascript:, data:, http:, relative, //host, mailto: ...) is dropped and
     only its text is kept.

     Every loop below moves forward on every pass, and nesting is capped, so no input can hang the
     page or blow the stack: the worst case is some text shown plainly. */
  const MAX_DEPTH = 8; // nested quotes / lists / bold-in-italic
  const MAX_INLINE = 20000; // longer runs of a single paragraph are shown as plain text

  const INLINE_SRC =
    '(`+)([^`]+?)\\1' + // 1,2 code
    '|\\*\\*(.+?)\\*\\*' + // 3 bold
    '|\\[([^\\]]+)\\]\\(((?:[^()\\s]|\\([^()\\s]*\\))+)\\)' + // 4,5 link (one level of () allowed in the address)
    '|(?<![\\w*])\\*(?![\\s*])(.+?)(?<![\\s*])\\*(?![\\w*])' + // 6 italic (*)
    '|(?<!\\w)_(?![\\s_])(.+?)(?<![\\s_])_(?!\\w)' + // 7 italic (_)
    '|(?<![\\w@/])(https:\\/\\/(?:[^()\\s<>\\[\\]]|\\([^()\\s<>\\[\\]]*\\))+)'; // 8 bare https:// address

  // Returns the normalised address when it is safe to link, otherwise null.
  function safeHref(raw) {
    if (typeof raw !== 'string' || raw.length > 2000) return null;
    if (!/^https:\/\/[^\s/?#@\\]/i.test(raw) || /[\s\\\u0000-\u001f\u007f]/.test(raw)) return null;
    let u;
    try { u = new URL(raw); } catch (e) { return null; }
    if (u.protocol !== 'https:' || u.username || u.password) return null; // no user:pass@host tricks
    return u.href;
  }

  function appendText(parent, s) {
    const parts = s.split('\n');
    parts.forEach((part, i) => {
      if (i > 0) parent.append(document.createElement('br'));
      if (part) parent.append(part);
    });
  }
  function makeLink(href, parent) {
    const a = document.createElement('a');
    a.href = href;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.referrerPolicy = 'no-referrer';
    parent.append(a);
    return a;
  }
  // inLink: already inside a link, so no second link may be made in it
  function inline(text, parent, depth, inLink) {
    depth = depth || 0;
    if (depth > MAX_DEPTH || text.length > MAX_INLINE) { appendText(parent, text); return; }
    const re = new RegExp(INLINE_SRC, 'g');
    let last = 0;
    let m;
    while ((m = re.exec(text))) {
      if (re.lastIndex <= last) {
        appendText(parent, text.charAt(last));
        re.lastIndex = ++last;
        continue;
      }
      if (m.index > last) appendText(parent, text.slice(last, m.index));
      if (m[2] !== undefined) {
        parent.append(el('code', null, m[2]));
      } else if (m[3] !== undefined) {
        const s = document.createElement('strong');
        inline(m[3], s, depth + 1, inLink);
        parent.append(s);
      } else if (m[4] !== undefined) {
        const href = inLink ? null : safeHref(m[5]);
        if (href) {
          const a = makeLink(href, parent);
          inline(m[4], a, depth + 1, true);
          a.append(el('span', 'vh', ' (opens in a new tab)'));
        } else {
          // A rejected destination must not turn a URL in its label into a link either.
          inline(m[4], parent, depth + 1, true);
        }
      } else if (m[6] !== undefined || m[7] !== undefined) {
        const e = document.createElement('em');
        inline(m[6] !== undefined ? m[6] : m[7], e, depth + 1, inLink);
        parent.append(e);
      } else if (m[8] !== undefined) {
        // A bare address is trimmed of trailing punctuation ("see https://x.org/a.") and linked only when safe.
        let end = m[8].length;
        while (end > 0 && '.,;:!?\'"*_'.includes(m[8].charAt(end - 1))) end--;
        const url = m[8].slice(0, end);
        re.lastIndex = m.index + end;
        const href = inLink ? null : safeHref(url);
        if (href) {
          const a = makeLink(href, parent);
          a.append(url);
          a.append(el('span', 'vh', ' (opens in a new tab)'));
        } else {
          appendText(parent, url);
        }
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
  // Line tests. None of them can backtrack badly, so a very long line stays fast.
  const isBlank = (s) => s.trim() === '';
  const isTableSep = (s) => {
    let t = s.trim();
    if (!t.includes('-')) return false;
    if (t.startsWith('|')) t = t.slice(1);
    if (t.endsWith('|')) t = t.slice(0, -1);
    return t.split('|').every((c) => /^:?-{3,}:?$/.test(c.trim()));
  };
  const isHr = (s) => {
    const t = s.replace(/\s+/g, '');
    return t.length >= 3 && /^(?:-+|\*+|_+)$/.test(t);
  };
  const isHeading = (s) => /^#{1,6}\s+\S/.test(s);
  const isQuote = (s) => /^\s*>/.test(s);
  const isUl = (s) => /^\s*[-*+]\s+\S/.test(s);
  const isOl = (s) => /^\s*\d+[.)]\s+\S/.test(s);
  const isTableStart = (lines, i) => /^\s*\|/.test(lines[i]) && i + 1 < lines.length && isTableSep(lines[i + 1]);
  const startsBlock = (lines, i) =>
    isBlank(lines[i]) || isHeading(lines[i]) || isHr(lines[i]) || isQuote(lines[i]) || isUl(lines[i]) || isOl(lines[i]) || isTableStart(lines, i);
  // Width of the leading whitespace (tabs are already turned into spaces by md()).
  const indentOf = (s) => s.length - s.trimStart().length;

  // Removes <!-- ... --> in one linear pass; an unclosed "<!--" is left as ordinary text.
  function stripComments(s) {
    let out = '';
    let pos = 0;
    for (;;) {
      const a = s.indexOf('<!--', pos);
      if (a === -1) break;
      const b = s.indexOf('-->', a + 4);
      if (b === -1) break;
      out += s.slice(pos, a);
      pos = b + 3;
    }
    return out + s.slice(pos);
  }

  function paragraphOf(text) {
    const p = document.createElement('p');
    inline(text, p);
    return p;
  }

  function md(src, opts) {
    opts = opts || {};
    const depth = opts.depth || 0;
    const frag = document.createDocumentFragment();
    const text0 = stripComments(String(src).replace(/\r\n?/g, '\n'))
      .replace(/^[ \t]+/gm, (ws) => ws.replace(/\t/g, '    ')); // tabs in leading whitespace count as 4 spaces
    const lines = text0.split('\n');
    if (depth > MAX_DEPTH) { // too deeply nested to be real content: show it plainly
      const p = document.createElement('p');
      appendText(p, text0.trim());
      frag.append(p);
      return frag;
    }
    const nest = { depth: depth + 1 };
    let skipH1 = !!opts.skipFirstH1;
    let i = 0;
    let lastStart = -1;
    while (i < lines.length) {
      // Forward-progress guard: a pass that consumed nothing (should be impossible) is treated as
      // a plain paragraph line, so the loop can never spin.
      if (i <= lastStart) {
        if (!isBlank(lines[i])) frag.append(paragraphOf(lines[i].trim()));
        i++;
        continue;
      }
      lastStart = i;

      const line = lines[i];
      if (isBlank(line)) { i++; continue; }

      if (isHeading(line)) {
        i++;
        const m = /^(#{1,6})\s+/.exec(line);
        let content = line.slice(m[0].length).trim();
        const closing = /\s#+$/.exec(content); // optional closing hashes: "## Title ##"
        if (closing) content = content.slice(0, closing.index).trim();
        if (m[1].length === 1 && skipH1) { skipH1 = false; continue; }
        const h = document.createElement('h' + Math.min(6, m[1].length + 2));
        inline(content, h);
        frag.append(h);
        continue;
      }
      if (isHr(line)) { frag.append(document.createElement('hr')); i++; continue; }

      if (isQuote(line)) {
        const q = [];
        while (i < lines.length && isQuote(lines[i])) { q.push(lines[i].replace(/^\s*>\s?/, '')); i++; }
        const bq = document.createElement('blockquote');
        bq.append(md(q.join('\n'), nest));
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
        // A list starts at the indentation of its first item (so a lone "  - item" is fine). Items
        // within 1 space of that indentation are siblings; lines indented 2 or more spaces further
        // belong to the item above and are rendered again as nested content.
        const ordered = isOl(line);
        const sameKind = ordered ? isOl : isUl;
        const marker = ordered ? /^\s*\d+[.)]\s+/ : /^\s*[-*+]\s+/;
        const base = indentOf(line);
        const isSibling = (k) => k < lines.length && sameKind(lines[k]) && indentOf(lines[k]) < base + 2;
        const list = document.createElement(ordered ? 'ol' : 'ul');
        while (isSibling(i)) {
          const before = i;
          let text = lines[i].replace(marker, '');
          i++;
          const nested = [];
          while (i < lines.length && !isBlank(lines[i]) && indentOf(lines[i]) >= base + 2) { nested.push(lines[i].slice(base + 2)); i++; }
          const li = document.createElement('li');
          while (nested.length && !isUl(nested[0]) && !isOl(nested[0])) text += ' ' + nested.shift().trim();
          inline(text, li);
          if (nested.length) li.append(md(nested.join('\n'), nest));
          list.append(li);
          // a single blank line between items keeps the same list going
          if (i < lines.length && isBlank(lines[i]) && isSibling(i + 1)) i++;
          if (i <= before) {
            const fallback = el('li');
            fallback.append(paragraphOf(lines[i]));
            list.append(fallback);
            i++;
          }
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
      frag.append(paragraphOf(text));
    }
    return frag;
  }

  /* ---------------------------------------------------------------- load everything
     Every file is requested on its own, with its own timeout, and every section draws itself the
     moment the file it needs arrives. A file that is missing, slow or broken only turns its own
     section into a short, calm message; the rest of the page is unaffected. */
  function section(deps, render, targets) {
    const fail = () => targets.forEach((id) => failed($(id)));
    Promise.all(deps).then((values) => {
      try { render(...values); } catch (e) { fail(); }
    }, fail);
  }

  function init() {
    const holdings = load('data/holdings.json', 'json');
    const changes = load('data/changes.json', 'json');
    const week = load('data/this-week.json', 'json');
    const rules = load('data/rules.json', 'json');
    const thesis = load('data/THESIS.md', 'text');
    const scam = load('data/scam-signs.md', 'text');
    const ledger = load('data/ledger.md', 'text');
    section([holdings], renderPortfolio, ['pf-rows']);
    section([holdings], renderAvoid, ['avoid-list']);
    section([rules], (r) => {
      $('pf-amount').textContent = money(r.notional_usd || 100000);
      renderTrack(r);
    }, ['pf-amount', 'track-lede']);

    section([changes], renderChanged, ['changed-body']);
    section([changes], renderChangesTab, ['changes-list']);

    section([week], (w) => renderWeek(w, 'week-body', 'week-date', false), ['week-body']);
    section([week], (w) => renderWeek(w, 'week-big-body', 'week-big-date', true), ['week-big-body']);

    section([thesis], (t) => clear($('thesis-body')).append(md(t, { skipFirstH1: true })), ['thesis-body']);
    section([scam], (t) => clear($('scam-body')).append(md(t, { skipFirstH1: true })), ['scam-body']);
    section([ledger], renderLedger, ['ledger-body']);
  }

  init();
})();
