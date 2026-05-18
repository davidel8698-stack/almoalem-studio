// =============================================================
// build/templates/project-page.mjs
// -------------------------------------------------------------
// Renders a complete per-project HTML page from one case study.
//
// Inputs:  case (one row from data/cases.en.json), allCases (for prev/next),
//          siteUrl (canonical origin), lang ('en' | 'he')
// Output:  full HTML string for dist/work/<slug>/index.html
//
// Key decisions baked in here (see plan):
//   • Slim page — only the project content. No home-page sections,
//     no hero, no work scroller. The page exists to BE the project
//     case study and rank for project-specific queries.
//   • Reuses the same lib/site.css the home page links, so caching is
//     shared. Site brand styles all apply.
//   • Wraps the case content in <div class="detail open is-static">.
//     The .detail descendant CSS in site.css drives the layout; an
//     override at the bottom of this file flips position:fixed off.
//   • Includes per-project <title>, description, canonical, OG,
//     Twitter, AND a JSON-LD `CreativeWork` + `BreadcrumbList`.
//     This is the SEO payload that makes each page individually
//     rankable.
//   • prev/next links at the bottom keep crawlers (and readers)
//     traversing the archive.
// =============================================================

// HTML-safe escape — for any user-facing text injected into attributes
// or content. JSON strings already escaped inside JSON-LD context.
const esc = (s) => String(s ?? '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');

// Project pages live at:
//   dist/work/<slug>/index.html         (EN, depth 2 — REL='../..')
//   dist/he/work/<slug>/index.html      (HE, depth 3 — REL='../../..')
// REL is computed per-language so root-level assets resolve in both.
// Canonical URLs in <link rel="canonical"> and JSON-LD stay ABSOLUTE.
function pickRel(lang) { return lang === 'he' ? '../../..' : '../..'; }

// Pull a clean 155-char snippet for meta description.
function describe(caseStudy) {
  // Prefer a curated SEO description per case (≤160 chars, no truncation).
  // Falls back to the first sentence of the problem statement, then to a
  // word-boundary trim with no ellipsis (cleaner SERP look).
  if (caseStudy.seoDescription) return caseStudy.seoDescription;
  const raw = (caseStudy.problem || '').replace(/\s+/g, ' ').trim();
  if (raw.length <= 155) return raw;
  const trim = raw.slice(0, 155);
  return trim.slice(0, trim.lastIndexOf(' '));   // no ellipsis — Google adds its own
}

// =============================================================
// Per-section rendering
// =============================================================
function renderStats(c) {
  return `
    <div class="stats">
      <div class="st"><span class="k">// Client</span><div class="v">${esc(c.client)}</div></div>
      <div class="st"><span class="k">// Scope</span><div class="v">${esc(c.scope)}</div></div>
      <div class="st"><span class="k">// Role</span><div class="v">${esc(c.role)}</div></div>
      <div class="st"><span class="k">// Year</span><div class="v">${esc(c.year)}</div></div>
    </div>`;
}

function renderOutcome(c) {
  return c.outcome.map((o) => `
      <div class="o">
        <span class="k">${esc(o.k)}</span>
        <span class="v">${esc(o.v)}</span>
      </div>`).join('');
}

function renderSpreads(c) {
  return c.spreads.map((s, n) => `
      <div class="s">
        <span class="n">${String(n + 1).padStart(2, '0')}</span>
        <span>${esc(s)}</span>
      </div>`).join('');
}

function renderStack(c) {
  return c.stack.map((t) => `<span class="pill">${esc(t)}</span>`).join(' ');
}

// =============================================================
// JSON-LD per project — CreativeWork + BreadcrumbList
// Both stand on their own; Google can pick up either independently.
// =============================================================
function renderJsonLd(c, siteUrl, lang) {
  const langPath = lang === 'he' ? '/he' : '';
  const projectUrl = `${siteUrl}${langPath}/work/${c.slug}/`;
  const ldGraph = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'CreativeWork',
        '@id': `${projectUrl}#work`,
        name: `${c.client} — ${c.scope}`,
        url: projectUrl,
        creator: { '@id': `${siteUrl}/#person` },
        about: c.desc,
        datePublished: `${c.year}`,
        inLanguage: lang,
        isPartOf: { '@id': `${siteUrl}/#website` },
        keywords: c.stack.join(', '),
        image: `${siteUrl}/og.png`
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: `${siteUrl}${langPath}/` },
          { '@type': 'ListItem', position: 2, name: 'Work', item: `${siteUrl}${langPath}/#work` },
          { '@type': 'ListItem', position: 3, name: c.client, item: projectUrl }
        ]
      },
      ...(c.quote ? [{
        '@type': 'Review',
        '@id': `${projectUrl}#review`,
        itemReviewed: { '@id': `${projectUrl}#work` },
        reviewBody: c.quote.text,
        author: { '@type': 'Person', name: c.quote.by, jobTitle: c.quote.role }
      }] : [])
    ]
  };
  return `<script type="application/ld+json">\n${JSON.stringify(ldGraph, null, 2)}\n</script>`;
}

