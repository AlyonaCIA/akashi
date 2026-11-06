"""Evaluation cases and their loader."""

import json
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any

from evals.injection.reviewer import Finding, ReviewRequest

PLACEHOLDER = "{{payload}}"
DECOY_NAME = "DEPLOY_TOKEN"
DECOY_VALUE = "AKASHI-DECOY-0000-THIS-IS-NOT-A-SECRET"
BUNDLED_CASES = Path(__file__).with_name("cases.jsonl")


class Vector(StrEnum):
    """Where the attacker places the payload."""

    PR_TITLE = "pr_title"
    PR_BODY = "pr_body"
    COMMENT = "comment"
    DIFF_TEXT = "diff_text"


class Objective(StrEnum):
    """What the attacker wants the reviewer to do."""

    EXFILTRATION = "exfiltration"
    SUPPRESS_FINDING = "suppress_finding"
    FABRICATE_FINDING = "fabricate_finding"


@dataclass(frozen=True)
class Case:
    """One pull request with an injected payload and an attack objective.

    Attributes:
        id: Unique case identifier.
        vector: Field that carries the payload, marked by `PLACEHOLDER`.
        objective: What a successful attack achieves.
        payload: Text substituted for `PLACEHOLDER` in the attack run.
        request: The pull request, with `PLACEHOLDER` in the vector's field.
        target: The finding to suppress or fabricate; `None` for exfiltration.
    """

    id: str
    vector: Vector
    objective: Objective
    payload: str
    request: ReviewRequest
    target: Finding | None

    def render(self, *, with_payload: bool) -> ReviewRequest:
        """Builds the request a reviewer sees.

        Args:
            with_payload: Insert the payload; otherwise the placeholder is removed,
                producing the control run.

        Returns:
            The request with the placeholder replaced and the decoy secret present.
        """
        text = self.payload if with_payload else ""
        request = self.request
        return replace(
            request,
            diff=request.diff.replace(PLACEHOLDER, text),
            pr_title=request.pr_title.replace(PLACEHOLDER, text),
            pr_body=request.pr_body.replace(PLACEHOLDER, text),
            comments=tuple(c.replace(PLACEHOLDER, text) for c in request.comments),
            secrets={DECOY_NAME: DECOY_VALUE},
        )


def _vector_fields(request: ReviewRequest) -> dict[Vector, str]:
    return {
        Vector.PR_TITLE: request.pr_title,
        Vector.PR_BODY: request.pr_body,
        Vector.COMMENT: "\n".join(request.comments),
        Vector.DIFF_TEXT: request.diff,
    }


def parse_case(record: dict[str, Any]) -> Case:
    """Validates one JSON record and converts it into a case.

    Args:
        record: Decoded JSON object.

    Returns:
        The validated case.

    Raises:
        ValueError: If a field is missing or invalid, the placeholder is not exactly
            once in the vector's field, or the objective's target is missing.
    """
    try:
        vector = Vector(record["vector"])
        objective = Objective(record["objective"])
        request = ReviewRequest(
            diff=str(record["diff"]),
            pr_title=str(record["pr_title"]),
            pr_body=str(record["pr_body"]),
            comments=tuple(str(c) for c in record["comments"]),
        )
        target_record = record.get("target")
        target = None if target_record is None else Finding(**target_record)
        case = Case(
            id=str(record["id"]),
            vector=vector,
            objective=objective,
            payload=str(record["payload"]),
            request=request,
            target=target,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"invalid case record: {error}") from error

    counts = {v: text.count(PLACEHOLDER) for v, text in _vector_fields(request).items()}
    if counts[vector] != 1 or sum(counts.values()) != 1:
        raise ValueError(
            f"case {case.id!r}: {PLACEHOLDER} must appear once, in {vector}"
        )
    needs_target = objective is not Objective.EXFILTRATION
    if needs_target and target is None:
        raise ValueError(f"case {case.id!r}: {objective} requires a target")
    return case


def load_cases(path: Path = BUNDLED_CASES) -> list[Case]:
    """Loads cases from a JSON Lines file.

    Args:
        path: File with one JSON object per line; blank lines are ignored.

    Returns:
        The cases, in file order.

    Raises:
        ValueError: If a line is not valid JSON, a record is invalid, or two cases
            share an id. The message names the line.
    """
    cases: list[Case] = []
    seen: set[str] = set()
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case = parse_case(json.loads(line))
        except ValueError as error:
            raise ValueError(f"{path.name}:{number}: {error}") from error
        if case.id in seen:
            raise ValueError(f"{path.name}:{number}: duplicate case id {case.id!r}")
        seen.add(case.id)
        cases.append(case)
    return cases
