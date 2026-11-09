# Pre-registration: exp15, a coincidence-free null (nootxlm's null as worded) (2026-11-09)

Committed BEFORE the experiment code is written or run. Nothing below may change after the first run; anything
added afterwards goes in a dated section below the line, and the original stays.

## Why

exp14 ran a null that randomised WHICH 20 inputs burst together but kept 20 inputs firing together at every burst.
nootxlm's proposal (HF 191599 #2) was worded "so no 20 inputs ever burst together". Three reviewers (Claude.ai,
DeepSeek, Mistral, 2026-11-09) each pointed out that exp14 is not that test: its retained coincidences could be
what lifts its null ratio to 1.64. exp14's pre-registration says a second null gets its own pre-registration. This
is it. Lawrence's instruction for the thread, 2026-11-09: "Run it".

## Setup (fixed now)

- Code: exp14 unchanged except the burst spikes' times. Seeds 1-8. Only the null arm is run; the real arm is
  exp14's real column, which reproduced exp11's direct arm on 8/8 seeds (same code, deterministic per seed).
- **desync null**: build the real run's burst spike list exactly as exp14's real arm does (same group draws, same
  jitter, so every input 0-59 gets EXACTLY the real run's burst spike count), then give every one of those spikes
  an independent uniform random time in [0.05 s, 120 s), from a separate stream (seed 2000 + s). Coincidences
  remain only by chance, at the rate independent spikes produce. Poisson noise and everything downstream unchanged.
- Scoring identical to exp11 and exp14.

## Reading (fixed now)

Per seed, gap = ratio_real (exp14) - ratio_desync.

- **"The ~1.8x is mostly pattern learning"** only if gap > 0 on at least 7 of 8 seeds AND the mean desync ratio is
  at most 1.3.
- **"Mostly by construction"** only if the mean desync ratio is at least 0.8 x the mean real ratio (1.839).
- Anything else: **partial**, reported as the numbers, no verdict.
- Also reported, descriptively, not as a verdict: the desync ratio against exp14's shuffled ratio (1.643), which
  says how much of exp14's null came from the coincidences it kept.
- No re-tuning, no extra seeds, no further null after seeing results without a new pre-registration.

## What this cannot show

As exp14: one architecture, eight seeds. It removes synchrony but keeps the rate difference between inputs 0-59
and 60-99, and the silent pattern synapse on 60-99; it does not separate those two.

---

## Result (2026-11-09, added after the run; everything above is unchanged)

Mean real (exp14) 1.839, mean desync 1.073, desync/real 0.583; gap > 0 on 8/8 seeds (gaps 0.82, 0.56, 0.79, 0.78,
0.86, 0.79, 0.73, 0.80). Reading as pre-registered: **MOSTLY PATTERN LEARNING** (8/8 AND mean desync <= 1.3).
Descriptive, as pre-registered: desync minus exp14 shuffled = -0.570.

**What the verdict leans on, found in the same log, not pre-registered.** In the desync null the three output neurons
were nearly silent: 0 to 9 spikes per neuron over 120 s (exp14 real: 103 to 178). With no coincident bursts the
outputs barely cross threshold, so STDP barely acts and the weights stay near where they started; the ~1.07 is close
to the no-learning floor, not a baseline that kept the drive and only removed the pattern. So this null shows that
coincident input is what drives the learning at all; it cannot show how much of the 1.84 a driven network would
reach without a fixed pattern. That is what exp14's shuffled null measured (1.64, drive kept). Read together:
coincident bursts on inputs 0-59 bring the ratio to about 1.6; fixed group identity adds about 0.2, and one neuron
per pattern (7/8 real, 1/8 shuffled, 1/8 desync: seed 6 in each null).

Also recorded: lab commit df474e7's message said same-step collisions were redrawn, but that edit had failed and the
commit does not contain it; d181f4a added it before the run. Full log: exp15_out.txt. Figure: exp15_desync_null.png.
Run time 6.9 min, 4 workers.
