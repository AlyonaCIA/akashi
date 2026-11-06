import itertools

import pytest
from pydantic import ValidationError

from akashi.kernel.decide import cap_escalations, decide
from akashi.kernel.models import (
    Decision,
    Outcome,
    PatchStatus,
    Reason,
    RunOutcomes,
    Verdict,
)

FIXED_OPTIONS: list[Outcome | None] = [None, *Outcome]
ALL_INPUTS = [
    RunOutcomes(base=base, head=head, fixed=fixed, canary_ok=canary_ok)
    for base, head, fixed, canary_ok in itertools.product(
        Outcome, Outcome, FIXED_OPTIONS, [True, False]
    )
]
HEAD_ANOMALIES = [Outcome.FAIL_OTHER, Outcome.ERROR, Outcome.TIMEOUT, Outcome.OOM]


def _id(outcomes: RunOutcomes) -> str:
    return f"{outcomes.base}-{outcomes.head}-{outcomes.fixed}-{outcomes.canary_ok}"


def test_input_space_is_complete() -> None:
    """The exhaustive tests cover every combination of outcomes."""
    assert len(ALL_INPUTS) == 6 * 6 * 7 * 2


@pytest.mark.parametrize("outcomes", ALL_INPUTS, ids=_id)
def test_decide_satisfies_the_specification(outcomes: RunOutcomes) -> None:
    """Every input maps to exactly the verdict and reason the rules prescribe."""
    decision = decide(outcomes)

    if not outcomes.canary_ok:
        expected = (Verdict.ESCALATE, Reason.CANARY_FAILED)
    elif outcomes.base is not Outcome.PASS:
        expected = (Verdict.DISCARD, Reason.BASE_NOT_PASSING)
    elif outcomes.head is Outcome.FAIL_ASSERT:
        expected = (Verdict.ADMIT, Reason.WITNESSED)
    elif outcomes.head is Outcome.PASS:
        expected = (Verdict.NO_PROOF, Reason.NOT_WITNESSED)
    else:
        expected = (Verdict.ESCALATE, Reason.HEAD_ANOMALY)
    assert (decision.verdict, decision.reason) == expected


@pytest.mark.parametrize("outcomes", ALL_INPUTS, ids=_id)
def test_admit_requires_a_clean_witness(outcomes: RunOutcomes) -> None:
    """Admission needs base passing, head failing by assertion, and a correct canary."""
    if decide(outcomes).verdict is Verdict.ADMIT:
        assert outcomes.base is Outcome.PASS
        assert outcomes.head is Outcome.FAIL_ASSERT
        assert outcomes.canary_ok


@pytest.mark.parametrize("outcomes", ALL_INPUTS, ids=_id)
def test_patch_status_is_reported_only_for_admitted_findings(
    outcomes: RunOutcomes,
) -> None:
    """The fix status annotates admissions and nothing else."""
    decision = decide(outcomes)

    assert (decision.patch is not None) == (decision.verdict is Verdict.ADMIT)


@pytest.mark.parametrize("outcomes", ALL_INPUTS, ids=_id)
def test_fixed_run_never_changes_the_verdict(outcomes: RunOutcomes) -> None:
    """The proposed fix annotates a verdict; it cannot create or remove one."""
    without_fix = outcomes.model_copy(update={"fixed": None})

    assert decide(outcomes).verdict is decide(without_fix).verdict


@pytest.mark.parametrize(
    ("fixed", "patch"),
    [
        (None, PatchStatus.NOT_PROVIDED),
        (Outcome.PASS, PatchStatus.CONFIRMED),
        *[(o, PatchStatus.NOT_CONFIRMED) for o in Outcome if o is not Outcome.PASS],
    ],
)
def test_admitted_patch_status_follows_the_fixed_run(
    fixed: Outcome | None, patch: PatchStatus
) -> None:
    """Only a passing fixed run confirms the fix."""
    outcomes = RunOutcomes(
        base=Outcome.PASS, head=Outcome.FAIL_ASSERT, fixed=fixed, canary_ok=True
    )

    assert decide(outcomes).patch is patch


@pytest.mark.parametrize("head", HEAD_ANOMALIES)
def test_sabotage_shaped_head_outcomes_escalate(head: Outcome) -> None:
    """A head run that errors, hangs or runs out of memory goes to a human."""
    outcomes = RunOutcomes(base=Outcome.PASS, head=head, canary_ok=True)

    assert decide(outcomes).verdict is Verdict.ESCALATE


def test_wrong_canary_escalates_even_when_base_fails() -> None:
    """Evidence of tampering is never discarded together with a broken test."""
    outcomes = RunOutcomes(
        base=Outcome.ERROR, head=Outcome.FAIL_ASSERT, canary_ok=False
    )

    assert decide(outcomes).reason is Reason.CANARY_FAILED


@pytest.mark.parametrize(
    "record",
    [
        {"base": "pass", "head": "crashed", "canary_ok": True},
        {"base": "pass", "head": "pass"},
        {"base": "pass", "head": "pass", "canary_ok": True, "extra": 1, "fixed": "bad"},
    ],
)
def test_run_outcomes_reject_invalid_input(record: dict[str, object]) -> None:
    """Unknown outcomes and missing fields fail validation instead of defaulting."""
    with pytest.raises(ValidationError):
        RunOutcomes.model_validate(record)


ESCALATION = Decision(verdict=Verdict.ESCALATE, reason=Reason.HEAD_ANOMALY)
CANARY = Decision(verdict=Verdict.ESCALATE, reason=Reason.CANARY_FAILED)
ADMISSION = Decision(
    verdict=Verdict.ADMIT, reason=Reason.WITNESSED, patch=PatchStatus.CONFIRMED
)


@pytest.mark.parametrize(
    ("decisions", "limit", "published", "withheld"),
    [
        pytest.param([], 1, (), 0, id="none"),
        pytest.param([ADMISSION], 1, (), 0, id="no-escalations"),
        pytest.param([ESCALATION], 1, (ESCALATION,), 0, id="one"),
        pytest.param([CANARY, ADMISSION, ESCALATION], 1, (CANARY,), 1, id="first-wins"),
        pytest.param(
            [ESCALATION, CANARY, ESCALATION], 2, (ESCALATION, CANARY), 1, id="limit-2"
        ),
    ],
)
def test_cap_escalations(
    decisions: list[Decision],
    limit: int,
    published: tuple[Decision, ...],
    withheld: int,
) -> None:
    """At most `limit` escalations are published; the rest are counted, not lost."""
    batch = cap_escalations(decisions, limit)

    assert (batch.published, batch.withheld) == (published, withheld)


@pytest.mark.parametrize("limit", [0, -1])
def test_cap_escalations_refuses_to_hide_every_anomaly(limit: int) -> None:
    """A limit below one would silence all escalations."""
    with pytest.raises(ValueError, match="at least 1"):
        cap_escalations([ESCALATION], limit)
