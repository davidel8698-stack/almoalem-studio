// =============================================================
// build/templates/partials.mjs
// -------------------------------------------------------------
// Pure render functions for every JS-filled container on the
// home page. Output of each function is a STRING of HTML that
// becomes the innerHTML of its container.
//
// The runtime JS in mono.html has the same logic inline; this
// file is the BUILD-TIME equivalent, kept byte-identical so the
// JS hydration (which re-assigns innerHTML on first paint and on
// language toggle) produces the same DOM. No flicker.
//
// If you change either side, change BOTH.
// =============================================================

// --- Section constants — runtime-side has the same in mono.html ---
const TOOLS = {
  '01': ['Figma', 'Adobe', 'Type'],
  '02': ['Figma', 'Framer', 'Webflow'],
  '03': ['React', 'Next.js', 'TypeScript', 'Sanity'],
  '04': ['DaVinci', 'After FX', 'Photoshop'],
};
const PROCESS_DURATIONS = ['1 call', '1 week', '1 week', '3–5 wk', '4–6 wk', '1 month'];
const TESTIMONIAL_TINTS = ['#c8be9e', '#beb792', '#d2c8ab'];
const PG_CLASSES = ['a', 'b', 'c', 'd', 'e', 'f'];
const PG_TAGS = ['Type', 'Cursor', 'Writing', 'Photo'];
const PG_TINTS = ['#cabf9f', '#beb792', '#d2c8ab', '#bdb38e'];

// --- helpers ---
const initials = (name) =>
  name.split(/\s+/).map((w) => w[0]).slice(0, 2).join('');

// =============================================================
// 1. WORK  (#work-scroller)
// =============================================================
export function renderWork(d, workBase = 'work') {
  // Each project card is a REAL anchor to <workBase>/<slug>/. The runtime
  // JS intercepts the click to open the in-page overlay (with pushState
  // so the URL still updates) — but cmd-click, right-click and JS-off
  // visits all behave like a normal link, hitting the standalone page.
  //
  // workBase defaults to 'work' (relative to root). For /he/ pages set it
  // to '../work' so cards point UP to the canonical EN project pages.
  const cards = d.work.projects
    .map(
      (p, i) => `
      <a href="${workBase}/${p.slug}/" class="proj-card" data-idx="${i}" data-slug="${p.slug}" data-cursor="view" data-cursor-text="${d.work.view}">
        <div class="img" style="--ptint:${p.tint}">
          <span class="num">${p.id}</span>
          <span class="corner-tl"></span><span class="corner-tr"></span>
          <span class="corner-bl"></span><span class="corner-br"></span>
          <span class="label">${p.client} · ${p.scope}</span>
        </div>
        <div class="body">
          <span class="name">${p.client}</span>
          <span class="arr">↗</span>
          <span class="scope">${p.scope} · ${p.role}</span>
          <span class="y">${p.year}</span>
          <span class="desc">${p.desc}</span>
        </div>
      </a>
    `
    )
    .join('');
  // pad-end div sits at the end so the horizontal scroll has room past the
  // last card — this matches what the runtime JS appends.
  return cards + '<div class="pad-end"></div>';
}

// =============================================================
// 2. ABOUT — paragraphs (#about-paras)
// =============================================================
export function renderAboutParas(d) {
  return d.about.paragraphs.map((p) => `<p>${p}</p>`).join('');
}

// =============================================================
// 3. ABOUT — facts grid (#about-facts)
// =============================================================
export function renderAboutFacts(d) {
  return d.about.facts
    .map(
      ([k, v]) =>
        `<div class="f"><span class="k">${k}</span><span class="v">${v}</span></div>`
    )
    .join('');
}

// =============================================================
// 4. APPROACH (#svc-grid)
// =============================================================
export function renderServices(d) {
  return d.services.items
    .map((s) => {
      const t = TOOLS[s.n] || [];
      return `
        <div class="svc" data-reveal>
          <span class="n">/ ${s.n}</span>
          <div>
            <h3>${s.t}</h3>
            <p>${s.d}</p>
            <div class="stack">${t.map((x) => `<span>${x}</span>`).join('')}</div>
          </div>
        </div>`;
    })
    .join('');
}

// =============================================================
// 5. PROCESS (#proc-row)
// =============================================================
export function renderProcess(d) {
  return d.process.steps
    .map(
      (s, i) => `
      <div class="step">
        <span class="n">/ ${s.n}</span>
        <h3>${s.t}</h3>
        <p>${s.d}</p>
        <span class="dur">${PROCESS_DURATIONS[i]}</span>
      </div>
    `
    )
    .join('');
}

