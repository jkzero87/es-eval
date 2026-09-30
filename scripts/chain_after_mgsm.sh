#!/usr/bin/env bash
# Wait for the MGSM run to exit, then chain the next job.
#   - 750 unique (id, lang) records in results/mgsm_raw.jsonl -> launch run_belebele.py
#   - otherwise -> relaunch run_mgsm.py (it resumes) and exit
# Both are launched detached with setsid nohup. Log: results/chain.log
#
# Usage (detached):
#   cd /home/jkzero/es-eval && setsid nohup scripts/chain_after_mgsm.sh [PID] >> results/chain.log 2>&1 < /dev/null &
set -u

ROOT=/home/jkzero/es-eval
PID=${1:-23294}
EXPECTED=750
cd "$ROOT" || exit 1

log() { echo "[$(date +%Y-%m-%dT%H:%M:%S)] chain: $*"; }

# Match on the command line too, so a reused PID doesn't keep us waiting forever.
alive() { tr '\0' ' ' 2>/dev/null < "/proc/$PID/cmdline" | grep -q run_mgsm; }

log "watching PID $PID (poll every 30 s)"
while alive; do
    sleep 30
done
log "PID $PID has exited"

n=$(.venv/bin/python - <<'EOF'
import json
seen = set()
with open("results/mgsm_raw.jsonl", encoding="utf-8") as f:
    for line in f:
        try:
            rec = json.loads(line)
            seen.add((rec["id"], rec["lang"]))
        except (json.JSONDecodeError, KeyError):
            pass
print(len(seen))
EOF
)
log "mgsm_raw.jsonl: ${n:-?} unique id+lang records (expected $EXPECTED)"

# Never start a second copy next to one that is already running.
if pgrep -f "scripts/run_(mgsm|belebele)\.py" >/dev/null; then
    log "a run_mgsm/run_belebele process is already running; launching nothing"
    pgrep -af "scripts/run_(mgsm|belebele)\.py"
    exit 1
fi

if [ "${n:-0}" -eq "$EXPECTED" ]; then
    log "MGSM complete; launching run_belebele.py"
    HF_HOME=/home/jkzero/es-eval/.hf_cache setsid nohup .venv/bin/python scripts/run_belebele.py >> results/belebele_run.log 2>&1 < /dev/null &
    log "run_belebele.py started as PID $!"
else
    log "MGSM incomplete (${n:-?}/$EXPECTED); relaunching run_mgsm.py to resume, not starting Belebele"
    HF_HOME=/home/jkzero/es-eval/.hf_cache setsid nohup .venv/bin/python scripts/run_mgsm.py >> results/mgsm_run.log 2>&1 < /dev/null &
    log "run_mgsm.py restarted as PID $!"
fi
