#!/usr/bin/env python3
"""test_ledger_bridge.py -- drive the ledger -> plasticity bridge both ways. Standard library only.

    python -I test_ledger_bridge.py        # exit 0 only if every check holds

The repo's test style (research_grade.py) is a both-ways self-test, not pytest: a check that has only ever passed has
never been observed, so every guard is driven green AND red in the same run. Here:

  AMENDMENT PRESENT  -> the next seed's config takes the prescribed value (tau_plus 20 -> 40, i.e. 2x baseline).
  AMENDMENT ABSENT   -> the run ABORTS; the next seed never runs; no default, no baseline fallback.
  ONE-DIRECTIONAL    -> the ledger file's sha256 is unchanged across a full cycle (the net never writes back).

CI runs this file (.github/workflows/tests.yml). It needs neither Brian2 nor PyTorch: the "experiment" is a stub
runner that records the config it was handed, which is all the bridge's contract is about.
"""
import hashlib
import json
import os
import sys
import tempfile

# Under `python -I` (the repo's convention, see .github/workflows/tests.yml) isolated mode drops the script's own
# directory from sys.path, so a sibling import needs it put back. ledger_bridge.py lives beside this file.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger_bridge as lb

FAILURES = []


def check(cond, label):
    print(("ok   " if cond else "FAIL ") + label)
    if not cond:
        FAILURES.append(label)


