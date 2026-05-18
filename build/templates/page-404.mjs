// =============================================================
// build/templates/page-404.mjs
// -------------------------------------------------------------
// Custom 404 page. Served by the host's 404 handler (Cloudflare
// Pages, Netlify, Vercel all use /404.html by convention).
// Bilingual — links to both EN and HE home.
// =============================================================

export function render404({ siteUrl }) {
  return `<!doctype html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>404 — Not found · David Almoalem</title>
<meta name="description" content="The page you were looking for doesn't exist. Try the homepage or the journal.">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="${siteUrl}/404">

<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#f0ebde" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0c0c09" media="(prefers-color-scheme: dark)">

<link rel="stylesheet" href="/lib/fonts-self-hosted.css">
<link rel="stylesheet" href="/lib/site.css">

<style>
  html, body { background: var(--bg); color: var(--ink); }
  body.page-404 { display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 2rem; box-sizing: border-box; }
  .nf-shell { text-align: center; max-width: 600px; }
  .nf-code { font-family: 'Instrument Serif', serif; font-size: clamp(6rem, 18vw, 12rem); line-height: 1; letter-spacing: -0.04em; margin: 0; opacity: 0.95; }
  .nf-line { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.12em; opacity: 0.5; margin: 1rem 0 0; }
  .nf-msg { font-family: 'Mona Sans', sans-serif; font-weight: 300; font-size: 1.1rem; line-height: 1.5; margin: 2rem auto; max-width: 42ch; opacity: 0.78; }
  .nf-actions { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; margin-top: 2rem; }
  .nf-actions a { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; text-decoration: none; color: inherit; padding: 0.8rem 1.4rem; border: 1px solid color-mix(in srgb, var(--ink) 32%, transparent); transition: background 0.18s ease, color 0.18s ease; }
  .nf-actions a:hover { background: var(--ink); color: var(--bg); }
  .nf-actions a.he { font-family: 'Mona Sans', sans-serif; }
</style>
</head>

<body class="page-404">
  <div class="nf-shell">
    <p class="nf-code">404</p>
    <p class="nf-line">Page not found · עמוד לא נמצא</p>
    <p class="nf-msg">The page you were looking for doesn't exist, was moved, or has been retired. Try the homepage, the work archive, or the journal.</p>
    <div class="nf-actions">
      <a href="/">Home</a>
      <a href="/#work">Work</a>
      <a href="/journal/">Journal</a>
      <a href="/he/" class="he" dir="rtl">לעברית</a>
    </div>
  </div>
</body>
</html>`;
}
