"""exp18_posthoc.py -- POST HOC, descriptive only: two checks asked for by an outside read of exp18 (Gemini, 2026-11-20).

1. Saturation. Are the claimed group's burst synapses near wmax = 2.0, so that a ceiling, not plasticity, limited
   their growth under the threshold? Reported: max weight, and the share at or above 1.8 (0.9 * wmax), per arm.
2. Was the ratio's flatness automatic? Normalisation is the only thing that moves the silent burst synapses on
   inputs 60-99, so their change between arms (s_threshold / s_control) is the budget's own scale. The ratio is
   recomputed with the threshold arm's noise synapses and silent synapses, but with the claimed burst synapses
   scaled by that same factor (as if plasticity had left them to follow the budget like the silent ones). If that
   ratio sits above 1.839, the ratio held because the claimed synapses lagged the budget, not by arithmetic alone.
Run:  .venv\\Scripts\\python.exe exp18_posthoc.py > exp18_posthoc_out.txt      In: exp18_weights.npz
"""
import numpy as np

GROUPS = [list(range(0, 20)), list(range(20, 40)), list(range(40, 60))]
SEEDS = list(range(1, 9))


def claims(n1, b1):
    W = n1 + b1
    mean_on = np.array([[W[k, g].mean() for g in GROUPS] for k in range(3)])
    return mean_on.argmax(0)


def main():
    z = np.load("exp18_weights.npz")
    print("1. saturation of the claimed group's burst synapses (wmax = 2.0)")
    for arm in ("control", "threshold"):
        allw = []
        for s in SEEDS:
            n1, b1 = z[f"{arm}_s{s}_n1"], z[f"{arm}_s{s}_b1"]
            c = claims(n1, b1)
            for g in range(3):
                allw += list(b1[c[g], GROUPS[g]])
        allw = np.array(allw)
        print(f"   {arm:9s}: {len(allw)} synapses, mean {allw.mean():.3f}, max {allw.max():.3f}, "
              f"share >= 1.8: {(allw >= 1.8).mean():.4f}, share >= 1.0: {(allw >= 1.0).mean():.3f}")
    print("\n2. the ratio if the claimed burst synapses had followed the budget (seed by seed)")
    obs, cf = [], []
    for s in SEEDS:
        nc, bc = z[f"control_s{s}_n1"], z[f"control_s{s}_b1"]
        nt, bt = z[f"threshold_s{s}_n1"], z[f"threshold_s{s}_b1"]
        cc, ct = claims(nc, bc), claims(nt, bt)
        r_obs, r_cf = [], []
        for g in range(3):
            kc, kt = cc[g], ct[g]
            budget = bt[kt, 60:].mean() / bc[kc, 60:].mean()      # silent synapses: moved only by normalisation
            num_obs = bt[kt, GROUPS[g]].mean() + nt[kt, GROUPS[g]].mean()
            num_cf = bc[kc, GROUPS[g]].mean() * budget + nt[kt, GROUPS[g]].mean()
            den = bt[kt, 60:].mean() + nt[kt, 60:].mean()
            r_obs.append(num_obs / den)
            r_cf.append(num_cf / den)
        obs.append(np.mean(r_obs)); cf.append(np.mean(r_cf))
        print(f"   seed {s}: observed {obs[-1]:.3f}  claimed synapses scaled with the budget {cf[-1]:.3f}")
    print(f"   MEAN observed {np.mean(obs):.3f}  if the claimed synapses had followed the budget {np.mean(cf):.3f}")


if __name__ == "__main__":
    main()
