#!/usr/bin/env python3
"""Run every task once for one arm (stock or stack) in one wave.

Each task gets a fresh git workspace and a fresh HOME/XDG tree, so nothing leaks
between tasks or arms. The only difference between arms is OPENCODE_CONFIG_DIR:
`arms/stock` (empty) vs `arms/stack` (your opencode.json, agents, skills, plugins).

Results are appended as JSON lines to <out>/<arm>-w<wave>.jsonl, with raw event
logs under <out>/logs/.
"""
import argparse
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks"
CHECK_TIMEOUT_S = 180


def load_tasks(selector):
    tasks = sorted(p for p in TASKS.iterdir() if (p / "task.json").exists())
    if selector and selector != "all":
        wanted = {s.strip() for s in selector.split(",") if s.strip()}
        unknown = wanted - {p.name for p in tasks}
        if unknown:
            sys.exit(f"unknown task(s): {', '.join(sorted(unknown))}")
        tasks = [p for p in tasks if p.name in wanted]
    return tasks


def git(ws, *args):
    subprocess.run(["git", *args], cwd=ws, check=True, capture_output=True)


def make_workspace(task_dir, ws):
    shutil.copytree(task_dir / "repo", ws)
    git(ws, "init", "-q", "-b", "main")
    (ws / ".git" / "info" / "exclude").write_text("__pycache__/\n*.pyc\nnode_modules/\n.bench_hidden/\n")
    git(ws, "-c", "user.name=bench", "-c", "user.email=bench@example.invalid", "add", "-A")
    git(ws, "-c", "user.name=bench", "-c", "user.email=bench@example.invalid", "commit", "-qm", "task fixture")


def isolated_env(scratch, arm_dir, shared_config, cache_dir):
    env = {k: v for k, v in os.environ.items() if not k.startswith("OPENCODE_")}
    home = scratch / "home"
    home.mkdir(parents=True, exist_ok=True)
    env.update(
        HOME=str(home),
        XDG_CONFIG_HOME=str(home / ".config"),
        XDG_DATA_HOME=str(home / ".local" / "share"),
        XDG_STATE_HOME=str(home / ".local" / "state"),
        XDG_CACHE_HOME=str(cache_dir),
        OPENCODE_CONFIG_DIR=str(arm_dir),
        OPENCODE_DISABLE_AUTOUPDATE="1",
        # Ignore ~/.claude skills and CLAUDE.md so only what the arm declares counts.
        OPENCODE_DISABLE_CLAUDE_CODE="1",
        CI="1",
    )
    if shared_config and shared_config.exists():
        env["OPENCODE_CONFIG"] = str(shared_config)
    return env


