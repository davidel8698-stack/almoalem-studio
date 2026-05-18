// =============================================================
// build/templates/jsonld.mjs
// -------------------------------------------------------------
// Builds the full schema.org @graph for the home page in EN or HE.
// Entities:
//   1. Person          — David, canonical (language-independent)
//   2. ProfessionalService — the studio, with hasOfferCatalog
//   3. Service × 4     — detailed offerings, referenceable by @id
//   4. WebSite         — site identity + SearchAction
//   5. ItemList (work) — 6 CreativeWork projects
//   6. ItemList (journal) — Article entries
//   7. Review × 3      — testimonials (no fabricated star ratings)
//   8. BreadcrumbList  — language-aware breadcrumbs
//
// Single source of truth: data/content.<lang>.json
// =============================================================

export const SITE = 'https://almoalem.studio';

// "Apr 2026" → "2026-04" (best-effort)
export function parseDate(s) {
  const months = { jan:'01',feb:'02',mar:'03',apr:'04',may:'05',jun:'06',jul:'07',aug:'08',sep:'09',oct:'10',nov:'11',dec:'12' };
  const m = String(s).match(/(\w{3})[^\d]*(\d{4})/i);
  if (!m) return s;
  const mm = months[m[1].slice(0,3).toLowerCase()];
  return mm ? `${m[2]}-${mm}` : s;
}

