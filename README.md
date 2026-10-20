# opencode-stack-bench

A small A/B benchmark that answers one question: **does my opencode setup actually help?**

It runs the same coding tasks, with the same model, through two arms of opencode v2:

| Arm | Config dir | What it gets |
|---|---|---|
| `stock` | `arms/stock/` (empty) | opencode's built-in defaults only |
| `stack` | `arms/stack/` | your `opencode.json`, `AGENTS.md`, agents, skills, plugins and MCP servers |

Each **wave** runs every task once per arm. Several waves give you a repeated, paired measurement,
and the report tells you whether the difference is real or noise.

## Quick start

1. **Fill in your stack.** Replace the placeholders in [`arms/stack/`](arms/stack/README.md).
   Everything marked `PLACEHOLDER` is an example.
2. **Add a provider key** as a repository secret (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
   `OPENROUTER_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY` or `OPENCODE_API_KEY` are wired up already;
   add others to the `env:` block in `.github/workflows/bench.yml`).
   Secrets for MCP servers or plugins go in the same block.
3. **Run it.** Actions → *Benchmark stock vs stack* → *Run workflow*. Set `model`
   (for example `anthropic/claude-sonnet-4-5`; run `opencode models` locally for exact ids),
   or set a `BENCH_MODEL` repository variable once.
4. **Read the result** on the run's summary page. The `report` artifact has `summary.md`,
   `summary.json`, every raw result row, and each run's full opencode event log.

## What a run does

```
plan ──► run (wave × arm matrix) ──► report
```

For each task, `bench/run_arm.py`:

1. copies `tasks/<id>/repo/` into a fresh git workspace;
2. gives opencode a fresh `HOME`/XDG tree, `OPENCODE_CONFIG_DIR=arms/<arm>`, and
   `OPENCODE_DISABLE_CLAUDE_CODE=1`, so nothing leaks between tasks or arms;
3. runs `opencode run --standalone --auto --format json -m <model> "<prompt.md>"` with a timeout;
4. copies in the hidden tests from `tasks/<id>/hidden/` (the agent never sees them) and scores
   the fraction that pass;
5. records tokens, cost, steps, tool calls, wall time and diff size from the JSON event stream.

The stack arm job also prints what opencode really loaded from `arms/stack/` (config sources,
agents, skills, plugins, MCP servers) in the **Validate stack config** step. opencode drops unknown
config keys silently, so check that step after you change the stack.

## Reading the report

- **Verdict** uses the paired difference (stack minus stock) over every (task, wave) pair, with a
  bootstrap 95% confidence interval. "Helps" means the whole interval is above zero.
- **Sign test** counts how many pairs the stack won, tied and lost.
- **Wave-to-wave SD** shows how noisy the model is. If it is large compared to the gap
  between arms, run more waves.
- **Infra errors** (bad key, unknown model, crash before any model step) are excluded and listed.
- Cost and time matter too. A stack that ties on score but is cheaper or faster can still be worth it.

Rough guide: 3 waves × 6 tasks gives 18 pairs, enough to spot a large effect. For a small one,
use 5 to 10 waves or add tasks.

## Workflow inputs

| Input | Default | Notes |
|---|---|---|
| `model` | `vars.BENCH_MODEL` | `provider/model[#variant]`, same for both arms |
| `waves` | `3` | 1 to 20 |
| `tasks` | `all` | comma separated ids from `tasks/` |
| `opencode_version` | `latest` | npm version of `@opencode/cli` |
| `stack_agent` | empty | run the stack arm with `--agent <name>` (e.g. `bench-builder`) |
| `timeout` | `0` | per-task seconds; 0 uses each `task.json` |
| `max_parallel` | `4` | lower it if you hit rate limits |

## Tasks

| Id | Kind |
|---|---|
| `py-business-days` | bug fix with edge cases |
| `py-wordfreq-cli` | add CLI flags without breaking behaviour |
| `py-parse-duration` | implement a parser from a spec |
| `py-inventory` | multi-module bug hunt plus a new method |
| `js-lru-cache` | implement a data structure with TTL |
| `js-semver-sort` | fix and complete a SemVer library (hardest) |

Add your own: create `tasks/<id>/` with `task.json` (`runner` is `python` or `node`, `tests` is the
hidden test count), `prompt.md`, `repo/` (starting code), `hidden/` (tests: `test*.py` for Python,
`*.test.js` for Node) and `solution/` (files copied over `repo/` that must pass every hidden test).
Tasks that mirror your real work tell you the most.

The **Self-test task suite** workflow runs on every push without calling a model. It checks that
each reference solution passes and no untouched fixture already passes.

## Run locally

```bash
npm i -g @opencode/cli
export ANTHROPIC_API_KEY=...
python3 bench/run_arm.py --arm stock --wave 1 --model anthropic/claude-sonnet-4-5 --out results
python3 bench/run_arm.py --arm stack --wave 1 --model anthropic/claude-sonnet-4-5 --out results
python3 bench/report.py results
bash bench/inspect_arm.sh arms/stack   # what opencode loads from your stack
bash bench/selftest.sh                 # validate the task suite
```

`shared/opencode.json` is applied to both arms through `OPENCODE_CONFIG`. Use it for things that
must be identical in both, such as a custom provider block.

## Notes on opencode v2

Checked against `@opencode/cli` 2.1.1:

- v2 config keys are `agents` (with `system` for the prompt), `plugins`, and `mcp.servers.<name>`
  (with `disabled`). v1 names (`agent`, `plugin`, `mcp.<name>`, `prompt`, `enabled`) are migrated
  automatically.
- From the config dir, opencode loads `opencode.json`, `AGENTS.md`, `agents/*.md`,
  `skills/<name>/SKILL.md` and `plugins/*.{ts,js}`.
- Relative `instructions` paths resolve against the task workspace, not the config dir. Use
  `{env:OPENCODE_CONFIG_DIR}/file.md` for extra rule files that live in `arms/stack/`.
- `opencode run` without `--standalone` talks to a shared background service, which would mix
  configs between arms; the harness always passes `--standalone`.
- opencode picks the project directory from `$PWD`, so the harness sets it for each task.
