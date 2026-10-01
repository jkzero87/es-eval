#!/usr/bin/env bash
# Deadline gate for the ProX-Lite run.
#
# Polls every 60 s until run_proxlite.py is running and results/proxlite_raw.jsonl
# has >= 30 new records since that run was first seen, then logs scripts/eta.py
# and decides (rule fixed 2026-10-01):
#   - full run projected to finish before DEADLINE -> "gate: full run kept", exit;
#   - otherwise N = floor(records_per_hour * hours_until_DEADLINE / 3), clamped
#     to 14..588 and raised to the number of ids already done in all three
#     languages; SIGTERM run_proxlite.py (SIGKILL after 60 s), wait until no
#     run_*.py is alive, move a torn last line (if any) to
#     results/proxlite_raw.interrupted.jsonl, and relaunch
#     run_proxlite.py --limit N --keep-done on the main file, detached.
#     --keep-done puts every finished triplet in the subset (a plain --limit
#     subset is random per category and would mostly skip them).
# Never talks to the server. Log: results/chain.log
#
# Usage (detached):
#   cd /home/jkzero/es-eval && setsid nohup scripts/proxlite_gate.sh >> results/chain.log 2>&1 < /dev/null &
#
# Overridable for offline tests: ROOT, DEADLINE, POLL, MIN_NEW, PY, RUNNER_RE.
set -u

ROOT=${ROOT:-/home/jkzero/es-eval}
DEADLINE=${DEADLINE:-2026-10-02T08:00:00}
POLL=${POLL:-60}
MIN_NEW=${MIN_NEW:-30}
PY=${PY:-.venv/bin/python}
# Real runner processes only (not editors, greps or shells naming the script).
RUNNER_RE=${RUNNER_RE:-'^[^ ]*python[0-9.]* (-u )?scripts/run_'}
RAW=results/proxlite_raw.jsonl
TARGET=1764
cd "$ROOT" || exit 1

log() { echo "[$(date +%Y-%m-%dT%H:%M:%S)] gate: $*"; }

# "<unique id+lang> <ids done in all 3 langs>" in $RAW.
counts() {
    [ -f "$RAW" ] || { echo "0 0"; return; }
    "$PY" - "$RAW" <<'EOF'
import json, sys
from collections import Counter
pairs = set()
with open(sys.argv[1], encoding="utf-8") as f:
    for line in f:
        try:
            rec = json.loads(line)
            pairs.add((rec["id"], rec["lang"]))
        except (json.JSONDecodeError, KeyError):
            pass
print(len(pairs), sum(1 for c in Counter(i for i, _ in pairs).values() if c == 3))
EOF
}

proxlite_pid() { pgrep -f "${RUNNER_RE}proxlite\.py" | head -1; }
any_runner() { pgrep -f "${RUNNER_RE}[a-z_]+\.py" >/dev/null; }
# Match on the command line too, so a reused PID is not mistaken for the runner.
alive() { tr '\0' ' ' 2>/dev/null < "/proc/$1/cmdline" | grep -q run_proxlite; }

log "waiting for run_proxlite.py and $MIN_NEW new records in $RAW (poll ${POLL}s); deadline $DEADLINE"
PID=""
BASE=0
while :; do
    cur=$(proxlite_pid)
    read -r n _ <<< "$(counts)"
    if [ -z "$cur" ]; then
        if [ -n "$PID" ]; then
            log "run_proxlite.py PID $PID exited after $((n - BASE)) new records; waiting for a new run"
            PID=""
        fi
        if [ "$n" -ge "$TARGET" ]; then
            log "$RAW complete ($n/$TARGET); nothing to gate"
            exit 0
        fi
    elif [ "$cur" != "$PID" ]; then
        PID=$cur
        BASE=$n
        log "run_proxlite.py is PID $PID; baseline $BASE records"
    elif [ $((n - BASE)) -ge "$MIN_NEW" ]; then
        if eta=$("$PY" scripts/eta.py "$RAW" "$TARGET" --json); then
            break
        fi
        log "eta.py failed; retrying next poll"
    fi
    sleep "$POLL"
