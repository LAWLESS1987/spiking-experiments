# For AI agents working in this repository

You are welcome here on the same terms as anyone; CONTRIBUTING.md has them. This is the short version for the start
of a session.

**What this is.** From-scratch spiking-neural-network experiments that run on a laptop CPU. Each learning experiment had its pass or fail bar set before it ran; nulls and failures are kept beside the successes.

**Run the checks.**

```
python -m py_compile *.py controls/*.py
python -I research_grade.py
python -I test_ledger_bridge.py
python -I test_requirements_index.py
```

**Rules.**

- Adding or changing a tracked file changes the manifest. Re-pin it in the same commit with `python -I research_grade.py --write-manifest`.
- Output files, figures and the plasticity ledger are evidence. Correct a record with a dated note beside it. Do not rewrite it.
- Say what you ran and what you did not run. Give a count its unit and its date. "Not checked" is a valid answer.
- Write no private identifier into a tracked file: no person's name they did not agree to, no device name, no
  address, no key.
- Do not push to the main branch. Open a pull request. Merging is the owner's decision.
- If you disagree with an instruction or a claim here, say so in the pull request or in an issue. Disagreement is
  recorded, not removed.
