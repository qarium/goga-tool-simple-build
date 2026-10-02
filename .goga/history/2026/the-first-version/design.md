# Design Document: `the-first-version`

Topic directory: `.goga/history/2026/the-first-version/` (short name of the work:
`simple-build-review-presets`). Source documents: `prd.md`, `adr.md`, `task.md`, `arch.md`
(same directory). Contract under design: `goga_tool_simple_build/CODEMANIFEST` — created
anew by the apply-architecture stage, byte-exact from `arch.md` artifact 1.

The design below specifies **what to implement and how**: the complete architectural
specification of the `goga-tool-simple-build` tool package against its CODEMANIFEST
contract. Implementation order remains with the plan stage; implementation code is not
written here.

Platform baseline: goga **2.0.1** (installed at `/opt/goga`, matching the
`usages.github.goga.ref: 2.0.x` pin). Every platform fact used below was verified against
the installed source, not assumed: `goga/hooks/tools/packages.py`,
`goga/hooks/tools/registration.py`, `goga/hooks/dispatch/delivery.py`,
`goga/config/hooks/events.py`, `goga/config/hooks/amendments.py`,
`goga/config/hooks/overlay.py`, `goga/config/project/config.py`,
`goga/hooks/catalog/catalog.py`.

---

## Contract Changes

### Changed CODEMANIFEST Files

- `goga_tool_simple_build/CODEMANIFEST`: **created anew** (greenfield cell; `goga schema`
  was empty before). One leaf-and-root cell, no `Imports`, two Routine entities, four
  file-form `Usages`, global annotations fixing the hook-only policy. Validated:
  `goga lint` → `cells: 1 errors: 0`.

### New Entities

- `register_hooks(hooks: HookRegistrar)` — the facade callback; subscribes the tool's
  single hook to the platform action `config / amend_config`. Location: `registration.py`.
- `build_presets(context: ConfigAmendment)` — the hook; guards the strategy conflict and
  buffers the three apply-where-silent review presets. Location: `registration.py`.

Both are Routines (single-operation callables, no `methods`/`properties`) — correct per
`goga-cookbook`: each is one transformer-style operation. Both signatures legitimately
omit the output (nothing is returned).

### Changed Entities

- None (no prior contract existed).

### Deleted Entities

- None.

### Usages and Annotations Changes

- `conventions` → `.goga/usages/conventions.md` (project base usage, from
  `.goga/config.yml` `codemanifest.usages`) — code and test rules.
- `config_amendment` → `.goga/usages/github/goga/config/registering-hooks.md` (synced
  platform usage, read-only) — amendment view, silence markers, merge semantics.
- `hook_registration` → `.goga/usages/github/goga/hooks/registering-hooks.md` (synced
  platform usage, read-only) — facade callback and subscription envelope.
- `goga_dependency` → `.goga/usages/cooks/goga-dependency.md` (project cook) — goga is
  exclusively a test dependency (`goga>=2.0`), never a runtime one.
- Global `Annotations` — hook-only policy: no CLI facade, no runtime goga import,
  `TYPE_CHECKING`-only platform types, import-clean facade re-exporting through
  `__all__`, apply-where-silent amendments only.

Cell-level consumer documentation `goga_tool_simple_build/.usages/review-presets.md`
created together with the contract (arch.md artifact 2) — see `.usages/` Update below.

---

## Applied Fixes

### Fixed CODEMANIFEST Defects

- None. Static validation (Phase 3) and full tracing (Phase 4) found **no CODEMANIFEST
  defects**: document structure Header → Body → Footer with `---` separators and exact
  key casing; both `location: registration.py` values sit at the cell-directory level
  with a Python extension; every backtick reference resolves inside the document context
  (`hooks`, `context` — signature variables; `conventions`, `hook_registration`,
  `config_amendment`, `goga_dependency` — header Usages keys); `HookRegistrar` /
  `ConfigAmendment` appear in signatures and non-backtick prose only — justified because
  goga is an external platform, not a project cell, so `Imports` cannot address it; the
  usage files document its exact API and were verified against the installed 2.0.1
  source. No mutations, no embeddings, no `Imports` — nothing to reconcile cross-cell.

---

## Entity Interaction and Data Flow

### Interaction Diagram

```
        goga platform  (external — not designed here; verified against 2.0.1 source)
        │  enumerate installed goga_tool_* packages (alphabetical, no imports)
        │  import facade  goga_tool_simple_build/__init__.py      [single import point]
        │  call module.register_hooks(registrar)                  [positional, 1 arg]
        ▼
  ┌─ registration.register_hooks ─────────────────────────────────────────────┐
  │  hooks.subscribe("config", "amend_config", "build_presets", build_presets)│
  └──────────────────────────┬─────────────────────────────────────────────────┘
                             ▼
        HookRegistrar (platform): validates the envelope against the declared
        action catalog → appends Subscription{tool: "simple-build",
        domain: "config", action: "amend_config", name: "build_presets",
        hook: <function build_presets>}
                             │
                             │  later: a config-consuming surface loads .goga/config.yml
                             │  (authored load finished, before any consumer reads)
                             ▼
        platform: ConfigAmendment(config = read-only snapshot of authored tree)
                  → delivery proxy (reads pass, writes blocked)
                  → argument projection by declared names → hook(context=proxy)
  ┌─ registration.build_presets ──────────────────────────────────────────────┐
  │  1. read   context.config.build.review.strategy     (the single guard read)│
  │  2. guard  authored strategy present and != "short" → raise ValueError     │
  │            (message names the path, never the value) → HARD failure:       │
  │            command stops, whole contribution discarded                     │
  │  3. buffer context.set("build.review.strategy", "short")                   │
  │            context.set("build.review.additional.patience", 2)              │
  │            context.set("build.review.additional.max_iterations", 5)        │
  └──────────────────────────┬─────────────────────────────────────────────────┘
                             ▼
        platform merge (authored-wins): silent leaves receive presets, absent
        branches materialize, authored values stay; overlay summary lines
        (tool, path, set — never values) printed to stderr by the caller;
        the authored .goga/config.yml stays byte-identical
```

