# ADR-0006: Restrict scope by CWE class

Status: Proposed · Date: 2026-09-25

## Context

Repair reliability splits sharply by vulnerability locality. On the same system with the
same model: **81% Pass@1 on syntactically local CWEs, 42% on interprocedural dataflow
cases** — which are precisely the ones that justify buying a static analyser.

Vendors already exploit this. Pixee publishes its routing: SQL injection by concatenation,
command injection, path traversal, SSRF, weak crypto and XXE go through deterministic AST
codemods with, in their words, zero hallucination risk. Only classes that cannot be
expressed as a transformation reach a model.

The worked example in `app/prompts/fixer_agent.md` is SQL injection by string
concatenation — a class the industry already fixes with a deterministic transformation.

## Decision

Three tiers, and the tier is part of the published finding.

**Tier A — deterministic transformation, no model.** SQL injection by concatenation,
command injection via `subprocess` with `shell=True`, path traversal, SSRF, weak
hashing/crypto, XXE, `pickle` deserialisation of untrusted input, hardcoded secrets.
Detected by rule, fixed by codemod, verified by re-running the rule.

**Tier B — signal plus LLM verification.** Classes with a static signature where
reachability decides whether the signal matters. This is the main path and where
[ADR-0001](0001-deterministic-recall-llm-precision.md) applies.

**Tier C — generate and test differentially.** Missing ownership checks on authenticated
endpoints, broken authorization, tenant leakage, secrets in error-path logging. These have
**no static signature**; no tool emits them as a candidate. The only available oracle is
[ADR-0003](0003-differential-security-tests.md), and the budget per finding is much higher.

Anything outside the three tiers is out of scope and says so. Silence about an unclaimed
class is better than a low-confidence guess.

## Consequences

- Tier A findings are reproducible and effectively free. They should be the majority of
  published output early on.
- Tier C is where code written by agents actually fails — a field study of 300 PRs found
  its three serious findings were missing ownership checks, secrets in error logging, and
  path traversal in an export path. Scoping it out entirely would forfeit the product's
  reason to exist; scoping it in without a differential oracle produces noise.
- Restricting scope is cheaper than improving the oracle and can ship immediately.

## Alternatives rejected

**Unbounded CWE coverage.** What exists today. It spends the same budget per class
regardless of whether the model is reliable on it, and it publishes Tier C guesses with
Tier A confidence.

**Tier A only.** Reliable, and roughly what a linter already gives the team. Not worth a
multi-agent system.

## What would reverse this

Measured per-CWE precision on our own corpus. The tier boundaries are hypotheses derived
from published splits; they should be replaced by our own numbers as soon as shadow mode
produces enough labelled findings.
