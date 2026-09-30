#!/usr/bin/env bash
# Wait for the MGSM run to exit, then chain the next job.
#   - 750 unique (id, lang) records in results/mgsm_raw.jsonl -> launch run_belebele.py
#   - otherwise -> relaunch run_mgsm.py (it resumes) and keep watching, until
#     the file is complete or MAX_NO_PROGRESS consecutive runs add nothing
# Both are launched detached with setsid nohup. Log: results/chain.log
#
# Usage (detached):
#   cd /home/jkzero/es-eval && setsid nohup scripts/chain_after_mgsm.sh [PID] >> results/chain.log 2>&1 < /dev/null &
set -u

ROOT=/home/jkzero/es-eval
PID=${1:-23294}
EXPECTED=750
MAX_NO_PROGRESS=3
cd "$ROOT" || exit 1

# pgrep pattern for real runner processes only (not editors, greps or shells
# that merely mention the script name).
RUNNER_RE='^[^ ]*python[0-9.]* (-u )?scripts/run_'

log() { echo "[$(date +%Y-%m-%dT%H:%M:%S)] chain: $*"; }

# Match on the command line too, so a reused PID doesn't keep us waiting forever.
alive() { tr '\0' ' ' 2>/dev/null < "/proc/$PID/cmdline" | grep -q run_mgsm; }

count_unique() {
    .venv/bin/python - <<'EOF'
import json
seen = set()
try:
    with open("results/mgsm_raw.jsonl", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                seen.add((rec["id"], rec["lang"]))
            except (json.JSONDecodeError, KeyError):
                pass
except FileNotFoundError:
    pass
print(len(seen))
EOF
}

no_progress=0
last_n=-1
while :; do
    log "watching PID $PID (poll every 30 s)"
    while alive; do
        sleep 30
    done
    log "PID $PID has exited"

    n=$(count_unique)
    log "mgsm_raw.jsonl: ${n:-?} unique id+lang records (expected $EXPECTED)"
    if [ "${n:-0}" -eq "$EXPECTED" ]; then
        break
    fi

    # Someone else already restarted MGSM: watch that process instead.
    other=$(pgrep -f "${RUNNER_RE}(mgsm)\.py" | head -1)
    if [ -n "$other" ]; then
        log "run_mgsm.py already running as PID $other; watching it instead"
        PID=$other
        continue
    fi
    # Never start anything next to another runner.
    if pgrep -f "${RUNNER_RE}[a-z_]+\.py" >/dev/null; then
        log "another run_*.py process is running; launching nothing"
        pgrep -af "${RUNNER_RE}[a-z_]+\.py"
        exit 1
    fi

    if [ "${n:-0}" -le "$last_n" ]; then
        no_progress=$((no_progress + 1))
    else
        no_progress=0
    fi
    last_n=${n:-0}
    if [ "$no_progress" -ge "$MAX_NO_PROGRESS" ]; then
        log "no progress in $MAX_NO_PROGRESS consecutive relaunches (stuck at $n/$EXPECTED); giving up, check results/mgsm_run.log"
        exit 1
    fi

    log "MGSM incomplete (${n:-?}/$EXPECTED); relaunching run_mgsm.py to resume, will keep watching"
    HF_HOME=/home/jkzero/es-eval/.hf_cache setsid nohup .venv/bin/python scripts/run_mgsm.py >> results/mgsm_run.log 2>&1 < /dev/null &
    PID=$!
    sleep 5
    alive || PID=$(pgrep -f "${RUNNER_RE}(mgsm)\.py" | head -1)
    log "run_mgsm.py restarted as PID ${PID:-?}"
done

# Never start Belebele next to one that is already running.
if pgrep -f "${RUNNER_RE}[a-z_]+\.py" >/dev/null; then
    log "a run_*.py process is already running; launching nothing"
    pgrep -af "${RUNNER_RE}[a-z_]+\.py"
    exit 1
fi

log "MGSM complete; launching run_belebele.py"
HF_HOME=/home/jkzero/es-eval/.hf_cache setsid nohup .venv/bin/python scripts/run_belebele.py >> results/belebele_run.log 2>&1 < /dev/null &
log "run_belebele.py started as PID $!"