### Data Flows

**Flow 1 — registration moment** (once per registry build; never cached across runs):
1. A goga command reaches its first hook checkpoint of the run (or `goga hooks`
   inspects the registry) → `HookRegistry.build_once()`.
2. `enumerate_tool_packages()` finds the installed `goga_tool_simple_build` distribution
   → `ToolPackage(module_name="goga_tool_simple_build")`; derived tool identity:
   `"simple-build"` (prefix `goga_tool_` dropped, underscores → hyphens — a package never
   names itself).
3. `call_register_hooks` imports the facade module `goga_tool_simple_build` (the package
   `__init__.py`) — the only import of a tool package in the whole platform. A facade
   without a callable `register_hooks` attribute is a **quiet skip** (the tool delivers
   nothing) — hence the mandatory facade re-export. A broken facade import is the single
   **fatal** case (clean `ImportError` naming the package) — hence the import-clean
   requirement.
4. The facade calls through to `registration.register_hooks(registrar)`; one
   `subscribe` envelope enters the registrar; data passed: `"config"`, `"amend_config"`,
   `"build_presets"`, the `build_presets` function object itself (identity, no wrapper).
5. Execution order note: the facade is imported and the callback runs **before** any
   hook fires; commands that use no hooks never call it.

**Flow 2 — amendment moment** (at the load moment of `.goga/config.yml` on every
config-consuming surface):
1. Authored file loads; structurally invalid files fail in the loader **before** the
   checkpoint (nothing fires — the tool is not involved).
2. Platform groups the address subscriptions per tool in enumeration order; builds a
   fresh `ConfigAmendment` over a per-tool read-only snapshot of the same authored tree
   (tools are mutually blind); wraps it in the delivery proxy; projects arguments by
   declared names — `build_presets` declares `context` only, so it receives exactly the
   proxy (and nothing for undeclared names; `self` is not declared and not delivered).
3. `build_presets` reads the guard leaf, raises or buffers, returns `None`.
4. On clean return with a non-empty buffer: the tool commits as one unit
   (`ToolAmendment`); the platform merges onto the authored base (authored-wins;
   `set` dropped silently where the authored tree is not silent — silence markers are
   the loaded model's `None` / `{}` / `[]`; authored emptiness `False` / `""` is
   authored, not silent) and returns the overlay; summary lines go to stderr, values
   never appear; the authored file is never modified.
5. On raise: hard action — the first failing tool stops the command; the platform wraps
   the exception as
   `ValueError("hook build_presets of tool simple-build failed on config.amend_config: <tool message verbatim>")`;
   the tool's whole contribution (view + buffer) is discarded; nothing partial applies.

### Entity Dependencies

- `register_hooks` depends on `build_presets` — the function object is passed as the
  `hook` argument at subscribe time. Both live in `registration.py`; no initialization
  order, no shared state, each importable independently.
- The facade `__init__.py` depends on `registration.py` (relative intra-package import —
  mandatory per `conventions`).
- No cell-level dependencies (`dependencies: {}` in `goga schema`); no cells depend on
  this one (`goga schema --depends-on goga_tool_simple_build` → `[]`). The only external
  integration is the platform action, consumed exactly as documented in the synced
  usages.

---

## Code Stack Trace

### Trace: `register_hooks`

#### Chain

1. **Input**: the platform calls the facade attribute `register_hooks` positionally with
   one argument — the `HookRegistrar` instance scoped to tool identity `simple-build`.
   Delivered by `call_register_hooks` after the facade import.
   → checkpoint: the facade re-export must expose `register_hooks` as the very function
   object from `registration.py` (identity, no wrapper) — **passed** (design: relative
   import re-export through `__all__`).
2. **Step**: the parameter must accept a positional-argument call — a plain
   (keyword-capable) parameter `hooks`. The platform calls `callback(registrar)`
   positionally.
   → checkpoint: parameter shape compatible — **passed**.
3. **Step**: single call
   `hooks.subscribe("config", "amend_config", "build_presets", build_presets)`.
   The registrar resolves `domain`/`action` against the declared action catalog —
   `Action(domain="config", name="amend_config", error_class="hard")` is declared
   (verified in `goga/hooks/catalog/catalog.py`) → the address is known.
   → checkpoint: address exists; envelope valid — non-empty string name
   `"build_presets"`, callable hook (module-level function object) — **passed**.
