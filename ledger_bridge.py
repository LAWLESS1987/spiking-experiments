#!/usr/bin/env python3
"""ledger_bridge.py -- the ledger -> plasticity bridge, one portable file, standard library only (Python 3.9+).

    python -I ledger_bridge.py --config-in next_run_config.json --config-out next_run_config.json
    python -I ledger_bridge.py --config-in - --config-out next_run_config.json   # baseline on stdin

IT DOES EXACTLY ONE THING. After an experiment run completes, it queries the covenant ledger for the most recent
amendment affecting a plasticity parameter (tau_plus or the background rate), extracts the prescribed value, and
writes it into the config the NEXT run will start from. Nothing else.

THE DIRECTION IS ONE-WAY, ON PURPOSE (so the loop's effect can be audited): ledger -> net config, never back. No
function in this file writes to the ledger. test_ledger_bridge.py pins that by asserting the ledger file's sha256 is
unchanged across a full cycle.

THE LEDGER IS A HARD DEPENDENCY, NOT A SUGGESTION. If the ledger cannot be read, or holds no amendment that
prescribes a plasticity parameter, the run ABORTS with a logged reason -- it NEVER falls back to a default or
baseline value. A silent fallback would let the loop keep running on stale parameters and call it a result; that is
the failure this guard exists to make impossible. `baseline` in the ledger is a reference for amendment authors and
for the config the FIRST run starts from; the bridge never treats it as an amendment.

WHERE THE LEDGER IS. docs/PLASTICITY_LEDGER.json in this repository: the machine-readable half of the covenant
ledger as it is reachable here, beside docs/RETRACTED.json and docs/CLAIMS_INDEX.json (the prose half). A plasticity
amendment cites the standing record it derives from; a RETRACTED pointer (e.g. SE-R3, which withdrew the claim that
the ratio pointed to the plasticity rule) is not a standing source and must not be cited as if it prescribes a value.

WHAT THIS CANNOT DO. It does not decide WHICH value is right -- that is an amendment author's judgement, recorded by
hand with a cited source. It does not run the experiment; it only hands the next run its config. And it does not read
the prose ledger's free text for numbers: amendments are structured JSON, so there is no regex guessing a value out
of a paragraph.
"""
import argparse
import hashlib
import json
import logging
import os
import sys

LEDGER_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "PLASTICITY_LEDGER.json")

# The only parameters a plasticity amendment may prescribe, with the baseline each is measured against.
# tau_plus_ms  == the STDP taupre, 20 ms baseline (exp11_inhib_pop.py:76 and every STDP script).
# background_rate_hz == the PoissonGroup noise rate, 5 Hz baseline (exp11_inhib_pop.py:51 and the others).
PLASTICITY_PARAMS = ("tau_plus_ms", "background_rate_hz")

log = logging.getLogger("ledger_bridge")


class LedgerAbort(Exception):
    """Raised when the ledger cannot be read or holds no plasticity amendment. The run must stop; never default."""


def _abort(reason):
    """Log the reason and abort. The logged line is the audit trail for why a run did not proceed."""
    log.error("ABORT: %s", reason)
    raise LedgerAbort(reason)


