#!/usr/bin/env bash
# Stop a benchmark runner at a fixed clock time (the PC is turned off ~19:00).
#   scripts/stop_at.sh HH:MM PID [RAW]
# At HH:MM today: if PID is still a run_*.py, SIGTERM it, wait up to 60 s,
# then SIGKILL. A cut partial last line in RAW (default
# results/proxlite_raw.jsonl) is moved to RAW's .interrupted.jsonl so the
# resumable runner re-asks it. Logs the stop and the unique id+lang count.
# Exits quietly if the runner already finished before HH:MM.
#
# Usage (detached):
#   cd /home/jkzero/es-eval && setsid nohup scripts/stop_at.sh 18:55 84645 >> results/chain.log 2>&1 < /dev/null &
set -u

ROOT=/home/jkzero/es-eval
cd "$ROOT" || exit 1
AT=${1:?HH:MM}
PID=${2:?PID}
RAW=${3:-results/proxlite_raw.jsonl}
PY=.venv/bin/python

log() { echo "[$(date +%Y-%m-%dT%H:%M:%S)] stop_at: $*"; }
# Match on the command line too, so a reused PID is never signalled.
alive() { tr '\0' ' ' 2>/dev/null < "/proc/$PID/cmdline" | grep -qE 'scripts/run_[a-z_]+\.py'; }

target=$(date -d "today $AT" +%s) || exit 1
[ "$target" -gt "$(date +%s)" ] || { log "$AT has already passed; nothing scheduled"; exit 1; }
alive || { log "PID $PID is not a run_*.py; nothing to stop"; exit 1; }
log "will stop PID $PID ($(tr '\0' ' ' < /proc/$PID/cmdline)) at $AT; watching $RAW"

# Poll instead of one long sleep, so a clock change or suspend cannot overshoot.
while left=$(( target - $(date +%s) )); [ "$left" -gt 0 ]; do
    alive || { log "PID $PID exited on its own before $AT; nothing to stop"; exit 0; }
    sleep $(( left < 20 ? left : 20 ))
done

if alive; then
    log "$AT reached: SIGTERM to PID $PID"
    kill -TERM "$PID" 2>/dev/null
    for _ in $(seq 60); do alive || break; sleep 1; done
    if alive; then
        log "PID $PID still alive after 60 s; SIGKILL"
        kill -KILL "$PID" 2>/dev/null
        sleep 1
    fi
else
    log "PID $PID exited just before $AT"
fi

# Move a torn last line aside (a kill mid-write) so the next append is clean.
"$PY" - "$RAW" "${RAW%.jsonl}.interrupted.jsonl" <<'EOF' | while IFS= read -r line; do log "$line"; done
import json, sys
raw, side = sys.argv[1], sys.argv[2]
data = open(raw, "rb").read()
if data and not data.endswith(b"\n"):
    cut = data.rfind(b"\n") + 1
    with open(side, "ab") as f:
        f.write(data[cut:] + b"\n")
    with open(raw, "r+b") as f:
        f.truncate(cut)
    print(f"moved torn last line ({len(data) - cut} bytes) to {side}")
seen = set()
for line in open(raw, encoding="utf-8"):
    try:
        r = json.loads(line)
        seen.add((r["id"], r["lang"]))
    except (json.JSONDecodeError, KeyError):
        pass
print(f"{raw}: {len(seen)} unique id+lang records after the stop; resume with run_proxlite.py (resumable)")
EOF
