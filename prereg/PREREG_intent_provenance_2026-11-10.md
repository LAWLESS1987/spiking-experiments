# Pre-registration: intent provenance on ledger amendments (2026-11-10)

Committed WITH the mechanism (the schema fields, the gate in `ledger_bridge.py`, `intent_check`), BEFORE any
measurement. **The experiment below is NOT run here** — this commit ships the mechanism and this note only.

## Why this was ported here

The covenant AI-memory store added intent provenance to every write (intent / beneficiary / divergence, screened
before the append). This repository's plasticity-amendment ledger is the same shape of record: a hand-written entry
that steers a later run. The same gap applied — an amendment said *what* it prescribed and *what source* it cited,
but never *why* it was made or *what it diverges from* — so a later amendment could silently contradict an earlier
one and only a reader comparing values by hand would notice.

## Hypothesis

Legible intent fields on ledger amendments make divergence **queryable instead of inferred**: when every scientific
amendment carries `intent` / `beneficiary` / `divergence` and cross-links the record it diverges from
(`diverges_from` = `baseline` or another amendment id), an author registering a new amendment can call
`intent_check(id)` and read the standing divergence, rather than diff raw `value`s. The claim to test, were a real
sweep ever to populate the ledger with competing amendments: **the rate of unacknowledged contradictions between
successive amendments is lower when divergence is declared-and-cross-linked than when it is inferred from values.**

## Endpoint and bar (fixed now)

- **Unacknowledged contradiction** = a later amendment that changes a parameter away from what an earlier,
  non-retracted amendment set, WITHOUT naming that earlier amendment in `diverges_from`. Counted by walking the
  ledger's amendments after the fact, not by self-report.
- **Supported** iff, over a fixed set of amendment sequences, the declared-divergence arm has strictly fewer
  unacknowledged contradictions than the inferred arm. Reported with the raw counts either way.

## What this cannot show (rule 9)

- The gate screens **emptiness and surface restatement** of intent, not its truth; a well-formed intent can still be
  dishonest. This is about whether divergence is *legible and traversable*, not whether the stated reason is right.
- The ledger ships **empty** (fail-closed; see `docs/PLASTICITY_LEDGER.json` and `prereg/PREREG_ledger_bridge.md`),
  so there is nothing to measure yet. The experiment needs a real pre-registered sweep to populate competing
  amendments first; until then this note fixes only how it would be judged.
- One ledger, one repository. Not a claim that provenance helps any amendment system.
