# ADR-0004: Privilege separation between components that read hostile input

Status: Proposed · Date: 2026-09-25

## Context

Every input this agent processes is attacker-controlled: the diff, file paths, the PR
title and body, commit messages, code comments, HTML comments invisible in the rendered
view, dependency source, and any `*.md` in the head branch.

Documented consequences of not separating these concerns:

- A CI agent reading a `CLAUDE.md` **from the pull request** was instructed not to flag
  comparison operators "as those modules are reviewed by a separate security team". It
  complied and missed a planted timing oracle. The same agent without that file found it.
- Injection via unsanitised PR titles combined with `pull_request_target` produced a
  supply-chain compromise affecting thousands of repositories; the payload invoked
  installed AI CLIs with their permission-bypass flags to exfiltrate the filesystem.
- Executed-workflow testing finds every provider susceptible to at least one high-severity
  attack in default configuration, and that simulation misses 71.2% of attacks that real
  execution confirms.

Mitigations that live inside the prompt do not count. The countermeasure has to be
enforced by infrastructure, independently of the model.

## Decision

Enforce the plane boundaries in [`../README.md`](../README.md). Concretely:

**Plane 0 — intake.** Trigger on `pull_request`, never `pull_request_target`.
`permissions: {}` at workflow level. `persist-credentials: false` on `actions/checkout`.
No self-hosted runners for public repositories.

**Restore agent configuration from the base branch.** Before any model call, restore
`.claude/`, `.mcp.json`, `CLAUDE.md`, `AGENTS.md` and any instruction file the agent reads
from `base`. Keep the PR-authored versions under a separate path, reference only.

**Plane 2 — the model.** No `GITHUB_TOKEN`, no OIDC request token, no cloud credentials in
the environment. Not scrubbed: absent — a sibling process can read a parent's environment.
Egress limited to the model provider. No general shell tool; typed tools with closed
domains only.

**Separate context windows.** Untrusted content (diff, PR text, tool stdout) goes to a
quarantined window that returns structured values. The window that plans actions never
reads raw untrusted text.

**Plane 3 → Plane 4.** The only thing crossing is a schema-validated JSON document. Prose
is re-rendered from templates; model text occupies bounded slots. This collapses the
exfiltration bandwidth of a compromised model to a few hundred validated characters.

**Plane 4 — posting.** Mint an installation token per PR: one repository,
`pull_requests:write` + `checks:write`, one-hour TTL. Never a personal access token, never
`contents:write`.

**Fork pull requests are not reviewed automatically.** They require an explicit human
command.

## Consequences

- Fork PRs — the highest-value case for an open-source security bot — need a human in the
  admission path. Accepted.
- Two checkouts are required when the agent needs head-branch files.
- The posting service must be a separate deployable. It currently lives outside this
  repository and is unmodelled; that gap has to close before fork review is enabled.

## Alternatives rejected

**Sanitising untrusted content.** Stripping HTML comments, invisible characters and hidden
attributes is worth doing, but vendors who implement it state plainly that new bypasses
emerge. Useful as depth, not as the boundary.

**Guardrail models that classify injection attempts.** Probabilistic defence against an
adversary who can iterate for free.

## What would reverse this

Nothing foreseeable. Least privilege across a trust boundary is not a tuning parameter.
