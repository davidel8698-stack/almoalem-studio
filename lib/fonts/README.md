# `lib/fonts/` — self-hosted font binaries

To switch from Google Fonts to self-hosted, drop these five `.woff2` files
into this folder. The CSS in `lib/fonts-self-hosted.css` already references
them. Total weight: ~250 KB.

## Files to download

| Filename here | Source | Direct download |
|---|---|---|
| `JetBrainsMono-VariableFont_wght.woff2` | JetBrains Mono official | https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/webfonts/JetBrainsMono%5Bwght%5D.woff2 |
| `JetBrainsMono-Italic-VariableFont_wght.woff2` | JetBrains Mono official | https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/webfonts/JetBrainsMono-Italic%5Bwght%5D.woff2 |
| `Geist-VariableFont_wght.woff2` | Vercel | https://github.com/vercel/geist-font/raw/main/packages/next/fonts/Geist/woff2/Geist-Variable.woff2 |
| `MonaSans-VariableFont_wdth_wght.woff2` | GitHub Mona Sans | https://github.com/github/mona-sans/raw/main/fonts/webfonts/MonaSans%5Bwdth,wght%5D.woff2 |
| `MonaSans-Italic-VariableFont_wdth_wght.woff2` | GitHub Mona Sans | https://github.com/github/mona-sans/raw/main/fonts/webfonts/MonaSans-Italic%5Bwdth,wght%5D.woff2 |

> The upstream files ship with literal `[` `]` in the filename (e.g.
> `MonaSans[wdth,wght].woff2`). We rename to `MonaSans-VariableFont_wdth_wght.woff2`
> on download because a `<link rel="preload" href>` URL-encodes brackets
> (`%5B…%5D`) while a CSS `url(...)` does not, producing two cache keys for
> the same file and a duplicate font download on every cold load. The
> bracket-free name avoids that gotcha entirely.

## After download — flip the switch

In every HTML file's `<head>`, replace the Google Fonts block:

```html
<!-- before -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=…">
<link href="https://fonts.googleapis.com/css2?family=…" rel="stylesheet">

<!-- after -->
<link rel="preload" as="font" type="font/woff2"
      href="lib/fonts/MonaSans-VariableFont_wdth_wght.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2"
      href="lib/fonts/Geist-VariableFont_wght.woff2" crossorigin>
<link rel="stylesheet" href="lib/fonts-self-hosted.css">
```

The `preload` lines apply to the home page's hero — Mona Sans is the
display face, Geist is the body. JetBrains Mono is preloaded only if
visible above the fold (it isn't on most pages, so omit by default).

## Project pages

Same swap, but paths are one level deeper: `lib/fonts/...` becomes
`../../lib/fonts/...` from `dist/work/<slug>/index.html`. The
`href="../../lib/fonts-self-hosted.css"` form works.

## Why this matters

- Eliminates two third-party DNS lookups (`fonts.googleapis.com`,
  `fonts.gstatic.com`).
- LCP improves by ~50–150 ms on first visit.
- Privacy: removes Google's font-load tracking. GDPR-friendlier.
- Reliability: no dependence on Google's CDN uptime for typography.

## Licensing

All three fonts are OFL-licensed (open). Self-hosting is explicitly
permitted. You don't need to attribute on each page, but please keep
the OFL.txt with each font if redistributing the source.

## After replacing

1. Delete the `<link>`s that point at `fonts.googleapis.com` /
   `fonts.gstatic.com`.
2. Hard-reload (Cmd+Shift+R / Ctrl+Shift+R) to bust the font cache.
3. DevTools → Network → filter by Font → confirm the woff2 files load
   from your own domain and not from gstatic.
