#!/usr/bin/env python3
"""
Local-search improver / optimality sanity check, independent of CP-SAT.

Starting from a schedule, tries every legal one-step change (flip one person's
day, move a block boundary by one day, swap a day between two people, swap a
whole day-column between two people) and reports whether any of them improves
fairness lexicographically: (combined range, days range, Shabbat range, excess).
If the solver's answer is optimal, nothing should improve.

    python3 improve.py janet.json [--rounds 3]
"""
import argparse
import copy
import json
import random

import rules


def score(S):
    m = rules.metrics(S)
    return (m["comb_range"], m["range"], m["sh_range"], m["excess"])


def neighbours(S):
    P = rules.PEOPLE
    pairs = dict(rules.PAIRS)
    rev = {b: a for a, b in rules.PAIRS}

    def setday(T, p, i, v):
        T[p][i] = v
        if p in pairs:
            T[pairs[p]][i] = v
        if p in rev:
            T[rev[p]][i] = v

    for p in P:
        H = rules.EZ_CUT if p == "EZ" else 21
        for i in range(H):
            T = copy.deepcopy(S)
            setday(T, p, i, 1 - S[p][i])
            yield f"flip {p} {rules.DAYS[i]}", T
        # move a boundary by one day (shift a block edge)
        for i in range(1, H):
            if S[p][i] != S[p][i - 1]:
                T = copy.deepcopy(S)
                setday(T, p, i, S[p][i - 1])
                yield f"extend-left {p} {rules.DAYS[i]}", T
                T = copy.deepcopy(S)
                setday(T, p, i - 1, S[p][i])
                yield f"extend-right {p} {rules.DAYS[i-1]}", T
    for a in P:
        for b in P:
            if a >= b:
                continue
            for i in range(21):
                if S[a][i] != S[b][i]:
                    T = copy.deepcopy(S)
                    setday(T, a, i, S[b][i]); setday(T, b, i, S[a][i])
                    yield f"swap {a}<->{b} {rules.DAYS[i]}", T
            # swap whole tails from day i on
            for i in range(1, 21):
                T = copy.deepcopy(S)
                for j in range(i, 21):
                    va, vb = S[a][j], S[b][j]
                    setday(T, a, j, vb); setday(T, b, j, va)
                yield f"swap-tail {a}<->{b} from {rules.DAYS[i]}", T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--rounds", type=int, default=2, help="rounds of random two-step probes after the exhaustive one-step pass")
    a = ap.parse_args()
    out = json.load(open(a.src, encoding="utf-8"))
    S = {p: list(v) for p, v in out["schedule"].items()}
    params = out["params"]
    base_v = rules.violations(S, params)
    print("start:", "LEGAL" if not base_v else f"ILLEGAL {base_v[:3]}", "score", score(S))
    best = score(S)
    improved = []
    legal_neighbours = 0
    n = 0
    for name, T in neighbours(S):
        n += 1
        if rules.violations(T, params):
            continue
        legal_neighbours += 1
        sc = score(T)
        if sc < best:
            improved.append((name, sc))
    print(f"one-step moves tried: {n}, legal: {legal_neighbours}, improving: {len(improved)}")
    for name, sc in improved[:10]:
        print("  IMPROVES:", name, "->", sc)
    # random two-step probes: a random legal-or-not first step, then an exhaustive second step
    rnd = random.Random(7)
    two = 0
    for r in range(a.rounds):
        cands = list(neighbours(S))
        rnd.shuffle(cands)
        for name1, T1 in cands[:60]:
            for name2, T2 in neighbours(T1):
                if rules.violations(T2, params):
                    continue
                if score(T2) < best:
                    two += 1
                    if two <= 5:
                        print("  TWO-STEP IMPROVES:", name1, "+", name2, "->", score(T2))
    print(f"two-step improving sequences found: {two}")
    print("RESULT:", "no improving move found (local optimum)" if not improved and not two else "IMPROVEMENT EXISTS")


if __name__ == "__main__":
    main()
