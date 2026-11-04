#!/usr/bin/env python3
"""
Fairness audit of a schedule JSON: every measure a soldier might compare,
per person, plus the team-level ranges.  Independent of the solver (uses rules.py).

    python3 audit.py janet.json
"""
import json
import sys

import rules as R

SHORT = {"IM": "איתי", "AH": "עלי", "MA": "מרדכי", "SA": "סאמר", "RH": "רפאת", "EY": "עילי", "AC": "אביאל",
         "IK": "איתמר", "LE": "ליאור", "EZ": "ערן", "KA": "קיאן", "SG": "סייף", "IS": "אילן"}
PROMISED = {"IM": 5, "AH": 5, "SA": 5, "RH": 5, "MA": 3, "EY": 7}   # index of promised exit day (10.11 -> 5, 8.11 -> 3, 12.11 -> 7)


def main(path):
    out = json.load(open(path, encoding="utf-8"))
    S = out["schedule"]
    params = out["params"]
    v = R.violations(S, params)
    m = R.metrics(S)
    print("hard rules:", "OK" if not v else v)
    print(f"ranges: days {m['range']}  Shabbatot {m['sh_range']}  combined {m['comb_range']}  excess {m['excess']}")
    print()
    hdr = f"{'person':>8} {'days':>4} {'home':>4} {'shab':>4} {'comb':>4} {'plan':>4} {'trips':>5} {'longest':>7} {'3-day':>5} {'home blocks':>12} {'wkend home':>10} {'consec':>6} {'fri up':>6} {'early':>5}"
    print(hdr)
    rows = []
    for p in R.PEOPLE:
        H = R.EZ_CUT if p == "EZ" else 21
        seq = S[p][:H]
        st = R.stints(seq)
        now = 1 if p in R.ON_BASE_NOW else 0
        ups = sum(1 for i in range(H) if seq[i] == 1 and (seq[i - 1] if i else now) == 0)
        pre = R.ON_BASE_NOW.get(p, 0)
        run, longest = pre, pre
        for x in seq:
            run = run + 1 if x else 0
            longest = max(longest, run)
        three = sum(1 for s_, a, b in st if s_ == 1 and (b - a + 1) == 3 and a > 0)
        home_blocks = [b - a + 1 for s_, a, b in st if s_ == 0]
        wk = sum(1 for i in R.SAT if i - 1 < H and seq[i - 1] == 0 and (i >= H or seq[i] == 0))
        sats = [i for i in R.SAT if i < H and seq[i]]
        consec = sum(1 for a, b in zip(sats, sats[1:]) if b - a == 7)
        fri = sum(1 for i in range(H) if seq[i] == 1 and (seq[i - 1] if i else now) == 0 and R.DAYS[i].weekday() == 4)
        early = 0
        if p in PROMISED:
            first_home = next((i for i in range(H) if seq[i] == 0), None)
            early = max(0, PROMISED[p] - first_home) if first_home is not None else 0
        days_total = 21 if p == "EZ" else 35
        tot = m["total"][p]
        rows.append((p, tot, days_total - tot, m["shabbat"][p], (tot + m["shabbat"][p]) if p != "EZ" else "-", sum(seq), ups, longest, three,
                     "/".join(map(str, home_blocks)) or "-", wk, consec, fri, early))
    for r in rows:
        print(f"{SHORT[r[0]]:>8} {r[1]:>4} {r[2]:>4} {r[3]:>4} {str(r[4]):>4} {r[5]:>4} {r[6]:>5} {r[7]:>7} {r[8]:>5} {r[9]:>12} {r[10]:>10} {r[11]:>6} {r[12]:>6} {r[13]:>5}")
    non_ez = [r for r in rows if r[0] not in ("EZ",)]
    print()
    print("team: weekends at home (Fri+Sat) range:", max(r[10] for r in non_ez) - min(r[10] for r in non_ez),
          "| trips range:", max(r[6] for r in non_ez) - min(r[6] for r in non_ez),
          "| people with consecutive Shabbatot:", [SHORT[r[0]] for r in non_ez if r[11]],
          "| Friday arrivals:", sum(r[12] for r in rows),
          "| 3-day base stints:", sum(r[8] for r in rows),
          "| early descents (days):", sum(r[13] for r in rows))


if __name__ == "__main__":
    main(sys.argv[1])
