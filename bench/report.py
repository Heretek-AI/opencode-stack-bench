#!/usr/bin/env python3
"""Aggregate results/*.jsonl into a stock-vs-stack comparison.

Writes summary.md (also suitable for $GITHUB_STEP_SUMMARY) and summary.json.
The headline number is the paired difference in hidden-test score
(stack minus stock) over every (task, wave) pair, with a bootstrap 95% CI.
"""
import argparse
import json
import math
import random
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

BASE, TREAT = "stock", "stack"


def load(results_dir):
    rows = []
    for p in sorted(Path(results_dir).rglob("*.jsonl")):
        if "logs" in p.parts:
            continue
        for line in p.read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def mean(xs):
    return st.fmean(xs) if xs else float("nan")


def sd(xs):
    return st.stdev(xs) if len(xs) > 1 else 0.0


def bootstrap_ci(diffs, n=10000, seed=0):
    if not diffs:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    k = len(diffs)
    means = sorted(st.fmean(rng.choices(diffs, k=k)) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def sign_test_p(wins, losses):
    """Exact two-sided binomial sign test, ties dropped."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def fmt(x, nd=3):
    if isinstance(x, float) and math.isnan(x):
        return "n/a"
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def arm_stats(rows):
    ok = [r for r in rows if not r.get("infra_error")]
    waves = defaultdict(list)
    for r in ok:
        waves[r["wave"]].append(r["score"])
    wave_means = [mean(v) for _, v in sorted(waves.items())]
    return {
        "runs": len(rows),
        "infra_errors": len(rows) - len(ok),
        "timeouts": sum(1 for r in ok if r.get("timed_out")),
        "mean_score": mean([r["score"] for r in ok]),
        "solve_rate": mean([1.0 if r["solved"] else 0.0 for r in ok]),
        "wave_means": wave_means,
        "wave_sd": sd(wave_means),
        "mean_duration_s": mean([r.get("duration_s", 0) for r in ok]),
        "mean_tokens_in": mean([r.get("tokens_in", 0) for r in ok]),
        "mean_tokens_out": mean([r.get("tokens_out", 0) for r in ok]),
        "mean_cost_usd": mean([r.get("cost_usd", 0) for r in ok]),
        "total_cost_usd": sum(r.get("cost_usd", 0) for r in ok),
        "mean_tool_calls": mean([r.get("tool_calls", 0) for r in ok]),
        "mean_lines_changed": mean([r.get("lines_added", 0) + r.get("lines_removed", 0) for r in ok]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="?", default="results")
    ap.add_argument("--out", default=None, help="directory for summary.md/json (default: results dir)")
    ap.add_argument("--min-effect", type=float, default=0.02,
                    help="score difference below which a significant result is still called negligible")
    args = ap.parse_args()

    rows = load(args.results)
    if not rows:
        sys.exit(f"no results found under {args.results}")
    by_arm = defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)
    order = [a for a in (BASE, TREAT) if a in by_arm] + sorted(a for a in by_arm if a not in (BASE, TREAT))
    stats = {arm: arm_stats(by_arm[arm]) for arm in order}

    # Paired comparison per (task, wave).
    idx = {(r["arm"], r["task"], r["wave"]): r for r in rows if not r.get("infra_error")}
    pairs = []
    for (arm, task, wave), r in idx.items():
        if arm == TREAT and (BASE, task, wave) in idx:
            pairs.append((task, wave, idx[(BASE, task, wave)], r))
    diffs = [t["score"] - b["score"] for _, _, b, t in pairs]
    wins = sum(1 for d in diffs if d > 1e-9)
    losses = sum(1 for d in diffs if d < -1e-9)
    ties = len(diffs) - wins - losses
    lo, hi = bootstrap_ci(diffs)
    mdiff = mean(diffs)
    p = sign_test_p(wins, losses)

    if not pairs:
        verdict = "No paired runs: both arms need results for the same task and wave."
    elif lo > 0 and mdiff >= args.min_effect:
        verdict = f"**Your stack helps.** It scores {mdiff:+.3f} higher on average (95% CI {lo:+.3f} to {hi:+.3f})."
    elif hi < 0 and -mdiff >= args.min_effect:
        verdict = f"**Your stack hurts.** It scores {mdiff:+.3f} lower on average (95% CI {lo:+.3f} to {hi:+.3f})."
    else:
        verdict = (f"**No clear quality difference.** Mean difference {mdiff:+.3f} (95% CI {lo:+.3f} to {hi:+.3f}). "
                   "Run more waves to narrow the interval, or compare cost and time below.")

    per_task = defaultdict(lambda: {BASE: [], TREAT: []})
    for r in rows:
        if not r.get("infra_error") and r["arm"] in (BASE, TREAT):
            per_task[r["task"]][r["arm"]].append(r)

    md = ["# opencode stack benchmark", ""]
    models = sorted({r.get("model") or "(config default)" for r in rows})
    waves = sorted({r["wave"] for r in rows})
    md += [f"Model: `{', '.join(models)}` · Waves: {len(waves)} · Tasks: {len(per_task)} · Paired runs: {len(pairs)}", ""]
    md += [verdict, ""]
    md += [f"Paired (task, wave) outcomes: stack better {wins}, tied {ties}, worse {losses}; sign test p = {p:.3f}.", ""]

    md += ["## Arms", "", "| Metric | " + " | ".join(stats) + " |", "|---|" + "---|" * len(stats)]
    metrics = [
        ("Mean hidden-test score", "mean_score", 3), ("Solve rate (all tests pass)", "solve_rate", 3),
        ("Wave-to-wave SD of mean score", "wave_sd", 3), ("Mean wall time (s)", "mean_duration_s", 1),
        ("Mean input tokens", "mean_tokens_in", 0), ("Mean output tokens", "mean_tokens_out", 0),
        ("Mean cost per task (USD)", "mean_cost_usd", 4), ("Total cost (USD)", "total_cost_usd", 4),
        ("Mean tool calls", "mean_tool_calls", 1), ("Mean lines changed", "mean_lines_changed", 1),
        ("Runs", "runs", None), ("Infra errors (excluded)", "infra_errors", None), ("Timeouts", "timeouts", None),
    ]
    for label, key, nd in metrics:
        cells = []
        for s in stats.values():
            v = s[key]
            cells.append(str(v) if nd is None else (fmt(float(v), nd) if nd else f"{v:,.0f}" if not math.isnan(v) else "n/a"))
        md.append(f"| {label} | " + " | ".join(cells) + " |")
    md.append("")

    md += ["## Per task (mean score across waves)", "", f"| Task | {BASE} | {TREAT} | Δ | {BASE} time (s) | {TREAT} time (s) |",
           "|---|---|---|---|---|---|"]
    task_rows = {}
    for task, arms in sorted(per_task.items()):
        b = mean([r["score"] for r in arms[BASE]])
        t = mean([r["score"] for r in arms[TREAT]])
        bt = mean([r.get("duration_s", 0) for r in arms[BASE]])
        tt = mean([r.get("duration_s", 0) for r in arms[TREAT]])
        task_rows[task] = {BASE: b, TREAT: t, "delta": t - b}
        md.append(f"| {task} | {fmt(b)} | {fmt(t)} | {fmt(t - b, 3) if not math.isnan(t - b) else 'n/a'} | {fmt(bt, 1)} | {fmt(tt, 1)} |")
    md.append("")

    md += ["## Per wave (mean score)", "", "| Wave | " + " | ".join(stats) + " |", "|---|" + "---|" * len(stats)]
    for w in waves:
        cells = [fmt(mean([r["score"] for r in by_arm[a] if r["wave"] == w and not r.get("infra_error")])) for a in stats]
        md.append(f"| {w} | " + " | ".join(cells) + " |")
    md.append("")

    infra = [r for r in rows if r.get("infra_error")]
    if infra:
        md += ["## Infra errors", "", "These runs produced no model steps (bad API key, unknown model, crash) and are excluded:", ""]
        for r in infra[:20]:
            md.append(f"- {r['arm']} w{r['wave']} {r['task']}: exit {r.get('exit_code')} {r.get('first_error', '')}".rstrip())
        md.append("")

    md += ["## How to read this", "",
           "- Score is the fraction of hidden tests passing after the agent finishes; the agent never sees these tests.",
           "- Each wave runs every task once per arm, with the same model, so the only difference is your config.",
           "- The CI comes from resampling the paired (task, wave) differences. If it straddles 0, you need more waves "
           "or harder tasks before concluding anything.",
           "- A stack that ties on score but is cheaper or faster can still be worth keeping.", ""]

    out = Path(args.out or args.results)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text("\n".join(md))
    (out / "summary.json").write_text(json.dumps({
        "verdict": verdict, "mean_diff": mdiff, "ci95": [lo, hi], "wins": wins, "ties": ties, "losses": losses,
        "sign_test_p": p, "arms": stats, "per_task": task_rows}, indent=2, default=str))
    print("\n".join(md))
    if not pairs:
        sys.exit(1)


if __name__ == "__main__":
    main()
