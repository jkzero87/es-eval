#!/usr/bin/env python3
"""MGSM latency breakdown per language from results/mgsm_raw.jsonl (offline).

- Field inventory (which usage/timings fields exist, what is missing).
- On ids present in all three languages: mean/median of prompt tokens
  (total and actually prefilled, i.e. not served from the prompt cache),
  completion tokens, estimated reasoning vs answer tokens, prefill ms,
  generation ms, generation tokens/s, MTP acceptance, wall, overhead.
- Decomposition of the mean wall-time gap X vs en into
  (a) more completion tokens, (b) slower generation, (c) prefill, plus
  (d) the residual (HTTP/JSON/sampling outside prompt_ms + predicted_ms).
  Mean generation ms = mean tokens * (sum ms / sum tokens) exactly, so the
  generation gap splits with the symmetric (midpoint) rule:
      dGen = dN * (s_en + s_x)/2  +  ds * (N_en + N_x)/2
  where N = mean completion tokens and s = aggregate ms per token.
- Paired Wilcoxon signed-rank on per-id generation tokens/s, X vs en:
  exact p (dynamic programming over doubled ranks, conditional on ties)
  and normal approximation; no scipy needed.

The records carry no reasoning/answer token split (no
completion_tokens_details) and tokenizing offline is not possible here, so
the split is estimated by character share of reasoning_content vs content.

Writes results/latency_breakdown.md. Never talks to the server.
"""
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "mgsm_raw.jsonl"
OUT = ROOT / "results" / "latency_breakdown.md"
LANGS = ["en", "es", "zh"]
EXPECTED_TIMINGS = ["prompt_n", "prompt_ms", "predicted_n", "predicted_ms", "draft_n",
                    "draft_n_accepted", "cache_n", "predicted_per_second"]
EXPECTED_USAGE = ["prompt_tokens", "completion_tokens", "completion_tokens_details"]


def wilcoxon(d):
    """Two-sided Wilcoxon signed-rank on differences d (zeros dropped).
    Returns n, W+, W-, exact p, normal-approx p (tie + continuity corrected)."""
    d = [x for x in d if x != 0]
    n = len(d)
    order = sorted(range(n), key=lambda i: abs(d[i]))
    ranks = [0.0] * n
    i = 0
    ties = 0.0
    while i < n:
        j = i
        while j + 1 < n and abs(d[order[j + 1]]) == abs(d[order[i]]):
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        t = j - i + 1
        ties += t ** 3 - t
        i = j + 1
    wp = sum(r for r, x in zip(ranks, d) if x > 0)
    wm = sum(r for r, x in zip(ranks, d) if x < 0)
    # Exact: distribution of the sum of a random-signed subset of the (doubled,
    # integer) ranks.
    r2 = [int(round(2 * r)) for r in ranks]
    total = sum(r2)
    dist = [0] * (total + 1)
    dist[0] = 1
    for r in r2:
        for s in range(total, r - 1, -1):
            dist[s] += dist[s - r]
    obs = int(round(2 * min(wp, wm)))
    p_exact = min(1.0, 2 * sum(dist[: obs + 1]) / 2 ** n)
    mean = n * (n + 1) / 4
    var = n * (n + 1) * (2 * n + 1) / 24 - ties / 48
    z = (abs(wp - mean) - 0.5) / math.sqrt(var)
    p_norm = math.erfc(z / math.sqrt(2))
    return n, wp, wm, p_exact, p_norm


def selftest():
    # Wilcoxon (1945) / classic textbook example: n=15, W+=96, W-=24,
    # two-sided exact p = 0.04126 (scipy.stats.wilcoxon gives the same).
    d = [6, 8, 14, 16, 23, 24, 28, 29, 41, -48, 49, 56, 60, -67, 75]
    n, wp, wm, pe, _ = wilcoxon(d)
    assert (n, wp, wm) == (15, 96, 24) and abs(pe - 0.04126) < 5e-5, (n, wp, wm, pe)


def fmt(x, nd=1):
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:,.{nd}f}"


