"""Repository policy for GitHub Actions workflows, complementing zizmor.

zizmor (run in CI) already rejects `pull_request_target`, actions not pinned to a commit
and excessive permissions; `test_zizmor_rejects_a_bad_workflow` proves it does. The rules
below are the ones zizmor does not enforce:

- the workflow sets `permissions: {}` at the top level;
- every job sets `timeout-minutes`;
- no job in a workflow triggered by attacker-influenced content references `secrets.*`.

Blind spots: reusable workflows called with `uses:` at job level are checked only as
files in this repository, not as called; a reusable workflow inherits the caller's
permissions and secrets, which this test does not trace. Composite actions, expressions
built at runtime, and settings outside the YAML (repository or organisation defaults)
are not inspected.
"""

import json
import re
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

WORKFLOWS_DIR = Path(__file__).parents[2] / ".github" / "workflows"
UNTRUSTED_TRIGGERS = frozenset(
    {
        "pull_request",
        "pull_request_target",
        "pull_request_review",
        "pull_request_review_comment",
        "issue_comment",
        "issues",
        "discussion",
        "discussion_comment",
        "workflow_run",
    }
)
SECRETS_REFERENCE = re.compile(r"\bsecrets\.")


def _load(text: str) -> dict[str, Any]:
    document: dict[Any, Any] = yaml.safe_load(text)
    if True in document and "on" not in document:
        document["on"] = document.pop(True)
    return document


def _triggers(workflow: dict[str, Any]) -> set[str]:
    on: object = workflow.get("on")
    if isinstance(on, str):
        return {on}
    if isinstance(on, list | dict):
        events = cast("Iterable[object]", on)
        return {str(event) for event in events}
    return set()


def top_level_permission_violations(workflow: dict[str, Any]) -> list[str]:
    """Returns a violation unless the workflow sets `permissions: {}` at the top level.

    Args:
        workflow: Parsed workflow document.

    Returns:
        Zero or one violation message.
    """
    if workflow.get("permissions") != {}:
        return ["top-level permissions must be {}"]
    return []


def job_violations(workflow: dict[str, Any], job_id: str) -> list[str]:
    """Checks one job against the timeout and secrets rules.

    Args:
        workflow: Parsed workflow document.
        job_id: Key of the job under `jobs`.

    Returns:
        One message per violated rule.
    """
    job: dict[str, Any] = workflow["jobs"][job_id]
    violations: list[str] = []
    if "uses" not in job and "timeout-minutes" not in job:
        violations.append(f"job {job_id!r} has no timeout-minutes")
    if _triggers(workflow) & UNTRUSTED_TRIGGERS and SECRETS_REFERENCE.search(
        json.dumps(job)
    ):
        violations.append(
            f"job {job_id!r} references secrets in a workflow triggered by untrusted content"
        )
    return violations


WORKFLOWS = sorted(WORKFLOWS_DIR.glob("*.yml"))
JOBS = [
    (path, job_id)
    for path in WORKFLOWS
    for job_id in _load(path.read_text()).get("jobs", {})
]


def test_workflows_are_found() -> None:
    """The policy runs against at least one workflow, so it cannot pass vacuously."""
    assert WORKFLOWS


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda path: path.name)
def test_workflow_denies_permissions_by_default(path: Path) -> None:
    """Every workflow starts from no permissions; jobs grant what they need."""
    assert top_level_permission_violations(_load(path.read_text())) == []


@pytest.mark.parametrize(
    ("path", "job_id"), JOBS, ids=[f"{p.name}:{j}" for p, j in JOBS]
)
def test_job_follows_policy(path: Path, job_id: str) -> None:
    """Every job has a timeout and keeps secrets away from untrusted triggers."""
    assert job_violations(_load(path.read_text()), job_id) == []


@pytest.mark.parametrize(
    ("workflow", "expected"),
    [
        pytest.param(
            "on: push\njobs: {}\n",
            ["top-level permissions must be {}"],
            id="missing-permissions",
        ),
        pytest.param(
            "on: push\npermissions: write-all\njobs: {}\n",
            ["top-level permissions must be {}"],
            id="write-all",
        ),
        pytest.param(
            "on: push\npermissions:\n  contents: read\njobs: {}\n",
            ["top-level permissions must be {}"],
            id="grants-at-top-level",
        ),
        pytest.param("on: push\npermissions: {}\njobs: {}\n", [], id="compliant"),
    ],
)
def test_top_level_permission_rule_detects_mutations(
    workflow: str, expected: list[str]
) -> None:
    """The permission rule rejects every non-empty or missing top-level grant."""
    assert top_level_permission_violations(_load(workflow)) == expected


@pytest.mark.parametrize(
    ("workflow", "expected"),
    [
        pytest.param(
            "on: push\njobs:\n  a:\n    runs-on: x\n",
            ["job 'a' has no timeout-minutes"],
            id="no-timeout",
        ),
        pytest.param(
            "on: push\njobs:\n  a:\n    uses: ./.github/workflows/r.yml\n",
            [],
            id="reusable-call-exempt",
        ),
        pytest.param(
            "on: pull_request\njobs:\n  a:\n    timeout-minutes: 5\n"
            "    env:\n      T: ${{ secrets.TOKEN }}\n",
            ["job 'a' references secrets in a workflow triggered by untrusted content"],
            id="secret-on-pull-request",
        ),
        pytest.param(
            "on: [issue_comment]\njobs:\n  a:\n    timeout-minutes: 5\n"
            "    steps:\n      - run: echo ${{ secrets.TOKEN }}\n",
            ["job 'a' references secrets in a workflow triggered by untrusted content"],
            id="secret-on-issue-comment-list-trigger",
        ),
        pytest.param(
            "on:\n  push:\n    branches: [main]\njobs:\n  a:\n    timeout-minutes: 5\n"
            "    env:\n      T: ${{ secrets.TOKEN }}\n",
            [],
            id="secret-on-trusted-push",
        ),
        pytest.param(
            "on: pull_request\njobs:\n  a:\n    timeout-minutes: 5\n"
            "    env:\n      T: ${{ github.token }}\n",
            [],
            id="github-token-allowed",
        ),
    ],
)
def test_job_rules_detect_mutations(workflow: str, expected: list[str]) -> None:
    """Each job rule fires on a workflow that breaks it and stays silent otherwise."""
    assert job_violations(_load(workflow), "a") == expected


def test_zizmor_rejects_a_bad_workflow(tmp_path: Path) -> None:
    """The rules delegated to zizmor are live: it flags the trigger and the unpinned action."""
    zizmor = shutil.which("zizmor")
    assert zizmor is not None, "zizmor must be installed (uv sync)"
    workflow = tmp_path / ".github" / "workflows" / "bad.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "on: pull_request_target\njobs:\n  a:\n    runs-on: ubuntu-24.04\n"
        "    steps:\n      - uses: actions/checkout@v4\n"
    )

    completed = subprocess.run(  # noqa: S603
        [zizmor, "--offline", "--format", "json", str(workflow)],
        capture_output=True,
        text=True,
        check=False,
    )

    audits = {finding["ident"] for finding in json.loads(completed.stdout)}
    assert completed.returncode != 0
    assert {"dangerous-triggers", "unpinned-uses"} <= audits
