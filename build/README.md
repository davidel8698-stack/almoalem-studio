# Build pipeline — almoalem.studio

Three layers of source-of-truth, by deliberate design.

## Layer 1 — `data/`
Plain JSON. Single source of truth for **content**.
- `content.en.json` / `content.he.json` — UI strings, projects list, journal items, etc.
- `cases.en.json` / `cases.he.json` — full case studies, per slug, plus `seoDescription` + `ogImageAlt`.
- `journal-articles.en.json` — article bodies (paragraphs).

Edit these to change copy. Run `node build/build.mjs --clean` to propagate.

## Layer 2 — `build/templates/*.mjs`
Pure render functions. Single source of truth for **structure**.
- `partials.mjs` — 10 home-page section renderers (work, about, services, etc.)
- `project-page.mjs` — full project page template (EN + HE — handles depth via `pickRel(lang)`)
- `jsonld.mjs` — schema.org `@graph` builder + image sitemap
- `he-home.mjs` — transforms EN home → HE home (16 documented steps)

Edit these to change layout/structure. Re-run build.

## Layer 3 — `prototypes/mono.html`
The **visual prototype**. Single source of truth for **brand chrome + interactions** (CSS in `<style>`, runtime JS like xray panel, ASK panel, loader, hero animations, cursor).

This file is **manually authored**. The build extracts the inline `<style>` into `lib/site.css` (Phase 1b) and uses the page body as the host for Phase 1 pre-rendering. Inline runtime JS stays.

## Layer 4 — `dist/`
Generated output. **Never edit directly** — run the build.

## Reproducibility
`node build/build.mjs --clean` runs 6 phases:

| Phase | What |
|---|---|
| 0 | Copy + path rewrite + regenerate `lib/content.js` from JSON |
| 1 | Pre-render 10 sections from `data/content.en.json` |
| 1b | Extract inline `<style>` → `lib/site.css` |
| 2 | Emit 6 `/work/<slug>/` pages, patch click handler, write sitemap |
| 3 | Transform EN home → HE home; emit 6 `/he/work/<slug>/` if cases are translated |
| 4 | Inject verification meta, harden `initI18n`, dedupe `<h1>` in overlay |
| 5 | Rebuild JSON-LD with extended schemas, generate image sitemap |

Optional flags: `--clean`, `--phase=N` (stop after phase N).

## Intentional divergences

Some things are deliberately NOT unified across layers, and won't be:

### A. Brand chrome & interactions live ONLY in the prototype
The loader, ASK panel, x-ray mode, help cheat sheet, hero font-axis animation, cursor follower, marquee strips, scroll velocity — all of these live as inline `<style>` and inline `<script>` in `prototypes/mono.html`. They're **not** templated because:
- They're brand expression, not content. Changing them is a design decision, not a data update.
- Templating them would require building a meta-language for animations and panel states. Cost too high vs maintenance ROI.

If you want to tweak the loader or x-ray panel, edit `prototypes/mono.html` directly. The next build will carry the change through.

### B. Inline runtime JS that re-renders sections
The home page has inline `<script>` that re-renders work cards, journal cards, etc. from `window.PORTFOLIO_CONTENT` on first paint. This duplicates what `partials.mjs` produces at build time.

Both must stay in lock-step:
- **Build-time** version (in `partials.mjs`): renders into the initial HTML for crawlers.
- **Runtime** version (in `prototypes/mono.html`): re-renders when the user clicks the language toggle (legacy from before per-language URLs) and for tweak-driven changes.

If you change one, change the other. The current build patches the inline runtime where it can (see `phase2` patches in `build.mjs`).

### C. Asset paths use relative URLs
Every link inside the site uses relative paths (`work/<slug>/`, `../journal/<slug>/`, `../../lib/site.css`). Two reasons:
- The build is **portable** — `dist/` works at any deploy origin (root, subdirectory, sandbox preview).
- Canonical / OG / JSON-LD URLs are **absolute** (use `https://almoalem.studio`) — those are SEO source-of-truth and don't move.

If you change the production origin, update `SITE` constants in `build/build.mjs` and `build/templates/jsonld.mjs`.

### D. Hebrew translations are layered
- UI strings (nav, hero, services, etc.) → `data/content.he.json` ← parity with EN
- Case study bodies → `data/cases.he.json` ← currently AI-drafted, ready for copywriter polish
- Brand chrome strings (footer, x-ray panel chrome) → patched in `he-home.mjs` ← hardcoded HE strings, edit there

There is no `data/chrome.he.json` because the strings are too few to warrant a fourth file.

## Adding a new project
1. Append to `content.en.json.work.projects` and `content.he.json.work.projects` with a new `slug`.
2. Add a new entry to `cases.en.json` and `cases.he.json` with all required fields (`problem`, `approach`, `outcome`, `spreads`, `quote`, `rework`, `timeline`, `stack`, plus `seoDescription` + `ogImageAlt`).
3. Drop a hero image at `dist/images/<slug>-hero.png` (and optionally `<slug>-og.png` if you want a unique OG card).
4. Run `node build/build.mjs --clean`.

The build emits `/work/<slug>/`, `/he/work/<slug>/`, sitemap entries with `image:image`, JSON-LD ItemList updates, prev/next nav between projects.

## Adding a new journal article
1. Append a tuple to `content.en.json.journal.items` and `content.he.json.journal.items`. Both must have a 5th element — the slug.
2. Add the body to `data/journal-articles.en.json` keyed by slug.
3. Run the build.

Journal pages emit at `/journal/<slug>/`. RSS feed at `/journal/feed.xml` regenerates automatically.

## Deploy checklist
- [ ] Replace `https://almoalem.studio` everywhere if domain changes (search `build/templates/`, `build/build.mjs`, `data/`)
- [ ] Replace `REPLACE_WITH_GSC_TOKEN` + `REPLACE_WITH_BING_TOKEN` after verifying in Search Console / Bing Webmaster
- [ ] Replace social handles (`@almoalem`) in JSON-LD `sameAs` arrays (see `build/templates/jsonld.mjs`)
- [ ] Submit `sitemap.xml` to Google Search Console + Bing Webmaster
- [ ] Set up HTTPS, HSTS, compression on the host
- [ ] Confirm `404.html` is served at hosting's 404 handler

## Local development
The dist/ folder is static HTML. Serve it with anything:
```
cd dist && python -m http.server 8000
# or
cd dist && npx serve
```

Or just open `dist/index.html` in a browser — works file:// for inspection (some features like `@font-face` need a server).
