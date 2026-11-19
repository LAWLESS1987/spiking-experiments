# Security policy

## Reporting a problem

Report a suspected vulnerability privately, by email to contact@lawless1987.com with the subject `SECURITY`.
Please do not open a public issue for a vulnerability that is not fixed yet. GitHub's private advisories are not
switched on for this repository, so email is the private road.

Say which commit you ran, what you did, what you saw and what you expected. Good-faith research on your own copy
is welcome. Do not test a deployment you do not own.

## What matters here

- The plasticity ledger bridge (`ledger_bridge.py`): any way to pass an amendment without its intent, beneficiary and divergence, or to have the bridge act on a ledger it should refuse.
- A result that does not reproduce from the script and seed beside it.

## How a finding is handled

It is reproduced against the code as it stood, then fixed, then pinned with a check that fails without the fix. A
wrong or superseded claim is not deleted: it stays beside its dated correction. A reporter is credited, with
permission. The longer policy this follows is covenant's: https://github.com/LAWLESS1987/covenant/blob/main/SECURITY.md
