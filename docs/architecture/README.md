# Akashi architecture

Target architecture and the decisions behind it. Evidence for every quantitative claim is
in [`evidence.md`](evidence.md); individual decisions are in [`decisions/`](decisions/).

ADR-0001 to ADR-0007 were written against Sentoru, Akashi's predecessor. Paths under
`app/` in their context sections refer to Sentoru's code; figures labelled
**[measured]** were measured on Sentoru.

## The invariant

**A deterministic pass owns recall. The LLM owns precision.**

A pattern matcher cannot decide whether a code path is reachable, already mitigated, or
introduced by this pull request. An LLM can — but it is a poor hypothesis generator when
the search space is unbounded, and a near-useless verifier of its own output.

The current implementation inverts this: the LLM generates findings and nothing filters
them. Every other problem in this document follows from that inversion.

Two corollaries, both measured:

- A second LLM pass over the same context is not verification. Verification requires
  **new evidence** — callers, sanitizers, an executed test. See [ADR-0001](decisions/0001-deterministic-recall-llm-precision.md).
- Utility is a step function in precision and nearly flat in recall. Three false
  positives and the team mutes the bot; effective recall then drops to zero.

## Planes

Planes are separated by two properties that must never coincide: **who holds credentials**
and **who reads attacker-controlled input**.

```
PLANE 0 · INTAKE            no credentials, no LLM
  trigger: pull_request  (never pull_request_target)
  permissions: {}  ·  persist-credentials: false
  normalise diff -> content_key  ·  early-exit gates
        |
PLANE 1 · SIGNALS           deterministic, <3 s, reproducible
  zizmor · ruff S · uv audit · semgrep OSS · guarddog (delta deps only)
  output: Signal[] (SARIF-normalised)
        |
PLANE 2 · VERIFICATION      LLM, no credentials, egress limited to the model provider
  per signal: reachable? already mitigated? introduced by THIS diff?
  context = causal slice, not the whole diff
  PR title/body/comments/*.md -> separate window, marked as data
  agent config restored from the BASE branch
        |
PLANE 3 · ADMISSION         deterministic, no LLM
  CVE-alias dedup · anchor validation · cap · cross-run fingerprint
  no proof -> not published
        |
PLANE 4 · POSTING           holds credentials, never sees hostile input
  installation token minted per PR: one repo,
  pull_requests:write + checks:write, 1 hour TTL
```

Plane 4 is a separate deployable, not yet built. The contract between
Plane 3 and Plane 4 is a validated JSON document and nothing else — no free text, no
shared filesystem, no shared credentials. See
[ADR-0004](decisions/0004-untrusted-input-isolation.md).

## Data contract

A `Signal` is a candidate, not a finding. A `Finding` is a signal that survived
verification and admission.

```python
class Signal(BaseModel):
    source: str  # "ruff" | "uv-audit" | "semgrep" | "zizmor" | "guarddog"
    rule_id: str
    message: str
    file: str
    line: int
    line_text: str  # must match the file at `line`; see ADR-0005
    cwe: str | None
    cve: str | None
    aliases: list[str]  # GHSA/PYSEC/OSV ids for the same CVE
    package: str | None  # dependency advisories: filtered by package, not line


class Finding(BaseModel):
    signal: Signal
    verdict: Literal["reachable", "unreachable", "mitigated", "pre-existing"]
    evidence: list[str]  # file:line citations proving the verdict
    patch: GitPatch | None
    test: DifferentialTest | None
```

`evidence` is mandatory and must contain at least one `file:line` citation that resolves.
A verdict without resolvable evidence is dropped in Plane 3, not surfaced with lower
confidence.

## Package layout

```
src/akashi/
├── signals/            # PLANE 1 — deterministic, no LLM
│   ├── runners.py      #   tool invocation, parallel
│   ├── sarif.py        #   normalise to Signal
│   └── delta.py        #   restrict to what the diff adds
├── admission/          # PLANE 3 — deterministic, no LLM
│   ├── dedup.py
│   ├── anchor.py
│   └── rank.py         #   KEV -> EPSS -> reachability -> CVSS
└── verify/             # PLANE 2 — one LLM call per signal
    └── context.py      #   causal slice: signal + function + callers + sanitizers
```

Planes 0 and 4 live in CI and in the posting service, not in this package.

## Build order

Ordered by measured return, not by dependency.

1. **Plane 1 alone.** Deterministic, cacheable, needs no LLM. Publishes SARIF. Produces a
   product that does not hallucinate before any agent work begins.
2. **Plane 3 without Plane 2.** CVE-alias dedup removed 48% of raw dependency output on
   Sentoru. Anchor validation costs nothing and removes a class of hallucination.
3. **Problem-specification refinement.** Rewriting the input moves Pass@1 further than any
   architectural change measured (see [evidence.md](evidence.md)).
4. **Repository context in prose** — deployment, trust boundaries, authentication.
5. **Plane 2 as a cost cascade.** Cheap classifier over all signals, expensive agent over
   the top fraction.
6. **Plane 0 and Plane 4 hardening.** Required before reviewing pull requests from forks.

## Known unverified

- Function-level reachability for Python is materially less reliable than for Java or Go.
  Reachability is used as a ranking input, never as a suppression filter. See
  [ADR-0005](decisions/0005-finding-admission.md).
