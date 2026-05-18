// =============================================================
// build/templates/journal-page.mjs
// -------------------------------------------------------------
// Renders:
//   (a) Journal landing page → dist/journal/index.html
//   (b) Per-article pages    → dist/journal/<slug>/index.html
//
// Inputs read from:
//   data/content.<lang>.json  (journal.items = list of [num, title, date, readTime, slug])
//   data/journal-articles.en.json (body paragraphs per slug)
//
// EN only at the moment — Hebrew journal item titles exist in content.he.json
// but article bodies don't, so we only emit EN article pages. HE journal
// landing reuses the EN articles list with HE chrome.
// =============================================================

const esc = (s) => String(s ?? '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');

// Same-shape REL helpers as project-page.mjs.
function landingRel(lang) { return lang === 'he' ? '../..' : '..'; }
function articleRel(lang) { return lang === 'he' ? '../../..' : '../..'; }

// =============================================================
// (a) Landing page — list of all articles
// =============================================================
export function renderJournalLanding({ content, siteUrl, lang }) {
  const REL = landingRel(lang);
  const isHe = lang === 'he';
  const landingUrl = `${siteUrl}${isHe ? '/he' : ''}/journal/`;
  const enLandingUrl = `${siteUrl}/journal/`;
  const heLandingUrl = `${siteUrl}/he/journal/`;

  const title = isHe
    ? 'יומן · דוד אלמועלם'
    : 'Journal · David Almoalem';
  const description = isHe
    ? 'מאמרים על עבודה איטית, פורטפוליו משעמם, ושנה של לקוחות עצמאיים. דוד אלמועלם.'
    : 'Essays on slow work, boring portfolios, and a year of solo client work. David Almoalem.';

  // Render article cards from journal.items (5-tuple shape).
  const cards = content.journal.items.map((row) => {
    const [num, articleTitle, date, readTime, slug] = row;
    return `
      <li class="j-card">
        <a href="${esc(slug)}/" data-cursor="view">
          <span class="num">${esc(num)}</span>
          <h2 class="ttl">${esc(articleTitle)}</h2>
          <div class="meta">
            <span>${esc(date)}</span>
            <span class="dot" aria-hidden="true">·</span>
            <span>${esc(readTime)}</span>
          </div>
        </a>
      </li>`;
  }).join('');

  // Minimal JSON-LD — Blog + CollectionPage with author reference.
  const jsonLd = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'CollectionPage',
        '@id': `${landingUrl}#page`,
        url: landingUrl,
        name: title,
        description,
        inLanguage: lang,
        isPartOf: { '@id': `${siteUrl}/#website` },
        about: { '@id': `${siteUrl}/#person` },
      },
      {
        '@type': 'Blog',
        '@id': `${siteUrl}/#blog`,
        name: isHe ? 'יומן דוד אלמועלם' : 'David Almoalem Journal',
        url: landingUrl,
        author: { '@id': `${siteUrl}/#person` },
        publisher: { '@id': `${siteUrl}/#person` },
        inLanguage: lang,
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: isHe ? 'בית' : 'Home', item: `${siteUrl}${isHe ? '/he' : ''}/` },
          { '@type': 'ListItem', position: 2, name: isHe ? 'יומן' : 'Journal', item: landingUrl },
        ],
      },
    ],
  };

  return `<!doctype html>
<html lang="${lang}" dir="${isHe ? 'rtl' : 'ltr'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<meta name="author" content="David Almoalem">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="${landingUrl}">
<link rel="alternate" hreflang="en" href="${enLandingUrl}">
<link rel="alternate" hreflang="he" href="${heLandingUrl}">
<link rel="alternate" hreflang="x-default" href="${enLandingUrl}">
<link rel="alternate" type="application/rss+xml" title="${esc(title)}" href="${REL}/journal/feed.xml">

<meta name="geo.region" content="IL-TA">
<meta name="geo.placename" content="Tel Aviv">

<link rel="icon" type="image/svg+xml" href="${REL}/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="${REL}/favicon.png">
<link rel="apple-touch-icon" sizes="180x180" href="${REL}/apple-touch-icon.png">
<link rel="manifest" href="${REL}/site.webmanifest">
<meta name="theme-color" content="#f0ebde" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0c0c09" media="(prefers-color-scheme: dark)">

<meta property="og:type" content="website">
<meta property="og:site_name" content="David Almoalem">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${landingUrl}">
<meta property="og:locale" content="${isHe ? 'he_IL' : 'en_US'}">
<meta property="og:locale:alternate" content="${isHe ? 'en_US' : 'he_IL'}">
<meta property="og:image" content="${siteUrl}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@almoalem">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(description)}">
<meta name="twitter:image" content="${siteUrl}/og.png">

<link rel="preload" as="font" type="font/woff2" href="${REL}/lib/fonts/MonaSans%5Bwdth,wght%5D.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="${REL}/lib/fonts/Geist-VariableFont_wght.woff2" crossorigin>
<link rel="stylesheet" href="${REL}/lib/fonts-self-hosted.css">
<link rel="stylesheet" href="${REL}/lib/site.css">

<script type="application/ld+json">
${JSON.stringify(jsonLd, null, 2)}
</script>

<style>
  body.journal-landing { background: var(--bg); color: var(--ink); padding-bottom: 4rem; }
  .journal-page-shell { max-width: 980px; margin: 0 auto; padding: 4rem 2rem 2rem; }
  .journal-page-shell .hd { display: flex; align-items: baseline; justify-content: space-between; gap: 2rem; margin-bottom: 4rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--ink); }
  .journal-page-shell .hd h1 { font-family: 'Mona Sans', sans-serif; font-weight: 700; font-size: clamp(2.5rem, 6vw, 4.5rem); letter-spacing: -0.025em; line-height: 1; margin: 0; }
  .journal-page-shell .hd .kicker { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.6; }
  .j-grid { list-style: none; margin: 0; padding: 0; display: grid; gap: 0; border-top: 1px solid color-mix(in srgb, var(--ink) 18%, transparent); }
  .j-card { border-bottom: 1px solid color-mix(in srgb, var(--ink) 18%, transparent); }
  .j-card a { display: grid; grid-template-columns: 6ch 1fr auto; align-items: baseline; gap: 2rem; padding: 1.6rem 0; color: inherit; text-decoration: none; transition: padding 0.18s ease; }
  .j-card a:hover { padding-inline-start: 1rem; }
  .j-card .num { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; opacity: 0.55; letter-spacing: 0.05em; }
  .j-card .ttl { font-family: 'Instrument Serif', 'Mona Sans', serif; font-weight: 400; font-size: clamp(1.4rem, 2.6vw, 1.9rem); line-height: 1.15; margin: 0; max-width: 60ch; }
  .j-card .meta { font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; opacity: 0.6; display: flex; gap: 0.5rem; align-items: center; white-space: nowrap; }
  .j-card .meta .dot { opacity: 0.4; }
  .back-link { display: inline-flex; align-items: center; gap: 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; opacity: 0.7; text-decoration: none; color: inherit; margin-top: 3rem; }
  .back-link:hover { opacity: 1; }
  [dir="rtl"] .j-card a:hover { padding-inline-start: 0; padding-inline-end: 1rem; }
</style>
</head>

<body class="journal-landing" data-direction="mono">
<a href="#main" class="skip-link">Skip to content</a>

<nav class="nav" id="nav">
  <a href="${REL}/" class="brand" data-cursor="dot">
    <span class="mark mono" aria-hidden="true">DA</span>
    <span>David Almoalem<span class="role"> · Designer / Developer</span></span>
  </a>
  <div class="links">
    <a href="${REL}/#work"><span class="num">01</span>${isHe ? 'עבודות' : 'Work'}</a>
    <a href="${REL}/#about"><span class="num">02</span>${isHe ? 'אודות' : 'About'}</a>
    <a href="${REL}/#approach"><span class="num">03</span>${isHe ? 'תהליך' : 'Approach'}</a>
    <a href="${REL}/#contact"><span class="num">04</span>${isHe ? 'קשר' : 'Contact'}</a>
  </div>
  <div class="right"></div>
</nav>

<main id="main" class="journal-page-shell">
  <header class="hd">
    <h1>${esc(content.journal.title)}</h1>
    <span class="kicker">${esc(content.journal.kicker || '')}</span>
  </header>

  <ul class="j-grid">${cards}
  </ul>

  <a class="back-link" href="${REL}/">${isHe ? '← לעמוד הבית' : '← Back to home'}</a>
</main>

<footer class="footer">
  <span class="l">© 2026 David Almoalem · ${isHe ? 'נבנה בקפידה, ביד' : 'Built carefully, by hand'}</span>
  <span class="c">${isHe ? 'נוצר ביד בתל אביב' : 'Crafted by hand in Tel Aviv'} · 32.0853° N</span>
  <span class="r">Set in Geist + JetBrains Mono · <b>no analytics</b> · no cookies · plain html</span>
</footer>

<script src="${REL}/lib/core.js"></script>
</body>
</html>`;
}

