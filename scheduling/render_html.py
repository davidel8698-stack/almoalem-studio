#!/usr/bin/env python3
"""
Build the shareable RTL HTML page of the ג'אנט from the page JSON that
render.py writes.

    python3 render_html.py page-data.json out.html
"""
import json
import sys

TEMPLATE = r"""<title>ג'אנט צוות אלמועלם</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@500;700&family=IBM+Plex+Sans+Hebrew:wght@400;500;600&display=swap">
<style>
/* Layout: one column, a wide scrolling roster grid in the middle; tokens: paper + olive field. */
:root {
  --bg: #f6f3ec;
  --fg: #1f2419;
  --muted: #6b6f60;
  --line: #d9d4c6;
  --card: #fffdf8;
  --accent: #4f6b2f;
  --base: #6a8a3b;
  --base-fg: #ffffff;
  --home: #ece7da;
  --home-fg: #5b5e52;
  --shabbat: #f2e6cf;
  --warn: #b5541c;
  --released: #d7d2c4;
  --display: "Frank Ruhl Libre", "David Libre", "Times New Roman", serif;
  --body: "IBM Plex Sans Hebrew", "Assistant", "Arial Hebrew", Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #161a14; --fg: #ebe8de; --muted: #a3a697; --line: #33392d; --card: #1e241b;
    --accent: #a7c46d; --base: #5f7f36; --base-fg: #f5f7ee; --home: #2a2f26; --home-fg: #b8bbac;
    --shabbat: #2e2a1f; --warn: #e08a4e; --released: #3a3e34; color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #161a14; --fg: #ebe8de; --muted: #a3a697; --line: #33392d; --card: #1e241b;
  --accent: #a7c46d; --base: #5f7f36; --base-fg: #f5f7ee; --home: #2a2f26; --home-fg: #b8bbac;
  --shabbat: #2e2a1f; --warn: #e08a4e; --released: #3a3e34; color-scheme: dark;
}
body { background: var(--bg); color: var(--fg); font-family: var(--body); direction: rtl; font-size: 16px; line-height: 1.55; }
.wrap { max-width: 1100px; margin: 0 auto; padding-block: 28px 56px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
h1 { font-family: var(--display); font-weight: 700; font-size: clamp(30px, 5vw, 44px); line-height: 1.1; margin: 0 0 6px; text-wrap: balance; }
h2 { font-family: var(--display); font-weight: 500; font-size: 24px; margin: 40px 0 12px; text-wrap: balance; }
p { margin: 0 0 10px; max-width: 70ch; }
.sub { color: var(--muted); font-size: 17px; margin-bottom: 18px; }
.facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; margin: 18px 0 8px; }
.fact { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; min-width: 0; }
.fact b { display: block; font-size: 26px; font-family: var(--display); font-weight: 700; line-height: 1.1; font-variant-numeric: tabular-nums; }
.fact span { color: var(--muted); font-size: 14px; }
.legend { display: flex; flex-wrap: wrap; gap: 14px; color: var(--muted); font-size: 14px; margin: 8px 0 10px; align-items: center; }
.legend i { display: inline-block; width: 16px; height: 16px; border-radius: 3px; vertical-align: -3px; margin-left: 5px; border: 1px solid var(--line); }
.scroll { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--card); }
table.grid { border-collapse: separate; border-spacing: 0; font-size: 13px; font-variant-numeric: tabular-nums; min-width: 100%; }
table.grid th, table.grid td { padding: 0; text-align: center; border-bottom: 1px solid var(--line); border-left: 1px solid var(--line); height: 30px; }
table.grid th { font-weight: 500; color: var(--muted); background: var(--card); position: sticky; top: 0; z-index: 2; height: 44px; line-height: 1.15; }
table.grid th.sat, table.grid td.sat { background: var(--shabbat); }
table.grid th.sat { color: var(--warn); }
table.grid td.name, table.grid th.name { position: sticky; right: 0; z-index: 3; background: var(--card); text-align: right; padding: 0 10px; font-weight: 600; white-space: nowrap; min-width: 120px; border-left: 2px solid var(--line); }
table.grid td.name small { color: var(--muted); font-weight: 400; }
table.grid td.day { min-width: 34px; width: 34px; }
table.grid td.b { background: var(--base); color: var(--base-fg); }
table.grid td.b.sat { background: var(--base); box-shadow: inset 0 0 0 2px var(--shabbat); }
table.grid td.h { background: var(--home); color: var(--home-fg); }
table.grid td.x { background: var(--released); color: var(--muted); }
table.grid td.up { border-right: 3px solid var(--fg); }
table.grid td.down { border-right: 3px dashed var(--warn); }
table.grid td.fixed::after { content: "•"; color: var(--warn); font-weight: 700; font-size: 18px; line-height: 0; }
table.grid td.tot, table.grid th.tot { position: sticky; left: 0; z-index: 3; background: var(--card); min-width: 96px; font-weight: 600; border-right: 2px solid var(--line); white-space: nowrap; }
table.grid td.tot small { color: var(--muted); font-weight: 400; }
table.grid tr.david td.day { background: var(--accent); color: var(--base-fg); }
table.grid tr.count td { color: var(--muted); font-size: 12px; height: 26px; background: var(--card); }
table.grid tr.count td.low { color: var(--warn); font-weight: 700; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 14px 16px; min-width: 0; }
.card h3 { margin: 0 0 4px; font-size: 18px; font-weight: 600; display: flex; justify-content: space-between; gap: 8px; align-items: baseline; }
.card h3 span { font-family: var(--display); font-size: 22px; font-variant-numeric: tabular-nums; color: var(--accent); white-space: nowrap; }
.card .meta { color: var(--muted); font-size: 14px; margin-bottom: 8px; }
.card ul { margin: 0; padding: 0; list-style: none; display: grid; gap: 4px; font-size: 15px; }
.card li { display: flex; gap: 8px; align-items: baseline; }
.card li i { width: 10px; height: 10px; border-radius: 2px; flex: none; display: inline-block; position: relative; top: 1px; }
.card li.b i { background: var(--base); } .card li.h i { background: var(--home); border: 1px solid var(--line); }
.card li.r i { background: var(--released); border: 1px solid var(--line); }
.moves { display: grid; gap: 6px; padding: 0; margin: 0; list-style: none; max-width: 70ch; }
.moves li { display: grid; grid-template-columns: 130px 1fr; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--line); }
.moves b { font-variant-numeric: tabular-nums; }
.moves .up::before { content: "עולים: "; color: var(--accent); font-weight: 600; }
.moves .down::before { content: "יורדים: "; color: var(--warn); font-weight: 600; }
.rules { max-width: 70ch; padding-right: 20px; margin: 0; }
.rules li { margin-bottom: 6px; }
.note { background: var(--card); border: 1px solid var(--line); border-right: 4px solid var(--warn); border-radius: 8px; padding: 12px 16px; max-width: 70ch; }
@media (max-width: 480px) {
  .moves li { grid-template-columns: 1fr; gap: 2px; }
  table.grid td.name, table.grid th.name { min-width: 92px; padding: 0 8px; }
}
@media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
</style>
<div class="wrap" lang="he">
  <h1>ג'אנט יציאות – צוות אלמועלם</h1>
  <p class="sub">מעודכן ל-5.11.26 עד הירידה מהקו ב-26.11.26 · כלל 65% במוצב · לפחות 2 מפקדים</p>
  <div class="facts" id="facts"></div>
  <p id="headline"></p>

  <h2>הלוח</h2>
  <div class="legend">
    <span><i style="background:var(--base)"></i>מוצב</span>
    <span><i style="background:var(--home)"></i>בית</span>
    <span><i style="background:var(--shabbat)"></i>שבת</span>
    <span><i style="background:var(--released)"></i>משוחרר</span>
    <span><i style="border-right:3px solid var(--fg);background:transparent"></i>יום עלייה</span>
    <span><i style="border-right:3px dashed var(--warn);background:transparent"></i>יום ירידה</span>
    <span><b style="color:var(--warn)">•</b> אילוץ בית</span>
    <span>★ מפקד</span>
  </div>
  <div class="scroll"><table class="grid" id="grid"></table></div>
  <p class="sub" style="margin-top:8px">יום העלייה נספר כיום מוצב, יום הירידה כיום בית. המניין בשורה התחתונה כולל את דוד. מי שיורד מחכה למחליף שלו (חפיפה).</p>

  <h2>שורה תחתונה לכל לוחם</h2>
  <div class="cards" id="cards"></div>

  <h2>עליות וירידות לפי תאריך</h2>
  <ul class="moves" id="moves"></ul>

  <h2>הכללים שהלוח עומד בהם</h2>
  <ul class="rules" id="rules"></ul>

  <h2>הנחות שצריך לאשר</h2>
  <div class="note" id="assumptions"></div>
</div>
<script>
const DATA = __DATA__;
const CMD = new Set(["IM","AC","EZ"]);
const FIXED = {IM:["17.11"], MA:["8.11"], KA:["19.11"], SG:["19.11"]};
const PRE = {label:"4.11", dow:"ד'", sat:false, pre:true};
const POST = {label:"26.11", dow:"ה'", post:true};
const days = [PRE, ...DATA.days, POST];

function cellState(p, j) {
  const d = days[j];
  if (d.pre) return p.now === null ? "b" : (p.now ? "b" : "h");
  if (d.post) return p.key === "EZ" ? "x" : "exit";
  const i = j - 1;
  if (p.key === "EZ" && d.label.split(".")[0] * 1 >= DATA.ez_exit.split(".")[0] * 1) return "x";
  return p.seq[i] ? "b" : "h";
}

// ---- facts
const nonEz = DATA.people.filter(p => p.key !== "EZ");
const tots = nonEz.map(p => p.total), shs = nonEz.map(p => p.shabbat);
const minT = Math.min(...tots), maxT = Math.max(...tots), minS = Math.min(...shs), maxS = Math.max(...shs);
const ez = DATA.people.find(p => p.key === "EZ");
document.getElementById("facts").innerHTML = [
  ["10 מתוך 14", "במוצב בכל רגע (65% = 9.1, מעוגל למעלה)"],
  ["9 מתוך 13", "אחרי שחרור ערן ב-" + DATA.ez_exit],
  [(minT === maxT ? minT : minT + "–" + maxT) + " / 35", "ימי מוצב לכל לוחם בסוף התעסוקה"],
  [(minS === maxS ? minS : minS + "–" + maxS) + " / 5", "שבתות לכל לוחם"],
].map(([b, s]) => `<div class="fact"><b>${b}</b><span>${s}</span></div>`).join("");
document.getElementById("headline").textContent =
  `כולם מסיימים עם ${minT === maxT ? minT : minT + " עד " + maxT} ימי מוצב מתוך 35 (כולל מה שכבר נעשה מ-22.10) ו-${minS === maxS ? minS : minS + " עד " + maxS} שבתות מתוך 5. ` +
  `ערן, בתעסוקה המקוצרת שלו, מסיים עם ${ez.total} מתוך ${ez.days_total} ימים ו-${ez.shabbat} שבתות.`;

// ---- grid
const grid = document.getElementById("grid");
let html = "<thead><tr><th class='name'>לוחם</th>";
for (const d of days) html += `<th class="${d.sat ? "sat" : ""}">${d.label}<br><small>${d.dow}</small></th>`;
html += "<th class='tot'>סה\"כ</th></tr></thead><tbody>";
html += "<tr class='david'><td class='name'>דוד אלמועלם <small>★</small></td>" + days.map(d => `<td class="day ${d.sat ? "sat" : ""}">${d.post ? "↓" : ""}</td>`).join("") + "<td class='tot'>35 / 35</td></tr>";
for (const p of DATA.people) {
  html += `<tr><td class="name">${p.short} <small>${CMD.has(p.key) ? "★ " : ""}${p.name.replace(p.short, "").trim()}</small></td>`;
  let prev = null;
  days.forEach((d, j) => {
    const st = cellState(p, j);
    const cls = ["day"];
    if (d.sat) cls.push("sat");
    if (st === "b") cls.push("b"); else if (st === "h") cls.push("h"); else if (st === "x") cls.push("x");
    if (!d.pre && !d.post && prev !== null) {
      if (st === "b" && prev === "h") cls.push("up");
      if (st === "h" && prev === "b") cls.push("down");
      if (st === "x" && prev === "b") cls.push("down");
    }
    if ((FIXED[p.key] || []).includes(d.label)) cls.push("fixed");
    let txt = "";
    if (d.post) txt = st === "x" ? "" : "↓";
    html += `<td class="${cls.join(" ")}">${txt}</td>`;
    prev = (st === "exit") ? prev : st;
  });
  html += `<td class="tot">${p.total} / ${p.days_total} <small>· ${p.shabbat} שבתות</small></td></tr>`;
}
// presence row
html += "<tr class='count'><td class='name'>במוצב</td>";
days.forEach((d, j) => {
  if (d.pre) { html += `<td>${1 + DATA.people.filter(p => p.now !== false).length}</td>`; return; }
  if (d.post) { html += "<td>ירידה</td>"; return; }
  const i = j - 1;
  const n = 1 + DATA.people.reduce((a, p) => a + p.seq[i], 0);
  html += `<td class="${n < d.need ? "low" : ""} ${d.sat ? "sat" : ""}">${n}</td>`;
});
html += "<td class='tot'><small>נדרש 10 / 9</small></td></tr></tbody>";
grid.innerHTML = html;

// ---- cards
function stints(seq) {
  const res = []; let cur = seq[0], start = 0;
  for (let i = 1; i < seq.length; i++) if (seq[i] !== cur) { res.push([cur, start, i - 1]); cur = seq[i]; start = i; }
  res.push([cur, start, seq.length - 1]); return res;
}
const cards = document.getElementById("cards");
cards.innerHTML = DATA.people.map(p => {
  let seq = p.seq, items = [];
  if (p.key === "EZ") {
    const cut = DATA.days.findIndex(d => d.label === DATA.ez_exit);
    seq = seq.slice(0, cut);
  }
  const st = stints(seq);
  for (const [s, a, b] of st) {
    const span = a === b ? DATA.days[a].label : `${DATA.days[a].label} עד ${DATA.days[b].label}`;
    items.push(`<li class="${s ? "b" : "h"}"><i></i><span>${s ? "מוצב" : "בית"} ${span} <small style="color:var(--muted)">(${b - a + 1})</small></span></li>`);
  }
  if (p.key === "EZ") items.push(`<li class="r"><i></i><span>סיום התעסוקה המקוצרת ${DATA.ez_exit}</span></li>`);
  const fut = seq.reduce((a, v) => a + v, 0);
  return `<div class="card"><h3>${p.name}${CMD.has(p.key) ? " ★" : ""}<span>${p.total} / ${p.days_total}</span></h3>
    <div class="meta">מוצב עד 4.11: ${p.hist} · מתוכנן מ-5.11: ${fut} · בית סה"כ: ${p.days_total - p.total} · שבתות: ${p.shabbat} מתוך 5</div>
    <ul>${items.join("")}</ul></div>`;
}).join("");

// ---- moves
document.getElementById("moves").innerHTML = DATA.moves.map(m =>
  `<li><b>${m.date} (${m.dow})</b><div>${m.up.length ? `<div class="up">${m.up.join(", ")}</div>` : ""}${m.down.length ? `<div class="down">${m.down.join(", ")}</div>` : ""}</div></li>`
).join("");

// ---- rules
document.getElementById("rules").innerHTML = [
  "<b>65% מהצוות במוצב בכל רגע:</b> 65% מ-14 = 9.1, כלומר 10 במוצב (כולל דוד, ואילן בימי המשמרת שלו). אחרי שחרור ערן הצוות הוא 13, 65% מ-13 = 8.45, כלומר 9.",
  "<b>לפחות 2 מפקדים במוצב:</b> דוד תמיד, ובנוסף לפחות אחד מבין איתי / אביאל / ערן.",
  "<b>אילוצים:</b> איתי בבית ב-17.11, מרדכי בבית ב-8.11, קיאן וסייף בבית ב-19.11.",
  "<b>זוגות:</b> עלי ורפאת תמיד יחד, קיאן וסייף תמיד יחד.",
  "<b>אין עליות או ירידות בשבת.</b> מי שבמוצב בשישי סוגר את השבת.",
  `<b>רצפים:</b> לפחות ${DATA.params.min_base} ימי מוצב ברצף, לפחות ${DATA.params.min_home} ימי בית ברצף (חוץ מבית עד סוף התעסוקה), לא יותר מ-${DATA.params.max_base} ימי מוצב ברצף.`,
  "<b>לא פוגעים במה שכבר הובטח:</b> מי שבמוצב עכשיו לא יורד לפני תאריך היציאה שתוכנן לו. חלקם נשארים יותר, וזה מתקזז בהמשך כך שכולם מסיימים שווה.",
  "<b>איזון:</b> הלוח נבחר כך שסך ימי המוצב של כל לוחם על פני כל התעסוקה (22.10 עד 25.11) שווה ככל האפשר, וכך גם השבתות, בלי ימי מוצב מיותרים מעבר לכלל.",
].map(s => `<li>${s}</li>`).join("");

document.getElementById("assumptions").innerHTML = `<p style="margin:0 0 6px"><b>הלוח בנוי על ההנחות הבאות. אם אחת מהן לא נכונה, מריצים שוב ומקבלים לוח מעודכן:</b></p>
<ol style="margin:0;padding-right:20px">
<li>דוד במוצב לאורך כל התעסוקה ונספר במניין.</li>
<li>סייף בבית עכשיו יחד עם קיאן (לא הופיע ברשימת "בבית").</li>
<li>ערן משתחרר ב-${DATA.ez_exit} (26.11 פחות שבועיים). אם התאריך אחר, הלוח שלו ושל המפקדים זז.</li>
<li>אילן נספר במניין ה-65% בימי המשמרת שלו, ומקבל אותו יחס כמו כולם. אם הוא לא נספר, כל אחד מפסיד בערך יום בית.</li>
<li>ה-65% מחושב מכלל הצוות (14) ומעוגל למעלה. אם 9 מתוך 14 מקובל, כולם מרוויחים יום בית.</li>
<li>הצורך יורד ל-9 אחרי שחרור ערן. אם צריך 10 גם אז, כל אחד מפסיד בערך יום בית.</li>
<li>מי שבבית ב-25.11 מגיע ישירות לירידה/שחרור ב-26.11, לפי מה שתחליט.</li>
</ol>`;
</script>
"""


def main(src, dst):
    data = json.load(open(src, encoding="utf-8"))
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    with open(dst, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {dst} ({len(html)} bytes)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