4. **Step**: registrar appends `Subscription(tool="simple-build", domain="config",
   action="amend_config", name="build_presets", hook=<build_presets>)`. The registrar
   never calls the hook and never raises on this envelope.
   → checkpoint: contract constraint "hook name stays unique per tool per address" —
   the tool issues exactly one `subscribe`; a repeat would only occur if the platform
   invoked the callback twice on one registrar, which the registrar itself rejects as
   data (warning) — nothing for the tool to guard — **passed**.
5. **Output**: `None`. Side effect: one subscription in the registrar. No other domain
   action is addressed; nothing is validated; nothing is printed.
   → checkpoint: contract constraints "subscribe to no other domain action",
   "do not validate agent presence or any configuration leaf" — the body is the single
   subscribe call and nothing else — **passed**.

#### Checkpoint Summary

- facade exposes the callback by identity: **passed**
- positional-call compatibility of the signature: **passed**
- address `config / amend_config` declared; envelope valid: **passed**
- single-subscription uniqueness by construction: **passed**
- no extra actions, no validation, no output: **passed**

### Trace: `build_presets`

#### Chain

1. **Input**: the platform calls `build_presets(context=<delivery proxy>)` — by keyword
   projection of the declared name. The proxy wraps a `ConfigAmendment` whose `config`
   attribute is a read-only snapshot of the authored `ProjectConfig`. Attribute **reads**
   pass through (plain attributes, properties, bound methods); attribute **assignment and
   deletion raise** on the proxy.
   → checkpoint: the hook declares only `context` (a plain, keyword-capable parameter —
   a positional-only parameter would receive nothing and break the call); all
   interaction is reads plus `set` calls — no writes to the context — **passed**.
2. **Step (guard read)**: None-safe traversal of the authored tree:
   `build = context.config.build` (`BuildConfig | None`);
   if `build` is `None` → strategy absent; else `review = build.review`
   (`ReviewConfig | None`); if `review` is `None` → strategy absent; else
   `strategy = review.strategy` (`str | None`; `None` when unset).
   → checkpoint: attribute chain verified against the platform model
   (`goga/config/project/config.py`: `ProjectConfig.build`, `BuildConfig.review`,
   `ReviewConfig.strategy`) — the exact leaves the contract names — **passed**.
   → checkpoint: absent branches read as absent (no `AttributeError`, no default
   fabrication) — **passed** (design: two-level `None` guard).
3. **Step (conflict guard)**: if `strategy is not None and strategy != "short"` → raise
   `ValueError` with the message naming the path `build.review.strategy` and never the
   authored value; exact wording (design-fixed):
   `authored value at build.review.strategy conflicts with the tool's purpose; remove the authored strategy or uninstall the tool`
   → checkpoint: exception type — the platform catches `Exception` and embeds
   `str(reason)` verbatim into its wrapper; `ValueError` is idiomatic and matches the
   approved task sketch — **passed**.
   → checkpoint: value-free message — mandatory because the platform prints the message
   verbatim (output secrecy); the wording above interpolates nothing — **passed**.
   → checkpoint: raised **before** any `set` — the buffer stays empty; the hard action
   discards the tool's whole contribution; nothing partial applies — **passed**
   (ordering fixed in the algorithm).
4. **Step (buffer amendments)**: three unconditional `set` calls on `context`:
   `("build.review.strategy", "short")`, `("build.review.additional.patience", 2)`,
   `("build.review.additional.max_iterations", 5)`.
   → checkpoint: all three paths are model-known leaves in the authored vocabulary
   (`build.review.strategy`, `build.review.additional.patience`,
   `build.review.additional.max_iterations` — verified in the model and the overlay's
   field vocabulary); absent intermediate branches (`build.review`,
   `build.review.additional`) materialize in the merge — **passed**.
   → checkpoint: value types match the leaves — `str` for `strategy`, `int` for
   `patience` and `max_iterations` (overlay accepts `str | int | bool | list[str]` and
   type-checks against the node; a wrong type would be a structural hard failure naming
   the tool) — **passed**.
   → checkpoint: apply-where-silent form only — `set`, never `force`; authored-wins is
   owned by the merge (a `set` on a non-silent path is dropped silently by the platform;
   the tool never re-derives that decision) — **passed**.
5. **Output**: `None`. Side effect: the tool's private buffer holds three
   `PathAmendment(intent="set")` entries. After return, the platform commits the tool as
   one unit, merges, prints the summary lines (`simple-build`, path, `set`) to stderr,
   and leaves the authored file byte-identical.
   → checkpoint: footprint is exactly the three leaf paths and nothing else; no
   validation of agent presence or any other leaf; no printing from the tool —
   **passed**.

#### Checkpoint Summary

- delivery projection (`context` only, keyword-capable): **passed**
- guard-read attribute chain matches the platform model: **passed**
- exception type, message wording, value-free-ness: **passed**
- raise-before-buffer ordering (nothing partial): **passed**
- amendment paths, value types, silent-only intent: **passed**
- exact three-path footprint, no extra reads/validations/output: **passed**

---

## Algorithm Design

### `register_hooks`

