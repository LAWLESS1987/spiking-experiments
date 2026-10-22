"""Review control for exp3_stdp.py (Conscious Ledger review, 2026-10-19). Same network, rule and readout as exp3 run 3
(5 mV, 120 s), with two modes:
  sync  -- the original hidden pattern (inputs 0-19 burst together every 250 ms, 2 ms jitter);
  async -- RATE-MATCHED control: the same number of extra spikes per pattern input, at independent uniform times.
It also reports the two pathways separately (the pattern pathway of inputs 20-99 never spikes).
Run:  python exp3_ctrl.py sync|async <seed>   (results: exp3_ctrl_<mode>_seed<N>.out)
"""
import sys
import numpy as np
from brian2 import (Hz, NeuronGroup, PoissonGroup, SpikeGeneratorGroup, SpikeMonitor, Synapses, ms, mV, prefs, run, second, seed, start_scope)
mode, sd = sys.argv[1], int(sys.argv[2])
prefs.codegen.target = "numpy"; start_scope(); seed(sd); rng = np.random.default_rng(sd)
N, GROUP, DUR = 100, 20, 120 * second
noise = PoissonGroup(N, rates=5 * Hz)
times, idx = [], []
for t in np.arange(0.05, float(DUR / second), 0.25):
    for i in range(GROUP):
        tt = t + rng.normal(0, 0.002) if mode == "sync" else rng.uniform(0.0, float(DUR/second))
        times.append(tt); idx.append(i)
times=np.array(times); idx=np.array(idx)
# drop exact-duplicate (idx,time-bin) (SpikeGeneratorGroup rejects duplicates)
order = np.argsort(times); times, idx = times[order], idx[order]
key = set(); keep=[]
for k,(i,t) in enumerate(zip(idx, times)):
    b=(i,int(t/1e-4))
    if b in key: continue
    key.add(b); keep.append(k)
pattern = SpikeGeneratorGroup(N, idx[keep], times[keep] * second)
out = NeuronGroup(1, "dv/dt = -v / (10*ms) : volt", threshold="v > 5*mV", reset="v = 0*mV", method="exact")
taupre = taupost = 20 * ms; wmax, Apre = 2.0, 0.01; Apost = -Apre * 1.05
stdp = """w : 1
          dapre/dt = -apre / taupre : 1 (event-driven)
          dapost/dt = -apost / taupost : 1 (event-driven)"""
on_pre = """v_post += w * mV
            apre += Apre
            w = clip(w + apost, 0, wmax)"""
on_post = """apost += Apost
             w = clip(w + apre, 0, wmax)"""
sn = Synapses(noise, out, stdp, on_pre=on_pre, on_post=on_post); sp = Synapses(pattern, out, stdp, on_pre=on_pre, on_post=on_post)
for s in (sn, sp): s.connect(); s.w = "rand() * 0.6"
w0p = np.array(sp.w).copy()
spk = SpikeMonitor(out); run(DUR)
wn, wp = np.array(sn.w), np.array(sp.w); w = wn + wp
g, r = w[:GROUP].mean(), w[GROUP:].mean()
print(f"mode={mode} seed={sd} out_spikes={spk.num_spikes} group={g:.2f} rest={r:.2f} ratio={g/r:.2f} | rest noise-path={wn[GROUP:].mean():.2f} rest pattern-path(never spikes)={wp[GROUP:].mean():.2f} unchanged={np.allclose(wp[GROUP:],w0p[GROUP:])} | ratio noise-path only={wn[:GROUP].mean()/wn[GROUP:].mean():.2f}")
