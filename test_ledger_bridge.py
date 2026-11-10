#!/usr/bin/env python3
"""test_ledger_bridge.py -- drive the ledger -> plasticity bridge both ways. Standard library only.

    python -I test_ledger_bridge.py        # exit 0 only if every check holds

The repo's test style (research_grade.py) is a both-ways self-test, not pytest: a check that has only ever passed has
never been observed, so every guard is driven green AND red in the same run. Here:

  AMENDMENT PRESENT  -> the next seed's config takes the prescribed value (tau_plus 20 -> 40, i.e. 2x baseline).
  AMENDMENT ABSENT   -> the run ABORTS; the next seed never runs; no default, no baseline fallback.
  ONE-DIRECTIONAL    -> the ledger file's sha256 is unchanged across a full cycle (the net never writes back).
  RETRACTED CITATION -> an amendment citing a retracted (or missing) source is never selected; the run ABORTS (W6).
  MECHANISM EXERCISE -> the mechanism_exercise class exercises the loop but is never selected as a finding, and an
                        exercise entry that tries to cite a standing source is REFUSED (W7).

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


# Intent provenance (intent/beneficiary/divergence) is now required on every
# scientific amendment. The W1-W7 checks are about OTHER properties, so
# write_ledger injects a fixed valid triple into any scientific amendment that
# omits it -- an intent that shares no words with the rationales, so the
# restatement screen stays out of the way. mechanism_exercise entries are left
# alone (they carry no provenance). W8 passes inject_prov=False to drive the
# provenance guard itself, both ways.
_DEF_PROV = {"intent": "steer the next experiment toward a cleaner measurement",
             "beneficiary": "future unknown agent", "divergence": "none"}


def write_ledger(path, amendments, inject_prov=True):
    out = []
    for a in amendments:
        a = dict(a)
        if (inject_prov and a.get("kind") != "mechanism_exercise"
                and "intent" not in a):
            for k, v in _DEF_PROV.items():
                a.setdefault(k, v)
        out.append(a)
    doc = {
        "what": "synthetic ledger for test_ledger_bridge.py",
        "baseline": {"tau_plus_ms": 20.0, "background_rate_hz": 5.0},
        "amendments": out,
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
        [{"id": "A1", "date": "2026-10-01", "source": "test", "param": "tau_plus_ms", "value": 25.0},
         {"id": "A2", "date": "2026-11-09", "source": "test", "param": "background_rate_hz", "value": 2.0},
         {"id": "A3", "date": "2026-10-15", "source": "test", "param": "tau_plus_ms", "value": 30.0}],
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

    # --- W6: THE NEGATIVE TEST (the one the consult called most important): a RETRACTED or missing citation can
    #         never activate a parameter change. Hermetic: a synthetic retractions file lists SE-R3. -------------
    retracted = os.path.join(tmp, "retracted.json")
    with open(retracted, "w", encoding="utf-8") as fh:
        json.dump({"retractions": [{"id": "SE-R3"}, {"id": "SE-R1"}]}, fh)

    good_src = write_ledger(
        os.path.join(tmp, "good_source.json"),
        [{"id": "SE-A1", "date": "2026-11-10", "source": "PREREG_sweep_2027",
          "param": "background_rate_hz", "value": 2.0}],
    )
    chosen = lb.latest_plasticity_amendment(good_src, retracted_path=retracted)
    check(chosen["id"] == "SE-A1", "W6.0 an amendment citing a standing (non-retracted) source IS applied")

    retr_cite = write_ledger(
        os.path.join(tmp, "retracted_cite.json"),
        [{"id": "SE-A1", "date": "2026-11-10", "source": "SE-R3",
          "param": "background_rate_hz", "value": 2.0}],
    )
    try:
        lb.latest_plasticity_amendment(retr_cite, retracted_path=retracted)
        check(False, "W6.1 an amendment citing a RETRACTED source ABORTS (retracted citation cannot activate a change)")
    except lb.LedgerAbort:
        check(True, "W6.1 an amendment citing a RETRACTED source ABORTS (retracted citation cannot activate a change)")

    no_src = write_ledger(
        os.path.join(tmp, "no_source.json"),
        [{"id": "SE-A1", "date": "2026-11-10", "param": "background_rate_hz", "value": 2.0}],
    )
    try:
        lb.latest_plasticity_amendment(no_src, retracted_path=retracted)
        check(False, "W6.2 an amendment with no cited source ABORTS")
    except lb.LedgerAbort:
        check(True, "W6.2 an amendment with no cited source ABORTS")

    try:
        lb.latest_plasticity_amendment(good_src, retracted_path=os.path.join(tmp, "no_retracted_file.json"))
        check(False, "W6.3 an unreadable retractions file ABORTS the scientific path (cannot certify the citation is live)")
    except lb.LedgerAbort:
        check(True, "W6.3 an unreadable retractions file ABORTS the scientific path (cannot certify the citation is live)")

    # --- W7: the mechanism_exercise class -- exercise the loop WITHOUT it ever counting as a plasticity finding. --
    ex = write_ledger(
        os.path.join(tmp, "exercise.json"),
        [{"id": "SE-X1", "date": "2026-11-10", "kind": "mechanism_exercise", "source": "none",
          "param": "tau_plus_ms", "value": 20.0, "rationale": "no-op baseline; exercise the parse->config path only"}],
    )
    try:
        lb.latest_plasticity_amendment(ex, retracted_path=retracted)
        check(False, "W7.0 a mechanism_exercise entry is NOT selected by the scientific path (fail-closed holds)")
    except lb.LedgerAbort:
        check(True, "W7.0 a mechanism_exercise entry is NOT selected by the scientific path (fail-closed holds)")

    runner_x = RecordingRunner()
    try:
        lb.run_trial(runner_x, [1, 2], BASELINE, ledger_path=ex, retracted_path=retracted)
        check(False, "W7.1 run_trial never applies an exercise entry (an exercise-only ledger aborts the trial)")
    except lb.LedgerAbort:
        check(True, "W7.1 run_trial never applies an exercise entry (an exercise-only ledger aborts the trial)")

    ex_cfg = lb.bridge_exercise(dict(BASELINE), ledger_path=ex)
    check(ex_cfg["tau_plus_ms"] == 20.0, "W7.2 the exercise path DOES resolve the entry (dry-run config), non-citable")

    # THE GUARD, both ways: an exercise entry that CITES a standing source is refused -- the label cannot launder it.
    ex_bad = write_ledger(
        os.path.join(tmp, "exercise_cites.json"),
        [{"id": "SE-X2", "date": "2026-11-10", "kind": "mechanism_exercise", "source": "PREREG_sweep_2027",
          "param": "tau_plus_ms", "value": 21.0}],
    )
    try:
        lb.latest_mechanism_exercise(ex_bad)
        check(False, "W7.3 an exercise entry that CITES a standing source is REFUSED (the label cannot launder a citation)")
    except lb.LedgerAbort:
        check(True, "W7.3 an exercise entry that CITES a standing source is REFUSED (the label cannot launder a citation)")

    # --- W8: INTENT PROVENANCE on amendments, driven both ways. ------------------------------------------------
    good_retr = os.path.join(tmp, "w8_retracted.json")
    with open(good_retr, "w", encoding="utf-8") as fh:
        json.dump({"retractions": [{"id": "SE-R3"}]}, fh)

    def _amend(**over):
        base = {"id": "SE-A1", "date": "2026-11-10", "source": "PREREG_sweep_2027",
                "param": "background_rate_hz", "value": 2.0,
                "rationale": "lower the noise floor",
                "intent": "sharpen selectivity by quieting the background",
                "beneficiary": "future unknown agent", "divergence": "none"}
        base.update(over)
        return base

    # present + well-formed -> applied.
    w8_ok = write_ledger(os.path.join(tmp, "w8_ok.json"), [_amend()], inject_prov=False)
    sel = lb.latest_plasticity_amendment(w8_ok, retracted_path=good_retr)
    check(sel["id"] == "SE-A1", "W8.0 a scientific amendment WITH provenance is selected")

    # each field missing -> abort.
    for drop in ("intent", "beneficiary", "divergence"):
        led = write_ledger(os.path.join(tmp, f"w8_no_{drop}.json"),
                           [_amend(**{drop: "  "})], inject_prov=False)
        try:
            lb.latest_plasticity_amendment(led, retracted_path=good_retr)
            check(False, f"W8.{drop} an amendment missing {drop} ABORTS")
        except lb.LedgerAbort:
            check(True, f"W8.{drop} an amendment missing {drop} ABORTS")

    # intent restates the rationale -> abort.
    led = write_ledger(os.path.join(tmp, "w8_restate.json"),
                       [_amend(intent="lower the noise floor")], inject_prov=False)
    try:
        lb.latest_plasticity_amendment(led, retracted_path=good_retr)
        check(False, "W8.restate an intent that RESTATES the rationale ABORTS")
    except lb.LedgerAbort:
        check(True, "W8.restate an intent that RESTATES the rationale ABORTS")

    # divergence != none: needs a resolvable diverges_from; 'baseline' is valid.
    led = write_ledger(os.path.join(tmp, "w8_div_ok.json"),
                       [_amend(divergence="conflicts with the 5 Hz baseline", diverges_from="baseline")],
                       inject_prov=False)
    sel = lb.latest_plasticity_amendment(led, retracted_path=good_retr)
    check(sel.get("diverges_from") == "baseline",
          "W8.div-ok divergence != none with diverges_from='baseline' is applied and cross-linked")

    led = write_ledger(os.path.join(tmp, "w8_div_nolink.json"),
                       [_amend(divergence="conflicts with something", diverges_from="")],
                       inject_prov=False)
    try:
        lb.latest_plasticity_amendment(led, retracted_path=good_retr)
        check(False, "W8.div-nolink divergence != none with NO diverges_from ABORTS")
    except lb.LedgerAbort:
        check(True, "W8.div-nolink divergence != none with NO diverges_from ABORTS")

    led = write_ledger(os.path.join(tmp, "w8_div_dangle.json"),
                       [_amend(divergence="conflicts with ghost", diverges_from="SE-A999")],
                       inject_prov=False)
    try:
        lb.latest_plasticity_amendment(led, retracted_path=good_retr)
        check(False, "W8.div-dangle diverges_from naming no amendment ABORTS")
    except lb.LedgerAbort:
        check(True, "W8.div-dangle diverges_from naming no amendment ABORTS")

    led = write_ledger(os.path.join(tmp, "w8_div_contra.json"),
                       [_amend(divergence="none", diverges_from="baseline")], inject_prov=False)
    try:
        lb.latest_plasticity_amendment(led, retracted_path=good_retr)
        check(False, "W8.div-contra divergence 'none' WITH a diverges_from ABORTS")
    except lb.LedgerAbort:
        check(True, "W8.div-contra divergence 'none' WITH a diverges_from ABORTS")

    # intent_check: verbatim fields + a satisfiability flag.
    ic = lb.intent_check("SE-A1", w8_ok, good_retr)
    check(ic["intent"] == "sharpen selectivity by quieting the background"
          and ic["beneficiary"] == "future unknown agent",
          "W8.ic0 intent_check returns the fields VERBATIM")
    check(ic["satisfiable"] is True, "W8.ic1 a well-formed, standing amendment is satisfiable")

    led = write_ledger(os.path.join(tmp, "w8_ic_retr.json"),
                       [_amend(source="SE-R3")], inject_prov=False)
    ic2 = lb.intent_check("SE-A1", led, good_retr)
    check(ic2["satisfiable"] is False and "retracted" in ic2["assessment"],
          "W8.ic2 an amendment citing a retracted source reads UNSATISFIABLE")

    ic3 = lb.intent_check("NOPE", w8_ok, good_retr)
    check(ic3["satisfiable"] is False and "no amendment" in ic3["assessment"],
          "W8.ic3 an unknown id reads UNSATISFIABLE")

    print()
    if FAILURES:
        print("test_ledger_bridge: %d FAILED -- %s" % (len(FAILURES), "; ".join(FAILURES)))
        return 1
    print("test_ledger_bridge: all checks passed")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
