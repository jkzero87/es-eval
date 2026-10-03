Fix phase (reopened 2026-10-02). First GPU job 2026-10-03: write and commit scripts/run_lever2.py, then run lever 2 per results/lever2_plan.md.

## End-of-session routine

After any long GPU job (benchmark run, eval, model server under load):

1. Run `journalctl -k --since today | grep Xid` and report the count (0 is the expected answer).
2. If any Xid appears, append one line per event to `~/local-llm-lab/notes/gpu-xid-log.md`
   (create it if missing): date and time, Xid number, and the job that was running
   (script/command and model). **No GPU UUIDs, PDIs or serial numbers** (that repo is public).
   Then commit and push local-llm-lab.