export function buildHomeGraph({ langContent, lang }) {
  const isHe = lang === 'he';
  const homeUrl = isHe ? `${SITE}/he/` : `${SITE}/`;
  const c = langContent;

  // -- Person (canonical, language-independent) --
  const person = {
    '@type': 'Person',
    '@id': `${SITE}/#person`,
    name: 'David Almoalem',
    givenName: 'David',
    familyName: 'Almoalem',
    url: `${SITE}/`,
    email: 'mailto:hello@almoalem.studio',
    jobTitle: 'Independent Designer & Developer',
    description:
      'Independent designer and developer based in Tel Aviv. Considered websites and brand identity systems for founders, studios and museums.',
    image: `${SITE}/og.png`,
    address: {
      '@type': 'PostalAddress',
      addressLocality: 'Tel Aviv',
      addressRegion: 'Tel Aviv District',
      addressCountry: 'IL',
    },
    worksFor: { '@id': `${SITE}/#studio` },
    knowsLanguage: ['en', 'he'],
    knowsAbout: [
      'Brand identity design',
      'Website design',
      'Front-end engineering',
      'Design systems',
      'Typography',
      'Art direction',
      'Editorial design',
      'React',
      'Next.js',
      'TypeScript',
    ],
    sameAs: [
      'https://read.cv/almoalem',
      'https://twitter.com/almoalem',
      'https://www.are.na/david-almoalem',
      'https://www.linkedin.com/in/almoalem',
    ],
  };

  // -- 4 detailed Service entities --
  const services = c.services.items.map((s) => ({
    '@type': 'Service',
    '@id': `${SITE}/#service-${s.n}`,
    name: s.t,
    description: s.d,
    provider: { '@id': `${SITE}/#studio` },
    serviceType: s.t,
    areaServed: [
      { '@type': 'Place', name: 'Worldwide' },
      { '@type': 'Country', name: 'Israel' },
    ],
    audience: {
      '@type': 'BusinessAudience',
      name: 'Founders, studios and cultural institutions',
    },
  }));

  // -- ProfessionalService (studio), references Service entities --
  const studio = {
    '@type': 'ProfessionalService',
    '@id': `${SITE}/#studio`,
    name: 'David Almoalem · Studio',
    alternateName: 'Almoalem Studio',
    founder: { '@id': `${SITE}/#person` },
    employee: { '@id': `${SITE}/#person` },
    url: `${SITE}/`,
    email: 'mailto:hello@almoalem.studio',
    image: `${SITE}/og.png`,
    logo: `${SITE}/og.png`,
    description:
      'Independent design and development studio in Tel Aviv. End-to-end brand identity, website design, and front-end engineering for founders, studios and cultural institutions.',
    priceRange: '$$$',
    areaServed: [
      { '@type': 'Place', name: 'Worldwide' },
      { '@type': 'Country', name: 'Israel' },
    ],
    address: { '@type': 'PostalAddress', addressLocality: 'Tel Aviv', addressCountry: 'IL' },
    geo: { '@type': 'GeoCoordinates', latitude: 32.0853, longitude: 34.7818 },
    knowsLanguage: ['en', 'he'],
    hasOfferCatalog: {
      '@type': 'OfferCatalog',
      name: 'Services',
      itemListElement: services.map((s) => ({
        '@type': 'Offer',
        itemOffered: { '@id': s['@id'] },
      })),
    },
    sameAs: [
      'https://read.cv/almoalem',
      'https://twitter.com/almoalem',
      'https://www.are.na/david-almoalem',
    ],
  };

  // -- WebSite --
  const website = {
    '@type': 'WebSite',
    '@id': `${SITE}/#website`,
    url: `${SITE}/`,
    name: 'David Almoalem',
    description:
      'Portfolio of David Almoalem — independent designer and developer in Tel Aviv.',
    publisher: { '@id': `${SITE}/#person` },
    inLanguage: ['en', 'he'],
    potentialAction: {
      '@type': 'SearchAction',
      target: `${SITE}/?q={search_term_string}`,
      'query-input': 'required name=search_term_string',
    },
  };

  // -- ItemList (work) --
  // Language-aware project URLs: HE home points to /he/work/<slug>/, EN home
  // to /work/<slug>/. The canonical @id stays language-independent (CreativeWork
  // identity does not vary by locale).
  const workLangPath = isHe ? '/he' : '';
  const workList = {
    '@type': 'ItemList',
    '@id': `${SITE}/#work`,
    name: c.work.title,
    description: c.work.meta || c.work.title,
    numberOfItems: c.work.projects.length,
    itemListOrder: 'https://schema.org/ItemListOrderDescending',
    itemListElement: c.work.projects.map((p, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      item: {
        '@type': 'CreativeWork',
        '@id': `${SITE}/work/${p.slug}/#work`,
        name: `${p.client} — ${p.scope}`,
        url: `${SITE}${workLangPath}/work/${p.slug}/`,
        creator: { '@id': `${SITE}/#person` },
        about: p.desc,
        datePublished: p.year,
        inLanguage: lang,
        image: `${SITE}/og.png`,
      },
    })),
  };

  // -- ItemList (journal) — Article entries --
  const journalList = {
    '@type': 'ItemList',
    '@id': `${homeUrl}#journal`,
    name: c.journal.title,
    description: c.journal.kicker || 'Writing on slow work',
    numberOfItems: c.journal.items.length,
    itemListElement: c.journal.items.map((row, i) => {
      const [num, title, date, readTime, slug] = row;
      const minutes = parseInt(readTime, 10) || 5;
      return {
        '@type': 'ListItem',
        position: i + 1,
        item: {
          '@type': 'Article',
          '@id': `${SITE}/journal/${slug}/`,
          headline: title,
          alternativeHeadline: num,
          datePublished: parseDate(date),
          author: { '@id': `${SITE}/#person` },
          publisher: { '@id': `${SITE}/#person` },
          url: `${SITE}/journal/${slug}/`,
          wordCount: minutes * 200,
          inLanguage: lang,
          isPartOf: { '@id': `${SITE}/#website` },
        },
      };
    }),
  };

  // -- 3 × Review --
  const reviews = c.testimonials.items.map((t, i) => ({
    '@type': 'Review',
    '@id': `${homeUrl}#review-${i + 1}`,
    itemReviewed: { '@id': `${SITE}/#studio` },
    reviewBody: t.quote,
    author: { '@type': 'Person', name: t.author, jobTitle: t.role },
    inLanguage: lang,
    datePublished: '2026-01-01',
  }));

  // -- BreadcrumbList (language-aware) --
  const crumb = isHe
    ? { home: 'בית', work: 'עבודות', about: 'אודות', approach: 'תהליך', contact: 'צרו קשר' }
    : { home: 'Home', work: 'Work', about: 'About', approach: 'Approach', contact: 'Contact' };
  const breadcrumb = {
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: crumb.home,    item: `${homeUrl}` },
      { '@type': 'ListItem', position: 2, name: crumb.work,    item: `${homeUrl}#work` },
      { '@type': 'ListItem', position: 3, name: crumb.about,   item: `${homeUrl}#about` },
      { '@type': 'ListItem', position: 4, name: crumb.approach,item: `${homeUrl}#approach` },
      { '@type': 'ListItem', position: 5, name: crumb.contact, item: `${homeUrl}#contact` },
    ],
  };

  return {
    '@context': 'https://schema.org',
    '@graph': [
      person,
      studio,
      ...services,
      website,
      workList,
      journalList,
      ...reviews,
      breadcrumb,
    ],
  };
}

// =============================================================
// Image sitemap builder
// =============================================================
const xmlEscape = (s) =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');

function urlBlock({ loc, lastmod, changefreq, priority, hreflang, images }) {
  let xml = `  <url>
    <loc>${loc}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>`;
  for (const h of hreflang || []) {
    xml += `\n    <xhtml:link rel="alternate" hreflang="${h.lang}" href="${h.href}"/>`;
  }
  for (const img of images || []) {
    xml += `\n    <image:image>\n      <image:loc>${img.loc}</image:loc>`;
    if (img.title) xml += `\n      <image:title>${img.title}</image:title>`;
    if (img.caption) xml += `\n      <image:caption>${img.caption}</image:caption>`;
    xml += `\n    </image:image>`;
  }
  return xml + `\n  </url>`;
}

