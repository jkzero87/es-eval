#!/usr/bin/env bash
# Wait for the Belebele run to start and then exit, then chain the next job.
#   - 1464 unique (id, lang) records in results/belebele_raw.jsonl -> launch run_proxlite.py
#   - otherwise -> relaunch run_belebele.py (it resumes) and exit
# Both are launched detached with setsid nohup. Log: results/chain.log
#
# Usage (detached):
#   cd /home/jkzero/es-eval && setsid nohup scripts/chain_after_belebele.sh >> results/chain.log 2>&1 < /dev/null &
set -u

ROOT=/home/jkzero/es-eval
RAW=results/belebele_raw.jsonl
EXPECTED=1464
cd "$ROOT" || exit 1

# pgrep pattern for real runner processes only (not editors, greps or shells
# that merely mention the script name).
RUNNER_RE='^[^ ]*python[0-9.]* (-u )?scripts/run_'

log() { echo "[$(date +%Y-%m-%dT%H:%M:%S)] chain-belebele: $*"; }

count_unique() {
    [ -f "$RAW" ] || { echo 0; return; }
    .venv/bin/python - "$RAW" <<'EOF'
import json, sys
seen = set()
with open(sys.argv[1], encoding="utf-8") as f:
    for line in f:
        try:
            rec = json.loads(line)
            seen.add((rec["id"], rec["lang"]))
        except (json.JSONDecodeError, KeyError):
            pass
print(len(seen))
EOF
}

any_runner() { pgrep -f "${RUNNER_RE}[a-z_]+\.py" >/dev/null; }

# Match on the command line too, so a reused PID doesn't keep us waiting forever.
alive() { tr '\0' ' ' 2>/dev/null < "/proc/$1/cmdline" | grep -q run_belebele; }

# Phase 1: wait for run_belebele.py to start (it is launched by chain_after_mgsm.sh).
log "waiting for run_belebele.py to start (poll every 30 s)"
PID=""
while :; do
    PID=$(pgrep -f "${RUNNER_RE}(belebele)\.py" | head -1)
    [ -n "$PID" ] && break
    # Already finished before we started watching: nothing to wait for.
    if ! any_runner && [ "$(count_unique)" -eq "$EXPECTED" ]; then
        log "run_belebele.py not running but $RAW is already complete"
        break
    fi
    sleep 30
done

# Phase 2: wait for it to exit.
if [ -n "$PID" ]; then
    log "run_belebele.py is PID $PID; waiting for it to exit"
    while alive "$PID"; do
        sleep 30
    done
    log "PID $PID has exited"
fi

n=$(count_unique)
log "$RAW: ${n:-?} unique id+lang records (expected $EXPECTED)"

# Never start a second copy next to one that is already running.
if any_runner; then
    log "a run_*.py process is already running; launching nothing"
    pgrep -af "${RUNNER_RE}[a-z_]+\.py"
    exit 1
fi

if [ "${n:-0}" -eq "$EXPECTED" ]; then
    log "Belebele complete; launching run_proxlite.py"
    HF_HOME=/home/jkzero/es-eval/.hf_cache setsid nohup .venv/bin/python scripts/run_proxlite.py >> results/proxlite_run.log 2>&1 < /dev/null &
    log "run_proxlite.py started as PID $!"
else
    log "Belebele incomplete (${n:-?}/$EXPECTED); relaunching run_belebele.py to resume, not starting ProX-Lite"
    HF_HOME=/home/jkzero/es-eval/.hf_cache setsid nohup .venv/bin/python scripts/run_belebele.py >> results/belebele_run.log 2>&1 < /dev/null &
    log "run_belebele.py restarted as PID $!"
fi
