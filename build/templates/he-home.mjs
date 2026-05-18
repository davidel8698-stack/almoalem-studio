// =============================================================
// build/templates/he-home.mjs
// -------------------------------------------------------------
// Transforms a finished EN home (dist/index.html) into a working
// /he/ home page. Called by phase3 in build.mjs. Keeps the same
// CSS/JS infrastructure — only the textual surface and metadata
// change.
//
// Why a transform rather than a parallel template:
//   The home page has a lot of branded markup that's tedious to
//   maintain in two places. Instead, we build EN once and use a
//   set of typed replacements to derive the HE version. Every
//   replacement is annotated with what it covers, so the file
//   reads as a checklist of the EN→HE diff.
// =============================================================

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname } from 'node:path';
import { buildHomeGraph } from './jsonld.mjs';
import { SECTIONS } from './partials.mjs';

export const SITE = 'https://almoalem.studio';

// HE static text overrides not covered by data-i18n / JSON content files.
// These come from the page's hand-written markup and must be translated
// at build time.
const HE_HERO_HEADLINE = `
    מעצב <span class="slash">/</span><br>
    ממשקים שקטים<br>
    למוצרים <span class="ital">שאפתניים.</span>
  `;

const HE_FOOTER_L = '© 2026 דוד אלמועלם · v.4.1 · build אחרון 16 במאי 2026';
const HE_FOOTER_C = 'נוצר ביד בתל אביב · 32.0853° N';
const HE_FOOTER_R =
  'מוגדר ב-Geist + JetBrains Mono · <b>בלי אנליטיקס</b> · בלי עוגיות · plain html';

const HE_TITLE = 'דוד אלמועלם — מעצב ומפתח עצמאי · תל אביב';
const HE_KEYWORDS =
  'מעצב עצמאי תל אביב, מפתח אתרים, מותג ויזואלי, מערכות מותג, designer Tel Aviv, brand identity, design and development';
const HE_OG_ALT = 'דוד אלמועלם — מעצב ומפתח עצמאי, תל אביב';

const HREFLANG_BLOCK = [
  '<link rel="alternate" hreflang="en" href="https://almoalem.studio/">',
  '<link rel="alternate" hreflang="he" href="https://almoalem.studio/he/">',
  '<link rel="alternate" hreflang="x-default" href="https://almoalem.studio/">',
].join('\n');

const TOOLS = {
  '01': ['Figma', 'Adobe', 'Type'],
  '02': ['Figma', 'Framer', 'Webflow'],
  '03': ['React', 'Next.js', 'TypeScript', 'Sanity'],
  '04': ['DaVinci', 'After FX', 'Photoshop'],
};
const PROCESS_DURATIONS_HE = ['שיחה', 'שבוע', 'שבוע', '3–5 שב׳', '4–6 שב׳', 'חודש'];
const PG_TAGS_HE = ['טיפו׳', 'סמן', 'כתיבה', 'צילום'];

// Balanced-tag injection helper — same algorithm as build.mjs.
function injectIntoContainer(html, id, content) {
  const idMarker = `id="${id}"`;
  const idIdx = html.indexOf(idMarker);
  if (idIdx === -1) throw new Error(`#${id} not found`);
  let tagStart = idIdx;
  while (tagStart > 0 && html[tagStart] !== '<') tagStart--;
  let tagEnd = idIdx;
  while (tagEnd < html.length && html[tagEnd] !== '>') tagEnd++;
  const tagName = html.slice(tagStart + 1, tagEnd).match(/^(\w+)/)[1];
  const openRE = new RegExp(`<${tagName}\\b`, 'gi');
  const closeRE = new RegExp(`</${tagName}\\s*>`, 'gi');
  let depth = 1, cursor = tagEnd + 1;
  while (cursor < html.length && depth > 0) {
    openRE.lastIndex = cursor;
    closeRE.lastIndex = cursor;
    const om = openRE.exec(html);
    const cm = closeRE.exec(html);
    if (!cm) throw new Error(`Unbalanced <${tagName}> for #${id}`);
    if (om && om.index < cm.index) { depth++; cursor = om.index + om[0].length; }
    else { depth--; if (depth === 0) return html.slice(0, tagEnd + 1) + content + html.slice(cm.index); cursor = cm.index + cm[0].length; }
  }
  throw new Error(`No </${tagName}> for #${id}`);
}

function getByPath(obj, path) {
  return path.split('.').reduce((o, k) => (o ? o[k] : undefined), obj);
}

