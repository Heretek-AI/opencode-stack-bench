---
name: minimal-diff
description: PLACEHOLDER skill. Use when fixing a bug in existing code, to keep the change small and avoid regressions.
---
- Find the root cause first; reproduce it with a failing test or a one-off script.
- Change the fewest lines that fix the cause. Keep public signatures unchanged.
- Re-run existing tests to check for regressions before finishing.
