# Architecture Plan — simple-build-review-presets

## Topic

**Short name:** `simple-build-review-presets`
**Plan path:** `.goga/history/2026/the-first-version/arch.md` (topic: `.goga/history/2026/the-first-version`)

Cells architecture for the `goga-tool-simple-build` tool package: one leaf cell delivering the
tool's entire goga extension surface — a facade callback subscribing a single review-presets
hook to the `config / amend_config` platform action.

Source documents: `prd.md`, `adr.md`, `task.md` (same topic directory).

---

## Implementation Order

| # | Cell | Rationale |
|---|------|-----------|
| 1 | `goga_tool_simple_build` | **Created anew.** No `Imports` — the cell has no project-cell dependencies (leaf and root at once). Nothing precedes it. |

One cell total; the order is trivial but the cell is a leaf by construction, so it is designed
and applied first.

---

## Artifacts

### Cell: `goga_tool_simple_build` — CREATED ANEW

Package directory is the cell (Python: cell = package). Final structure after apply:

```
goga_tool_simple_build/
├── CODEMANIFEST               (create — artifact 1)
├── .usages/
│   └── review-presets.md      (create — artifact 2)
├── __init__.py                (existing, empty — facade re-export per global annotations)
└── registration.py            (implementation location named by the contract)
```

#### Artifact 1 — `goga_tool_simple_build/CODEMANIFEST`

```yaml
Usages:
  conventions: .goga/usages/conventions.md
  config_amendment: .goga/usages/github/goga/config/registering-hooks.md
  hook_registration: .goga/usages/github/goga/hooks/registering-hooks.md
  goga_dependency: .goga/usages/cooks/goga-dependency.md

Annotations: |
  Use `conventions` for code writing rules and testing.
  Use `hook_registration` from Usages for the facade callback and subscription contract.
  Use `config_amendment` from Usages for the amendment view, silence markers, and merge semantics.
  Use `goga_dependency` from Usages for the goga dependency policy.

  The cell is hook-only: no CLI facade and no runtime import of goga — platform types
  (HookRegistrar, ConfigAmendment) are referenced under TYPE_CHECKING only, and the
  package facade stays import-clean with or without goga installed.
  The package facade re-exports the contract API through __all__.
  Contribute amendments exclusively through the apply-where-silent form; never the override form.

---

"register_hooks(hooks: HookRegistrar)":
  location: registration.py
  annotations: |
    Subscribe the tool's single review-presets hook to the configuration amendment action.

    `hooks`: platform registration surface delivered to the facade callback

    Algorithm:
    1. Subscribe `build_presets` to the config / amend_config address under the hook
       name build_presets, using the subscribe operation of `hooks` defined in `hook_registration`

    Requirements:
    - Hook name stays unique per tool per address

    Constraints:
    - Subscribe to no other domain action
    - Do not validate agent presence or any configuration leaf

"build_presets(context: ConfigAmendment)":
  location: registration.py
  annotations: |
    Contribute the three simple-build review presets and guard the strategy conflict.

    `context`: read-and-amend view over the authored configuration, delivered per `config_amendment`

    Algorithm:
    1. Read the authored leaf build.review.strategy from the configuration of `context`;
       absent branches read as absent
    2. If the authored value is present and is not short — raise an exception whose message
       names the path build.review.strategy and never the authored value
    3. Buffer three apply-where-silent amendments through `context`: build.review.strategy
       set to short, build.review.additional.patience set to 2,
       build.review.additional.max_iterations set to 5

    Requirements:
    - Amendments are unconditional — the only deliberate read of the configuration is the
      single guard leaf of step 1
    - Authored-wins is owned by the merge layer — never re-derived here
    - The exact footprint is the three leaf paths of step 3 and nothing else

    Constraints:
    - Never use the override form of amendment — the presets never overwrite authored values
    - Never print or embed configuration values in any output or error message
    - Do not validate agent presence or any leaf beyond the strategy conflict

---

Author: Goga
CreatedAt: 01/10/26
Description: |
  Review presets for simple builds: the tool's single subscription to the goga
  configuration amendment action, contributing the three fixed review leaves and
  guarding the strategy conflict.
```

#### Artifact 2 — `goga_tool_simple_build/.usages/review-presets.md`

````md
# Review presets — what an installed tool guarantees

