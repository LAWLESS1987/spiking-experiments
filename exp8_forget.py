"""Experiment 8: fix (b), weak separation from noise, by LETTING UNREINFORCED SYNAPSES FORGET.

THE REASONING, which is why this is not another homeostasis tweak. (b) asks that a neuron's mean weight on its
claimed pattern be more than 2x its mean weight on the noise-only inputs -- a RATIO. Weight-total normalisation
(exp6/exp7) and firing-rate scaling are MULTIPLICATIVE: they rescale all of a neuron's weights by one factor, so
they cannot change that ratio. The ratio is set by the plasticity rule alone. So iterating on homeostasis could
never fix (b). exp5->6->7 confirmed it: on the corrected apparatus (a) now holds across seeds, but (b) failed 0/8.

The literature fix that targets the ratio: ASP, "Learning to Forget with Adaptive Synaptic Plasticity"
(Panda et al., arXiv 1703.07655). Unreinforced synapses slowly decay toward zero. Noise synapses (rarely co-active
with the neuron's pattern-driven spikes) forget; pattern synapses (reinforced by STDP every time their group
fires) survive -- so the pattern-to-noise ratio grows. That is a change in the LEARNING RULE, where (b) lives.

CONTROL vs TREATMENT, same eight seeds (1..8), on the corrected apparatus (explicit Network -- both STDP synapses
simulated). The ONLY difference is the homeostatic/selectivity mechanism:
  control   ("normalise"): every 100 ms rescale each neuron's incoming weights so the total stays at its start
                            (exp6/exp7 -- the ratio-preserving one).
  treatment ("forget"):    every 100 ms multiply every plastic weight by (1 - LEAK), LEAK = 0.02, clipped to
                            [0, wmax]. No total-normalisation. Unreinforced weights decay; reinforced ones persist.
LEAK = 0.02 per 100 ms is fixed BEFORE the run (half-life ~3.5 s; a pattern group recurs ~every 0.75 s, so pattern
synapses out-run the decay and noise synapses do not). Not tuned to pass.

PASS BAR per run -- UNCHANGED from exp5-7: (a) each pattern claimed by a DIFFERENT neuron; (b) each neuron's mean
weight on its claimed group > 2x its mean weight on the noise-only inputs.
KEEP RULE -- fixed before the run: forgetting is kept as an improvement IFF it passes (a AND b) on STRICTLY MORE
of the eight seeds than the normalisation control. A tie or worse is not kept. Recorded as is.
Run:  .venv\\Scripts\\python.exe exp8_forget.py      Out: exp8_forget.png
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
LEAK = 0.02                                          # treatment: fraction forgotten per 100 ms, fixed before the run


def run_once(s, mechanism):
    """One run at seed s. mechanism in {'normalise','forget'}. Returns (a_and_b, claimer, spikes)."""
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
    inhib = Synapses(out, out, on_pre="v_post = clip(v_post - 6*mV, -6*mV, 100*mV)")
    inhib.connect(condition="i != j")

    taupre = taupost = 20 * ms
    Apre = 0.01
    Apost = -Apre * 1.05
    stdp = """w : 1
              dapre/dt = -apre / taupre : 1 (event-driven)
              dapost/dt = -apost / taupost : 1 (event-driven)"""
    on_pre = "v_post += w * mV\napre += Apre\nw = clip(w + apost, 0, WMAX)"
    on_post = "apost += Apost\nw = clip(w + apre, 0, WMAX)"
    syns = []
    for src in (noise, pattern):
        syn = Synapses(src, out, stdp, on_pre=on_pre, on_post=on_post)
        syn.connect()
        syn.w = "rand() * 0.6"
        syns.append(syn)

    state = {"targets": None}

    @network_operation(dt=100 * ms)
    def homeostasis():
        if mechanism == "forget":
            for syn in syns:
                syn.w = np.clip(np.array(syn.w) * (1.0 - LEAK), 0, WMAX)
            return
        tot = np.zeros(K)                             # mechanism == "normalise"
        for syn in syns:
            np.add.at(tot, np.array(syn.j), np.array(syn.w))
        if state["targets"] is None:
            state["targets"] = tot.copy()
            return
        for syn in syns:
            j = np.array(syn.j)
            syn.w = np.array(syn.w) * (state["targets"][j] / np.maximum(tot[j], 1e-9))

    spk = SpikeMonitor(out)
    net = Network(noise, pattern, out, inhib, syns[0], syns[1], spk, homeostasis)
    net.run(DUR)

    W = np.zeros((K, N))
    for syn in syns:
        W[np.array(syn.j), np.array(syn.i)] += np.array(syn.w)
    mean_on = np.array([[W[k, list(g)].mean() for g in GROUPS] for k in range(K)])
    noise_w = W[:, 60:].mean(1)
    claimer = mean_on.argmax(0)
    a = len(set(claimer.tolist())) == K
    b = all(mean_on[claimer[g], g] > 2 * noise_w[claimer[g]] for g in range(K))
    return bool(a and b), claimer.tolist(), [int((np.array(spk.i) == k).sum()) for k in range(K)]


print("exp8: forget vs normalise across seeds %s (bar and keep rule fixed before the run)\n" % SEEDS)
norm_pass, forget_pass = 0, 0
for s in SEEDS:
    nok, nclaim, nspk = run_once(s, "normalise")
    fok, fclaim, fspk = run_once(s, "forget")
    norm_pass += nok
    forget_pass += fok
    print(f"seed {s}: normalise {'PASS' if nok else 'fail'} claim={nclaim} spk={nspk}  |  "
          f"forget {'PASS' if fok else 'fail'} claim={fclaim} spk={fspk}")

print(f"\nnormalise (control) passed {norm_pass}/{len(SEEDS)} ; forget (treatment) passed {forget_pass}/{len(SEEDS)}")
print("KEEP RULE: forgetting kept as an improvement?", "YES" if forget_pass > norm_pass else
      "NO -- not strictly more seeds than the control (recorded as is)")

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(["normalise\n(control)", "forget\n(exp8)"], [norm_pass, forget_pass], color=["tab:gray", "tab:blue"])
ax.set_ylabel("seeds passing (of %d)" % len(SEEDS)); ax.set_ylim(0, len(SEEDS))
ax.set_title("one-neuron-per-pattern AND claimed > 2x noise, seeds 1..8")
for i, v in enumerate([norm_pass, forget_pass]):
    ax.text(i, v + 0.05, str(v), ha="center")
plt.tight_layout(); plt.savefig("exp8_forget.png", dpi=110)
print("saved exp8_forget.png")
