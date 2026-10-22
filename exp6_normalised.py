"""Experiment 6 (redesign of exp5): three neurons COMPETE to learn three hidden patterns (STDP + winner-take-all), no labels.

Inputs: 100 neurons firing at random. Three hidden groups (0-19, 20-39, 40-59) each burst together, one group at a
time, picked at random every 250 ms. Inputs 60-99 are noise only.
Outputs: 3 neurons, each connected to all 100 inputs, learning by STDP.
  - Lateral inhibition: when one output fires, it pushes the others down (winner takes all).
  - Adaptive threshold: each time a neuron fires, its threshold rises a little and then slowly relaxes, so one neuron
    cannot claim every pattern.

THE ONE DESIGN CHANGE from exp5 run 1: per-neuron weight normalisation (Diehl & Cook 2015). Every 100 ms each
output neuron's incoming weights are rescaled so their total stays at its starting value. Strengthening one pattern
must weaken others, so no neuron can grow strong on everything. Everything else is exp5 run 1.

PASS BAR, the same as exp5, written before the first run:
  (a) each pattern group is claimed by a DIFFERENT output neuron (the neuron with the highest mean weight on it), and
  (b) for each neuron, its mean weight on its claimed group is more than 2x its mean weight on the noise-only inputs.
Run:  .venv\\Scripts\\python.exe exp6_normalised.py      Out: exp6_normalised.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from brian2 import (network_operation, Hz, NeuronGroup, PoissonGroup, SpikeGeneratorGroup, SpikeMonitor, Synapses, ms, mV, prefs, run,
                    second, seed, start_scope)

prefs.codegen.target = "numpy"
start_scope()
seed(5)
rng = np.random.default_rng(5)
N, G, K, DUR = 100, 20, 3, 120 * second
groups = [range(0, 20), range(20, 40), range(40, 60)]

noise = PoissonGroup(N, rates=5 * Hz)
times, idx = [], []
for t in np.arange(0.05, float(DUR / second), 0.25):
    g = rng.integers(K)
    for i in groups[g]:
        times.append(t + rng.normal(0, 0.002)); idx.append(i)
order = np.argsort(times)
pattern = SpikeGeneratorGroup(N, np.array(idx)[order], np.array(times)[order] * second)

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
on_pre = """v_post += w * mV
            apre += Apre
            w = clip(w + apost, 0, wmax)"""
on_post = """apost += Apost
             w = clip(w + apre, 0, wmax)"""
syns = []
for src in (noise, pattern):
    s = Synapses(src, out, stdp, on_pre=on_pre, on_post=on_post)
    s.connect()
    s.w = "rand() * 0.6"
    syns.append(s)
targets = None


@network_operation(dt=100 * ms)
def normalise():
    global targets
    tot = np.zeros(K)
    for s in syns:
        np.add.at(tot, np.array(s.j), np.array(s.w))
    if targets is None:
        targets = tot.copy()                 # each neuron keeps its starting total
        return
    for s in syns:
        j = np.array(s.j)
        s.w = np.array(s.w) * (targets[j] / np.maximum(tot[j], 1e-9))


spk = SpikeMonitor(out)
run(DUR)

W = np.zeros((K, N))
for s in syns:
    W[np.array(s.j), np.array(s.i)] += np.array(s.w)
mean_on = np.array([[W[k, list(g)].mean() for g in groups] for k in range(K)])   # neuron x group
noise_w = W[:, 60:].mean(1)
claimer = mean_on.argmax(0)                                                       # which neuron claims each group
print("output spikes per neuron:", [int((np.array(spk.i) == k).sum()) for k in range(K)])
for gi in range(K):
    print(f"group {gi} ({groups[gi].start}-{groups[gi].stop - 1}): claimed by neuron {claimer[gi]}; "
          f"mean weights by neuron {np.round(mean_on[:, gi], 2).tolist()}")
print("noise-only inputs, mean weight by neuron:", np.round(noise_w, 2).tolist())
a = len(set(claimer.tolist())) == K
b = all(mean_on[claimer[g], g] > 2 * noise_w[claimer[g]] for g in range(K))
print(f"(a) one neuron per pattern: {'MET' if a else 'NOT MET'}   (b) claimed group > 2x noise: {'MET' if b else 'NOT MET'}")
print("PASS" if a and b else "NOT PASSED -- recorded as is")

fig, ax = plt.subplots(1, K, figsize=(14, 3.6), sharey=True)
colors = ["tab:orange", "tab:green", "tab:purple"]
for k in range(K):
    c = ["tab:gray"] * N
    for gi, g in enumerate(groups):
        for i in g:
            c[i] = colors[gi]
    ax[k].bar(range(N), W[k], color=c)
    ax[k].set_title(f"output neuron {k}: learned weights"); ax[k].set_xlabel("input neuron")
ax[0].set_ylabel("weight")
plt.tight_layout(); plt.savefig("exp6_normalised.png", dpi=110)
print("saved exp6_normalised.png")
