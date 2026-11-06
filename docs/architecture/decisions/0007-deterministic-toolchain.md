# ADR-0007: Toolchain for the deterministic signal pass

Status: Proposed · Date: 2026-09-25

## Context

Plane 1 must be fast enough to run on every pull request, reproducible, and cheap enough
that its output can be cached by diff hash. Every candidate below was run against this
repository (272 packages, 17 Python files in `app/`); figures are in
[`../evidence.md`](../evidence.md).

## Decision

Run these, in parallel, on the delta only:

| Tool | Latency | Role |
|---|---:|---|
| `zizmor` on `.github/workflows/` | 0.26 s | CI workflow misconfiguration |
| `ruff check --select S` | 0.42 s | Python security lint |
| `uv audit --no-dev` | 1.2 s | Dependency advisories via OSV |
| `semgrep --config=p/python --config=p/secrets` (OSS, local) | 1.4 s | Pattern SAST |
| `guarddog`, delta dependencies only | ~5 s/package | Malicious package detection |

`zizmor` is first because the initial vector of the `ultralytics` PyPI compromise was
GitHub Actions script injection, and this repository is already affected: 54 findings
including `actions/checkout@main` (a mutable ref), workflow-level `id-token: write`, and
three `secrets: inherit`.

Add to `pyproject.toml`:

```toml
[tool.ruff.lint]
select = [..., "S"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]        # assert is the point of a test
"notebooks/**" = ["S101"]
```

## Excluded, with reasons

- **Bandit.** Identical result to `ruff --select S` on this repository, 4× slower, one
  more dependency. Ruff is already in the toolchain.
- **pip-audit.** Same 420 findings against the same OSV backend in 60 s versus 1.2 s.
  Keep it in a nightly job as a fallback source, not in the PR path.
- **Pysa.** The only serious open-source interprocedural taint analyser for Python, but
  Pyre is archived and Pysa is mid-migration onto Pyrefly. Watch, do not adopt.
- **Full-tree malware scanning.** At roughly one malicious package per 10⁴–10⁵
  publications, a 99%-precision detector over the whole tree produces mostly false
  positives. Scan only what the PR adds or upgrades — typically 0–3 packages.
- **SBOM generation in the PR.** `uv.lock` is already a resolved transitive graph with
  hashes; an SBOM derived from it is a format translation. 52.9% of real-world SBOMs
  declare no edges at all. Generate at release, and only when an external consumer exists
  — the CRA's main obligations apply from December 2027.

## Safety CLI

`.github/workflows/_dependency_scanning.yml` declares `on: workflow_call` and has no
callers; it has never run. Either wire it up or delete it.

Its value in this architecture is not scanning — `uv audit` is 50× faster for the same
answer — but the MCP server at `app/tools.py:180`, which gives Plane 2 a vulnerability
intelligence lookup during verification. Keep it there, not as a gate.

## Consequences

- Plane 1 completes in under 3 s for a typical PR and is cacheable by diff hash.
- CI gains a reproducible security gate independent of any model, deployable before any
  agent work.
- Pattern SAST detects roughly 13% of real vulnerabilities per commit. This is a hygiene
  control, not a detection control, and the pipeline must not present it as the latter.

## What would reverse this

`uv audit` is a preview feature with a single data source and no fallback. If Astral
changes its interface or OSV becomes unavailable, promote `pip-audit -s pypi` from the
nightly job to the PR path and accept the 60 s.
