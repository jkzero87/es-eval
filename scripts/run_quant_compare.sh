#!/usr/bin/env bash
# Run one benchmark against the IQ4_XS 27B (tag q4), then put the production
# server on :8092 back exactly as it was.
#
#   scripts/run_quant_compare.sh [--dry-run] mgsm|belebele|proxlite
#
# 1. Refuse if any run_*.py or chain_after_*.sh is running (a watcher could
#    otherwise start a *baseline* run against the q4 server).
# 2. Save the :8092 server's argv (one arg per line) to results/restore_8092.argv
#    and its GGML_*/CUDA_* environment to results/restore_8092.env, stop it,
#    wait until its VRAM is freed.
# 3. Start llama-server (binary from the saved argv) with the IQ4_XS model and
#    the certified config, same GGML_*/CUDA_* env; poll /health up to 300 s.
# 4. Run scripts/run_<bench>.py --tag q4 (all three langs), in the foreground.
# 5. Stop the q4 server, relaunch the original from the saved argv/env, detached
#    with setsid nohup (as ~/bin/manifiestate does), poll /health, and update
#    ~/.local/state/llmstack/model.pid so `chao` keeps working.
# Step 5 also runs if anything fails or the script is interrupted after step 2.
#
# It takes as long as the benchmark (hours for proxlite); run it detached:
#   cd /home/jkzero/es-eval && setsid nohup scripts/run_quant_compare.sh proxlite \
#     >> results/quant_compare.log 2>&1 < /dev/null &
#
# --dry-run prints every command that would change something instead of running
# it; read-only lookups (pgrep, /proc, ss, nvidia-smi) still run.
set -u

ROOT=/home/jkzero/es-eval
PORT=8092
Q4_MODEL=/home/jkzero/models/Qwen3.8-27B/Qwen3.8-27B-UD-IQ4_XS.gguf
ARGV_FILE=$ROOT/results/restore_8092.argv
ENV_FILE=$ROOT/results/restore_8092.env   # record; the env used comes from /proc at start
PIDFILE=$HOME/.local/state/llmstack/model.pid
HEALTH_TIMEOUT=300
STOP_TIMEOUT=120
RUNNER_RE='^[^ ]*python[0-9.]* (-u )?scripts/run_[a-z_]+\.py'
WATCHER_RE='^([^ ]*/)?bash [^ ]*chain_after_[a-z_]+\.sh'

DRY=0
if [ "${1:-}" = "--dry-run" ]; then DRY=1; shift; fi
BENCH=${1:-}
case "$BENCH" in
    mgsm|belebele|proxlite) ;;
    *) echo "usage: $0 [--dry-run] mgsm|belebele|proxlite" >&2; exit 2 ;;
esac
cd "$ROOT" || exit 1

log() { echo "[$(date +%Y-%m-%dT%H:%M:%S)] quant-compare: $*"; }
# run CMD...: execute, or print it in dry-run mode.
run() {
    if [ "$DRY" = 1 ]; then printf 'DRY-RUN:'; printf ' %q' "$@"; echo; else "$@"; fi
}
port_pid() { ss -Htlnp "sport = :$PORT" | grep -oP 'pid=\K[0-9]+' | head -1; }
healthy() { curl -sf "localhost:$PORT/health" >/dev/null; }
gpu_used() { nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1; }
on_gpu() { nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -qx "$1"; }

# stop_server PID: SIGTERM, wait for the process to exit and leave the GPU.
stop_server() {
    local pid=$1 i
    log "stopping llama-server PID $pid (GPU used: $(gpu_used) MiB)"
    run kill -TERM "$pid"
    [ "$DRY" = 1 ] && { echo "DRY-RUN: wait until PID $pid has exited and is gone from nvidia-smi compute apps (<= ${STOP_TIMEOUT}s)"; return 0; }
    for ((i = 0; i < STOP_TIMEOUT; i++)); do
        if ! kill -0 "$pid" 2>/dev/null && ! on_gpu "$pid"; then
            log "PID $pid gone; VRAM freed (GPU used: $(gpu_used) MiB)"
            return 0
        fi
        sleep 1
    done
    log "PID $pid still alive or on the GPU after ${STOP_TIMEOUT}s; sending SIGKILL"
    kill -KILL "$pid" 2>/dev/null
    for ((i = 0; i < 30; i++)); do on_gpu "$pid" || { log "VRAM freed (GPU used: $(gpu_used) MiB)"; return 0; }; sleep 1; done
    log "ERROR: PID $pid still holds VRAM"
    return 1
}

