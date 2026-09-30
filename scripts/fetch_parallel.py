#!/usr/bin/env python3
"""Fetch parallel datasets and save aligned jsonl files per language.

- facebook/belebele: configs eng_Latn, spa_Latn, zho_Hans, split test.
  Deduplicate passages by `link`; align by `link` (+ `question_number` for
  questions). Keep flores_passage and question.
- juletxara/mgsm: configs en, es, zh, split test; align by row index.
- Output: data/{source}_{lang}.jsonl with an `id` column.
- Asserts identical id sets across the three languages per source.
"""
import json
import sys
from pathlib import Path

from datasets import load_dataset, get_dataset_config_names

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def fail_with_error(dataset_name, config, err):
    print(f"ERROR: failed to load {dataset_name} config={config!r}: {err}", file=sys.stderr)
    try:
        names = get_dataset_config_names(dataset_name)
        print(f"Available configs for {dataset_name}: {names}", file=sys.stderr)
    except Exception as e:
        print(f"(could not list configs: {e})", file=sys.stderr)
    raise


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def fetch_belebele():
    """Load belebele in three languages, dedupe passages by link, align
    passages by link and questions by (link, question_number)."""
    langs = ["eng_Latn", "spa_Latn", "zho_Hans"]
    lang_short = {"eng_Latn": "en", "spa_Latn": "es", "zho_Hans": "zh"}

    raw = {}
    for lang in langs:
        try:
            raw[lang] = load_dataset("facebook/belebele", lang, split="test")
        except Exception as e:
            fail_with_error("facebook/belebele", lang, e)

    # Inspect columns of the first row
    sample = raw["eng_Latn"][0]
    print("belebele columns:", list(sample.keys()))
    passage_col = "flore_passage" if "flore_passage" in sample else "flores_passage"
    print("passage column:", passage_col)

    # Deduplicate by link: keep first occurrence per link, preserving order.
    deduped = {}
    for lang in langs:
        seen = set()
        out = []
        for row in raw[lang]:
            link = row["link"]
            if link in seen:
                continue
            seen.add(link)
            out.append(row)
        deduped[lang] = out
        print(f"  {lang}: {len(raw[lang])} rows -> {len(out)} unique links")

    # Links common to all three languages
    link_sets = [set(r["link"] for r in deduped[l]) for l in langs]
    common_links = sorted(set.intersection(*link_sets))
    print(f"  common links across en/es/zh: {len(common_links)}")

    # Question alignment key: (link, question_number)
    q_key = lambda r: (r["link"], r.get("question_number"))
    q_index = {lang: {} for lang in langs}
    for lang in langs:
        for row in deduped[lang]:
            k = q_key(row)
            if k not in q_index[lang]:
                q_index[lang][k] = row
    common_qkeys = sorted(set.intersection(*[set(q_index[l]) for l in langs]),
                          key=lambda k: (k[0], k[1] if k[1] is not None else 0))
    print(f"  aligned questions: {len(common_qkeys)}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for lang, short in lang_short.items():
        link_to_row = {r["link"]: r for r in deduped[lang]}
        out_path = DATA_DIR / f"belebele_{short}.jsonl"
        rows = []
        for i, link in enumerate(common_links, start=1):
            row = link_to_row[link]
            rows.append({
                "id": i,
                "link": link,
                "flores_passage": row.get(passage_col),
            })
        for k in common_qkeys:
            row = q_index[lang][k]
            rows.append({
                "id": f"q{row['link']}:{row.get('question_number')}",
                "link": k[0],
                "question_number": k[1],
                "flores_passage": row.get(passage_col),
                "question": row.get("question"),
            })
        write_jsonl(out_path, rows)
        print(f"  wrote {out_path.name}: {len(common_links)} passages + {len(common_qkeys)} questions")
    return common_links, common_qkeys


def fetch_mgsm():
    """Load juletxara/mgsm in three languages, align by row index."""
    langs = ["en", "es", "zh"]
    raw = {}
    for lang in langs:
        try:
            raw[lang] = load_dataset("juletxara/mgsm", lang, split="test")
        except Exception as e:
            fail_with_error("juletxara/mgsm", lang, e)

    counts = {l: len(raw[l]) for l in langs}
    print(f"mgsm row counts: {counts}")
    n = min(counts.values())
    if len(set(counts.values())) != 1:
        print("NOTE: row counts differ; aligning by index up to the min count", file=sys.stderr)

    print("mgsm columns:", list(raw["en"][0].keys()))

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for lang in langs:
        out_path = DATA_DIR / f"mgsm_{lang}.jsonl"
        rows = []
        for i in range(n):
            row = raw[lang][i]
            rec = {"id": i + 1}
            for col in raw[lang].column_names:
                v = row[col]
                if v is not None:
                    rec[col] = v
            rows.append(rec)
        write_jsonl(out_path, rows)
        print(f"  wrote {out_path.name}: {n} rows")
    return n


def verify_alignment(source):
    files = {
        "en": DATA_DIR / f"{source}_en.jsonl",
        "es": DATA_DIR / f"{source}_es.jsonl",
        "zh": DATA_DIR / f"{source}_zh.jsonl",
    }
    id_sets = {}
    for lang, path in files.items():
        with path.open(encoding="utf-8") as f:
            id_sets[lang] = {json.loads(line)["id"] for line in f}
    ok = id_sets["en"] == id_sets["es"] == id_sets["zh"]
    print(f"{source}: id sets identical across en/es/zh: {'OK' if ok else 'MISMATCH'} ({len(id_sets['en'])} ids)")
    if not ok:
        raise AssertionError(f"{source}: id sets differ across languages")
    return len(id_sets["en"])


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    links, qkeys = fetch_belebele()
    n_mgsm = fetch_mgsm()
    n_b = verify_alignment("belebele")
    n_m = verify_alignment("mgsm")
    print(f"row counts: belebele={n_b} (passages={len(links)}, questions={len(qkeys)}), mgsm={n_m}")


if __name__ == "__main__":
    main()
