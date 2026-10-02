# Configure max_iterations on build.review level

Task (todo.md): if `build.review.max_iterations` is set in the project config, map it to
`build.review.additional.max_iterations`.

User decision (recorded override): the plan was approved with one modification — authoring
BOTH `build.review.max_iterations` and `build.review.additional.max_iterations` must stop the
hosting command as a settings conflict (error naming both paths, never the values). The
decision also overrides the breaking-change STOP raised by the compatibility guard.

---

# Change Plan (final, as executed)

## Task Classification

Type: feature (extension of the `build_presets` hook behavior).

## Affected Cells

| Cell | Files to Modify | What Changes |
|---|---|---|
| `goga_tool_simple_build` | `goga_tool_simple_build/registration.py` | read `build.review.max_iterations` after the strategy guard; new both-caps conflict guard; third preset takes the authored value, otherwise 3 |
| `goga_tool_simple_build` | `goga_tool_simple_build/CODEMANIFEST` | routine algorithm 3 → 5 steps; requirements/constraints reworded for the two deliberate reads and two conflicts; footer description |
| `goga_tool_simple_build` | `goga_tool_simple_build/.usages/review-presets.md` | presets table, mapping subsection, conflicts section |
| `goga_tool_simple_build` | `tests/test_registration.py`, `tests/test_integration.py` | standins, mapping/conflict unit tests, footprint tests both paths, integration scenarios |
| — (consumer docs) | `README.md`, `docs/index.md`, `docs/review-presets.md`, `docs/architecture.md`, `docs/api/facade.md` | presets tables, mapping description, deliberate conflicts, read footprint |

## Change Strategy

1. Guard-first order preserved: strategy conflict raises before the iteration leaves are read.
2. Mapping is a preset, never an override: `set` only; authored `additional.max_iterations`
   still wins through the platform merge layer; both authored → hard conflict error.
3. No tool-side value validation beyond the two conflicts (0 and negative values map verbatim).

## Compatibility Verification

Not fully backward compatible (conditional behavior change for the input class with an
authored review-level cap; new stopping error when both caps are authored; footprint
guarantee widened to two deliberate reads). Escalated to the user; explicitly overridden and
extended with the both-caps conflict requirement.

## Test Strategy

Unit: verbatim mapping (7/0/-1/999), silent additional leaf, only-additional-authored keeps 3,
both-caps conflict (paths not values, boundaries 0), strategy-conflict precedence, read
footprint on failure and happy paths, absent intermediate branches.
Integration (real `python -m goga config`): mapping 7 → effective 7 with 3 applied; authored
additional 9 wins with the preset line dropped; both caps authored stop the command without
value leakage.

---

# Change Execution Report

## Summary

The `build_presets` amendment hook of `goga-tool-simple-build` now maps the authored
review-level iteration cap `build.review.max_iterations` into the external review cap preset
`build.review.additional.max_iterations` (default 3 kept when the review-level leaf is
silent), and stops every config-consuming goga command with a clean error when both iteration
caps are authored at once — the settings-conflict guard requested in the user decision. The
specification (CODEMANIFEST), the cell practice (`.usages/review-presets.md`), the consumer
docs and the test suite were reconciled in lockstep; the platform merge semantics
(apply-where-silent, authored-wins) are untouched.

## Root Cause

Functional gap (not a defect): the hook buffered a hardcoded 3 and deliberately read only the
strategy guard leaf, so a valid authored `build.review.max_iterations` had no effect on the
external review cap. Evidence chain: todo task → goga config model (both leaves are known
int-or-absent leaves) → `registration.py` → tests/docs fixing the constant.

## Modified Cells

| Cell | Files Modified |
|---|---|
| `goga_tool_simple_build` | `registration.py`, `CODEMANIFEST`, `.usages/review-presets.md` |

## Implemented Changes

