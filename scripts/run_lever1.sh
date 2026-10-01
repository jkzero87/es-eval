#!/usr/bin/env bash
# Lever 1 (results/lever1_plan.md): MGSM en+es with the plain-reading system
# prompt, then score against the baseline and count reasoning tokens exactly.
#   1. run_mgsm.py --langs en,es --system prompts/plain_reading.txt --tag plain
#      -> results/mgsm_raw.plain.jsonl (500 records)
#   2. score_mgsm.py --raw results/mgsm_raw.plain.jsonl --baseline results/mgsm_raw.jsonl
#      --no-tokenize (exact counts come from step 3) -> results/lever1_score.txt
#   3. mgsm_token_split.py --raw results/mgsm_raw.plain.jsonl
#      -> results/mgsm_token_split.plain.jsonl (/tokenize, 1 s safeguard)
# Refuses to start while any run_*.py, chain_*.sh or proxlite_gate.sh is alive.
# Steps 2-3 run only if step 1 left all 500 records.
#
# Usage:
#   scripts/run_lever1.sh --dry-run      # guard check + commands, runs nothing
#   cd /home/jkzero/es-eval && setsid nohup scripts/run_lever1.sh >> results/lever1_run.log 2>&1 < /dev/null &
set -u

ROOT=/home/jkzero/es-eval
PY=.venv/bin/python
TAG=plain
RAW=results/mgsm_raw.$TAG.jsonl
EXPECTED=500
cd "$ROOT" || exit 1

DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

# Real runner processes only (not editors, greps or shells naming the script).
RUNNER_RE='^[^ ]*python[0-9.]* (-u )?scripts/run_[a-z_]+\.py'
WATCHER_RE='^(bash )?(scripts/)?(chain_[a-z_]+|proxlite_gate)\.sh'

log() { echo "[$(date +%Y-%m-%dT%H:%M:%S)] lever1: $*"; }

CMD_RUN=("$PY" scripts/run_mgsm.py --langs en,es --system prompts/plain_reading.txt --tag "$TAG")
CMD_SCORE=("$PY" scripts/score_mgsm.py --raw "$RAW" --baseline results/mgsm_raw.jsonl --no-tokenize)
CMD_SPLIT=("$PY" scripts/mgsm_token_split.py --raw "$RAW")

busy=$( { pgrep -af "$RUNNER_RE"; pgrep -af "$WATCHER_RE"; } | grep -v "run_lever1" )
if [ -n "$busy" ]; then
    log "refusing: a runner or watcher is alive:"
    echo "$busy" | sed 's/^/    /'
    [ $DRY -eq 1 ] && log "(dry run) would refuse to start"
    exit 1
fi
[ -s prompts/plain_reading.txt ] || { log "missing prompts/plain_reading.txt"; exit 1; }

if [ $DRY -eq 1 ]; then
    log "(dry run) guard clear; would run:"
    printf '    %s\n' "${CMD_RUN[*]}" "${CMD_SCORE[*]} > results/lever1_score.txt" "${CMD_SPLIT[*]}"
    [ -e "$RAW" ] && log "(dry run) note: $RAW exists ($(wc -l < "$RAW") lines); run_mgsm.py resumes it"
    exit 0
fi

log "step 1: ${CMD_RUN[*]}"
"${CMD_RUN[@]}"
n=$("$PY" - "$RAW" <<'EOF'
import json, sys
seen = set()
for line in open(sys.argv[1], encoding="utf-8"):
    try:
        r = json.loads(line)
        seen.add((r["id"], r["lang"]))
    except (json.JSONDecodeError, KeyError):
        pass
print(len(seen))
EOF
)
if [ "${n:-0}" -ne "$EXPECTED" ]; then
    log "$RAW has ${n:-?}/$EXPECTED unique id+lang records; rerun this script to resume. Not scoring."
    exit 1
fi

log "step 2: ${CMD_SCORE[*]} > results/lever1_score.txt"
"${CMD_SCORE[@]}" > results/lever1_score.txt 2>&1 || { log "scorer failed; see results/lever1_score.txt"; exit 1; }

log "step 3: ${CMD_SPLIT[*]}"
"${CMD_SPLIT[@]}" || { log "token split stopped (see above); rerun this script to resume"; exit 1; }
log "done; apply the decision rule in results/lever1_plan.md"
