"""Experiment 16: rescoring real / shuffled / desync -- descriptive only (pre-registered: PREREG_exp16_rescore.md).

Reruns the three conditions with exactly their earlier code paths (exp14 real and shuffled null, exp15 desync null)
and records the noise-synapse and burst-synapse weights at t = 0 and at the end, so the score can be read against
where the weights started and without the burst synapse (silent on inputs 60-99). No verdict is attached.
Run:  .venv\\Scripts\\python.exe exp16_rescore.py > exp16_out.txt      Out: exp16_weights.npz
"""
import numpy as np
from brian2 import (network_operation, Hz, Network, NeuronGroup, PoissonGroup, SpikeGeneratorGroup, SpikeMonitor,
                    Synapses, ms, mV, prefs, second, seed as br_seed, start_scope)

prefs.codegen.target = "numpy"
N, K, DUR = 100, 3, 120 * second
GROUPS = [range(0, 20), range(20, 40), range(40, 60)]
SEEDS = list(range(1, 9))
CONDS = ("real", "shuffled", "desync")
EARLIER = {  # printed ratios: exp14_out.txt (real, null) and exp15_out.txt (desync)
    "real": {1: 1.83, 2: 1.56, 3: 1.92, 4: 1.86, 5: 1.9, 6: 1.91, 7: 1.9, 8: 1.83},
    "shuffled": {1: 1.62, 2: 1.58, 3: 1.75, 4: 1.66, 5: 1.59, 6: 1.69, 7: 1.77, 8: 1.48},
    "desync": {1: 1.01, 2: 1.0, 3: 1.13, 4: 1.08, 5: 1.04, 6: 1.12, 7: 1.17, 8: 1.03},
}


def score(W):
    mean_on = np.array([[W[k, list(g)].mean() for g in GROUPS] for k in range(K)])
    noise_w = W[:, 60:].mean(1)
    claimer = mean_on.argmax(0)
    ratio = float(np.mean([mean_on[claimer[g], g] / max(noise_w[claimer[g]], 1e-9) for g in range(K)]))
    return round(ratio, 2), claimer.tolist()


def mats(syns):
    out = []
    for syn in syns:
        W = np.zeros((K, N))
        W[np.array(syn.j), np.array(syn.i)] = np.array(syn.w)
        out.append(W)
    return out                                            # [noise, burst]


def run_once(s, cond):
    start_scope()
    br_seed(s)
    rng = np.random.default_rng(s)
    shuf = np.random.default_rng(1000 + s)               # exp14's null stream
    desync = np.random.default_rng(2000 + s)             # exp15's null stream

    noise = PoissonGroup(N, rates=5 * Hz)
    times, idx = [], []
    for t in np.arange(0.05, float(DUR / second), 0.25):
        g = rng.integers(K)
        members = shuf.choice(60, size=20, replace=False) if cond == "shuffled" else GROUPS[g]
        for i in members:
            times.append(t + rng.normal(0, 0.002)); idx.append(int(i))
    if cond == "desync":                                 # exp15, verbatim
        times = desync.uniform(0.05, float(DUR / second), size=len(times))
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
    n0, b0 = mats(syns)

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
    n1, b1 = mats(syns)
    spikes = [int((np.array(spk.i) == k).sum()) for k in range(K)]
    return n0, b0, n1, b1, spikes


def main():
    import os
    from multiprocessing import Pool
    tasks = [(s, c) for s in SEEDS for c in CONDS]
    nworkers = max(1, int(os.environ.get("EXP16_WORKERS", "4")))
    print("exp16: rescoring real / shuffled / desync, seeds %s, descriptive only (%d workers, numpy)\n" % (SEEDS, nworkers))
    with Pool(nworkers) as pool:
        res = dict(zip(tasks, pool.starmap(run_once, tasks)))
    store = {}
    for c in CONDS:
        rows = []
        for s in SEEDS:
            n0, b0, n1, b1, spikes = res[(s, c)]
            et, ec = score(n1 + b1)
            st, sc = score(n0 + b0)
            en, _ = score(n1)
            sn, _ = score(n0)
            rows.append((et, st, en, sn, ec == sc))
            print(f"{c:8s} seed {s}: end_total={et} (earlier {EARLIER[c][s]}{'' if et == EARLIER[c][s] else ' MISMATCH'}) "
                  f"start_total={st} end_noise={en} start_noise={sn} claim_end={ec} claim_start={sc} "
                  f"same_claim={ec == sc} spk={spikes}")
            for name, arr in (("n0", n0), ("b0", b0), ("n1", n1), ("b1", b1)):
                store[f"{c}_s{s}_{name}"] = arr
        m = np.array([r[:4] for r in rows], dtype=float).mean(0)
        print(f"{c:8s} MEANS end_total={m[0]:.3f} start_total={m[1]:.3f} end_noise={m[2]:.3f} start_noise={m[3]:.3f} "
              f"same_claim={sum(r[4] for r in rows)}/{len(SEEDS)} reproduce={sum(r[0] == EARLIER[c][s] for r, s in zip(rows, SEEDS))}/{len(SEEDS)}\n")
    np.savez_compressed("exp16_weights.npz", **store)
    print("saved exp16_weights.npz")


if __name__ == "__main__":
    main()
