"""Experiment 18: an LTP threshold tied to pre-before-post timing (pre-registered: prereg/PREREG_exp18_ltp_threshold.md).

CONTROL  exp16_rescore.run_once(s, "real"), imported unchanged: exp11's direct-inhibition network.
TREATMENT the same code path, line for line, with ONE change: at a post spike a synapse potentiates only if its
         presynaptic trace apre exceeds LTP_THR = Apre * exp(-5 ms / taupre), i.e. its input fired within the last
         5 ms. LTD and everything else unchanged.
Seeds 1-8, 120 s. Bar (a AND b, exp11's lines), keep rule, collapse rule, validity reading and the reproduction check
are applied here exactly as the pre-registration states them, and printed beside the numbers.
Run:  .venv\\Scripts\\python.exe exp18_ltp_threshold.py > exp18_out.txt      Out: exp18_weights.npz
      .venv\\Scripts\\python.exe exp18_ltp_threshold.py --smoke   (seed 0, 2 s: checks the code runs; reads nothing)
"""
import sys

import numpy as np
from brian2 import (network_operation, Hz, Network, NeuronGroup, PoissonGroup, SpikeGeneratorGroup, SpikeMonitor,
                    Synapses, ms, mV, prefs, second, seed as br_seed, start_scope)

import exp16_rescore as X                                 # the control, unchanged
from exp17_selectivity_new_seeds import perm95, sel       # exp17's measure and its relabeling null, unchanged

prefs.codegen.target = "numpy"
N, K = 100, 3
GROUPS = [range(0, 20), range(20, 40), range(40, 60)]
TRUE = [list(g) for g in GROUPS]
SEEDS = list(range(1, 9))
WINDOW_MS = 5.0                                           # fixed in the pre-registration, not tuned
COLLAPSE_SPIKES, COLLAPSE_SEEDS = 20, 5
PUBLISHED_REAL = {1: 1.83, 2: 1.56, 3: 1.92, 4: 1.86, 5: 1.9, 6: 1.91, 7: 1.9, 8: 1.83}   # exp16 real == exp11 direct


def run_treatment(s, dur_s=120.0):
    """exp16_rescore.run_once(s, "real") line for line; the one change is marked CHANGED."""
    DUR = dur_s * second
    start_scope()
    br_seed(s)
    rng = np.random.default_rng(s)

    noise = PoissonGroup(N, rates=5 * Hz)
    times, idx = [], []
    for t in np.arange(0.05, float(DUR / second), 0.25):
        g = rng.integers(K)
        for i in GROUPS[g]:
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
    ltp_thr = Apre * float(np.exp(-WINDOW_MS / 20.0))    # CHANGED: the trace one spike leaves 5 ms after arriving
    ltp_floor = Apre * float(np.exp(-100.0 / 20.0))      # counters only: below this no pre spike is recent
    stdp = """w : 1
              n_pass : 1
              n_block : 1
              dapre/dt = -apre / taupre : 1 (event-driven)
              dapost/dt = -apost / taupost : 1 (event-driven)"""
    on_pre = "v_post += w * mV\napre += Apre\nw = clip(w + apost, 0, wmax)"
    on_post = ("apost += Apost\n"                                            # LTD side unchanged
               "n_pass += int(apre > ltp_thr)\n"
               "n_block += int(apre <= ltp_thr) * int(apre > ltp_floor)\n"
               "w = clip(w + apre * int(apre > ltp_thr), 0, wmax)")          # CHANGED: gated potentiation
    syns = []
    for src in (noise, pattern):
        syn = Synapses(src, out, stdp, on_pre=on_pre, on_post=on_post)
        syn.connect()
        syn.w = "rand() * 0.6"
        syns.append(syn)
    n0, b0 = X.mats(syns)

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
    n1, b1 = X.mats(syns)
    spikes = [int((np.array(spk.i) == k).sum()) for k in range(K)]
    counts = {name: (np.array(syn.i), np.array(syn.j), np.array(syn.n_pass), np.array(syn.n_block))
              for name, syn in (("noise", syns[0]), ("burst", syns[1]))}
    return n0, b0, n1, b1, spikes, counts


def task(s, arm):
    if arm == "control":
        n0, b0, n1, b1, spikes = X.run_once(s, "real")
        return n0, b0, n1, b1, spikes, None
    return run_treatment(s)


def pass_ab(W):
    """exp11's scoring lines, verbatim in effect: (a) distinct claimers, (b) each group's claimer > 2x its 60-99 mean."""
    mean_on = np.array([[W[k, list(g)].mean() for g in GROUPS] for k in range(K)])
    noise_w = W[:, 60:].mean(1)
    claimer = mean_on.argmax(0)
    a = len(set(claimer.tolist())) == K
    per = [mean_on[claimer[g], g] / max(noise_w[claimer[g]], 1e-9) for g in range(K)]
    b = all(mean_on[claimer[g], g] > 2 * noise_w[claimer[g]] for g in range(K))
    return bool(a and b), claimer.tolist(), [round(float(p), 2) for p in per], round(float(np.mean(per)), 2)


def split(n1, b1, claimer):
    rows = []
    for gi, g in enumerate(TRUE):
        k = claimer[gi]
        others = [i for h, gg in enumerate(TRUE) if h != gi for i in gg]
        rows.append((b1[k, g].mean(), n1[k, g].mean(), b1[k, 60:].mean(), n1[k, 60:].mean(), b1[k, others].mean()))
    return np.array(rows).mean(0)                         # b, n_g, s, n, o


