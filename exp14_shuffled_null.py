"""Experiment 14: a shuffled-burst NULL for the ~1.9x claimed/noise ratio (pre-registered: PREREG_exp14_shuffled_null.md).

WHY. exp7-12 stall at a ratio of ~1.5-1.9x against the 2x bar, and none of them measured what ratio the scoring
gives with NO pattern to learn. nootxlm (HF 191599 #2, 2026-11-09) proposed the test: same seeds, same Poisson
streams, but no 20 inputs ever burst together; score exactly as now; the gap to the real run is the learning.

THE ONE CHANGE (null vs real): which inputs each burst fires.
  real: one of the three fixed groups (0-19, 20-39, 40-59) -- exactly exp11's "direct" arm.
  null: 20 inputs drawn at random, without replacement, from 0-59, from a SEPARATE random stream (1000 + seed), so
        the main stream (group draw, jitter) is consumed identically and every input in 0-59 still bursts with
        probability 1/3. Burst times, jitter, noise streams and everything downstream are unchanged.
Scoring is exp11's, unchanged. The reading rule is in the pre-registration, fixed before this file existed.
Run:  .venv\\Scripts\\python.exe exp14_shuffled_null.py      Out: exp14_out.txt (by redirect), exp14_shuffled_null.png
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
EXP11_DIRECT = {1: 1.83, 2: 1.56, 3: 1.92, 4: 1.86, 5: 1.9, 6: 1.91, 7: 1.9, 8: 1.83}   # exp11_out.txt, as printed


def run_once(s, cond):
    """One run at seed s. cond in {'real','null'}. Returns (a_and_b, claimer, spikes, ratio)."""
    start_scope()
    br_seed(s)
    rng = np.random.default_rng(s)
    shuf = np.random.default_rng(1000 + s)               # the null's own stream; unused (but harmless) for 'real'

    noise = PoissonGroup(N, rates=5 * Hz)
    times, idx = [], []
    for t in np.arange(0.05, float(DUR / second), 0.25):
        g = rng.integers(K)
        members = GROUPS[g] if cond == "real" else shuf.choice(60, size=20, replace=False)
        for i in members:
            times.append(t + rng.normal(0, 0.002)); idx.append(int(i))
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
    tasks = [(s, c) for s in SEEDS for c in ("real", "null")]
    nworkers = max(1, int(os.environ.get("EXP14_WORKERS", "4")))
    print("exp14: shuffled-burst null vs real, seeds %s (reading rule fixed first in PREREG_exp14; "
          "%d parallel workers, numpy backend)\n" % (SEEDS, nworkers))
    with Pool(nworkers) as pool:
        out = pool.starmap(run_once, tasks)
    res = {t: r for t, r in zip(tasks, out)}

    real, null, gaps, repro = [], [], [], []
    for s in SEEDS:
        rok, rclaim, rspk, rr = res[(s, "real")]
        nok, nclaim, nspk, nr = res[(s, "null")]
        real.append(rr); null.append(nr); gaps.append(round(rr - nr, 2)); repro.append(rr == EXP11_DIRECT[s])
        print(f"seed {s}: real {'PASS' if rok else 'fail'} claim={rclaim} spk={rspk} ratio={rr}  |  "
              f"null {'PASS' if nok else 'fail'} claim={nclaim} spk={nspk} ratio={nr}  |  gap={round(rr - nr, 2)}")

    mr, mn = float(np.mean(real)), float(np.mean(null))
    pos = sum(1 for g in gaps if g > 0)
    print(f"\nREPRODUCTION: real ratios equal exp11 direct on {sum(repro)}/{len(SEEDS)} seeds")
    print(f"mean real {mr:.3f} ; mean null {mn:.3f} ; null/real {mn / mr:.3f} ; gap > 0 on {pos}/{len(SEEDS)} seeds")
    if pos >= 7 and mn <= 1.3:
        verdict = "MOSTLY PATTERN LEARNING (gap > 0 on >= 7/8 AND mean null <= 1.3)"
    elif mn >= 0.8 * mr:
        verdict = "MOSTLY BY CONSTRUCTION (mean null >= 0.8 x mean real)"
    else:
        verdict = "PARTIAL -- numbers only, no verdict"
    print("READING (pre-registered):", verdict)

    fig, ax = plt.subplots(figsize=(6.5, 4))
    x = np.arange(len(SEEDS))
    ax.bar(x - 0.2, real, 0.4, label="real (fixed groups)", color="tab:blue")
    ax.bar(x + 0.2, null, 0.4, label="null (shuffled bursts)", color="tab:gray")
    ax.axhline(2.0, ls="--", c="k", lw=1, label="2x bar")
    ax.axhline(1.0, ls=":", c="k", lw=1)
    ax.set_xticks(x); ax.set_xticklabels([str(s) for s in SEEDS]); ax.set_xlabel("seed")
    ax.set_ylabel("claimed / noise weight ratio"); ax.legend(fontsize=8)
    ax.set_title("exp14: real vs shuffled-burst null, seeds 1..8")
    plt.tight_layout(); plt.savefig("exp14_shuffled_null.png", dpi=110)
    print("saved exp14_shuffled_null.png")


if __name__ == "__main__":
    _driver()
