# ADR-0001: A deterministic pass owns recall; the LLM owns precision

Status: Proposed · Date: 2026-09-25

## Context

The agent currently uses an LLM as the primary vulnerability detector over a raw diff.
Measured behaviour of that configuration: the same 7B model scores 68.26% F1 on a noisy
benchmark and 3.09% on a de-duplicated one; frontier models separate a vulnerable function
from its patched twin with 0.06–0.14 pairwise accuracy; renaming a variable flips the
verdict in 26% of cases. Against a 1% base rate, a detector that flags a third of benign
code has ~2% precision regardless of recall.

Meanwhile a second LLM pass scoring its own output 1–10 was measured as "nearly random",
and is separately steerable by text the pull-request author controls.

## Decision

Split recall and precision across components:

- **Recall** belongs to deterministic tools (`src/akashi/signals/`). They emit `Signal` objects —
  candidates, reproducible, cacheable, no model in the path.
- **Precision** belongs to one LLM call per signal (`src/akashi/verify/`). Its job is to decide
  reachability, existing mitigation, and whether this diff introduced the path — by
  retrieving evidence it did not already have: the enclosing function, its callers, the
  sanitizers on the path.
- A signal that survives with at least one resolving `file:line` citation becomes a
  `Finding`. Without citations it is dropped, not downgraded.

The verification call must receive **new evidence**, not a second reading of the same
prompt. This is the property that distinguishes verification from self-grading.

## Consequences

- The LLM can no longer invent a vulnerability class that no tool emits. This is a real
  loss of recall, addressed in [ADR-0006](0006-cwe-scope-restriction.md).
- Findings become reproducible in their candidate set, even though verdicts are not.
- Cost scales with the number of signals requiring verification, not with diff size. This
  is the variable to budget against.
- The deterministic pass is useful on its own and ships first.

## Alternatives rejected

**Keep the LLM as detector, add a filter.** Filtering a distribution you generated yourself
cannot recover precision the generator never had; the measured self-judgement result closes
this path.

**Two detectors in parallel with an arbiter** (Checkmarx Fusion, AWS Continuum). Defensible
— frontier models and rule engines find genuinely different things — but it doubles cost
and forfeits scan-to-scan reproducibility for a recall gain we cannot yet measure. Revisit
once Plane 1 has a baseline.

## What would reverse this

A measurement on our own corpus showing the LLM-as-detector path finds classes the tool
path misses at a precision above the team's tolerance. Run it in shadow mode.
