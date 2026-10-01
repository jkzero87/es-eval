#!/usr/bin/env python3
"""ETA for a running benchmark: eta.py <raw.jsonl> <target> [--log FILE] [--window N]

Raw records carry no timestamp, so timing comes from the runner's log
(results/<bench>_run.log by default, '<bench>' being the raw file name up to
'_raw'): the '[ts] (n/m) id=...' progress lines written after the latest run
start. If the log is missing or has fewer than 2 such lines, it falls back to
the summed 'wall' of the last records (request time only, so optimistic).

Prints records/hour and mean completion tokens over the last N records
(default 30), unique id+lang done vs target, and the estimated finish time.
Read-only; never talks to the server.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROGRESS = re.compile(r"^\[(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)\] \(\d+/\d+\) id=")
RUN_START = re.compile(r"^\[[^]]+\] .*\bdone=\d+ pending=\d+ total=\d+")


def load_records(raw):
    recs, seen = [], set()
    with raw.open(encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                key = (rec["id"], rec["lang"])
            except (json.JSONDecodeError, KeyError):
                continue
            if key not in seen:
                seen.add(key)
                recs.append(rec)
    return recs


def log_times(log):
    """Timestamps of progress lines since the latest run start in LOG."""
    times = []
    with log.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if RUN_START.match(line):
                times = []
            elif m := PROGRESS.match(line):
                times.append(datetime.fromisoformat(m[1]))
    return times


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("raw", type=Path)
    ap.add_argument("target", type=int)
    ap.add_argument("--log", type=Path, help="runner log (default: <bench>_run.log next to RAW)")
    ap.add_argument("--window", type=int, default=30, help="records to average over (default 30)")
    args = ap.parse_args()

    recs = load_records(args.raw) if args.raw.exists() else []
    done = len(recs)
    remaining = max(args.target - done, 0)
    last = recs[-args.window:]
    tokens = [(r.get("usage") or {}).get("completion_tokens") for r in last]
    tokens = [t for t in tokens if isinstance(t, (int, float))]

    log = args.log or args.raw.with_name(args.raw.name.split("_raw")[0] + "_run.log")
    times = log_times(log)[-args.window:] if log.exists() else []
    if len(times) >= 2 and times[-1] > times[0]:
        sec_per_rec = (times[-1] - times[0]).total_seconds() / (len(times) - 1)
        anchor, source = times[-1], f"{log.name}, last {len(times)} progress lines"
    elif last and all(isinstance(r.get("wall"), (int, float)) for r in last):
        sec_per_rec = sum(r["wall"] for r in last) / len(last)
        anchor = datetime.fromtimestamp(args.raw.stat().st_mtime)
        source = f"summed 'wall' of last {len(last)} records (no usable log; optimistic)"
    else:
        sys.exit(f"{args.raw}: {done}/{args.target} done; not enough timing data for an ETA")

    print(f"file          {args.raw}")
    print(f"done          {done}/{args.target} unique id+lang ({100 * done / args.target:.1f}%)")
    print(f"rate          {3600 / sec_per_rec:.0f} records/h ({sec_per_rec:.1f} s/record; {source})")
    if tokens:
        print(f"completion    {sum(tokens) / len(tokens):.0f} tokens mean over last {len(tokens)}")
    if remaining == 0:
        print("finish        complete")
    else:
        finish = anchor + timedelta(seconds=remaining * sec_per_rec)
        left = finish - datetime.now()
        print(f"finish        {finish:%Y-%m-%d %H:%M} ({remaining} left, "
              f"~{max(left.total_seconds(), 0) / 3600:.1f} h from now; last record {anchor:%H:%M:%S})")


if __name__ == "__main__":
    main()
