#!/usr/bin/env bash
# Offline test of proxlite_gate.sh with a fake runner and fake timestamps.
# Never touches results/ or the server: everything runs in a temp root, and the
# fake runner is started as '.venv/bin/fakepy scripts/run_proxlite.py' with the
# gate's RUNNER_RE pointed at 'fakepy', so real runners are never matched.
#
#   keep   720 rec/h, deadline +24 h          -> full run kept, runner untouched
#   limit  60 rec/h, deadline +10 h, torn line -> N=199, torn line moved aside,
#                                                SIGTERM, relaunch --limit 199 --keep-done
#   floor  60 rec/h, deadline +3 h, 300 finished triplets, runner ignores SIGTERM
#                                             -> N raised to 311, SIGKILL, relaunch
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
PYBIN=$(command -v python3)
FAIL=0
ROOTS=()
trap 'pkill -f "^\.venv/bin/fakepy scripts/run_proxlite"; rm -rf "${ROOTS[@]}" "${SEED_FILE:-}"' EXIT

make_root() {
    local root
    root=$(mktemp -d)
    mkdir -p "$root/scripts" "$root/results" "$root/.venv/bin"
    ln -s "$PYBIN" "$root/.venv/bin/fakepy"
    cp "$HERE/proxlite_gate.sh" "$HERE/eta.py" "$root/scripts/"
    # Seeded records exist before the fake runner starts: baseline, not new.
    [ -n "${SEED_FILE:-}" ] && cp "$SEED_FILE" "$root/results/proxlite_raw.jsonl"
    cat > "$root/scripts/run_proxlite.py" <<'EOF'
import json, os, signal, sys, time
from datetime import datetime, timedelta
if len(sys.argv) > 1:                      # the gate's relaunch: record argv and exit
    open("results/relaunch_argv.txt", "w").write(" ".join(sys.argv[1:]) + "\n")
    sys.exit()
if os.environ.get("FAKE_IGNORE_TERM"):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
interval, count = float(os.environ["FAKE_INTERVAL"]), int(os.environ.get("FAKE_COUNT", 33))
skip = int(os.environ.get("FAKE_SKIP", 0))   # ids already done by the seeded file
pairs = [(q, l) for q in range(70 + skip, 658) for l in ("en", "es", "zh")]
print(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] question_id 70..657 (588 ids); "
      f"done={3 * skip} pending={len(pairs)} total=1764", flush=True)
time.sleep(3)                              # like the real dataset load: gate sees us first
t0 = datetime.now() - timedelta(seconds=interval * (count + 2))
for k, (q, l) in enumerate(pairs[:count], 1):
    rec = {"id": q, "lang": l, "usage": {"completion_tokens": 1000 + k}, "wall": interval}
    with open("results/proxlite_raw.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")
    ts = t0 + timedelta(seconds=interval * k)
    print(f"[{ts:%Y-%m-%dT%H:%M:%S}] ({k}/{len(pairs)}) id={q} {l} finish=stop", flush=True)
    time.sleep(0.05)
if os.environ.get("FAKE_TORN"):
    with open("results/proxlite_raw.jsonl", "a") as f:
        f.write('{"id": 999, "lang": "en", "content": "cut he')
while True:
    time.sleep(1)
EOF
    echo "$root"
}

# run_case NAME DEADLINE_OFFSET_H [ENV=VAL...]: start fake runner + gate, wait for the gate.
run_case() {
    local name=$1 hours=$2 root deadline runner
    shift 2
    root=$(make_root)
    deadline=$(date -d "+${hours} hours" +%Y-%m-%dT%H:%M:%S)
    # exec, and no inherited stdout: otherwise the subshell waits on the fake
    # runner while holding the \$(run_case) pipe open.
    ( cd "$root" && exec env "$@" setsid nohup .venv/bin/fakepy scripts/run_proxlite.py \
        >> results/proxlite_run.log 2>&1 < /dev/null ) > /dev/null 2>&1 &
    ( cd "$root" && ROOT=$root DEADLINE=$deadline POLL=1 PY=.venv/bin/fakepy \
        RUNNER_RE='^[^ ]*fakepy[0-9.]* (-u )?scripts/run_' \
        timeout 120 scripts/proxlite_gate.sh >> results/chain.log 2>&1 )
    echo "$root"
}

