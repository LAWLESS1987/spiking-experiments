"""Experiment 12: Misha Mahowald's O(N) winner-take-all as a FOURTH inhibition architecture on the (b) near-miss.

WHAT MAHOWALD'S CIRCUIT ACTUALLY IS, AND WHY IT IS A DISTINCT ARM. Lazzaro, Ryckebusch, Mahowald & Mead,
"Winner-Take-All Networks of O(N) Complexity" (NIPS 1988 / 1989), mediate competition through a SINGLE SHARED
node -- a common line that every cell drives and that feeds back to every cell -- instead of all-to-all lateral
wiring. That is why it is O(N): N connections up, N down, one global node, no N^2 lateral mesh. The three arms we
can now compare differ ONLY in how inhibition is routed:
  direct      (control, exp5-7):  out->out, i!=j, N(N-1) synapses.                      -- blunt all-to-all.
  inhib_pop   (exp11, Diehl&Cook): K inhibitory neurons; exc[k] drives inh[k] which inhibits the OTHERS (not k).
  wta_global  (THIS, Mahowald):    ONE global inhibitory node; every out neuron drives it, it inhibits EVERY
                                   out neuron (including the one that just won -- faithful to the shared line; the
                                   winner has already spiked and is counted, the point is that losers are
                                   suppressed before they reach threshold).
Inhibition STRENGTH is held at 6 mV in every arm, so the only thing that varies is the routing topology -- this
isolates Mahowald's architectural contribution (a single O(N) common node) rather than an amount of inhibition.

This arm became usable only now: before the exp5-11 competitive rig existed there was nothing to put her circuit
into. exp1 was a feedforward classifier. Now there is a validated STDP + lateral-inhibition apparatus, so her WTA
can be instantiated and measured head-to-head on the same near-miss, same seeds, same bar. (AER and the silicon
retina stay out of reach -- those are hardware, and this lab is simulation-only.)

Params fixed BEFORE the run, with reasons, not tuned: global node tau 5 ms, threshold 2 mV, exc->node weight 10 mV
(one exc spike reliably fires the node, matching exp11's exc->inh), node->out 6 mV (matched to the control and exp11).

PASS BAR per run -- UNCHANGED from exp5-11: (a) each pattern claimed by a DIFFERENT output neuron; (b) each neuron's
mean weight on its claimed group > 2x its mean weight on the noise-only inputs.
KEEP RULE -- fixed before the run: Mahowald's global WTA is kept as an improvement IFF it passes (a AND b) on
STRICTLY MORE of the eight seeds than the direct control. A tie or worse is not kept. Recorded as is either way.
Run:  .venv\\Scripts\\python.exe exp12_mahowald_wta.py      Out: exp12_mahowald_wta.png
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
WMAX = 2.0


def run_once(s, arch):
    """One run at seed s. arch in {'direct','wta_global'}. Returns (a_and_b, claimer, spikes, ratio)."""
    start_scope()
    br_seed(s)
    rng = np.random.default_rng(s)

    noise = PoissonGroup(N, rates=5 * Hz)
    times, idx = [], []
    for t in np.arange(0.05, float(DUR / second), 0.25):
        g = rng.integers(K)
        for i in GROUPS[g]:
            times.append(t + rng.normal(0, 0.002)); idx.append(i)
    o = np.argsort(times)
    pattern = SpikeGeneratorGroup(N, np.array(idx)[o], np.array(times)[o] * second)

    out = NeuronGroup(K, """dv/dt = -v / (10*ms) : volt
                            dtheta/dt = -theta / (2000*ms) : volt""",
                      threshold="v > 5*mV + theta", reset="v = 0*mV; theta += 1*mV", method="exact")

    if arch == "direct":                                  # control: direct lateral inhibition (exp5-7)
        inhib = Synapses(out, out, on_pre="v_post = clip(v_post - 6*mV, -6*mV, 100*mV)")
        inhib.connect(condition="i != j")
        inh_objs = [inhib]
    else:                                                 # treatment: Mahowald O(N) single shared global node
        node = NeuronGroup(1, "dv/dt = -v / (5*ms) : volt", threshold="v > 2*mV", reset="v = 0*mV", method="exact")
        e2n = Synapses(out, node, on_pre="v_post += 10*mV")          # every out neuron drives the common line
        e2n.connect()
        n2e = Synapses(node, out, on_pre="v_post = clip(v_post - 6*mV, -6*mV, 100*mV)")  # common line inhibits all
        n2e.connect()
        inh_objs = [node, e2n, n2e]

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
    net = Network(noise, pattern, out, *inh_objs, syns[0], syns[1], spk, normalise)
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
    # SPEEDUP (2026-10-20): the 16 (seed, arch) tasks are independent and fully determined by (seed, arch)
    # -- each calls start_scope()+br_seed(s)+default_rng(s) -- so farming them across processes is
    # RESULT-IDENTICAL to the serial run. Backend stays numpy (no cython: the venv has no MSVC compiler),
    # so these numbers remain directly comparable to exp11's numpy run. The serial numpy version is frozen
    # in git at the pre-registration commit. Workers capped (EXP12_WORKERS, default 5) to respect RAM.
    import os
    from multiprocessing import Pool
    tasks = [(s, arch) for s in SEEDS for arch in ("direct", "wta_global")]
    nworkers = max(1, int(os.environ.get("EXP12_WORKERS", "5")))
    print("exp12: Mahowald O(N) global WTA vs direct lateral inhibition, seeds %s "
          "(bar+keep rule fixed first; %d parallel workers, numpy backend)\n" % (SEEDS, nworkers))
    with Pool(nworkers) as pool:
        out = pool.starmap(run_once, tasks)           # starmap preserves task order
    res = {t: r for t, r in zip(tasks, out)}

    direct_pass, wta_pass = 0, 0
    for s in SEEDS:
        dok, dclaim, dspk, dr = res[(s, "direct")]
        wok, wclaim, wspk, wr = res[(s, "wta_global")]
        direct_pass += dok
        wta_pass += wok
        print(f"seed {s}: direct {'PASS' if dok else 'fail'} claim={dclaim} spk={dspk} ratio={dr}  |  "
              f"wta_global {'PASS' if wok else 'fail'} claim={wclaim} spk={wspk} ratio={wr}")

    print(f"\ndirect (control) passed {direct_pass}/{len(SEEDS)} ; wta_global (treatment) passed {wta_pass}/{len(SEEDS)}")
    print("KEEP RULE: Mahowald global WTA kept?", "YES" if wta_pass > direct_pass else
          "NO -- not strictly more seeds than the control (recorded as is)")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["direct\n(control)", "Mahowald WTA\n(exp12)"], [direct_pass, wta_pass], color=["tab:gray", "tab:cyan"])
    ax.set_ylabel("seeds passing (of %d)" % len(SEEDS)); ax.set_ylim(0, len(SEEDS))
    ax.set_title("one-neuron-per-pattern AND claimed > 2x noise, seeds 1..8")
    for i, v in enumerate([direct_pass, wta_pass]):
        ax.text(i, v + 0.05, str(v), ha="center")
    plt.tight_layout(); plt.savefig("exp12_mahowald_wta.png", dpi=110)
    print("saved exp12_mahowald_wta.png")


if __name__ == "__main__":
    _driver()
