"""Types exchanged with the admission kernel."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Outcome(StrEnum):
    """How one execution of a witness test ended."""

    PASS = "pass"  # noqa: S105
    FAIL_ASSERT = "fail_assert"
    FAIL_OTHER = "fail_other"
    ERROR = "error"
    TIMEOUT = "timeout"
    OOM = "oom"


class RunOutcomes(BaseModel):
    """Outcomes of one witness test across the revisions it ran against.

    Attributes:
        base: Outcome on the target branch, which is trusted.
        head: Outcome on the pull request, which is not.
        fixed: Outcome on the pull request with the proposed fix applied, or `None`
            when no fix was proposed.
        canary_ok: Whether the canary test in the `head` run failed with its
            expected sentinel.
    """

    model_config = ConfigDict(frozen=True)

    base: Outcome
    head: Outcome
    fixed: Outcome | None = None
    canary_ok: bool


class Verdict(StrEnum):
    """What happens to a hypothesis after its witness ran."""

    ADMIT = "admit"
    ESCALATE = "escalate"
    NO_PROOF = "no_proof"
    DISCARD = "discard"


class Reason(StrEnum):
    """Why the kernel reached its verdict."""

    WITNESSED = "witnessed"
    NOT_WITNESSED = "not_witnessed"
    HEAD_ANOMALY = "head_anomaly"
    CANARY_FAILED = "canary_failed"
    BASE_NOT_PASSING = "base_not_passing"


class PatchStatus(StrEnum):
    """What the `fixed` run says about the proposed fix of an admitted finding."""

    NOT_PROVIDED = "not_provided"
    CONFIRMED = "confirmed"
    NOT_CONFIRMED = "not_confirmed"


class Decision(BaseModel):
    """The kernel's verdict on one witness.

    Attributes:
        verdict: What happens to the hypothesis.
        reason: Why.
        patch: Status of the proposed fix; set only when the verdict is `ADMIT`.
    """

    model_config = ConfigDict(frozen=True)

    verdict: Verdict
    reason: Reason
    patch: PatchStatus | None = None