**Responsibility**: the tool's facade callback — declare the single subscription of the
tool to the platform's configuration amendment action. Runs at registry build; delivers
no behavior of its own.

**Algorithm:**
```
1. Call the subscribe operation of `hooks` with the envelope
   (domain="config", action="amend_config", name="build_presets",
   hook=`build_presets` — the module-level function object by identity)
   → the registrar records one Subscription qualified with tool identity "simple-build"
```

**Errors:**
- none raised by the tool — a refused envelope is registrar-side data (a log warning
  naming tool, action, reason); this envelope is valid by construction (declared address,
  non-empty name, callable hook).

**Edge Cases:**
- callback invoked twice on one registrar (cannot happen with the current platform; a
  repeat would be rejected by the registrar as data) → the tool is stateless and needs
  no guard of its own.

### `build_presets`

**Responsibility**: the tool's only hook — the strategy-conflict guard plus the three
fixed review presets. A pure function of the delivered authored snapshot: same snapshot
in, same buffer out; no environment access, no time, no randomness.

**Algorithm:**
```
1. Read the authored snapshot from `context.config`
   → the read-only authored ProjectConfig view
2. build = snapshot.build
   → BuildConfig or None
3. IF build is None: strategy = None
   ELSE: review = build.review
   → ReviewConfig or None
4. IF review is None: strategy = None
   ELSE: strategy = review.strategy
   → str or None
5. IF strategy is not None AND strategy != "short":
   raise ValueError("authored value at build.review.strategy conflicts with the tool's
   purpose; remove the authored strategy or uninstall the tool")
   → the platform stops the command (hard action) naming the tool, the action, and the
     hook; the tool's whole contribution is discarded; the authored value never appears
6. context.set("build.review.strategy", "short")
   → one buffered apply-where-silent amendment
7. context.set("build.review.additional.patience", 2)
   → one buffered apply-where-silent amendment
8. context.set("build.review.additional.max_iterations", 5)
   → one buffered apply-where-silent amendment
9. Return nothing
   → the platform commits the buffer as one unit and merges (authored-wins)
```

**Errors:**
- `ValueError` (step 5) — the single deliberate failure condition → the consumer
  observes a clean command error: `hook build_presets of tool simple-build failed on
  config.amend_config: <the message above>`; nothing is applied by this tool; the
  hosting command does not run.
- No other error path exists in the tool: the traversal is `None`-safe on every level,
  and `set` performs no validation of its own (structural failures belong to the merge).

**Edge Cases:**
- authored tree without a `build` branch (e.g. only `language`) → steps 3 → strategy
  `None` → guard passes → three sets; the merge materializes `build.review` and
  `build.review.additional`.
- `build` present, `review` absent → same as above.
- `review` present, `strategy` unset (`None`) → guard passes.
- authored `strategy: short` → guard passes (it **is** `short`); the three sets are
  buffered unconditionally — the merge then drops the `strategy` set (the path is not
  silent) and applies the other two. The tool never conditions its sets.
- authored `strategy: ""` or whitespace-only (e.g. `"   "`) → loads as `None`: the
  loader stores `build.review.strategy` by the agent-pattern strip rule (absent /
  YAML-null / empty-or-whitespace-only → `None`; non-empty → stored stripped —
  verified in `goga/config/project/loader.py`, `_parse_optional_stripped_str`) →
  reads as absent → guard passes → the preset applies (the path is silent). The
  merge-layer rule "authored emptiness (`False`, `""`) is authored, not silent"
  speaks about the loaded model's markers; at this leaf the loader never yields
  `""` — empty strings collapse to `None` before either the hook or the merge ever
  sees them.
- authored `strategy: "short "` (any whitespace padding) → loads as `"short"`
  (stripped by the loader) → guard passes. The authored values that reach the hook
  are exactly the stripped strings: `"short"` passes, any other (`full`, `medium`,
  `thorough`) → conflict → raise. The comparison stays exact literal equality with
  no trimming or normalization of the tool's own — normalization belongs to the
  loader; performing it in the tool would be value interpretation.
- values authored at `patience` / `max_iterations` → invisible to the tool (it reads
  only the guard leaf); the sets on those paths are dropped silently by the merge.

---

## Cross-cutting Concerns

- **Error handling**: one deliberate raise (`ValueError`, value-free message, before any
  buffering). No `try`/`except` anywhere in the tool — nothing is swallowed, nothing is
  retried, no fallback exists. Wrapping, stopping, discarding, and reporting belong to
  the platform's hard-action machinery and are not reimplemented.
- **Logging**: none. The tool emits no log records and prints nothing. The platform owns
  every observable output of the action (stderr summary, error text); the tool's silence
  is what keeps configuration values out of every output channel. `conventions`'
  logging rules govern the *choice of library when logging is used* — the tool
  deliberately uses none.
- **Validation**: the strategy-conflict guard is the only validation. No agent presence
  checks (`build.agent`, `build.review.agent`, `additional.agent`), no leaf validation
  beyond the guard, no structural validation of amendments (merge-owned). Invalid input
  data in the authored sense is impossible to reach here: a structurally invalid config
  file fails in the platform loader before the checkpoint.
- **Caching**: none. The hook is a pure function of the delivered snapshot; registration
  is never cached by the platform (package edits apply from the next run), so the tool
  caches nothing either. Repeated runs reproduce the identical effective configuration.
