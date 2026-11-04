#!/usr/bin/env python3
"""
Render a schedule JSON (from solver.py) into:
  * janet.md        – the Hebrew document for the soldiers (phone-friendly lists first, tables last)
  * janet-notes.md  – notes for the commander (what changed, open questions, trade-offs)
  * page-data.json  – compact data for render_html.py

    python3 render.py schedule.json janet.md janet-notes.md page-data.json
"""
import datetime as dt
import json
import sys

HEB_DOW = {0: "ב'", 1: "ג'", 2: "ד'", 3: "ה'", 4: "ו'", 5: "שבת", 6: "א'"}
HEB_DOW_LONG = {0: "שני", 1: "שלישי", 2: "רביעי", 3: "חמישי", 4: "שישי", 5: "שבת", 6: "ראשון"}
ORDER = ["IM", "AC", "EZ", "AH", "RH", "KA", "SG", "MA", "SA", "IK", "LE", "EY", "IS"]
SHORT = {
    "IM": "איתי", "AH": "עלי", "MA": "מרדכי", "SA": "סאמר", "RH": "רפאת", "EY": "עילי",
    "AC": "אביאל", "IK": "איתמר", "LE": "ליאור", "EZ": "ערן", "KA": "קיאן", "SG": "סייף", "IS": "אילן",
}
CMD = {"IM", "AC", "EZ"}
START = dt.date(2026, 10, 22)
EXIT = dt.date(2026, 11, 26)
# when the stint that is running on 4.11 began (for honest block lengths)
SINCE = {"IM": dt.date(2026, 11, 1), "AH": dt.date(2026, 11, 2), "MA": dt.date(2026, 11, 2),
         "SA": dt.date(2026, 11, 2), "RH": dt.date(2026, 11, 2), "EY": dt.date(2026, 11, 4),
         "AC": dt.date(2026, 10, 28), "IK": dt.date(2026, 10, 29), "LE": dt.date(2026, 10, 30),
         "EZ": dt.date(2026, 10, 30), "KA": dt.date(2026, 10, 31), "SG": dt.date(2026, 10, 31),
         "IS": dt.date(2026, 11, 4)}
PROMISED = {"IM": "10.11", "AH": "10.11", "SA": "10.11", "RH": "10.11", "MA": "8.11", "EY": "12.11"}


def fmt(d):
    return f"{d.day}.{d.month}"


def stints(seq):
    res, cur, start = [], seq[0], 0
    for i in range(1, len(seq)):
        if seq[i] != cur:
            res.append((cur, start, i - 1)); cur, start = seq[i], i
    res.append((cur, start, len(seq) - 1))
    return res


