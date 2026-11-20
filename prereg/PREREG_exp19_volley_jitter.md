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
