#!/usr/bin/env python3
"""Offline test of score_proxlite.py (--subset, category-weighted accuracy).

Fake records in a temp dir; scorers run in-process with sockets blocked and
--no-tokenize. Compares against the committed (HEAD) scorer:
  - without --subset the old output is unchanged apart from the new weighted
    table and the per-category 'full n' column;
  - a subset skewed toward one category gives w_acc != acc;
  - McNemar paired counts are identical to HEAD (no weighting) and to counts
    computed independently here;
  - --subset drops unlisted ids and ids missing a language;
  - the *_keepdone.txt warning appears first without --subset, not with it.
"""
import contextlib
import io
import json
import random
import re
import runpy
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _no_net(*a, **k):
    raise RuntimeError("network blocked in test")


socket.create_connection = _no_net
socket.socket.connect = _no_net

FULL = {
    "biology": 36, "business": 40, "chemistry": 56, "computer science": 20,
    "economics": 42, "engineering": 48, "health": 35, "history": 19, "law": 48,
    "math": 68, "other": 46, "philosophy": 25, "physics": 65, "psychology": 40,
}
LANGS = ["en", "es", "zh"]


def fake_records():
    """Business ids (1..40) are ~all right, every other category ~all wrong;
    langs disagree on a few ids so McNemar has discordant pairs."""
    rng = random.Random(7)
    recs, ok, cat_of = [], {}, {}
    qid = 1
    for cat, n in FULL.items():
        for _ in range(n):
            cat_of[qid] = cat
            for lang in LANGS:
                p = 0.9 if cat == "business" else 0.15
                if lang == "zh":
                    p -= 0.1
                good = rng.random() < p
                gold = rng.choice("ABCD")
                pred = gold if good else "ABCD"[("ABCD".index(gold) + 1) % 4]
                recs.append({"id": qid, "lang": lang, "gold": gold, "category": cat,
                             "content": f"Reasoning...\nAnswer: {pred}", "usage": {"completion_tokens": 100}})
                ok[(qid, lang)] = good
            qid += 1
    return recs, ok, cat_of


def run(scorer, argv):
    out = io.StringIO()
    sys.argv = [scorer.name, *argv]
    sys.path.insert(0, str(scorer.parent))
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            runpy.run_path(str(scorer), run_name="__main__")
    finally:
        sys.path.pop(0)
        sys.modules.pop("score_mgsm", None)
    return out.getvalue()


def section(text, title):
    lines = text.splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith(f"=== {title}"))
    j = next((k for k in range(i + 1, len(lines)) if lines[k].startswith("===")), len(lines))
    return [l for l in lines[i:j] if l.strip()]


def mcnemar_rows(text):
    return section(text, "Paired vs en")


FAIL = []
TMPDIRS = []


def check(desc, cond):
    print(f"  {'ok  ' if cond else 'FAIL'} {desc}")
    if not cond:
        FAIL.append(desc)


