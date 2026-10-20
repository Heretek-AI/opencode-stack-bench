#!/usr/bin/env bash
# Validate the task suite without a model: solutions must score 1.0, untouched fixtures must not.
set -euo pipefail
cd "$(dirname "$0")/.."
out="$(mktemp -d)"
python3 bench/run_arm.py --arm stock --mode solution --out "$out/solution"
python3 bench/run_arm.py --arm stock --mode noop --out "$out/noop"
python3 - "$out" <<'PY'
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
bad = []
for line in (out / "solution" / "stock-w1.jsonl").read_text().splitlines():
    r = json.loads(line)
    tests = json.loads(Path("tasks", r["task"], "task.json").read_text()).get("tests")
    if not r["solved"]:
        bad.append(f"{r['task']}: reference solution scores {r['passed']}/{r['total']}")
    if tests != r["total"]:
        bad.append(f"{r['task']}: task.json says tests={tests} but the hidden suite has {r['total']}")
for line in (out / "noop" / "stock-w1.jsonl").read_text().splitlines():
    r = json.loads(line)
    if r["solved"]:
        bad.append(f"{r['task']}: untouched fixture already passes all hidden tests")
print("\n".join(bad) or "task suite OK")
sys.exit(1 if bad else 0)
PY
