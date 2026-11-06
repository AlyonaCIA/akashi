# ADR-0002: Phases and context partitioning, not agent roles

Status: Proposed · Date: 2026-09-25

## Context

`app/agent.py` composes a `SequentialAgent` of three role-named agents — Analyst, Fixer,
Pentester — plus an orchestrator and an optional Search agent. All five run
`gemini-2.5-flash`.

That configuration has been measured directly. With a capability gap (strong model
directing a weak one) multi-agent matches a single strong agent at lower cost: 62% vs 60%.
With the **same model in both roles it is worse than the single agent: 42% vs 44%**. The
proposed mechanism is that models are trained as monolithic agents, so splitting them into
director and worker fights their training distribution.

The same study isolates where the value actually is: a review-only loop adds 2 pp;
structured exploration and planning add 11 pp.

Multi-agent designs that do win share a different property — they partition **context or
workspace**, not persona: git worktrees, event-based message passing, dedicated explorer
subagents. The strongest security-repair result defines its subagents by the *kind of
context each collects* (dataflow, runtime crash semantics, commit history), not by job
title.

## Decision

Replace the role pipeline with phases. Each phase has a distinct input contract:

| Phase | Input | Model |
|---|---|---|
| Signals | diff + repo | none |
| Verification | one signal + its causal slice | one call per signal, parallel |
| Admission | verified findings | none |

Parallelism comes from **one verification call per signal with a disjoint context window**,
which is context partitioning, not role-play. The prompt content in `app/prompts/` survives;
the topology does not.

Keep a single model tier for verification. Introduce a second tier only as a cost cascade
(cheap classifier over all signals, expensive agent over the top fraction) — a capability
gap deployed for cost, not for hierarchy.

## Consequences

- Fewer sequential LLM hops; latency becomes a function of the slowest verification, not
  of the chain length.
- Session state as the coupling mechanism (`output_key` chaining) disappears. Phases pass
  typed objects.
- The system no longer depends on one agent correctly summarising for the next.

## Alternatives rejected

**Keep roles, give each a different model.** Would satisfy the capability-gap condition,
but buys hierarchy we have no evidence we need, and triples the model surface to maintain.

**Single agent with tools, no phases.** Competitive on general software tasks, but gives up
the deterministic signal set that [ADR-0001](0001-deterministic-recall-llm-precision.md)
depends on.

## What would reverse this

Evidence that our verification step benefits from genuinely different context per role — at
which point the correct split is by context type, not by job title.
