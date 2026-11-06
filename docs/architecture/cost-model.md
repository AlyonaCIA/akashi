# Cost and latency model

Cost and latency per pull request, as functions of quantities that shadow mode measures.
Labels: **[measured]** cites [`evidence.md`](evidence.md); **[decision]** cites a record;
**[estimate]** is a working assumption with its dominant uncertainty named. Prices are
not fixed here: take them from the provider's price list at measurement time.

## Quantities

| Symbol | Meaning | Source |
|---|---|---|
| `S` | Signals Plane 1 emits for the lines and packages the diff adds | Shadow mode |
| `A` | Candidates left after Plane 3's deterministic filters (alias dedup, anchor check) | Shadow mode |
| `f` | Fraction of candidates the cheap classifier escalates to the full verifier | Shadow mode |
| `t_c`, `t_v` | Tokens per call (input + output) for classifier and verifier | Shadow mode |
| `r_c`, `r_v` | Mean extra attempts per call (invalid output, timeout) | Shadow mode |
| `H` | Model hypotheses per pull request that need a witness | Shadow mode |
| `t_g` | Tokens to generate one witness test | Shadow mode |
| `k` | Container runs per witness: 2 (`base`, `head`), 3 with a proposed fix | [decision] ADR-0003 |
| `τ` | Testability: share of hypotheses with `base` passing and `head` failing by the declared assertion | Shadow mode |
| `P` | Findings published per pull request; at most 3 | [decision] ADR-0005 |

## Cost per pull request

Model tokens:

```
T = A · t_c · (1 + r_c)            # classifier over every candidate
  + f · A · t_v · (1 + r_v)        # full verifier over the escalated fraction
  + H · t_g                        # witness generation
```

Money is `T` split into input and output tokens, each multiplied by its model's price,
plus `H · k` runner executions billed as runner-minutes.

The figure that decides viability is **cost per published finding**, `T / P`, not cost
per pull request: a pull request with no admissible finding costs tokens and publishes
nothing.

Witnesses: publishing one witnessed finding takes on average `1 / τ` hypotheses, so
`k / τ` container runs. At the gate threshold `τ = 0.3`, that is about 3.3 hypotheses and
7 to 10 runs per witnessed finding.

## Latency per pull request

Stages run in sequence; calls inside a stage run with concurrency `c`.

```
L = L_1                                   # Plane 1: slowest tool, tools run in parallel
  + ⌈A / c⌉ · L_c · (1 + r_c)             # classifier
  + ⌈f · A / c⌉ · L_v · (1 + r_v)          # verifier
  + ⌈H / c_w⌉ · k · L_run                  # witnesses, c_w containers in parallel
```

`L_1` on Sentoru **[measured]**: `semgrep` 1.4 s, `uv audit` 1.2 s, `ruff` 0.42 s,
`zizmor` 0.26 s, so `L_1 ≈ 1.4 s` plus process start-up. Plane 1 is cacheable by diff
hash and tool versions.

## Where the uncertainty is

- `A` **[estimate]**: dominated by the repository, not by Akashi. Delta restriction should
  keep most pull requests near zero; dependency upgrades are the exception, because one
  lockfile change can carry many advisories.
- `t_v` **[estimate]**: dominated by the size of the causal slice (enclosing function,
  callers, sanitizers). It is the largest per-call term and the first to measure.
- `τ` **[estimate]**: no figure exists for Python application logic. The external figures cited
  in ADR-0003 (about 18%) come from memory-safety bugs in C and C++ judged by
  sanitizers.

## What shadow mode records per pull request

`S`, `A`, `f`; input and output tokens and wall time for every model call; attempts per
call; `H`; the outcome of every witness run (`base`, `head`, `head` with fix); `P`; and the
human label for every candidate. From these: cost per published finding, p50 and p95 of
`L`, and the share of cost spent on candidates that were never published.
