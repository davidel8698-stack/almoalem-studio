#!/usr/bin/env python3
"""
Independent checker for a schedule JSON produced by solver.py.
Re-derives every hard rule from scratch (does not import the solver's model)
and prints PASS/FAIL lines.  Exit code 1 on any failure.

    python3 verify.py schedule.json
"""
import datetime as dt
import json
import math
import sys

START = dt.date(2026, 10, 22)
LAST = dt.date(2026, 11, 25)

NEED = {14: 9, 13: 8}                          # confirmed by the team commander (5.11)
ILAN = dict(max_base=6)                        # commutes daily; no min-stint / Shabbat-move rules

RULES = dict(
    commanders={"IM", "AC", "EZ"},            # + David always
    pairs=[("AH", "RH"), ("KA", "SG")],
    fixed_home={"IM": ["2026-11-17"], "MA": ["2026-11-08"], "KA": ["2026-11-19"], "SG": ["2026-11-19"],
                "LE": ["2026-11-05"]},
    on_base_4_11={"IM", "AH", "MA", "SA", "RH", "EY"},
    stint_len_4_11={"IM": 4, "AH": 3, "MA": 3, "SA": 3, "RH": 3, "EY": 1},
    planned_exit={"IM": "2026-11-10", "AH": "2026-11-10", "SA": "2026-11-10", "RH": "2026-11-10",
                  "MA": "2026-11-08", "EY": "2026-11-12"},
    hist={"IM": 6, "AH": 6, "MA": 6, "SA": 6, "RH": 6, "EY": 5, "AC": 6, "IK": 7, "LE": 8,
          "EZ": 8, "KA": 9, "SG": 9, "IS": 6},
    hist_sh={"IM": 1, "AH": 1, "MA": 1, "SA": 1, "RH": 1, "EY": 0, "AC": 0, "IK": 1, "LE": 1,
             "EZ": 1, "KA": 2, "SG": 2, "IS": 0},
)


def main(path):
    out = json.load(open(path, encoding="utf-8"))
    S = out["schedule"]
    days = [dt.date.fromisoformat(d) for d in out["days"]]
    N = len(days)
    V = out["params"]
    ez_exit = dt.date.fromisoformat(out["ez_exit"])
    ilan_counts = out.get("ilan_counts", True)
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + msg)
        ok = ok and cond

    check(days[0] == dt.date(2026, 11, 5) and days[-1] == LAST and N == 21, "horizon is 5.11–25.11 (21 days)")
    check(set(S) == set(RULES["hist"]), "all 13 scheduled people present (David is implicit)")

    # presence
    worst = None
    for i, d in enumerate(days):
        roster = 14 if d < ez_exit else 13
        need = NEED[roster]
        present = 1 + sum(S[p][i] for p in S if (ilan_counts or p != "IS"))
        if present < need:
            worst = (d, present, need)
            break
    check(worst is None, f"presence rule every day ({NEED[14]} of 14, {NEED[13]} of 13 from {ez_exit.day}.{ez_exit.month})" +
          (f" — violated {worst}" if worst else ""))

    # commanders
    bad = [days[i] for i in range(N) if 1 + sum(S[c][i] for c in RULES["commanders"]) < 2]
    check(not bad, f"≥2 commanders every day (David + one of Itay/Aviel/Eran){' — bad: ' + str(bad) if bad else ''}")

    # Eran released
    ez_idx = [i for i, d in enumerate(days) if d >= ez_exit]
    check(all(S["EZ"][i] == 0 for i in ez_idx), f"Eran is home from his exit day {ez_exit.isoformat()}")

    # fixed home days
    for p, ds in RULES["fixed_home"].items():
        for dstr in ds:
            i = days.index(dt.date.fromisoformat(dstr))
            check(S[p][i] == 0, f"{p} home on {dstr}")

    # pairs
    for a, b in RULES["pairs"]:
        check(S[a] == S[b], f"pair {a}+{b} always together")

    # no moves on Shabbat (Ilan commutes daily and is exempt)
    sat = [i for i, d in enumerate(days) if d.weekday() == 5]
    check(all(S[p][i] == S[p][i - 1] for p in S if p != "IS" for i in sat), "nobody goes up or down on Shabbat")

    # stint lengths
    def stints(seq):
        res, cur, start = [], seq[0], 0
        for i in range(1, len(seq)):
            if seq[i] != cur:
                res.append((cur, start, i - 1)); cur, start = seq[i], i
        res.append((cur, start, len(seq) - 1))
        return res

    for p in S:
        H = (days.index(ez_exit) - 1) if p == "EZ" else N - 1
        seq = S[p][: H + 1]
        st = stints(seq)
        if p != "IS":
            for k, (state, a, b) in enumerate(st):
                L = b - a + 1
                first = (k == 0)
                last = (k == len(st) - 1)
                if state == 1 and not first:
                    check(L >= V["min_base"], f"{p}: base stint {days[a]}..{days[b]} has ≥{V['min_base']} days ({L})")
                if state == 0 and not first and not last:
                    check(L >= V["min_home"], f"{p}: home stint {days[a]}..{days[b]} has ≥{V['min_home']} days ({L})")
        # max base stint incl. the stint running on 4.11
        pre = RULES["stint_len_4_11"].get(p, 0) if p in RULES["on_base_4_11"] else 0
        run = pre
        longest = 0
        for v in seq:
            run = run + 1 if v else 0
            longest = max(longest, run)
        cap = ILAN["max_base"] if p == "IS" else V["max_base"]
        check(longest <= cap, f"{p}: longest base stint {longest} ≤ {cap}")

    # continuity with 4.11: people at base keep going at least until promised exit
    for p, ex in RULES["planned_exit"].items():
        exd = dt.date.fromisoformat(ex)
        early = [days[i] for i in range(N) if days[i] < exd and S[p][i] == 0]
        print(f"INFO {p}: sent home before promised exit {ex}: {[d.isoformat() for d in early] or 'no'}")

    # totals & Shabbatot
    tot = {p: RULES["hist"][p] + sum(S[p]) for p in S}
    sh = {p: RULES["hist_sh"][p] + sum(S[p][i] for i in sat) for p in S}
    check(tot == out["total"], "totals in JSON match recomputation")
    check(sh == out["shabbat"], "Shabbat totals in JSON match recomputation")
    non_ez = [p for p in S if p != "EZ"]
    rng = max(tot[p] for p in non_ez) - min(tot[p] for p in non_ez)
    shr = max(sh[p] for p in non_ez) - min(sh[p] for p in non_ez)
    print(f"INFO totals (of 35): {dict(sorted(tot.items(), key=lambda kv: kv[1]))}")
    print(f"INFO Shabbatot (of 5): {dict(sorted(sh.items(), key=lambda kv: kv[1]))}")
    print(f"INFO range of totals = {rng}, range of Shabbatot = {shr}, Eran {tot['EZ']}/21 and {sh['EZ']} Shabbatot")
    excess = sum((1 + sum(S[p][i] for p in S)) - NEED[14 if days[i] < ez_exit else 13] for i in range(N))
    print(f"INFO base person-days above the rule's minimum: {excess}")
    print("ALL PASS" if ok else "SOME FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
