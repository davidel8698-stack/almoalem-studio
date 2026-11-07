#!/usr/bin/env python3
"""
Write the team rotation as a simple Excel workbook.

    python3 render_xlsx.py janet.json janet.xlsx
Sheet 1: one row per soldier, one column per day (מוצב / בית), totals by formula.
Sheet 2: per-person list of up/down dates and Shabbatot.
"""
import datetime as dt
import json
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ORDER = ["IM", "AC", "EZ", "AH", "RH", "KA", "SG", "MA", "SA", "IK", "LE", "EY", "IS"]
CMD = {"IM", "AC", "EZ"}
HEB_DOW = {0: "ב", 1: "ג", 2: "ד", 3: "ה", 4: "ו", 5: "שבת", 6: "א"}
HEB_DOW_LONG = {0: "שני", 1: "שלישי", 2: "רביעי", 3: "חמישי", 4: "שישי", 5: "שבת", 6: "ראשון"}
TODAY = dt.date(2026, 11, 4)
EXIT = dt.date(2026, 11, 26)

FONT = "Arial"
GREEN = PatternFill("solid", fgColor="6A8A3B")
GREEN_D = PatternFill("solid", fgColor="4F6B2F")
SAND = PatternFill("solid", fgColor="EDE7D8")
GRAY = PatternFill("solid", fgColor="D9D4C6")
SAT = PatternFill("solid", fgColor="F3D99A")
HEAD = PatternFill("solid", fgColor="E9E4D6")
WHITE_B = Font(name=FONT, size=11, bold=True, color="FFFFFF")
BLACK = Font(name=FONT, size=11)
BLACK_B = Font(name=FONT, size=11, bold=True)
CENTER = Alignment(horizontal="center", vertical="center")
RIGHT = Alignment(horizontal="right", vertical="center")
THIN = Side(style="thin", color="CFC9B8")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def fmt(d):
    return f"{d.day}.{d.month}"