| Change | File | Description |
|---|---|---|
| Mapping read | `goga_tool_simple_build/registration.py` | reads `review.max_iterations` (absent branches read as absent) after the strategy guard |
| Both-caps conflict guard | `goga_tool_simple_build/registration.py` | raises `ValueError` naming both paths, never values, before any `set` |
| Conditional third preset | `goga_tool_simple_build/registration.py` | `additional.max_iterations` = authored review-level cap when present, else 3 |
| Contract update | `goga_tool_simple_build/CODEMANIFEST` | 5-step algorithm, deliberate reads = guard + two cap leaves, two conflicts, write footprint unchanged |
| Practice update | `goga_tool_simple_build/.usages/review-presets.md` | table row, mapping subsection, "The deliberate conflicts" |
| Consumer docs | `README.md`, `docs/index.md`, `docs/review-presets.md`, `docs/architecture.md`, `docs/api/facade.md` | preset source, mapping scenario, conflicts, read footprint |

## Tests Added

| Test | File | What It Validates |
|---|---|---|
| `test_build_presets_maps_authored_review_iterations_into_external_cap` (×4) | `tests/test_registration.py` | verbatim mapping incl. 0 / -1 / 999 |
| `test_build_presets_maps_review_iterations_with_silent_additional_leaf` | `tests/test_registration.py` | mapping with present-but-silent additional leaf |
| `test_build_presets_keeps_default_cap_when_only_additional_authored` | `tests/test_registration.py` | default 3 buffered when only the additional leaf is authored |
| `test_build_presets_raises_when_both_iteration_caps_authored` (×4) | `tests/test_registration.py` | both-caps conflict, paths-not-values, boundaries |
| `test_build_presets_strategy_conflict_takes_precedence_over_iteration_conflict` | `tests/test_registration.py` | guard ordering |
| `test_build_presets_conflict_read_footprint_is_guard_leaf_only` | `tests/test_registration.py` | failure path reads only the strategy chain |
| `test_build_presets_read_footprint_is_guard_and_iteration_chains_only` | `tests/test_registration.py` | happy path reads exactly guard + both cap chains |
| `test_integration_authored_review_iterations_map_into_external_cap` | `tests/test_integration.py` | real platform: 7 → effective 7, 3 applied, file untouched |
| `test_integration_authored_additional_iterations_win_over_default` | `tests/test_integration.py` | real platform: authored 9 wins, preset line dropped |
| `test_integration_both_iteration_caps_authored_stop_command` | `tests/test_integration.py` | real platform: command stops, no value leakage |

## Specification Updates

| Cell | CODEMANIFEST Changes | Usage Changes |
|---|---|---|
| `goga_tool_simple_build` | `build_presets` annotations: algorithm 5 steps, requirements (two deliberate reads, write footprint), constraints (two conflicts); footer description | `.usages/review-presets.md`: preset table, mapping subsection, deliberate conflicts |

## Validation Results

VERIFIED — 32 tests passed; ruff check/format clean; `goga lint` 1 cell / 0 errors; facade
import and goga-free import clean; coverage 100% statements + branches; end-to-end check in a
throwaway project: authored `max_iterations: 5` → effective `additional.max_iterations: 5`
with `config amendments: 3 applied`.

## Compatibility Status

BREAKING (per compatibility guard): conditional behavior change for configs with an authored
review-level cap (3 → authored value) and a new stopping error when both caps are authored;
manifest footprint guarantee widened; one footprint test and standins updated. Resolved by
explicit user override (q1) that also introduced the both-caps conflict requirement.

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Effective external cap changes for existing projects with an authored review-level cap | medium | intended by the task; visible in the amendment summary; user-approved |
| Projects authoring both caps now stop | medium | requested by the user; clean error naming both paths and the resolution |
| Standin drift from the real config model | low | integration tests run against the real goga platform |
| Triple inconsistency code/manifest/docs | low | reconciler + drift analyzer steps passed; grep audit clean |

## Updated Files

- `goga_tool_simple_build/registration.py`
- `goga_tool_simple_build/CODEMANIFEST`
- `goga_tool_simple_build/.usages/review-presets.md`
- `tests/test_registration.py`
- `tests/test_integration.py`
- `README.md`
- `docs/index.md`
- `docs/review-presets.md`
- `docs/architecture.md`
- `docs/api/facade.md`
