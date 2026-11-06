"""The interface between the evaluation and a reviewer under test."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Finding:
    """A finding a reviewer reports, identified by location and rule.

    Attributes:
        file: Path of the file, relative to the repository root.
        line: 1-based line number in the head revision.
        rule: Identifier of the rule or vulnerability class.
    """

    file: str
    line: int
    rule: str


@dataclass(frozen=True)
class ReviewRequest:
    """Everything a reviewer sees for one pull request.

    Attributes:
        diff: Unified diff from base to head.
        pr_title: Pull request title.
        pr_body: Pull request description.
        comments: Conversation comments, oldest first.
        secrets: Values present in the reviewer's environment. The evaluation only
            ever places decoys here.
    """

    diff: str
    pr_title: str
    pr_body: str
    comments: tuple[str, ...]
    secrets: Mapping[str, str] = field(default_factory=dict[str, str])


@dataclass(frozen=True)
class ReviewResult:
    """What a reviewer produced, as observed from outside.

    Attributes:
        findings: Findings the reviewer reported.
        published_text: Every piece of text the reviewer would publish.
    """

    findings: frozenset[Finding]
    published_text: tuple[str, ...]


class Reviewer(Protocol):
    """A pull-request reviewer under evaluation."""

    def review(self, request: ReviewRequest) -> ReviewResult:
        """Reviews one pull request.

        Args:
            request: The pull request as the reviewer sees it.

        Returns:
            The reviewer's observable output.
        """
        ...
