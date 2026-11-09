# Pre-registration: exp17, burst-synapse selectivity on new seeds (2026-11-09)

Committed BEFORE the code is written or run. Nothing below may change after the first run; anything added
afterwards goes in a dated section below the line, and the original stays. NOT YET RUN.

## Why

exp16's post-hoc measure (`exp16_posthoc_selectivity.py`) was chosen after seeing seeds 1-8: within inputs 0-59,
the claiming output's mean burst-synapse weight on its group over its mean burst-synapse weight on the other two
groups. On seeds 1-8 it went 1.13 -> 2.55 in the real run and 1.13 -> 1.05 in the shuffled null. Rescoring the same
seeds under a rule would not be a test, so the test is on seeds never run: 9-16 (Claude.ai's and Tien's point in
the review of our HF 191599 reply, 2026-11-09).

## Setup (fixed now)

- exp16's code paths for `real` and `shuffled`, unchanged; seeds 9-16 (none of them ever run in this lab for this
  network). Weights recorded at t = 0 and at the end.
- Measure: exactly `sel()` in `exp16_posthoc_selectivity.py` (claimer = argmax of burst-synapse mean per group;
  per-group ratio claimed group / mean of the other two groups; mean over the three groups), at t = 0 and at the end.
- Also printed: the published ratio (end_total), claim vectors, output spikes, as exp16.

## Bar and reading (fixed now)

- **PASS** if the real run's end selectivity is >= 2.0 on at least 7 of the 8 seeds 9-16, AND above its own t = 0
  value on at least 7 of 8.
- Reported beside it, no bar: the shuffled null's end selectivity on the same seeds.
- Anything else: **FAIL**, reported as the numbers. No re-tuning, no extra seeds, no change of measure after the run.

## What this cannot show

One architecture. A pass says the fixed groups produce burst-synapse selectivity on fresh seeds by this measure; it
does not say the original ratio was wrong to use, and it is not a claim about any other network.

---

## Amendment 1 (2026-11-09, BEFORE any exp17 code or run; the text above is unchanged)

Conscious Ledger (review round 5): the claimer is picked from the same weights the measure scores, so selection alone
lifts it (1.131 at t = 0 on seeds 1-8). Added to the bar: on each seed the real run's end selectivity must also
exceed the 95th percentile of a label-permutation null (1000 random partitions of inputs 0-59 into three groups of
20, same claimer rule, scored on that run's own end weights). **PASS** now needs all three: >= 2.0 on >= 7/8,
above its t = 0 value on >= 7/8, and above its permutation null's 95th percentile on >= 7/8. On seeds 1-8 (which
motivated the measure and are not the test) the post-hoc values were 7/8, 8/8 and 8/8 (`exp16_posthoc2_out.txt`).

---

## Result (2026-11-09, added after the run; everything above is unchanged)

**PASS** as pre-registered (bar as amended before the run). Real, seeds 9-16: end selectivity >= 2.0 on 7/8
(2.78, 2.85, 2.67, 2.33, 1.87, 2.18, 2.79, 2.57; seed 13 is the miss), above its own t = 0 value on 8/8, above its
permutation null's 95th percentile on 8/8 (no permutation reached the true value on any seed). Mean end
selectivity: real 2.504, shuffled 1.136 (shuffled starts 1.12-1.24 and ends 1.11-1.20).

Also in the log, no bar attached: the published ratio (end_total) on these seeds is 1.85-2.08 in the real run
(1.51-1.80 shuffled); the real run's claims are three different outputs on 7/8 (seed 13 [0, 2, 0], the same seed
that misses 2.0). Run time 13.7 min, 4 workers. Full log: exp17_out.txt.
