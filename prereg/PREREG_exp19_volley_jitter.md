# Pre-registration: exp19, a tighter volley (2026-11-20)

Committed BEFORE the code is written or run. Nothing below may change after the first run; anything added
afterwards goes below the line, dated, and the original stays. NOT YET RUN, and not yet asked to run.

## Why

`docs/SYNTHESIS_exp14-17_2026-11-20.md`, claim 3: the claimed burst synapses stop near 3x the background because
the claimer fires inside its own group's volley. Each group's 20 spikes jitter with an sd of 2 ms. As the weights
grow, the claimer fires earlier in the volley, and the volley's later spikes depress what its earlier spikes
potentiated.

exp18 ruled out the noise synapses as what holds the published ratio, and showed post hoc that the claimed
synapses rose least when normalisation raised everything (`docs/SYNTHESIS_exp11-18_2026-11-20.md`). This changes
the input timing, not the plasticity rule.

## Setup (fixed now)

- **Control:** `exp16_rescore.run_once(s, "real")`, imported unchanged (exp11's direct inhibition).
- **Treatment:** the same code path with ONE change, the burst jitter: `rng.normal(0, 0.0005)` in place of
  `rng.normal(0, 0.002)`. That is a 0.5 ms sd, a quarter of the original.
- **Why 0.5 ms (fixed now, not tuned):** the volley then spans about 2 ms instead of about 8 ms. That is well inside
  the 10 ms membrane time constant, so if the claim holds, most of each volley arrives before the claimer's spike.
- **Seeds and runs:** seeds 1-8, 120 s, the same as exp7-18.
- **Counters, both arms, on the burst synapses** (counting does not change the dynamics):
  - potentiation events, at a post spike with a recent presynaptic spike;
  - depression events, at a presynaptic spike within 100 ms after a post spike.

  They are summed for the claimer's own group and divided by the number of that group's bursts.

## Bar, keep rule and readings (fixed now)

- **REGIME GUARD, checked first.** The change has moved the network out of its regime if, on 5 or more of the 8
  seeds, either of these happens:
  - an output fires fewer than 20 or more than 534 spikes in 120 s (534 is 3x the control's maximum of 178 in
    exp14-18);
  - all three groups are claimed by one output.

  If so: say so and stop, with no reading on the mechanism.
- **PASS per seed:** exp11's (a AND b), unchanged.
- **KEEP RULE (the operator's):** the tighter volley is kept as a change IFF it passes on STRICTLY MORE seeds than
  the control.
- **MECHANISM READING.**
  - **SUPPORTED** only if all three hold:
    - (1) (a AND b) passes on at least 6 of 8 seeds;
    - (2) end selectivity (exp17's `sel()`) is >= 2.0 on at least as many seeds as the control, with a mean not
      lower;
    - (3) depression events per own-group burst on the claimer's own burst synapses are lower than the control's
      on at least 6 of 8 seeds.
  - **REFUTED** if (3) holds but (1) fails: the volley's timing moved and the equilibrium did not.
  - **UNDETERMINED** otherwise, reported as the numbers.
- **REPRODUCTION CHECK:** the control's ratios against exp16's published values, as in exp18.
- **REPORTED, no bar:**
  - per-seed tables;
  - histograms of the ratio and of selectivity for both arms, in bins of 0.1;
  - the split into b, n_g, s, n and o;
  - the counters.

## What this cannot show

One network and one jitter value. SUPPORTED would say that the volley's timing can lift the equilibrium past the
bar, not that it is the only thing holding it. Behaviour is not measured here (open point 2 of the 2026-11-20
synthesis).

---

## Amendment 1 (2026-11-20, BEFORE any exp19 code or run; the text above is unchanged)

Made after an outside read of the pull request (Gemini, signed out) and the post hoc check it led to
(`exp18_posthoc_out.txt`).

- **The Why is corrected (SE-R4).** It said exp18 "ruled out the noise synapses as what holds the published ratio".
  It did not. Had the claimed synapses kept pace with the budget, the ratio would have averaged 1.997; and the gate
  also trimmed 4.5% of their own potentiation. exp19's question is unchanged: what holds the claimed burst synapses
  near 3x the background.
- **The mediator is narrowed to the volley.** Counter (3) counts depression events at a presynaptic spike within
  10 ms after a post spike, not 100 ms. At 2 ms jitter a volley spans about 8 ms, so this counts the volley's own
  late spikes and not post spikes driven by something else up to 100 ms earlier. The 100 ms count is still reported,
  with no bar.
- **Timing against drive.** A tighter volley also raises the peak drive. Per seed and arm, these are added to what
  is reported:
  - the share of each group's bursts on which its claimer fires within 20 ms of the volley's onset;
  - the same share for the other groups' bursts;
  - the claimer's first-spike latency from the onset.

  If the claimers' share on their own bursts rises by more than 20% over the control's, a SUPPORTED reading is
  recorded as "timing and drive together, not separated".
- **Saturation.** For both arms, the share of claimed burst synapses at or above 1.8 (0.9 * wmax) is reported. If
  it exceeds 10% in the treatment, any reading notes that the ceiling, not timing, may be what moved.