def main():
    tmp = Path(tempfile.mkdtemp())
    TMPDIRS.append(tmp)
    (tmp / "old").mkdir()
    (tmp / "old" / "score_proxlite.py").write_text(
        subprocess.run(["git", "-C", str(HERE.parent), "show", "HEAD:scripts/score_proxlite.py"],
                       capture_output=True, text=True, check=True).stdout)
    (tmp / "old" / "score_mgsm.py").write_text((HERE / "score_mgsm.py").read_text())
    old, new = tmp / "old" / "score_proxlite.py", HERE / "score_proxlite.py"

    res = tmp / "results"
    res.mkdir()
    raw = res / "proxlite_raw.jsonl"
    recs, ok, cat_of = fake_records()
    # Subset skewed toward business: 30 business ids + 1 per other category,
    # plus one listed id that lacks zh (must be dropped).
    business = [q for q, c in cat_of.items() if c == "business"]
    others = [next(q for q, c in cat_of.items() if c == cat) for cat in FULL if cat != "business"]
    missing_zh = next(q for q, c in cat_of.items() if c == "math" and q not in others)
    subset = sorted(business[:30] + others + [missing_zh])
    recs = [r for r in recs if not (r["id"] == missing_zh and r["lang"] == "zh")]
    raw.write_text("".join(json.dumps(r) + "\n" for r in recs))
    sub = res / f"proxlite_subset_{len(subset)}_keepdone.txt"
    sub.write_text("".join(f"{q}\n" for q in subset))
    base = ["--raw", str(raw), "--no-tokenize"]

    print("== without --subset vs HEAD (no keepdone file)")
    sub_tmp = sub.rename(res / "subset.txt")
    o_old, o_new = run(old, base), run(new, base)
    stripped = re.sub(r"\n\n=== Category-weighted accuracy.*?(?=\n\n===)", "", o_new, flags=re.S)
    cat_rows = set(section(o_new, "Per-category")[1:])  # header + rows, not the title
    stripped = "\n".join(l[:-8] if l in cat_rows else l for l in stripped.splitlines()) + "\n"
    check("output = HEAD output + weighted table + 'full n' column", stripped == o_old)
    check("no warning without a keepdone file", "WARNING" not in o_new)
    check("McNemar rows identical to HEAD", mcnemar_rows(o_old) == mcnemar_rows(o_new))
    sub = sub_tmp.rename(sub)

    print("== keepdone warning")
    o_warn = run(new, base)
    check("warning is the first line without --subset", o_warn.splitlines()[0].startswith("WARNING:"))
    o_sub = run(new, base + ["--subset", str(sub)])
    check("no warning with --subset", "WARNING" not in o_sub)

    print("== --subset (skewed toward business)")
    print("\n".join("    " + l for l in section(o_sub, "Category-weighted")))
    kept = set(subset) - {missing_zh}
    check(f"scores {3 * len(kept)} records (listed ids with all 3 langs)",
          f"scored {3 * len(kept)} records" in o_sub)
    for lang in LANGS:
        row = next(l for l in section(o_sub, "Category-weighted") if l.startswith(lang + " "))
        n, acc, wacc = row.split()[1:4]
        exp_acc = sum(ok[(q, lang)] for q in kept) / len(kept)
        per_cat = {}
        for q in kept:
            per_cat.setdefault(cat_of[q], []).append(ok[(q, lang)])
        exp_w = sum(FULL[c] / 588 * sum(v) / len(v) for c, v in per_cat.items())
        check(f"{lang}: acc {acc} = {exp_acc:.4f}, w_acc {wacc} = {exp_w:.4f}, and they differ",
              int(n) == len(kept) and f"{exp_acc:.4f}" == acc and f"{exp_w:.4f}" == wacc
              and abs(float(acc) - float(wacc)) > 0.05)

    print("== McNemar counts with --subset: raw paired counts, independent of weighting")
    for other in ("es", "zh"):
        row = next(l for l in mcnemar_rows(o_sub) if l.startswith(f"{other} vs en"))
        got = [int(x) for x in row.split()[3:8]]
        en_only = sum(ok[(q, "en")] and not ok[(q, other)] for q in kept)
        oth_only = sum(ok[(q, other)] and not ok[(q, "en")] for q in kept)
        both = sum(ok[(q, "en")] and ok[(q, other)] for q in kept)
        exp = [len(kept), both, len(kept) - both - en_only - oth_only, en_only, oth_only]
        check(f"{other} vs en counts {got} = {exp}", got == exp)
    # Same records, scored by HEAD (no weighting at all): identical paired rows.
    sub_raw = tmp / "sub_only.jsonl"
    sub_raw.write_text("".join(json.dumps(r) + "\n" for r in recs if r["id"] in kept))
    o_head_sub = run(old, ["--raw", str(sub_raw), "--no-tokenize"])
    check("McNemar rows identical to HEAD on the same subset", mcnemar_rows(o_head_sub) == mcnemar_rows(o_sub))

    print("ALL OK" if not FAIL else f"{len(FAIL)} FAILURES")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    try:
        main()
    finally:
        for d in TMPDIRS:
            shutil.rmtree(d, ignore_errors=True)
