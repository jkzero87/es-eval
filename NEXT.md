Fix phase (reopened 2026-10-02). Status 2026-10-06: lever 2 is planned (results/lever2_plan.md, pre-registered) and not started; scripts/run_lever2.py does not exist yet. Next GPU job: write and commit scripts/run_lever2.py, then run lever 2 per the plan.

## End-of-session routine

After any long GPU job (benchmark run, eval, model server under load):

1. Run `journalctl -k --since today | grep Xid` and report the count (0 is the expected answer).
2. If any Xid appears, append one line per event to `~/local-llm-lab/notes/gpu-xid-log.md`
   (create it if missing): date and time, Xid number, and the job that was running
   (script/command and model). **No GPU UUIDs, PDIs or serial numbers** (that repo is public).
   Then commit and push local-llm-lab.