// =============================================================
// 6. TESTIMONIALS (#t-grid)
// Asymmetric: first quote big, rest small in a second column.
// =============================================================
export function renderTestimonials(d) {
  const t = d.testimonials.items;
  return `
      <div class="col">
        <div class="t-card" data-cursor="read">
          <span class="q-mark">"</span>
          <p class="q">${t[0].quote}</p>
          <div class="ftr"><span class="avatar" style="--abg:${TESTIMONIAL_TINTS[0]}">${initials(t[0].author)}</span><span class="a">${t[0].author}</span><span class="r">— ${t[0].role}</span></div>
        </div>
      </div>
      <div class="col">
        ${t
          .slice(1)
          .map(
            (x, i) => `
          <div class="t-card small" data-cursor="read">
            <span class="q-mark">"</span>
            <p class="q">${x.quote}</p>
            <div class="ftr"><span class="avatar" style="--abg:${TESTIMONIAL_TINTS[i + 1]}">${initials(x.author)}</span><span class="a">${x.author}</span><span class="r">— ${x.role}</span></div>
          </div>
        `
          )
          .join('')}
      </div>
    `;
}

// =============================================================
// 7. AWARDS (#aw-list)
// =============================================================
export function renderAwards(d) {
  return d.awards.items
    .map(
      ([s, w, y], i) => `
      <div class="aw" data-cursor="read">
        <span class="n">/ 0${i + 1}</span>
        <span class="src">${s}</span>
        <span class="what">${w}</span>
        <span class="y">${y}</span>
        <span class="badge"></span>
      </div>
    `
    )
    .join('');
}

// =============================================================
// 8. PLAYGROUND (#pg-mosaic)
// =============================================================
export function renderPlayground(d) {
  return d.playground.items
    .map(
      (p, i) => `
      <div class="pg ${PG_CLASSES[i]}" data-cursor="view" data-cursor-text="${d.cursor.view}">
        <div class="img" style="--ptint:${PG_TINTS[i % PG_TINTS.length]}">
          <span>${p.t} · ${p.d.split(' ').slice(0, 5).join(' ')}</span>
        </div>
        <div class="body"><span class="t">${p.t}</span><span class="tag">${PG_TAGS[i]}</span></div>
      </div>
    `
    )
    .join('');
}

// =============================================================
// 9. JOURNAL (#j-grid)
// =============================================================
export function renderJournal(d, workBase = '') {
  // Journal cards link to /journal/<slug>/ — the slug is the 5th
  // tuple element added in Phase 4.4. workBase prefix (e.g. '../')
  // adapts depth for /he/ where the JS-side knows where it sits.
  return d.journal.items
    .map(
      ([n, t_, d_, r, slug]) => `
      <a href="${workBase}journal/${slug || ''}/" class="j" data-cursor="read">
        <div class="top"><span class="n">${n}</span><span class="meta">${d_}</span></div>
        <h3 class="t">${t_}</h3>
        <div class="row"><span class="read">${r} read</span><span class="arr">↗</span></div>
      </a>
    `
    )
    .join('');
}

// =============================================================
// 10. CONTACT lines (#ct-lines)
// =============================================================
export function renderContactLines(d) {
  return d.contact.lines
    .map(([k, v]) => {
      const isMail = v.includes('@');
      const isLink =
        isMail ||
        v.includes('.com') ||
        v.includes('.cv') ||
        v.includes('Are.na');
      const valHtml = isLink
        ? `<a href="${isMail ? 'mailto:' + v : '#'}">${v}</a>`
        : v;
      return `<div class="line"><span class="k">${k}</span><span class="v">${valHtml}</span></div>`;
    })
    .join('');
}

// =============================================================
// Container-ID → render-function map.
// build.mjs iterates this and injects each.
// =============================================================
export const SECTIONS = [
  { id: 'work-scroller', render: renderWork },
  { id: 'about-paras', render: renderAboutParas },
  { id: 'about-facts', render: renderAboutFacts },
  { id: 'svc-grid', render: renderServices },
  { id: 'proc-row', render: renderProcess },
  { id: 't-grid', render: renderTestimonials },
  { id: 'aw-list', render: renderAwards },
  { id: 'pg-mosaic', render: renderPlayground },
  { id: 'j-grid', render: renderJournal },
  { id: 'ct-lines', render: renderContactLines },
];
