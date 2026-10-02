# Deliver simple-build review presets through one config amendment subscription

Source documents: `.goga/history/2026/the-first-version/adr.md` (decision record),
`.goga/history/2026/the-first-version/prd.md` (product requirements).

## Current State

The repository is the `goga-tool-simple-build` tool package project itself:
`pyproject.toml` is configured (Python >=3.10, setuptools + setuptools-scm,
`dependencies = []`, test extra with pytest / pytest-cov / pytest-mock / ruff),
and the package directory `goga_tool_simple_build/` exists — but its facade
`__init__.py` is empty: no `register_hooks` callback, no subscription, no
behavior. The tool currently delivers nothing.

There is no cell architecture yet (`goga schema` reports no cells), no
`tests/` directory, and no CODEMANIFEST. The goga 2.0.x platform usages are
synced and pinned (`.goga/config.yml`: `usages.github.goga.ref: 2.0.x`); the
action this task subscribes to — the hard `config / amend_config` action with
its `ConfigAmendment` view — is fully documented there.

## Description

Implement the tool `goga-tool-simple-build`: exactly one hard-action
subscription to `config / amend_config` (hook name `build_presets`) that

- buffers three unconditional `set` amendments (apply-where-silent;
  authored values win — owned by the platform merge layer, not by the tool):
  - `build.review.strategy` = `short`
  - `build.review.additional.patience` = `2`
  - `build.review.additional.max_iterations` = `5`
- performs a single deliberate read of the authored configuration — the leaf
  `build.review.strategy` — solely as a conflict guard: an authored value
  other than `short` raises an exception whose message names the path
  `build.review.strategy` and never the authored value; the platform turns
  the failure into a clean error naming the tool and the action, stops the
  hosting command, and discards the tool's whole contribution.

Everything else — merge rules, amendment summary to stderr, output secrecy,
file integrity, determinism, hard failure semantics — is owned by the goga
platform and must not be reimplemented in the tool.

## Scope

**In scope:**

- The `register_hooks` facade callback subscribing `build_presets` to
  `config / amend_config`.
