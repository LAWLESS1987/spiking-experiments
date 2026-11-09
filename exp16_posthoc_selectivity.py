"""exp16 post-hoc (NOT pre-registered; written after reading exp16_out.txt): burst-synapse selectivity.

exp16 showed the published ratio lives in the burst synapses (noise-only ratios stay at their t = 0 values in every
condition), and that its denominator compares inputs that burst with inputs whose burst synapse never fires. This
asks the question within the bursting inputs only: for each group g, the claiming output's mean BURST-synapse
weight on g over its mean burst-synapse weight on the other two groups (inputs 0-59). Claimer = argmax of burst
weight per group. Same at t = 0, for the selection floor. Reads exp16_weights.npz; runs nothing.
Run:  .venv\\Scripts\\python.exe exp16_posthoc_selectivity.py > exp16_posthoc_out.txt
"""
import numpy as np

GROUPS = [list(range(0, 20)), list(range(20, 40)), list(range(40, 60))]
K = 3
d = np.load("exp16_weights.npz")


def sel(B):
    mean_on = np.array([[B[k, g].mean() for g in GROUPS] for k in range(K)])
    claimer = mean_on.argmax(0)
    r = []
    for g in range(K):
        k = claimer[g]
        others = [h for h in range(K) if h != g]
        r.append(mean_on[k, g] / max(np.mean([mean_on[k, h] for h in others]), 1e-9))
    return float(np.mean(r))


print("exp16 post-hoc burst-synapse selectivity within inputs 0-59 (NOT pre-registered)\n")
for c in ("real", "shuffled", "desync"):
    st, en = [], []
    for s in range(1, 9):
        a, b = sel(d[f"{c}_s{s}_b0"]), sel(d[f"{c}_s{s}_b1"])
        st.append(a); en.append(b)
        print(f"{c:8s} seed {s}: start {a:.2f}  end {b:.2f}")
    print(f"{c:8s} MEANS start {np.mean(st):.3f}  end {np.mean(en):.3f}  (end > start on {sum(e > t for e, t in zip(en, st))}/8)\n")
