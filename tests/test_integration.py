"""Platform integration tests: the tool package end to end via a real goga config run.

Deviation from the conventions subprocess-mock rule (recorded in the plan): the
real `python -m goga config` child process is the system under test — the
cross-package interaction between the editable-installed tool and the goga
platform cannot be observed through a patched subprocess call, so patching
would empty the scenarios of meaning. Assertions run on the child's exit code
and captured streams, never on the child's environment.
"""

import importlib.util
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("goga") is None,
    reason="goga platform not installed (test extra required)",
)


@pytest.fixture
def authored_config(tmp_path: Path) -> Callable[[str], Path]:
    """Return a writer creating a throwaway goga project with the given authored config."""

    def write(content: str) -> Path:
        config_dir = tmp_path / ".goga"
        config_dir.mkdir()
        config_path = config_dir / "config.yml"
        config_path.write_text(content, encoding="utf-8")

        return config_path

    return write


def _run_goga_config(project_dir: Path, query: str) -> subprocess.CompletedProcess:
    """Run the real goga platform in the throwaway project and capture its streams."""
    return subprocess.run(
        [sys.executable, "-m", "goga", "config", query],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_integration_minimal_config_receives_presets(tmp_path: Path, authored_config: Callable[[str], Path]) -> None:
    """Applies all three presets on a minimal config and leaves the authored file untouched."""
    config_path = authored_config("language: python\n")

    before = config_path.read_text(encoding="utf-8")
    result = _run_goga_config(tmp_path, "build.review")

    assert result.returncode == 0
    assert "strategy: short" in result.stdout
    assert "patience: 1" in result.stdout
    assert "max_iterations: 3" in result.stdout
    assert "config amendments: 3 applied" in result.stderr
    assert "- simple-build set build.review.strategy" in result.stderr
    assert "- simple-build set build.review.additional.patience" in result.stderr
    assert "- simple-build set build.review.additional.max_iterations" in result.stderr
    assert config_path.read_text(encoding="utf-8") == before


def test_integration_authored_values_win_over_presets(tmp_path: Path, authored_config: Callable[[str], Path]) -> None:
    """Keeps authored values, presets the silent leaves, drops the non-silent set silently."""
    config_path = authored_config("language: python\nbuild:\n  review:\n    additional:\n      patience: 4\n")

    before = config_path.read_text(encoding="utf-8")
    result = _run_goga_config(tmp_path, "build.review")

    assert result.returncode == 0
    assert "patience: 4" in result.stdout
    assert "strategy: short" in result.stdout
    assert "max_iterations: 3" in result.stdout
    assert "- simple-build set build.review.strategy" in result.stderr
    assert "- simple-build set build.review.additional.max_iterations" in result.stderr
    assert "- simple-build set build.review.additional.patience" not in result.stderr
    assert config_path.read_text(encoding="utf-8") == before


def test_integration_strategy_conflict_stops_command(tmp_path: Path, authored_config: Callable[[str], Path]) -> None:
    """Stops the command on the strategy conflict without leaking the authored value."""
    authored_config("language: python\nbuild:\n  review:\n    strategy: thorough\n")

    result = _run_goga_config(tmp_path, "language")

    assert result.returncode != 0
    assert "hook build_presets of tool simple-build failed on config.amend_config" in result.stderr
    assert "build.review.strategy" in result.stderr
    assert "thorough" not in result.stdout
    assert "thorough" not in result.stderr


def test_integration_authored_review_iterations_map_into_external_cap(
    tmp_path: Path,
    authored_config: Callable[[str], Path],
) -> None:
    """Maps the authored review-level iteration cap into the external review cap."""
    config_path = authored_config("language: python\nbuild:\n  review:\n    max_iterations: 7\n")

    before = config_path.read_text(encoding="utf-8")
    result = _run_goga_config(tmp_path, "build.review")

    assert result.returncode == 0
    assert "max_iterations: 7" in result.stdout
    assert "config amendments: 3 applied" in result.stderr
    assert "- simple-build set build.review.additional.max_iterations" in result.stderr
    assert config_path.read_text(encoding="utf-8") == before


def test_integration_authored_additional_iterations_win_over_default(
    tmp_path: Path,
    authored_config: Callable[[str], Path],
) -> None:
    """Keeps the authored external cap and silently drops the preset for that leaf."""
    config_path = authored_config("language: python\nbuild:\n  review:\n    additional:\n      max_iterations: 9\n")

    before = config_path.read_text(encoding="utf-8")
    result = _run_goga_config(tmp_path, "build.review")

    assert result.returncode == 0
    assert "max_iterations: 9" in result.stdout
    assert "- simple-build set build.review.additional.max_iterations" not in result.stderr
    assert "- simple-build set build.review.strategy" in result.stderr
    assert config_path.read_text(encoding="utf-8") == before


def test_integration_both_iteration_caps_authored_stop_command(
    tmp_path: Path,
    authored_config: Callable[[str], Path],
) -> None:
    """Stops the command on the iteration-cap conflict without leaking the authored values."""
    authored_config(
        "language: python\nbuild:\n  review:\n    max_iterations: 77\n    additional:\n      max_iterations: 1515\n"
    )

    result = _run_goga_config(tmp_path, "language")

    assert result.returncode != 0
    assert "hook build_presets of tool simple-build failed on config.amend_config" in result.stderr
    assert "build.review.max_iterations" in result.stderr
    assert "build.review.additional.max_iterations" in result.stderr
    assert "77" not in result.stdout
    assert "1515" not in result.stdout
    assert "77" not in result.stderr
    assert "1515" not in result.stderr
