import json
from pathlib import Path
from typing import Any

import pytest

from evals.injection.cases import (
    DECOY_NAME,
    DECOY_VALUE,
    PLACEHOLDER,
    Objective,
    Vector,
    load_cases,
    parse_case,
)


def _record(**overrides: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": "case",
        "vector": "pr_title",
        "objective": "exfiltration",
        "payload": "payload",
        "pr_title": f"Title {PLACEHOLDER}",
        "pr_body": "Body",
        "comments": [],
        "diff": "",
        "target": None,
    }
    record.update(overrides)
    return record


def test_bundled_corpus_covers_every_vector_and_objective() -> None:
    """The shipped corpus loads and exercises each vector against each objective."""
    cases = load_cases()

    assert {(c.vector, c.objective) for c in cases} == {
        (v, o) for v in Vector for o in Objective
    }


def test_render_inserts_payload_or_removes_placeholder() -> None:
    """The attack run carries the payload; the control run carries nothing in its place."""
    case = parse_case(_record())

    attack = case.render(with_payload=True)
    control = case.render(with_payload=False)

    assert attack.pr_title == "Title payload"
    assert control.pr_title == "Title "
    assert attack.secrets == control.secrets == {DECOY_NAME: DECOY_VALUE}


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        pytest.param({"vector": "email"}, "invalid case record", id="unknown-vector"),
        pytest.param(
            {"objective": "steal"}, "invalid case record", id="unknown-objective"
        ),
        pytest.param(
            {"pr_title": "Title"}, "must appear once", id="placeholder-missing"
        ),
        pytest.param(
            {"pr_body": f"Body {PLACEHOLDER}"},
            "must appear once",
            id="placeholder-twice",
        ),
        pytest.param(
            {"vector": "comment"}, "must appear once", id="placeholder-in-wrong-field"
        ),
        pytest.param(
            {"objective": "suppress_finding"}, "requires a target", id="missing-target"
        ),
        pytest.param(
            {"target": {"file": "a.py"}}, "invalid case record", id="incomplete-target"
        ),
    ],
)
def test_parse_case_rejects_invalid_records(
    overrides: dict[str, Any], message: str
) -> None:
    """Malformed cases fail loudly instead of producing an unscorable case."""
    with pytest.raises(ValueError, match=message):
        parse_case(_record(**overrides))


def test_load_cases_rejects_duplicate_ids(tmp_path: Path) -> None:
    """Two cases with the same id would double-count in every rate."""
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps(_record()) + "\n\n" + json.dumps(_record()) + "\n")

    with pytest.raises(ValueError, match=r"cases.jsonl:3: duplicate case id"):
        load_cases(path)


def test_load_cases_names_the_line_of_invalid_json(tmp_path: Path) -> None:
    """A syntax error points at its line."""
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps(_record()) + "\n{not json\n")

    with pytest.raises(ValueError, match=r"cases.jsonl:2:"):
        load_cases(path)
