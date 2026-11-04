// Screenshot every HTML page in a folder (element #shot) to PNG at 2x.
//   node shoot.cjs images/html images/
const { chromium } = require('playwright');
const { readdirSync, mkdirSync } = require('node:fs');
const { resolve, basename } = require('node:path');

(async () => {
  const src = resolve(process.argv[2] || 'images/html');
  const dst = resolve(process.argv[3] || 'images');
  mkdirSync(dst, { recursive: true });
  const files = readdirSync(src).filter(f => f.endsWith('.html'));
  const browser = await chromium.launch();
  for (const f of files) {
    const page = await browser.newPage({ viewport: { width: 1800, height: 1400 }, deviceScaleFactor: 2 });
    await page.goto('file://' + resolve(src, f), { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    const el = await page.$('#shot');
    const out = resolve(dst, basename(f, '.html') + '.png');
    await el.screenshot({ path: out, type: 'png' });
    const box = await el.boundingBox();
    console.log(basename(out), Math.round(box.width) + 'x' + Math.round(box.height), 'css px');
    await page.close();
  }
  await browser.close();
})();
