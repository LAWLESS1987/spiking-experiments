"""Experiment 15: a COINCIDENCE-FREE null (pre-registered: PREREG_exp15_desync_null.md).

WHY. exp14's null randomised which 20 inputs burst together but kept 20 firing together at every burst; nootxlm's
proposal (HF 191599 #2) was worded "so no 20 inputs ever burst together". Three reviewers flagged the difference.
THE ONE CHANGE from exp14's real arm: every burst spike keeps its input (so each input 0-59 has exactly the real
run's burst spike count) but gets an independent uniform random time in [0.05 s, 120 s) from a separate stream
(2000 + seed). The real arm is exp14's real column (reproduced exp11 8/8), not rerun.
Run:  .venv\\Scripts\\python.exe exp15_desync_null.py > exp15_out.txt      Out: exp15_desync_null.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from brian2 import (network_operation, Hz, Network, NeuronGroup, PoissonGroup, SpikeGeneratorGroup, SpikeMonitor,
                    Synapses, ms, mV, prefs, second, seed as br_seed, start_scope)

prefs.codegen.target = "numpy"
N, K, DUR = 100, 3, 120 * second
GROUPS = [range(0, 20), range(20, 40), range(40, 60)]
SEEDS = list(range(1, 9))
EXP14_REAL = {1: 1.83, 2: 1.56, 3: 1.92, 4: 1.86, 5: 1.9, 6: 1.91, 7: 1.9, 8: 1.83}    # exp14_out.txt real column
EXP14_SHUF = {1: 1.62, 2: 1.58, 3: 1.75, 4: 1.66, 5: 1.59, 6: 1.69, 7: 1.77, 8: 1.48}   # exp14_out.txt null column


def run_once(s, cond):
    """One run at seed s. cond == 'desync' for this experiment. Returns (a_and_b, claimer, spikes, ratio)."""
    start_scope()
    br_seed(s)
    rng = np.random.default_rng(s)
    desync = np.random.default_rng(2000 + s)             # the null's own stream

    noise = PoissonGroup(N, rates=5 * Hz)
    times, idx = [], []
    for t in np.arange(0.05, float(DUR / second), 0.25):
        g = rng.integers(K)
        for i in GROUPS[g]:
            times.append(t + rng.normal(0, 0.002)); idx.append(int(i))
    if cond == "desync":                                 # same spikes per input, independent uniform times
        times = desync.uniform(0.05, float(DUR / second), size=len(times))
        # two spikes of one input in the same 0.1 ms step are refused by SpikeGeneratorGroup: redraw just those
        while True:
            key = np.array(idx) * 10**8 + np.floor(times / 1e-4).astype(np.int64)
            _, first = np.unique(key, return_index=True)
            dup = np.setdiff1d(np.arange(len(key)), first)
            if not len(dup):
                break
            times[dup] = desync.uniform(0.05, float(DUR / second), size=len(dup))
        times = list(times)
    o = np.argsort(times)
    pattern = SpikeGeneratorGroup(N, np.array(idx)[o], np.array(times)[o] * second)

    out = NeuronGroup(K, """dv/dt = -v / (10*ms) : volt
                            dtheta/dt = -theta / (2000*ms) : volt""",
                      threshold="v > 5*mV + theta", reset="v = 0*mV; theta += 1*mV", method="exact")
    inhib = Synapses(out, out, on_pre="v_post = clip(v_post - 6*mV, -6*mV, 100*mV)")
    inhib.connect(condition="i != j")

    taupre = taupost = 20 * ms
    wmax, Apre = 2.0, 0.01
    Apost = -Apre * 1.05
    stdp = """w : 1
              dapre/dt = -apre / taupre : 1 (event-driven)
              dapost/dt = -apost / taupost : 1 (event-driven)"""
    on_pre = "v_post += w * mV\napre += Apre\nw = clip(w + apost, 0, wmax)"
    on_post = "apost += Apost\nw = clip(w + apre, 0, wmax)"
    syns = []
    for src in (noise, pattern):
        syn = Synapses(src, out, stdp, on_pre=on_pre, on_post=on_post)
        syn.connect()
        syn.w = "rand() * 0.6"
        syns.append(syn)

    state = {"targets": None}

    @network_operation(dt=100 * ms)
    def normalise():
        tot = np.zeros(K)
        for syn in syns:
            np.add.at(tot, np.array(syn.j), np.array(syn.w))
        if state["targets"] is None:
            state["targets"] = tot.copy()
            return
        for syn in syns:
            j = np.array(syn.j)
            syn.w = np.array(syn.w) * (state["targets"][j] / np.maximum(tot[j], 1e-9))

    spk = SpikeMonitor(out)
    net = Network(noise, pattern, out, inhib, syns[0], syns[1], spk, normalise)
    net.run(DUR)

    W = np.zeros((K, N))
    for syn in syns:
        W[np.array(syn.j), np.array(syn.i)] += np.array(syn.w)
    mean_on = np.array([[W[k, list(g)].mean() for g in GROUPS] for k in range(K)])
    noise_w = W[:, 60:].mean(1)
    claimer = mean_on.argmax(0)
    a = len(set(claimer.tolist())) == K
    b = all(mean_on[claimer[g], g] > 2 * noise_w[claimer[g]] for g in range(K))
    ratio = float(np.mean([mean_on[claimer[g], g] / max(noise_w[claimer[g]], 1e-9) for g in range(K)]))
    return bool(a and b), claimer.tolist(), [int((np.array(spk.i) == k).sum()) for k in range(K)], round(ratio, 2)


def _driver():
    import os
    from multiprocessing import Pool
    nworkers = max(1, int(os.environ.get("EXP15_WORKERS", "4")))
    print("exp15: coincidence-free (desync) null, seeds %s, against exp14's real column (reading rule fixed first in "
          "PREREG_exp15; %d parallel workers, numpy backend)\n" % (SEEDS, nworkers))
    with Pool(nworkers) as pool:
        out = pool.starmap(run_once, [(s, "desync") for s in SEEDS])
    real = [EXP14_REAL[s] for s in SEEDS]
    des, gaps = [], []
    for s, (ok, claim, spk, r) in zip(SEEDS, out):
        des.append(r); gaps.append(round(EXP14_REAL[s] - r, 2))
        print(f"seed {s}: desync {'PASS' if ok else 'fail'} claim={claim} spk={spk} ratio={r}  |  "
              f"exp14 real {EXP14_REAL[s]}  shuffled {EXP14_SHUF[s]}  |  gap(real-desync)={round(EXP14_REAL[s] - r, 2)}")
    mr, md = float(np.mean(real)), float(np.mean(des))
    ms = float(np.mean([EXP14_SHUF[s] for s in SEEDS]))
    pos = sum(1 for g in gaps if g > 0)
    print(f"\nmean real {mr:.3f} ; mean desync {md:.3f} ; desync/real {md / mr:.3f} ; gap > 0 on {pos}/{len(SEEDS)} seeds")
    print(f"descriptive: mean exp14 shuffled {ms:.3f} ; desync - shuffled {md - ms:+.3f}")
    if pos >= 7 and md <= 1.3:
        verdict = "MOSTLY PATTERN LEARNING (gap > 0 on >= 7/8 AND mean desync <= 1.3)"
    elif md >= 0.8 * mr:
        verdict = "MOSTLY BY CONSTRUCTION (mean desync >= 0.8 x mean real)"
    else:
        verdict = "PARTIAL -- numbers only, no verdict"
    print("READING (pre-registered):", verdict)

    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(SEEDS))
    ax.bar(x - 0.27, real, 0.27, label="real (exp14)", color="tab:blue")
    ax.bar(x, [EXP14_SHUF[s] for s in SEEDS], 0.27, label="shuffled null (exp14)", color="tab:gray")
    ax.bar(x + 0.27, des, 0.27, label="desync null (exp15)", color="tab:orange")
    ax.axhline(2.0, ls="--", c="k", lw=1, label="2x bar")
    ax.axhline(1.0, ls=":", c="k", lw=1)
    ax.set_xticks(x); ax.set_xticklabels([str(s) for s in SEEDS]); ax.set_xlabel("seed")
    ax.set_ylabel("claimed / noise weight ratio"); ax.legend(fontsize=8)
    ax.set_title("exp15: real vs shuffled vs coincidence-free null, seeds 1..8")
    plt.tight_layout(); plt.savefig("exp15_desync_null.png", dpi=110)
    print("saved exp15_desync_null.png")


if __name__ == "__main__":
    _driver()
