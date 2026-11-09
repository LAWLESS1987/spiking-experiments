"""Experiment 17: burst-synapse selectivity on NEW seeds 9-16 (pre-registered: PREREG_exp17_selectivity_new_seeds.md,
bar as amended before any run in Amendment 1).

Runs exp16's `real` and `shuffled` code paths unchanged (imported from exp16_rescore.run_once) on seeds 9-16, which
have never been run for this network. Measure: exp16_posthoc_selectivity's sel(), at t = 0 and at the end, plus a
label-permutation null (1000 random partitions of inputs 0-59, same claimer rule, on each run's own end weights).
PASS needs all three on >= 7 of 8 seeds: real end selectivity >= 2.0; above its own t = 0 value; above its
permutation null's 95th percentile. Shuffled is reported beside it with no bar.
Run:  .venv\\Scripts\\python.exe exp17_selectivity_new_seeds.py > exp17_out.txt      Out: exp17_weights.npz
"""
import numpy as np

from exp16_rescore import run_once, score

SEEDS = list(range(9, 17))
K = 3
TRUE = [list(range(0, 20)), list(range(20, 40)), list(range(40, 60))]


def sel(B, groups):                                       # exp16_posthoc_selectivity.sel / exp16_posthoc2.sel
    mean_on = np.array([[B[k, g].mean() for g in groups] for k in range(K)])
    claimer = mean_on.argmax(0)
    r = []
    for g in range(K):
        k = claimer[g]
        r.append(mean_on[k, g] / max(np.mean([mean_on[k, h] for h in range(K) if h != g]), 1e-9))
    return float(np.mean(r))


def perm95(B, seed):
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(1000):
        p = rng.permutation(60)
        vals.append(sel(B, [list(p[0:20]), list(p[20:40]), list(p[40:60])]))
    return float(np.percentile(vals, 95)), float((np.array(vals) >= sel(B, TRUE)).mean())


def main():
    import os
    from multiprocessing import Pool
    tasks = [(s, c) for s in SEEDS for c in ("real", "shuffled")]
    nworkers = max(1, int(os.environ.get("EXP17_WORKERS", "4")))
    print("exp17: burst-synapse selectivity on NEW seeds %s (bar fixed in PREREG_exp17 + Amendment 1; %d workers)\n"
          % (SEEDS, nworkers))
    with Pool(nworkers) as pool:
        res = dict(zip(tasks, pool.starmap(run_once, tasks)))
    store, counts = {}, {"ge2": 0, "up": 0, "perm": 0}
    for c in ("real", "shuffled"):
        ends = []
        for s in SEEDS:
            n0, b0, n1, b1, spikes = res[(s, c)]
            st, en = sel(b0, TRUE), sel(b1, TRUE)
            p95, frac = perm95(b1, 50000 + s)
            et, ec = score(n1 + b1)
            ends.append(en)
            if c == "real":
                counts["ge2"] += en >= 2.0
                counts["up"] += en > st
                counts["perm"] += en > p95
            print(f"{c:8s} seed {s}: sel start {st:.2f} end {en:.2f}  perm95 {p95:.2f} (null >= true {frac:.3f})  "
                  f"end_total {et} claim {ec} spk {spikes}")
            for name, arr in (("n0", n0), ("b0", b0), ("n1", n1), ("b1", b1)):
                store[f"{c}_s{s}_{name}"] = arr
        print(f"{c:8s} MEAN end selectivity {np.mean(ends):.3f}\n")
    n = len(SEEDS)
    print(f"real: end >= 2.0 on {counts['ge2']}/{n}; above own start on {counts['up']}/{n}; "
          f"above permutation 95th on {counts['perm']}/{n}")
    ok = counts["ge2"] >= 7 and counts["up"] >= 7 and counts["perm"] >= 7
    print("READING (pre-registered):", "PASS" if ok else "FAIL -- reported as the numbers")
    np.savez_compressed("exp17_weights.npz", **store)
    print("saved exp17_weights.npz")


if __name__ == "__main__":
    main()