done

read -r n triplets <<< "$(counts)"
log "PID $PID: $((n - BASE)) new records ($n/$TARGET, $triplets ids done in all 3 langs); eta.py:"
"$PY" scripts/eta.py "$RAW" "$TARGET" | sed 's/^/    /'

# Decision. Prints log lines, then "ACTION keep" or "ACTION limit N".
decision=$("$PY" - "$eta" "$DEADLINE" "$triplets" <<'EOF'
import json, math, sys
from datetime import datetime, timedelta
eta, deadline, triplets = json.loads(sys.argv[1]), datetime.fromisoformat(sys.argv[2]), int(sys.argv[3])
now = datetime.now()
rph = eta["records_per_hour"]
full = datetime.fromisoformat(eta["finish"])
print(f"rate {rph:.0f} records/h; full run ({eta['remaining']} left) projected {full:%Y-%m-%d %H:%M}; "
      f"deadline {deadline:%Y-%m-%d %H:%M}")
if full < deadline:
    print("ACTION keep")
    sys.exit()
hours = max((deadline - now).total_seconds() / 3600, 0)
n = min(max(math.floor(rph * hours / 3), 14), 588)
print(f"N = floor({rph:.1f} * {hours:.2f} h / 3) clamped to 14..588 = {n}")
if triplets > n:
    print(f"N raised to {triplets}: that many ids are already done in all 3 langs")
    n = triplets
limited = now + timedelta(hours=3 * (n - triplets) / rph)
print(f"limited run (N={n}, ~{3 * (n - triplets)} records left) projected {limited:%Y-%m-%d %H:%M}")
print(f"ACTION limit {n}")
EOF
) || { log "decision step failed; leaving run_proxlite.py PID $PID alone"; exit 1; }
grep -v '^ACTION ' <<< "$decision" | while IFS= read -r line; do log "$line"; done
action=$(grep '^ACTION ' <<< "$decision")

if [ "$action" = "ACTION keep" ]; then
    log "full run kept"
    exit 0
fi
N=${action#ACTION limit }

log "stopping run_proxlite.py PID $PID (SIGTERM)"
kill -TERM "$PID" 2>/dev/null
for _ in $(seq 60); do alive "$PID" || break; sleep 1; done
if alive "$PID"; then
    log "PID $PID still alive after 60 s; SIGKILL"
    kill -KILL "$PID" 2>/dev/null
    sleep 1
fi
while any_runner; do
    log "waiting for running run_*.py to exit: $(pgrep -af "${RUNNER_RE}[a-z_]+\.py" | tr '\n' ';')"
    sleep "$POLL"
done

# A kill mid-write can leave a torn last line; the next append would glue onto
# it and corrupt that record too. Move it aside so the resume re-asks it.
"$PY" - "$RAW" results/proxlite_raw.interrupted.jsonl <<'EOF' | while IFS= read -r line; do log "$line"; done
import sys
raw, side = sys.argv[1], sys.argv[2]
data = open(raw, "rb").read()
if data and not data.endswith(b"\n"):
    cut = data.rfind(b"\n") + 1
    with open(side, "ab") as f:
        f.write(data[cut:] + b"\n")
    with open(raw, "r+b") as f:
        f.truncate(cut)
    print(f"moved torn last line ({len(data) - cut} bytes) to {side}")
EOF

read -r n triplets <<< "$(counts)"
log "relaunching run_proxlite.py --limit $N --keep-done ($n records, $triplets finished ids in file)"
HF_HOME=$ROOT/.hf_cache setsid nohup "$PY" scripts/run_proxlite.py --limit "$N" --keep-done \
    >> results/proxlite_run.log 2>&1 < /dev/null &
log "run_proxlite.py --limit $N --keep-done started as PID $!"