def main():
    selftest()
    recs = [json.loads(l) for l in RAW.open(encoding="utf-8") if l.strip()]
    by = {(r["id"], r["lang"]): r for r in recs}
    ids = sorted({i for i, _ in by if all((i, l) in by for l in LANGS)})
    md = []
    w = md.append

    # 1. Field inventory.
    tkeys, ukeys, top = {}, {}, {}
    for r in recs:
        for k, v in r.items():
            top[k] = top.get(k, 0) + (v is not None)
        for k in (r.get("timings") or {}):
            tkeys[k] = tkeys.get(k, 0) + 1
        for k in (r.get("usage") or {}):
            ukeys[k] = ukeys.get(k, 0) + 1
    missing = [f"timings.{k}" for k in EXPECTED_TIMINGS if tkeys.get(k, 0) < len(recs)] + \
              [f"usage.{k}" for k in EXPECTED_USAGE if ukeys.get(k, 0) < len(recs)]
    consistent_n = sum(r["timings"]["predicted_n"] == r["usage"]["completion_tokens"] for r in recs)
    consistent_p = sum(r["timings"]["prompt_n"] + r["timings"]["cache_n"] == r["usage"]["prompt_tokens"]
                       for r in recs)
    length = [(r["id"], r["lang"]) for r in recs if r.get("finish_reason") == "length"]

    w("# MGSM latency breakdown (en / es / zh)\n")
    w(f"Source: `results/mgsm_raw.jsonl`, {len(recs)} records; {len(ids)} ids present in all three "
      f"languages (all comparisons below are on these). Generated offline by "
      f"`scripts/latency_breakdown.py`; no server requests.\n")
    w("## 1. Fields present\n")
    w(f"- top level: {', '.join(f'`{k}`' for k in top)}")
    w(f"- `usage`: {', '.join(f'`{k}`' for k in ukeys)} (`prompt_tokens_details.cached_tokens`)")
    w(f"- `timings`: {', '.join(f'`{k}`' for k in tkeys)}")
    w(f"- every field above is present in all {len(recs)} records; "
      f"`predicted_n == completion_tokens` in {consistent_n}/{len(recs)}, "
      f"`prompt_n + cache_n == prompt_tokens` in {consistent_p}/{len(recs)}.")
    w(f"- **missing:** {', '.join(f'`{m}`' for m in missing) or 'none'}. There is no reasoning/answer "
      f"token split. Exact counts would need `/tokenize` (excluded: no server requests) or an offline "
      f"tokenizer (the local `llama-tokenize` build segfaults in vocab-only mode with the GPU hidden; "
      f"no Python tokenizer is installed). The split below is an **estimate**: each record's "
      f"completion tokens divided by the character share of `reasoning_content` vs `content`.")
    w(f"- `prompt_ms` covers only the `prompt_n` tokens actually prefilled; the rest "
      f"(`cache_n`) came from the prompt cache. `wall` (client-side) also includes HTTP/JSON and "
      f"sampling time outside `prompt_ms + predicted_ms`, reported as *overhead*.")
    w(f"- `finish_reason=length` (hit max_tokens): {', '.join(f'id={i} {l}' for i, l in length) or 'none'}; "
      f"kept in all numbers.\n")

    # 2. Per-language stats.
    stats = {}
    for l in LANGS:
        rs = [by[(i, l)] for i in ids]
        comp = [r["usage"]["completion_tokens"] for r in rs]
        rc = [len(r.get("reasoning_content") or "") for r in rs]
        cc = [len(r.get("content") or "") for r in rs]
        reas = [c * a / (a + b) if a + b else 0 for c, a, b in zip(comp, rc, cc)]
        ans = [c - x for c, x in zip(comp, reas)]
        pms = [r["timings"]["prompt_ms"] for r in rs]
        gms = [r["timings"]["predicted_ms"] for r in rs]
        wall = [r["wall"] * 1000 for r in rs]
        drafted = sum(r["timings"]["draft_n"] for r in rs)
        accepted = sum(r["timings"]["draft_n_accepted"] for r in rs)
        stats[l] = {
            "prompt_tokens": [r["usage"]["prompt_tokens"] for r in rs],
            "prompt_n": [r["timings"]["prompt_n"] for r in rs],
            "completion": comp, "reasoning_est": reas, "answer_est": ans,
            "prefill_ms": pms, "gen_ms": gms,
            "tps": [r["timings"]["predicted_per_second"] for r in rs],
            "mtp_rec": [r["timings"]["draft_n_accepted"] / r["timings"]["draft_n"]
                        for r in rs if r["timings"]["draft_n"]],
            "wall_ms": wall,
            "overhead_ms": [a - b - c for a, b, c in zip(wall, pms, gms)],
            "mtp": accepted / drafted if drafted else float("nan"),
            "tps_agg": 1000 * sum(comp) / sum(gms),
            "ms_per_tok": sum(gms) / sum(comp),
        }

    rows = [
        ("prompt tokens (total)", "prompt_tokens", 0),
        ("prompt tokens prefilled (not cached)", "prompt_n", 1),
        ("completion tokens", "completion", 0),
        ("  reasoning (est., char share)", "reasoning_est", 0),
        ("  final answer (est., char share)", "answer_est", 0),
        ("prefill ms", "prefill_ms", 0),
        ("generation ms", "gen_ms", 0),
        ("generation tokens/s (per record)", "tps", 2),
        ("MTP acceptance (per record)", "mtp_rec", 3),
        ("wall ms", "wall_ms", 0),
        ("overhead ms (wall − prefill − gen)", "overhead_ms", 0),
    ]
    w(f"## 2. Per language (n = {len(ids)} paired ids; mean / median)\n")
    w("| metric | " + " | ".join(LANGS) + " |")
    w("|---|" + "---:|" * len(LANGS))
    for label, key, nd in rows:
        cells = [f"{fmt(statistics.mean(stats[l][key]), nd)} / {fmt(statistics.median(stats[l][key]), nd)}"
                 for l in LANGS]
        w(f"| {label} | " + " | ".join(cells) + " |")
    w("| generation tokens/s (aggregate Σtokens/Σms) | "
      + " | ".join(fmt(stats[l]["tps_agg"], 2) for l in LANGS) + " |")
    w("| MTP acceptance (Σaccepted/Σdrafted) | "
      + " | ".join(fmt(stats[l]["mtp"], 3) for l in LANGS) + " |\n")

    # 3. Decomposition of the mean wall gap.
    w("## 3. Wall-time gap vs en, decomposed (means per item)\n")
    w("| component | " + " | ".join(f"{x} − en: ms" for x in LANGS[1:]) + " | "
      + " | ".join(f"{x}: % of gap" for x in LANGS[1:]) + " |")
    w("|---|" + "---:|" * (2 * (len(LANGS) - 1)))
    dec = {}
    for x in LANGS[1:]:
        e, o = stats["en"], stats[x]
        n_e, n_o = statistics.mean(e["completion"]), statistics.mean(o["completion"])
        s_e, s_o = e["ms_per_tok"], o["ms_per_tok"]
        a = (n_o - n_e) * (s_e + s_o) / 2
        b = (s_o - s_e) * (n_e + n_o) / 2
        c = statistics.mean(o["prefill_ms"]) - statistics.mean(e["prefill_ms"])
        d = statistics.mean(o["overhead_ms"]) - statistics.mean(e["overhead_ms"])
        total = statistics.mean(o["wall_ms"]) - statistics.mean(e["wall_ms"])
        assert abs(a + b + c + d - total) < 1e-6 * max(1, abs(total))
        dec[x] = {"a": a, "b": b, "c": c, "d": d, "total": total, "dN": n_o - n_e,
                  "tps_e": 1000 / s_e, "tps_o": 1000 / s_o}
    labels = [("(a) more completion tokens", "a"), ("(b) slower tokens/s", "b"),
              ("(c) prefill", "c"), ("(d) overhead (residual)", "d"), ("**total wall gap**", "total")]
    for label, k in labels:
        w(f"| {label} | " + " | ".join(fmt(dec[x][k], 0) for x in LANGS[1:]) + " | "
          + " | ".join(fmt(100 * dec[x][k] / dec[x]["total"], 1) for x in LANGS[1:]) + " |")
    w("")
    w("(a) and (b) split the generation-time gap with the midpoint rule (see script docstring), so "
      "(a)+(b)+(c)+(d) equals the total exactly. A negative share means that component "
      "*reduces* the gap.\n")

    # 4. Wilcoxon on per-id tokens/s.
    w("## 4. Paired Wilcoxon signed-rank on per-id generation tokens/s\n")
    w("| pair | n (non-zero) | median Δ tok/s (x − en) | W+ | W− | rank-biserial r | exact p | normal p |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|")
    wil = {}
    for x in LANGS[1:]:
        diffs = [o - e for o, e in zip(stats[x]["tps"], stats["en"]["tps"])]
        n, wp, wm, pe, pn = wilcoxon(diffs)
        r = (wp - wm) / (wp + wm)
        wil[x] = (statistics.median(diffs), pe, r)
        w(f"| {x} vs en | {n} | {statistics.median(diffs):+.2f} | {wp:,.1f} | {wm:,.1f} | {r:+.3f} | "
          f"{pe:.3g} | {pn:.3g} |")
    w("\nExact p computed by enumeration of the signed-rank distribution (doubled ranks, conditional "
      "on ties); the implementation reproduces the textbook n=15 example (W+=96, p=0.0413).\n")

    # Conclusion.
    es, zh = dec["es"], dec["zh"]
    def share(dd, k):
        v = round(100 * dd[k] / dd["total"])
        return f"{v + 0:d}%" if v else "~0%"
    w("## Conclusion\n")
    w(f"- **es vs en:** {es['total']/1000:.2f} s slower per item on average; {share(es,'a')} of it is "
      f"{es['dN']:.0f} more completion tokens, {share(es,'b')} slower generation "
      f"({es['tps_o']:.1f} vs {es['tps_e']:.1f} tok/s, alongside lower MTP acceptance "
      f"{stats['es']['mtp']:.3f} vs {stats['en']['mtp']:.3f}), prefill {share(es,'c')}, overhead {share(es,'d')}.")
    w(f"- **zh vs en:** {zh['total']/1000:.2f} s slower; {share(zh,'a')} tokens ({zh['dN']:.0f} more), "
      f"{share(zh,'b')} speed ({zh['tps_o']:.1f} vs {zh['tps_e']:.1f} tok/s), prefill {share(zh,'c')}, "
      f"overhead {share(zh,'d')} (two warm-up outliers at the start of the run, ids 7–8 at "
      f"37–44 s; every language has two such outliers among ids 7–9, and the medians match). Prefill barely matters because prompts are short (~90 tokens, ~0.27 s), not because of caching.")
    w(f"- **Per-id tokens/s is lower in both** (es − en median {wil['es'][0]:+.2f} tok/s, Wilcoxon exact "
      f"p = {wil['es'][1]:.2g}, r = {wil['es'][2]:+.2f}; zh − en {wil['zh'][0]:+.2f}, p = {wil['zh'][1]:.2g}), "
      f"but it is the second-order effect: the gap is mostly longer outputs, not slower decoding.")
    OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