def read_ledger(ledger_path=LEDGER_DEFAULT):
    """Read and parse the ledger. READ-ONLY. Aborts (never returns) on any failure to read or parse."""
    try:
        with open(ledger_path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        _abort("ledger could not be read at %r (%s)" % (ledger_path, exc))
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        _abort("ledger at %r is not valid JSON (%s)" % (ledger_path, exc))


def _is_plasticity_amendment(a):
    """True iff a is a well-formed amendment prescribing one of the plasticity parameters."""
    if not isinstance(a, dict):
        return False
    if a.get("param") not in PLASTICITY_PARAMS:
        return False
    if not isinstance(a.get("value"), (int, float)) or isinstance(a.get("value"), bool):
        return False
    if not isinstance(a.get("date"), str) or not a.get("date"):
        return False
    if not a.get("id"):
        return False
    return True


def latest_plasticity_amendment(ledger_path=LEDGER_DEFAULT):
    """Return the most recent plasticity amendment in the ledger, or abort if there is none.

    'Most recent' = highest ISO date; ties broken by position (later in the list is later). Malformed entries are
    ignored, not guessed at. If no well-formed plasticity amendment remains, the run aborts -- no default.
    """
    ledger = read_ledger(ledger_path)
    amendments = ledger.get("amendments")
    if not isinstance(amendments, list):
        _abort("ledger at %r has no 'amendments' list" % (ledger_path,))
    candidates = [(a["date"], i, a) for i, a in enumerate(amendments) if _is_plasticity_amendment(a)]
    if not candidates:
        _abort("ledger at %r holds no amendment prescribing a plasticity parameter %r" % (ledger_path, list(PLASTICITY_PARAMS)))
    candidates.sort(key=lambda t: (t[0], t[1]))
    chosen = candidates[-1][2]
    log.info("amendment %s (%s): %s = %s", chosen.get("id"), chosen.get("date"), chosen["param"], chosen["value"])
    return chosen


def amend_config(config, amendment):
    """Return a NEW config dict with the amendment's prescribed parameter set to its value. Pure; ledger -> config.

    The input config is not mutated, and the ledger is not touched. Only the one prescribed parameter changes.
    """
    if not isinstance(config, dict):
        raise TypeError("config must be a dict, got %r" % type(config).__name__)
    out = dict(config)
    out[amendment["param"]] = amendment["value"]
    return out


def bridge_after_run(config_in, ledger_path=LEDGER_DEFAULT):
    """The one thing: given the config a run just used, return the config the NEXT run must start from.

    Reads the latest plasticity amendment (aborting if none) and applies it. Called AFTER a run completes and BEFORE
    the next run starts. Raises LedgerAbort rather than ever returning a default.
    """
    amendment = latest_plasticity_amendment(ledger_path)
    return amend_config(config_in, amendment)


def run_trial(runner, seeds, config_in, ledger_path=LEDGER_DEFAULT):
    """Drive a multi-seed trial through the bridge, one directional hop per seed boundary.

    runner(seed, config) runs one experiment seed and returns whatever it likes (ignored here). After each seed
    completes, the bridge produces the next seed's config from the ledger. `runner` is the net: it is given a config
    and never the ledger, so by construction it cannot write back. Returns the list of (seed, config_used).

    If the bridge aborts between seeds, the trial stops there: the remaining seeds never run, and no default is used.
    """
    seeds = list(seeds)
    if not seeds:
        return []
    used = []
    config = dict(config_in)
    for n, s in enumerate(seeds):
        runner(s, config)
        used.append((s, config))
        if n < len(seeds) - 1:               # produce the NEXT seed's config from the ledger (hard dependency)
            config = bridge_after_run(config, ledger_path)
    return used


def _read_config_in(arg):
    if arg == "-":
        return json.loads(sys.stdin.read())
    with open(arg, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(description="Apply the latest plasticity amendment to the next run's config.")
    p.add_argument("--ledger", default=LEDGER_DEFAULT, help="path to the plasticity-amendment ledger")
    p.add_argument("--config-in", required=True, help="path to the config the last run used, or '-' for stdin JSON")
    p.add_argument("--config-out", required=True, help="path to write the next run's config")
    args = p.parse_args(argv)
    try:
        config_in = _read_config_in(args.config_in)
    except (OSError, json.JSONDecodeError) as exc:
        log.error("ABORT: could not read --config-in %r (%s)", args.config_in, exc)
        return 2
    try:
        next_config = bridge_after_run(config_in, args.ledger)
    except LedgerAbort:
        return 2                              # reason already logged by _abort
    with open(args.config_out, "w", encoding="utf-8") as fh:
        json.dump(next_config, fh, indent=1, sort_keys=True)
        fh.write("\n")
    log.info("wrote next-run config to %s", args.config_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
