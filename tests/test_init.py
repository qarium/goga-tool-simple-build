"""Facade tests: contract re-export by identity and import cleanliness."""

import subprocess
import sys

import goga_tool_simple_build as facade
from goga_tool_simple_build import registration


def test_facade_reexports_contract_api():
    """Re-exports both contract routines by identity with an exact __all__."""
    assert facade.build_presets is registration.build_presets
    assert facade.register_hooks is registration.register_hooks
    assert facade.__all__ == ["build_presets", "register_hooks"]


def test_facade_imports_without_goga_runtime():
    """Imports in a fresh interpreter without loading any goga module at runtime.

    Deviation from the conventions subprocess-mock rule: the child interpreter is
    the system under test — the only honest source of a fresh sys.modules — so the
    subprocess call is not patched; the child's exit code is the assertion.
    """
    script = (
        "import goga_tool_simple_build, sys; "
        "sys.exit(1 if [m for m in sys.modules if m == 'goga' or m.startswith('goga.')] else 0)"
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0
