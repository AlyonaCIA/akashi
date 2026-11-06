"""Verdict rules for witness outcomes and the per-pull-request escalation cap."""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from akashi.kernel.models import (
    Decision,
    Outcome,
    PatchStatus,
    Reason,
    RunOutcomes,
    Verdict,
)

DEFAULT_ESCALATION_LIMIT = 1


def decide(outcomes: RunOutcomes) -> Decision:
    """Decides what to do with a hypothesis given its witness outcomes.

    Rules, first match wins:

    1. The canary did not fail as expected: `ESCALATE`. The `head` run may be
       sabotaged, so nothing it reports is trusted, whatever `base` did.
    2. `base` did not pass: `DISCARD`. The test does not hold on trusted code, so it
       says nothing about the pull request.
    3. `head` failed by assertion: `ADMIT`, with the fix status from `fixed`.
    4. `head` passed: `NO_PROOF`.
    5. `head` failed any other way: `ESCALATE`. Code under test can make its own run
       error, hang or exhaust memory to suppress a finding.

    No verdict means the code is safe. `NO_PROOF` and `DISCARD` mean this witness
    showed nothing; they are never evidence of the absence of a vulnerability.

    Args:
        outcomes: Outcomes of the witness on each revision.

    Returns:
        The decision. Defined for every input; never raises.
    """
    if not outcomes.canary_ok:
        return Decision(verdict=Verdict.ESCALATE, reason=Reason.CANARY_FAILED)
    if outcomes.base is not Outcome.PASS:
        return Decision(verdict=Verdict.DISCARD, reason=Reason.BASE_NOT_PASSING)
    if outcomes.head is Outcome.FAIL_ASSERT:
        return Decision(
            verdict=Verdict.ADMIT,
            reason=Reason.WITNESSED,
            patch=_patch_status(outcomes.fixed),
        )
    if outcomes.head is Outcome.PASS:
        return Decision(verdict=Verdict.NO_PROOF, reason=Reason.NOT_WITNESSED)
    return Decision(verdict=Verdict.ESCALATE, reason=Reason.HEAD_ANOMALY)


def _patch_status(fixed: Outcome | None) -> PatchStatus:
    if fixed is None:
        return PatchStatus.NOT_PROVIDED
    if fixed is Outcome.PASS:
        return PatchStatus.CONFIRMED
    return PatchStatus.NOT_CONFIRMED


class EscalationBatch(BaseModel):
    """Escalations to publish for one pull request, and how many were held back.

    Attributes:
        published: Escalations to raise with a human, in input order.
        withheld: Escalations over the limit. Reported as a count, never dropped
            silently.
    """

    model_config = ConfigDict(frozen=True)

    published: tuple[Decision, ...]
    withheld: int


def cap_escalations(
    decisions: Sequence[Decision], limit: int = DEFAULT_ESCALATION_LIMIT
) -> EscalationBatch:
    """Limits the escalations raised for one pull request.

    Args:
        decisions: Every decision taken for the pull request.
        limit: Maximum escalations to publish; at least one.

    Returns:
        The first `limit` escalations and the count of the rest.

    Raises:
        ValueError: If `limit` is less than one, which would hide every anomaly.
    """
    if limit < 1:
        raise ValueError(f"limit must be at least 1, got {limit}")
    escalations = [d for d in decisions if d.verdict is Verdict.ESCALATE]
    return EscalationBatch(
        published=tuple(escalations[:limit]),
        withheld=max(0, len(escalations) - limit),
    )