- The `build_presets` hook: three unconditional `set` amendments and the
  strategy-conflict guard (the tool's single deliberate failure condition).
- Tests for the above (approach owned by the plan stage — see Notes).
- The test-extra dependency declaration `goga>=2.0` in `pyproject.toml` per
  the `goga-dependency` policy.

**Out of scope:**

- Override (`force`) amendments of any kind.
- Validation of agent presence (`build.review.agent`, `build.agent`,
  `additional.agent`) or of any leaf beyond the strategy conflict (R10).
- Any presets beyond the three review leaves; tasks-pass settings; review
  roles; base_ref; finalize.
- Changes to goga core, domain actions, merge rules, summary format, output.
- Tool-own configuration (user-tunable presets) — the values are constants.
- Subscriptions to any other domain action; an own CLI (`main` facade) or
  `install` lifecycle — the tool is hook-only.
- Runtime dependencies of any kind.

## Acceptance Criteria

- With a minimal authored configuration (e.g. `language` + `build.agent`) and
  the tool installed, every config-consuming goga surface produces an
  effective configuration with `build.review.strategy == "short"`,
  `build.review.additional.patience == 2`,
  `build.review.additional.max_iterations == 5`; `goga config` reports these
  values; the authored `.goga/config.yml` stays byte-identical.
- A configuration with no `build` section at all (e.g. only `language`) loads
  on every config-consuming surface without any error attributable to the
  tool: the absent branches materialize with the three presets, and the
  missing-agent error, where a consumer raises it, belongs to the platform
  (R3 — no agent validation).
- Authored `patience` / `max_iterations` (or `strategy: short`) win: the
  corresponding presets are dropped silently, the remaining silent leaves
  still receive theirs, and the summary lists only applied amendments.
- An authored `build.review.strategy` other than `short` stops every
  config-consuming command with a clean error naming the tool, the action,
  and the path `build.review.strategy`; the authored value never appears in
  the output; no amendment is applied; the file stays byte-identical.
- When amendments apply, the run prints the platform summary to stderr (tool
  plus one line per applied amendment: path, `set`); when nothing applies,
  nothing is printed; no configuration values appear in any output.
- Repeated runs produce the identical effective configuration; with the tool
  removed, the effective configuration equals the authored one exactly.
- The package declares no runtime dependencies, imports cleanly without goga
  installed, and performs no runtime import of goga (TYPE_CHECKING only);
  `goga>=2.0` is declared in the test extra; `pytest tests/ -x` and
  `ruff check goga_tool_simple_build/` pass per `conventions`.

## Stack

- **Frameworks:** goga 2.0.x hooks platform (extension surface only — no
  goga code changes); setuptools + setuptools-scm for packaging.
- **Libraries:** none at runtime (`dependencies = []`). Test-only:
  pytest >=8.0, pytest-cov >=5.0, pytest-mock >=3.10, ruff >=0.15,
  goga >=2.0 (per `goga-dependency`).
- **Infrastructure:** none — the presets live only in the effective
  in-memory configuration of each run.

## External Dependencies

| Component | Usage file | Status |
|-----------|------------|--------|
| goga config domain (amend_config contract) | `.goga/usages/github/goga/config/registering-hooks.md` | existing (synced) |
| goga hooks platform (registration contract) | `.goga/usages/github/goga/hooks/registering-hooks.md` | existing (synced) |
| goga dependency policy | `.goga/usages/cooks/goga-dependency.md` | created |
| project code/test conventions | `.goga/usages/conventions.md` | existing |

Synced usage files are managed by `goga usages sync` — reference them read-only, never create or update them in the task.

## Risks and Constraints

- Platform constraints (from the PRD, binding): extension mechanism only;
  hook receives only declared parameters (`context`, `self`); configuration
  is read-only; amendments only through the buffer; hard-action semantics;
  authored-wins merge rules; no persistence; output secrecy; tool identity
  derived from the package name; import-clean facade; goga 2.0.x target.
- The conflict error must stay value-free — the platform prints the
  exception message verbatim, so the message names the path only.
- Deferred decisions (owned by later pipeline stages, recorded in the ADR):
  module layout (everything in the facade vs facade + registration module,
  the `goga_tool_autonomous` pattern) — design/prototype stage; test approach
  (unit against a stand-in amendment view vs integration through
  `goga config`) — plan stage.
- Environment note: `goga usages status` could not reach the github remote
  from the working environment (check failed); the task is formulated
  against the locally synced 2.0.x state, matching the PRD pin.

## Scope Estimate

Single task — one hook, one subscription, three constants, one guard; no
independent subsystems. No decomposition, no additional topics.

## Existing Architecture

None — `goga schema` reports no cells. The task fills the package facade for
the first time; no existing cells are impacted and no integration points
beyond the documented platform action exist.

## Notes

Approved formulation dialog (specify stage): formulation and boundaries
approved as proposed; a layout-agnostic illustrative code sketch is included
below (approved); the `goga-dependency` cooks usage was created during
formulation with the user's emphasis that goga is exclusively a test
dependency with the version range `>=2.0`.

Illustrative sketch of the contract (Python; not a module-layout decision —
exact placement and None-safe traversal are implementation details):

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from goga.hooks.tools.registration import HookRegistrar


def register_hooks(hooks: "HookRegistrar") -> None:
    """Subscribe the single review-presets hook to the config amendment action."""
    hooks.subscribe("config", "amend_config", "build_presets", build_presets)


def build_presets(context) -> None:
    """Contribute the three review presets; fail on an authored strategy conflict."""
    build = context.config.build
    strategy = build.review.strategy if build is not None and build.review is not None else None

    if strategy is not None and strategy != "short":
        raise ValueError(
            "authored value at build.review.strategy conflicts with the tool's purpose; "
            "remove the authored strategy or uninstall the tool"
        )

    context.set("build.review.strategy", "short")
    context.set("build.review.additional.patience", 2)
    context.set("build.review.additional.max_iterations", 5)
```

The reference pattern for the deferred layout decision exists in the
ecosystem: `goga_tool_autonomous` (facade re-exporting a `registration`
module, with its own CODEMANIFEST and the `goga-dependency` cooks usage this
task now mirrors).