# start_server LOG ARGV...: start detached with the saved env; sets STARTED_PID.
start_server() {
    local logf=$1; shift
    local envs=("${ORIG_ENV[@]}")
    log "starting: ${envs[*]} $* (log: $logf)"
    if [ "$DRY" = 1 ]; then
        printf 'DRY-RUN: env'; [ ${#envs[@]} -gt 0 ] && printf ' %q' "${envs[@]}"
        printf ' setsid nohup'; printf ' %q' "$@"; printf ' > %q 2>&1 < /dev/null &\n' "$logf"
        STARTED_PID=DRYPID
        return 0
    fi
    env "${envs[@]}" setsid nohup "$@" > "$logf" 2>&1 < /dev/null &
    STARTED_PID=$!
}

# wait_healthy PID: poll /health up to HEALTH_TIMEOUT s while PID is alive.
wait_healthy() {
    local pid=$1 i
    [ "$DRY" = 1 ] && { echo "DRY-RUN: poll http://localhost:$PORT/health every 1 s, up to ${HEALTH_TIMEOUT}s"; return 0; }
    for ((i = 0; i < HEALTH_TIMEOUT; i++)); do
        healthy && { log "healthy after ${i}s (PID $pid, GPU used: $(gpu_used) MiB)"; return 0; }
        kill -0 "$pid" 2>/dev/null || { log "ERROR: PID $pid exited before becoming healthy"; return 1; }
        sleep 1
    done
    log "ERROR: not healthy after ${HEALTH_TIMEOUT}s"
    return 1
}

record_pid() {
    [ -d "$(dirname "$PIDFILE")" ] || return 0
    if [ "$DRY" = 1 ]; then echo "DRY-RUN: echo $1 > $PIDFILE"; else echo "$1" > "$PIDFILE"; fi
}

# --- 1. refuse if anything else is using the server or could start to
busy=0
if pgrep -f "$RUNNER_RE" >/dev/null; then
    log "refusing: a benchmark runner is running:"; pgrep -af "$RUNNER_RE"; busy=1
fi
if pgrep -f "$WATCHER_RE" >/dev/null; then
    log "refusing: a chain watcher is running (it could start a baseline run against the q4 server):"
    pgrep -af "$WATCHER_RE"; busy=1
fi
if [ "$busy" = 1 ]; then
    [ "$DRY" = 1 ] || exit 1
    echo "DRY-RUN: (would exit here; continuing to show the remaining commands)"
fi

# --- 2. save the production server's argv/env, then stop it
ORIG_PID=$(port_pid)
if [ -z "$ORIG_PID" ]; then log "ERROR: nothing listening on :$PORT"; exit 1; fi
if ! tr '\0' '\n' < "/proc/$ORIG_PID/cmdline" | head -1 | grep -q 'llama-server$'; then
    log "ERROR: PID $ORIG_PID on :$PORT is not llama-server: $(tr '\0' ' ' < /proc/$ORIG_PID/cmdline)"
    exit 1
fi
mapfile -t ORIG_ARGV < <(tr '\0' '\n' < "/proc/$ORIG_PID/cmdline")
mapfile -t ORIG_ENV < <(tr '\0' '\n' < "/proc/$ORIG_PID/environ" | grep -E '^(GGML|CUDA)_[A-Z0-9_]*=')
BIN=${ORIG_ARGV[0]}
log "production server: PID $ORIG_PID, ${#ORIG_ARGV[@]} args, env: ${ORIG_ENV[*]:-(none)}"
if [ "$DRY" = 1 ]; then
    echo "DRY-RUN: write ${#ORIG_ARGV[@]} lines to $ARGV_FILE:"; printf '    %s\n' "${ORIG_ARGV[@]}"
    echo "DRY-RUN: write ${#ORIG_ENV[@]} lines to $ENV_FILE:"; printf '    %s\n' "${ORIG_ENV[@]}"
else
    printf '%s\n' "${ORIG_ARGV[@]}" > "$ARGV_FILE"
    printf '%s\n' "${ORIG_ENV[@]}" > "$ENV_FILE"
fi

Q4_PID=""
RESTORED=0
restore() {
    [ "$RESTORED" = 1 ] && return
    RESTORED=1
    log "--- 5. restoring the production server"
    if [ -n "$Q4_PID" ] && { [ "$DRY" = 1 ] || kill -0 "$Q4_PID" 2>/dev/null; }; then
        stop_server "$Q4_PID"
    fi
    local restore_argv=()
    if [ "$DRY" = 1 ]; then restore_argv=("${ORIG_ARGV[@]}"); else mapfile -t restore_argv < "$ARGV_FILE"; fi
    start_server "$HOME/logs/27b_gsq_$(date +%Y%m%d_%H%M).log" "${restore_argv[@]}"
    if wait_healthy "$STARTED_PID"; then
        local now=$STARTED_PID
        [ "$DRY" = 1 ] || now=$(port_pid)
        record_pid "${now:-$STARTED_PID}"
        log "production server restored (PID ${STARTED_PID})"
    else
        log "ERROR: production server did not come back; restart it with ~/bin/manifiestate"
    fi
}
trap restore EXIT
trap 'log "interrupted"; exit 130' INT TERM HUP

stop_server "$ORIG_PID" || exit 1

# --- 3. q4 server with the certified config
log "--- 3. starting the q4 server"
start_server "$HOME/logs/27b_q4_$(date +%Y%m%d_%H%M).log" "$BIN" -m "$Q4_MODEL" \
    --spec-type draft-mtp --spec-draft-n-max 3 \
    -ngl 99 -fa on -c 32768 -ub 256 \
    -ctk q8_0 -ctv q8_0 -ctkd q8_0 -ctvd q8_0 \
    -t 6 --parallel 1 --reasoning-effort medium \
    --port "$PORT"
Q4_PID=$STARTED_PID
wait_healthy "$Q4_PID" || exit 1
record_pid "$Q4_PID"

# --- 4. the benchmark (all three languages, tagged q4)
log "--- 4. running $BENCH --tag q4"
if [ "$DRY" = 1 ]; then
    echo "DRY-RUN: HF_HOME=$ROOT/.hf_cache .venv/bin/python scripts/run_$BENCH.py --tag q4 >> results/${BENCH}_run.q4.log 2>&1 < /dev/null"
    rc=0
else
    HF_HOME=$ROOT/.hf_cache .venv/bin/python scripts/run_"$BENCH".py --tag q4 >> "results/${BENCH}_run.q4.log" 2>&1 < /dev/null
    rc=$?
fi
log "$BENCH --tag q4 exited with code $rc"

# --- 5. via the EXIT trap
exit "$rc"
