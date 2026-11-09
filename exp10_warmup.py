"""Experiment 10: warm up, then prune -- let the network learn under normalisation, THEN forget the un-consolidated
noise. The fix for exp9's cold start.

exp8 (uniform decay) and exp9 (activity-dependent decay) both collapsed: with forgetting on from t=0, synapses decay
before any LTP can build the consolidation that would protect them, and the network dies before it learns what to
keep. But exp9's ratio metric showed the normalise baseline already reaches ~1.9x on every seed -- a near-miss of
the 2x bar. So the plan: WARM UP under normalisation for the first WARMUP_S seconds (pattern weights grow and their
consolidation c builds via LTP), THEN switch to activity-dependent forgetting so the never-consolidated noise
erodes while the protected pattern survives, pushing ~1.9x past 2x. Consolidation c decays in BOTH phases (so it
reflects RECENT reinforcement), the weight-forgetting only acts after the warmup.

MECHANISM (treatment). Each synapse carries c in [0,1]: c += CINC on each LTP event, and c *= exp(-0.1/TAUC) every
100 ms (always). For t < WARMUP_S: weight-total normalisation (exp7). For t >= WARMUP_S: w *= (1 - LEAK*(1 - c))
every 100 ms, no normalisation -- full decay when c=0 (noise), none when c=1 (consolidated pattern). Params fixed
BEFORE the run, with reasons, not tuned: WARMUP_S=60 (half the run to learn), LEAK=0.05, TAUC=5 s, CINC=0.34
(same values as exp9; the ONLY new thing is the warmup gate).

CONTROL = normalisation throughout (exp7). TREATMENT = warmup-then-forget. Same eight seeds, corrected apparatus,
(a)+(b) bar UNCHANGED. KEEP RULE fixed before the run: warmup-forgetting kept IFF it passes (a AND b) on STRICTLY
MORE of the eight seeds than the control. Recorded as is.
Run:  .venv\\Scripts\\python.exe exp10_warmup.py      Out: exp10_warmup.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from brian2 import (network_operation, defaultclock, Hz, Network, NeuronGroup, PoissonGroup, SpikeGeneratorGroup,
                    SpikeMonitor, Synapses, ms, mV, prefs, second, seed as br_seed, start_scope)

prefs.codegen.target = "numpy"
N, K, DUR = 100, 3, 120 * second
GROUPS = [range(0, 20), range(20, 40), range(40, 60)]
SEEDS = list(range(1, 9))
WMAX = 2.0
WARMUP_S, LEAK, TAUC_S, CINC = 60.0, 0.05, 5.0, 0.34
CDECAY = float(np.exp(-0.1 / TAUC_S))


def run_once(s, mechanism):
    """One run at seed s. mechanism in {'normalise','warmup_forget'}. Returns (a_and_b, claimer, spikes, ratio)."""
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
        for syn in syns:                                  # c always decays, so it tracks RECENT reinforcement
            syn.c = np.clip(np.array(syn.c) * CDECAY, 0, 1)
        forgetting = (mechanism == "warmup_forget") and (float(defaultclock.t / second) >= WARMUP_S)
        if forgetting:
            for syn in syns:
                syn.w = np.clip(np.array(syn.w) * (1.0 - LEAK * (1.0 - np.array(syn.c))), 0, WMAX)
            return
        tot = np.zeros(K)                                 # normalise (control always; treatment during warmup)
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


print("exp10: warmup-then-forget vs normalise across seeds %s (bar and keep rule fixed before the run)\n" % SEEDS)
norm_pass, warm_pass = 0, 0
for s in SEEDS:
    nok, nclaim, nspk, nr = run_once(s, "normalise")
    wok, wclaim, wspk, wr = run_once(s, "warmup_forget")
    norm_pass += nok
    warm_pass += wok
    print(f"seed {s}: normalise {'PASS' if nok else 'fail'} claim={nclaim} spk={nspk} ratio={nr}  |  "
          f"warmup_forget {'PASS' if wok else 'fail'} claim={wclaim} spk={wspk} ratio={wr}")

print(f"\nnormalise (control) passed {norm_pass}/{len(SEEDS)} ; warmup_forget (treatment) passed {warm_pass}/{len(SEEDS)}")
print("KEEP RULE: warmup-then-forget kept?", "YES" if warm_pass > norm_pass else
      "NO -- not strictly more seeds than the control (recorded as is)")

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(["normalise\n(control)", "warmup+forget\n(exp10)"], [norm_pass, warm_pass], color=["tab:gray", "tab:olive"])
ax.set_ylabel("seeds passing (of %d)" % len(SEEDS)); ax.set_ylim(0, len(SEEDS))
ax.set_title("one-neuron-per-pattern AND claimed > 2x noise, seeds 1..8")
for i, v in enumerate([norm_pass, warm_pass]):
    ax.text(i, v + 0.05, str(v), ha="center")
plt.tight_layout(); plt.savefig("exp10_warmup.png", dpi=110)
print("saved exp10_warmup.png")
