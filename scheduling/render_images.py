#!/usr/bin/env python3
"""
Build WhatsApp-ready images of the ג'אנט: one team grid plus one personal
card per soldier.  Writes HTML pages, then shoot.mjs screenshots them.

    python3 render_images.py janet.json images/      # writes images/html/*.html
    node shoot.cjs images/html images/               # screenshots them to images/*.png
"""
import argparse
import datetime as dt
import json
import os

from render import (CMD, HEB_DOW, HEB_DOW_LONG, ORDER, PROMISED, SHORT, SINCE, START, EXIT, fmt, stints)

FIXED = {"IM": ["17.11"], "MA": ["8.11"], "KA": ["19.11"], "SG": ["19.11"], "LE": ["5.11", "6.11"]}


def css(font_dir):
    face = ""
    if font_dir:
        for w in (400, 700, 900):
            face += f'@font-face {{ font-family: "Heebo"; src: url("file://{font_dir}/Heebo-{w}.ttf"); font-weight: {w}; }}\n'
    return face + """
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #f6f3ec; }
body { font-family: "Heebo", "DejaVu Sans", "Arial Hebrew", Arial, sans-serif; color: #1f2419; direction: rtl; -webkit-font-smoothing: antialiased; }
.page { background: #f6f3ec; padding: 36px 40px; }
h1 { margin: 0; font-size: 44px; font-weight: 900; line-height: 1.1; }
.sub { font-size: 24px; color: #5b5e52; margin: 8px 0 22px; font-weight: 500; }
table { border-collapse: separate; border-spacing: 0; width: 100%; table-layout: fixed; }
th, td { text-align: center; padding: 0; height: 46px; font-weight: 700; font-size: 18px; border-bottom: 2px solid #f6f3ec; }
th { height: 62px; font-size: 19px; color: #3d4036; line-height: 1.05; background: #e9e4d6; border-bottom: 3px solid #cfc9b8; }
th.sat { background: #f3d99a; color: #6b4a00; }
th.name, td.name { width: 230px; text-align: right; padding-right: 14px; font-size: 24px; background: #f6f3ec; }
td.name small { font-size: 16px; color: #6b6f60; font-weight: 500; }
th.tot, td.tot { width: 96px; font-size: 17px; background: #f6f3ec; color: #3d4036; }
td.tot { font-size: 30px; font-weight: 900; }
td.tot.tb { color: #2e6a2a; background: #dfe9d0; border-right: 4px solid #f6f3ec; }
td.tot.th { color: #7a5a1c; background: #efe6cf; }
td.tot.ts { font-size: 18px; font-weight: 700; width: 90px; color: #6b4a00; }
th.tot.ts { width: 90px; }
tr.count td.tot { font-size: 15px; font-weight: 500; background: #f6f3ec; }
td.b { background: #3f7f3a; color: #fff; }
td.h { background: #ece6d6; color: #8a8572; }
td.x { background: #d9d4c6; color: #8a8572; }
td.sat { box-shadow: inset 0 0 0 3px #f3d99a; }
td.b.sat { box-shadow: inset 0 0 0 3px #f3d99a; }
td.up, td.down { font-size: 15px; letter-spacing: -0.3px; }
td.up { background: #2e6a2a; }
td.down { background: #d9cfa8; color: #4a3c14; }
td.dot::after { content: " ●"; color: #e0a020; font-size: 14px; }
tr.david td.b { background: #5f8f3b; }
tr.count td { height: 40px; background: #f6f3ec; color: #5b5e52; font-size: 17px; }
tr.count td.name { font-size: 18px; }
.legend { display: flex; gap: 34px; margin-top: 22px; font-size: 20px; color: #3d4036; align-items: center; flex-wrap: wrap; }
.legend i { display: inline-block; width: 30px; height: 24px; vertical-align: -5px; margin-left: 8px; border-radius: 4px; }
.notes { margin-top: 14px; font-size: 19px; color: #5b5e52; line-height: 1.5; }

/* personal card */
.card { width: 1080px; min-height: 1350px; background: #f6f3ec; padding: 0; display: flex; flex-direction: column; }
.band { background: #2e6a2a; color: #fff; padding: 22px 48px; font-size: 26px; font-weight: 700; display: flex; justify-content: space-between; }
.card .body { padding: 36px 48px; display: flex; flex-direction: column; gap: 26px; flex: 1; }
.card h1 { font-size: 64px; }
.card .role { font-size: 28px; color: #5b5e52; font-weight: 500; }
.strip { display: grid; grid-template-columns: repeat(22, 1fr); gap: 3px; }
.strip div { height: 54px; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 700; border-radius: 4px; }
.strip .b { background: #3f7f3a; color: #fff; } .strip .h { background: #e3ddcb; color: #8a8572; } .strip .x { background: #d9d4c6; color: #8a8572; }
.strip .sat { box-shadow: inset 0 0 0 3px #f3d99a; }
.strip .ex { background: #cfc9b8; color: #3d4036; font-size: 16px; }
.striplbl { display: grid; grid-template-columns: repeat(22, 1fr); gap: 3px; font-size: 15px; color: #6b6f60; text-align: center; margin-top: -18px; }
.moves { display: flex; flex-direction: column; gap: 14px; }
.mv { display: flex; align-items: center; gap: 22px; background: #fffdf8; border: 2px solid #ddd7c6; border-radius: 12px; padding: 16px 24px; font-size: 34px; font-weight: 700; }
.mv .ico { width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 34px; color: #fff; flex: none; }
.mv.up .ico { background: #3f7f3a; } .mv.down .ico { background: #b5541c; } .mv.end .ico { background: #6b6f60; }
.mv small { font-size: 24px; color: #6b6f60; font-weight: 500; margin-right: auto; }
.totals { background: #fffdf8; border: 3px solid #2e6a2a; border-radius: 14px; padding: 18px 24px; }
.totals .lbl { font-size: 22px; color: #5b5e52; font-weight: 500; margin-bottom: 10px; }
.totals .nums { display: flex; justify-content: space-between; align-items: baseline; }
.totals .n { font-size: 30px; font-weight: 700; }
.totals .n b { font-size: 64px; font-weight: 900; line-height: 1; }
.totals .n.b { color: #2e6a2a; } .totals .n.h { color: #7a5a1c; }
.totals .bar { display: flex; height: 26px; border-radius: 8px; overflow: hidden; margin-top: 10px; }
.totals .bar i { display: block; height: 100%; }
.totals .bar .b { background: #3f7f3a; } .totals .bar .h { background: #e0d5b4; }
.facts { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.fact { background: #fffdf8; border: 2px solid #ddd7c6; border-radius: 12px; padding: 12px; text-align: center; }
.fact b { display: block; font-size: 40px; font-weight: 900; color: #2e6a2a; line-height: 1.1; }
.fact span { font-size: 22px; color: #5b5e52; }
.foot { margin-top: auto; background: #e9e4d6; color: #3d4036; padding: 18px 48px; font-size: 22px; line-height: 1.45; }
.shab { font-size: 28px; }
.shab b { color: #6b4a00; }
"""


