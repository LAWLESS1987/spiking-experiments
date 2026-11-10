# Pre-registration: the ledger -> plasticity loop (2026-11-09)

Committed BEFORE the eight-seed trial is written or run. Nothing below may change after the first run; anything added
afterwards goes in a dated section below the line, and the original stays. **NOT YET RUN — this commit ships the
mechanism (`ledger_bridge.py`) and this note only; the trial is future work.**

## Hypothesis

A ledger-driven plasticity-parameter change improves the pattern/noise weight ratio over a static baseline across
eight fresh seeds. Concretely: register one amendment in `docs/PLASTICITY_LEDGER.json` (a `tau_plus_ms` or
`background_rate_hz` value), run the direct-inhibition network (exp11's `arch="direct"`) on eight seeds never used for
it, with `ledger_bridge.py` handing each seed after the first the amended config, and compare the end ratio against
the same eight seeds run at baseline (tau_plus 20 ms, background 5 Hz).

## Setup (fixed now)

- Network and measure: exp11_inhib_pop.py's `arch="direct"` path, unchanged, and its published ratio (claimed
  group mean weight / noise-input mean weight). Eight seeds never run for this network (candidate: 17-24).
- Treatment: the latest plasticity amendment in `docs/PLASTICITY_LEDGER.json`, applied by `ledger_bridge.bridge_after_run`
  to the config of every seed after the first. The amendment is registered by hand, with a cited source, BEFORE the
  run; its value is fixed once written.
- Control: the same eight seeds at baseline, with no amendment (which, by `ledger_bridge.py`'s contract, means the
  loop aborts — so the control is run directly from the baseline config, not through the bridge).
- The loop is one-directional (ledger -> config). The net is never given the ledger and writes nothing back; the
  parameter under test is set only from the ledger, so the comparison is between one registered value and baseline.

## Bar and reading (fixed now)

- **PASS** if the treatment's mean end ratio over the eight seeds exceeds the baseline's mean end ratio on the same
  eight seeds, AND exceeds it on at least 6 of the 8 seed-matched pairs.
- Reported beside it, no bar attached: per-seed ratios for both arms, and the burst-synapse selectivity (exp17's
  `sel()`) for both arms.
- Anything else: **FAIL**, reported as the numbers. No re-tuning, no extra seeds, no change of measure after the run.

## What this cannot show

- **The endpoint is confounded (SE-R3).** SE-R3 (docs/RETRACTED.json) withdrew the claim that the ~1.9x ratio was a
  learning ceiling pointing to the plasticity rule; exp14-16 showed the ratio reads 1.07 at t=0 before any learning
  and its denominator holds burst synapses that never fire. So a change in "the ratio" is NOT by itself evidence
  about learning. The selectivity reported beside it is the cleaner endpoint; this note keeps the ratio only because
  it is the pre-registered quantity named in the hypothesis, and reads any ratio movement against that caveat.
- **One architecture, one registered value.** A pass says a single ledger-registered value moved this measure on
  fresh seeds for one network. It is not a claim about other values, other parameters, other networks, or about the
  loop being the right way to search parameters.
- This note does not assert any value is the right one. `docs/PLASTICITY_LEDGER.json` ships with no amendment: until
  one is registered by hand with a standing source, the bridge aborts and this trial cannot run.