def write_ledger(path, amendments):
    doc = {
        "what": "synthetic ledger for test_ledger_bridge.py",
        "baseline": {"tau_plus_ms": 20.0, "background_rate_hz": 5.0},
        "amendments": amendments,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    return path


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class RecordingRunner:
    """Stands in for an experiment run. Given (seed, config); records a deep-ish copy; never sees the ledger."""

    def __init__(self):
        self.calls = []

    def __call__(self, seed, config):
        self.calls.append((seed, dict(config)))


BASELINE = {"tau_plus_ms": 20.0, "background_rate_hz": 5.0}
TAU_PLUS_BASELINE = 20.0


def main():
    tmp = tempfile.mkdtemp(prefix="ledger_bridge_test_")

    # --- WAY 1: amendment present. tau_plus 20 -> 40 (2x), two-seed mini-trial. -------------------------------
    present = write_ledger(
        os.path.join(tmp, "ledger_present.json"),
        [{"id": "SE-TEST-A1", "date": "2026-11-09", "source": "test",
          "param": "tau_plus_ms", "value": TAU_PLUS_BASELINE * 2, "rationale": "double tau_plus (synthetic)"}],
    )
    sha_before = sha256(present)
    runner = RecordingRunner()
    used = lb.run_trial(runner, [1, 2], BASELINE, ledger_path=present)

    check(len(used) == 2 and len(runner.calls) == 2, "W1.0 both seeds ran")
    check(used[0][1]["tau_plus_ms"] == TAU_PLUS_BASELINE, "W1.1 seed 1 ran at baseline tau_plus (20)")
    # The requirement: the SECOND seed's config reflects the amended value.
    check(used[1][1]["tau_plus_ms"] == TAU_PLUS_BASELINE * 2 == 40.0, "W1.2 seed 2's config is the amended tau_plus (40 = 2x)")
    check(used[1][1]["background_rate_hz"] == 5.0, "W1.3 the un-amended parameter (background rate) is untouched")
    check(runner.calls[1][1]["tau_plus_ms"] == 40.0, "W1.4 the stub net was actually handed tau_plus=40 for seed 2")

    # --- ONE-DIRECTIONAL: the ledger was not written during the cycle. ----------------------------------------
    check(sha256(present) == sha_before, "W1.5 ledger sha256 unchanged across the cycle (net never writes back)")

    # amend_config must not mutate its input config.
    cfg = dict(BASELINE)
    amended = lb.amend_config(cfg, {"param": "tau_plus_ms", "value": 40.0, "id": "x", "date": "2026-11-09"})
    check(cfg["tau_plus_ms"] == 20.0 and amended["tau_plus_ms"] == 40.0, "W1.6 amend_config returns a new dict, input unmutated")

    # --- WAY 2: amendment absent -> ABORT, no default, next seed never runs. -----------------------------------
    empty = write_ledger(os.path.join(tmp, "ledger_empty.json"), [])
    runner2 = RecordingRunner()
    aborted = False
    try:
        lb.run_trial(runner2, [1, 2], BASELINE, ledger_path=empty)
    except lb.LedgerAbort:
        aborted = True
    check(aborted, "W2.0 empty-amendments ledger ABORTS the trial")
    check(len(runner2.calls) == 1, "W2.1 only seed 1 ran; seed 2 never started (no default fallback)")

    # A ledger with a baseline block but no amendments must STILL abort (baseline is not an amendment).
    only_baseline = write_ledger(os.path.join(tmp, "ledger_baseline_only.json"), [])
    try:
        lb.latest_plasticity_amendment(only_baseline)
        check(False, "W2.2 baseline block alone does not satisfy the bridge")
    except lb.LedgerAbort:
        check(True, "W2.2 baseline block alone does not satisfy the bridge")

    # Missing file -> abort (read failure is a hard dependency failure, not an empty result).
    try:
        lb.latest_plasticity_amendment(os.path.join(tmp, "does_not_exist.json"))
        check(False, "W2.3 an unreadable ledger aborts")
    except lb.LedgerAbort:
        check(True, "W2.3 an unreadable ledger aborts")

    # Invalid JSON -> abort.
    bad = os.path.join(tmp, "bad.json")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write("{ not json")
    try:
        lb.latest_plasticity_amendment(bad)
        check(False, "W2.4 an unparseable ledger aborts")
    except lb.LedgerAbort:
        check(True, "W2.4 an unparseable ledger aborts")

    # An amendment for a non-plasticity param must be ignored (abort), not applied.
    offtopic = write_ledger(
        os.path.join(tmp, "offtopic.json"),
        [{"id": "SE-TEST-A2", "date": "2026-11-09", "param": "learning_rate", "value": 0.1}],
    )
    try:
        lb.latest_plasticity_amendment(offtopic)
        check(False, "W2.5 an amendment for a non-plasticity parameter does not count")
    except lb.LedgerAbort:
        check(True, "W2.5 an amendment for a non-plasticity parameter does not count")

    # --- MOST-RECENT selection: later date wins. --------------------------------------------------------------
    multi = write_ledger(
        os.path.join(tmp, "multi.json"),
        [{"id": "A1", "date": "2026-10-01", "param": "tau_plus_ms", "value": 25.0},
         {"id": "A2", "date": "2026-11-09", "param": "background_rate_hz", "value": 2.0},
         {"id": "A3", "date": "2026-10-15", "param": "tau_plus_ms", "value": 30.0}],
    )
    latest = lb.latest_plasticity_amendment(multi)
    check(latest["id"] == "A2", "W3.0 the most recent amendment (by date) is chosen")

    # --- CLI: abort returns a non-zero exit code and writes no config; success writes the amended config. ------
    cfg_in = os.path.join(tmp, "cfg_in.json")
    with open(cfg_in, "w", encoding="utf-8") as fh:
        json.dump(BASELINE, fh)
    cfg_out = os.path.join(tmp, "cfg_out.json")
    rc_empty = lb.main(["--ledger", empty, "--config-in", cfg_in, "--config-out", cfg_out])
    check(rc_empty == 2 and not os.path.exists(cfg_out), "W4.0 CLI abort: exit 2, no config written")
    rc_ok = lb.main(["--ledger", present, "--config-in", cfg_in, "--config-out", cfg_out])
    wrote_40 = os.path.exists(cfg_out) and json.load(open(cfg_out, encoding="utf-8"))["tau_plus_ms"] == 40.0
    check(rc_ok == 0 and wrote_40, "W4.1 CLI success: exit 0, next config has the amended tau_plus")

    # --- The SHIPPED ledger is fail-closed: empty by design, so a real run aborts today. ----------------------
    shipped = lb.LEDGER_DEFAULT
    if os.path.exists(shipped):
        try:
            lb.latest_plasticity_amendment(shipped)
            check(False, "W5.0 the shipped docs/PLASTICITY_LEDGER.json aborts (empty by design)")
        except lb.LedgerAbort:
            check(True, "W5.0 the shipped docs/PLASTICITY_LEDGER.json aborts (empty by design)")

    print()
    if FAILURES:
        print("test_ledger_bridge: %d FAILED -- %s" % (len(FAILURES), "; ".join(FAILURES)))
        return 1
    print("test_ledger_bridge: all checks passed")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