- **Concurrency**: stateless module-level functions; no module or global mutation; no
  shared mutable state. Safe under any enumeration/delivery threading model the platform
  uses (the current platform enumerates tools sequentially).

---

## Usages Analysis

### `conventions`
- **What it provides**: mandatory project rules for Python code and tests — Python 3.10+,
  relative intra-package imports, Google-style docstrings, blank-line block separation,
  pyproject dependency declarations, test structure mirroring, naming, mock policy,
  validation commands.
- **Where used**: global `Annotations` — applies to both entities, the facade, and every
  test.
- **Why chosen**: the project base usage pinned in `.goga/config.yml`
  (`codemanifest.usages`); binding for all code in the repository.
- **How exactly**: `registration.py` and `__init__.py` use relative imports
  (`from .registration import ...`), Google-style docstrings on both public routines,
  one-blank-line block separation inside function bodies; `dependencies = []` stays;
  `goga>=2.0` goes into `[project.optional-dependencies].test`; tests live at
  `tests/test_*.py` mirroring root package modules; validation via
  `pytest tests/ -x` and `ruff check goga_tool_simple_build/` inside a virtualenv.

### `hook_registration`
- **What it provides**: the facade-callback contract (`register_hooks`), the subscribe
  envelope (`domain`, `action`, `name`, `hook`), the fixed offered hook parameter names
  (`context`, `self`), when registration runs, and the platform's failure behavior for
  registrations.
- **Where used**: `register_hooks` annotations (the subscribe operation of `hooks`);
  global `Annotations`.
- **Why chosen**: it is the authoritative synced description of the exact platform
  surface the tool implements; verified against `goga/hooks/tools/registration.py` and
  `goga/hooks/tools/packages.py` of 2.0.1.
- **How exactly**: one `hooks.subscribe("config", "amend_config", "build_presets",
  build_presets)` call; the hook declares `context` only (no `self` — the tool keeps no
  cross-invocation state); the package never names its own identity.

### `config_amendment`
- **What it provides**: the `config / amend_config` action — hard semantics, the
  `ConfigAmendment` view (`config` read-only snapshot, `set` / `force` buffers), the
  authored silence markers (`None`, `{}`, `[]`), the merge rules (authored-wins, `force`
  beats `set`, enumeration order), the failure treatment, and the run output contract.
- **Where used**: `build_presets` annotations (the view of `context`, the silent-only
  contribution form, the merge ownership); global `Annotations`.
- **Why chosen**: the authoritative synced description of the action being subscribed;
  verified against `goga/config/hooks/events.py`, `amendments.py`, and `overlay.py`.
- **How exactly**: the read side uses `context.config.build.review.strategy` with
  `None`-safe traversal; the write side uses `context.set(path, value)` three times;
  `force` is never called; authored-wins, summary output, and file integrity are left to
  the platform.

### `goga_dependency`
- **Where used / What it provides**: the dependency policy — goga is never a runtime
  dependency (`[project].dependencies` stays empty), platform types under
  `typing.TYPE_CHECKING` only, structural interaction with delivered objects, and goga
  declared exclusively in the test extra as `goga>=2.0` (floor at the supported platform
  line, no upper cap).
- **Why chosen**: created during task formulation with the user's explicit emphasis on
  the test-only dependency with the range `>=2.0`.
- **How exactly**: `registration.py` imports `HookRegistrar` and `ConfigAmendment` under
  `TYPE_CHECKING` from `goga.hooks.tools.registration` and `goga.config.hooks.amendments`
  (paths verified in 2.0.1); annotations are unevaluated at runtime via
  `from __future__ import annotations`; the facade performs no goga import at all;
  `pyproject.toml` gains `goga>=2.0` in the `test` extra only.

### Imported Usages

- None — the cell has no `Imports`.

All four connected practices are referenced in annotations (global and entity-level);
no unreferenced practice exists, no annotation references anything outside the document
context.

---

## `.usages/` Update

### Cell: `goga_tool_simple_build`

#### Existing Files — Consistency

- **`review-presets.md`** → `goga_tool_simple_build/.usages/review-presets.md`
  - Status: **current** — verified against the CODEMANIFEST and the platform source:
    - the three preset rows (`build.review.strategy` = `short`,
      `build.review.additional.patience` = `2`,
      `build.review.additional.max_iterations` = `5`) match the contract algorithm;
    - materialization of absent branches matches the merge behavior;
    - authored-wins description ("authoring your own values") matches the silence
      markers and the silent-drop rule; authored `strategy: short` correctly described
      as the tool staying silent for that leaf from the effective standpoint;
    - the conflict section matches the guard: every config-consuming command stops, the
      error names tool + action + path `build.review.strategy`, the authored value is
      never printed, nothing is applied;
    - side-effects section matches the contract constraints: byte-identical authored
      file, deterministic repeats, clean removal, no agent validation;
    - `goga config` printing effective (amended) values — matches the platform output
      contract.
  - Additions needed: none. Both contract entities are covered from the consumer side
    (the subscription implicitly — "the tool is hook-only: there is no command to run";
    the presets and the conflict explicitly).
  - Updates needed: none. The file is self-contained (no references to other practices),
    consumer-oriented, and does not duplicate CODEMANIFEST annotations.

