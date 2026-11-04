#!/usr/bin/env python3
"""
Balanced home/base rotation ("ג'אנט יציאות") solver for צוות אלמועלם,
planning window 5.11.26 – 25.11.26 (26.11 = ירידה מקו, exit day for everyone).

Model: CP-SAT (OR-Tools).  Every (person, day) is a boolean: 1 = at the outpost
(מוצב) that day, 0 = at home.  Counting follows the team's own convention:
the day you go up counts as a base day, the day you go down counts as a home day
("נכנס 1.11, יום 4 ב-4.11, יוצא 10.11").  Total countable days: 22.10–25.11 = 35.

Hard rules
  * presence every day as the commander confirmed: 9 of 14, 8 of 13 once Eran
    goes down on 12.11 (that is the team's reading of "65%"; see NEED)
  * ≥ 2 commanders every day (David + at least one of Itay / Aviel / Eran)
  * fixed home days: Itay 17.11, Mordechai 8.11, Kian + Saif 19.11
  * pairs move together: Ali + Rafat, Kian + Saif
  * nobody goes up or down on Shabbat
  * minimum / maximum stint lengths (per variant), daily swap cap

Objective (weighted, roughly lexicographic)
  1. equal FINAL base-day totals over the whole deployment (history + plan)
  2. not one base day more than the 65% rule needs
  3. equal Shabbat totals
  4. keep the exits already promised, few trips, no mass-swap days

Usage:  python3 solver.py [--variant G_commander] [--json out.json] [--time 120]
                          [--need14 9 --need13 8] [--no-ilan-count] [--eran-exit 12.11]
                          [-w early=2500 ...]
"""
import argparse
import datetime as dt
import json
import math
import sys

from ortools.sat.python import cp_model

# ----------------------------------------------------------------------------
# Calendar
# ----------------------------------------------------------------------------
START = dt.date(2026, 10, 22)          # עלייה לקו
TODAY = dt.date(2026, 11, 4)           # status snapshot the team gave
PLAN_FROM = dt.date(2026, 11, 5)       # first day the new plan may change anything
LAST_NIGHT = dt.date(2026, 11, 25)     # last countable day; 26.11 everyone goes down
EXIT = dt.date(2026, 11, 26)
DAYS = [PLAN_FROM + dt.timedelta(days=i) for i in range((LAST_NIGHT - PLAN_FROM).days + 1)]
N = len(DAYS)                          # 21 days: 5.11 .. 25.11
TOTAL_DAYS = (LAST_NIGHT - START).days + 1    # 35
IDX = {d: i for i, d in enumerate(DAYS)}
SATURDAYS = [i for i, d in enumerate(DAYS) if d.weekday() == 5]   # 7.11, 14.11, 21.11
FRIDAYS = [i for i, d in enumerate(DAYS) if d.weekday() == 4]
HEB_DOW = {0: "ב'", 1: "ג'", 2: "ד'", 3: "ה'", 4: "ו'", 5: "ש'", 6: "א'"}


def D(day, month=11):
    return IDX[dt.date(2026, month, day)]


