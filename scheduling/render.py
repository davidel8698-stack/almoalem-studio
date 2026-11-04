#!/usr/bin/env python3
"""
Render a schedule JSON (from solver.py) into the Hebrew Markdown document
(the ג'אנט) and a compact JSON for the HTML page.

    python3 render.py schedule.json out.md [page-data.json]
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


def fmt(d):
    return f"{d.day}.{d.month}"


def stints(seq):
    res, cur, start = [], seq[0], 0
    for i in range(1, len(seq)):
        if seq[i] != cur:
            res.append((cur, start, i - 1)); cur, start = seq[i], i
    res.append((cur, start, len(seq) - 1))
    return res


def main(src, dst, page=None):
    out = json.load(open(src, encoding="utf-8"))
    S = out["schedule"]
    days = [dt.date.fromisoformat(d) for d in out["days"]]
    N = len(days)
    names = out["names"]
    ez_exit = dt.date.fromisoformat(out["ez_exit"])
    on_now = out["on_base_now"]
    sat = [i for i, d in enumerate(days) if d.weekday() == 5]

    def mark(p):
        return SHORT[p] + ("*" if p in CMD else "")

    L = []
    A = L.append
    A("# ג'אנט יציאות מעודכן – צוות אלמועלם")
    A("")
    A("**תקף מ-5.11.26 עד הירידה מהקו ב-26.11.26.** המצב של 4.11 נשאר כפי שהוא; השינויים מתחילים ב-5.11.")
    A("")
    A("לוח זה נבנה על ידי פותר אופטימיזציה שמחפש, מבין כל הלוחות שעומדים בכללים, את הלוח שבו כולם מסיימים את התעסוקה "
      "עם מספר ימי מוצב שווה ככל האפשר (כולל מה שכבר נעשה מ-22.10), מספר שבתות שווה, ובלי ימי מוצב מיותרים מעבר לכלל ה-65%.")
    A("")
    A("## 1. הכללים שהלוח עומד בהם")
    A("")
    A("- **65% מהצוות במוצב בכל רגע, החל מיום חמישי 5.11:** **9 במוצב** (כולל דוד, ואילן בימי המשמרת שלו). "
      f"ערן יורד ב-{fmt(ez_exit)}, ומאז הצוות הוא 13 חיילים ונדרשים **8 במוצב**.")
    A("- **לפחות 2 מפקדים במוצב:** דוד תמיד במוצב, ובנוסף תמיד לפחות אחד מבין איתי / אביאל / ערן.")
    A("- **אילוצים אישיים:** איתי בבית ב-17.11, מרדכי בבית ב-8.11, קיאן וסייף בבית ב-19.11.")
    A("- **זוגות:** עלי ורפאת תמיד יחד, קיאן וסייף תמיד יחד.")
    A("- **אין עליות או ירידות בשבת.** מי שבמוצב בשישי סוגר את השבת.")
    A(f"- **רצפים:** לא יותר מ-{out['params']['max_base']} ימי מוצב ברצף (כולל הרצף שכבר התחיל). "
      f"לפחות {out['params']['min_home']} ימי בית ברצף, עם העדפה חזקה ל-5 (חוץ מבית שנמשך עד סוף התעסוקה). "
      f"לפחות {out['params']['min_base']} ימי מוצב ברצף.")
    A("- **אילן** מגיע יומי וחוזר הביתה בלילה. יום משמרת שלו נספר כיום מוצב במניין, והוא מקבל אותו מספר ימי מוצב כמו כולם. "
      "הכללים של הרצפים לא חלים עליו (אפשר להזיז את ימי המשמרת שלו כל עוד המניין היומי נשמר).")
    A("- **ספירה:** יום העלייה נספר כיום מוצב, יום הירידה כיום בית (כמו בסיכום שלכם). סך הכול 35 ימים נספרים (22.10 עד 25.11); "
      "26.11 הוא יום הירידה של כולם.")
    A("")

    # ---- per-person summary ------------------------------------------------
    A("## 2. שורה תחתונה לכל לוחם")
    A("")
    A("| לוחם | מוצב עד 4.11 | מוצב מ-5.11 | **סה\"כ מוצב** | **סה\"כ בית** | שבתות (מתוך 5) | הרצפים מ-5.11 |")
    A("|---|---|---|---|---|---|---|")
    for p in ORDER:
        seq = S[p]
        if p == "EZ":
            H = days.index(ez_exit)
            seq = seq[:H]
            days_total = (ez_exit - START).days
        else:
            days_total = 35
        fut = sum(seq)
        tot = out["total"][p]
        st = stints(seq)
        parts = []
        for k, (state, a, b) in enumerate(st):
            label = "מוצב" if state else "בית"
            span = f"{fmt(days[a])}" if a == b else f"{fmt(days[a])} עד {fmt(days[b])}"
            if p == "EZ" and k == len(st) - 1 and state == 0:
                parts.append(f"יורד {fmt(days[a])} – סיום התעסוקה המקוצרת (שחרור {fmt(ez_exit)})")
            else:
                parts.append(f"{label} {span} ({b - a + 1})")
        if p == "EZ" and st[-1][0] == 1:
            parts.append(f"יורד {fmt(ez_exit)} – סיום התעסוקה המקוצרת")
        role = " (מפקד)" if p in CMD else ""
        A(f"| {names[p]}{role} | {out['hist'][p]} | {fut} | **{tot}/{days_total}** | **{days_total - tot}** | "
          f"{out['shabbat'][p]} | {', '.join(parts)} |")
    A(f"| דוד אלמועלם (מפקד) | 14 | {N} | **35/35** | **0** | 5 | במוצב לאורך כל התעסוקה (הנחה – ראה סעיף 6) |")
    A("")
    non_ez = [p for p in ORDER if p != "EZ"]
    tots = [out["total"][p] for p in non_ez]
    shs = [out["shabbat"][p] for p in non_ez]
    A(f"סה\"כ ימי מוצב לכל לוחם: בין {min(tots)} ל-{max(tots)} מתוך 35. שבתות: בין {min(shs)} ל-{max(shs)} מתוך 5. "
      f"ערן: {out['total']['EZ']} מתוך {(ez_exit - START).days} ימים בתעסוקה המקוצרת שלו "
      f"({round(100 * out['total']['EZ'] / (ez_exit - START).days)}% לעומת {round(100 * sum(tots) / len(tots) / 35)}% אצל כולם).")
    A("")

    # ---- moves by date -----------------------------------------------------
    A("## 3. עליות וירידות לפי תאריך")
    A("")
    A("מי שיורד מחכה שהמחליף שלו יגיע למוצב (חפיפה), כדי שהמניין לא ירד מתחת לנדרש באף שעה.")
    A("")
    prev = {p: (1 if on_now[p] else 0) if on_now[p] is not None else None for p in ORDER}
    moves = []
    for i, d in enumerate(days):
        up, down = [], []
        for p in ORDER:
            cur = S[p][i]
            if p == "EZ" and d >= ez_exit:
                if d == ez_exit and prev[p] == 1:
                    down.append(SHORT[p] + " (סיום תעסוקה)")
                prev[p] = 0
                continue
            if prev[p] is None:
                if cur == 1:
                    up.append(SHORT[p])
            elif cur != prev[p]:
                if p == "EZ" and cur == 0 and not any(S[p][j] for j in range(i, N)):
                    down.append(SHORT[p] + " (סיום תעסוקה)")
                else:
                    (up if cur else down).append(SHORT[p])
            prev[p] = cur
        if up or down:
            moves.append((d, up, down))
    for d, up, down in moves:
        line = f"- **{fmt(d)} ({HEB_DOW_LONG[d.weekday()]})** –"
        if up:
            line += f" עולים: {', '.join(up)}."
        if down:
            line += f" יורדים: {', '.join(down)}."
        A(line)
    A("")

    # ---- daily table ---------------------------------------------------------
    A("## 4. הלוח יום-יום")
    A("")
    A("כוכבית = מפקד. המניין כולל את דוד.")
    A("")
    A("| תאריך | יום | במוצב (מניין) | בבית |")
    A("|---|---|---|---|")
    base0 = [mark(p) for p in ORDER if on_now[p]] + ["אילן (משמרת יום)"]
    home0 = [mark(p) for p in ORDER if on_now[p] is False]
    A(f"| 4.11 | ד' | דוד*, {', '.join(base0)} ({1 + len(base0)}) – מצב קיים | {', '.join(home0)} |")
    for i, d in enumerate(days):
        at_base = [mark(p) for p in ORDER if S[p][i]]
        at_home = [mark(p) for p in ORDER if not S[p][i] and not (p == "EZ" and d >= ez_exit)]
        if d >= ez_exit:
            at_home.append("ערן (משוחרר)")
        need = out["need"][i]
        cnt = 1 + len(at_base)
        extra = "" if cnt == need else f", נדרש {need}"
        shabbat = " **שבת**" if d.weekday() == 5 else ""
        A(f"| {fmt(d)}{shabbat} | {HEB_DOW[d.weekday()]} | דוד*, {', '.join(at_base)} ({cnt}{extra}) | {', '.join(at_home)} |")
    A(f"| 26.11 | ה' | ירידה מהקו – כולם | |")
    A("")

    # ---- Shabbatot -------------------------------------------------------------
    A("## 5. מי סוגר שבת")
    A("")
    for i in sat:
        A(f"- **שבת {fmt(days[i])}:** דוד, {', '.join(SHORT[p] for p in ORDER if S[p][i])}.")
    A("")

    # ---- assumptions, questions, what-ifs ----------------------------------
    A("## 6. הנחות שלקחתי – צריך את האישור שלך")
    A("")
    A("אם אחת מההנחות לא נכונה, מריצים את הפותר שוב (דקה) ומקבלים לוח מעודכן. בסוגריים – מה משתנה אם ההנחה שגויה.")
    A("")
    A("1. **דוד במוצב לאורך כל התעסוקה** ונספר במניין (אם גם אתה יוצא הביתה – צריך את התאריכים שלך; כלל שני המפקדים נהיה צפוף אחרי ירידת ערן, כי נשארים רק איתי ואביאל).")
    A("2. **סייף נמצא עכשיו בבית יחד עם קיאן** – הוא לא הופיע ברשימת \"בבית\" בסיכום שלך, אבל הוא ביקש להיות עם קיאן ויש לו אותם מספרים.")
    A(f"3. **{fmt(ez_exit)} הוא יום הירידה של ערן** (נספר אצלו כיום בית, כמו כל יום ירידה), כלומר הלילה האחרון שלו במוצב הוא {fmt(ez_exit - dt.timedelta(days=1))}, "
      f"ומ-{fmt(ez_exit)} נדרשים 8 במוצב. הלוח נותן לו יחס מוצב-בית כמו של כולם ביחס לתעסוקה המקוצרת שלו.")
    A("4. **מי שבמוצב עכשיו יכול לרדת לפני תאריך היציאה שתוכנן לו** אם זה עוזר לאיזון (זו הקלה, לא פגיעה). הלוח מעדיף לא לעשות את זה, אבל תקרת 8 הימים מחייבת למשל את איתי (עלה 1.11) לרדת עד 9.11.")
    A("5. **האילוצים האישיים הם ליום אחד** (איתי 17.11, מרדכי 8.11, קיאן וסייף 19.11). הלוח נותן לכל אחד מהם רצף בית של 4 ימים לפחות סביב התאריך.")
    A("6. **אין אילוץ שכולם יהיו במוצב ביום הירידה.** מי שבבית ב-25.11 מגיע ישירות לירידה/שחרור ב-26.11, או שלא – לפי מה שתחליט. זה לא משנה את הספירה.")
    A("7. **ספירת העבר:** לקחתי את המספרים מהסיכום שלך (עד 3.11) והוספתי את 4.11 למי שבמוצב (כולל אילן, שרשום בסיכום כ\"יומיות\").")
    A("8. **שבתות של אילן:** משמרת יום בשבת נספרת לו כשבת, ולכן הוא נכלל באיזון השבתות. אם הוא לא אמור לעבוד בשבתות – אומרים לי והלוח מתעדכן.")
    A("")
    A("## 7. מה עוד יעזור לי לשפר את הלוח")
    A("")
    A("- תאריכים שבהם אתה (דוד) צריך להיות בבית, אם יש.")
    A("- האם יש ימים שבהם אסור לבצע החלפות (למשל ימי משימה מיוחדת), או מגבלה על מספר האנשים שמתחלפים ביום אחד (כרגע עד 6).")
    A("- ימים שבהם אילן לא יכול להגיע, ואם יש לו העדפה לימים קבועים בשבוע.")
    A("- מי מבין הלוחמים גר רחוק (נסיעה ארוכה) – כדי להעדיף אצלו בלוקים ארוכים יותר.")
    A("")
    A("## 8. איך מריצים שוב")
    A("")
    A("```")
    A("cd scheduling")
    A("pip install ortools")
    A("python3 solver.py --variant G_commander --time 300 --json out.json   # אפשר: --need14 10 --need13 9 / --no-ilan-count / --eran-exit 13.11")
    A("python3 verify.py out.json          # בדיקה בלתי תלויה של כל הכללים")
    A("python3 render.py out.json janet.md page.json && python3 render_html.py page.json janet.html")
    A("```")
    A("")
    A("הנתונים (היסטוריה, אילוצים, זוגות, תאריכי יציאה שהובטחו) נמצאים בראש הקובץ `solver.py` וקל לעדכן אותם.")
    A("")

    md = "\n".join(L)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(md)

    if page:
        data = {
            "days": [{"iso": d.isoformat(), "label": fmt(d), "dow": HEB_DOW[d.weekday()], "sat": d.weekday() == 5,
                      "need": out["need"][i]} for i, d in enumerate(days)],
            "people": [{"key": p, "name": names[p], "short": SHORT[p], "cmd": p in CMD,
                        "hist": out["hist"][p], "total": out["total"][p], "shabbat": out["shabbat"][p],
                        "now": on_now[p], "seq": S[p],
                        "days_total": (ez_exit - START).days if p == "EZ" else 35} for p in ORDER],
            "moves": [{"date": fmt(d), "dow": HEB_DOW_LONG[d.weekday()], "up": up, "down": down} for d, up, down in moves],
            "ez_exit": fmt(ez_exit),
            "params": out["params"],
        }
        with open(page, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"wrote {dst}" + (f" and {page}" if page else ""))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
