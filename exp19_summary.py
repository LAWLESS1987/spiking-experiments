"""exp19_summary.py -- descriptive only: the figures the exp19 write-up quotes, computed from exp19_out.txt.
Written while the run was in progress, before its output was read. No bar and no reading: those are printed by
exp19_volley_jitter.py itself, as pre-registered.
Run:  python -I exp19_summary.py > exp19_summary_out.txt      (standard library only)"""
import re
from statistics import mean

ROW = re.compile(r"^(control|treatment)\s+seed (\d+): (PASS|fail) claim=\[([^\]]*)\] per-group=\[([^\]]*)\] "
                 r"ratio=([\d.]+).*?spk=\[([^\]]*)\] sel ([\d.]+)->([\d.]+) \| b ([\d.]+) n_g ([\d.]+) s ([\d.]+) "
                 r"n ([\d.]+) o ([\d.]+)")
CNT = re.compile(r"per own-group burst: dep10 ([\d.]+) dep100 ([\d.]+) pot10 ([\d.]+) pot100 ([\d.]+) \| nominal "
                 r"pot10 ([+-][\d.]+) dep10 ([+-][\d.]+) net ([+-][\d.]+)")
RSP = re.compile(r"responses within 20 ms: own (\d+)/(\d+) \([^)]*\), other (\d+)/(\d+) \([^)]*\); latency from onset "
                 r"mean (-?[\d.]+|n/a)(?: ms)? median (-?[\d.]+|n/a)(?: ms)?; from centre mean (-?[\d.]+|n/a)(?: ms)? \| "
                 r"claimed burst synapses >= 1.8: (\d+)/(\d+)")


def num(x):
    return None if x == "n/a" else float(x)


def main():
    rows, last = {"control": {}, "treatment": {}}, None
    for line in open("exp19_out.txt", encoding="utf-8"):
        m = ROW.match(line.strip())
        if m:
            arm, s = m.group(1), int(m.group(2))
            claim = [int(x) for x in m.group(4).split(",")]
            rows[arm][s] = dict(ok=m.group(3) == "PASS", distinct=len(set(claim)) == 3,
                                per=[float(x) for x in m.group(5).split(",")], ratio=float(m.group(6)),
                                spk=[int(x) for x in m.group(7).split(",")], sel0=float(m.group(8)),
                                sel=float(m.group(9)), b=float(m.group(10)), ng=float(m.group(11)),
                                s=float(m.group(12)), n=float(m.group(13)), o=float(m.group(14)))
            last = (arm, s)
            continue
        c = CNT.search(line)
        if c and last:
            rows[last[0]][last[1]].update(zip(("dep10", "dep100", "pot10", "pot100", "dw_pot", "dw_dep", "dw_net"),
                                              (float(x) for x in c.groups())))
            continue
        r = RSP.search(line)
        if r and last:
            g = r.groups()
            rows[last[0]][last[1]].update(own_hit=int(g[0]), own_n=int(g[1]), oth_hit=int(g[2]), oth_n=int(g[3]),
                                          lat_on=num(g[4]), lat_on_med=num(g[5]), lat_ce=num(g[6]), sat=int(g[7]),
                                          sat_n=int(g[8]))
    for arm in ("control", "treatment"):
        r = list(rows[arm].values())
        print(f"{arm}: PASS {sum(x['ok'] for x in r)}/8; ratio mean {mean(x['ratio'] for x in r):.3f}; selectivity "
              f"mean {mean(x['sel'] for x in r):.3f}; distinct claims {sum(x['distinct'] for x in r)}/8; per-group "
              f"ratios above 2.0 {sum(p > 2.0 for x in r for p in x['per'])}/24; spikes "
              f"{min(min(x['spk']) for x in r)}-{max(max(x['spk']) for x in r)}")
        print(f"   split means: b {mean(x['b'] for x in r):.3f}  n_g {mean(x['ng'] for x in r):.3f}  "
              f"s {mean(x['s'] for x in r):.3f}  n {mean(x['n'] for x in r):.3f}  o {mean(x['o'] for x in r):.3f}  "
              f"b/o {mean(x['b'] / x['o'] for x in r):.2f}  b/((s+n)/2) {mean(x['b'] / ((x['s'] + x['n']) / 2) for x in r):.2f}")
        print(f"   per own-group burst, means: dep10 {mean(x['dep10'] for x in r):.3f}  dep100 "
              f"{mean(x['dep100'] for x in r):.3f}  pot10 {mean(x['pot10'] for x in r):.3f}  pot100 "
              f"{mean(x['pot100'] for x in r):.3f}  nominal net {mean(x['dw_net'] for x in r):+.5f}")
        oh, on = sum(x["own_hit"] for x in r), sum(x["own_n"] for x in r)
        th, tn = sum(x["oth_hit"] for x in r), sum(x["oth_n"] for x in r)
        lo = [x["lat_on"] for x in r if x["lat_on"] is not None]
        lc = [x["lat_ce"] for x in r if x["lat_ce"] is not None]
        print(f"   responses pooled: own {oh}/{on} ({oh / on:.3f}), other {th}/{tn} "
              f"({(th / tn) if tn else float('nan'):.3f}); latency mean of seed means: from onset "
              f"{mean(lo) if lo else float('nan'):.2f} ms, from centre {mean(lc) if lc else float('nan'):.2f} ms; "
              f"saturation pooled {sum(x['sat'] for x in r)}/{sum(x['sat_n'] for x in r)}")
    c, t = rows["control"], rows["treatment"]
    for k, label in (("b", "claimed burst b"), ("o", "other-group burst o"), ("s", "silent burst s"),
                     ("ng", "claimed inputs' noise n_g"), ("n", "noise on 60-99 n"), ("dep10", "dep10 per burst"),
                     ("pot10", "pot10 per burst")):
        cm, tm = mean(x[k] for x in c.values()), mean(x[k] for x in t.values())
        print(f"treatment / control, {label}: {tm / cm:.3f} ({(tm / cm - 1) * 100:+.1f}%)")
    for k, label in (("sel", "selectivity"), ("ratio", "ratio"), ("dep10", "dep10 per burst"),
                     ("pot10", "pot10 per burst")):
        print(f"{label}: treatment higher on {sum(t[s][k] > c[s][k] for s in c)}/8, lower on "
              f"{sum(t[s][k] < c[s][k] for s in c)}/8, equal on {sum(t[s][k] == c[s][k] for s in c)}/8")


if __name__ == "__main__":
    main()
