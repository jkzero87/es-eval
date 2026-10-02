#!/usr/bin/env python3
"""Offline plumbing test of belebele_decision.py on the Belebele baseline only
(results/belebele_raw.jsonl + results/belebele_token_split.jsonl), no new run:

  baseline as treatment    -> (a) FAIL, (b) PASS, (c) PASS, (d) FAIL, (e) PASS
  one treatment missing    -> exit 2, no verdict
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE.parent / "results"
PY = sys.executable
FAIL = []


def run(raw, split):
    p = subprocess.run([PY, str(HERE / "belebele_decision.py"), "--raw", str(raw), "--split", str(split)],
                       capture_output=True, text=True)
    return p.returncode, dict(re.findall(r"^\((\w)\) .* (PASS|FAIL)$", p.stdout, re.M)), p.stdout


def check(name, got, want, out):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {name}: {got}" + ("" if ok else f" (want {want})"))
    if not ok:
        FAIL.append(name)
        print(out)


code, res, out = run(R / "belebele_raw.jsonl", R / "belebele_token_split.jsonl")
check("baseline as treatment", (code, res),
      (0, {"a": "FAIL", "b": "PASS", "c": "PASS", "d": "FAIL", "e": "PASS"}), out)

tmp = Path(tempfile.mkdtemp())
try:
    lines = (R / "belebele_raw.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
    drop = next(i for i, l in enumerate(lines) if json.loads(l)["lang"] == "es")
    (tmp / "raw.jsonl").write_text("".join(lines[:drop] + lines[drop + 1:]), encoding="utf-8")
    code, res, out = run(tmp / "raw.jsonl", R / "belebele_token_split.jsonl")
    check("one es treatment record missing -> exit 2", (code, out.startswith("NO VERDICT")), (2, True), out)
finally:
    shutil.rmtree(tmp)

print("ALL OK" if not FAIL else f"{len(FAIL)} FAILURES")
sys.exit(1 if FAIL else 0)