// =============================================================
// Master page render
// =============================================================
export function renderProjectPage({ caseStudy, allCases, allProjects, siteUrl, lang }) {
  const c = caseStudy;
  const REL = pickRel(lang);
  // Per-language canonical URLs. Each language version is its own canonical
  // (Google requires unique canonicals per locale); they cross-reference via
  // hreflang siblings so search engines understand they are translations.
  const langPath  = lang === 'he' ? '/he' : '';
  const projectUrl    = `${siteUrl}${langPath}/work/${c.slug}/`;
  const enProjectUrl  = `${siteUrl}/work/${c.slug}/`;
  const heProjectUrl  = `${siteUrl}/he/work/${c.slug}/`;
  const description = describe(c);

  // prev/next via the original project order in content.en.json
  const order = allProjects.map((p) => p.slug);
  const idx = order.indexOf(c.slug);
  const prev = order[(idx - 1 + order.length) % order.length];
  const next = order[(idx + 1) % order.length];
  const prevCase = allCases[prev];
  const nextCase = allCases[next];

  const title = `${c.client} — ${c.scope} · David Almoalem`;

  return `<!doctype html>
<html lang="${lang}" dir="${lang === 'he' ? 'rtl' : 'ltr'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<!-- SEO — primary, project-specific -->
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<meta name="author" content="David Almoalem">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="${projectUrl}">
<link rel="alternate" hreflang="en" href="${enProjectUrl}">
<link rel="alternate" hreflang="he" href="${heProjectUrl}">
<link rel="alternate" hreflang="x-default" href="${enProjectUrl}">

<!-- Geo (consistent with home) -->
<meta name="geo.region" content="IL-TA">
<meta name="geo.placename" content="Tel Aviv">

<!-- Icons / theme -->
<link rel="icon" type="image/svg+xml" href="${REL}/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="${REL}/favicon.png">
<link rel="apple-touch-icon" sizes="180x180" href="${REL}/apple-touch-icon.png">
<link rel="manifest" href="${REL}/site.webmanifest">
<meta name="theme-color" content="#f0ebde" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0c0c09" media="(prefers-color-scheme: dark)">

<!-- Open Graph -->
<meta property="og:type" content="article">
<meta property="og:site_name" content="David Almoalem">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${projectUrl}">
<meta property="og:locale" content="${lang === 'he' ? 'he_IL' : 'en_US'}">
<meta property="og:locale:alternate" content="${lang === 'he' ? 'en_US' : 'he_IL'}">
<meta property="og:image" content="${siteUrl}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="${esc(c.ogImageAlt || c.client + ' — David Almoalem')}">
<meta property="article:author" content="David Almoalem">
<meta property="article:published_time" content="${c.year}-01-01">

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@almoalem">
<meta name="twitter:creator" content="@almoalem">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(description)}">
<meta name="twitter:image" content="${siteUrl}/og.png">

<!-- Prev / next for the project sequence -->
<link rel="prev" href="../${prev}/">
<link rel="next" href="../${next}/">

<!-- Fonts + main stylesheet (self-hosted; shared with home for caching) -->
<link rel="preload" as="font" type="font/woff2" href="${REL}/lib/fonts/MonaSans%5Bwdth,wght%5D.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="${REL}/lib/fonts/Geist-VariableFont_wght.woff2" crossorigin>
<link rel="stylesheet" href="${REL}/lib/fonts-self-hosted.css">
<link rel="stylesheet" href="${REL}/lib/site.css">

<!-- Structured data -->
${renderJsonLd(c, siteUrl, lang)}
</head>

<body class="project-page" data-direction="mono" data-slug="${esc(c.slug)}">

<a href="#main" class="skip-link">Skip to content</a>

<!-- ===================== NAV (slim) ===================== -->
<nav class="nav" id="nav">
  <a href="${REL}/" class="brand" data-cursor="dot">
    <span class="mark mono" aria-hidden="true">DA</span>
    <span>David Almoalem<span class="role"> · Designer / Developer</span></span>
  </a>
  <div class="links">
    <a href="${REL}/#work"><span class="num">01</span>Work</a>
    <a href="${REL}/#about"><span class="num">02</span>About</a>
    <a href="${REL}/#approach"><span class="num">03</span>Approach</a>
    <a href="${REL}/#contact"><span class="num">04</span>Contact</a>
  </div>
  <div class="right">

  </div>
</nav>

<!-- ===================== PROJECT ===================== -->
<main id="main">
<article class="detail open is-static" data-screen-label="${esc(c.id)} ${esc(c.client)}">

  <!-- Close-bar removed for standalone project pages. The site <nav>
       above already supplies brand + section links + "← All work". -->

  <section class="d-hero">
    <div class="top">
      <div class="l">
        <span class="hash">#case / ${esc(c.id)}</span>
        <span class="cap">${esc(c.scope)}</span>
      </div>
      <span class="cap">${esc(c.year)}</span>
    </div>
    <h1>${esc(c.client)}</h1>
    ${renderStats(c)}
  </section>

  <section class="d-cover">
    <div class="ps-placeholder" style="--tint:${esc(c.tint)}">${esc(c.client)} · hero · 21:9</div>
  </section>

  <!-- The brief -->
  <section class="d-body">
    <div class="l">
      <span>— The brief</span>
      <h2>${lang === 'he' ? 'התקציר, בפסקה אחת.' : 'The brief, in one paragraph.'}</h2>
    </div>
    <div class="r"><p>${esc(c.problem)}</p></div>
  </section>

  <!-- The approach -->
  <section class="d-body">
    <div class="l">
      <span>— The approach</span>
      <h2>${lang === 'he' ? 'איך עבדנו.' : 'How we worked.'}</h2>
    </div>
    <div class="r">${c.approach.map((p) => `<p>${esc(p)}</p>`).join('')}</div>
  </section>

  <!-- Outcome -->
  <section class="d-outcome">${renderOutcome(c)}</section>

  <!-- Spreads -->
  <section class="d-body">
    <div class="l">
      <span>— Selected spreads</span>
      <h2>${lang === 'he' ? 'מהסטודיו.' : 'From the studio.'}</h2>
    </div>
    <div class="r d-spreads">${renderSpreads(c)}</div>
  </section>

  <!-- Quote -->
  ${c.quote ? `
  <section class="d-quote">
    <p class="d-quote-text">&ldquo;${esc(c.quote.text)}&rdquo;</p>
    <div class="d-quote-by">
      <span>${esc(c.quote.by)}</span>
      <span class="role">— ${esc(c.quote.role)}</span>
    </div>
  </section>` : ''}

  <!-- Meta -->
  <section class="d-meta-grid">
    <div class="m-block">
      <span class="k">// Timeline</span>
      <span class="v">${esc(c.timeline)}</span>
    </div>
    <div class="m-block">
      <span class="k">// Stack</span>
      <span class="v">${renderStack(c)}</span>
    </div>
    <div class="m-block">
      <span class="k">// What I'd do differently</span>
      <span class="v">${esc(c.rework)}</span>
    </div>
  </section>

  <!-- Gallery placeholders — replaced with real spreads when available -->
  <section class="d-gal">
    <div class="ps-placeholder" style="--tint:${esc(c.tint)}">Spread · 01</div>
    <div class="ps-placeholder" style="--tint:${esc(c.tint)}">Spread · 02</div>
    <div class="ps-placeholder" style="--tint:${esc(c.tint)}">Spread · 03</div>
    <div class="ps-placeholder" style="--tint:${esc(c.tint)}">Spread · 04</div>
  </section>

  <!-- Prev / next -->
  <nav class="d-nav" aria-label="Project pagination">
    <a href="../${esc(prev)}/" data-cursor="view" data-cursor-text="${lang === 'he' ? 'לפרויקט' : 'View'}">
      <span class="k">← Previous</span>
      <span class="v">${esc(prevCase.client)}</span>
    </a>
    <a href="../${esc(next)}/" data-cursor="view" data-cursor-text="${lang === 'he' ? 'לפרויקט' : 'View'}" style="text-align:end">
      <span class="k">Next →</span>
      <span class="v">${esc(nextCase.client)}</span>
    </a>
  </nav>

</article>
</main>

<!-- ===================== FOOTER ===================== -->
<footer class="footer">
  <span class="l">© 2026 David Almoalem · Built carefully, by hand</span>
  <span class="c">Crafted by hand in Tel Aviv · 32.0853° N</span>
  <span class="r">Set in Geist + JetBrains Mono · <b>no analytics</b> · no cookies · plain html</span>
</footer>

<!-- ============================================================
     PROJECT-PAGE LAYOUT OVERRIDE
     The .detail element is normally an overlay (position:fixed,
     translateY hidden). On project pages we flatten it to flow
     inline with the page so the case study IS the page.
     ============================================================ -->
<style>
  body.project-page { background: var(--bg); color: var(--ink); }
  body.project-page .detail.is-static {
    position: static;
    inset: auto;
    transform: none;
    overflow: visible;
    min-height: 0;
  }
  body.project-page main { padding-top: 0; }
  /* close-bar override no longer needed — removed in template */
</style>

<!-- Minimal JS: cursor / smooth-scroll / magnetic / reveal -->
<script src="${REL}/lib/core.js"></script>

</body>
</html>`;
}
