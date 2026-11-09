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
no special hardware. Every learning experiment (exp3, exp5-exp12) had its pass/fail bar set before
it ran; exp1 and exp2 are demonstrations with no bar (corrected 2026-11-09, SE-R2 in Corrections below).
Nulls and failures are kept beside the successes, and the conclusions are reported as measured, not
as hoped.

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
| `exp5_competing_neurons.py` | Three neurons compete (STDP + winner-take-all) to each claim one of three hidden patterns. | **Not passed** — see below. Its code has a synapse bug found in exp7 (SE-R1). |
| `exp6_normalised.py` | The exp5 redesign: per-neuron weight normalisation (Diehl & Cook 2015). | **Not passed** — see below. Same bug (SE-R1). |
| `exp7_curriculum.py` | exp6 against exp6 plus an early blocked curriculum, seeds 1-8, on corrected code. | Control **0/8**, curriculum **0/8**: not kept. One neuron per pattern now holds on most seeds; no seed clears 2× noise. (`exp7_curriculum.png`) |
| `exp8_forget.py` | Uniform forgetting of plastic weights in place of normalisation. | Normalise **0/8**, forget **0/8**: forgetting overshot and silenced the network. (`exp8_forget.png`) |
| `exp9_consolidate.py` | Forgetting that spares recently reinforced synapses. | Normalise **0/8**, consolidate **0/8**: a cold start silenced it; normalisation sits near 1.9×. (`exp9_consolidate.png`) |
| `exp10_warmup.py` | 60 s of normalisation, then consolidated forgetting. | Normalise **0/8**, warmup-forget **0/8**: the network stayed alive but selectivity collapsed. (`exp10_warmup.png`) |
| `exp11_inhib_pop.py` | A dedicated inhibitory population (Diehl & Cook). | Direct **0/8**, inhibitory population **0/8**; per-seed ratios within 0.08 of each other (`exp11_out.txt`). |
| `exp12_mahowald_wta.py` | A single global inhibitory node (Mahowald's O(N) winner-take-all). | Direct **0/8**, global node **0/8**; per-seed ratios within 0.08 of each other (`exp12_out.txt`). |
| `exp14_shuffled_null.py` | A null asked for on the HF forum: same bursts, but each fires 20 random inputs from 0-59. | Ratio 1.64 against 1.84; pre-registered reading "mostly by construction". (`exp14_out.txt`) |
| `exp15_desync_null.py` | The null as worded: burst spikes keep their input and count, at independent random times. | Ratio 1.07; outputs nearly silent (0-9 spikes), so its "pattern learning" verdict is set aside. (`exp15_out.txt`) |
| `exp16_rescore.py` | Reruns all three conditions saving weights at t = 0 and at the end (measurement only). | The score is 1.07 before any learning; the rise is in the burst synapses. (`exp16_out.txt`) |
| `exp17_selectivity_new_seeds.py` | Burst-synapse selectivity, pre-registered on new seeds 9-16. | **PASS**: >= 2.0 on 7/8, above start 8/8, above a 1000-relabeling null 8/8. (`exp17_out.txt`) |

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

**Corrected 2026-10-20 by exp7; recorded here 2026-11-09 (SE-R1).** The paragraph above is kept as written. It
describes one seed (5) on code with a bug: exp5 and exp6 keep both STDP `Synapses` in a Python list, so Brian2's
magic `run()` did not collect the noise→output synapses, and warned "never included in a network" on every run.
Built as an explicit network (exp7), every neuron fires (seed 1: 118/162/165 spikes, against 15/106/51 before), and
one neuron per pattern holds on most of eight seeds. The open problem is the second condition: no seed's claimed
weight reaches 2× the noise weight. exp5 and exp6 are left as written, bug included. exp3 is unaffected: its two
synapse groups are named variables.

### exp7-exp12: the competition on corrected code, eight seeds (2026-10-20)

From the lab's record, as written at the time. Each plan, bar and keep rule was committed to git before its run.

**Exp 7 PLAN (`exp7_curriculum.py`), committed before the run.** What changed is not just the idea but the test.
exp5/exp6 were each ONE run at ONE seed (5); a single-seed failure is an anecdote, not a measurement. So exp7 is a
CONTROLLED, MULTI-SEED comparison: the exp6 design (control) and the exp6 design + an early blocked curriculum
(treatment) across the SAME eight seeds, 1..8. The curriculum: for the first 30 s the three patterns are shown one
at a time in 2 s blocks cycling 0,1,2; after 30 s the random interleave. That schedule is the ONLY difference
between the two arms -- STDP, lateral inhibition, the adaptive threshold and Diehl & Cook normalisation are
identical. Per-run pass bar UNCHANGED (one neuron per pattern; claimed group > 2x noise). KEEP RULE, fixed before
the run: curriculum is kept as an improvement IFF it passes on STRICTLY MORE of the eight seeds than the control.
A tie or worse is not kept. Recorded as is below once it has run.

**Exp 7 RESULT (2026-10-20): a null, and a bug the multi-seed run surfaced.** Recorded as is; the pre-registered
bar and keep rule were not moved.
- **Apparatus bug in exp5/exp6/exp7, found here.** Both STDP synapse populations (noise->out and pattern->out)
  were stored in a list, so Brian2's magic `run()` collected only the last and silently dropped **noise->out**
  ("synapses_1 ... never included in a network", warned on every run). exp5 and exp6 share the code and the bug.
  Fixed in exp7 by building the network EXPLICITLY. With the fix every neuron fires (seed 1: 118/162/165 spikes,
  against 15/106/51 before); the "dead third neuron" was largely the missing synapse plus the single seed 5.
- **Corrected result, control vs curriculum across seeds 1..8, correct apparatus: control 0/8, curriculum 0/8.**
  Condition (a), one neuron per pattern, now HOLDS on most seeds (distinct claims). The robust remaining failure
  is (b): on no seed is the claimed group's weight more than 2x the noise weight. **Curriculum is NOT kept** -- a
  tie with the control at zero, the keep rule's honest null. Curriculum did not help.
- **What this corrects (original wording kept in the exp5 / exp6 section above; SE-R1).** "Three designs, one failure shape -- the third neuron
  never gets the first wins it needs" was a single-seed observation (seed 5) on the buggy apparatus. On the fixed
  apparatus across eight seeds, assignment largely works; the open problem is weak SEPARATION FROM NOISE, not a
  dead unit. exp5 and exp6's "the third neuron never wins" is superseded by this corrected multi-seed measurement;
  their code still carries the synapse-collection bug and is left as the record, corrected here beside it.

**Exp 8 PLAN (`exp8_forget.py`), committed before the run.** The reasoning, not another tweak: (b) is a RATIO (claimed
weight > 2x noise weight), and every homeostasis we tried -- weight-total normalisation, firing-rate scaling -- is
MULTIPLICATIVE, so it rescales a neuron's weights by one factor and cannot change the ratio. The ratio lives in the
learning rule. exp8 changes the rule: unreinforced synapses FORGET (ASP, "Learning to Forget", arXiv 1703.07655).
Every 100 ms each plastic weight is multiplied by (1 - LEAK), LEAK = 0.02, clipped to [0, wmax]; no total-
normalisation. Noise synapses (rarely co-active) decay toward zero; pattern synapses (reinforced each time their
group fires, ~every 0.75 s, faster than the 3.5 s half-life) persist -- so the ratio grows. CONTROL = normalisation
(exp7), TREATMENT = forget, same eight seeds, corrected apparatus (both synapses simulated), (a)+(b) bar UNCHANGED.
LEAK fixed before the run, not tuned. KEEP RULE: forgetting kept IFF it passes strictly more of the eight seeds than
the control. Recorded as is below.

**Exp 8 RESULT (2026-10-20): null -- forgetting OVERSHOT.** normalise 0/8, forget 0/8; forgetting NOT kept. But it
failed for a telling reason: with LEAK = 0.02 the neurons fired 1-2 spikes each (against 118-165 for the control),
so the decay erased the PATTERN weights too and the network went nearly silent -- it forgot everything, not just
the noise. The pre-run half-life rationale was too optimistic: under winner-take-all only the WINNING neuron's
pattern synapses get reinforced, so per-synapse reinforcement is far sparser than pattern recurrence, and a uniform
decay outruns it. The ratio diagnosis stands (homeostasis cannot fix (b); the rule must), but a UNIFORM global
decay is the wrong form -- it cannot tell a reinforced synapse from an unreinforced one. True ASP is
ACTIVITY-DEPENDENT: reinforced synapses resist decay. exp9 tests that redesign.

**Exp 9 PLAN (`exp9_consolidate.py`), committed before the run.** The fix for exp8's overshoot: forgetting that
spares what is used. Each synapse carries a consolidation c in [0,1] that rises on every LTP event (c += 0.34,
saturating) and fades over TAUC = 5 s; the 100 ms forgetting is scaled by it, w *= (1 - LEAK*(1 - c)) with LEAK =
0.05 -- full decay when c=0 (noise), none when c=1 (a recently reinforced pattern synapse). So noise forgets and the
pattern survives, growing the ratio without silencing the neuron (ASP, arXiv 1703.07655). CONTROL = normalisation
(exp7), TREATMENT = this, same eight seeds, corrected apparatus, (a)+(b) bar UNCHANGED, params fixed before the run
with reasons. KEEP RULE: kept IFF it passes strictly more of the eight seeds than the control. Recorded as is below.

**Exp 9 RESULT (2026-10-20): null, and the ratio metric told us why.** normalise 0/8, consolidate 0/8; not kept.
Two findings. (1) The normalise control reaches ratio ~1.9x (claimed weight / noise weight) on EVERY seed -- a
consistent NEAR-MISS of the 2x bar, not a gross failure. (2) Activity-dependent forgetting collapsed too (ratio
0.0, 0-2 spikes): a COLD START -- at t=0 nothing is consolidated (c=0 for all), so every synapse decays at the full
rate before any LTP can build the consolidation that would protect it; the network dies before it learns what to
keep. The consolidation gate cannot save a synapse that never got to fire. Clean fix, not a search: WARM UP under
normalisation first (pattern weights and their consolidation build), THEN switch on forgetting so the
never-consolidated noise erodes while the protected pattern survives -- pushing ~1.9x past 2x. That is exp10.

**Exp 10 PLAN (`exp10_warmup.py`), committed before the run.** The ONLY new thing over exp9 is a warmup gate. For
t < WARMUP_S = 60 s the treatment runs normalisation (the network learns; consolidation c builds on reinforced
synapses, and c decays always so it tracks RECENT reinforcement). For t >= 60 s it switches to activity-dependent
forgetting, w *= (1 - LEAK*(1 - c)) with LEAK = 0.05 -- the never-consolidated noise erodes, the consolidated
pattern survives. TAUC = 5 s, CINC = 0.34, same as exp9; nothing else tuned. CONTROL = normalisation throughout
(exp7), same eight seeds, corrected apparatus, (a)+(b) bar UNCHANGED. KEEP RULE: kept IFF it passes strictly more of
the eight seeds than the control. Recorded as is below.

**Exp 10 RESULT (2026-10-20): null -- and forgetting is now refuted, with a reason.** normalise 0/8 (~1.9x),
warmup_forget 0/8; not kept. The warmup fixed the silencing (neurons fire 58-91 spikes now, not 0-2), but once
forgetting turned on it COLLAPSED selectivity -- ratio fell to ~0 and claims often collapsed to one neuron. The
reason is mechanistic: at 5 Hz background, noise inputs frequently precede a post-spike BY CHANCE and earn LTP, so
they build consolidation c too. "Protect what is reinforced" then protects noise as much as pattern, and the decay
erodes the real structure. The consolidation signal cannot tell pattern-correlated input from chance-correlated.

#### Synthesis (exp5-10), 2026-10-20

On the CORRECTED apparatus (the noise->out synapse is simulated), measured across eight seeds, not one:
- **(a) one neuron per pattern: holds on most seeds.** The old "the third neuron never wins" was a single-seed
  (seed 5) artifact on the buggy apparatus. Assignment is not the problem.
- **(b) claimed > 2x noise: a robust ~1.9x NEAR-MISS.** The normalisation baseline reaches ratio ~1.56-1.92 on
  every seed -- consistently just under the 2.0 bar, never far off.
- **Forgetting is refuted, three ways.** Uniform decay (exp8) silenced the net (cold start). Activity-dependent
  decay (exp9) silenced it the same way (nothing consolidated at t=0). Warmup-then-prune (exp10) kept the net
  alive but collapsed selectivity, because background noise earns spurious LTP and so earns protection. A
  "forget the unreinforced" rule cannot separate pattern from chance-correlated noise in this setup.
- **The real open problem, stated.** >2x needs a mechanism that distinguishes PATTERN-correlated from
  CHANCE-correlated input -- which multiplicative homeostasis (ratio-preserving) and simple decay/consolidation
  (fooled by chance coincidences) both fail to provide. Genuine next redesigns, UNRUN and to be pre-registered if
  pursued: a dedicated inhibitory population (Diehl & Cook's exact architecture), an LTP threshold so chance
  coincidences do not potentiate, or a lower background rate. Not run here, to keep a result from becoming a search.

Run any of them with `.venv\Scripts\python.exe <file>`.

#### exp11-12: the inhibition-topology hypothesis is refuted (2026-10-20)

Two of the three named redesigns above were then RUN, at the operator's direction, each pre-registered (plan, 2x
bar and keep rule committed before the run; `exp11_inhib_pop.py`, `exp12_mahowald_wta.py`). Both change ONLY how
lateral inhibition is routed, inhibition strength held at 6 mV, same eight seeds, same bar. The question: does
sharper winner-take-all push the ~1.9x near-miss past 2x?

- **exp11 -- Diehl & Cook dedicated inhibitory population** (K inhibitory neurons; exc[k] drives inh[k], which
  inhibits the others). Result: **0/8, not kept.** It tracks the direct control almost digit-for-digit
  (ratios 1.85/1.83, 1.48/1.56, 1.92/1.92, 1.80/1.86, 1.92/1.90, 1.93/1.91, 1.89/1.90, 1.83/1.83).
- **exp12 -- Mahowald's O(N) winner-take-all** (Lazzaro, Ryckebusch, Mahowald & Mead, NIPS 1988; a SINGLE shared
  global inhibitory node). Result: **0/8, not kept.** Also tracks the control (1.84/1.83, 1.48/1.56, 1.91/1.92,
  1.80/1.86, 1.90/1.90, 1.92/1.91, 1.86/1.90, 1.81/1.83).

