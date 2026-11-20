"""exp18_summary.py -- descriptive only: the figures the exp18 write-up quotes, computed from exp18_out.txt.
Run:  python -I exp18_summary.py > exp18_summary_out.txt      (standard library only)"""
import re
from statistics import mean

ROW = re.compile(r"^(control|threshold)\s+seed (\d+): (PASS|fail) claim=\[([^\]]*)\] per-group=\[([^\]]*)\] ratio=([\d.]+)"
                 r".*?spk=\[([^\]]*)\] sel ([\d.]+)->([\d.]+) perm95 ([\d.]+) \| b ([\d.]+) n_g ([\d.]+) s ([\d.]+) "
                 r"n ([\d.]+) o ([\d.]+)")
CNT = re.compile(r"LTP let through / blocked at post spikes: burst_own_group (\d+)/(\d+); burst_other_groups (\d+)/(\d+); "
                 r"burst_60_99 (\d+)/(\d+); noise (\d+)/(\d+)")


def main():
    rows, counts, last = {"control": {}, "threshold": {}}, {}, None
    for line in open("exp18_out.txt", encoding="utf-8"):
        m = ROW.match(line.strip())
        if m:
            arm, s = m.group(1), int(m.group(2))
            claim = [int(x) for x in m.group(4).split(",")]
            per = [float(x) for x in m.group(5).split(",")]
            vals = [float(m.group(i)) for i in range(6, 7)] + [float(m.group(i)) for i in range(8, 16)]
            spk = [int(x) for x in m.group(7).split(",")]
            rows[arm][s] = dict(ok=m.group(3) == "PASS", distinct=len(set(claim)) == 3, per=per, ratio=vals[0],
                                spk=spk, sel0=vals[1], sel=vals[2], p95=vals[3], b=vals[4], ng=vals[5], s=vals[6],
                                n=vals[7], o=vals[8])
            last = (arm, s)
            continue
        c = CNT.search(line)
        if c and last:
            counts[last[1]] = [int(x) for x in c.groups()]
    for arm in ("control", "threshold"):
        r = rows[arm].values()
        print(f"{arm}: ratio mean {mean(x['ratio'] for x in r):.3f}; selectivity mean {mean(x['sel'] for x in r):.3f}; "
              f"distinct claims {sum(x['distinct'] for x in r)}/8; per-group ratios above 2.0 "
              f"{sum(p > 2.0 for x in r for p in x['per'])}/24; spikes {min(min(x['spk']) for x in r)}-"
              f"{max(max(x['spk']) for x in r)}")
        print(f"   split means: b {mean(x['b'] for x in r):.3f}  n_g {mean(x['ng'] for x in r):.3f}  "
              f"s {mean(x['s'] for x in r):.3f}  n {mean(x['n'] for x in r):.3f}  o {mean(x['o'] for x in r):.3f}  "
              f"b/o {mean(x['b'] / x['o'] for x in r):.2f}")
    c, t = rows["control"], rows["threshold"]
    for k, label in (("b", "claimed burst b"), ("o", "other-group burst o"), ("s", "silent burst s"),
                     ("ng", "claimed inputs' noise n_g"), ("n", "noise on 60-99 n")):
        cm, tm = mean(x[k] for x in c.values()), mean(x[k] for x in t.values())
        print(f"threshold / control, {label}: {tm / cm:.3f} ({(tm / cm - 1) * 100:+.1f}%)")
    print(f"selectivity lower under the threshold on {sum(t[s]['sel'] < c[s]['sel'] for s in c)}/8 seeds; "
          f"ratio higher on {sum(t[s]['ratio'] > c[s]['ratio'] for s in c)}/8, lower on "
          f"{sum(t[s]['ratio'] < c[s]['ratio'] for s in c)}/8, equal on {sum(t[s]['ratio'] == c[s]['ratio'] for s in c)}/8")
    tot = [sum(v[i] for v in counts.values()) for i in range(8)]
    for name, (lt, bl) in (("burst, own group", tot[0:2]), ("burst, other groups", tot[2:4]),
                           ("burst, inputs 60-99", tot[4:6]), ("noise", tot[6:8])):
        share = lt / (lt + bl) if lt + bl else float("nan")
        print(f"gate, all 8 seeds, {name}: let through {lt}, blocked {bl}, share let through {share:.3f}")
    noise_share = [counts[s][6] / (counts[s][6] + counts[s][7]) for s in sorted(counts)]
    print(f"noise share let through per seed: {min(noise_share):.3f}-{max(noise_share):.3f}")


if __name__ == "__main__":
    main()