def main(src, dst_team, dst_notes, page=None):
    out = json.load(open(src, encoding="utf-8"))
    S = out["schedule"]
    days = [dt.date.fromisoformat(d) for d in out["days"]]
    N = len(days)
    names = out["names"]
    ez_exit = dt.date.fromisoformat(out["ez_exit"])
    ez_cut = days.index(ez_exit)                      # Eran's sequence is meaningful before this index
    on_now = dict(out["on_base_now"])
    on_now["IS"] = True                               # Ilan was on day shift on 4.11
    sat = [i for i, d in enumerate(days) if d.weekday() == 5]
    need = out["need"]

    def seq_of(p):
        return S[p][:ez_cut] if p == "EZ" else S[p]

    def days_total(p):
        return (ez_exit - START).days if p == "EZ" else 35

    def mark(p):
        return SHORT[p] + (" ★" if p in CMD else "")

    # ---- per-person moves (date, kind) -------------------------------------
    def moves_of(p):
        seq = seq_of(p)
        mv = []
        prev = 1 if on_now[p] else 0
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

    # ---- blocks with honest start dates ------------------------------------
    def blocks_of(p):
        """(state, start, end, length) blocks; the stint running on 4.11 is shown
        with its real start date, and if the plan flips it on 5.11 it is listed first."""
        seq = seq_of(p)
        now_state = 1 if on_now[p] else 0
        res = []
        st = stints(seq)
        if seq[0] != now_state:
            res.append((now_state, SINCE[p], dt.date(2026, 11, 4), (dt.date(2026, 11, 4) - SINCE[p]).days + 1))
        for k, (state, a, b) in enumerate(st):
            start = SINCE[p] if (k == 0 and seq[0] == now_state) else days[a]
            end = days[b]
            res.append((state, start, end, (end - start).days + 1))
        return res

    per_day_base = [[p for p in ORDER if S[p][i] and not (p == "EZ" and i >= ez_cut)] for i in range(N)]
    per_day_home = [[p for p in ORDER if not S[p][i] and not (p == "EZ" and i >= ez_cut)] for i in range(N)]
    excess_days = [(days[i], 1 + len(per_day_base[i]), need[i]) for i in range(N) if 1 + len(per_day_base[i]) > need[i]]

    # moves by date
    by_date = {}
    for p in ORDER:
        for d, kind in moves_of(p):
            if kind in ("exit",):
                continue
            by_date.setdefault(d, {"up": [], "down": []})
            if p == "IS":
                by_date[d]["up" if kind == "up" else "down"].append("אילן (" + ("מתחיל משמרות" if kind == "up" else "מסיים משמרות") + ")")
            elif kind == "end":
                by_date[d]["down"].append("ערן (סיום התעסוקה המקוצרת)")
            else:
                by_date[d][kind].append(SHORT[p])

    non_ez = [p for p in ORDER if p != "EZ"]
    tots = [out["total"][p] for p in non_ez]
    shs = [out["shabbat"][p] for p in non_ez]
    first = by_date.get(days[0], {"up": [], "down": []})

    # =======================================================================
    # TEAM DOCUMENT
    # =======================================================================
    L = []
    A = L.append
    A("# ג'אנט יציאות – צוות אלמועלם, 5.11 עד 26.11")
    A("")
    A("עודכן 4.11. המצב של היום (4.11) נשאר כפי שהוא; השינויים מתחילים מחר.")
    A("")
    A(f"**מחר, {HEB_DOW_LONG[days[0].weekday()]} {fmt(days[0])}:** עולים: {', '.join(first['up'])}. "
      f"יורדים (אחרי שהעולים הגיעו): {', '.join(first['down']) or 'אף אחד'}. במוצב מחר: {1 + len(per_day_base[0])}.")
    A("")
    A("## 1. הכללים בקצרה")
    A("")
    A(f"- **{need[0]} במוצב בכל יום מ-5.11** (כולל דוד, ואילן בימי המשמרת שלו) – זה כלל ה-65% כפי שסוכם, מעוגל כלפי מטה. "
      f"מ-{fmt(ez_exit)}, אחרי ירידת ערן, הצוות הוא 13 ונדרשים **{need[ez_cut]}**.")
    A("- **תמיד לפחות 2 מפקדים במוצב:** דוד, ועוד אחד מבין איתי / אביאל / ערן.")
    A("- **לא עולים ולא יורדים בשבת.** מי שבמוצב בשישי סוגר את השבת.")
    A(f"- **רצף במוצב:** עד {out['params']['max_base']} ימים, כולל ימים שכבר נעשו. "
      f"**רצף בבית:** לפחות {out['params']['min_home']} ימים (5 כשהאיזון מאפשר), חוץ מבית שנמשך עד סוף התעסוקה.")
    A("- **אילוצים:** איתי בבית ב-17.11, מרדכי בבית ב-8.11, קיאן וסייף בבית ב-19.11. **זוגות:** עלי ורפאת, קיאן וסייף – תמיד יחד.")
    A("- **חפיפה:** מי שיורד יורד רק אחרי שהמחליף שלו הגיע למוצב. בימים של החלפת מפקד (5.11, 16.11) זה קריטי.")
    A("- **ספירה:** יום העלייה נספר כיום מוצב, יום הירידה כיום בית. 35 ימים נספרים (22.10 עד 25.11); 26.11 ירידה מהקו.")
    A(f"- **האיזון:** כולם מסיימים את התעסוקה עם {min(tots)}–{max(tots)} ימי מוצב מתוך 35 ו-{min(shs)}–{max(shs)} שבתות מתוך 5, "
      "כולל מה שכבר נעשה מ-22.10. מי שהיה יותר במוצב עד היום מקבל יותר בית מכאן.")
    A("")

    # ---- per-person plan ---------------------------------------------------
    A("## 2. התוכנית של כל אחד")
    A("")
    for p in ORDER:
        seq = seq_of(p)
        tot = out["total"][p]
        dtot = days_total(p)
        sh = out["shabbat"][p]
        sats = [fmt(days[i]) for i in sat if S[p][i] and not (p == "EZ" and i >= ez_cut)]
        role = " (מפקד)" if p in CMD else ""
        if p == "IS":
            shifts = [f"{fmt(days[a])}" if a == b else f"{fmt(days[a])} עד {fmt(days[b])}" for s, a, b in stints(seq) if s]
            line = (f"**{names[p]}** – ימי משמרת: {', '.join(shifts)}. "
                    f"סה\"כ {sum(seq)} ימי משמרת מ-5.11, {tot} מתוך 35 בכל התעסוקה. "
                    f"משמרות בשבת: {', '.join(sats) if sats else 'אין'}. "
                    "(חוזר הביתה כל לילה; אפשר להזיז ימים בתיאום, כל עוד המניין היומי נשמר.)")
            A(f"- {line}")
            continue
        parts = []
        for d, kind in moves_of(p):
            if kind == "up":
                parts.append(f"עולה {fmt(d)}")
            elif kind == "down":
                parts.append(f"יורד {fmt(d)}")
            elif kind == "end":
                parts.append(f"יורד {fmt(d)} – סיום התעסוקה המקוצרת")
            elif kind == "exit":
                parts.append("יורד 26.11 עם כולם")
        # promised-exit note
        note = ""
        if p in PROMISED:
            first_down = next((fmt(d) for d, k in moves_of(p) if k == "down"), None)
            if first_down and first_down != PROMISED[p]:
                note = f" (הירידה הראשונה הייתה מתוכננת ל-{PROMISED[p]})"
            elif first_down:
                note = " (כמתוכנן)"
        if seq[-1] == 0 and p != "EZ":
            parts.append("מסיים את התעסוקה בבית")
        line = f"**{names[p]}{role}** – " + ", ".join(parts) + note + ". "
        line += f"סוגר שבתות: {', '.join(sats) if sats else 'לא סוגר שבת נוספת'}. "
        sh_txt = "שבת אחת" if sh == 1 else f"{sh} שבתות"
        line += f"סה\"כ {tot} מתוך {dtot} ימי מוצב, {sh_txt}" + (" מתוך 3 בתעסוקה שלו" if p == "EZ" else " מתוך 5") + "."
        A(f"- {line}")
    A("- **דוד אלמועלם (מפקד)** – במוצב לאורך כל התעסוקה.")
    A("")

    # ---- moves by date -----------------------------------------------------
    A("## 3. עליות וירידות לפי תאריך")
    A("")
    for d in sorted(by_date):
        up, down = by_date[d]["up"], by_date[d]["down"]
        line = f"- **{fmt(d)} ({HEB_DOW_LONG[d.weekday()]})** –"
        if up:
            line += f" עולים: {', '.join(up)}."
        if down:
            line += f" יורדים: {', '.join(down)}."
        A(line)
    A("- **26.11 (חמישי)** – ירידה מהקו.")
    A("")

    # ---- Shabbatot ---------------------------------------------------------
    A("## 4. מי סוגר שבת")
    A("")
    for i in sat:
        A(f"- **שבת {fmt(days[i])}:** דוד, {', '.join(SHORT[p] for p in per_day_base[i])}.")
    A("")

    # ---- blocks table ------------------------------------------------------
    A("## 5. הרצפים של כל אחד (טבלה)")
    A("")
    A("אורך הרצף הראשון כולל את הימים שכבר נעשו לפני 5.11. ★ = מפקד.")
    A("")
    A("| לוחם | מוצב עד 4.11 | מוצב מ-5.11 | סה\"כ מוצב | סה\"כ בית | שבתות | הרצפים |")
    A("|---|---|---|---|---|---|---|")
    for p in ORDER:
        seq = seq_of(p)
        tot = out["total"][p]
        dtot = days_total(p)
        cells = []
        for state, start, end, n in blocks_of(p):
            if p == "IS":
                label = "משמרות" if state else "לא במשמרת"
            else:
                label = "מוצב" if state else "בית"
            span = f"{fmt(start)}" if start == end else f"מ-{fmt(start)} עד {fmt(end)}"
            cells.append(f"{label} {span} ({n})")
        if p == "EZ":
            cells.append(f"סיום התעסוקה {fmt(ez_exit)}")
        A(f"| {mark(p)} {names[p].replace(SHORT[p], '').strip()} | {out['hist'][p]} | {sum(seq)} | **{tot}/{dtot}** | {dtot - tot} | "
          f"{out['shabbat'][p]}{'/3' if p == 'EZ' else '/5'} | {', '.join(cells)} |")
    A("| דוד ★ אלמועלם | 14 | 21 | **35/35** | 0 | 5/5 | במוצב כל התעסוקה |")
    A("")

    # ---- daily table -------------------------------------------------------
    A("## 6. הלוח יום-יום (טבלה)")
    A("")
    A("★ = מפקד. המניין כולל את דוד. אילן נספר בימי המשמרת שלו.")
    A("")
    A("| תאריך | יום | במוצב (מניין) | בבית |")
    A("|---|---|---|---|")
    base0 = [mark(p) for p in ORDER if on_now[p] and p != "IS"] + ["אילן (משמרת)"]
    home0 = [mark(p) for p in ORDER if not on_now[p]]
    A(f"| 4.11 | ד' | דוד ★, {', '.join(base0)} ({1 + len(base0)}) – מצב קיים | {', '.join(home0)} |")
    for i, d in enumerate(days):
        at_base = [("אילן (משמרת)" if p == "IS" else mark(p)) for p in per_day_base[i]]
        at_home = [("אילן (לא במשמרת)" if p == "IS" else mark(p)) for p in per_day_home[i]]
        if i >= ez_cut:
            at_home.append("ערן (סיים)")
        cnt = 1 + len(at_base)
        extra = "" if cnt == need[i] else f", נדרש {need[i]}"
        shabbat = " **שבת**" if d.weekday() == 5 else ""
        A(f"| {fmt(d)}{shabbat} | {HEB_DOW[d.weekday()]} | דוד ★, {', '.join(at_base)} ({cnt}{extra}) | {', '.join(at_home)} |")
    A("| 26.11 | ה' | ירידה מהקו | |")
    A("")
    if excess_days:
        for d, cnt, nd in excess_days:
            ups = by_date.get(d, {}).get("up", [])
            nxt = by_date.get(d + dt.timedelta(days=1), {}).get("down", [])
            A(f"ב-{fmt(d)} יש {cnt} במוצב ({cnt - nd} מעל הנדרש): {', '.join(ups)} עולים כבר ב-{fmt(d)} כדי לקבל רצף של "
              f"{out['params']['min_base']} ימים עד הסוף, ו{', '.join(nxt)} יורדים רק למחרת כדי להגיע לאותו מספר ימי מוצב כמו כולם.")
            A("")

    with open(dst_team, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    # =======================================================================
    # COMMANDER NOTES
    # =======================================================================
    M = []
    B = M.append
    B("# הערות למפקד – לא לשליחה לצוות")
    B("")
    B("## מה השתנה לעומת מה שהובטח")
    B("")
    for p in ["IM", "AH", "RH", "MA", "SA", "EY"]:
        first_down = next((fmt(d) for d, k in moves_of(p) if k == "down"), None)
        if first_down != PROMISED[p]:
            B(f"- **{SHORT[p]}:** יורד {first_down} במקום {PROMISED[p]}.")
        else:
            B(f"- **{SHORT[p]}:** יורד {first_down}, כמתוכנן.")
    B("")
    B("למה איתי יורד מחר: הוא עלה 1.11, ועם תקרת 8 הימים, הבית ב-17.11, איסור תנועה בשבת, מינימום 4 ימים לרצף "
      "והיעד של 19 ימי מוצב – ירידה ב-5.11 (או 6.11) היא היחידה שמביאה אותו ל-19 ימים ו-3 שבתות. ירידה ב-9.11 משאירה אותו על 18, "
      "וירידה ב-8.11 נותנת לו 4 שבתות.")
    B("")
    B("למה סאמר יורד מחר: אין כלל שמחייב את זה; הפותר בחר בזה כי זו הדרך היחידה שמצא להשאיר את כולם על 19–20 ימים. "
      "הרצתי גם גרסה שמשאירה את סאמר עד 10.11 כמתוכנן – המחיר הוא שאיתי מסיים עם 18 ימים (כולם 19–20, הוא 18). "
      "אם אתה מעדיף את זה, אומרים לי ומריצים.")
    B("")
    B("## שאלות פתוחות")
    B("")
    B("1. **אתה:** אושר – אתה במוצב כל התעסוקה. שים לב שאחרי ירידת ערן רק איתי ואביאל ממלאים את כלל שני המפקדים, "
      "ולכן ההחלפות ביניהם (16.11, 20.11) צמודות.")
    B("2. **26.11:** מי שבבית ב-25.11 (" + ", ".join(SHORT[p] for p in per_day_home[N - 1] if p != "IS") + ") – מגיע לירידה מהקו או משוחרר מהבית? "
      "במסמך לצוות כתוב רק \"ירידה מהקו\"; צריך להוסיף הנחיה.")
    B("3. **מרדכי 8.11:** הוא יורד בבוקר 8.11 (יום הירידה נספר כבית, כמו בתוכנית המקורית שלו). אם הוא צריך להיות בבית כבר מהבוקר – "
      "מורידים אותו בשישי 6.11 (שבת חוסמת את 7.11).")
    B("4. **אילן בשבת:** אושר שהוא עובד בשבתות. הלוח מסתמך על משמרת יום שלו בשבתות " + ", ".join(fmt(days[i]) for i in sat if S["IS"][i]) +
      ". בשבתות האלה המניין מדויק על הנדרש, ואחרי שישי אי אפשר להעלות מישהו במקומו – כדאי לוודא איתו מראש.")
    B("5. **אפס רזרבה:** חוץ מ-22.11, כל יום הוא בדיוק על המניין הנדרש. חולה אחד או איחור אחד = פחות מהנדרש. "
      "המנופים: להזיז ימי משמרת של אילן (עד 6 ברצף), או להעלות מישהו יום מוקדם. אם אתה רוצה רזרבה קבועה של אחד – זה עולה לכולם יום בית.")
    B("6. **מניין בלילה:** אילן נספר ביום. בלילות שבהם הוא במשמרת המניין בפועל הוא אחד פחות (למשל 7 במקום 8 ב-12–14.11, 17–18.11, 23–25.11). "
      "סיכמנו שזה מקובל; רק שתדע.")
    B("7. **החלפת מפקדים ב-16.11:** איתי יורד (חייב להיות בבית ב-17.11) ואביאל עולה באותו יום. מ-12.11 עד 19.11 יש בכל רגע רק מפקד אחד חוץ ממך, "
      "אז כדאי לקבוע שעה ברורה לאביאל ושאיתי לא זז לפני שהוא במוצב.")
    B("8. **עליות בשישי:** ליאור עולה בשישי 13.11 ואיתי בשישי 20.11. שתיהן כפויות (בית של 4 ימים שמסתיים ביום חמישי + איסור עלייה בשבת). "
      "אם זה בעייתי להם – להגיד.")
    B("9. **שתי שבתות ברצף:** ליאור ומרדכי סוגרים 7.11 ו-14.11; איתי וסאמר סוגרים 14.11 ו-21.11 (בלי סוף שבוע בבית ביניהן). "
      "עם 22 מקומות בשבתות ל-12 לוחמים זה בלתי נמנע אצל ארבעה.")
    B("")
    B("## מי נושא יותר ומי פחות")
    B("")
    hi = [SHORT[p] for p in non_ez if out["total"][p] == max(tots)]
    lo = [SHORT[p] for p in non_ez if out["total"][p] == min(tots)]
    B(f"- {max(tots)} ימי מוצב: {', '.join(hi)}. {min(tots)} ימי מוצב: {', '.join(lo)}.")
    B(f"- {max(shs)} שבתות: {', '.join(SHORT[p] for p in non_ez if out['shabbat'][p] == max(shs))}. "
      f"{min(shs)} שבתות: {', '.join(SHORT[p] for p in non_ez if out['shabbat'][p] == min(shs))}.")
    B("- מי שגם על המקסימום של ימים וגם של שבתות (קיאן, סייף, איתמר) נכנס לתוכנית עם היסטוריה גבוהה (9/2 ו-7/1), "
      "ומי שעל המינימום בשניהם (אביאל, אילן) נכנס עם 0 שבתות. ההפרש הוא יום אחד ושבת אחת, והוא נובע מהמבנה (זוגות, שבתות, מפקדים), לא מהעדפה.")
    B("- עילי: 15 מתוך 21 ימי התוכנית במוצב (הכי הרבה), שני רצפים של 8, ובכל זאת מסיים על 20 – כי נכנס עם 5 ימים ו-0 שבתות.")
    B("- עלי ורפאת: שני רצפים של 8 ימים (2–9.11 ו-15–22.11). זה כפוי: תקרת 8 מ-2.11, הירידה שהובטחה ל-10.11, שבת 14.11 ויעד 19 ימים.")
    B(f"- ערן: {out['total']['EZ']} מתוך {(ez_exit - START).days} ימי מוצב ({round(100 * out['total']['EZ'] / (ez_exit - START).days)}%) "
      f"לעומת {round(100 * sum(tots) / len(tots) / 35)}% אצל כולם, ו-{out['shabbat']['EZ']} שבת מתוך 3 שהיו לו. "
      "אפשר במקום זה שיסגור את 7.11 (עולה 5.11, יורד 9.11) – אז מישהו אחר יורד ל-2 שבתות.")
    B("")
    B("## חלופות שחושבו")
    B("")
    B("- **להשאיר את סאמר עד 10.11 כמתוכנן:** אפשרי; המחיר – איתי מסיים עם 18 במקום 19.")
    B("- **מינימום 5 ימי בית קשיח:** אין לוח חוקי (בעיקר בגלל איתי: תקרת 8, בית ב-17.11 ואיסור שבת).")
    B("- **לבטל את ה-10 במוצב ב-22.11:** אביאל, עלי ורפאת יורדים ב-22.11 במקום 23.11 ומסיימים עם 18 במקום 19.")
    B("- **10 במוצב גם אחרי ירידת ערן:** כל אחד מפסיד בערך יום בית.")
    B("- **בלי עליות בשישי:** אין לוח עם אותו איזון; שתי העליות בשישי נשארות.")
    B("")
    B("## איך מריצים שוב")
    B("")
    B("```")
    B("cd scheduling && pip install ortools")
    B("python3 solver.py --variant G_commander --time 300 --json janet.json     # -w early=6000 / --eran-exit 13.11 / --need13 9 ...")
    B("python3 verify.py janet.json                                            # בדיקה בלתי תלויה של כל הכללים")
    B("python3 render.py janet.json janet.md janet-notes.md page.json && python3 render_html.py page.json janet.html")
    B("```")
    B("")
    B("הנתונים (היסטוריה, אילוצים, זוגות, תאריכי יציאה שהובטחו, מניין נדרש) נמצאים בראש `solver.py`.")
    B("")
    with open(dst_notes, "w", encoding="utf-8") as f:
        f.write("\n".join(M))

    if page:
        data = {
            "days": [{"iso": d.isoformat(), "label": fmt(d), "dow": HEB_DOW[d.weekday()], "sat": d.weekday() == 5,
                      "need": need[i]} for i, d in enumerate(days)],
            "people": [{"key": p, "name": names[p], "short": SHORT[p], "cmd": p in CMD,
                        "hist": out["hist"][p], "total": out["total"][p], "shabbat": out["shabbat"][p],
                        "now": on_now[p], "seq": S[p], "since": fmt(SINCE[p]),
                        "promised": PROMISED.get(p),
                        "days_total": days_total(p)} for p in ORDER],
            "moves": [{"date": fmt(d), "dow": HEB_DOW_LONG[d.weekday()], "up": by_date[d]["up"], "down": by_date[d]["down"]}
                      for d in sorted(by_date)],
            "ez_exit": fmt(ez_exit),
            "params": out["params"],
            "excess": [{"date": fmt(d), "count": c, "need": n} for d, c, n in excess_days],
        }
        with open(page, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"wrote {dst_team}, {dst_notes}" + (f", {page}" if page else ""))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
