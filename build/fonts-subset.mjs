// =============================================================
// build/fonts-subset.mjs
// -------------------------------------------------------------
// Subsets the self-hosted variable fonts to Latin glyphs only.
//
//   reads  : lib/fonts/src/*.woff2   (pristine upstream originals)
//   writes : lib/fonts/*.woff2       (subset — same filenames)
//
// The site's non-Latin text (Hebrew) is rendered by the system
// "Heebo"/system-ui fallback, NEVER by these faces — so a Latin
// subset is loss-free for every glyph the site actually paints.
//
// Variable axes (wght on all three, plus wdth on Mona Sans) are
// PRESERVED — only unused glyph outlines are dropped. The hero
// per-character `wdth`/`wght` "bulge" animation and the animated
// section numbers keep working pixel-identically.
//
// Run manually (NOT part of `npm run build`):
//     npm run fonts:subset
//
// Re-run only when an upstream font in lib/fonts/src/ changes.
// Dependency: subset-font (devDependency — HarfBuzz-WASM, no Python).
// =============================================================

import { readFile, writeFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import subsetFont from 'subset-font';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const SRC  = join(ROOT, 'lib/fonts/src');
const OUT  = join(ROOT, 'lib/fonts');

// Unicode ranges to KEEP. Generous on purpose — covers all Latin
// scripts, diacritics, punctuation, currency, arrows and symbols
// the UI uses (↗ → — · ‘ ’ “ ” € ™ etc). The byte savings come
// from dropping Cyrillic / Greek / CJK / Hebrew / Arabic and the
// thousands of other glyphs these large variable fonts ship with.
const RANGES = [
  [0x0020, 0x007e], // Basic Latin
  [0x00a0, 0x00ff], // Latin-1 Supplement
  [0x0100, 0x017f], // Latin Extended-A
  [0x0180, 0x024f], // Latin Extended-B
  [0x0250, 0x02af], // IPA Extensions
  [0x02b0, 0x02ff], // Spacing Modifier Letters
  [0x0300, 0x036f], // Combining Diacritical Marks
  [0x1e00, 0x1eff], // Latin Extended Additional
  [0x2000, 0x206f], // General Punctuation
  [0x2070, 0x209f], // Super/Subscripts
  [0x20a0, 0x20bf], // Currency Symbols
  [0x2100, 0x214f], // Letterlike Symbols (™ etc.)
  [0x2150, 0x218f], // Number Forms
  [0x2190, 0x21ff], // Arrows (↗ → ↑ ↓ etc.)
  [0x2200, 0x22ff], // Mathematical Operators (− ∕ etc.)
  [0x2300, 0x23ff], // Miscellaneous Technical
  [0x25a0, 0x25ff], // Geometric Shapes
  [0x2600, 0x26ff], // Miscellaneous Symbols
  [0xfb00, 0xfb06], // Latin ligatures (ﬁ ﬂ)
  [0xfeff, 0xfeff], // Byte Order Mark
  [0xfffd, 0xfffd], // Replacement Character
];

let keep = '';
for (const [a, b] of RANGES) {
  for (let c = a; c <= b; c++) keep += String.fromCodePoint(c);
}

async function run() {
  if (!existsSync(SRC)) {
    console.error(`[fonts:subset] missing ${SRC}`);
    console.error('  Put the pristine upstream .woff2 files in lib/fonts/src/ first.');
    process.exit(1);
  }
  const files = (await readdir(SRC)).filter((f) => f.endsWith('.woff2'));
  if (!files.length) {
    console.error('[fonts:subset] no .woff2 files found in lib/fonts/src/');
    process.exit(1);
  }

  console.log(`── fonts:subset — Latin subset of ${files.length} variable font(s)`);
  let totalBefore = 0;
  let totalAfter = 0;
  for (const f of files) {
    const input = await readFile(join(SRC, f));
    // No `variationAxes` option → all variable axes preserved.
    // No `noLayoutClosure` → GSUB/GPOS features (ss01, calt, case…) kept.
    const out = await subsetFont(input, keep, { targetFormat: 'woff2' });
    await writeFile(join(OUT, f), out);
    totalBefore += input.length;
    totalAfter += out.length;
    const pct = ((1 - out.length / input.length) * 100).toFixed(1);
    console.log(
      `   ${f}: ${(input.length / 1024).toFixed(1)} → ${(out.length / 1024).toFixed(1)} KB (−${pct}%)`
    );
  }
  const pct = ((1 - totalAfter / totalBefore) * 100).toFixed(1);
  console.log(
    `✓  ${files.length} font(s) subset → lib/fonts/  ` +
    `(total ${(totalBefore / 1024).toFixed(0)} → ${(totalAfter / 1024).toFixed(0)} KB, −${pct}%)`
  );
}

run().catch((e) => {
  console.error('[fonts:subset] failed:', e);
  process.exit(1);
});