// Accepts an optional `imageExists` predicate (slug → boolean). When provided,
// the per-project hero image is included only if the file is actually on disk.
// Falls back to the homepage OG card otherwise, so the sitemap never lies.
export function buildSitemap({ en, casesEn, articles, imageExists }) {
  const homeHreflang = [
    { lang: 'en', href: `${SITE}/` },
    { lang: 'he', href: `${SITE}/he/` },
    { lang: 'x-default', href: `${SITE}/` },
  ];

  const homes = [
    urlBlock({
      loc: `${SITE}/`,
      lastmod: new Date().toISOString().slice(0, 10),
      changefreq: 'monthly',
      priority: '1.0',
      hreflang: homeHreflang,
      images: [{
        loc: `${SITE}/og.png`,
        title: 'David Almoalem — Independent Designer &amp; Developer',
        caption: 'Considered websites and brand systems for founders, studios and museums. Tel Aviv.',
      }],
    }),
    urlBlock({
      loc: `${SITE}/he/`,
      lastmod: new Date().toISOString().slice(0, 10),
      changefreq: 'monthly',
      priority: '1.0',
      hreflang: homeHreflang,
      images: [{
        loc: `${SITE}/og.png`,
        title: 'דוד אלמועלם — מעצב ומפתח עצמאי',
        caption: 'אתרים מדודים ומערכות מותג לפאונדרים, סטודיואים ומוזיאונים. תל אביב.',
      }],
    }),
  ];

  const projects = en.work.projects.map((p) => {
    const c = casesEn[p.slug];
    // Use the per-project hero image only when the file truly exists on disk
    // (imageExists predicate, optional). Otherwise fall back to the homepage
    // OG card so Google never sees a 404 reference.
    const heroReal = c.imageUrl && (typeof imageExists !== 'function' || imageExists(p.slug));
    const cover = heroReal
      ? { loc: c.imageUrl, title: xmlEscape(`${p.client} — ${p.scope}`), caption: xmlEscape(c.desc) }
      : { loc: `${SITE}/og.png`, title: xmlEscape(`${p.client} — ${p.scope}`), caption: xmlEscape(c.desc) };
    const spreadImages = (c.spreadImages || []).map((url, i) => ({
      loc: url,
      title: xmlEscape(`${p.client} — spread ${i + 1}`),
      caption: xmlEscape(c.spreads[i] || ''),
    }));
    // Per-project hreflang siblings (EN ↔ HE), so each translated case
    // declares its alternate locale explicitly.
    return urlBlock({
      loc: `${SITE}/work/${p.slug}/`,
      lastmod: `${p.year}-12-31`,
      changefreq: 'yearly',
      priority: '0.8',
      hreflang: [
        { lang: 'en', href: `${SITE}/work/${p.slug}/` },
        { lang: 'he', href: `${SITE}/he/work/${p.slug}/` },
        { lang: 'x-default', href: `${SITE}/work/${p.slug}/` },
      ],
      images: [cover, ...spreadImages],
    });
  });

  // -- Journal landing + per-article URLs --
  // Only emit articles that have bodies in journal-articles.en.json.
  const journalBlocks = [];
  if (en.journal && Array.isArray(en.journal.items) && articles) {
    journalBlocks.push(urlBlock({
      loc: `${SITE}/journal/`,
      lastmod: new Date().toISOString().slice(0, 10),
      changefreq: 'monthly',
      priority: '0.9',
      hreflang: [
        { lang: 'en', href: `${SITE}/journal/` },
        { lang: 'he', href: `${SITE}/he/journal/` },
        { lang: 'x-default', href: `${SITE}/journal/` },
      ],
    }));
    for (const row of en.journal.items) {
      const [num, title, date, readTime, slug] = row;
      if (!articles[slug]) continue; // skip article without body
      const a = articles[slug];
      const isoDate = a.date && /^\d{4}-\d{2}-\d{2}$/.test(a.date) ? a.date : null;
      journalBlocks.push(urlBlock({
        loc: `${SITE}/journal/${slug}/`,
        lastmod: isoDate || new Date().toISOString().slice(0, 10),
        changefreq: 'yearly',
        priority: '0.7',
      }));
    }
  }

  return `<?xml version="1.0" encoding="UTF-8"?>
<!--
  sitemap.xml — almoalem.studio
  Home pair (EN + HE) + 6 project pages (EN + HE hreflang siblings)
  + journal landing + per-article URLs. image:image blocks reference
  per-project hero photos when they exist on disk, otherwise fall back
  to the homepage OG card so Google never sees a dangling 404.
-->
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
${homes.join('\n')}
${projects.join('\n')}
${journalBlocks.length ? journalBlocks.join('\n') + '\n' : ''}</urlset>
`;
}
