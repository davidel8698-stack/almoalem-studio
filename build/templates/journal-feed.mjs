// =============================================================
// build/templates/journal-feed.mjs
// -------------------------------------------------------------
// RSS 2.0 feed for the journal. Each article published as a full
// <item> with title, link, pubDate, author, and description.
// Output: dist/journal/feed.xml
// =============================================================

const xmlEscape = (s) => String(s ?? '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&apos;');

// "2026-04-08" → "Wed, 08 Apr 2026 00:00:00 GMT" (RFC 822)
function rfc822(isoDate) {
  if (!isoDate) return new Date().toUTCString();
  const d = new Date(isoDate + 'T00:00:00Z');
  if (isNaN(d.getTime())) return new Date().toUTCString();
  return d.toUTCString();
}

export function buildJournalFeed({ articles, journalItems, siteUrl }) {
  const feedUrl = `${siteUrl}/journal/feed.xml`;
  const channelUrl = `${siteUrl}/journal/`;

  // Order matches content.en.json (most recent first by design).
  const items = journalItems.map((row) => {
    const [num, title, date, readTime, slug] = row;
    const article = articles[slug] || {};
    const articleUrl = `${siteUrl}/journal/${slug}/`;
    const isoDate = article.date && /^\d{4}-\d{2}-\d{2}$/.test(article.date)
      ? article.date
      : null;
    const summary = article.subtitle
      || (article.paragraphs && article.paragraphs[0])
      || '';
    return `    <item>
      <title>${xmlEscape(title)}</title>
      <link>${articleUrl}</link>
      <guid isPermaLink="true">${articleUrl}</guid>
      <pubDate>${rfc822(isoDate)}</pubDate>
      <author>hello@almoalem.studio (David Almoalem)</author>
      <category>${xmlEscape(num)}</category>
      <description>${xmlEscape(summary)}</description>
    </item>`;
  }).join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>David Almoalem · Journal</title>
    <link>${channelUrl}</link>
    <atom:link href="${feedUrl}" rel="self" type="application/rss+xml"/>
    <description>Essays on slow work, boring portfolios, and a year of solo client work. By David Almoalem, independent designer and developer in Tel Aviv.</description>
    <language>en</language>
    <copyright>© 2026 David Almoalem</copyright>
    <managingEditor>hello@almoalem.studio (David Almoalem)</managingEditor>
    <webMaster>hello@almoalem.studio (David Almoalem)</webMaster>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <generator>almoalem.studio build pipeline</generator>
    <image>
      <url>${siteUrl}/og.png</url>
      <title>David Almoalem · Journal</title>
      <link>${channelUrl}</link>
    </image>
${items}
  </channel>
</rss>
`;
}
