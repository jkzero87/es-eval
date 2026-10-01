# Where things stand (2026-10-01, PC turned off at ~17:50)

The PC is turned off around 19:00 and nothing runs overnight: every run must
finish or be stopped by 18:55 (`scripts/stop_at.sh HH:MM PID`).

## Done
- MGSM 750/750 and Belebele 1464/1464 complete, scored and audited
  (`results/mgsm_audit.md`, `results/belebele_audit.md`; es causes "pending
  Juan's review").
- Latency breakdown with the exact reasoning/answer token split
  (`results/latency_breakdown.md`); reasoning-gap audit of the top 20 MGSM ids
  (`results/reasoning_gap_audit.md`).
- Belebele follow-up: the es−en reasoning gap is the same as on MGSM (+113.5 vs
  +114.4 tokens, ratio 1.49 vs 1.50).
- Lever 1 pre-registered (`results/lever1_plan.md`, criteria (a)–(d) incl. the
  binding ratio ≤ 1.25); runner, decision script and tests ready, not run yet.

## Stopped
- ProX-Lite: stopped cleanly at 17:48 by hand at **98/1764** records (last
  line intact; see `results/chain.log`). The gate kept the full run
  (projected 00:56, before the old 08:00 deadline), so there is no subset
  file. `run_proxlite.py` is resumable.

## Next
1. **Lever 1 first** (≈ 1.5 h, needs its own window: start by ~17:15 at the
   latest):
   `scripts/run_lever1.sh --dry-run`, then
   `setsid nohup scripts/run_lever1.sh >> results/lever1_run.log 2>&1 < /dev/null &`
   plus `scripts/stop_at.sh 18:55 <PID>`. Verdict in
   `results/lever1_decision.txt`; no prompt-tuning loops.
2. **Then ProX-Lite:** ~1,666 records left at 16–23 s each (id 80 took 5 min)
   ≈ 8–11 h, so more than one daytime window. Either resume the full run over
   two days (`run_proxlite.py`, each day with `stop_at.sh 18:55`), or run a
   subset that fits: `run_proxlite.py --limit N --keep-done` keeps the 32
   finished triplets; score with `score_proxlite.py --subset`, which also
   reports category-weighted accuracy.
3. Juan's review of the es audit causes (MGSM and Belebele).
