#!/usr/bin/env python3
"""
Second-engine cross-check: the same hard rules written as a MILP for SCIP
(OR-Tools linear solver), used as a feasibility oracle with caps on
(combined range, days range, Shabbat range, excess).  A different solver
technology than CP-SAT confirming INFEASIBLE for a tighter cap is an
independent proof that the chosen schedule cannot be made more equal.

    python3 milp_check.py --comb 0 --days 1 --shab 1 --excess 1
"""
import argparse

from ortools.linear_solver import pywraplp

import rules as R

P = R.PEOPLE
NON_EZ = [p for p in P if p != "EZ"]
N = 21
PARAMS = dict(min_base=3, min_home=4, max_base=8)


def build(caps, time_limit=120):
    s = pywraplp.Solver.CreateSolver("SCIP")
    s.SetTimeLimit(int(time_limit * 1000))
    x = {(p, i): s.BoolVar(f"x_{p}_{i}") for p in P for i in range(N)}
    H = {p: (R.EZ_CUT - 1 if p == "EZ" else N - 1) for p in P}
    for i in range(R.EZ_CUT, N):
        s.Add(x["EZ", i] == 0)
    for i in range(N):
        s.Add(sum(x[p, i] for p in P) + 1 >= R.NEED[i])
        s.Add(sum(x[c, i] for c in R.COMMANDERS) >= 1)
    for p, idxs in R.FIXED_HOME.items():
        for i in idxs:
            s.Add(x[p, i] == 0)
    for p, idxs in R.FIXED_BASE.items():
        for i in idxs:
            s.Add(x[p, i] == 1)
    for a, b in R.PAIRS:
        for i in range(N):
            s.Add(x[a, i] == x[b, i])
    for p in P:
        if p == "IS":
            continue
        for sat in R.SAT:
            s.Add(x[p, sat] == x[p, sat - 1])
    # transitions
    arr, dep = {}, {}
    for p in P:
        now = 1 if p in R.ON_BASE_NOW else 0
        if p == "IS":
            now = 1
        for i in range(H[p] + 1):
            a = s.BoolVar(f"a_{p}_{i}"); d = s.BoolVar(f"d_{p}_{i}")
            arr[p, i], dep[p, i] = a, d
            prev = now if i == 0 else x[p, i - 1]
            s.Add(a >= x[p, i] - prev)
            s.Add(a <= x[p, i])
            s.Add(a <= 1 - prev)
            s.Add(d >= prev - x[p, i])
            s.Add(d <= prev)
            s.Add(d <= 1 - x[p, i])
    # stint minima (Ilan exempt), maxima
    for p in P:
        mb = 2 if p == "IS" else PARAMS["min_base"]
        mh = 1 if p == "IS" else PARAMS["min_home"]
        MB = R.ILAN_MAX if p == "IS" else PARAMS["max_base"]
        for i in range(H[p] + 1):
            if i + mb - 1 > H[p]:
                s.Add(arr[p, i] == 0)
            else:
                for k in range(mb):
                    s.Add(x[p, i + k] >= arr[p, i])
            for k in range(mh):
                if i + k <= H[p]:
                    s.Add(x[p, i + k] <= 1 - dep[p, i])
        pre = R.ON_BASE_NOW.get(p, 0)
        for end in range(N):
            start = end - MB
            terms = [x[p, j] for j in range(max(0, start), end + 1)]
            const = max(0, min(pre, -start)) if start < 0 else 0
            s.Add(sum(terms) + const <= MB)
    # totals and caps
    tot = {p: R.HIST[p] + sum(x[p, i] for i in range(N)) for p in P}
    sh = {p: R.HIST_SH[p] + sum(x[p, i] for i in R.SAT) for p in P}
    for p, q in [(p, q) for p in NON_EZ for q in NON_EZ if p != q]:
        if "days" in caps:
            s.Add(tot[p] - tot[q] <= caps["days"])
        if "shab" in caps:
            s.Add(sh[p] - sh[q] <= caps["shab"])
        if "comb" in caps:
            s.Add(tot[p] + sh[p] - tot[q] - sh[q] <= caps["comb"])
    if "excess" in caps:
        s.Add(sum(x[p, i] for p in P for i in range(N)) + N - sum(R.NEED) <= caps["excess"])
    s.Minimize(sum(x[p, i] for p in P for i in range(N)))
    st = s.Solve()
    name = {pywraplp.Solver.OPTIMAL: "FEASIBLE(optimal)", pywraplp.Solver.FEASIBLE: "FEASIBLE",
            pywraplp.Solver.INFEASIBLE: "INFEASIBLE", pywraplp.Solver.NOT_SOLVED: "UNKNOWN(time)",
            pywraplp.Solver.ABNORMAL: "ABNORMAL"}.get(st, str(st))
    sched = None
    if st in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        sched = {p: [int(round(x[p, i].solution_value())) for i in range(N)] for p in P}
    return name, sched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comb", type=int, default=None)
    ap.add_argument("--days", type=int, default=None)
    ap.add_argument("--shab", type=int, default=None)
    ap.add_argument("--excess", type=int, default=None)
    ap.add_argument("--time", type=float, default=120)
    a = ap.parse_args()
    caps = {k: v for k, v in dict(comb=a.comb, days=a.days, shab=a.shab, excess=a.excess).items() if v is not None}
    name, sched = build(caps, a.time)
    print(f"SCIP with caps {caps}: {name}")
    if sched:
        v = R.violations(sched, PARAMS)
        m = R.metrics(sched)
        print("  witness legal by rules.py:", "yes" if not v else v[:3])
        print(f"  witness metrics: comb {m['comb_range']}, days {m['range']}, shab {m['sh_range']}, excess {m['excess']}")


if __name__ == "__main__":
    main()
