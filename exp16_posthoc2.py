"""exp16 post-hoc 2 (NOT pre-registered; written after reviewers' round 5 on 2026-11-09). Reads exp16_weights.npz.

(a) ChatGPT: "essentially no learning" in the desync null rested on summary scores. Measure the weights directly:
    mean |w_end - w_start| per synapse, burst and noise synapses, per condition.
(b) Conscious Ledger: the selectivity measure picks its claimer from the same weights, so selection alone lifts it.
    Label-permutation null: in each run, score selectivity (exp16_posthoc_selectivity.sel, same claimer rule) on
    1000 random partitions of inputs 0-59 into three groups of 20, and report where the true grouping falls.
Run:  .venv\\Scripts\\python.exe exp16_posthoc2.py > exp16_posthoc2_out.txt
"""
import numpy as np

d = np.load("exp16_weights.npz")
K = 3
TRUE = [list(range(0, 20)), list(range(20, 40)), list(range(40, 60))]


def sel(B, groups):
    mean_on = np.array([[B[k, g].mean() for g in groups] for k in range(K)])
    claimer = mean_on.argmax(0)
    r = []
    for g in range(K):
        k = claimer[g]
        r.append(mean_on[k, g] / max(np.mean([mean_on[k, h] for h in range(K) if h != g]), 1e-9))
    return float(np.mean(r))


print("(a) mean |w_end - w_start| per synapse (weights live in [0, 2]; initialised uniform [0, 0.6])\n")
for c in ("real", "shuffled", "desync"):
    b = np.mean([np.abs(d[f"{c}_s{s}_b1"] - d[f"{c}_s{s}_b0"])[:, :60].mean() for s in range(1, 9)])
    n = np.mean([np.abs(d[f"{c}_s{s}_n1"] - d[f"{c}_s{s}_n0"]).mean() for s in range(1, 9)])
    print(f"{c:8s} burst synapses (inputs 0-59) {b:.4f}   noise synapses (all inputs) {n:.4f}")

print("\n(b) label-permutation null for burst selectivity, 1000 random partitions of 0-59 per run\n")
rng = np.random.default_rng(12345)
for c in ("real", "shuffled"):
    pct, true_v, null_hi = [], [], []
    for s in range(1, 9):
        B = d[f"{c}_s{s}_b1"]
        t = sel(B, TRUE)
        nulls = []
        for _ in range(1000):
            p = rng.permutation(60)
            nulls.append(sel(B, [list(p[0:20]), list(p[20:40]), list(p[40:60])]))
        nulls = np.array(nulls)
        pct.append(float((nulls >= t).mean())); true_v.append(t); null_hi.append(float(np.percentile(nulls, 95)))
        print(f"{c:8s} seed {s}: true {t:.2f}  null median {np.median(nulls):.2f}  null 95th {np.percentile(nulls, 95):.2f}  "
              f"fraction of null >= true {pct[-1]:.3f}")
    print(f"{c:8s} MEANS true {np.mean(true_v):.3f}  null 95th {np.mean(null_hi):.3f}  "
          f"seeds with true above null 95th: {sum(t > h for t, h in zip(true_v, null_hi))}/8\n")