def main(src, dst):
    out = json.load(open(src, encoding="utf-8"))
    S = out["schedule"]
    days = [dt.date.fromisoformat(d) for d in out["days"]]        # 5.11 .. 25.11
    names = out["names"]
    ez_exit = dt.date.fromisoformat(out["ez_exit"])
    on_now = dict(out["on_base_now"]); on_now["IS"] = True
    hist = out["hist"]                 # base days through 4.11 inclusive
    hist_sh = out["hist_sh"]
    grid_days = [TODAY] + days         # 4.11 .. 25.11 (22 countable days in the grid)

    def state(p, d):
        if d == TODAY:
            return "מוצב" if on_now[p] else "בית"
        i = days.index(d)
        if p == "EZ" and d >= ez_exit:
            return "סיים"
        if p == "IS":
            return "משמרת" if S[p][i] else "בית"
        return "מוצב" if S[p][i] else "בית"

    wb = Workbook()
    ws = wb.active
    ws.title = "ג'אנט"
    ws.sheet_view.rightToLeft = True

    ws["A1"] = "ג'אנט יציאות – צוות אלמועלם, 4.11 עד 26.11"
    ws["A1"].font = Font(name=FONT, size=14, bold=True)
    ws["A2"] = "ירוק = מוצב, בהיר = בית, צהוב = שבת. יום העלייה נספר כיום מוצב, יום הירידה כיום בית. מי שיורד מחכה שהמחליף שלו הגיע."
    ws["A2"].font = Font(name=FONT, size=10, color="5B5E52")

    # header rows 4 (dates) and 5 (day of week)
    HR, DR = 4, 5
    ws.cell(HR, 1, "לוחם").font = BLACK_B
    ws.cell(DR, 1, "").fill = HEAD
    for j, d in enumerate(grid_days):
        c = ws.cell(HR, 2 + j, fmt(d))
        c.font = BLACK_B; c.alignment = CENTER; c.fill = SAT if d.weekday() == 5 else HEAD; c.border = BORDER
        c2 = ws.cell(DR, 2 + j, HEB_DOW[d.weekday()])
        c2.font = BLACK; c2.alignment = CENTER; c2.fill = SAT if d.weekday() == 5 else HEAD; c2.border = BORDER
    col_exit = 2 + len(grid_days)
    c = ws.cell(HR, col_exit, "26.11"); c.font = BLACK_B; c.alignment = CENTER; c.fill = HEAD; c.border = BORDER
    c = ws.cell(DR, col_exit, "ירידה"); c.font = BLACK; c.alignment = CENTER; c.fill = HEAD; c.border = BORDER
    totals_hdr = ["מוצב עד 3.11", "מוצב מ-4.11", "סה\"כ מוצב", "סה\"כ בית", "שבתות (מתוך 5)"]
    for k, h in enumerate(totals_hdr):
        c = ws.cell(HR, col_exit + 1 + k, h); c.font = BLACK_B; c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.fill = HEAD; c.border = BORDER
        ws.cell(DR, col_exit + 1 + k, "").fill = HEAD
    ws.cell(HR, 1).fill = HEAD; ws.cell(HR, 1).border = BORDER
    ws.row_dimensions[HR].height = 30

    first_col = get_column_letter(2)
    last_col = get_column_letter(1 + len(grid_days))         # last countable day column (25.11)
    sat_cols = [get_column_letter(2 + j) for j, d in enumerate(grid_days) if d.weekday() == 5]

    # David row
    r = DR + 1
    ws.cell(r, 1, "דוד אלמועלם (מפקד)").font = BLACK_B
    for j, d in enumerate(grid_days):
        c = ws.cell(r, 2 + j, "מוצב"); c.fill = GREEN_D; c.font = WHITE_B; c.alignment = CENTER; c.border = BORDER
    c = ws.cell(r, col_exit, "ירידה"); c.fill = GRAY; c.font = BLACK; c.alignment = CENTER; c.border = BORDER
    ws.cell(r, col_exit + 1, 13)                       # 22.10..3.11
    ws.cell(r, col_exit + 2, f'=COUNTIF({first_col}{r}:{last_col}{r},"מוצב")')
    ws.cell(r, col_exit + 3, f"={get_column_letter(col_exit + 1)}{r}+{get_column_letter(col_exit + 2)}{r}")
    ws.cell(r, col_exit + 4, f"=35-{get_column_letter(col_exit + 3)}{r}")
    ws.cell(r, col_exit + 5, 5)
    for k in range(5):
        c = ws.cell(r, col_exit + 1 + k); c.alignment = CENTER; c.border = BORDER; c.font = BLACK_B if k == 2 else BLACK

    # soldiers
    for p in ORDER:
        r += 1
        label = names[p] + (" (מפקד)" if p in CMD else "")
        ws.cell(r, 1, label).font = BLACK_B
        ws.cell(r, 1).alignment = RIGHT
        for j, d in enumerate(grid_days):
            st = state(p, d)
            c = ws.cell(r, 2 + j, st)
            c.alignment = CENTER; c.border = BORDER
            if st in ("מוצב", "משמרת"):
                c.fill = GREEN; c.font = WHITE_B
            elif st == "סיים":
                c.fill = GRAY; c.font = Font(name=FONT, size=10, color="6B6F60")
            else:
                c.fill = SAND; c.font = Font(name=FONT, size=11, color="6B6F60")
        last = state(p, days[-1])
        c = ws.cell(r, col_exit, "ירידה" if last in ("מוצב", "משמרת") else ("" if last == "סיים" else "בבית"))
        c.fill = GRAY; c.font = BLACK; c.alignment = CENTER; c.border = BORDER
        # history through 3.11 = history through 4.11 minus 4.11 if at base then
        h3 = hist[p] - (1 if on_now[p] else 0)
        ws.cell(r, col_exit + 1, h3)
        ws.cell(r, col_exit + 2, f'=COUNTIF({first_col}{r}:{last_col}{r},"מוצב")+COUNTIF({first_col}{r}:{last_col}{r},"משמרת")')
        ws.cell(r, col_exit + 3, f"={get_column_letter(col_exit + 1)}{r}+{get_column_letter(col_exit + 2)}{r}")
        total_days = (ez_exit - dt.date(2026, 10, 22)).days if p == "EZ" else 35
        ws.cell(r, col_exit + 4, f"={total_days}-{get_column_letter(col_exit + 3)}{r}")
        sat_terms = "+".join(f'COUNTIF({cl}{r},"מוצב")+COUNTIF({cl}{r},"משמרת")' for cl in sat_cols)
        ws.cell(r, col_exit + 5, f"={hist_sh[p]}+{sat_terms}")
        for k in range(5):
            c = ws.cell(r, col_exit + 1 + k); c.alignment = CENTER; c.border = BORDER; c.font = BLACK_B if k == 2 else BLACK
    last_row = r

    # presence row
    r += 1
    ws.cell(r, 1, "במוצב (כולל דוד)").font = BLACK_B
    for j, d in enumerate(grid_days):
        cl = get_column_letter(2 + j)
        c = ws.cell(r, 2 + j, f'=COUNTIF({cl}{DR + 1}:{cl}{last_row},"מוצב")+COUNTIF({cl}{DR + 1}:{cl}{last_row},"משמרת")')
        c.alignment = CENTER; c.font = BLACK_B; c.border = BORDER; c.fill = HEAD
    r += 1
    ws.cell(r, 1, "נדרש").font = BLACK
    for j, d in enumerate(grid_days):
        need = "" if d == TODAY else (9 if d < ez_exit else 8)
        c = ws.cell(r, 2 + j, need); c.alignment = CENTER; c.font = Font(name=FONT, size=10, color="6B6F60"); c.border = BORDER
    r += 2
    ws.cell(r, 1, "הערות").font = BLACK_B
    notes = [
        "\"מוצב עד 3.11\" לפי הסיכום של הצוות (קיאן 8 אחרי תיקון של יום יציאה שלא נרשם). \"מוצב מ-4.11\" נספר אוטומטית מהטבלה.",
        f"ערן: סיום התעסוקה המקוצרת ב-{fmt(ez_exit)}; סה\"כ הימים שלו מתוך {(ez_exit - dt.date(2026, 10, 22)).days}.",
        "אילן מגיע יומי: \"משמרת\" = יום משמרת, נספר כיום מוצב.",
        "9 במוצב כל יום עד 11.11, 8 מ-12.11. אין עליות וירידות בשבת.",
    ]
    for n in notes:
        r += 1
        ws.cell(r, 1, n).font = Font(name=FONT, size=10, color="5B5E52")

    ws.column_dimensions["A"].width = 26
    for j in range(len(grid_days) + 1):
        ws.column_dimensions[get_column_letter(2 + j)].width = 6.5
    for k in range(5):
        ws.column_dimensions[get_column_letter(col_exit + 1 + k)].width = 9
    ws.freeze_panes = ws.cell(DR + 1, 2)
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    # ---- sheet 2: per person moves -----------------------------------------
    ws2 = wb.create_sheet("עליות וירידות")
    ws2.sheet_view.rightToLeft = True
    ws2["A1"] = "מתי כל אחד עולה ויורד"; ws2["A1"].font = Font(name=FONT, size=14, bold=True)
    hdr = ["לוחם", "התוכנית מ-5.11", "סוגר שבתות", "סה\"כ מוצב", "סה\"כ בית"]
    for k, h in enumerate(hdr):
        c = ws2.cell(3, 1 + k, h); c.font = BLACK_B; c.fill = HEAD; c.border = BORDER; c.alignment = CENTER
    sat_idx = [i for i, d in enumerate(days) if d.weekday() == 5]
    rr = 3
    for p in ORDER:
        rr += 1
        seq = S[p][: days.index(ez_exit)] if p == "EZ" else S[p]
        parts = []
        prev = 1 if on_now[p] else 0
        for i, v in enumerate(seq):
            if v != prev:
                d = days[i]
                if p == "IS":
                    parts.append(("משמרות מ-" if v else "לא במשמרת מ-") + fmt(d))
                else:
                    parts.append(("עולה " if v else "יורד ") + fmt(d) + f" ({HEB_DOW_LONG[d.weekday()]})")
            prev = v
        if p == "EZ":
            parts.append(f"סיום התעסוקה {fmt(ez_exit)}")
        elif seq[-1] == 1:
            parts.append("יורד 26.11 עם כולם")
        else:
            parts.append("מסיים בבית")
        sats = [fmt(days[i]) for i in sat_idx if i < len(seq) and seq[i]]
        total_days = (ez_exit - dt.date(2026, 10, 22)).days if p == "EZ" else 35
        vals = [names[p] + (" (מפקד)" if p in CMD else ""), ", ".join(parts), ", ".join(sats) or "-",
                out["total"][p], total_days - out["total"][p]]
        for k, v in enumerate(vals):
            c = ws2.cell(rr, 1 + k, v); c.font = BLACK_B if k == 0 else BLACK; c.border = BORDER
            c.alignment = Alignment(horizontal="right" if k < 3 else "center", vertical="center", wrap_text=True)
    ws2.column_dimensions["A"].width = 26
    ws2.column_dimensions["B"].width = 70
    ws2.column_dimensions["C"].width = 22
    ws2.column_dimensions["D"].width = 12
    ws2.column_dimensions["E"].width = 12
    rr += 2
    ws2.cell(rr, 1, "סה\"כ מוצב ובית בגיליון זה הועתקו מהלוח; הנוסחאות נמצאות בגיליון \"ג'אנט\".").font = Font(name=FONT, size=10, color="5B5E52")

    wb.save(dst)
    print("wrote", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
