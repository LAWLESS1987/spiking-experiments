---
license: apache-2.0
pretty_name: Spiking Neural Network Experiments
tags:
  - spiking-neural-networks
  - snntorch
  - brian2
  - neuromorphic
  - mnist
---

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

## Auditability baseline

```
python -I research_grade.py      # standard library only; exit 0 only if every check holds
```

One portable file shared across these repositories. It drives each of its checks red and green on a synthetic case,
then checks this repository and prints what it examined:

- **Claims** (`docs/CLAIMS_INDEX.json`): each result above, the exact sentence where it stands and the script that
  reproduces it. All six are `custodian-run`: the author ran the shipped, seeded scripts. CI does not, because they
  need PyTorch, snnTorch and Brian2; it only checks that every script parses. Only run 3 of exp3 has its figures in a
  shipped log (`controls/exp3_ctrl_sync_seed1.out`).
- **Retractions** (`docs/RETRACTED.json`): empty. Nothing has been withdrawn; the nulls and failures are reported,
  not retracted.
- **Manifest** (`MANIFEST.sha256`): every tracked file pinned by sha256 (text LF-normalized, images raw).

Passing means the results are auditable, not that they are true or that a rerun will match to the last digit.


---

## Part of one system — each piece usable on its own

These repositories are independent instruments that also compose into a single apparatus for **building and honestly auditing trustworthy multi-intelligence systems**. Any one can be used standalone; together they form the stack:

- **Governed core** — [covenant](https://huggingface.co/Lawless1987/covenant): a self-governing multi-agent system with an ethics gate inside the transaction path.
- **Observability & provenance** — [threefold](https://huggingface.co/Lawless1987/threefold) (the L-lens layer over Jacobian Lens) and [threefold-memory](https://huggingface.co/Lawless1987/threefold-memory) (its persistent, provenance-tracked memory): every action measured and recorded under one task identity.
- **Measurement instruments** — [contradiction-probe](https://huggingface.co/Lawless1987/contradiction-probe) and [flinch-observability](https://huggingface.co/Lawless1987/flinch-observability), with the session records [flinch-record](https://huggingface.co/Lawless1987/flinch-record) and [grokflinch](https://huggingface.co/Lawless1987/grokflinch): preregistered, blind-scored tests of AI behaviour that embody the covenant's rule — *investigate a signal, never convict on one*.
- **Neuromorphic research** — [spiking-experiments](https://huggingface.co/Lawless1987/spiking-experiments): from-scratch spiking-network experiments with the pass/fail bar declared before each run.
- **Ledger surface** — [Sentinel-Witness](https://huggingface.co/Lawless1987/Sentinel-Witness): the trading / ledger dashboard.

**This repository's place in it:** the neuromorphic research lab behind the covenant's stdlib spiking reflexes.