# ----------------------------------------------------------------------------
# People.  hist_base = base days 22.10–4.11 inclusive (14 days).
# hist_sh = Shabbatot closed so far (of 2).  on_base_now = status on 4.11.
# stint_len = length of the stint in progress on 4.11 (days, incl. 4.11).
# planned_exit = exit date in the plan that is currently running (if at base).
# ----------------------------------------------------------------------------
PEOPLE = {
    # key: dict(name, cmd, hist, hist_sh, now, stint, planned_exit)
    "IM": dict(name="איתי מדר",            cmd=True,  hist=6, hist_sh=1, now=True,  stint=4, exit=dt.date(2026, 11, 10)),
    "AH": dict(name="עלי חאשן",            cmd=False, hist=6, hist_sh=1, now=True,  stint=3, exit=dt.date(2026, 11, 10)),
    "MA": dict(name="מרדכי מנחם אלמקייס",  cmd=False, hist=6, hist_sh=1, now=True,  stint=3, exit=dt.date(2026, 11, 8)),
    "SA": dict(name="סאמר עראידה",         cmd=False, hist=6, hist_sh=1, now=True,  stint=3, exit=dt.date(2026, 11, 10)),
    "RH": dict(name="רפאת חיחי",           cmd=False, hist=6, hist_sh=1, now=True,  stint=3, exit=dt.date(2026, 11, 10)),
    "EY": dict(name="עילי רופא",           cmd=False, hist=5, hist_sh=0, now=True,  stint=1, exit=dt.date(2026, 11, 12)),
    "AC": dict(name="אביאל כהן",           cmd=True,  hist=6, hist_sh=0, now=False, stint=8, exit=None),   # home since 28.10
    "IK": dict(name="איתמר קרני",          cmd=False, hist=7, hist_sh=1, now=False, stint=7, exit=None),   # home since 29.10
    "LE": dict(name="ליאור אבן חן",        cmd=False, hist=8, hist_sh=1, now=False, stint=6, exit=None),   # home since 30.10
    "EZ": dict(name="ערן זכי נתן",         cmd=True,  hist=8, hist_sh=1, now=False, stint=6, exit=None),   # home since 30.10
    "KA": dict(name="קיאן אבו זידאן",      cmd=False, hist=9, hist_sh=2, now=False, stint=5, exit=None),   # home since 31.10
    "SG": dict(name="סייף גאנם",           cmd=False, hist=9, hist_sh=2, now=False, stint=5, exit=None),   # home since 31.10
    "IS": dict(name="אילן שייביץ",         cmd=False, hist=6, hist_sh=0, now=None,  stint=0, exit=None),   # day shifts; on 4.11
}
DAVID = "דוד אלמועלם"
COMMANDERS = [k for k, v in PEOPLE.items() if v["cmd"]]
PAIRS = [("AH", "RH"), ("KA", "SG")]
FIXED_HOME = {"IM": [dt.date(2026, 11, 17)], "MA": [dt.date(2026, 11, 8)],
              "KA": [dt.date(2026, 11, 19)], "SG": [dt.date(2026, 11, 19)],
              "LE": [dt.date(2026, 11, 5)]}     # child's surgery; can come up late on Friday 6.11
EZ_EXIT_DEFAULT = dt.date(2026, 11, 12)      # Eran's last day; from then the roster is 13
NOT_EZ = [k for k in PEOPLE if k != "EZ"]
# Presence the team requires (incl. David), by roster size.  Confirmed by the
# team commander: 9 of 14 (not 10), and 8 of 13 once Eran is released.
NEED = {14: 9, 13: 8}
# Ilan commutes: a "base day" for him is a day shift, he sleeps at home, and he
# counts toward the 65% on those days.  His blocks follow looser rules.
ILAN = dict(min_base=2, min_home=1, max_base=7)


# ----------------------------------------------------------------------------
# Variants (structural parameters that are a judgment call)
# ----------------------------------------------------------------------------
VARIANTS = {
    "A_balanced":    dict(min_base=4, min_home=3, max_base=12, max_churn=6, w_trans=1.0, w_long=1.0, long_from=10, w_short=0.0),
    "B_longblocks":  dict(min_base=5, min_home=4, max_base=13, max_churn=6, w_trans=2.0, w_long=0.0, long_from=13, w_short=0.0),
    "C_shortblocks": dict(min_base=4, min_home=3, max_base=10, max_churn=6, w_trans=0.5, w_long=2.0, long_from=8, w_short=0.0),
    "D_home4":       dict(min_base=4, min_home=4, max_base=12, max_churn=6, w_trans=1.0, w_long=1.0, long_from=10, w_short=0.0),
    "E_home4_base11": dict(min_base=4, min_home=4, max_base=11, max_churn=6, w_trans=1.0, w_long=1.0, long_from=9, w_short=0.0),
    # like A, but a home block of exactly 3 days costs half a base day (soft)
    "F_soft4":       dict(min_base=4, min_home=3, max_base=12, max_churn=6, w_trans=1.0, w_long=1.0, long_from=10, w_short=1.0),
    # The commander's rules (5.11): max 8 base days in a row, home blocks of at
    # least 4 days, and try hard for 5 (a 4-day block costs w_short × short_home).
    "G_commander":   dict(min_base=4, min_home=4, max_base=8, max_churn=6, w_trans=1.0, w_long=0.0, long_from=8, w_short=1.0),
    "H_commander_5": dict(min_base=4, min_home=5, max_base=8, max_churn=6, w_trans=1.0, w_long=0.0, long_from=8, w_short=0.0),
    # Only the commander's own rules are hard here (max 8 base, min 4 home); the
    # self-imposed minimum base stint is relaxed to 3 and the daily swap cap to 8,
    # so fairness is limited by the real rules alone.
    "I_fair":        dict(min_base=3, min_home=4, max_base=8, max_churn=8, w_trans=1.0, w_long=0.0, long_from=8, w_short=1.0),
}

