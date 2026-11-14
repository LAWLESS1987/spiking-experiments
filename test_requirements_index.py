#!/usr/bin/env python3
"""test_requirements_index.py -- a requirements file that pins a local-version build must name where to get it.

    python -I test_requirements_index.py        # exit 0 only if every check holds

WHY. A pin such as `torch==2.14.1+cpu` carries a local version label (`+cpu`). PyPI does not host local versions, so
`pip install -r requirements.txt` in a clean environment cannot resolve it unless the SAME file names the index that
serves it (for the PyTorch CPU builds: `--extra-index-url https://download.pytorch.org/whl/cpu`). Until 2026-11-14
requirements.txt carried the two `+cpu` pins and no index line, and a clean install failed.

WHAT IT CHECKS. Every requirements*.txt in the repository: if it holds a `==<version>+<label>` pin, it must also
hold an index line (`--extra-index-url`, `--index-url`, `-i`, `--find-links` or `-f`, each with a value). Driven
both ways first, in the repo's style: the rule is shown to fail on a synthetic file with the pin and no index line,
and to pass once the line is added, before the shipped files are read.

WHAT IT CANNOT SEE. It reads text only: no pip, no network. It does not know whether the named index really serves
the pinned version, only that the file no longer relies on PyPI for a build PyPI cannot hold.

CI runs this file (.github/workflows/tests.yml). Standard library only.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP_DIR = {".git", "__pycache__", "node_modules", ".venv", "venv", ".trash", ".pytest_cache", "data"}

# `name==1.2.3+label`, optionally with extras; comments and environment markers after it are ignored.
LOCAL_PIN = re.compile(r"^\s*([A-Za-z0-9._-]+(?:\[[^\]]*\])?)\s*==\s*([^\s;#+]+\+[A-Za-z0-9.]+)")
INDEX_LINE = re.compile(r"^\s*(--extra-index-url|--index-url|-i|--find-links|-f)(\s+|=)\S+")

FAILURES = []


def check(cond, label):
    print(("ok   " if cond else "FAIL ") + label)
    if not cond:
        FAILURES.append(label)


def local_pins(text):
    """The `name==version+label` pins in a requirements file's text, as written."""
    return ["%s==%s" % m.groups() for m in (LOCAL_PIN.match(line) for line in text.splitlines()) if m]


def has_index_line(text):
    return any(INDEX_LINE.match(line) for line in text.splitlines())


def unresolvable(text):
    """The local-version pins this file cannot resolve from PyPI: all of them when it names no index, else none."""
    return [] if has_index_line(text) else local_pins(text)


def requirements_files(root=ROOT):
    found = []
    for d, ds, fs in os.walk(root):
        ds[:] = [x for x in ds if x not in SKIP_DIR]
        for f in fs:
            if f.startswith("requirements") and f.endswith(".txt"):
                found.append(os.path.join(d, f))
    return sorted(found)


def main():
    # --- the rule, both ways, on synthetic text ---------------------------------------------------------------
    bare = "numpy==2.5.2\ntorch==2.14.1+cpu\ntorchvision==0.29.1+cpu  # cpu build\n"
    check(unresolvable(bare) == ["torch==2.14.1+cpu", "torchvision==0.29.1+cpu"],
          "S.0 a +cpu pin with no index line is reported (red)")
    check(unresolvable("--extra-index-url https://download.pytorch.org/whl/cpu\n" + bare) == [],
          "S.1 ...the same pins with an --extra-index-url line pass (green)")
    check(unresolvable("# --extra-index-url https://download.pytorch.org/whl/cpu\n" + bare) != [],
          "S.2 ...an index line that is only a comment does not count (red)")
    check(unresolvable("--extra-index-url\n" + bare) != [], "S.3 ...an index option with no address does not count (red)")
    check(unresolvable("numpy==2.5.2\npython-dateutil==2.9.0.post0\n") == [],
          "S.4 a file with no local-version pin needs no index line (green)")

    # --- the shipped files ----------------------------------------------------------------------------------
    files = requirements_files()
    check(bool(files), "R.0 at least one requirements*.txt was found to check")
    for path in files:
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        bad = unresolvable(text)
        check(not bad, "R.1 %s: every local-version pin has an index line in the same file%s"
              % (rel, "" if not bad else " -- no index line for " + ", ".join(bad)))

    print()
    if FAILURES:
        print("test_requirements_index: %d FAILED -- %s" % (len(FAILURES), "; ".join(FAILURES)))
        return 1
    print("test_requirements_index: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
