"""exp17_decompose_ratio.py -- descriptive only: split the published ratio into its parts on exp17's saved weights.

For each group g and its claimer k (the argmax of total weight, as exp16_rescore.score() picks it):
  b   = the claimer's mean BURST-synapse weight on g's 20 inputs (the synapses the pattern drives)
  n_g = the claimer's mean NOISE-synapse weight on the same inputs (5 Hz background, never pattern-driven)
  s   = the claimer's mean burst-synapse weight on inputs 60-99 (silent: those burst synapses never get a spike)
  n   = the claimer's mean noise-synapse weight on inputs 60-99
  o   = the claimer's mean burst-synapse weight on the other two groups
so that the published per-group ratio is (b + n_g) / (s + n). With n_g ~ n ~ s ~ x (the unlearned background), it is
about (1 + b/x) / 2: a ratio of 2 needs the learned burst synapse at about 3x the background.

No verdict attached; written 2026-11-20 as the diagnosis behind prereg/PREREG_exp18_ltp_threshold.md.
Run:  .venv\\Scripts\\python.exe exp17_decompose_ratio.py > exp17_decompose_out.txt      In: exp17_weights.npz
"""
import numpy as np

GROUPS = [list(range(0, 20)), list(range(20, 40)), list(range(40, 60))]
SEEDS = list(range(9, 17))


def parts(n1, b1):
    W = n1 + b1
    mean_on = np.array([[W[k, g].mean() for g in GROUPS] for k in range(3)])
    claim = mean_on.argmax(0)
    rows = []
    for gi, g in enumerate(GROUPS):
        k = claim[gi]
        others = [i for h, gg in enumerate(GROUPS) if h != gi for i in gg]
        b, ng = b1[k, g].mean(), n1[k, g].mean()
        s, n = b1[k, 60:].mean(), n1[k, 60:].mean()
        o = b1[k, others].mean()
        rows.append((b, ng, s, n, o, (b + ng) / (s + n)))
    return rows


def main():
    z = np.load("exp17_weights.npz")
    for cond in ("real", "shuffled"):
        allrows = []
        for s in SEEDS:
            rows = parts(z[f"{cond}_s{s}_n1"], z[f"{cond}_s{s}_b1"])
            allrows += rows
            print(f"{cond:8s} seed {s}: " + "  ".join(
                f"g{g}: b {r[0]:.3f} n_g {r[1]:.3f} s {r[2]:.3f} n {r[3]:.3f} o {r[4]:.3f} ratio {r[5]:.2f}"
                for g, r in enumerate(rows)))
        a = np.array(allrows)
        x = (a[:, 2] + a[:, 3]) / 2
        print(f"{cond:8s} MEANS b {a[:,0].mean():.3f}  n_g {a[:,1].mean():.3f}  s {a[:,2].mean():.3f}  "
              f"n {a[:,3].mean():.3f}  o {a[:,4].mean():.3f}  b/x {np.mean(a[:,0] / x):.2f}  o/x {np.mean(a[:,4] / x):.2f}  "
              f"per-group ratio {a[:,5].mean():.2f} (min {a[:,5].min():.2f}, max {a[:,5].max():.2f}; "
              f"above 2.0: {(a[:,5] > 2).sum()} of {len(a)})\n")


if __name__ == "__main__":
    main()