// =============================================================
// (b) Per-article page — full body content
// =============================================================
export function renderJournalArticle({ article, slug, content, siteUrl, prevSlug, nextSlug }) {
  const REL = articleRel('en'); // EN articles only
  const articleUrl = `${siteUrl}/journal/${slug}/`;

  // Build prev/next labels from journal.items in content.en.json.
  const itemBySlug = Object.fromEntries(content.journal.items.map((row) => [row[4], row]));
  const prevItem = prevSlug ? itemBySlug[prevSlug] : null;
  const nextItem = nextSlug ? itemBySlug[nextSlug] : null;

  const isoDate = (article.date && /^\d{4}-\d{2}-\d{2}$/.test(article.date))
    ? article.date
    : new Date().toISOString().slice(0, 10);

  const description = article.subtitle || (article.paragraphs && article.paragraphs[0] && article.paragraphs[0].slice(0, 155)) || '';
  const wordCount = (article.paragraphs || []).reduce((n, p) => n + p.split(/\s+/).length, 0);

  const paragraphs = (article.paragraphs || []).map((p) => `<p>${esc(p)}</p>`).join('\n      ');

  const jsonLd = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Article',
        '@id': `${articleUrl}#article`,
        headline: article.title,
        alternativeHeadline: article.eyebrow,
        description,
        datePublished: isoDate,
        dateModified: isoDate,
        author: { '@id': `${siteUrl}/#person` },
        publisher: { '@id': `${siteUrl}/#person` },
        url: articleUrl,
        mainEntityOfPage: articleUrl,
        wordCount,
        inLanguage: 'en',
        isPartOf: { '@id': `${siteUrl}/#blog` },
        image: `${siteUrl}/og.png`,
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home',    item: `${siteUrl}/` },
          { '@type': 'ListItem', position: 2, name: 'Journal', item: `${siteUrl}/journal/` },
          { '@type': 'ListItem', position: 3, name: article.title, item: articleUrl },
        ],
      },
    ],
  };

  const title = `${article.title} · David Almoalem`;

  return `<!doctype html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<meta name="author" content="David Almoalem">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="${articleUrl}">
<link rel="alternate" type="application/rss+xml" title="David Almoalem · Journal" href="${REL}/journal/feed.xml">

<meta name="geo.region" content="IL-TA">
<meta name="geo.placename" content="Tel Aviv">

<link rel="icon" type="image/svg+xml" href="${REL}/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="${REL}/favicon.png">
<link rel="apple-touch-icon" sizes="180x180" href="${REL}/apple-touch-icon.png">
<link rel="manifest" href="${REL}/site.webmanifest">
<meta name="theme-color" content="#f0ebde" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0c0c09" media="(prefers-color-scheme: dark)">

<meta property="og:type" content="article">
<meta property="og:site_name" content="David Almoalem">
<meta property="og:title" content="${esc(article.title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${articleUrl}">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="${siteUrl}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="article:author" content="David Almoalem">
<meta property="article:published_time" content="${isoDate}">
<meta property="article:section" content="Journal">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@almoalem">
<meta name="twitter:creator" content="@almoalem">
<meta name="twitter:title" content="${esc(article.title)}">
<meta name="twitter:description" content="${esc(description)}">
<meta name="twitter:image" content="${siteUrl}/og.png">

${prevItem ? `<link rel="prev" href="../${esc(prevSlug)}/">` : ''}
${nextItem ? `<link rel="next" href="../${esc(nextSlug)}/">` : ''}

<link rel="preload" as="font" type="font/woff2" href="${REL}/lib/fonts/MonaSans%5Bwdth,wght%5D.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="${REL}/lib/fonts/Geist-VariableFont_wght.woff2" crossorigin>
<link rel="stylesheet" href="${REL}/lib/fonts-self-hosted.css">
<link rel="stylesheet" href="${REL}/lib/site.css">

<script type="application/ld+json">
${JSON.stringify(jsonLd, null, 2)}
</script>

<style>
  body.journal-article { background: var(--bg); color: var(--ink); padding-bottom: 6rem; }
  .article-shell { max-width: 680px; margin: 0 auto; padding: 4rem 2rem 2rem; }
  .article-shell .eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.6; }
  .article-shell h1 { font-family: 'Instrument Serif', 'Mona Sans', serif; font-weight: 400; font-size: clamp(2.4rem, 5vw, 3.6rem); line-height: 1.1; letter-spacing: -0.01em; margin: 1rem 0 1.4rem; }
  .article-shell .subtitle { font-family: 'Mona Sans', sans-serif; font-weight: 300; font-size: 1.2rem; line-height: 1.4; opacity: 0.78; margin: 0 0 2.4rem; }
  .article-shell .meta-row { display: flex; gap: 1rem; align-items: center; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; opacity: 0.6; margin-bottom: 3rem; padding-bottom: 1.5rem; border-bottom: 1px solid color-mix(in srgb, var(--ink) 18%, transparent); }
  .article-shell .body { font-family: 'Mona Sans', sans-serif; font-size: 1.06rem; line-height: 1.7; }
  .article-shell .body p { margin: 0 0 1.4rem; }
  .article-shell .body p:first-of-type::first-letter { font-family: 'Instrument Serif', serif; font-size: 3.6rem; line-height: 0.9; float: left; padding: 0.3rem 0.4rem 0 0; }
  .article-nav { display: flex; justify-content: space-between; gap: 2rem; margin-top: 4rem; padding-top: 1.5rem; border-top: 1px solid color-mix(in srgb, var(--ink) 18%, transparent); font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; }
  .article-nav a { color: inherit; text-decoration: none; display: flex; flex-direction: column; gap: 0.4rem; }
  .article-nav a .k { opacity: 0.55; font-size: 0.72rem; }
  .article-nav a .v { font-family: 'Instrument Serif', serif; font-size: 1.1rem; max-width: 28ch; }
  .article-nav a:hover .v { text-decoration: underline; text-underline-offset: 0.25em; }
  .back-to-journal { display: inline-flex; align-items: center; gap: 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; opacity: 0.7; text-decoration: none; color: inherit; margin-top: 3rem; }
  .back-to-journal:hover { opacity: 1; }
</style>
</head>

<body class="journal-article" data-direction="mono">
<a href="#main" class="skip-link">Skip to content</a>

<nav class="nav" id="nav">
  <a href="${REL}/" class="brand" data-cursor="dot">
    <span class="mark mono" aria-hidden="true">DA</span>
    <span>David Almoalem<span class="role"> · Designer / Developer</span></span>
  </a>
  <div class="links">
    <a href="${REL}/#work"><span class="num">01</span>Work</a>
    <a href="${REL}/journal/"><span class="num">02</span>Journal</a>
    <a href="${REL}/#about"><span class="num">03</span>About</a>
    <a href="${REL}/#contact"><span class="num">04</span>Contact</a>
  </div>
  <div class="right"></div>
</nav>

<main id="main">
  <article class="article-shell">
    <span class="eyebrow">${esc(article.eyebrow || '')}</span>
    <h1>${esc(article.title)}</h1>
    ${article.subtitle ? `<p class="subtitle">${esc(article.subtitle)}</p>` : ''}
    <div class="meta-row">
      <time datetime="${isoDate}">${esc(article.date || '')}</time>
      <span class="dot" aria-hidden="true">·</span>
      <span>${esc(article.readMin ? article.readMin + ' min read' : '')}</span>
    </div>

    <div class="body">
      ${paragraphs}
    </div>

    <nav class="article-nav" aria-label="Article pagination">
      ${prevItem ? `<a href="../${esc(prevSlug)}/" data-cursor="view"><span class="k">← Previous</span><span class="v">${esc(prevItem[1])}</span></a>` : '<span></span>'}
      ${nextItem ? `<a href="../${esc(nextSlug)}/" data-cursor="view" style="text-align:end"><span class="k">Next →</span><span class="v">${esc(nextItem[1])}</span></a>` : '<span></span>'}
    </nav>

    <a class="back-to-journal" href="../">← Back to journal</a>
  </article>
</main>

<footer class="footer">
  <span class="l">© 2026 David Almoalem · Built carefully, by hand</span>
  <span class="c">Crafted by hand in Tel Aviv · 32.0853° N</span>
  <span class="r">Set in Geist + JetBrains Mono · <b>no analytics</b> · no cookies · plain html</span>
</footer>

<script src="${REL}/lib/core.js"></script>
</body>
</html>`;
}
