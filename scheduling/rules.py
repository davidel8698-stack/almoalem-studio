#!/usr/bin/env python3
"""
The hard rules as one pure function, shared by the local-search improver and
the audit.  Independent re-implementation (does not import solver.py).

    violations(schedule, params) -> list of strings (empty = legal schedule)
schedule: {person: [0/1]*21} for 5.11..25.11; params: {min_base, min_home, max_base}
"""
import datetime as dt

DAYS = [dt.date(2026, 11, 5) + dt.timedelta(days=i) for i in range(21)]
SAT = [i for i, d in enumerate(DAYS) if d.weekday() == 5]
EZ_EXIT = dt.date(2026, 11, 12)
EZ_CUT = DAYS.index(EZ_EXIT)                       # Eran's sequence is meaningful for i < EZ_CUT
NEED = [9] * EZ_CUT + [8] * (21 - EZ_CUT)          # incl. David
COMMANDERS = ["IM", "AC", "EZ"]
PAIRS = [("AH", "RH"), ("KA", "SG")]
FIXED_HOME = {"IM": [DAYS.index(dt.date(2026, 11, 17))], "MA": [DAYS.index(dt.date(2026, 11, 8))],
              "KA": [DAYS.index(dt.date(2026, 11, 19))], "SG": [DAYS.index(dt.date(2026, 11, 19))],
              "LE": [DAYS.index(dt.date(2026, 11, 5))],
              "EZ": [0, 1, 2]}
FIXED_BASE = {"EZ": [3, 4, 5, 6]}
ON_BASE_NOW = {"IM": 4, "AH": 3, "MA": 3, "SA": 3, "RH": 3, "EY": 1, "IS": 1}     # stint length already running on 4.11 (Ilan: shift on 4.11)
HOME_NOW = ["AC", "IK", "LE", "EZ", "KA", "SG"]
ILAN_MAX = 7
PEOPLE = ["IM", "AH", "MA", "SA", "RH", "EY", "AC", "IK", "LE", "EZ", "KA", "SG", "IS"]
HIST = {"IM": 6, "AH": 6, "MA": 6, "SA": 6, "RH": 6, "EY": 5, "AC": 6, "IK": 7, "LE": 8, "EZ": 8, "KA": 8, "SG": 9, "IS": 6}
HIST_SH = {"IM": 1, "AH": 1, "MA": 1, "SA": 1, "RH": 1, "EY": 0, "AC": 0, "IK": 1, "LE": 1, "EZ": 1, "KA": 2, "SG": 2, "IS": 0}


def stints(seq):
    res, cur, start = [], seq[0], 0
    for i in range(1, len(seq)):
        if seq[i] != cur:
            res.append((cur, start, i - 1)); cur, start = seq[i], i
    res.append((cur, start, len(seq) - 1))
    return res


def violations(S, params):
    V = []
    mb, mh, MB = params["min_base"], params["min_home"], params["max_base"]
    for i in range(21):
        present = 1 + sum(S[p][i] for p in PEOPLE if not (p == "EZ" and i >= EZ_CUT))
        if present < NEED[i]:
            V.append(f"presence {present} < {NEED[i]} on {DAYS[i]}")
        if 1 + sum(S[c][i] for c in COMMANDERS if not (c == "EZ" and i >= EZ_CUT)) < 2:
            V.append(f"commanders < 2 on {DAYS[i]}")
    for i in range(EZ_CUT, 21):
        if S["EZ"][i]:
            V.append(f"Eran at base after release on {DAYS[i]}")
    for p, idxs in FIXED_HOME.items():
        for i in idxs:
            if S[p][i]:
                V.append(f"{p} must be home on {DAYS[i]}")
    for p, idxs in FIXED_BASE.items():
        for i in idxs:
            if not S[p][i]:
                V.append(f"{p} must be at base on {DAYS[i]}")
    for a, b in PAIRS:
        diff = sum(1 for i in range(21) if S[a][i] != S[b][i])
        if diff > (1 if (a, b) == ("KA", "SG") else 0):
            V.append(f"pair {a}+{b} differ on {diff} days")
    for p in PEOPLE:
        if p == "IS":
            continue
        for s in SAT:
            if S[p][s] != S[p][s - 1]:
                V.append(f"{p} moves on Shabbat {DAYS[s]}")
    for p in PEOPLE:
        H = EZ_CUT - 1 if p == "EZ" else 20
        seq = S[p][: H + 1]
        st = stints(seq)
        pre = ON_BASE_NOW.get(p, 0)
        # max base run incl. pre-plan days
        run, longest = pre, pre
        for v in seq:
            run = run + 1 if v else 0
            longest = max(longest, run)
        cap = ILAN_MAX if p == "IS" else MB
        if longest > cap:
            V.append(f"{p} base run {longest} > {cap}")
        if p == "IS":
            continue
        for k, (state, a, b) in enumerate(st):
            L = b - a + 1
            first, last = k == 0, k == len(st) - 1
            if state == 1 and not first and L < mb:
                V.append(f"{p} base stint {DAYS[a]} is {L} < {mb}")
            if state == 0 and not first and not last and L < mh:
                V.append(f"{p} home block {DAYS[a]} is {L} < {mh}")
            # a stint that continues the 4.11 state is fine; a flipped first stint must obey minimums too
            if first:
                now_base = p in ON_BASE_NOW
                if state == 1 and not now_base and L < mb and not last:
                    V.append(f"{p} first base stint is {L} < {mb}")
                if state == 0 and now_base and L < mh and not last:
                    V.append(f"{p} first home block is {L} < {mh}")
    return V


def metrics(S):
    tot = {p: HIST[p] + sum(S[p][: (EZ_CUT if p == "EZ" else 21)]) for p in PEOPLE}
    sh = {p: HIST_SH[p] + sum(S[p][i] for i in SAT if not (p == "EZ" and i >= EZ_CUT)) for p in PEOPLE}
    non_ez = [p for p in PEOPLE if p != "EZ"]
    comb = {p: tot[p] + sh[p] for p in non_ez}
    rng = lambda d: max(d.values()) - min(d.values())
    excess = sum((1 + sum(S[p][i] for p in PEOPLE if not (p == "EZ" and i >= EZ_CUT))) - NEED[i] for i in range(21))
    return dict(total=tot, shabbat=sh, comb=comb,
                comb_range=rng(comb), range=rng({p: tot[p] for p in non_ez}),
                sh_range=rng({p: sh[p] for p in non_ez}), excess=excess)
