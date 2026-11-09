"""Experiment 11: does a DEDICATED INHIBITORY POPULATION (Diehl & Cook 2015) push the (b) near-miss past 2x?

WHY THIS, AND WHY IT IS A TEST OF THE exp5-10 DIAGNOSIS, NOT A NEW GUESS. exp5->10 left one thing standing: on the
corrected apparatus the normalise control reaches (a) every seed but stalls at a pattern/noise weight ratio of
~1.9x -- just under the 2x bar (b) -- on all eight seeds. The synthesis diagnosed the cause: with only K=3 output
neurons inhibiting each other DIRECTLY, winner-take-all is blunt, so the winning neuron still fires on some
chance noise coincidences; those spikes potentiate noise synapses (spurious LTP) and hold the ratio near 1.9x.
That diagnosis makes a falsifiable prediction: SHARPEN the competition and the spurious noise LTP should fall and
the ratio should rise. Diehl & Cook (2015, "Unsupervised learning of digit recognition using STDP") sharpen it with
a dedicated inhibitory population instead of direct lateral synapses: each excitatory neuron drives ONE inhibitory
neuron, which inhibits every OTHER excitatory neuron. That is the standard architecture, and it is the clean way to
test the diagnosis -- if the diagnosis is right, routing inhibition through the population clears 2x on more seeds;
if it does not, the diagnosis is wrong and the ratio ceiling is something else.

THE ONE CHANGE (treatment vs control): how lateral inhibition is wired. Everything else -- STDP, adaptive threshold,
weight-total normalisation, the eight seeds, the (a AND b) bar -- is exactly the exp7 control.
  control   ("direct"):    out->out inhibitory synapses, i!=j, v_post -= 6 mV  (exp5-7's wiring).
  treatment ("inhib_pop"): a K-neuron inhibitory group; out->inh one-to-one (i==j, +10 mV so one exc spike fires its
                           paired inh), inh->out all-but-self (i!=j, v_post -= 6 mV). The 6 mV inhibition strength is
                           IDENTICAL to the control, so the ONLY difference is the routing (direct vs via a
                           dedicated population) -- not the amount of inhibition.
Params fixed BEFORE the run, with reasons, not tuned: inh tau 5 ms (inhibition is prompt), inh threshold 2 mV with
exc->inh weight 10 mV (one exc spike reliably crosses it), inh->out 6 mV (matches the control exactly).

PASS BAR per run -- UNCHANGED from exp5-10: (a) each pattern claimed by a DIFFERENT output neuron; (b) each neuron's
mean weight on its claimed group > 2x its mean weight on the noise-only inputs.
KEEP RULE -- fixed before the run: the inhibitory population is kept as an improvement IFF it passes (a AND b) on
STRICTLY MORE of the eight seeds than the direct control. A tie or worse is not kept. Recorded as is either way.
Run:  .venv\\Scripts\\python.exe exp11_inhib_pop.py      Out: exp11_inhib_pop.png
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
    """One run at seed s. arch in {'direct','inhib_pop'}. Returns (a_and_b, claimer, spikes, ratio)."""
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
    else:                                                 # treatment: dedicated inhibitory population (Diehl & Cook)
        inh = NeuronGroup(K, "dv/dt = -v / (5*ms) : volt", threshold="v > 2*mV", reset="v = 0*mV", method="exact")
        e2i = Synapses(out, inh, on_pre="v_post += 10*mV")           # each exc neuron drives its OWN inh neuron
        e2i.connect(condition="i == j")
        i2e = Synapses(inh, out, on_pre="v_post = clip(v_post - 6*mV, -6*mV, 100*mV)")   # inh inhibits the OTHERS
        i2e.connect(condition="i != j")
        inh_objs = [inh, e2i, i2e]

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
    # SPEEDUP (2026-10-20): the 16 (seed, arch) tasks are independent and fully determined by (seed, arch),
    # so farming them across processes is RESULT-IDENTICAL to the serial run. Backend stays numpy. The serial
    # numpy version is frozen in git at the pre-registration commit; this is a harness change, not a design one.
    # Workers capped (EXP11_WORKERS, default 4) to respect RAM.
    import os
    from multiprocessing import Pool
    tasks = [(s, arch) for s in SEEDS for arch in ("direct", "inhib_pop")]
    nworkers = max(1, int(os.environ.get("EXP11_WORKERS", "4")))
    print("exp11: dedicated inhibitory population vs direct lateral inhibition, seeds %s "
          "(bar+keep rule fixed first; %d parallel workers, numpy backend)\n" % (SEEDS, nworkers))
    with Pool(nworkers) as pool:
        out = pool.starmap(run_once, tasks)
    res = {t: r for t, r in zip(tasks, out)}

    direct_pass, pop_pass = 0, 0
    for s in SEEDS:
        dok, dclaim, dspk, dr = res[(s, "direct")]
        pok, pclaim, pspk, pr = res[(s, "inhib_pop")]
        direct_pass += dok
        pop_pass += pok
        print(f"seed {s}: direct {'PASS' if dok else 'fail'} claim={dclaim} spk={dspk} ratio={dr}  |  "
              f"inhib_pop {'PASS' if pok else 'fail'} claim={pclaim} spk={pspk} ratio={pr}")

    print(f"\ndirect (control) passed {direct_pass}/{len(SEEDS)} ; inhib_pop (treatment) passed {pop_pass}/{len(SEEDS)}")
    print("KEEP RULE: dedicated inhibitory population kept?", "YES" if pop_pass > direct_pass else
          "NO -- not strictly more seeds than the control (recorded as is)")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["direct\n(control)", "inhib pop\n(exp11)"], [direct_pass, pop_pass], color=["tab:gray", "tab:purple"])
    ax.set_ylabel("seeds passing (of %d)" % len(SEEDS)); ax.set_ylim(0, len(SEEDS))
    ax.set_title("one-neuron-per-pattern AND claimed > 2x noise, seeds 1..8")
    for i, v in enumerate([direct_pass, pop_pass]):
        ax.text(i, v + 0.05, str(v), ha="center")
    plt.tight_layout(); plt.savefig("exp11_inhib_pop.png", dpi=110)
    print("saved exp11_inhib_pop.png")


if __name__ == "__main__":
    _driver()
