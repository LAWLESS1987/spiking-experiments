"""exp19_posthoc.py -- POST HOC, descriptive only: three checks asked for by an outside read of exp19 (Gemini, 2026-11-20).

1. The response window. Amendment 2 anchors it at the volley's onset, its earliest input spike. A tighter volley's
   first spike sits closer to its centre (about 0.9 ms before it, against about 3.7 ms), so the window ends later
   relative to the centre. Here the claimers' response shares are recounted with windows anchored at the volley's
   scheduled centre, the same in both arms.
2. Events per answered volley. The pre-registered counters are per own-group volley, answered or not. Here they are
   divided by the number of own-group volleys answered within 20 ms of the onset, as registered.
3. The per-seed change in the published ratio, recomputed from the saved end weights with exp11's scoring lines.
Run:  .venv\\Scripts\\python.exe exp19_posthoc.py > exp19_posthoc_out.txt      In: exp19_weights.npz (numpy only)
"""
import numpy as np

GROUPS = [list(range(0, 20)), list(range(20, 40)), list(range(40, 60))]
SEEDS = list(range(1, 9))
ARMS = ("control", "treatment")
WINDOWS = (("as registered: onset to onset + 20 ms", "onset", 0.0, 0.020),
           ("centre - 4 ms to centre + 16 ms", "centre", -0.004, 0.016),
           ("centre - 1 ms to centre + 19 ms", "centre", -0.001, 0.019),
           ("centre to centre + 20 ms", "centre", 0.0, 0.020))


def claims_and_ratio(n1, b1):
    """exp11's scoring lines (exp16_rescore.score / exp18's pass_ab): claimer = argmax of the group means of n1 + b1."""
    W = n1 + b1
    mean_on = np.array([[W[k, g].mean() for g in GROUPS] for k in range(3)])
    noise_w = W[:, 60:].mean(1)
    c = mean_on.argmax(0)
    return c, float(np.mean([mean_on[c[g], g] / max(noise_w[c[g]], 1e-9) for g in range(3)]))


def hits(z, arm, s, c, anchor, lo, hi):
    oi, ot = z[f"{arm}_s{s}_out_i"], z[f"{arm}_s{s}_out_t"]
    onset, group = z[f"{arm}_s{s}_onset"], z[f"{arm}_s{s}_group"]
    centre = np.arange(0.05, 120.0, 0.25)[:len(onset)]
    ts = [np.sort(ot[oi == k]) for k in range(3)]
    own = own_n = oth = oth_n = 0
    for v in range(len(onset)):
        a0 = (onset[v] if anchor == "onset" else centre[v]) + lo
        a1 = (onset[v] if anchor == "onset" else centre[v]) + hi
        for k in sorted(set(c.tolist())):
            x = int(np.searchsorted(ts[k], a0, side="left"))
            fired = x < len(ts[k]) and ts[k][x] <= a1
            if c[group[v]] == k:
                own_n += 1; own += int(fired)
            else:
                oth_n += 1; oth += int(fired)
    return own, own_n, oth, oth_n


def main():
    z = np.load("exp19_weights.npz")
    cl = {(a, s): claims_and_ratio(z[f"{a}_s{s}_n1"], z[f"{a}_s{s}_b1"]) for a in ARMS for s in SEEDS}
    print("1. claimers' response shares, pooled over the eight seeds, by window")
    for label, anchor, lo, hi in WINDOWS:
        sh = {}
        for a in ARMS:
            t = np.array([hits(z, a, s, cl[(a, s)][0], anchor, lo, hi) for s in SEEDS]).sum(0)
            sh[a] = (t[0] / t[1], t[2] / t[3] if t[3] else float("nan"))
        print(f"   {label:38s} own: control {sh['control'][0]:.3f}, treatment {sh['treatment'][0]:.3f}, ratio "
              f"{sh['treatment'][0] / sh['control'][0]:.3f} | other: control {sh['control'][1]:.3f}, treatment "
              f"{sh['treatment'][1]:.3f}")
    print("\n2. events per answered own-group volley (answered = registered window), pooled over the eight seeds")
    # The saved counters are per burst synapse in Brian2's all-to-all order, input-major: index = i * 3 + j.
    # Checked below against the per-volley figures exp19_volley_jitter.py printed into exp19_out.txt.
    pre, post = np.repeat(np.arange(100), 3), np.tile(np.arange(3), 100)
    logged = [tuple(float(x) for x in (l.split("dep10 ")[1].split()[0], l.split("pot10 ")[1].split()[0]))
              for l in open("exp19_out.txt", encoding="utf-8") if "per own-group burst:" in l]
    mine, per = [], {}
    for name in ("n_pot10", "n_dep10"):
        per[name] = {}
        for a in ARMS:
            ev = ans = 0.0
            for s in SEEDS:
                c = cl[(a, s)][0]
                cnt = z[f"{a}_s{s}_{name}"]
                tot = sum(float(cnt[np.isin(pre, GROUPS[g]) & (post == c[g])].sum()) for g in range(3))
                if name == "n_dep10":
                    mine.append((a, s, tot / len(z[f"{a}_s{s}_onset"])))
                ev += tot
                ans += hits(z, a, s, c, "onset", 0.0, 0.020)[0]
            per[name][a] = ev / ans
        print(f"   {name}: control {per[name]['control']:.3f}, treatment {per[name]['treatment']:.3f} "
              f"({(per[name]['treatment'] / per[name]['control'] - 1) * 100:+.1f}%)")
    same = sum(round(m[2], 3) == lg[0] for m, lg in zip(mine, logged))
    print(f"   check: dep10 per own-group volley recomputed here matches exp19_out.txt on {same}/{len(logged)} rows")
    print("\n3. the published ratio per seed (end weights, unrounded)")
    d = []
    for s in SEEDS:
        rc, rt = cl[("control", s)][1], cl[("treatment", s)][1]
        d.append(rt - rc)
        print(f"   seed {s}: control {rc:.3f}, treatment {rt:.3f}, change {rt - rc:+.3f}")
    print(f"   change: min {min(d):+.3f}, max {max(d):+.3f}, mean {np.mean(d):+.3f}; higher on {sum(x > 0 for x in d)}/8")


if __name__ == "__main__":
    main()
