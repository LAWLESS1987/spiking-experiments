"""Experiment 7: does an early blocked CURRICULUM fix "the third neuron never wins" -- measured against a control,
across seeds, not on one lucky run.

WHAT WE LEARNED THAT CHANGES THE TEST. exp5 run1, exp5 competing and exp6 normalised each failed the same way, and
each was ONE run at ONE seed (5). A single-seed result is an anecdote, not a measurement -- the covenant rule is
"one pattern is not evidence; count." So exp7 is not one run. It runs the exp6 design (the CONTROL) and the exp6
design + curriculum (the TREATMENT) across the SAME eight seeds (1..8) and counts how many each passes.

THE ONE DESIGN CHANGE (treatment vs control): the presentation schedule. For the first 30 s the three patterns are
shown one at a time in 2 s blocks, cycling 0,1,2 (15 blocks); after 30 s the random interleave of exp5/exp6.
Everything else -- STDP, winner-take-all lateral inhibition, the adaptive threshold, Diehl & Cook normalisation --
is exactly exp6, identical between the two arms. Control = curriculum off; treatment = curriculum on. Same seeds,
same everything else, so a difference is the curriculum.

PASS BAR per run -- UNCHANGED from exp5 and exp6, not moved:
  (a) each pattern group is claimed by a DIFFERENT output neuron, and
  (b) each neuron's mean weight on its claimed group is more than 2x its mean weight on the noise-only inputs.

KEEP RULE -- committed before the run: curriculum is kept as an improvement IFF it passes (a AND b) on STRICTLY
MORE of the eight seeds than the control does. A tie or worse is not kept. The result is recorded as is either way.
Run:  .venv\\Scripts\\python.exe exp7_curriculum.py      Out: exp7_curriculum.png
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
CURRICULUM_S, BLOCK_S = 30.0, 2.0


def run_once(s, curriculum):
    """One full run at seed s, curriculum on/off. Returns (a, b, claimer, spikes_per_neuron)."""
    start_scope()
    br_seed(s)
    rng = np.random.default_rng(s)

    noise = PoissonGroup(N, rates=5 * Hz)
    times, idx = [], []
    for t in np.arange(0.05, float(DUR / second), 0.25):
        g = (int(t / BLOCK_S) % K) if (curriculum and t < CURRICULUM_S) else rng.integers(K)
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
    # APPARATUS FIX (2026-10-20): both STDP synapses live in a list, so Brian2's magic run() collected only the
    # last one (pattern) and silently dropped the noise->out synapse ("synapses_1 ... never included in a network")
    # -- a bug present in exp5/exp6 too. Build the network EXPLICITLY so every object is simulated.
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
    spikes = [int((np.array(spk.i) == k).sum()) for k in range(K)]
    return bool(a and b), claimer.tolist(), spikes


print("exp7: curriculum vs control across seeds %s (pass bar and keep rule fixed before the run)\n" % SEEDS)
rows, ctrl_pass, curr_pass = [], 0, 0
for s in SEEDS:
    cok, cclaim, cspk = run_once(s, curriculum=False)
    kok, kclaim, kspk = run_once(s, curriculum=True)
    ctrl_pass += cok
    curr_pass += kok
    rows.append((s, cok, kok, cclaim, kclaim))
    print(f"seed {s}: control {'PASS' if cok else 'fail'} claim={cclaim} spk={cspk}  |  "
          f"curriculum {'PASS' if kok else 'fail'} claim={kclaim} spk={kspk}")

print(f"\ncontrol passed {ctrl_pass}/{len(SEEDS)} ; curriculum passed {curr_pass}/{len(SEEDS)}")
kept = curr_pass > ctrl_pass
print("KEEP RULE: curriculum kept as an improvement?" , "YES" if kept else
      "NO -- not strictly more seeds than the control (recorded as is)")

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(["control\n(exp6)", "curriculum\n(exp7)"], [ctrl_pass, curr_pass], color=["tab:gray", "tab:green"])
ax.set_ylabel("seeds passing (of %d)" % len(SEEDS)); ax.set_ylim(0, len(SEEDS))
ax.set_title("one-neuron-per-pattern + >2x-noise, across seeds 1..8")
for i, v in enumerate([ctrl_pass, curr_pass]):
    ax.text(i, v + 0.05, str(v), ha="center")
plt.tight_layout(); plt.savefig("exp7_curriculum.png", dpi=110)
print("saved exp7_curriculum.png")
