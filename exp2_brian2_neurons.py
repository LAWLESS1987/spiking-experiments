"""Experiment 2: biology-style spiking neurons in Brian2.

Ten leaky integrate-and-fire neurons each get a different steady input current. Weak input never reaches threshold;
stronger input fires faster. That rate-versus-input curve is the basic language spiking hardware computes in.

Run:  .venv\\Scripts\\python.exe exp2_brian2_neurons.py      Out: exp2_neurons.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from brian2 import NeuronGroup, SpikeMonitor, StateMonitor, ms, mV, prefs, run, start_scope

prefs.codegen.target = "numpy"     # pure Python: no C compiler needed on this PC
start_scope()
eqs = "dv/dt = (I - v) / (10*ms) : volt\nI : volt"
g = NeuronGroup(10, eqs, threshold="v > 15*mV", reset="v = 0*mV", method="exact")
g.I = [5 + 3 * i for i in range(10)] * mV          # 5 mV ... 32 mV of drive
spikes, trace = SpikeMonitor(g), StateMonitor(g, "v", record=[2, 9])
run(200 * ms)

rates = [len(spikes.spike_trains()[i]) / 0.2 for i in range(10)]
for i in range(10):
    print(f"neuron {i}: input {5 + 3 * i:2d} mV -> {rates[i]:5.0f} spikes per second")

fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
ax[0].plot(trace.t / ms, trace.v[0] / mV, label="neuron 2 (weak input)")
ax[0].plot(trace.t / ms, trace.v[1] / mV, label="neuron 9 (strong input)")
ax[0].axhline(15, ls="--", c="gray"); ax[0].set_xlabel("time (ms)"); ax[0].set_ylabel("membrane voltage (mV)")
ax[0].set_title("charge builds, crosses threshold, spikes, resets"); ax[0].legend()
ax[1].plot([5 + 3 * i for i in range(10)], rates, "o-")
ax[1].set_xlabel("input (mV)"); ax[1].set_ylabel("spikes per second"); ax[1].set_title("stronger input, faster firing")
plt.tight_layout(); plt.savefig("exp2_neurons.png", dpi=110)
print("saved exp2_neurons.png")
