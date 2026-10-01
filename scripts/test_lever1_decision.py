#!/usr/bin/env python3
"""Offline test of lever1_decision.py on synthetic "plain" runs built from the
baseline (results/mgsm_raw.jsonl + results/mgsm_token_split.jsonl):

  baseline as plain        -> (a) FAIL, (b) PASS, (c) PASS, (d) FAIL
  both langs x0.45         -> (a) PASS but (d) FAIL: the case (d) was added for
  es = 1.2 x en            -> all PASS, SUCCESS
  3 es answers flipped     -> (b) FAIL (235 < 236 even though McNemar p > 0.05)
  8 en answers flipped     -> (c) FAIL (McNemar p <= 0.05)
  one plain record missing -> exit 2, no verdict
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

base = [json.loads(l) for l in (R / "mgsm_raw.jsonl").open(encoding="utf-8")]
split = [json.loads(l) for l in (R / "mgsm_token_split.jsonl").open(encoding="utf-8")]
base = [r for r in base if r["lang"] in ("en", "es")]
split = [r for r in split if r["lang"] in ("en", "es")]
en_tok = {r["id"]: r["reasoning_tokens"] for r in split if r["lang"] == "en"}

sys.path.insert(0, str(HERE))
from score_mgsm import correct  # noqa: E402

FAIL = []


def run(name, raw, spl):
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / "raw.jsonl").write_text("".join(json.dumps(r) + "\n" for r in raw))
        (tmp / "split.jsonl").write_text("".join(json.dumps(r) + "\n" for r in spl))
        p = subprocess.run([PY, str(HERE / "lever1_decision.py"), "--raw", str(tmp / "raw.jsonl"),
                            "--split", str(tmp / "split.jsonl")], capture_output=True, text=True)
    finally:
        shutil.rmtree(tmp)
    res = dict(re.findall(r"^\((\w)\) .* (PASS|FAIL)$", p.stdout, re.M))
    verdict = next((l for l in p.stdout.splitlines() if l.startswith(("VERDICT", "NO VERDICT"))), "")
    return p.returncode, res, verdict, p.stdout


def check(name, got, want, out):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {name}: {got}" + ("" if ok else f" (want {want})"))
    if not ok:
        FAIL.append(name)
        print(out)


def flip(raw, lang, k):
    """Make the first k correct answers in LANG wrong."""
    out, n = [], 0
    for r in raw:
        r = dict(r)
        if r["lang"] == lang and n < k and correct(r):
            r["content"] = "Answer: -1"
            n += 1
        out.append(r)
    return out


def scaled(f_en, f_es):
    return [dict(r, reasoning_tokens=round(r["reasoning_tokens"] * (f_en if r["lang"] == "en" else f_es)))
            for r in split]


cases = [
    ("baseline as plain", base, split, (0, {"a": "FAIL", "b": "PASS", "c": "PASS", "d": "FAIL"})),
    ("both langs x0.45 (proportional)", base, scaled(0.45, 0.45),
     (0, {"a": "PASS", "b": "PASS", "c": "PASS", "d": "FAIL"})),
    ("es = 1.2 x en", base, [dict(r, reasoning_tokens=round(1.2 * en_tok[r["id"]])) if r["lang"] == "es" else r
                             for r in split], (0, {"a": "PASS", "b": "PASS", "c": "PASS", "d": "PASS"})),
    ("3 es answers flipped", flip(base, "es", 3), split, (0, {"a": "FAIL", "b": "FAIL", "c": "PASS", "d": "FAIL"})),
    ("8 en answers flipped", flip(base, "en", 8), split, (0, {"a": "FAIL", "b": "PASS", "c": "FAIL", "d": "FAIL"})),
]
for name, raw, spl, want in cases:
    code, res, verdict, out = run(name, raw, spl)
    check(name, (code, res), want, out)
    if name == "es = 1.2 x en":
        check("  verdict SUCCESS", verdict.startswith("VERDICT: SUCCESS"), True, out)
    if name == "both langs x0.45 (proportional)":
        check("  verdict FAIL on (d)", "fails on (d)" in verdict, True, out)

code, res, verdict, out = run("missing", base[1:], split)
check("one plain record missing -> exit 2, no verdict", (code, verdict.startswith("NO VERDICT")), (2, True), out)

print("ALL OK" if not FAIL else f"{len(FAIL)} FAILURES")
sys.exit(1 if FAIL else 0)