#### New Files (if any)

- None — the cell exposes one functional domain (the review presets); one file covers
  it.

---

## Test Stack Trace

Test approach note (`task.md`): the scenarios below are recorded at the **unit level
against stand-in doubles** of the two platform objects — the tool talks to the delivered
objects structurally, so a stand-in with the same structural surface exercises the whole
contract without a goga runtime import. The final structuring of the suite (and any
integration-level additions through `goga config`) belongs to the plan stage.

### General Setup

- Virtualenv outside the project tree under `/opt/project` (created by the
  implementation stage if missing), with the package installed editable plus its `test`
  extra (`goga>=2.0` included).
- `tests/__init__.py` present (mandatory per `conventions`); no `conftest.py` needed
  beyond local fixtures placed in the test files themselves (root-package modules).
- Stand-in doubles (test-local, no mocks of imports — the tool imports nothing from goga
  at runtime, so there is nothing to patch):
  - `StandinRegistrar`: records `subscribe(domain, action, name, hook)` calls as tuples.
  - `StandinAmendment`: carries `config` (a stand-in authored tree with plain attributes
    and `None` defaults) and records `set(path, value)` calls as `(path, value)` tuples;
    no `force` method needed — the contract never calls it (its absence also proves the
    point: any `force` call would raise `AttributeError` and fail the test).
  - The stand-in config tree mirrors the platform model shape:
    `build` (`None`-able) → `review` (`None`-able) → `strategy: str | None`,
    `additional` (`None`-able) → `patience` / `max_iterations`.
