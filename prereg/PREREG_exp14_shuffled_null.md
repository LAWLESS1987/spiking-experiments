# Pre-registration: exp14, a shuffled-burst null for the ~1.9x ratio (2026-11-09)

Committed BEFORE the experiment code is written or run. Nothing below may change after the first run; anything
added afterwards goes in a dated section below the line, and the original stays.

## Why

Our Hugging Face topic 191599 (2026-11-09) reported that STDP + winner-take-all on corrected code stalls at a
claimed-to-noise weight ratio of about 1.5-1.9x against a 2x bar on seeds 1-8, and asked where to look. nootxlm
answered (#2) with a null: rerun the same seeds with the same Poisson streams but no 20 inputs ever bursting
together, score the ratio exactly as now, and read the gap. Whatever the null gives is what the input statistics
and normalisation produce by construction; only the gap between it and the real run is pattern learning.
Lawrence, 2026-11-09: "Run it". The null had not been run in the lab; exp5-12 never measured a chance baseline.

## Setup (fixed now)

- Code: the exp11 "direct" arm unchanged (it is the exp7 control: N = 100 inputs, K = 3 outputs, 5 Hz Poisson
  noise on all 100, a burst every 0.25 s for 120 s, 2 ms jitter, STDP, adaptive threshold, weight-total
  normalisation every 100 ms, direct lateral inhibition 6 mV, explicit Network). Seeds 1-8.
- Two conditions per seed:
  - **real**: each burst fires one of the three fixed groups (inputs 0-19, 20-39, 40-59), as in exp11.
  - **null**: the same burst times, the same group draw and the same jitter draws (the main random stream is left
    untouched), but each burst fires 20 inputs drawn at random, without replacement, from 0-59, using a separate
    random stream (seed 1000 + s). So each of inputs 0-59 still takes part in a burst with probability 1/3, as in
    the real run (same per-input rate), but no fixed set of 20 ever fires together. Inputs 60-99 are untouched.
- Scoring identical in both conditions, and identical to exp11: claimed group means per output, `claimer` = argmax
  over outputs for each group, ratio = mean over the three groups of (claimer's mean weight on the group) /
  (claimer's mean weight on inputs 60-99). The (a) and (b) bars are computed and printed too.

## Reading (fixed now)

Per seed, gap = ratio_real - ratio_null.

- **Reproduction check.** The real column must equal exp11's direct ratios seed for seed (same code, same seeds).
  If it does not, that is reported first and the comparison is read with that caveat.
- **"The ~1.9x is mostly pattern learning"** only if gap > 0 on at least 7 of 8 seeds AND the mean null ratio is at
  most 1.3.
- **"The ~1.9x is mostly by construction"** only if the mean null ratio is at least 0.8 x the mean real ratio.
- Anything else: **partial**, reported as the numbers (mean null, mean real, per-seed gaps), with no verdict.
- No re-tuning, no extra seeds, no second null after seeing results. A second null, if one is wanted, gets its own
  pre-registration.

## What this cannot show

One architecture, eight seeds, one null. The null keeps the per-input rates but removes co-firing; it does not
separate the two routes by which inputs 0-59 differ from 60-99 (60-99 carry a pattern synapse that never fires
and is only ever scaled by normalisation; 0-59 receive extra spikes). If the null ratio is high, this run says the
scoring rewards rate, not which mechanism inside that does it. Nothing here concerns hardware or covenant.

---

## Result (2026-11-09, added after the run; everything above is unchanged)

Reproduction: the real column equals exp11's direct ratios on 8/8 seeds (spike counts equal too).
Mean real 1.839, mean null 1.643, null/real 0.893; gap > 0 on 7/8 seeds (gaps 0.21, -0.02, 0.17, 0.20, 0.31, 0.22,
0.13, 0.35). Reading as pre-registered: **MOSTLY BY CONSTRUCTION** (mean null >= 0.8 x mean real). The "pattern
learning" rule failed on its second condition (mean null 1.643 > 1.3), though its first held (7/8).

Descriptive only, NOT pre-registered: one-neuron-per-pattern assignment (bar a) holds on 7/8 seeds real and 1/8
null (seed 6). Every run fails bar b in both conditions. Full log: exp14_out.txt (Brian2's namespace warnings about
the loop variables `i` and `t` are in it; they name internal variables that Brian2 uses instead, and the 8/8
reproduction shows the real arm unchanged). Figure: exp14_shuffled_null.png. Run time 11.5 min, 4 workers.
