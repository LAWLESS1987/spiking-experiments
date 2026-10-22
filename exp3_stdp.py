"""Experiment 3: learning from spike TIMING (STDP), with no labels and no backpropagation.

Spike-timing-dependent plasticity is the learning rule neuromorphic chips can run on-chip:
  - if an input spike arrives just BEFORE the neuron fires, that connection is strengthened (it helped cause the spike);
  - if it arrives just AFTER, the connection is weakened.

Setup: 100 input neurons fire at random. Inputs 0-19 are a hidden "pattern group": now and then all 20 fire together.
One output neuron listens to all 100 and learns by STDP alone. Nothing tells it which inputs matter.
If STDP works, the pattern group's connections grow and the rest shrink.

Run 1 (kept as exp3_stdp_run1_null.py) used a 10 mV threshold: a 20-spike burst gives ~6 mV, so the output never
fired and STDP had nothing to learn from. This run uses 5 mV: a burst fires it, background noise (~1.5 mV) does not.

Run:  .venv\\Scripts\\python.exe exp3_stdp.py      Out: exp3_stdp.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from brian2 import (Hz, NeuronGroup, PoissonGroup, SpikeGeneratorGroup, SpikeMonitor, StateMonitor, Synapses, ms,
                    mV, prefs, run, second, seed, start_scope)

prefs.codegen.target = "numpy"
start_scope()
seed(1)
rng = np.random.default_rng(1)
N, GROUP, DUR = 100, 20, 120 * second   # run 3: declared before running, the only change from run 2 (30 s)

# Background noise: every input fires at random, 5 spikes per second.
noise = PoissonGroup(N, rates=5 * Hz)
# The hidden pattern: inputs 0-19 fire together about 4 times per second, with a little jitter.
times, idx = [], []
for t in np.arange(0.05, float(DUR / second), 0.25):
    for i in range(GROUP):
        times.append(t + rng.normal(0, 0.002))
        idx.append(i)
order = np.argsort(times)
pattern = SpikeGeneratorGroup(N, np.array(idx)[order], np.array(times)[order] * second)

out = NeuronGroup(1, "dv/dt = -v / (10*ms) : volt", threshold="v > 5*mV", reset="v = 0*mV", method="exact")

taupre = taupost = 20 * ms
wmax, Apre = 2.0, 0.01
Apost = -Apre * 1.05                       # slightly more weakening than strengthening keeps weights in check
stdp = """w : 1
          dapre/dt = -apre / taupre : 1 (event-driven)
          dapost/dt = -apost / taupost : 1 (event-driven)"""
on_pre = """v_post += w * mV
            apre += Apre
            w = clip(w + apost, 0, wmax)"""
on_post = """apost += Apost
             w = clip(w + apre, 0, wmax)"""
syn_noise = Synapses(noise, out, stdp, on_pre=on_pre, on_post=on_post)
syn_pat = Synapses(pattern, out, stdp, on_pre=on_pre, on_post=on_post)
for s in (syn_noise, syn_pat):
    s.connect()
    s.w = "rand() * 0.6"                   # everyone starts with small random weights
start_w = np.array(syn_noise.w) + np.array(syn_pat.w)   # both pathways, as at the end
wmon = StateMonitor(syn_noise, "w", record=True, dt=500 * ms)
wmon_p = StateMonitor(syn_pat, "w", record=True, dt=500 * ms)
spk = SpikeMonitor(out)
run(DUR)

# Each input has two pathways (its noise spikes and its pattern spikes); its total weight is their sum.
w_end = np.array(syn_noise.w) + np.array(syn_pat.w)
grp, rest = w_end[:GROUP].mean(), w_end[GROUP:].mean()
print(f"output spikes: {spk.num_spikes}")
print(f"average weight at the start:            {start_w.mean():.2f} (all inputs alike)")
print(f"average weight now, pattern inputs 0-19: {grp:.2f}")
print(f"average weight now, other inputs 20-99:  {rest:.2f}")
print("STDP found the hidden group" if grp > 2 * rest else "STDP did NOT separate the group on this run")

fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].bar(range(N), w_end, color=["tab:orange"] * GROUP + ["tab:gray"] * (N - GROUP))
ax[0].set_title("learned weight per input (orange = hidden pattern group)")
ax[0].set_xlabel("input neuron"); ax[0].set_ylabel("weight")
tw = wmon.t / second
total = wmon.w + wmon_p.w
ax[1].plot(tw, total[:GROUP].mean(0), c="tab:orange", label="pattern group 0-19")
ax[1].plot(tw, total[GROUP:].mean(0), c="tab:gray", label="other inputs")
ax[1].set_xlabel("time (s)"); ax[1].set_ylabel("average weight"); ax[1].legend()
ax[1].set_title("learning over time, from spike timing alone")
plt.tight_layout(); plt.savefig("exp3_stdp.png", dpi=110)
print("saved exp3_stdp.png")
