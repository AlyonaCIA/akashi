# ADR-0003: Differential security tests replace generated penetration tests

Status: Proposed · Date: 2026-09-25

## Context

`app/agents/pentester_agent.py` asks a model to write pytest code that exploits the
original vulnerability, from a textual description and the proposed patch. Nothing runs it.

Generating a proof-of-concept that actually reproduces a real vulnerability is measured at
~18–20% success on the two benchmarks for the task. Generating tests for *functional* bugs
is far easier (~60–70%) because the issue text already describes the observable behaviour;
producing a security PoC is a search over an input space under a reachability constraint.
The two numbers are not transferable.

An unexecuted test is worse than no test: it asserts a property nobody checked. And a
patch that preserves functionality without fixing security passes any regression suite —
measured functionality preservation 0.832 against security capability 0.251.

## Decision

Replace PoC generation with a **differential security test**.

The model writes a test asserting a security property — the parser rejects this input, the
endpoint returns 403 for this actor, this token comparison is constant-time. The test is
executed **twice**: against `base` and against `head`.

| base | head | Meaning |
|---|---|---|
| pass | fail | The pull request introduced the regression. Publish. |
| fail | fail | Pre-existing. Record, do not block this PR. |
| pass | pass | Property holds. Suppress. |
| fail | pass | The PR fixed it. Note in the summary. |

Only `pass → fail` is a finding.

## Consequences

- The success criterion is differential, which answers the question a PR reviewer actually
  has — "did this change introduce it?" — rather than "is this code vulnerable?".
- Pre-existing issues stop being attributed to the author who touched the file.
- The test runs in the repository's own harness, so the execution surface is the existing
  test runner rather than arbitrary generated code.
- The output is an artefact the author can merge into their suite.
- Requires two checkouts and two test runs. Budget accordingly; this is Plane 2's most
  expensive branch and should be gated behind verification, not run per signal.

## Alternatives rejected

**Execute generated exploits in a sandboxed microVM.** Isolation is solved and cheap
(~$0.01 per 5-minute microVM with egress disabled). The blocker is not containment, it is
hypothesis quality: at a ~20% reproduction rate, 40 hypotheses per PR means 40 sandbox
starts to publish one finding, and the failure mode is lowering the threshold to "find
more" until the output is noise.

**Keep unexecuted generated tests as advisory output.** They carry the authority of a test
without the evidence of one.

## What would reverse this

A measured hypothesis-reproduction rate above ~10% in shadow mode would make sandboxed
execution worth its budget. Measure before building it.