def run_opencode(args, task_dir, ws, env, log_base, timeout_s):
    prompt = (task_dir / "prompt.md").read_text()
    cmd = [args.opencode_bin, "run", "--standalone", "--auto", "--format", "json",
           "--title", f"{task_dir.name} {args.arm} w{args.wave}"]
    if args.model:
        cmd += ["-m", args.model]
    if args.agent:
        cmd += ["--agent", args.agent]
    cmd.append(prompt)
    # opencode resolves the project directory from $PWD, not the process cwd.
    env = {**env, "PWD": str(ws)}
    events_path = log_base.with_suffix(".events.jsonl")
    stderr_path = log_base.with_suffix(".stderr.log")
    start = time.monotonic()
    timed_out = False
    with open(events_path, "w") as out, open(stderr_path, "w") as err:
        proc = subprocess.Popen(cmd, cwd=ws, env=env, stdout=out, stderr=err,
                                stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
    duration = time.monotonic() - start
    return proc.returncode, timed_out, duration, events_path, stderr_path


def summarize_events(events_path):
    """Sum usage across `step_finish` events and count tool calls from `--format json` output."""
    s = {"steps": 0, "tokens_in": 0, "tokens_out": 0, "tokens_reasoning": 0,
         "tokens_cache_read": 0, "tokens_cache_write": 0, "cost_usd": 0.0,
         "tool_calls": 0, "tool_errors": 0, "error_events": 0, "events": 0}
    tools = Counter()
    for line in events_path.read_text(errors="replace").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        s["events"] += 1
        etype = ev.get("type")
        part = ev.get("part") or {}
        if etype == "step_finish":
            s["steps"] += 1
            tok = part.get("tokens") or {}
            cache = tok.get("cache") or {}
            s["tokens_in"] += tok.get("input") or 0
            s["tokens_out"] += tok.get("output") or 0
            s["tokens_reasoning"] += tok.get("reasoning") or 0
            s["tokens_cache_read"] += cache.get("read") or 0
            s["tokens_cache_write"] += cache.get("write") or 0
            s["cost_usd"] += part.get("cost") or 0
        elif etype == "tool_use":
            s["tool_calls"] += 1
            tools[part.get("tool", "?")] += 1
            if (part.get("state") or {}).get("status") == "error":
                s["tool_errors"] += 1
        elif etype == "error":
            s["error_events"] += 1
            err = ev.get("error") or {}
            s.setdefault("first_error", f"{err.get('type', '')}: {err.get('message', '')}"[:500])
    s["tools"] = dict(tools)
    return s


def diff_stats(ws):
    subprocess.run(["git", "add", "-A"], cwd=ws, capture_output=True)
    r = subprocess.run(["git", "diff", "--cached", "--numstat", "HEAD"], cwd=ws,
                       capture_output=True, text=True)
    files = added = removed = 0
    for line in r.stdout.splitlines():
        a, d, _ = line.split("\t", 2)
        files += 1
        added += int(a) if a.isdigit() else 0
        removed += int(d) if d.isdigit() else 0
    return {"files_changed": files, "lines_added": added, "lines_removed": removed}


def check(task_dir, ws, runner):
    hidden = ws / ".bench_hidden"
    if hidden.exists():
        shutil.rmtree(hidden)
    shutil.copytree(task_dir / "hidden", hidden)
    try:
        if runner == "python":
            r = subprocess.run([sys.executable, str(ROOT / "bench" / "pycheck.py"), str(hidden)],
                               cwd=ws, capture_output=True, text=True, timeout=CHECK_TIMEOUT_S)
            last = (r.stdout.strip().splitlines() or ["{}"])[-1]
            res = json.loads(last)
            return res.get("passed", 0), res.get("total", 0), r.stdout[-4000:] + r.stderr[-4000:]
        if runner == "node":
            files = sorted(str(p) for p in hidden.glob("*.test.js"))
            r = subprocess.run(["node", "--test", "--test-reporter=tap", *files],
                               cwd=ws, capture_output=True, text=True, timeout=CHECK_TIMEOUT_S)
            counts = {}
            for line in r.stdout.splitlines():
                parts = line.split()
                if len(parts) == 3 and parts[0] == "#" and parts[1] in ("pass", "fail", "cancelled") and parts[2].isdigit():
                    counts[parts[1]] = int(parts[2])
            passed = counts.get("pass", 0)
            return passed, passed + counts.get("fail", 0) + counts.get("cancelled", 0), r.stdout[-4000:] + r.stderr[-4000:]
    except subprocess.TimeoutExpired:
        return 0, 0, "check timed out"
    except (json.JSONDecodeError, OSError) as e:
        return 0, 0, f"check crashed: {e}"
    finally:
        shutil.rmtree(hidden, ignore_errors=True)
    raise ValueError(f"unknown runner {runner}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", required=True, help="directory name under arms/ (stock or stack)")
    ap.add_argument("--wave", type=int, default=1)
    ap.add_argument("--model", default=os.environ.get("BENCH_MODEL", ""), help="provider/model[#variant]; same for both arms")
    ap.add_argument("--agent", default="", help="agent to pass with --agent (only use for the stack arm)")
    ap.add_argument("--tasks", default="all", help="comma separated task ids, or 'all'")
    ap.add_argument("--timeout", type=int, default=0, help="per-task timeout in seconds (default: task.json)")
    ap.add_argument("--out", default="results")
    ap.add_argument("--shared-config", default=str(ROOT / "shared" / "opencode.json"),
                    help="config file applied to BOTH arms via OPENCODE_CONFIG (providers etc.)")
    ap.add_argument("--opencode-bin", default=os.environ.get("OPENCODE_BIN", "opencode"))
    ap.add_argument("--mode", choices=["opencode", "solution", "noop"], default="opencode",
                    help="solution/noop skip the agent and are used to self-test the task suite")
    ap.add_argument("--keep-workspaces", action="store_true")
    args = ap.parse_args()

    arm_src = ROOT / "arms" / args.arm
    if not arm_src.is_dir():
        sys.exit(f"no such arm: {arm_src}")
    out = Path(args.out).resolve()
    (out / "logs").mkdir(parents=True, exist_ok=True)
    results_path = out / f"{args.arm}-w{args.wave}.jsonl"

    tasks = load_tasks(args.tasks)
    # Same shuffled order for both arms within a wave, different order across waves.
    random.Random(args.wave).shuffle(tasks)

    scratch_root = Path(tempfile.mkdtemp(prefix=f"bench-{args.arm}-w{args.wave}-"))
    cache_dir = scratch_root / "cache"  # shared within this job so plugin/npm installs are paid once
    # Copy the arm so plugin installs or caches written next to the config never touch the repo.
    arm_dir = scratch_root / "arm"
    shutil.copytree(arm_src, arm_dir, ignore=shutil.ignore_patterns("README.md"))

    print(f"arm={args.arm} wave={args.wave} model={args.model or '(config default)'} tasks={len(tasks)}", flush=True)
    with open(results_path, "a") as results:
        for task_dir in tasks:
            meta = json.loads((task_dir / "task.json").read_text())
            scratch = scratch_root / task_dir.name
            ws = scratch / "ws"
            make_workspace(task_dir, ws)
            log_base = out / "logs" / f"{args.arm}-w{args.wave}-{task_dir.name}"
            rec = {"task": task_dir.name, "arm": args.arm, "wave": args.wave, "model": args.model,
                   "agent": args.agent, "mode": args.mode}
            if args.mode == "opencode":
                env = isolated_env(scratch, arm_dir, Path(args.shared_config), cache_dir)
                timeout_s = args.timeout or meta.get("timeout_s", 600)
                code, timed_out, duration, events_path, stderr_path = run_opencode(
                    args, task_dir, ws, env, log_base, timeout_s)
                usage = summarize_events(events_path)
                rec.update(exit_code=code, timed_out=timed_out, duration_s=round(duration, 2), **usage)
                # No model step at all means the run never really started (bad key, bad model id, crash).
                rec["infra_error"] = usage["steps"] == 0 and usage["tool_calls"] == 0
                if rec["infra_error"]:
                    rec["stderr_tail"] = stderr_path.read_text(errors="replace")[-1500:]
            else:
                if args.mode == "solution":
                    shutil.copytree(task_dir / "solution", ws, dirs_exist_ok=True)
                rec.update(exit_code=0, timed_out=False, duration_s=0.0, infra_error=False)
            rec.update(diff_stats(ws))
            passed, total, check_log = check(task_dir, ws, meta["runner"])
            expected = meta.get("tests") or total
            total = max(total, expected)
            rec.update(passed=passed, total=total, score=round(passed / total, 4) if total else 0.0,
                       solved=bool(total) and passed == total)
            log_base.with_suffix(".check.log").write_text(check_log)
            results.write(json.dumps(rec) + "\n")
            results.flush()
            flag = " INFRA-ERROR" if rec["infra_error"] else (" TIMEOUT" if rec["timed_out"] else "")
            print(f"  {task_dir.name:<22} {passed}/{total}  {rec['duration_s']:>7.1f}s"
                  f"  tok_in={rec.get('tokens_in', 0)} tok_out={rec.get('tokens_out', 0)}{flag}", flush=True)
            if rec.get("first_error"):
                print(f"    error: {rec['first_error']}", flush=True)
            if rec["infra_error"] and rec["stderr_tail"].strip():
                print("    " + rec["stderr_tail"].strip().replace("\n", "\n    ")[-800:], flush=True)

    if not args.keep_workspaces:
        shutil.rmtree(scratch_root, ignore_errors=True)
    print(f"results -> {results_path}")


if __name__ == "__main__":
    main()