WEIGHTS = dict(
    range=10000,      # one unit of range of final totals  (≈ 3 base days)
    dev=1000,         # per half-day deviation from the group midpoint
    ez=100,           # Eran ratio deviation, 72 units = one day
    base=3000,        # one base day for anyone beyond the rule's need
    sh_range=8000,    # range of final Shabbat totals
    sh_dev=500,       # per half-Shabbat deviation from midpoint
    ez_sh=500,        # Eran's Shabbat ratio
    early=2500,       # per day someone is sent home before the exit already promised
    fri_arrive=300,   # going up on a Friday
    trans=300,        # per trip (× variant multiplier)
    churn=500,        # per swap beyond 4 on one day
    long=500,         # per base day beyond long_from in one stint (× variant multiplier)
    short_home=4000,  # per home block of exactly min_home days that ends before the end of service (× w_short)
    comb_range=0,     # range of the combined burden score (base days + Shabbatot) over the deployment
    comb_dev=0,       # per half-unit deviation of the combined score from the group midpoint
    ez_days=0,        # per base day Eran does in the plan (to give him home time before his release)
)


def build_and_solve(variant, time_limit=120, need14=None, need13=None, ilan_counts=True,
                    ez_exit=EZ_EXIT_DEFAULT, log=False, weights=None, hard=None,
                    ez_home_from=None, workers=4):
    """hard: optional caps {"range": r, "sh_range": s, "comb_range": c, "excess": e,
    "ez_max_days": k}; ez_home_from: date from which Eran stays home for good."""
    V = VARIANTS[variant]
    W = dict(WEIGHTS, **(weights or {}))
    HARD = hard or {}
    m = cp_model.CpModel()
    P = list(PEOPLE)
    x = {(p, i): m.NewBoolVar(f"x_{p}_{i}") for p in P for i in range(N)}

    ez_last_night = ez_exit - dt.timedelta(days=1)
    ez_last = IDX[ez_last_night] if ez_last_night in IDX else -1
    horizon = {p: (N - 1 if p != "EZ" else ez_last) for p in P}

    # ---- roster / need per day --------------------------------------------
    def roster(i):
        return 14 if DAYS[i] <= ez_last_night else 13

    def need(i):
        r = roster(i)
        if r == 14 and need14 is not None:
            return need14
        if r == 13 and need13 is not None:
            return need13
        return NEED[r]

    def pv(p, key):
        """Structural parameter for person p (Ilan has his own)."""
        return ILAN[key] if (p == "IS" and key in ILAN) else V[key]

    # ---- Eran: released -----------------------------------------------------
    for i in range(N):
        if i > ez_last:
            m.Add(x["EZ", i] == 0)
        if ez_home_from is not None and DAYS[i] >= ez_home_from:
            m.Add(x["EZ", i] == 0)
    if "ez_max_days" in HARD:
        m.Add(sum(x["EZ", i] for i in range(N)) <= HARD["ez_max_days"])
    for d in HARD.get("ez_home", []):          # dates Eran must be home
        m.Add(x["EZ", IDX[d]] == 0)
    for d in HARD.get("ez_base", []):          # dates Eran must be at the outpost
        m.Add(x["EZ", IDX[d]] == 1)

    # ---- presence rule -----------------------------------------------------
    for i in range(N):
        present = [x[p, i] for p in P if (ilan_counts or p != "IS")]
        m.Add(sum(present) + 1 >= need(i))             # +1 = David
    # ---- commanders --------------------------------------------------------
    for i in range(N):
        m.Add(sum(x[c, i] for c in COMMANDERS) >= 1)   # + David = 2
    # ---- fixed home days ---------------------------------------------------
    for p, dates in FIXED_HOME.items():
        for d in dates:
            m.Add(x[p, IDX[d]] == 0)
    # ---- pairs -------------------------------------------------------------
    for a, b in PAIRS:
        for i in range(N):
            m.Add(x[a, i] == x[b, i])
    # ---- nobody moves on Shabbat (Ilan commutes daily, so he is exempt) -----
    for p in P:
        if p == "IS":
            continue
        for s in SATURDAYS:
            m.Add(x[p, s] == x[p, s - 1])

    # ---- transitions -------------------------------------------------------
    arrive, depart = {}, {}
    for p in P:
        for i in range(horizon[p] + 1):
            a = m.NewBoolVar(f"arr_{p}_{i}")
            d = m.NewBoolVar(f"dep_{p}_{i}")
            arrive[p, i], depart[p, i] = a, d
            if i == 0:
                now = PEOPLE[p]["now"]
                if now is None:                          # Ilan: free start
                    m.Add(a == 0)
                    m.Add(d == 0)
                elif now:
                    m.Add(a == 0)
                    m.Add(d == 1 - x[p, 0])
                else:
                    m.Add(a == x[p, 0])
                    m.Add(d == 0)
            else:
                m.Add(a >= x[p, i] - x[p, i - 1])
                m.Add(a <= x[p, i])
                m.Add(a <= 1 - x[p, i - 1])
                m.Add(d >= x[p, i - 1] - x[p, i])
                m.Add(d <= x[p, i - 1])
                m.Add(d <= 1 - x[p, i])

    # ---- stint lengths -----------------------------------------------------
    for p in P:
        H = horizon[p]
        mb, mh = pv(p, "min_base"), pv(p, "min_home")
        for i in range(H + 1):
            # an arrival starts a base stint of at least min_base days, fully
            # inside the person's service (no "come up for the last two nights")
            if i + mb - 1 > H:
                m.Add(arrive[p, i] == 0)
            else:
                for k in range(mb):
                    m.Add(x[p, i + k] == 1).OnlyEnforceIf(arrive[p, i])
            # a departure starts a home stint of at least min_home days, unless
            # it simply runs to the end of service
            for k in range(mh):
                if i + k <= H:
                    m.Add(x[p, i + k] == 0).OnlyEnforceIf(depart[p, i])

    # maximum base stint (sliding window that includes the stint in progress)
    for p in P:
        now = PEOPLE[p]["now"]
        pre = [] if now is None else [1 if now else 0] * PEOPLE[p]["stint"]
        MB = pv(p, "max_base")
        WIN = MB + 1
        for end in range(N):
            start = end - WIN + 1
            terms, const = [], 0
            for j in range(start, end + 1):
                if j >= 0:
                    terms.append(x[p, j])
                else:
                    kk = len(pre) + j
                    if kk >= 0:
                        const += pre[kk]
            if terms:
                m.Add(sum(terms) + const <= MB)

    # ---- daily churn -------------------------------------------------------
    churn_over = []
    for i in range(N):
        c = sum(arrive[p, i] + depart[p, i] for p in P if (p, i) in arrive)
        m.Add(c <= V["max_churn"])
        over = m.NewIntVar(0, 30, f"over_{i}")
        m.Add(over >= c - 4)
        churn_over.append(over)

    # ---- totals ------------------------------------------------------------
    total = {}
    for p in P:
        total[p] = m.NewIntVar(0, 40, f"tot_{p}")
        m.Add(total[p] == PEOPLE[p]["hist"] + sum(x[p, i] for i in range(N)))
    tmax = m.NewIntVar(0, 40, "tmax")
    tmin = m.NewIntVar(0, 40, "tmin")
    for p in NOT_EZ:
        m.Add(tmax >= total[p])
        m.Add(tmin <= total[p])
    devs = []
    for p in NOT_EZ:
        dv = m.NewIntVar(0, 100, f"dev_{p}")
        m.Add(dv >= 2 * total[p] - (tmax + tmin))
        m.Add(dv >= (tmax + tmin) - 2 * total[p])
        devs.append(dv)
    # Eran: same base ratio over his shorter service
    ez_days = (ez_last_night - START).days + 1            # 21
    ez_dev = m.NewIntVar(0, 5000, "ez_dev")
    m.Add(ez_dev >= 2 * TOTAL_DAYS * total["EZ"] - ez_days * (tmax + tmin))
    m.Add(ez_dev >= ez_days * (tmax + tmin) - 2 * TOTAL_DAYS * total["EZ"])

    # ---- Shabbatot ---------------------------------------------------------
    sh = {}
    for p in P:
        sh[p] = m.NewIntVar(0, 5, f"sh_{p}")
        m.Add(sh[p] == PEOPLE[p]["hist_sh"] + sum(x[p, s] for s in SATURDAYS))
    shmax = m.NewIntVar(0, 5, "shmax")
    shmin = m.NewIntVar(0, 5, "shmin")
    for p in NOT_EZ:
        m.Add(shmax >= sh[p])
        m.Add(shmin <= sh[p])
    sh_devs = []
    for p in NOT_EZ:
        dv = m.NewIntVar(0, 10, f"shdev_{p}")
        m.Add(dv >= 2 * sh[p] - (shmax + shmin))
        m.Add(dv >= (shmax + shmin) - 2 * sh[p])
        sh_devs.append(dv)
    # Eran can only reach 3 Shabbatot (of 5 for the others): |10·sh_EZ − 3·(max+min)|
    ez_sh_dev = m.NewIntVar(0, 100, "ez_sh_dev")
    m.Add(ez_sh_dev >= 10 * sh["EZ"] - 3 * (shmax + shmin))
    m.Add(ez_sh_dev >= 3 * (shmax + shmin) - 10 * sh["EZ"])

    # ---- combined burden: base days + Shabbatot (one Shabbat ~ one day) -------
    comb = {}
    for p in NOT_EZ:
        comb[p] = m.NewIntVar(0, 50, f"comb_{p}")
        m.Add(comb[p] == total[p] + sh[p])
    cmax = m.NewIntVar(0, 50, "cmax")
    cmin = m.NewIntVar(0, 50, "cmin")
    for p in NOT_EZ:
        m.Add(cmax >= comb[p])
        m.Add(cmin <= comb[p])
    comb_devs = []
    for p in NOT_EZ:
        dv = m.NewIntVar(0, 100, f"cdev_{p}")
        m.Add(dv >= 2 * comb[p] - (cmax + cmin))
        m.Add(dv >= (cmax + cmin) - 2 * comb[p])
        comb_devs.append(dv)
    # ---- hard caps (used by the feasibility frontier) ------------------------
    if "range" in HARD:
        m.Add(tmax - tmin <= HARD["range"])
    if "sh_range" in HARD:
        m.Add(shmax - shmin <= HARD["sh_range"])
    if "comb_range" in HARD:
        m.Add(cmax - cmin <= HARD["comb_range"])
    excess_expr = sum(x[p, i] for p in P for i in range(N)) + N - sum(need(i) for i in range(N))
    if "excess" in HARD:
        m.Add(excess_expr <= HARD["excess"])

    # ---- keep promised exits (soft): home before the promised exit costs ----
    early = []
    for p in P:
        ex = PEOPLE[p]["exit"]
        if ex is None:
            continue
        for i in range(N):
            if DAYS[i] < ex:
                early.append(1 - x[p, i])

    # ---- Friday arrivals (soft) --------------------------------------------
    fri_arr = [arrive[p, i] for p in P for i in FRIDAYS if (p, i) in arrive]

    # ---- long stints (soft) ------------------------------------------------
    long_pen = []
    if V["w_long"]:
        L = V["long_from"]
        for p in P:
            for i in range(N - L):
                b = m.NewBoolVar(f"long_{p}_{i}")
                m.Add(sum(x[p, j] for j in range(i, i + L + 1)) - L <= b)
                long_pen.append(b)

    # ---- home blocks of exactly min_home days (soft: prefer one day longer) --
    short_home = []
    if V.get("w_short", 0):
        L = V["min_home"]
        for p in P:
            if p == "IS":
                continue
            H = horizon[p]
            for i in range(1, H + 1):                 # i == 0 is the stint already running
                if i + L <= H:
                    b = m.NewBoolVar(f"short_{p}_{i}")
                    # b >= depart[i] + x[i+L] - 1  (home on i..i+L-1 and back on i+L)
                    m.Add(b >= depart[p, i] + x[p, i + L] - 1)
                    short_home.append(b)

    # trips: Ilan's daily commute counts half (a switch for him is not a trip)
    trips_main = sum(arrive[k] + depart[k] for k in arrive if k[0] != "IS")
    trips_ilan = sum(arrive[k] + depart[k] for k in arrive if k[0] == "IS")
    n_trans2 = 2 * trips_main + trips_ilan
    total_base = sum(total[p] for p in P)
    m.Minimize(
        W["range"] * (tmax - tmin)
        + W["dev"] * sum(devs)
        + W["ez"] * ez_dev
        + W["base"] * total_base
        + W["sh_range"] * (shmax - shmin)
        + W["sh_dev"] * sum(sh_devs)
        + W["ez_sh"] * ez_sh_dev
        + W["comb_range"] * (cmax - cmin)
        + W["comb_dev"] * sum(comb_devs)
        + W["ez_days"] * sum(x["EZ", i] for i in range(N))
        + W["early"] * sum(early)
        + W["fri_arrive"] * sum(fri_arr)
        + int(W["trans"] * V["w_trans"] / 2) * n_trans2
        + W["churn"] * sum(churn_over)
        + int(W["long"] * V["w_long"]) * sum(long_pen)
        + int(W["short_home"] * V.get("w_short", 0)) * sum(short_home)
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    solver.parameters.log_search_progress = log
    st = solver.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    sched = {p: [int(solver.Value(x[p, i])) for i in range(N)] for p in P}
    return {
        "variant": variant,
        "status": solver.StatusName(st),
        "objective": solver.ObjectiveValue(),
        "bound": solver.BestObjectiveBound(),
        "days": [d.isoformat() for d in DAYS],
        "need": [need(i) for i in range(N)],
        "roster": [roster(i) for i in range(N)],
        "schedule": sched,
        "total": {p: int(solver.Value(total[p])) for p in P},
        "shabbat": {p: int(solver.Value(sh[p])) for p in P},
        "names": {p: PEOPLE[p]["name"] for p in P},
        "hist": {p: PEOPLE[p]["hist"] for p in P},
        "hist_sh": {p: PEOPLE[p]["hist_sh"] for p in P},
        "on_base_now": {p: PEOPLE[p]["now"] for p in P},
        "planned_exit": {p: (PEOPLE[p]["exit"].isoformat() if PEOPLE[p]["exit"] else None) for p in P},
        "ez_exit": ez_exit.isoformat(),
        "params": V,
        "weights": W,
        "ilan_counts": ilan_counts,
        "metrics": {
            "range": int(solver.Value(tmax) - solver.Value(tmin)),
            "comb_range": (max(solver.Value(total[p]) + solver.Value(sh[p]) for p in NOT_EZ)
                           - min(solver.Value(total[p]) + solver.Value(sh[p]) for p in NOT_EZ)),
            "excess": int(solver.Value(excess_expr)),
            "ez_days": int(sum(solver.Value(x["EZ", i]) for i in range(N))),
            "total_base": int(solver.Value(total_base)),
            "sh_range": int(solver.Value(shmax) - solver.Value(shmin)),
            "trips": int(solver.Value(trips_main)),
            "ilan_switches": int(solver.Value(trips_ilan)),
            "early_days": int(sum(solver.Value(e) for e in early)) if early else 0,
            "fri_arrivals": int(sum(solver.Value(f) for f in fri_arr)) if fri_arr else 0,
            "short_home_blocks": int(sum(solver.Value(b) for b in short_home)) if short_home else None,
        },
    }


# ----------------------------------------------------------------------------
# Reporting helpers
# ----------------------------------------------------------------------------
def stints(seq):
    res = []
    cur, start = seq[0], 0
    for i in range(1, len(seq)):
        if seq[i] != cur:
            res.append((cur, start, i - 1))
            cur, start = seq[i], i
    res.append((cur, start, len(seq) - 1))
    return res


def fmt(d):
    return f"{d.day}.{d.month}"


def print_report(out):
    S = out["schedule"]
    P = list(PEOPLE)
    print(f"variant={out['variant']} status={out['status']} obj={out['objective']:.0f} "
          f"bound={out['bound']:.0f} metrics={out['metrics']}")
    print()
    print("day      need pres cmd  " + " ".join(f"{p:>2}" for p in P))
    for i, d in enumerate(DAYS):
        pres = 1 + sum(S[p][i] for p in P)
        cmd = 1 + sum(S[c][i] for c in COMMANDERS)
        row = " ".join(" █" if S[p][i] else " ." for p in P)
        print(f"{fmt(d):>5} {HEB_DOW[d.weekday()]:>2}  {out['need'][i]:>3} {pres:>4} {cmd:>3}  {row}")
    print()
    print("person  hist +fut = total   home  shab   stints (5.11-25.11)")
    for p in P:
        fut = sum(S[p])
        tot = out["total"][p]
        st = stints(S[p])
        desc = ", ".join(
            f"{'מוצב' if s else 'בית'} {fmt(DAYS[a])}-{fmt(DAYS[b])} ({b - a + 1})" for s, a, b in st
        )
        days_total = TOTAL_DAYS if p != "EZ" else (dt.date.fromisoformat(out["ez_exit"]) - START).days
        print(f"{p:>3} {out['names'][p]:<22} {out['hist'][p]:>2} +{fut:>2} = {tot:>2}/{days_total}  "
              f"{days_total - tot:>3}   {out['shabbat'][p]}/5   {desc}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="A_balanced")
    ap.add_argument("--json", default=None)
    ap.add_argument("--time", type=float, default=120)
    ap.add_argument("--need14", type=int, default=None, help="daily presence need while the roster is 14 (default ceil(0.65*14)=10)")
    ap.add_argument("--need13", type=int, default=None, help="daily presence need after Eran is released (default ceil(0.65*13)=9)")
    ap.add_argument("--no-ilan-count", action="store_true", help="Ilan does not count toward the 65%")
    ap.add_argument("--eran-exit", default=None, help="Eran's exit day, e.g. 12.11")
    ap.add_argument("--log", action="store_true")
    ap.add_argument("-w", "--weight", action="append", default=[], metavar="KEY=VALUE",
                    help="override an objective weight, e.g. -w early=5000 (see WEIGHTS)")
    ap.add_argument("--ez-home", default="", help="dates Eran must be home, e.g. 5.11,6.11,7.11")
    ap.add_argument("--ez-base", default="", help="dates Eran must be at the outpost, e.g. 8.11,9.11,10.11,11.11")
    ap.add_argument("--hard", action="append", default=[], metavar="KEY=VALUE",
                    help="hard cap, e.g. --hard range=1 --hard sh_range=1 --hard comb_range=0 --hard excess=1")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    ez_exit = EZ_EXIT_DEFAULT
    if args.eran_exit:
        dd, mm = args.eran_exit.split(".")
        ez_exit = dt.date(2026, int(mm), int(dd))
    weights = {}
    for kv in args.weight:
        k, v = kv.split("=")
        weights[k] = int(v)
    def dates(txt):
        res = []
        for t in filter(None, txt.split(",")):
            d, mth = t.split(".")
            res.append(dt.date(2026, int(mth), int(d)))
        return res
    hard = {k: int(v) for k, v in (h.split("=") for h in args.hard)}
    if args.ez_home:
        hard["ez_home"] = dates(args.ez_home)
    if args.ez_base:
        hard["ez_base"] = dates(args.ez_base)
    out = build_and_solve(args.variant, args.time, args.need14, args.need13,
                          not args.no_ilan_count, ez_exit, args.log, weights, hard or None,
                          workers=args.workers)
    if out is None:
        print("INFEASIBLE")
        sys.exit(1)
    print_report(out)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
