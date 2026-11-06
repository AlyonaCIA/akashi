# Evidence

Quantitative basis for [`README.md`](README.md) and [`decisions/`](decisions/).
Labels: **[measured]** = run against this repository, **[peer-reviewed]**,
**[vendor]** = self-published without disclosed methodology.

## LLMs as vulnerability detectors

| Claim | Figure | Source |
|---|---|---|
| Benchmark quality dominates reported skill | Same 7B model: 68.26% F1 on BigVul, **3.09% F1 on PrimeVul** | [arXiv:2403.18624](https://arxiv.org/abs/2403.18624), ICSE 2025 **[peer-reviewed]** |
| Cannot separate vulnerable from patched twin | 0.06–0.14 pairwise accuracy | [arXiv:2406.11147](https://arxiv.org/abs/2406.11147) **[peer-reviewed]** |
| Scaling does not fix it | Plateau at ~0.30 pairwise accuracy across model generations | [arXiv:2606.04739](https://arxiv.org/abs/2606.04739) **[peer-reviewed]** |
| Verdict flips on cosmetic edits | Renaming functions or variables flips 26% (PaLM2) / 17% (GPT-4) | [arXiv:2312.12575](https://arxiv.org/abs/2312.12575), IEEE S&P 2024 **[peer-reviewed]** |
| Frontier recall on a real corpus | 35–40% recall at ~95% precision, 1,913 cases | [Corgea](https://corgea.com/blog/we-benchmarked-7-models-on-1913-real-vulnerabilities) **[vendor]** |
| Field precision without an oracle | 1 of 5 findings self-labelled "confirmed" was real | [curl](https://daniel.haxx.se/blog/2026/05/11/mythos-finds-a-curl-vulnerability/) |

## Verification

| Claim | Figure | Source |
|---|---|---|
| Self-judgement is not verification | Severity scoring by the generating model was "nearly random" | [Greptile](https://www.greptile.com/blog/make-llms-shut-up) |
| Self-judgement is attacker-steerable | "Prior approval" framing drops refusal below 35% for small models; 20–30% security-reasoning rate on use-after-free for the best | [arXiv:2606.13757](https://arxiv.org/abs/2606.13757) **[peer-reviewed]** |
| Passing every deterministic oracle is not correctness | 37.7%–45.6% of auto-validated patches failed manual review | [arXiv:2602.07666](https://arxiv.org/abs/2602.07666), USENIX Sec 2026 **[peer-reviewed]** |
| PoC-only validation inflates results | **1.83×** average inflation; 25% of agent patches resemble the historical developer patch | [arXiv:2609.04075](https://arxiv.org/abs/2609.04075) **[peer-reviewed]** |
| Tests are not a correctness oracle | 25% of test-passing SWE-bench Verified patches admit formal counterexamples | [arXiv:2609.21190](https://arxiv.org/abs/2609.21190) **[peer-reviewed]** |
| Generated fixes preserve function, not security | Functionality preservation 0.832, security capability 0.251; 24.8% fully correct | [arXiv:2603.10072](https://arxiv.org/abs/2603.10072) **[peer-reviewed]** |
| Build + crash-repro is insufficient | ~60% of patches pass build+repro, **5–11%** survive fuzzing and differential testing | [Meta AutoPatchBench](https://engineering.fb.com/2025/04/29/ai-research/autopatchbench-benchmark-ai-powered-security-fixes/) **[vendor]** |
| An external oracle changes the regime | GPT-4 on buffer overflow: 0.05 → **1.00** with debugger, sandbox and a controller outside the LLM | [Project Naptime](https://projectzero.google/2024/06/project-naptime.html) |
| Coupling beats scaling compute | LLM+fuzzer 41/54 bugs vs fuzzer alone 8/54 at 7.2 CPU-years; $392 vs $3,264 | [Team Atlanta](https://team-atlanta.github.io/blog/post-sinkfuzz-glm/) |

## Architecture

| Claim | Figure | Source |
|---|---|---|
| Role decomposition without a capability gap is negative | Same model in both roles: **42% vs 44%** for the single agent. Review-only loop +2 pp; structured exploration and planning **+11 pp** | [arXiv:2603.26458](https://arxiv.org/abs/2603.26458) **[peer-reviewed]** |
| Multi-agent wins come from context partitioning | Gains traced to git worktrees, event message passing, dedicated explorer subagents — not personas | [arXiv:2603.21489](https://arxiv.org/abs/2603.21489), [arXiv:2606.25514](https://arxiv.org/abs/2606.25514) **[peer-reviewed]** |
| Best security-repair multi-agent result defines agents by context type | 73% on SEC-Bench (+29%) with dataflow / runtime / commit-history collectors | [arXiv:2607.29422](https://arxiv.org/abs/2607.29422) **[peer-reviewed]** |
| Thin scaffold beats elaborate scaffold | 77.4% SWE-bench Verified from a bash-only scaffold, by the Agentless authors | [arXiv:2511.13646](https://arxiv.org/abs/2511.13646) **[peer-reviewed]** |
| Sampling plus an executable verifier is the mechanism | Coverage 15.9% → 56% at 250 samples; selection, not generation, is the bottleneck | [arXiv:2407.21787](https://arxiv.org/abs/2407.21787) **[peer-reviewed]** |

## Context

| Claim | Figure | Source |
|---|---|---|
| Less context repairs better | Dataflow slice reduces input **19–57×**; Pass@1 19.3% → **82.31%** | [arXiv:2402.13291](https://arxiv.org/abs/2402.13291) **[peer-reviewed]** |
| Confirmed independently | 3× success rate at 1/6 the compute | [GitHub](https://github.blog/engineering/platform-security/fixing-security-vulnerabilities-with-ai/) **[vendor]** |
| Difficulty splits by CWE locality | **81%** Pass@1 on syntactically local CWEs, **42%** on interprocedural dataflow | [arXiv:2402.13291](https://arxiv.org/abs/2402.13291) **[peer-reviewed]** |
| Specification refinement beats architecture change | Pass@1 41% → **71%** (Agentless), 47% → 72% (AutoCodeRover), by rewriting the input only | [arXiv:2607.07882](https://arxiv.org/abs/2607.07882) **[peer-reviewed]** |
| Repository context prunes candidates cheaply | −71% to −76% candidates, zero high-severity lost (n=2 repos) | [ZeroPath](https://zeropath.com/blog/reduce-false-positives-with-repo-context) **[vendor]** |
| Runtime state beats stack traces as repair context | +26.2% over SOTA; stack traces are what induce surface fixes | [arXiv:2604.19305](https://arxiv.org/abs/2604.19305) **[peer-reviewed]** |

## Noise and delivery

| Claim | Figure | Source |
|---|---|---|
| Independent precision is far below vendor claims | **16.65%** precision on 1,000 PRs of which 500 are clean | [arXiv:2509.01494](https://arxiv.org/abs/2509.01494) **[peer-reviewed]** |
| Benchmarks without negatives cannot punish false positives | Same five repos: 82% self-scored, 45% re-scored by a third party | [DeepSource](https://deepsource.com/blog/ai-code-review-benchmarks) |
| Most credible vendor number is self-deprecating | 35.7–39.3% precision after verification, dedup and filtering | [CodeRabbit](https://www.coderabbit.ai/blog/opus-5-5-model-review) **[vendor]** |
| Feedback clustering works where LLM judging failed | Address rate 19% → 55%+ in two weeks | [Greptile](https://www.greptile.com/blog/make-llms-shut-up) |
| Production filtering stack | Thresholds per (assistant × language × category), separate grader model: 75% useful, 65% addressed vs 51% human baseline, 65k diffs/week | [Uber uReview](https://www.uber.com/blog/ureview/) **[vendor]** |
| Precision is a target, not an outcome | Tuned to an explicit 50% precision goal; traded quantity for quality | [Google](https://research.google/blog/resolving-code-review-comments-with-ml/) |
| Applicable suggestion blocks drive resolution | OR **1.617** (75.5% vs 64.6%), n=54,713 comments; length hurts (807 vs 617 chars) | [arXiv:2607.21997](https://arxiv.org/abs/2607.21997) **[peer-reviewed]** |
| Adding a reviewer can cost time without saving any | PR close time 5h52m → 8h20m (p ≪ 0.001); human comments unchanged | [arXiv:2412.18531](https://arxiv.org/abs/2412.18531) **[peer-reviewed]** |
| Terse confident output maximises automation bias | Agreement 89.22% with feedback only vs 77.45% with full explanation | [arXiv:2607.24601](https://arxiv.org/abs/2607.24601) **[peer-reviewed]** |

## Prioritisation

| Claim | Figure | Source |
|---|---|---|
| EPSS vs CVSS at equal coverage | 82% coverage for **7.3%** of CVEs (EPSS v3 ≥0.088) vs **58.1%** (CVSS ≥7) | [WEIS 2023](https://arxiv.org/abs/2302.14172) **[peer-reviewed]** |
| CVSS base does not order exploitation | AUC **0.051** | same |
| CVSS v4 did not fix the distribution | 56.0% of v4-scored CVEs are ≥7.0 vs 53.0% for v3.1 (n=1,944) | **[measured]** via NVD API |
| KEV must be a union term, not a substitute | 25.0% of KEV CVEs score below EPSS 0.088; adding all of KEV costs +2.3% volume | **[measured]** against FIRST EPSS v5 + CISA KEV feeds |
| Reachability is a ranking input, not a filter | Surviving share ranges 1%–70% across studies depending on unit of analysis; 11 of 41 executed cases were invisible to static analysis | [arXiv:2108.12078](https://arxiv.org/abs/2108.12078), [arXiv:2301.07972](https://arxiv.org/abs/2301.07972) **[peer-reviewed]** |
| Python reachability is the hard case | PyCG on real whole-program apps: precision ~0.19, recall ~0.48 | [arXiv:2305.05949](https://arxiv.org/abs/2305.05949) **[peer-reviewed]** |
| Advisory data is unreliable | 8.2% of GHSA advisories are human-reviewed; NVD abandoned universal enrichment 2026-04-15 | [arXiv:2602.06009](https://arxiv.org/html/2602.06009), [NIST](https://www.nist.gov/news-events/news/2026/04/nist-updates-nvd-operations-address-record-cve-growth) |

## Measured on Sentoru

272 packages, 17 Python files in `app/`, warm cache.

| Tool | Latency | Result |
|---|---:|---|
| `zizmor .github/workflows/` | 0.26 s | **54 findings**: 19 `unpinned-uses`, 1 `excessive-permissions`, 6 `artipacked`, 3 `secrets-inherit`, 3 `self-repository` |
| `ruff check --select S` | 0.42 s | 0 in `app/`; 27 `S101` in `tests/`, all false positives |
| `bandit -r app/` | 1.72 s | 0 — identical result to Ruff, 4× slower |
| `uv audit --no-dev` | 1.2 s | 420 raw → 216 after alias dedup → 28 packages |
| `pip-audit -s osv` | 60 s | identical 420 findings — 50× slower for the same answer |
| `semgrep --config=p/python` | 1.4 s | 0 in `app/` (187 rules) |

**48% of raw `uv audit` output is duplication**: 244 of 267 CVE groups carry exactly two
records, one GHSA and one PYSEC for the same vulnerability. Three packages hold 55% of the
volume (`nltk` 82, `pypdf` 81, `aiohttp` 66); the first two enter through `llama-index`.

`.github/workflows/_dependency_scanning.yml` declares `on: workflow_call` and has no
callers. The Safety CLI is not running in CI.
