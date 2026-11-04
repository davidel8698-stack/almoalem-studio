#!/usr/bin/env python3
"""
Feasibility frontier: for every combination of caps on
  (range of final base-day totals, range of final Shabbat totals, range of combined score)
ask CP-SAT whether ANY schedule obeying all hard rules exists.  Nothing is
optimised here, so an INFEASIBLE answer is a proof that no schedule can be
that equal; FEASIBLE comes with a witness.

    python3 frontier.py --variant I_fair [--time 60] [--ez-max 3] [--ez-home-from 9.11] [--json out.json]
"""
import argparse
import datetime as dt
import itertools
import json

import solver


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="I_fair")
    ap.add_argument("--time", type=float, default=60)
    ap.add_argument("--ez-max", type=int, default=None, help="cap on Eran's plan base days")
    ap.add_argument("--ez-home-from", default=None, help="Eran home for good from this date, e.g. 9.11")
    ap.add_argument("--excess-max", type=int, default=None, help="cap on base person-days above the daily minimum")
    ap.add_argument("--json", default=None)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--ez-home", default="", help="dates Eran must be home, e.g. 5.11,6.11,7.11")
    ap.add_argument("--ez-base", default="", help="dates Eran must be at the outpost, e.g. 8.11,9.11,10.11,11.11")
    ap.add_argument("--comb", action="store_true", help="also sweep caps on the combined score range")
    a = ap.parse_args()

    def dates(txt):
        res = []
        for t in filter(None, txt.split(",")):
            d, mth = t.split(".")
            res.append(dt.date(2026, int(mth), int(d)))
        return res
    ez_from = None
    if a.ez_home_from:
        d, mth = a.ez_home_from.split(".")
        ez_from = dt.date(2026, int(mth), int(d))

    results = []
    # Cheap objective so the solver just looks for feasibility
    quiet = dict(range=0, dev=0, ez=0, base=1, sh_range=0, sh_dev=0, ez_sh=0, early=0,
                 fri_arrive=0, trans=0, churn=0, long=0, short_home=0, comb_range=0, comb_dev=0, ez_days=0)
    combos = [(dr, sr, None) for dr, sr in itertools.product(range(0, 4), range(0, 3))]
    if a.comb:
        combos = [(dr, sr, cr) for dr in (0, 1, 2) for sr in (1, 2) for cr in (0, 1, 2)]
    for dr, sr, cr in combos:
        hard = {"range": dr, "sh_range": sr}
        if cr is not None:
            hard["comb_range"] = cr
        if a.ez_home:
            hard["ez_home"] = dates(a.ez_home)
        if a.ez_base:
            hard["ez_base"] = dates(a.ez_base)
        if a.ez_max is not None:
            hard["ez_max_days"] = a.ez_max
        if a.excess_max is not None:
            hard["excess"] = a.excess_max
        out = solver.build_and_solve(a.variant, a.time, weights=quiet, hard=hard,
                                     ez_home_from=ez_from, workers=a.workers)
        if out is None:
            status = "INFEASIBLE"
            info = ""
        else:
            status = out["status"]
            mt = out["metrics"]
            info = (f"witness: days {mt['range']}, shab {mt['sh_range']}, comb {mt['comb_range']}, "
                    f"excess {mt['excess']}, Eran {mt['ez_days']}")
        print(f"days range <= {dr}, Shabbat range <= {sr}, combined range <= {cr}: {status}  {info}", flush=True)
        results.append({"days_range": dr, "sh_range": sr, "comb_range": cr, "status": status, "info": info})
    if a.json:
        json.dump(results, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
