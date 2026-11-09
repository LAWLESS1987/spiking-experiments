"""Experiment 9: fix (b) by forgetting the NOISE but KEEPING the pattern -- activity-dependent decay (true ASP).

WHY exp8 failed and this is the fix, not a tweak. exp8 decayed every synapse uniformly, so it erased the pattern
weights along with the noise and the network went silent. The ratio diagnosis still holds (homeostasis is
ratio-preserving; the rule must change), but the decay has to DISTINGUISH reinforced from unreinforced synapses.
ASP (Panda et al., arXiv 1703.07655) does exactly that: a synapse carries a slow "consolidation" that rises when it
is potentiated and fades over seconds, and its forgetting rate is scaled DOWN by that consolidation. A noise synapse
(rarely potentiated) stays unconsolidated and decays; a pattern synapse (potentiated each time its group wins)
stays consolidated and resists decay. So the pattern survives and the noise forgets -- the ratio grows without
silencing the neuron.

MECHANISM. Each plastic synapse has c in [0,1]. On each LTP event (post-spike) c += CINC (clipped at 1). Every
100 ms c decays by factor exp(-0.1/TAUC) and the weight is forgotten by w *= (1 - LEAK*(1 - c)): fully (LEAK) when
c=0, not at all when c=1. Fixed BEFORE the run, with reasons, not tuned: LEAK=0.05 (unconsolidated half-life ~1.4 s,
aggressive on noise), TAUC=5 s (a synapse potentiated in the last few seconds stays protected), CINC=0.34 (about
three LTP events saturate c, so a winning pattern synapse is quickly protected).

CONTROL vs TREATMENT, same eight seeds (1..8), corrected apparatus (explicit Network, both STDP synapses). ONLY
difference: control = weight-total normalisation (exp7); treatment = activity-dependent forgetting (this).
PASS BAR per run UNCHANGED: (a) each pattern claimed by a DIFFERENT neuron; (b) claimed-group mean weight > 2x the
noise-only mean weight. KEEP RULE fixed before the run: consolidation-forgetting kept IFF it passes (a AND b) on
STRICTLY MORE of the eight seeds than the control. Recorded as is.
Run:  .venv\\Scripts\\python.exe exp9_consolidate.py      Out: exp9_consolidate.png
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
LEAK, TAUC_S, CINC = 0.05, 5.0, 0.34                 # treatment params, fixed before the run
CDECAY = float(np.exp(-0.1 / TAUC_S))                # consolidation decay per 100 ms homeostasis step


def run_once(s, mechanism):
    """One run at seed s. mechanism in {'normalise','consolidate'}. Returns (a_and_b, claimer, spikes)."""
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
              c : 1
              dapre/dt = -apre / taupre : 1 (event-driven)
              dapost/dt = -apost / taupost : 1 (event-driven)"""
    on_pre = "v_post += w * mV\napre += Apre\nw = clip(w + apost, 0, WMAX)"
    on_post = "apost += Apost\nw = clip(w + apre, 0, WMAX)\nc = clip(c + CINC, 0, 1)"
    syns = []
    for src in (noise, pattern):
        syn = Synapses(src, out, stdp, on_pre=on_pre, on_post=on_post, namespace={"CINC": CINC, "WMAX": WMAX})
        syn.connect()
        syn.w = "rand() * 0.6"
        syn.c = 0.0
        syns.append(syn)

    state = {"targets": None}

    @network_operation(dt=100 * ms)
    def homeostasis():
        if mechanism == "consolidate":
            for syn in syns:
                c = np.clip(np.array(syn.c) * CDECAY, 0, 1)
                syn.c = c
                syn.w = np.clip(np.array(syn.w) * (1.0 - LEAK * (1.0 - c)), 0, WMAX)
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
    ratio = float(np.mean([mean_on[claimer[g], g] / max(noise_w[claimer[g]], 1e-9) for g in range(K)]))
    return bool(a and b), claimer.tolist(), [int((np.array(spk.i) == k).sum()) for k in range(K)], round(ratio, 2)


print("exp9: activity-dependent forgetting vs normalise across seeds %s (bar and keep rule fixed before the run)\n" % SEEDS)
norm_pass, cons_pass = 0, 0
for s in SEEDS:
    nok, nclaim, nspk, nr = run_once(s, "normalise")
    cok, cclaim, cspk, cr = run_once(s, "consolidate")
    norm_pass += nok
    cons_pass += cok
    print(f"seed {s}: normalise {'PASS' if nok else 'fail'} claim={nclaim} spk={nspk} ratio={nr}  |  "
          f"consolidate {'PASS' if cok else 'fail'} claim={cclaim} spk={cspk} ratio={cr}")

print(f"\nnormalise (control) passed {norm_pass}/{len(SEEDS)} ; consolidate (treatment) passed {cons_pass}/{len(SEEDS)}")
print("KEEP RULE: activity-dependent forgetting kept?", "YES" if cons_pass > norm_pass else
      "NO -- not strictly more seeds than the control (recorded as is)")

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(["normalise\n(control)", "consolidate\n(exp9)"], [norm_pass, cons_pass], color=["tab:gray", "tab:red"])
ax.set_ylabel("seeds passing (of %d)" % len(SEEDS)); ax.set_ylim(0, len(SEEDS))
ax.set_title("one-neuron-per-pattern AND claimed > 2x noise, seeds 1..8")
for i, v in enumerate([norm_pass, cons_pass]):
    ax.text(i, v + 0.05, str(v), ha="center")
plt.tight_layout(); plt.savefig("exp9_consolidate.png", dpi=110)
print("saved exp9_consolidate.png")
