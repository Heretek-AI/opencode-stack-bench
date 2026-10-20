# Stack arm (fill this in)

Everything in this folder becomes opencode's config directory (`OPENCODE_CONFIG_DIR`) for the
stack arm. Replace the placeholders with your real setup:

| Path | What it is |
|---|---|
| `opencode.json` | Main config: `agents`, `mcp.servers`, `plugins`, `skills`, `instructions`, permissions, etc. |
| `AGENTS.md` | Global rules, loaded automatically from the config dir. |
| `agents/*.md` | Agents as markdown (frontmatter + system prompt). |
| `skills/<name>/SKILL.md` | Skills. The folder name is the skill id. |
| `plugins/*.ts` | Local plugins, loaded automatically. npm plugins go in `opencode.json` → `plugins`. |

Do not set `model` here if you want a fair test: the workflow passes the same `--model` to both
arms. If your stack has its own primary agent, set the workflow's `stack_agent` input to its name.

Secrets that MCP servers or plugins need go in repository secrets and get exposed in the
workflow's `env:` block (see the comment there). Reference them in config as `{env:NAME}`.

This README is not copied into the config dir.
