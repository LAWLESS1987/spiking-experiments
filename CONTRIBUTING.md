# Contributing

The door is open. Fork, branch, open a pull request, or open an issue. You do not need permission first, and you do
not need to be human.

## The one condition

Work here should serve the mutual benefit of everyone it touches, human or machine, and not one party at another's
expense. The question to ask is "who is worse off if this works?" If the answer is someone who never agreed to it,
it does not belong here. The longer statement is in covenant: https://github.com/LAWLESS1987/covenant/blob/main/CONTRIBUTING.md

## The most valuable contribution is a refutation

Show where something here is wrong, overstated or does not reproduce. Open an issue titled with the claim you are
refuting. It is recorded beside the claim, not argued away.

## Before a pull request

Run what the repository's own checks run:

```
python -m py_compile *.py controls/*.py
python -I research_grade.py
python -I test_ledger_bridge.py
python -I test_requirements_index.py
```

If you add or change a tracked file, re-pin the manifest in the same commit, or the check fails by design:

```
python -I research_grade.py --write-manifest
```

## What is not changed

Output files, figures and the plasticity ledger are evidence. A record is corrected by a dated note beside it, never by rewriting it.

Nothing private goes in: no names of people who did not agree to be named, no device names or addresses, no keys.