def build(src, outdir, font_url):
    out = json.load(open(src, encoding="utf-8"))
    S = out["schedule"]
    days = [dt.date.fromisoformat(d) for d in out["days"]]
    N = len(days)
    names = out["names"]
    ez_exit = dt.date.fromisoformat(out["ez_exit"])
    ez_cut = days.index(ez_exit)
    on_now = dict(out["on_base_now"]); on_now["IS"] = True
    need = out["need"]
    sat = [i for i, d in enumerate(days) if d.weekday() == 5]
    os.makedirs(outdir, exist_ok=True)
    today = dt.date(2026, 11, 4)

    def seq_of(p):
        return S[p][:ez_cut] if p == "EZ" else S[p]

    def state(p, i):
        if p == "EZ" and i >= ez_cut:
            return "x"
        return "b" if S[p][i] else "h"

    def moves_of(p):
        seq = seq_of(p)
        mv, prev = [], (1 if on_now[p] else 0)
        for i, v in enumerate(seq):
            if v != prev:
                mv.append((days[i], "up" if v else "down"))
            prev = v
        if p == "EZ":
            if seq[-1] == 1:
                mv.append((ez_exit, "end"))
            else:
                mv[-1] = (mv[-1][0], "end")
        elif seq[-1] == 1:
            mv.append((EXIT, "exit"))
        return mv

    # ------------------------------------------------------------------ grid
    H = ['<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>' + css(font_url) + '</style></head><body>']
    H.append('<div class="page" id="shot" style="width:1760px">')
    H.append('<h1>ג\'אנט יציאות – צוות אלמועלם</h1>')
    H.append(f'<div class="sub">5.11 עד 26.11 · {need[0]} במוצב בכל יום, {need[ez_cut]} מירידת ערן ב-{fmt(ez_exit)} · עודכן 4.11</div>')
    H.append('<table><thead><tr><th class="name">לוחם</th>')
    H.append(f'<th>{fmt(today)}<br><span style="font-weight:500">היום</span></th>')
    for i, d in enumerate(days):
        H.append(f'<th class="{"sat" if d.weekday() == 5 else ""}">{fmt(d)}<br><span style="font-weight:500">{HEB_DOW[d.weekday()]}</span></th>')
    H.append('<th>26.11<br><span style="font-weight:500">ירידה</span></th>'
             '<th class="tot">סה"כ<br>מוצב</th><th class="tot">סה"כ<br>בית</th><th class="tot ts">שבתות</th></tr></thead><tbody>')
    # David
    H.append('<tr class="david"><td class="name">דוד ★</td><td class="b"></td>' + "".join(f'<td class="b {"sat" if d.weekday() == 5 else ""}"></td>' for d in days)
             + '<td class="b">↓</td><td class="tot tb">35</td><td class="tot th">0</td><td class="tot ts">5</td></tr>')
    for p in ORDER:
        role = "★ " if p in CMD else ""
        H.append(f'<tr><td class="name">{role}{SHORT[p]} <small>{names[p].replace(SHORT[p], "").strip()}</small></td>')
        now_cls = "b" if on_now[p] else "h"
        H.append(f'<td class="{now_cls}">{"משמרת" if p == "IS" and on_now[p] else ""}</td>')
        mv = {d: k for d, k in moves_of(p)}
        for i, d in enumerate(days):
            st = state(p, i)
            cls = [st]
            txt = ""
            if d.weekday() == 5:
                cls.append("sat")
            k = mv.get(d)
            if k == "up":
                cls.append("up"); txt = "עולה" if p != "IS" else "משמרת"
            elif k == "down":
                cls.append("down"); txt = "יורד" if p != "IS" else "בית"
            elif k == "end":
                cls.append("down"); txt = "סיום"
            if fmt(d) in FIXED.get(p, []):
                cls.append("dot")
            H.append(f'<td class="{" ".join(cls)}">{txt}</td>')
        last = state(p, N - 1)
        H.append(f'<td class="{"x" if p == "EZ" else last}">{"↓" if last == "b" else ""}</td>')
        dtot = (ez_exit - START).days if p == "EZ" else 35
        sh = out["shabbat"][p]
        H.append(f'<td class="tot tb">{out["total"][p]}</td><td class="tot th">{dtot - out["total"][p]}</td>'
                 f'<td class="tot ts">{sh}{"/3" if p == "EZ" else ""}</td></tr>')
    H.append('<tr class="count"><td class="name">במוצב</td><td>8</td>')
    for i, d in enumerate(days):
        cnt = 1 + sum(1 for p in ORDER if state(p, i) == "b")
        H.append(f'<td class="{"sat" if d.weekday() == 5 else ""}">{cnt}</td>')
    H.append('<td></td><td class="tot" colspan="3">נדרש 9 עד 11.11, 8 מ-12.11</td></tr></tbody></table>')
    H.append('<div class="notes" style="margin-top:10px"><b>סה"כ מוצב / בית</b> = מתחילת הקו 22.10 עד 25.11 (35 ימים), כולל מה שכבר נעשה. ערן: מתוך 21 ימים עד שחרורו.</div>')
    H.append('<div class="legend"><span><i style="background:#3f7f3a"></i>מוצב</span><span><i style="background:#ece6d6;border:1px solid #cfc9b8"></i>בית</span>'
             '<span><i style="background:#fff;box-shadow:inset 0 0 0 3px #f3d99a"></i>שבת</span>'
             '<span><i style="background:#2e6a2a"></i>יום עלייה</span><span><i style="background:#d9cfa8"></i>יום ירידה</span>'
             '<span><span style="color:#e0a020">●</span> אילוץ בבית</span><span>★ מפקד</span>'
             '<span><i style="background:#e3ddcb"></i>אילן: ימי משמרת, חוזר הביתה בלילה</span></div>')
    # explain days above the minimum from the data itself
    extra_txt = ""
    for i, d in enumerate(days):
        cnt = 1 + sum(1 for p in ORDER if state(p, i) == "b")
        if cnt > need[i]:
            ups = [SHORT[p] for p in ORDER if p != "IS" and any(dd == d and k == "up" for dd, k in moves_of(p))]
            nxt = d + dt.timedelta(days=1)
            downs = [SHORT[p] for p in ORDER if p != "IS" and any(dd == nxt and k == "down" for dd, k in moves_of(p))]
            extra_txt += (f" ב-{fmt(d)} יש {cnt} במוצב ({cnt - need[i]} מעל הנדרש): {', '.join(ups)} עולים כבר ב-{fmt(d)}, "
                          f"ו{', '.join(downs)} יורדים רק למחרת, כדי שכולם יגיעו לאותו מספר ימים.")
    H.append('<div class="notes">יום העלייה נספר כיום מוצב, יום הירידה כיום בית. מי שיורד מחכה שהמחליף שלו יגיע למוצב. '
             'אין עליות וירידות בשבת.' + extra_txt + '</div>')
    H.append('</div></body></html>')
    html_dir = os.path.join(outdir, "html")
    os.makedirs(html_dir, exist_ok=True)
    with open(os.path.join(html_dir, "לוח הצוות.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(H))

    # ------------------------------------------------------------------ cards
    for p in ORDER:
        seq = seq_of(p)
        dtot = (ez_exit - START).days if p == "EZ" else 35
        tot = out["total"][p]
        sh = out["shabbat"][p]
        sats = [fmt(days[i]) for i in sat if S[p][i] and not (p == "EZ" and i >= ez_cut)]
        C = ['<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>' + css(font_url) + '</style></head><body>']
        C.append('<div class="card" id="shot">')
        C.append('<div class="band"><span>צוות אלמועלם · ג\'אנט יציאות</span><span>5.11 עד 26.11</span></div>')
        C.append('<div class="body">')
        role = "מפקד · " if p in CMD else ""
        C.append(f'<div><h1>{names[p]}</h1><div class="role">{role}התוכנית האישית שלך</div></div>')
        # totals over the whole deployment (the headline number)
        span_txt = f"מתחילת הקו 22.10 עד שחרורך ב-{fmt(ez_exit)} ({dtot} ימים)" if p == "EZ" else f"מתחילת הקו 22.10 עד 25.11 (35 ימים)"
        home = dtot - tot
        C.append(f'<div class="totals"><div class="lbl">סה"כ בתעסוקה, {span_txt}, כולל מה שכבר נעשה:</div>'
                 f'<div class="nums"><div class="n b"><b>{tot}</b> ימי מוצב</div><div class="n h"><b>{home}</b> ימי בית</div></div>'
                 f'<div class="bar"><i class="b" style="width:{100 * tot / dtot:.1f}%"></i><i class="h" style="width:{100 * home / dtot:.1f}%"></i></div></div>')
        # strip
        C.append('<div class="strip">')
        for i, d in enumerate(days):
            st = state(p, i)
            C.append(f'<div class="{st} {"sat" if d.weekday() == 5 else ""}">{d.day}</div>')
        C.append('<div class="ex">↓</div></div>')
        C.append('<div class="striplbl">' + "".join(f'<span>{HEB_DOW[d.weekday()].replace("שבת", "ש")}</span>' for d in days) + '<span>26</span></div>')
        # moves
        C.append('<div class="moves">')
        if p in FIXED:
            C.append(f'<div class="mv end" style="font-size:26px;padding:10px 24px"><div class="ico" style="width:48px;height:48px;font-size:26px;background:#e0a020">●</div>'
                     f'<div>אילוץ בבית: {", ".join(FIXED[p])} – נלקח בחשבון</div></div>')
        if p == "IS":
            shifts = [(days[a], days[b]) for s, a, b in stints(seq) if s]
            for a, b in shifts:
                span = f"{fmt(a)}" if a == b else f"{fmt(a)} עד {fmt(b)}"
                C.append(f'<div class="mv up"><div class="ico">☼</div><div>משמרות יום {span}</div><small>{HEB_DOW_LONG[a.weekday()]} עד {HEB_DOW_LONG[b.weekday()]}</small></div>')
        else:
            first_down = next((d for d, k in moves_of(p) if k == "down"), None)
            for d, k in moves_of(p):
                if k == "up":
                    C.append(f'<div class="mv up"><div class="ico">▲</div><div>עולה {fmt(d)}</div><small>יום {HEB_DOW_LONG[d.weekday()]}</small></div>')
                elif k == "down":
                    note = ""
                    if d == first_down and p in PROMISED and fmt(d) != PROMISED[p]:
                        note = f" (במקום {PROMISED[p]})"
                    C.append(f'<div class="mv down"><div class="ico">▼</div><div>יורד {fmt(d)}{note}</div><small>יום {HEB_DOW_LONG[d.weekday()]}</small></div>')
                elif k == "end":
                    C.append(f'<div class="mv end"><div class="ico">■</div><div>יורד {fmt(d)} – סיום התעסוקה</div><small>יום {HEB_DOW_LONG[d.weekday()]}</small></div>')
                elif k == "exit":
                    C.append('<div class="mv end"><div class="ico">↓</div><div>26.11 ירידה מהקו עם כולם</div><small>יום חמישי</small></div>')
            if seq[-1] == 0 and p != "EZ":
                C.append('<div class="mv end"><div class="ico">⌂</div><div>מסיים את התעסוקה בבית</div><small>הנחיה ל-26.11 תימסר בנפרד</small></div>')
        C.append('</div>')
        C.append(f'<div class="shab">סוגר שבתות: <b>{", ".join(sats) if sats else "לא סוגר שבת נוספת"}</b></div>')
        sh_den = 3 if p == "EZ" else 5
        plan_base = sum(seq)
        C.append('<div class="facts" style="grid-template-columns:1fr 1fr 1fr">'
                 f'<div class="fact"><b>{sh}</b><span>שבתות מתוך {sh_den}</span></div>'
                 f'<div class="fact"><b>{out["hist"][p]}</b><span>ימי מוצב עד 4.11</span></div>'
                 f'<div class="fact"><b>{plan_base}</b><span>ימי מוצב מ-5.11</span></div></div>')
        C.append('</div>')
        foot = "יורדים רק אחרי שהמחליף הגיע למוצב. אין עליות וירידות בשבת. יום העלייה נספר כיום מוצב, יום הירידה כיום בית."
        if p == "IS":
            foot = "חוזר הביתה כל לילה. יום משמרת נספר כיום מוצב. אפשר להזיז ימים בתיאום עם דוד, כל עוד המניין היומי נשמר."
        C.append(f'<div class="foot">{foot}</div>')
        C.append('</div></body></html>')
        with open(os.path.join(html_dir, f"{names[p]}.html"), "w", encoding="utf-8") as f:
            f.write("\n".join(C))
    print(f"wrote the team grid and {len(ORDER)} personal cards to {html_dir}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("outdir")
    ap.add_argument("--font-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"),
                    help="folder with Heebo-400/700/900.ttf")
    a = ap.parse_args()
    font_dir = os.path.abspath(a.font_dir) if os.path.isdir(a.font_dir) else None
    build(a.src, a.outdir, font_dir)