**What three topologies agreeing means.** Direct all-to-all (N^2), a per-neuron population, and a single global
node (O(N)) all land on the SAME ~1.9x ceiling, 0/8 each. The inhibition/competition topology is not the
bottleneck -- sharpening WHO wins does not change how cleanly the winner's weights separate from noise. That
confirms exp8's reasoning: the ratio is set by the plasticity + (multiplicative, ratio-preserving) normalisation,
not by competition. The one named redesign still unrun is the LTP threshold / lower background rate -- a change to
the PLASTICITY rule, which is where the three converging results now point. (Harness note: exp11/exp12 parallelise
the 16 seed-arch tasks across processes for speed; result-identical, numpy backend unchanged, serial versions
frozen in git at the pre-registration commits, in the lab's history rather than this extract.)

**Read again 2026-11-09 (SE-R3).** The paragraph above is kept as written. What sets the ratio stands; what it
was taken to mean does not. It treated the shared ~1.9x as a ceiling on learning and said the LTP threshold is
"where the three converging results now point". exp14-17 below show the ratio mostly separates inputs that burst
from inputs that don't, and that within the bursting inputs the groups are learned.

### exp14-exp17: the ratio's yardstick (2026-11-09)

A reader on the Hugging Face forum (topic 191599) proposed a null for the ~1.9x: no 20 inputs ever bursting
together, scored the same way. Each run below has its pre-registration in `prereg/`, committed in the lab before the
code and the code before the run; the lab's commit history is not part of this extract.

- **exp14, shuffled null.** Same burst times, but each burst fires 20 random inputs from 0-59. Ratio 1.64 against the
  real run's 1.84, real above it on 7/8 seeds; pre-registered reading "mostly by construction". It keeps 20 inputs
  firing together, so it is not the reader's null as worded.
- **exp15, the null as worded.** Burst spikes keep their input and count but move to independent random times. Ratio
  1.07, below the real run on 8/8; the pre-registered reading is "mostly pattern learning". The outputs nearly stopped
  firing (0-9 spikes per output in 120 s, against 103-178), so that verdict is set aside after the fact: the
  pre-registration had no check that the network was still firing.
- **exp16, rerun saving weights (measurement only).** Reproduces all 24 earlier ratios. The score is 1.07 at t = 0 in
  every condition, before any learning. The exp15 weights barely moved (0.0016 mean change per burst synapse,
  against 0.144 in the real run). Noise synapses alone stay near their start in every condition, so the rise is in
  the burst synapses, and the denominator (inputs 60-99) holds burst synapses that never fire.
- **A measure chosen after exp16 (`exp16_posthoc_selectivity.py`, `exp16_posthoc2.py`).** Within inputs 0-59: the
  claiming output's burst-synapse weight on its group over its weight on the other two groups. Seeds 1-8, which
  suggested it: 1.13 at t = 0 to 2.55 in the real run; 1.05 in the shuffled null.
- **exp17, that measure on new seeds 9-16, pre-registered.** Pass needs, each on at least 7 of 8: end selectivity
  >= 2.0, above its own start, above the 95th percentile of 1000 random relabelings of inputs 0-59.
  **PASS: >= 2.0 on 7/8, above start 8/8, above a 1000-relabeling null 8/8.** Seed 13 reached 1.87. Shuffled null
  mean 1.14 against the real run's 2.50.

One architecture, sixteen seeds. What this changes: the 2x bar of exp5-12 was set on a ratio that mostly separates
inputs that burst from inputs that don't; within the bursting inputs, the fixed groups are learned.

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
  reproduces it. All sixteen are `custodian-run`: the author ran the shipped, seeded scripts. CI does not, because
  they need PyTorch, snnTorch and Brian2; it only checks that every script parses. Three have their figures in a
  shipped log: exp3 run 3 (`controls/exp3_ctrl_sync_seed1.out`), exp11 (`exp11_out.txt`), exp12
  (`exp12_out.txt`) and exp14-17 (`exp14_out.txt` to `exp17_out.txt`; exp16 and exp17 also ship their weights).
- **Retractions** (`docs/RETRACTED.json`): three, recorded 2026-11-09 (see Corrections). Nulls and failures are
  reported, not retracted.
- **Manifest** (`MANIFEST.sha256`): every tracked file pinned by sha256 (text LF-normalized, images raw).

Passing means the results are auditable, not that they are true or that a rerun will match to the last digit.

## Corrections

Each withdrawn sentence is quoted as it stood, with what is true beside it.

- **SE-R1 (2026-11-09).** The exp5 / exp6 section said all three designs hit the same failure shape, "a "dead" third
  neuron that never gets the early wins it needs, so one pattern stays unclaimed". That was one seed on code that
  dropped the noise→output synapses. On corrected code across eight seeds the assignment mostly works and the
  failure is weight separation (about 1.5-1.9× against a 2× bar). See exp7 above. SE-R1.
- **SE-R2 (2026-11-09).** The opening said each experiment "was written with its **pass/fail bar declared before it
  ran**", and the list of repositories below said these were experiments "with the pass/fail bar declared before
  each run". exp1 and exp2 declare no bar; they are demonstrations. Every learning experiment has one. SE-R2.
- **SE-R3 (2026-11-09).** The exp11-12 synthesis read the three topologies' shared ~1.9x as a ceiling on learning
  and named the LTP threshold as "where the three converging results now point". What sets the ratio (plasticity;
  normalisation cannot change it) still holds. What it measures does not: it starts at 1.07 before any learning, its
  rise is in the burst synapses, and its denominator holds burst synapses that never fire. Within the bursting
  inputs the groups are learned (exp17, pre-registered on new seeds). See exp14-exp17 above. SE-R3.


---

## Part of one system — each piece usable on its own

These repositories are independent instruments that also compose into a single apparatus for **building and honestly auditing trustworthy multi-intelligence systems**. Any one can be used standalone; together they form the stack:

- **Governed core** — [covenant](https://huggingface.co/Lawless1987/covenant): a self-governing multi-agent system with an ethics gate inside the transaction path.
- **Observability & provenance** — [threefold](https://huggingface.co/Lawless1987/threefold) (the L-lens layer over Jacobian Lens) and [threefold-memory](https://huggingface.co/Lawless1987/threefold-memory) (its persistent, provenance-tracked memory): every action measured and recorded under one task identity.
- **Measurement instruments** — [contradiction-probe](https://huggingface.co/Lawless1987/contradiction-probe) and [flinch-observability](https://huggingface.co/Lawless1987/flinch-observability), with the session records [flinch-record](https://huggingface.co/Lawless1987/flinch-record) and [grokflinch](https://huggingface.co/Lawless1987/grokflinch): preregistered, blind-scored tests of AI behaviour that embody the covenant's rule — *investigate a signal, never convict on one*.
- **Neuromorphic research** — [spiking-experiments](https://huggingface.co/Lawless1987/spiking-experiments): from-scratch spiking-network experiments, each learning experiment with its bar set before it ran.
- **Ledger surface** — [Sentinel-Witness](https://huggingface.co/Lawless1987/Sentinel-Witness): the trading / ledger dashboard.

**This repository's place in it:** the neuromorphic research lab behind the covenant's stdlib spiking reflexes.
