**Closed 2026-10-07.** Fix phase closed: prompt (lever 1, FAIL) and translation (lever 2, stopped early by decision at 130/250, 2.15 × en tokens vs a 1.10 × bar; see results/translation_floor.md) levers are ruled out. No further runs planned in this repo. Next step: fine-tuning in https://github.com/jkzero87/es-reasoning-finetune.

(If lever 2 were ever resumed for completeness: `HF_HOME=/home/jkzero/es-eval/.hf_cache setsid nohup .venv/bin/python -u scripts/run_lever2.py >> results/lever2_run.log 2>&1 < /dev/null &` skips the 130 done ids; then `.venv/bin/python scripts/lever2_decision.py`.)

## End-of-session routine

After any long GPU job (benchmark run, eval, model server under load):

1. Run `journalctl -k --since today | grep Xid` and report the count (0 is the expected answer).
2. If any Xid appears, append one line per event to `~/local-llm-lab/notes/gpu-xid-log.md`
   (create it if missing): date and time, Xid number, and the job that was running
   (script/command and model). **No GPU UUIDs, PDIs or serial numbers** (that repo is public).
   Then commit and push local-llm-lab.