function htmlEscape(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export async function buildHeHome({ rootDir, distDir, log = () => {} }) {
  const enPath = `${distDir}/index.html`;
  const hePath = `${distDir}/he/index.html`;

  const he = JSON.parse(
    await readFile(`${rootDir}/data/content.he.json`, 'utf8')
  );
  let h = await readFile(enPath, 'utf8');

  // ----- 1. <html lang/dir> -----
  h = h.replace('<html lang="en" dir="ltr">', '<html lang="he" dir="rtl">');

  // ----- 2. <title>, meta description, keywords -----
  h = h.replace(
    /<title>[^<]*<\/title>/,
    `<title>${htmlEscape(HE_TITLE)}</title>`
  );
  h = h.replace(
    /<meta name="description" content="[^"]*">/,
    `<meta name="description" content="${htmlEscape(he.hero.lede)}">`
  );
  h = h.replace(
    /<meta name="keywords" content="[^"]*">/,
    `<meta name="keywords" content="${htmlEscape(HE_KEYWORDS)}">`
  );

  // ----- 3. canonical + hreflang siblings -----
  h = h.replace(
    /<link rel="canonical" href="[^"]*">/,
    '<link rel="canonical" href="https://almoalem.studio/he/">\n' + HREFLANG_BLOCK
  );

  // ----- 4. OG locale + url + title + desc + image:alt -----
  h = h.replace('<meta property="og:locale" content="en_US">', '<meta property="og:locale" content="he_IL">');
  h = h.replace('<meta property="og:locale:alternate" content="he_IL">', '<meta property="og:locale:alternate" content="en_US">');
  h = h.replace(/<meta property="og:title" content="[^"]*">/, `<meta property="og:title" content="${htmlEscape(HE_TITLE)}">`);
  h = h.replace(/<meta property="og:description" content="[^"]*">/, `<meta property="og:description" content="${htmlEscape(he.hero.lede.slice(0, 140))}">`);
  h = h.replace('<meta property="og:url" content="https://almoalem.studio/">', '<meta property="og:url" content="https://almoalem.studio/he/">');
  h = h.replace(/<meta property="og:image:alt" content="[^"]*">/, `<meta property="og:image:alt" content="${htmlEscape(HE_OG_ALT)}">`);

  // ----- 5. Twitter card -----
  h = h.replace(/<meta name="twitter:title" content="[^"]*">/, `<meta name="twitter:title" content="${htmlEscape(HE_TITLE)}">`);
  h = h.replace(/<meta name="twitter:description" content="[^"]*">/, `<meta name="twitter:description" content="${htmlEscape(he.hero.lede.slice(0, 140))}">`);
  h = h.replace(/<meta name="twitter:image:alt" content="[^"]*">/, `<meta name="twitter:image:alt" content="${htmlEscape(HE_OG_ALT)}">`);

  // ----- 6. JSON-LD graph (rebuilt for HE) -----
  const ldOpen = h.indexOf('<script type="application/ld+json">');
  const ldClose = h.indexOf('</script>', ldOpen) + '</script>'.length;
  const heGraph = buildHomeGraph({ langContent: he, lang: 'he' });
  h = h.slice(0, ldOpen) +
      `<script type="application/ld+json">\n${JSON.stringify(heGraph, null, 2)}\n</script>` +
      h.slice(ldClose);

  // ----- 7. Asset paths — /he/ is one level deep -----
  //         lib/* and root-level component refs need a leading "../".
  h = h.replace(/href="lib\//g, 'href="../lib/');
  h = h.replace(/src="lib\//g, 'src="../lib/');
  h = h.replace(/src="tweaks-panel\.jsx"/g, 'src="../tweaks-panel.jsx"');
  h = h.replace(/src="design-canvas\.jsx"/g, 'src="../design-canvas.jsx"');
  h = h.replace(/href="favicon/g, 'href="../favicon');
  h = h.replace(/href="apple-touch/g, 'href="../apple-touch');
  h = h.replace(/href="site\.webmanifest"/g, 'href="../site.webmanifest"');

  // ----- 8. Pre-rendered section content — re-render with HE data -----
  // Use partials.mjs SECTIONS, but pass workBase='../work' for HE
  // (cards on /he/ link UP to /work/<slug>/ which are EN-canonical).
  const heRenders = {
    'work-scroller': SECTIONS.find(s => s.id === 'work-scroller').render(he, '../work'),
    'about-paras':   SECTIONS.find(s => s.id === 'about-paras').render(he),
    'about-facts':   SECTIONS.find(s => s.id === 'about-facts').render(he),
    'svc-grid':      SECTIONS.find(s => s.id === 'svc-grid').render(he),
    'proc-row':      renderProcessHe(he),
    't-grid':        SECTIONS.find(s => s.id === 't-grid').render(he),
    'aw-list':       SECTIONS.find(s => s.id === 'aw-list').render(he),
    'pg-mosaic':     renderPlaygroundHe(he),
    'j-grid':        renderJournalHe(he),
    'ct-lines':      SECTIONS.find(s => s.id === 'ct-lines').render(he),
  };
  for (const [id, content] of Object.entries(heRenders)) {
    h = injectIntoContainer(h, id, content);
  }

  // ----- 9. data-i18n elements — set initial textContent to HE -----
  h = h.replace(
    /(<[^>]+\bdata-i18n="([^"]+)"[^>]*>)([\s\S]*?)(<\/[^>]+>)/g,
    (m, open, path, inner, close) => {
      const v = getByPath(he, path);
      if (typeof v !== 'string') return m;
      return `${open}${htmlEscape(v)}${close}`;
    }
  );

  // ----- 10. Language toggle: buttons → anchors (HE active) -----
  const oldToggle = `<span class="ps-lang-toggle">
      <button class="lang-en active" data-lang="en">EN</button>
      <span class="ps-sep">/</span>
      <button class="lang-he" data-lang="he">עב</button>
    </span>`;
  const newToggleHe = `<span class="ps-lang-toggle">
      <a class="lang-en" data-lang="en" href="../" hreflang="en" rel="alternate">EN</a>
      <span class="ps-sep">/</span>
      <a class="lang-he active" data-lang="he" href="" hreflang="he" rel="alternate" aria-current="page">עב</a>
    </span>`;
  // EN home may already have been patched to <a> form; handle both.
  const enHomeToggle = `<span class="ps-lang-toggle">
      <a class="lang-en active" data-lang="en" href="" hreflang="en" rel="alternate" aria-current="page">EN</a>
      <span class="ps-sep">/</span>
      <a class="lang-he" data-lang="he" href="he/" hreflang="he" rel="alternate">עב</a>
    </span>`;
  if (h.includes(oldToggle))   h = h.replace(oldToggle, newToggleHe);
  if (h.includes(enHomeToggle)) h = h.replace(enHomeToggle, newToggleHe);

  // ----- 11. Inline JS default lang -----
  h = h.replace('let lang = "en";', 'let lang = "he";');

  // ----- 12. Hero h1 inner — HE poster headline -----
  const heroOpen = h.indexOf('<h1 class="hero-h1">');
  if (heroOpen !== -1) {
    const heroOpenEnd = heroOpen + '<h1 class="hero-h1">'.length;
    const heroClose = h.indexOf('</h1>', heroOpenEnd);
    h = h.slice(0, heroOpenEnd) + HE_HERO_HEADLINE + h.slice(heroClose);
  }

  // ----- 13. Footer text -----
  h = h.replace(
    /© 2026 David Almoalem · <b>v\.4\.1<\/b> · last build <span id="build-date">[^<]*<\/span>/,
    HE_FOOTER_L
  );
  h = h.replace(/Crafted by hand in Tel Aviv · 32\.0853° N/, HE_FOOTER_C);
  h = h.replace(
    /Set in Geist \+ JetBrains Mono · <b>no analytics<\/b> · no cookies · plain html/,
    HE_FOOTER_R
  );

  // ----- 14. Misc strings (cosmetic cleanup) -----
  h = h.replace('>Booking Q3 · 2026<', '>פנוי לפרויקטים · רבעון 3 2026<');

  // ----- 15. <body data-work-base="../work"> so runtime renderWork
  //          rehydrates with correct hrefs back to the EN project pages.
  if (!h.includes('data-work-base')) {
    h = h.replace(
      /<body([^>]*data-direction="mono"[^>]*)>/,
      '<body$1 data-work-base="../work">'
    );
  }

  // ----- 16. Save -----
  await mkdir(dirname(hePath), { recursive: true });
  await writeFile(hePath, h, 'utf8');
  log(`he-home.mjs: wrote ${hePath} (${(h.length / 1024).toFixed(1)} KB)`);
  return h;
}

// ---- HE-specific section renderers (process durations + playground tags) ----
function renderProcessHe(d) {
  return d.process.steps
    .map(
      (s, i) => `
      <div class="step">
        <span class="n">/ ${s.n}</span>
        <h3>${s.t}</h3>
        <p>${s.d}</p>
        <span class="dur">${PROCESS_DURATIONS_HE[i]}</span>
      </div>
    `
    )
    .join('');
}

function renderPlaygroundHe(d) {
  const PG_CLASSES = ['a', 'b', 'c', 'd', 'e', 'f'];
  const PG_TINTS = ['#cabf9f', '#beb792', '#d2c8ab', '#bdb38e'];
  return d.playground.items
    .map(
      (p, i) => `
      <div class="pg ${PG_CLASSES[i]}" data-cursor="view" data-cursor-text="${d.cursor.view}">
        <div class="img" style="--ptint:${PG_TINTS[i % PG_TINTS.length]}">
          <span>${p.t} · ${p.d.split(' ').slice(0, 5).join(' ')}</span>
        </div>
        <div class="body"><span class="t">${p.t}</span><span class="tag">${PG_TAGS_HE[i]}</span></div>
      </div>
    `
    )
    .join('');
}

function renderJournalHe(d) {
  return d.journal.items
    .map(
      ([n, t_, d_, r, slug]) => `
      <a href="../journal/${slug || ''}/" class="j" data-cursor="read">
        <div class="top"><span class="n">${n}</span><span class="meta">${d_}</span></div>
        <h3 class="t">${t_}</h3>
        <div class="row"><span class="read">${r} read</span><span class="arr">↗</span></div>
      </a>
    `
    )
    .join('');
}
