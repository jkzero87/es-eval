#!/usr/bin/env python3
"""Reasoning / answer token gap vs en for a benchmark, MGSM alongside. Offline.

For each benchmark (raw file + its *_token_split.jsonl from
mgsm_token_split.py), on ids present in en, es and zh:
  - mean reasoning tokens per language; mean per-id (x − en) gap, median
    per-id gap, ratio mean x / mean en, paired Wilcoxon (exact p)
  - final answer: mean tokens, mean characters, tokens per character
    (Σ/Σ), and the answer gap split with the midpoint rule into "says more"
    (more characters) vs "costs more per character", as in latency_breakdown.md
Prints a markdown section (default: Belebele next to MGSM).
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from latency_breakdown import wilcoxon  # noqa: E402  (self-checked exact signed-rank)

R = Path(__file__).resolve().parents[1] / "results"
LANGS = ["en", "es", "zh"]


def load(path):
    return {(r["id"], r["lang"]): r for r in map(json.loads, path.open(encoding="utf-8")) if r}


def bench(name, raw_path, split_path):
    raw, split = load(raw_path), load(split_path)
    ids = sorted({i for i, _ in split if all((i, l) in split and (i, l) in raw for l in LANGS)})
    s = {}
    for l in LANGS:
        reas = [split[(i, l)]["reasoning_tokens"] for i in ids]
        ans = [split[(i, l)]["answer_tokens"] for i in ids]
        chars = [len(raw[(i, l)].get("content") or "") for i in ids]
        s[l] = dict(reas=reas, ans=ans, chars=chars, tpc=sum(ans) / sum(chars))
    out = {"name": name, "n": len(ids), "s": s}
    for x in ("es", "zh"):
        e, o = s["en"], s[x]
        d = [b - a for a, b in zip(e["reas"], o["reas"])]
        _, _, _, p, _ = wilcoxon(d)
        c_e, c_o = statistics.mean(e["chars"]), statistics.mean(o["chars"])
        da = statistics.mean(o["ans"]) - statistics.mean(e["ans"])
        more = (c_o - c_e) * (e["tpc"] + o["tpc"]) / 2
        cost = (o["tpc"] - e["tpc"]) * (c_e + c_o) / 2
        assert abs(more + cost - da) < 1e-6 * max(1, abs(da))
        out[x] = dict(gap=statistics.mean(d), median=statistics.median(d),
                      ratio=statistics.mean(o["reas"]) / statistics.mean(e["reas"]), p=p,
                      dans=da, more=more, cost=cost, dchars=c_o - c_e)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", default="Belebele")
    ap.add_argument("--raw", type=Path, default=R / "belebele_raw.jsonl")
    ap.add_argument("--split", type=Path, default=R / "belebele_token_split.jsonl")
    args = ap.parse_args()
    bs = [bench("MGSM", R / "mgsm_raw.jsonl", R / "mgsm_token_split.jsonl"),
          bench(args.name, args.raw, args.split)]

    p = print
    p(f"## Reasoning-token gap: {args.name} vs MGSM\n")
    p("Exact token counts via `/tokenize` (`mgsm_token_split.py`). Ids present in en, es and zh.\n")
    p("| | " + " | ".join(f"{b['name']} (n={b['n']})" for b in bs) + " |")
    p("|---|" + "---:|" * len(bs))
    for l in LANGS:
        p(f"| mean reasoning tokens, {l} | " + " | ".join(f"{statistics.mean(b['s'][l]['reas']):.1f}" for b in bs) + " |")
    for x in ("es", "zh"):
        p(f"| **{x} − en reasoning gap (mean of per-id)** | " + " | ".join(f"**{b[x]['gap']:+.1f}**" for b in bs) + " |")
        p(f"| {x} / en reasoning ratio | " + " | ".join(f"{b[x]['ratio']:.2f}" for b in bs) + " |")
        p(f"| median per-id {x} − en gap | " + " | ".join(f"{b[x]['median']:+.1f}" for b in bs) + " |")
        p(f"| Wilcoxon exact p ({x} vs en) | " + " | ".join(f"{b[x]['p']:.2g}" for b in bs) + " |")
    p("\n### Final-answer part\n")
    p("| | " + " | ".join(b["name"] for b in bs) + " |")
    p("|---|" + "---:|" * len(bs))
    for l in LANGS:
        p(f"| mean answer tokens / characters, {l} | " + " | ".join(
            f"{statistics.mean(b['s'][l]['ans']):.0f} / {statistics.mean(b['s'][l]['chars']):.0f}" for b in bs) + " |")
        p(f"| answer tokens per character, {l} | " + " | ".join(f"{b['s'][l]['tpc']:.3f}" for b in bs) + " |")
    for x in ("es", "zh"):
        p(f"| {x} − en answer tokens | " + " | ".join(f"{b[x]['dans']:+.1f}" for b in bs) + " |")
        p(f"| … says more ({x} − en characters × mean tok/char) | " + " | ".join(
            f"{b[x]['more']:+.1f} ({b[x]['dchars']:+.0f} chars)" for b in bs) + " |")
        p(f"| … costs more per character | " + " | ".join(f"{b[x]['cost']:+.1f}" for b in bs) + " |")
    p("\nThe two answer sub-rows add up to the answer gap exactly (midpoint rule). zh characters are not "
      "comparable with Latin-script characters, so for zh that split is arithmetic only.")


if __name__ == "__main__":
    main()
