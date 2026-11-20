# Pre-registration: exp18, an LTP threshold tied to pre-before-post timing (2026-11-20)

Committed BEFORE any exp18 run, together with the code it will run (`exp18_ltp_threshold.py`, unrun). Nothing below
may change after the first run; anything added afterwards goes below the line, dated, and the original stays.
NOT YET RUN.

## Why

The exp5-10 synthesis listed an LTP threshold "so chance coincidences do not potentiate" among the unrun redesigns,
and it was never run. SE-R3 withdrew the reading that the ~1.9x was a ceiling on learning and that this threshold
was where to look next; this run does not rest on that reading. It answers a narrower question, asked by the operator
on 2026-11-20. Does an activity-dependent LTP threshold, tied to pre-before-post timing so that 5 Hz chance
coincidences do not potentiate, pass exp11's bar on strictly more of seeds 1-8 than exp11's direct inhibition? And
if it does, is that pattern learning, or the ratio's dilution term moving?

That second question comes from `docs/SYNTHESIS_exp14-17_2026-11-20.md`. There the per-group ratio is about
(1 + b/x)/2, so shrinking the background synapses x can lift it with no change in selectivity. SE-R3 applies
throughout: the ratio is kept as the bar for comparability with exp7-12, not as a measure of pattern learning.

## Setup (fixed now)

- **Control:** `exp16_rescore.run_once(s, "real")`, imported unchanged. This is exp11's direct-inhibition network;
  exp16 reproduced exp11's direct ratios 8 of 8.
- **Treatment:** a copy of that code path with ONE change, the LTP step at a post spike. The weight potentiates
  (w += apre) only if the presynaptic trace apre > LTP_THR; otherwise it does not potentiate. Everything else is
  unchanged: LTD, Apre, Apost, taupre, taupost, wmax, normalisation, inhibition, inputs and their seeds, the adaptive
  threshold, the duration.
- **LTP_THR = Apre * exp(-5 ms / taupre) = 0.01 * e^(-0.25), about 0.00779.** That is the trace one presynaptic spike
  leaves 5 ms after it arrives. So a post spike potentiates a synapse only if that input fired within the last 5 ms,
  or, rarely, twice within the trace's memory.
- **Why 5 ms (fixed now, not tuned):**
  - A volley's 20 spikes jitter with an sd of 2 ms, so the spikes that precede the post spike they drive arrive
    within about 0-5 ms of it.
  - A 5 Hz background input has a 2.5% chance of a spike in any given 5 ms.
  - Against the unchanged rule, whose trace decays over 20 ms, the gate keeps about 22% (1 - e^(-5/20)) of the
    expected potentiation from chance coincidences, and nearly all of the potentiation within a volley.
  - The consolidation signal was considered as the gate and rejected: exp10 showed chance coincidences earn
    consolidation too.
- **Seeds and runs:** seeds 1-8, the seeds of exp7-12, 120 s each. Runs go in parallel processes; each (seed, arm)
  is fully determined by its seed.
- **Counters, treatment only.** For each synapse, two counts:
  - let through: the trace is above LTP_THR at a post spike;
  - blocked: the trace is above the value one spike leaves after 100 ms, but at or below LTP_THR.

  They are summed per class: burst synapses on the claimer's own group, burst synapses on the other two groups,
  burst synapses on inputs 60-99 (expected 0), and noise synapses.
- **Smoke test:** before the experimental runs, the code may be run once on seed 0 for 2 s to check that it executes.
  No number from it is read. A code fix it forces is committed as a dated amendment before any seed 1-8 run.

## Bar, keep rule and readings (fixed now)

- **PASS per seed, unchanged from exp7-12 (exp11's scoring lines):**
  - (a) the three groups are claimed by three different outputs;
  - (b) on each group, the claimer's mean weight (burst plus noise synapse) is more than 2x its mean on inputs
    60-99.
- **KEEP RULE (the operator's):** the threshold is kept IFF the treatment passes on STRICTLY MORE of the eight seeds
  than the control. A tie or worse is a null, recorded as is. The threshold is not tuned after any result is seen.
- **COLLAPSE (exp8's shape), checked first.** The threshold has collapsed firing if, on 5 or more of the 8 seeds,
  some treatment output fires fewer than 20 spikes in 120 s. The real run's outputs fired 103-178 in exp14-16. If it
  collapses: say so and stop. No rerun, no change.
- **VALIDITY (SE-R3).** This decides how a keep is read, not whether it is kept. A kept threshold counts as better
  PATTERN learning only if its end selectivity is at least 2.0 on at least as many seeds as the control's, and its
  mean is not lower. Selectivity is exp17's `sel()`: burst synapses, within inputs 0-59. Otherwise the keep is
  recorded as "the ratio moved, selectivity did not: the dilution term, not pattern learning".
- **REPRODUCTION CHECK.** The control's end ratio on each seed is compared with exp16's published real values (1.83,
  1.56, 1.92, 1.86, 1.9, 1.91, 1.9, 1.83). A mismatch is reported; the comparison between the two arms stays within
  this run either way.
- **REPORTED, no bar,** per seed and arm:
  - per-group ratios, claims and spikes per output;
  - selectivity at t = 0 and at the end, and its 95th percentile over 1000 relabelings;
  - the split into b, n_g, s, n and o, as in `exp17_decompose_ratio.py`;
  - a histogram of the per-seed ratio and of the per-seed selectivity for each arm, in bins of 0.1, so the
    distribution is read and not only the count;
  - the counters.

## What this cannot show

One architecture, one window. A null says this gate at 5 ms did not move the bar on these seeds, not that no LTP
threshold could. A keep on the ratio alone says the ratio moved; the validity reading says whether selectivity moved
with it. Behaviour (replaying each group's burst with the weights frozen) is not measured here.