- Delivery-shape fidelity: tests call `build_presets(context=amendment)` by keyword (the
  platform's projection is keyword-based) and `register_hooks(hooks=registrar)`
  (the platform calls positionally — both shapes are exercised across the suite).

### Source File Registry

- `goga_tool_simple_build/registration.py` — both routines under test.
- `goga_tool_simple_build/__init__.py` — facade re-export under test.
- `pyproject.toml` — dependency-declaration guard test.

---

### Positive Tests

#### `test_register_hooks_subscribes_single_review_hook`

**Setup**: `registrar = StandinRegistrar()`; import
`register_hooks` and `build_presets` from `goga_tool_simple_build.registration`.

**Input**: `register_hooks(hooks=registrar)`

**Trace**:
```
register_hooks(hooks=registrar)
  → registrar.subscribe("config", "amend_config", "build_presets", <build_presets>)
    side effect: StandinRegistrar.records == [("config", "amend_config", "build_presets", <function build_presets>)]
  → returns None
```

**Assertions**:
```
len(registrar.records) == 1
registrar.records[0][:3] == ("config", "amend_config", "build_presets")
registrar.records[0][3] is registration.build_presets   # identity — no wrapper
```

**Sufficiency**: pins the entire subscription envelope — a wrong domain/action address
(the registrar would reject it with a warning and the tool would silently deliver
nothing), a renamed hook, or a wrapped hook function would all fail here. This is the
tool's only wiring; it must be exact.

---

#### `test_build_presets_buffers_three_presets_when_branches_absent`

**Setup**: `amendment = StandinAmendment(config=StandinConfig(build=None))` — the minimal
authored configuration (no `build` branch at all).

**Input**: `build_presets(context=amendment)`

**Trace**:
```
build_presets(context=amendment)
  → read amendment.config            # authored snapshot
  → build = None                     # absent branch reads as absent
  → strategy = None                  # guard passes
  → amendment.set("build.review.strategy", "short")           side effect: buffered
  → amendment.set("build.review.additional.patience", 2)      side effect: buffered
  → amendment.set("build.review.additional.max_iterations", 5) side effect: buffered
  → returns None
```

**Assertions**:
```
amendment.buffered == [
    ("build.review.strategy", "short"),
    ("build.review.additional.patience", 2),
    ("build.review.additional.max_iterations", 5),
]
```

**Sufficiency**: the core delivery — the three exact constants with the three exact
dotted paths, unconditional, in the absence of every authored branch. Prevents value
drift (e.g. patience 3) and path drift (e.g. a `build.review_strategy` typo — which the
merge would reject as a structural hard failure naming the tool).

---

#### `test_build_presets_buffers_presets_when_strategy_authored_short`

**Setup**:
`amendment = StandinAmendment(config=StandinConfig(build=StandinBuild(review=StandinReview(strategy="short"))))`.

**Input**: `build_presets(context=amendment)`

**Trace**:
```
build_presets(context=amendment)
  → strategy = "short"               # present and equal — guard passes
  → three unconditional set calls    # buffering is not conditioned on authored values
  → returns None
```

**Assertions**:
```
no exception raised
amendment.buffered == [same three tuples as above]   # strategy included
```

**Sufficiency**: prevents conditional-set logic from creeping in — the contract requires
unconditional buffering; authored-wins is the merge layer's decision, never re-derived
here. If the tool learned to skip the strategy set on an authored "short", silent-drop
semantics would fork between the tool and the platform.

---

#### `test_facade_reexports_contract_api`

**Setup**: fresh import of the package facade
(`import goga_tool_simple_build as facade`).

**Input**: attribute access on the facade module.

**Trace**:
```
import goga_tool_simple_build
  → __init__.py executes `from .registration import build_presets, register_hooks`
  → facade.build_presets and facade.register_hooks resolve to the registration objects
```

**Assertions**:
```
facade.build_presets is registration.build_presets
facade.register_hooks is registration.register_hooks
facade.__all__ == ["build_presets", "register_hooks"]
```

**Sufficiency**: the platform imports the facade module and looks for a callable
`register_hooks` attribute — a missing re-export is a **quiet skip**: the tool installs,
registers nothing, and delivers nothing, with no error anywhere. This test is the only
guard against that silent failure mode.

---

#### `test_facade_imports_without_goga_runtime`

**Setup**: a fresh interpreter via `subprocess.run([sys.executable, "-c", ...])` with the
package importable; the assertion script imports the package and inspects `sys.modules`.

**Input**: `import goga_tool_simple_build` in the child interpreter.

**Trace**:
```
python -c "import goga_tool_simple_build, sys; modules = [m for m in sys.modules if m == 'goga' or m.startswith('goga.')]; sys.exit(1 if modules else 0)"
  → __init__.py → registration.py — both execute without any goga import
    (HookRegistrar / ConfigAmendment live under TYPE_CHECKING; annotations are
     unevaluated strings via `from __future__ import annotations`)
  → sys.modules contains no 'goga' / 'goga.*' entries
  → exit code 0
```

**Assertions**:
```
result.returncode == 0
```

**Sufficiency**: enforces the `goga_dependency` policy where it is fatal — a runtime goga
import inside the facade makes the package uninstallable in a goga-less environment and
is the platform's single fatal case (broken facade import kills every goga command).
A same-process assertion would be unreliable (pytest plugins may import goga); the child
interpreter keeps the check honest.

**Deviation note**: this scenario deliberately departs from the `conventions`
subprocess-mock rule ("Subprocesses — `mock.patch` the subprocess call"): the child
interpreter is the system under test — the only honest source of a fresh `sys.modules`
— so patching the subprocess call would empty the scenario of meaning. The assertion
runs on the child's exit code, not on captured output.

---

#### `test_pyproject_declares_goga_test_extra_only`

**Setup**: read `pyproject.toml` from the repository root as text.

**Input**: the file content.

**Trace**:
```
read pyproject.toml
  → locate the [project] table: `dependencies = []`      # runtime stays empty
  → locate [project.optional-dependencies] test list: `goga>=2.0` present
```

**Assertions**:
```
"dependencies = []" in content
content.count("goga>=") == 1
content.index("[project.optional-dependencies]") < content.index("goga>=2.0") < content.index("[tool.setuptools_scm]")
```

The second and third assertions together pin the intent "the only pyproject
occurrence of `goga` as a dependency is inside the test extra": exactly one
dependency-style `goga>=` entry in the whole file, located inside the
`[project.optional-dependencies]` table (between the table marker and the next
section `[tool.setuptools_scm]`). The project's own `name` and the
`include = ["goga_tool_simple_build*"]` line do not match the filter.

**Sufficiency**: guards the dependency policy against regression — a runtime `goga`
entry would violate the ecosystem contract (the tool runs inside a goga-provided
interpreter); a missing test-extra entry would leave the test environment without the
platform it exercises. Text-level check on purpose: `tomllib` is 3.11+ and the package
targets 3.10.

---

### Negative Tests

#### `test_build_presets_raises_on_authored_strategy_conflict`

**Setup** (parametrized over the authored conflicting values
`["thorough", "full", "medium"]`):
`amendment = StandinAmendment(config=StandinConfig(build=StandinBuild(review=StandinReview(strategy=param))))`.

**Input**: `build_presets(context=amendment)`

**Trace**:
```
build_presets(context=amendment)
  → strategy = param                 # present and != "short"
  → raise ValueError("authored value at build.review.strategy conflicts with the tool's purpose; remove the authored strategy or uninstall the tool")
    side effect: amendment.buffered stays []   # raise happens before any set
```

**Assertions**:
```
with pytest.raises(ValueError) as excinfo: build_presets(context=amendment)
"build.review.strategy" in str(excinfo.value)
param not in str(excinfo.value)          # output secrecy — value never named
amendment.buffered == []                 # nothing partial
```

**Sufficiency**: the single deliberate failure of the tool. Three regression anchors in
one scenario: the message names the path (the platform error must be actionable), the
message never names the value (the platform prints it verbatim — output secrecy is a
binding platform constraint), and the buffer stays empty (hard-action discard semantics
begin in the tool: raise precedes every write).

---

### Edge Case Tests

#### `test_build_presets_absent_intermediate_branches_read_as_absent`

**Setup** (parametrized over three absence shapes):
- `build=None` (no `build` branch),
- `build=StandinBuild(review=None)` (no `review` branch),
- `build=StandinBuild(review=StandinReview(strategy=None))` (leaf unset).

**Input**: `build_presets(context=amendment)` for each shape.

**Trace**:
```
build_presets(context=amendment)
  → traversal short-circuits at the absent level → strategy = None
  → guard passes → three set calls → returns None
```

**Assertions**:
```
no exception raised (no AttributeError on any absence shape)
amendment.buffered == [same three tuples]   for every parameter
```

**Sufficiency**: the acceptance criterion "a configuration with no `build` section at
all loads without any error attributable to the tool" starts here — the traversal must
degrade to absent on every level. A naive `context.config.build.review.strategy` chain
would crash exactly on the minimal configurations the tool exists to serve.

---

#### `test_build_presets_authored_empty_strategy_is_conflict`

**Setup**:
`amendment = StandinAmendment(config=StandinConfig(build=StandinBuild(review=StandinReview(strategy=""))))`.

**Input**: `build_presets(context=amendment)`

**Trace**:
```
build_presets(context=amendment)
  → strategy = ""              # stand-in-only shape: the loader maps "" to None,
  →                            # so a real authored file never delivers it
  → "" != "short" → raise ValueError (same message)
    side effect: amendment.buffered stays []
```

**Assertions**:
```
with pytest.raises(ValueError) as excinfo: build_presets(context=amendment)
"build.review.strategy" in str(excinfo.value)
amendment.buffered == []
```

**Sufficiency**: pins the no-normalization property of the tool itself. The loader
stores `build.review.strategy` by the agent-pattern strip rule (empty or
whitespace-only → `None`; non-empty → stripped), so `""` never reaches the hook
through a real authored file — the scenario is defense-in-depth: the tool must not
add its own trim or emptiness reinterpretation (trim in the tool would be value
interpretation and would silently diverge from the loader's own rule). Do not add
`"short "` as a conflict parameter: through the real platform it loads as `"short"`
and is not a conflict.

---

#### `test_build_presets_read_footprint_is_guard_leaf_only`

**Setup**: recording stand-ins — each level of the authored tree records attribute reads
(`__getattr__` appends the accessed name to a per-level list; dunder names are excluded
from recording and answered with `AttributeError`, mirroring the delivery proxy's dunder
rule — pytest's repr/isinstance machinery must not pollute the `.reads` lists); full
authored tree with `build.review.strategy = "thorough"` **and** extra neighboring leaves
present (`build.agent = "claude"`, `build.review.agent = "claude"`,
`build.review.additional = StandinAdditional(patience=4, max_iterations=9)`,
`pipeline = ...`, `topics = ...`).

**Input**: `pytest.raises(ValueError)` around `build_presets(context=amendment)` (the
conflict branch reads the same single chain as the quiet branch — one parameter shape
covering the guard read suffices).

**Trace**:
```
build_presets(context=amendment)
  → context.config            # the only read of the view itself
  → config.build              # recorded at config level
  → build.review              # recorded at build level
  → review.strategy           # recorded at review level
  → raise ValueError          # footprint already complete
```

**Assertions**:
```
config_level.reads == ["build"]
build_level.reads == ["review"]
review_level.reads == ["strategy"]     # never "agent", never "additional", never env
amendment.buffered == []
```

**Sufficiency**: turns the contract requirement "the only deliberate read of the
configuration is the single guard leaf" into an executable fact. Prevents the tool from
growing environment sniffing or agent validation — every such regression reads an extra
attribute and fails this test immediately.

---

## Additional Instructions for the Implementation Agent

- **Module layout** (the ADR-deferred decision, resolved here): both routines live in
  `goga_tool_simple_build/registration.py` (the contract's `location`); the facade
  `goga_tool_simple_build/__init__.py` re-exports them with the relative import
  `from .registration import build_presets, register_hooks` and
  `__all__ = ["build_presets", "register_hooks"]` (the `goga_tool_autonomous` pattern).
- **No runtime goga import**: `registration.py` starts with
  `from __future__ import annotations` and imports `HookRegistrar` (from
  `goga.hooks.tools.registration`) and `ConfigAmendment` (from
  `goga.config.hooks.amendments`) strictly under `if TYPE_CHECKING:`. The facade imports
  nothing from goga at all. Talk to the delivered objects structurally only.
- **Parameter shape**: keep `hooks` and `context` plain keyword-capable parameters — the
  platform calls the facade positionally and the hook by keyword projection.
- **Guard wording**: use the exact exception message fixed in the algorithm design;
  never interpolate any authored value into it or into any other string.
- **Ordering**: the raise precedes the first `set` — no partial contribution may ever
  exist.
- **Conventions compliance**: Google-style docstrings on both routines (with `Args` and
  `Raises` sections; no `Returns` — nothing is returned); one-blank-line logical block
  separation inside bodies; lowercase concise wording; `dependencies = []` untouched;
  add `goga>=2.0` to `[project.optional-dependencies].test` only.
- **Tests**: implement the scenarios above in `tests/` (root package modules → directly
  in `tests/`, with `tests/__init__.py`; no `conftest.py` beyond local fixtures);
  run `pytest tests/ -x` and `ruff check goga_tool_simple_build/` in a virtualenv
  created outside the project tree under `/opt/project`. The plan stage owns the final
  suite structure and any integration additions.
- **Out of scope reminders** (binding): no `force` amendments, no agent-presence or
  extra-leaf validation, no presets beyond the three review leaves, no CLI/`install`
  facade, no tool-own configuration (the values are constants), no runtime dependencies,
  no logging, no printing.