For project maintainers who install `goga-tool-simple-build` into a goga project
and want to know what the review pass of `goga build` will look like. The tool is
hook-only: there is no command to run and no file to edit for its part — the
presets apply from the first config-consuming goga run after installation.

## What you get

With the tool installed, every goga run that loads `.goga/config.yml` receives
three review presets wherever the authored configuration is silent:

| Path | Value |
|---|---|
| `build.review.strategy` | `short` |
| `build.review.additional.patience` | `2` |
| `build.review.additional.max_iterations` | `5` |

Absent intermediate branches (`build.review`, `build.review.additional`)
materialize on their own — a minimal configuration of `language` alone is enough.

## Relying on the effective values

A minimal authored configuration:

```yaml
language: python
```

Effective review configuration in every run:

```yaml
build:
  review:
    strategy: short
    additional:
      patience: 2
      max_iterations: 5
```

Check the effective values after a run with `goga config` — it prints the amended
values; the run also prints a short amendment summary to stderr naming the tool
and each applied path.

## Authoring your own values

Any review knob written explicitly wins. Author `patience` or `max_iterations`
(or `strategy: short`) and the tool stays silent for those leaves — no warning,
no error — while the remaining silent leaves still receive their presets:

```yaml
build:
  review:
    additional:
      patience: 4   # authored — wins over the preset 2
```

Effective: `strategy: short`, `patience: 4`, `max_iterations: 5`.

## The one deliberate conflict

Authoring `build.review.strategy` with a value other than `short` conflicts with
the tool's purpose. Every config-consuming goga command stops with a clean error
naming the tool, the action, and the path `build.review.strategy` — the authored
value is never printed, nothing is applied. Remove the authored strategy or
uninstall the tool to resolve it.

```yaml
build:
  review:
    strategy: thorough   # conflict — every goga command stops
```

## Side effects and reversibility

- The authored `.goga/config.yml` is never modified — it stays byte-identical;
  the presets live only in the effective in-memory configuration of each run.
- Repeated runs reproduce the same effective configuration.
- Removing the tool from the environment returns the project to exactly its
  authored behavior.
- The tool never validates agent presence and never touches agent values — a
  configuration with no review agent loads without any error from the tool.
````

---

## Dependency Map

```
            [goga platform — external, not designed here]
                 ^                        |
    subscribe    |                        |  delivers ConfigAmendment
                 v                        v
   +---------------------------------------------------+
   |   cell: goga_tool_simple_build   (leaf AND root)  |
   |                                                   |
   |   register_hooks  --subscribe-->  build_presets   |
   |   Imports: none        Usages: 4 practices       |
   |   both Routines located at: registration.py      |
   +---------------------------------------------------+
```

Inter-cell `Imports` connections: **none**. The graph has a single vertex and no edges;
circular dependencies are impossible by construction. The only integration is external —
the platform's `config / amend_config` action, consumed exactly as documented in the synced
usage files (`config_amendment`, `hook_registration`).

---

## Verification Checklist

After applying the artifacts:

- [ ] `goga lint` reports `cells: 1, errors: 0` — the assembled CODEMANIFEST passes DSL
      validation (annotation backtick references resolve; usage filepaths exist).
- [ ] `goga schema` lists cell `goga_tool_simple_build` with types `build_presets` and
      `register_hooks`, `dependencies: {}`, and `usages: ["review-presets.md"]`.
- [ ] Header carries the base usage `conventions` and the base annotation line from
      `.goga/config.yml` (`codemanifest.usages` / `codemanifest.annotations`).
- [ ] All four `Usages` paths resolve to existing files under `.goga/usages/`; the two
      synced platform usages were referenced read-only, not modified.
- [ ] Document structure is Header → Body → Footer with `---` separators; key casing exact;
      `location: registration.py` sits at the cell directory level with an extension.
- [ ] `.usages/review-presets.md` is self-contained (no references to other practices),
      consumer-oriented (how to rely on the presets), and does not duplicate CODEMANIFEST
      annotations.
- [ ] No existing cells were modified (greenfield — `goga schema` was empty before).

Out of plan scope (owned by later pipeline stages, per `task.md`): the `registration.py`
implementation and `__init__.py` facade re-export (design/coding stages), the `goga>=2.0`
test-extra declaration in `pyproject.toml`, and the test approach (plan stage).