check() {  # check DESC COMMAND...
    if "${@:2}"; then echo "  ok   $1"; else echo "  FAIL $1"; FAIL=1; fi
}

# The relaunched fake is detached; give it a moment to record its argv.
relaunch_argv() {
    for _ in $(seq 50); do [ -s "$1/results/relaunch_argv.txt" ] && break; sleep 0.1; done
    cat "$1/results/relaunch_argv.txt" 2>/dev/null
}

kill_fake() { pkill -f "^$1/.venv/bin/fakepy|^\.venv/bin/fakepy scripts/run_proxlite" 2>/dev/null; true; }

echo "== keep"
R=$(run_case keep 24 FAKE_INTERVAL=5); ROOTS+=("$R")
sed 's/^/    /' "$R/results/chain.log"
check "logs 'gate: full run kept'" grep -q 'gate: full run kept' "$R/results/chain.log"
check "fake runner left running" pgrep -f '^\.venv/bin/fakepy scripts/run_proxlite'
check "no relaunch" test ! -e "$R/results/relaunch_argv.txt"
kill_fake "$R"; sleep 1

echo "== limit (torn line, SIGTERM)"
R=$(run_case limit 10 FAKE_INTERVAL=60 FAKE_TORN=1); ROOTS+=("$R")
sed 's/^/    /' "$R/results/chain.log"
check "N=199 (60/h * ~10 h / 3)" test "$(relaunch_argv "$R")" = '--limit 199 --keep-done'
check "both projections logged" bash -c "grep -q 'full run .* projected' '$R/results/chain.log' && grep -q 'limited run (N=199' '$R/results/chain.log'"
check "torn line moved aside" grep -q '"id": 999' "$R/results/proxlite_raw.interrupted.jsonl"
check "raw ends with newline, 33 valid lines" bash -c "[ \"\$(tail -c1 '$R/results/proxlite_raw.jsonl' | od -An -c | tr -d ' ')\" = '\n' ] && [ \$(wc -l < '$R/results/proxlite_raw.jsonl') -eq 33 ]"
check "no SIGKILL needed" bash -c "! grep -q SIGKILL '$R/results/chain.log'"
check "fake runner stopped" bash -c "! pgrep -f '^\.venv/bin/fakepy scripts/run_proxlite' >/dev/null"

echo "== floor (300 finished triplets, SIGTERM ignored)"
SEED_FILE=$(mktemp)
python3 -c "
import json
for q in range(70, 370):
    for l in ('en','es','zh'):
        print(json.dumps({'id': q, 'lang': l, 'usage': {'completion_tokens': 500}, 'wall': 60}))" > "$SEED_FILE"
R=$(run_case floor 3 FAKE_INTERVAL=60 FAKE_SKIP=300 FAKE_IGNORE_TERM=1); ROOTS+=("$R")
sed 's/^/    /' "$R/results/chain.log"
check "baseline counts seeded records" grep -q 'baseline 900 records' "$R/results/chain.log"
check "N raised to finished triplets (311)" test "$(relaunch_argv "$R")" = '--limit 311 --keep-done'
check "SIGKILL after 60 s" grep -q 'SIGKILL' "$R/results/chain.log"
check "fake runner stopped" bash -c "! pgrep -f '^\.venv/bin/fakepy scripts/run_proxlite' >/dev/null"
rm -f "$SEED_FILE"

[ $FAIL -eq 0 ] && echo "ALL OK" || { echo "FAILURES"; exit 1; }
