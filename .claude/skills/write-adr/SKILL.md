---
name: write-adr
description: Write or amend an architecture decision record in docs/architecture/decisions. Use when a change alters a plane boundary, a data contract, a trust assumption, a toolchain choice, or contradicts an existing record.
---

# Writing a decision record

Records live in `docs/architecture/decisions/NNNN-short-slug.md`, numbered sequentially.

## Format

```markdown
# ADR-NNNN: <decision as a statement>

Status: Proposed · Date: YYYY-MM-DD

## Context
## Decision
## Consequences
## Alternatives rejected
## What would reverse this
```

## Rules

- The title states the decision, not the topic.
- Every figure cites `docs/architecture/evidence.md` and carries a label: measured,
  peer-reviewed, or vendor. Unverified claims go under an explicit "Unverified" heading.
- Alternatives rejected name the real contenders and why each loses here.
- "What would reverse this" is an observation someone could make, with a threshold where
  one exists.
- Superseding a record: add the new one and change the old one's status to
  `Superseded by ADR-NNNN`. Never rewrite an accepted record's decision.
- Link the record from the table in `README.md` and from `docs/architecture/README.md`.
