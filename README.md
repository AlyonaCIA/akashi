# Akashi

[![CI](https://github.com/AlyonaCIA/akashi/actions/workflows/ci.yml/badge.svg)](https://github.com/AlyonaCIA/akashi/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

**Publish a security finding on a pull request only when it can be proven.**

*Akashi* (証) is Japanese for proof, evidence. AI code reviewers that flag everything get
muted, and a muted reviewer catches nothing. Akashi inverts the usual design: deterministic
tools generate candidates, a model judges them against new evidence, and an admission
layer discards anything that cannot be checked.

![Akashi architecture](docs/assets/architecture.svg)

## How it works

| Plane | Role | Model | Credentials |
|---|---|---|---|
| 0 · Intake | Normalise the diff; run only on `pull_request` | No | No |
| 1 · Signals | `ruff` security rules, `zizmor`, `uv audit`, `semgrep` on what the diff adds | No | No |
| 2 · Verification | Judge each signal: reachable, mitigated, introduced by this change | Yes | No |
| 3 · Admission | Deduplicate, validate anchors, require `file:line` evidence, cap output | No | No |
| 4 · Posting | Publish validated results with a short-lived, per-PR token | No | Yes |

Two rules hold the design together:

- **Recall belongs to deterministic tools; precision belongs to the model.** The model
  never invents a finding, it only accepts or rejects a candidate.
- **The plane that reads attacker-controlled input never holds credentials.** Only
  schema-validated JSON crosses the trust boundary.

Hypotheses that come from the model also need a **witness**: a test that passes on `base`
and fails on `head`, executed in an isolated sandbox. The sandbox is built only if
measurement shows enough hypotheses can be witnessed.

## Status

Repository setup. Planes 1 to 4 are designed and migrate from Sentoru in separate pull
requests.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run pyright
```

## CI/CD

- **CI** (`ci.yml`) on every pull request and on `main`: lint, strict type check, tests
  on Python 3.12–3.14 with coverage, workflow security (`actionlint`, `zizmor`), and a
  build smoke test. `CI success` aggregates every job.
- **Release** (`release.yml`) on a `vX.Y.Z` tag matching the project version: builds the
  distributions, attests their provenance, and publishes a GitHub release.
- **Dependabot** updates GitHub Actions and Python dependencies weekly, after a seven-day
  cooldown.

All actions are pinned by commit SHA, and every job receives only the permissions it
needs.

## Origin

Akashi continues [Sentoru](https://github.com/Jorgelmh/sentoru-agent), by Jorge Mendez,
Lena Araujo and Juan Camilo Guevara. See [NOTICE](NOTICE).

## License

[Apache 2.0](LICENSE)
