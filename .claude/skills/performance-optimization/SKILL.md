---
name: performance-optimization
description: Measure-first performance work for Akashi. Use when a change targets latency, throughput, memory or cost per pull request, when someone claims code is slow or fast, or before adding a cache, parallelism or a faster dependency.
---

# Performance optimization

No change ships on a performance claim without a measurement before and after.

## Workflow

1. **Name the metric and the budget.** Wall time per pull request, p50 and p95; peak RSS;
   model tokens per pull request. Plane 1 budget: under 3 s for a typical pull request.
2. **Fix the workload.** A named input (diff, repository, commit) that anyone can rerun.
   Record it in the pull request.
3. **Baseline.** At least 20 runs; report p50 and p95, not the mean. Separate cold and
   warm runs.
4. **Locate the cost before changing code.**
   - CPU: `uv run python -m cProfile -s cumtime -m <module>`, or `uvx py-spy record`.
   - Memory: `tracemalloc` snapshots around the suspect call.
   - Subprocesses dominate Plane 1; time each tool separately before touching Python.
5. **State the complexity** of the path you change, in terms of its inputs
   (signals, added lines, packages). A constant-factor gain on an O(n²) path is not a fix.
6. **Change one thing.** Re-measure on the same workload.
7. **Report the arithmetic** in the pull request: before, after, n, p50, p95, and the
   dominant uncertainty.

## Rules

- Correctness first: the existing tests must pass unchanged.
- A cache needs a key that captures every input; for Plane 1 that is the diff hash plus
  tool versions.
- Parallelism needs a bound. Unbounded fan-out over model calls is a cost incident.
- Do not trade away a security property (sandbox flags, timeouts, output caps) for speed.
- If the gain is under the run-to-run noise, it is not a gain.
