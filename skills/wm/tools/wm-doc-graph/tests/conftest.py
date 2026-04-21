"""Shared pytest fixtures for wm-doc-graph tests.

Each test creates its own tiny markdown repo via `tmp_path` rather than
sharing a static fixture directory — keeps the fixture inputs close to
the assertions and avoids committing fixture data that would drift from
the assertions over time.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


# Canonical tiny repo used by most tests. Three files: `a.md` has a
# header, a signal, and an @-include; `b.md` has a <required_reading>
# block with a bare path mention; `sub/c.md` has a markdown link back
# to `a.md`. Every reference can be flipped on or off by editing one file.
_A_MD = """# Alpha

<purpose>alpha doc</purpose>

@~/.claude/skills/wm/references/gate-matrix.md

See [beta](../b.md) for more.
"""

_B_MD = """# Beta

## Subsection

<required_reading>
skills/wm/references/impact-scan.md
</required_reading>

```python
# This fenced block must not contribute a header or signal
@~/should-be-ignored.md
<purpose>should-be-ignored</purpose>
```
"""

_C_MD = """# Gamma

[back to a](../a.md)

Inline `[text](fake.md)` example — must NOT count as a link.
"""


@pytest.fixture
def markdown_repo(tmp_path: Path) -> Path:
    """Build the canonical tiny markdown repo under `tmp_path`."""
    (tmp_path / "a.md").write_text(_A_MD, encoding="utf-8")
    (tmp_path / "b.md").write_text(_B_MD, encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.md").write_text(_C_MD, encoding="utf-8")
    return tmp_path


@pytest.fixture
def wm_mock_project(tmp_path: Path) -> Path:
    """A WM-shaped mock project with a DECISIONS.md and a plan file.

    Used by integration tests for `impact` and `search`. Structure:

        tmp_path/
        ├── skills/wm/workflows/verify-plan.md  (contains @-includes + signals)
        ├── skills/wm/references/gate-matrix.md (a referenced target)
        ├── projects/sample-project/DECISIONS.md (one FIN mentioning verify-plan.md)
        └── projects/sample-project/plans/sample-plan.md
    """
    (tmp_path / "skills" / "wm" / "workflows").mkdir(parents=True)
    (tmp_path / "skills" / "wm" / "references").mkdir(parents=True)
    (tmp_path / "projects" / "sample-project" / "plans").mkdir(parents=True)

    (tmp_path / "skills" / "wm" / "workflows" / "verify-plan.md").write_text(
        "<purpose>verify a plan</purpose>\n"
        "<required_reading>\n"
        "@~/skills/wm/references/gate-matrix.md\n"
        "</required_reading>\n"
        "<process>\n"
        "<step name='Step 1'>do thing</step>\n"
        "</process>\n",
        encoding="utf-8",
    )
    (tmp_path / "skills" / "wm" / "references" / "gate-matrix.md").write_text(
        "# Gate Matrix\nExample content.\n",
        encoding="utf-8",
    )
    (tmp_path / "projects" / "sample-project" / "DECISIONS.md").write_text(
        "# Decisions\n\n"
        "---\n\n"
        "### FIN-001 — Touch verify-plan.md\n\n"
        "**Decision:** This FIN mentions `verify-plan.md` explicitly.\n\n"
        "**Rationale:** test fixture\n\n"
        "**Status:** suggested\n\n"
        "---\n\n"
        "### FIN-002 — Unrelated FIN\n\n"
        "**Decision:** This one only talks about oranges.\n\n"
        "---\n",
        encoding="utf-8",
    )
    (tmp_path / "projects" / "sample-project" / "plans" / "sample-plan.md").write_text(
        "# Sample plan\n\nStep 1: edit `skills/wm/workflows/verify-plan.md`\n",
        encoding="utf-8",
    )
    return tmp_path


def make_args(**fields) -> SimpleNamespace:
    """Build an argparse-like namespace for verb tests."""
    return SimpleNamespace(**fields)
