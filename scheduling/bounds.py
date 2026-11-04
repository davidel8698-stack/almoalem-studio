#!/usr/bin/env python3
"""
Counting-argument bounds on how equal the rotation can possibly be.
Independent of the solver: pure arithmetic on the confirmed rules and history.

    python3 bounds.py
"""
import math

DAYS_LEFT = 21                 # 5.11 .. 25.11
NEED_SCHEDULED = [8] * 7 + [7] * 14      # 9 incl. David until 11.11, then 8
TOTAL_DAYS = 35                # 22.10 .. 25.11
HIST = {"IM": 6, "AH": 6, "MA": 6, "SA": 6, "RH": 6, "EY": 5, "AC": 6, "IK": 7, "LE": 8, "KA": 9, "SG": 9, "IS": 6}
HIST_SH = {"IM": 1, "AH": 1, "MA": 1, "SA": 1, "RH": 1, "EY": 0, "AC": 0, "IK": 1, "LE": 1, "KA": 2, "SG": 2, "IS": 0}
EZ_HIST, EZ_HIST_SH, EZ_DAYS_LEFT = 8, 1, 7          # Eran: 5.11..11.11
SAT_NEED_SCHEDULED = {"7.11": 8, "14.11": 7, "21.11": 7}


def main():
    n = len(HIST)
    min_pool = sum(NEED_SCHEDULED)                    # 154 scheduled person-days at the daily minimum
    print(f"scheduled base person-days required 5.11-25.11 (at the daily minimum): {min_pool}")
    print(f"history of the 12 (through 4.11): {sum(HIST.values())} base days; Eran {EZ_HIST}")
    print()
    print("Final base-day totals of the 12 (sum = history + pool - Eran's plan days + excess):")
    for ez in range(0, EZ_DAYS_LEFT + 1):
        for excess in range(0, 7):
            total = sum(HIST.values()) + min_pool - ez + excess
            avg = total / n
            lo, hi = math.floor(avg), math.ceil(avg)
            how = "all equal" if lo == hi else f"{n*hi - total} at {lo}, {total - n*lo} at {hi}"
            if excess in (0, 2, 4, 6):
                print(f"  Eran {ez} plan days, excess {excess}: sum {total}, avg {avg:.2f} -> best split {how}")
        print()
    print("Shabbat slots on 7.11/14.11/21.11 at the daily minimum:", sum(SAT_NEED_SCHEDULED.values()),
          "(one of them may be Eran on 7.11)")
    base_sh = sum(HIST_SH.values())
    for ez_sat in (0, 1):
        for extra in (0, 2, 4):
            slots = sum(SAT_NEED_SCHEDULED.values()) - ez_sat + extra
            total = base_sh + slots
            avg = total / n
            lo, hi = math.floor(avg), math.ceil(avg)
            how = "all equal" if lo == hi else f"{n*hi - total} at {lo}, {total - n*lo} at {hi}"
            print(f"  Eran on 7.11={ez_sat}, extra closers {extra}: Shabbat sum {total}, avg {avg:.2f} -> best split {how}")
    print()
    print("Each extra Shabbat closer costs 2 excess base person-days (Friday + Saturday, no Saturday moves).")
    print("Every day at exactly the minimum => zero slack; 22.11-style excess days are the only reserve.")
    print()
    print("Combined burden (base days + Shabbatot): with sums S_days and S_sh the average is (S_days+S_sh)/12;")
    for ez in (4, 6):
        for extra in (0, 2):
            excess = extra
            s_days = sum(HIST.values()) + min_pool - ez + excess
            s_sh = base_sh + sum(SAT_NEED_SCHEDULED.values()) - 1 + extra
            tot = s_days + s_sh
            print(f"  Eran {ez} days (closing 7.11), extra closers {extra}: combined sum {tot}, avg {tot/n:.2f} -> "
                  f"{'all equal' if tot % n == 0 else f'{n - tot % n} at {tot//n}, {tot % n} at {tot//n + 1}'}")


if __name__ == "__main__":
    main()
