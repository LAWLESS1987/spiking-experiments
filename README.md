# Spiking neural network experiments

A small set of from-scratch spiking-neural-network experiments that run on a laptop CPU —
no special hardware. Each one was written with its **pass/fail bar declared before it ran**,
every run is kept (including the nulls and the failures), and the conclusions are reported as
measured, not as hoped.

## Setup

- snnTorch 1.0.0, PyTorch 2.14.1 (CPU), Brian2 2.10.1 — all open-source. Exact pins in
  `requirements.txt`.

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# or: .venv/bin/python -m pip install -r requirements.txt      # Linux/macOS
```

Run any experiment with that interpreter, e.g. `.venv/Scripts/python.exe exp1_mnist_snn.py`.

## Experiments

| File | What it shows | Result |
|---|---|---|
| `exp1_mnist_snn.py` | A 2-layer spiking network learns handwritten digits; information moves only as spikes over 25 time steps. | 9.0% before training (chance) → **91.2%** after 2 short passes, in 19 s. 9.1% of hidden neuron-steps spiked. (`exp1_spikes.png`) |
| `exp2_brian2_neurons.py` | Ten biology-style LIF neurons with rising input: below the 15 mV threshold none fire; above it the rate climbs. | 0 spikes/s at 5–14 mV; 45→155 spikes/s at 17–32 mV. (`exp2_neurons.png`) |
| `exp3_stdp.py` | Unsupervised learning from spike **timing** (STDP). One output neuron listens to 100 inputs, 20 of which secretly fire together. | Bar (pattern group > 2× the rest) set before running. See the three runs below. (`exp3_stdp.png`) |
| `exp5_competing_neurons.py` | Three neurons compete (STDP + winner-take-all) to each claim one of three hidden patterns. | **Not passed** — see below. |
| `exp6_normalised.py` | The exp5 redesign: per-neuron weight normalisation (Diehl & Cook 2015). | **Not passed** — see below. |

### exp3, every run kept
- **Run 1** (`exp3_stdp_run1_null.py`, 10 mV, 30 s): **null** — the output neuron never fired
  (a 20-spike burst gives ~6 mV), so STDP had nothing to learn from.
- **Run 2** (`exp3_stdp_run2_30s.py`, 5 mV, 30 s): pattern group 0.58→0.84, rest 0.58→0.59 —
  ratio 1.42×. **The 2× bar was not met.**
- **Run 3** (`exp3_stdp.py`, 120 s, declared beforehand as the only change): pattern 1.76, rest
  0.56 — **3.1×. Met.** The neuron found the hidden group from spike timing alone.

`controls/` holds the exp3 control runs (sync vs async inputs, three seeds each) used to check
the effect was real and not an artifact.

### exp5 / exp6, honest failure
Three designs were tried against the three-pattern competition; all three hit the **same
failure shape** — a "dead" third neuron that never gets the early wins it needs, so one pattern
stays unclaimed (exp5 run 1 and the +3 mV tweak, exp6 with weight normalisation). Each bar was
committed before its run; tuning was stopped rather than searched until it passed. Unrun next
ideas: present each pattern alone in early blocks, or give each neuron a different starting bias.

## Method notes

Bars before runs, nulls and failures kept beside the successes, controls where an effect is
claimed. The aim is a record you can check, not a highlight reel.
