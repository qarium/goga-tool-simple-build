"""Guard tests for the root-level dependency policy declared in pyproject.toml."""

from pathlib import Path

PYPROJECT_TOML = Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_pyproject_declares_goga_test_extra_only() -> None:
    """Verify goga is declared exactly once and only inside the test extra.

    The dependency policy keeps the runtime dependency list empty and pins the
    goga platform exclusively as a test dependency: exactly one `goga>=`
    requirement, located inside the `[project.optional-dependencies]` table.
    The check is text-level on purpose — `tomllib` is Python 3.11+ while the
    package targets 3.10.
    """
    content = PYPROJECT_TOML.read_text(encoding="utf-8")

    assert "dependencies = []" in content

    assert content.count("goga>=") == 1

    optional_table = content.index("[project.optional-dependencies]")
    goga_entry = content.index("goga>=2.0")
    setuptools_scm_section = content.index("[tool.setuptools_scm]")

    assert optional_table < goga_entry < setuptools_scm_section
