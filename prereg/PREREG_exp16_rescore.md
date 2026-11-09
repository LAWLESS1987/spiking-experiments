# Pre-registration: exp16, rescoring the three conditions (descriptive only) (2026-11-09)

Committed BEFORE the code is written or run. Nothing below may change after the run; anything added afterwards
goes in a dated section below the line, and the original stays.

## Why

Reviewers of our reply to HF 191599 #2 (round 3: Tien, Conscious Ledger; round 2: ChatGPT, Meta AI) asked for two
numbers before anything is posted: (1) the ratio at the START of each run, so the desync null's 1.07 can be read
against where the weights began rather than called "near the no-learning floor" by inference; (2) the ratio from
the NOISE synapses alone, because the score as written sums each input's noise synapse and burst synapse, and on
inputs 60-99 the burst synapse never fires but stays in the denominator.

## Setup (fixed now)

- The three conditions exactly as run: real (exp14 real), shuffled (exp14 null), desync (exp15). Seeds 1-8. Same
  code paths, so the end-of-run ratio must reproduce exp14/exp15's printed ratios; that is checked and printed.
- Recorded per run: noise-synapse and burst-synapse weight matrices at t = 0 (after initialisation, before any
  simulation) and at the end.
- Printed per run, all with the exp11 formula (claimer = argmax per group; ratio = mean over groups of claimer's
  mean weight on the group over its mean weight on inputs 60-99):
  1. `end_total`: the published score (noise + burst synapse). Must equal the earlier logs.
  2. `start_total`: the same score on the t = 0 weights.
  3. `end_noise`: the score on noise-synapse weights only (the burst synapse dropped for every input).
  4. `start_noise`: the same on the t = 0 noise weights.
  5. whether the end claim vector equals the start claim vector.
- Means over seeds for each, per condition.

## Reading

None. This is a measurement, not a test: no verdict is attached to any number, and nothing here changes exp14's or
exp15's pre-registered readings. What the reply says about these numbers is written after seeing them and labelled
as such.

## What this cannot show

Same architecture, same eight seeds. It does not separate shared timing from extra presynaptic spikes in the
shuffled null (a rate-matched, firing-matched null would; that needs its own pre-registration).

---

## Result (2026-11-09, added after the run; everything above is unchanged)

Reproduction: end_total equals the earlier printed ratio on 24/24 runs (8/8 per condition). Run time 20.3 min.

| condition | end_total | start_total | end_noise | start_noise | claims unchanged from t = 0 |
|---|---|---|---|---|---|
| real | 1.839 | 1.069 | 1.078 | 1.075 | 2/8 |
| shuffled | 1.643 | 1.069 | 1.060 | 1.075 | 6/8 |
| desync | 1.073 | 1.069 | 1.065 | 1.075 | 8/8 |

Read after the run (not pre-registered): the score's zero is about 1.07 (choosing the best group per output lifts
it above 1 before anything happens). The desync null did not learn: it ends where it started, claims unchanged on
8/8. Noise synapses alone never separate in any condition, as they cannot: their spikes are independent of the
bursts. So the published ratio lives in the burst synapses, and its denominator sets bursting inputs against inputs
whose burst synapse never fires.

## Post-hoc, NOT pre-registered (2026-11-09; `exp16_posthoc_selectivity.py`, `exp16_posthoc_out.txt`)

Chosen after reading the table above. Within inputs 0-59 only: claiming output's mean burst-synapse weight on its
group over its mean burst weight on the other two groups. Means, start -> end: real 1.131 -> 2.547 (up on 8/8;
>= 2 on 7/8, seed 2 at 1.83); shuffled 1.131 -> 1.054 (up on 0/8); desync 1.131 -> 1.130. Because the measure was
picked after the data, it is a hypothesis: it gets its own pre-registration and bar before it is reported as a
result.

## Post-hoc 2, NOT pre-registered (2026-11-09, after reviewers' round 5; `exp16_posthoc2.py`, `exp16_posthoc2_out.txt`)

(a) Mean |w_end - w_start| per synapse: real burst 0.1438, noise 0.0529; shuffled burst 0.1592, noise 0.0700;
desync burst 0.0016, noise 0.0034. The desync weights barely moved (ChatGPT asked for this rather than summary scores).
(b) Label-permutation null for the selectivity measure (Conscious Ledger): 1000 random partitions of inputs 0-59 into
three groups of 20, same claimer rule. Real: the true grouping beats every permutation on 8/8 seeds (true mean
2.547; null 95th percentile mean 1.319). Shuffled: true 1.054 against null 95th 1.162, above it on 0/8.