def counter_classes(counts, claimer):
    own = {j: set(i for g in range(K) if claimer[g] == j for i in TRUE[g]) for j in range(K)}
    tot = {c: [0, 0] for c in ("burst_own_group", "burst_other_groups", "burst_60_99", "noise")}
    i, j, p, bl = counts["noise"]
    tot["noise"] = [int(p.sum()), int(bl.sum())]
    i, j, p, bl = counts["burst"]
    for ii, jj, pp, bb in zip(i, j, p, bl):
        c = "burst_60_99" if ii >= 60 else ("burst_own_group" if ii in own[jj] else "burst_other_groups")
        tot[c][0] += int(pp); tot[c][1] += int(bb)
    return tot


def histogram(label, vals, lo=1.0, hi=3.2, step=0.1):
    edges = np.round(np.arange(lo, hi + 1e-9, step), 2)
    print(f"  {label}: " + " ".join(f"{v:.2f}" for v in vals))
    below = sum(v < lo for v in vals)
    if below:
        print(f"    < {lo:.1f} | " + "#" * below)
    for a, b in zip(edges[:-1], edges[1:]):
        n = sum(a <= v < b for v in vals)
        if n:
            print(f"    {a:.1f}-{b:.1f} | " + "#" * n)
    above = sum(v >= hi for v in vals)
    if above:
        print(f"    >= {hi:.1f} | " + "#" * above)


def main():
    import os
    from multiprocessing import Pool
    if "--smoke" in sys.argv:
        r = run_treatment(0, dur_s=2.0)
        print("smoke: ran 2 s on seed 0; spikes", r[4], "- no reading taken")
        return
    tasks = [(s, arm) for s in SEEDS for arm in ("control", "threshold")]
    nworkers = max(1, int(os.environ.get("EXP18_WORKERS", "8")))
    print("exp18: LTP threshold (pre-before-post within %.0f ms) vs exp11's direct inhibition, seeds %s "
          "(pre-registered: prereg/PREREG_exp18_ltp_threshold.md; %d workers, numpy)\n" % (WINDOW_MS, SEEDS, nworkers))
    with Pool(nworkers) as pool:
        res = dict(zip(tasks, pool.starmap(task, tasks)))

    summary, store = {}, {}
    for arm in ("control", "threshold"):
        rows = []
        for s in SEEDS:
            n0, b0, n1, b1, spikes, counts = res[(s, arm)]
            ok, claim, per, ratio = pass_ab(n1 + b1)
            st, en = sel(b0, TRUE), sel(b1, TRUE)
            p95, frac = perm95(b1, 60000 + s)
            b, ng, sl, nn, o = split(n1, b1, claim)
            rows.append(dict(seed=s, ok=ok, claim=claim, per=per, ratio=ratio, spikes=spikes, sel0=st, sel=en,
                             p95=p95, b=b, ng=ng, s=sl, n=nn, o=o, counts=counts))
            extra = ""
            if arm == "control":
                pub = PUBLISHED_REAL[s]
                extra = f"  (exp16 published {pub}{'' if ratio == pub else ' MISMATCH'})"
            print(f"{arm:9s} seed {s}: {'PASS' if ok else 'fail'} claim={claim} per-group={per} ratio={ratio}{extra} "
                  f"spk={spikes} sel {st:.2f}->{en:.2f} perm95 {p95:.2f} | b {b:.3f} n_g {ng:.3f} s {sl:.3f} "
                  f"n {nn:.3f} o {o:.3f}")
            if counts is not None:
                c = counter_classes(counts, claim)
                print("          LTP let through / blocked at post spikes: " + "; ".join(
                    f"{k} {v[0]}/{v[1]}" for k, v in c.items()))
            for name, arr in (("n0", n0), ("b0", b0), ("n1", n1), ("b1", b1)):
                store[f"{arm}_s{s}_{name}"] = arr
        summary[arm] = rows
        print()

    ctl, thr = summary["control"], summary["threshold"]
    cp, tp = sum(r["ok"] for r in ctl), sum(r["ok"] for r in thr)
    print("Per-seed distributions (bins of 0.1), read beside the counts:")
    for arm, rows in (("control", ctl), ("threshold", thr)):
        histogram(f"{arm} ratio", [r["ratio"] for r in rows])
        histogram(f"{arm} selectivity", [r["sel"] for r in rows])
    print()
    repro = sum(r["ratio"] == PUBLISHED_REAL[r["seed"]] for r in ctl)
    print(f"REPRODUCTION: control matches exp16's published ratio on {repro}/8 seeds")
    collapsed = sum(min(r["spikes"]) < COLLAPSE_SPIKES for r in thr)
    print(f"COLLAPSE CHECK: treatment seeds with an output under {COLLAPSE_SPIKES} spikes: {collapsed}/8")
    if collapsed >= COLLAPSE_SEEDS:
        print("READING (pre-registered): the threshold COLLAPSED firing (exp8's shape). Stopped here: no rerun, no change.")
    else:
        print(f"BAR (a AND b): control {cp}/8, threshold {tp}/8")
        kept = tp > cp
        print("KEEP RULE (pre-registered):", "KEPT -- strictly more seeds than the control" if kept else
              "NOT KEPT -- not strictly more seeds than the control (a null, recorded as is)")
        cs, ts = sum(r["sel"] >= 2.0 for r in ctl), sum(r["sel"] >= 2.0 for r in thr)
        cm, tm = float(np.mean([r["sel"] for r in ctl])), float(np.mean([r["sel"] for r in thr]))
        print(f"SELECTIVITY: >= 2.0 on control {cs}/8, threshold {ts}/8; mean control {cm:.3f}, threshold {tm:.3f}")
        if kept:
            print("VALIDITY (pre-registered):", "pattern learning moved with the ratio" if (ts >= cs and tm >= cm) else
                  "the ratio moved, selectivity did not: the dilution term, not pattern learning")
    np.savez_compressed("exp18_weights.npz", **store)
    print("saved exp18_weights.npz")


if __name__ == "__main__":
    main()
