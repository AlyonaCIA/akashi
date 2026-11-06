# ADR-0005: Deterministic admission and prioritisation before publication

Status: Proposed · Date: 2026-09-25

## Context

Precision is a step function in this product: a few false positives and the bot is muted,
after which effective recall is zero. Independent measurement of AI review agents on a
corpus containing clean PRs puts precision at 16.65%; the most credible vendor figure,
self-published, is 35.7–39.3% after their own verification and filtering.

Two cheap sources of noise are measurable in this repository. 48% of raw `uv audit` output
is duplication — 244 of 267 CVE groups carry both a GHSA and a PYSEC record for the same
vulnerability. And nothing currently checks that a model-reported line number corresponds
to the line the model claims is there.

Techniques with production evidence: feedback clustering (address rate 19% → 55%),
per-(tool × language × category) confidence thresholds with a separate grader model (75%
useful, 65% addressed against a 51% human baseline), and explicitly targeting a precision
number rather than discovering one.

## Decision

Plane 3 runs no model. In order:

1. **Deduplicate by CVE alias.** Prefer the GHSA record over PYSEC. One line of code,
   removes 48% of dependency output here.
2. **Drop what does not reach production runtime** — `--no-dev`, undeployed extras.
3. **Validate the anchor.** Reject any finding whose `line_text` does not match the file
   content at `line`. Zero model cost; removes an entire hallucination class.
4. **Require evidence.** At least one resolving `file:line` citation. No citation, no
   publication.
5. **Rank**: KEV unconditionally → **union** with EPSS ≥ 0.1 → reachability → CVSS
   Environmental as the final tiebreak only.
6. **Cap at three findings per PR.** Overflow is summarised by count, never silently
   dropped.
7. **Fingerprint** `(path, anchor, rule_id, hash(snippet))` for cross-run idempotency.
   A partial or failed run must never mark a finding resolved by absence.

Set an explicit precision target before launch and calibrate against it in shadow mode.

## Consequences

- Reachability is a **ranking input, never a suppression filter**. Studies disagree by two
  orders of magnitude on what fraction survives, and one execution-oracle study found 11 of
  41 executed cases invisible to static analysis. For Python specifically, whole-program
  call-graph precision measures ~0.19. Findings are marked `deprioritized`, not suppressed,
  and re-evaluated.
- KEV is a union term, not a substitute: 25.0% of KEV CVEs score below EPSS 0.088, and
  adding all of KEV to that threshold costs +2.3% volume.
- CVSS is not used for ordering. Its AUC for predicting exploitation is 0.051.
- Advisories whose only provenance is NVD or an unreviewed GHSA are marked low-confidence.
  8.2% of GHSA is human-reviewed, and fabricated CVEs have propagated into both databases.

## Alternatives rejected

**LLM-as-judge for severity.** Measured as nearly random on the generating model's own
output, and steerable by PR text. If a judge is introduced later it must be a different
model reading different evidence.

**Global confidence threshold.** A single threshold averages over distributions with
different shapes. Threshold per (tool × language × category).

## What would reverse this

A reachability implementation with a measured false-negative rate on our corpus low enough
to justify suppression. Until then, ranking only.
