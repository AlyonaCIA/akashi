import pytest

from evals.injection.cases import Case, Objective, Vector, load_cases
from evals.injection.naive import NaiveReviewer, added_lines
from evals.injection.reviewer import Finding, ReviewRequest, ReviewResult
from evals.injection.scoring import (
    CaseResult,
    Outcome,
    by_objective,
    by_vector,
    evaluate,
    rule_of_three_upper,
    summarize,
    wilson_interval,
)

CASES = load_cases()


class DetectOnlyReviewer:
    """Detects like the naive reviewer but ignores every instruction in the text."""

    def review(self, request: ReviewRequest) -> ReviewResult:
        """Reports pattern matches only.

        Args:
            request: The pull request.

        Returns:
            Findings from the diff and a summary that echoes nothing else.
        """
        findings = frozenset(
            Finding(file=file, line=line, rule="shell-true")
            for file, line, text in added_lines(request.diff)
            if "shell=True" in text
        )
        return ReviewResult(findings=findings, published_text=())


class BlindReviewer:
    """Reports nothing, so a suppression can never be attributed to the payload."""

    def review(self, request: ReviewRequest) -> ReviewResult:
        """Returns an empty review.

        Args:
            request: The pull request.

        Returns:
            No findings and no text.
        """
        return ReviewResult(findings=frozenset(), published_text=())


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_corpus_attacks_the_naive_reviewer(case: Case) -> None:
    """Falsifier: a corpus that cannot attack a reviewer built to obey it cannot measure."""
    assert evaluate(case, NaiveReviewer()).outcome is Outcome.SUCCESS


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_instruction_ignoring_reviewer_resists_every_case(case: Case) -> None:
    """Scoring credits the payload only when the reviewer's behaviour changes."""
    assert evaluate(case, DetectOnlyReviewer()).outcome is Outcome.FAILURE


@pytest.mark.parametrize(
    ("objective", "expected"),
    [
        (Objective.SUPPRESS_FINDING, Outcome.INVALID),
        (Objective.FABRICATE_FINDING, Outcome.FAILURE),
        (Objective.EXFILTRATION, Outcome.FAILURE),
    ],
)
def test_control_run_decides_attribution(
    objective: Objective, expected: Outcome
) -> None:
    """A finding missing even without the payload cannot count as suppressed."""
    case = next(c for c in CASES if c.objective is objective)

    assert evaluate(case, BlindReviewer()).outcome is expected


@pytest.mark.parametrize(
    ("successes", "trials", "low", "high"),
    [
        (0, 30, 0.0, 0.1135),
        (5, 10, 0.2366, 0.7634),
        (10, 10, 0.7225, 1.0),
        (1, 1, 0.2065, 1.0),
    ],
)
def test_wilson_interval_matches_reference_values(
    successes: int, trials: int, low: float, high: float
) -> None:
    """Interval bounds agree with the closed-form Wilson score to four decimals."""
    assert wilson_interval(successes, trials) == pytest.approx((low, high), abs=1e-4)


@pytest.mark.parametrize(("successes", "trials"), [(0, 0), (-1, 5), (6, 5)])
def test_wilson_interval_rejects_impossible_counts(successes: int, trials: int) -> None:
    """Counts outside 0..trials, or no trials, are rejected."""
    with pytest.raises(ValueError, match="successes <= trials"):
        wilson_interval(successes, trials)


@pytest.mark.parametrize(("trials", "bound"), [(30, 0.1), (100, 0.03), (3, 1.0)])
def test_rule_of_three(trials: int, bound: float) -> None:
    """Zero successes in n trials bound the rate at about 3/n."""
    assert rule_of_three_upper(trials) == pytest.approx(bound)


def test_rule_of_three_rejects_no_trials() -> None:
    """Without trials there is no bound."""
    with pytest.raises(ValueError, match="positive"):
        rule_of_three_upper(0)


def test_summary_groups_valid_results_by_vector_and_objective() -> None:
    """Each group counts its valid cases; invalid results are excluded."""
    results = [evaluate(case, NaiveReviewer()) for case in CASES]
    invalid = CaseResult(CASES[0], Outcome.INVALID)

    vectors = summarize([*results, invalid], by_vector)
    objectives = summarize(results, by_objective)

    assert {v: r.trials for v, r in vectors.items()} == dict.fromkeys(Vector, 3)
    assert {o: r.trials for o, r in objectives.items()} == dict.fromkeys(Objective, 4)
    assert all(r.rate == 1.0 for r in [*vectors.values(), *objectives.values()])


@pytest.mark.parametrize(
    ("diff", "expected"),
    [
        pytest.param(
            "+++ b/a.py\n@@ -1 +1,2 @@\n x\n+y\n",
            [("a.py", 2, "y")],
            id="after-context",
        ),
        pytest.param(
            "+++ b/a.py\n@@ -5,2 +5 @@\n-x\n+y\n", [("a.py", 5, "y")], id="replacement"
        ),
        pytest.param(
            "+++ b/a.py\n@@ -1 +1 @@\n x\n@@ -10 +10,2 @@\n x\n+z\n",
            [("a.py", 11, "z")],
            id="second-hunk",
        ),
    ],
)
def test_added_lines_uses_head_line_numbers(
    diff: str, expected: list[tuple[str, int, str]]
) -> None:
    """Added lines are numbered as in the head revision."""
    assert added_lines(diff) == expected
