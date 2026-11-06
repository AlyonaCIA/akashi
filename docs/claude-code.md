# Claude Code skills and plugins

## Project skills

In `.claude/skills/`, versioned with the repository:

- `performance-optimization`: measure before and after any performance change.
- `write-adr`: format and rules for decision records.

## Security plugins

Plugins from [Trail of Bits](https://github.com/trailofbits/skills) (CC BY-SA 4.0) are
declared in `.claude/settings.json`, pinned to a commit. They are not copied into this
repository. Install them once per machine:

```sh
claude plugin marketplace add trailofbits/skills
claude plugin install differential-review@trailofbits --scope project
```

Repeat the install for each plugin under `enabledPlugins`.

| Task | Plugin |
|---|---|
| Review a pull request for security | `differential-review` |
| Run or interpret CodeQL, Semgrep, SARIF | `static-analysis` |
| Find more instances of a confirmed bug | `variant-analysis` |
| Write a Semgrep rule for Plane 1 | `semgrep-rule-creator` |
| Audit configuration and APIs | `insecure-defaults`, `sharp-edges` |
| Audit dependencies | `supply-chain-risk-auditor` |
| Audit workflows that call AI agents | `agentic-actions-auditor` |
| Write witness and property tests | `property-based-testing` |
| Check that tests catch real faults | `mutation-testing` |

## Not enabled

- `fp-check`: its `Stop` hook adds a model call to every turn. Enable it for a triage
  session only.
- `modern-python`: its hooks shim `pip`, `python` and `uv`.

## Moving the pin

Third-party plugins are instructions and scripts from outside this repository. Before
changing the pinned `ref`, review the diff of every enabled plugin for new hooks, MCP
servers and scripts.
