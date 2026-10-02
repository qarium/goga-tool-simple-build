# Simple Build Review Presets — `goga-tool-simple-build`

## Problem

Goga users who want a simple build with a minimal, token-efficient review pass
must hand-tune the review knobs (review strategy, external-review patience and
iteration cap) in `.goga/config.yml`. Tuning them correctly requires
understanding the review-loop mechanics — how strategies, review rounds, and
the external review cycle interact and consume tokens. Without that expertise
the author is left with the built-in defaults (a `medium` strategy and an
unbounded external review), which run a heavier review process and spend more
tokens than a simple build needs.

The outcome currently prevented: a cheap, minimal review pass achievable
without expert knowledge of the review algorithms — and without re-deriving
the right knob values in every project.

## Users

**Primary user — the goga project maintainer.** A developer who installs goga
tool packages and runs `goga build` in their project. They write (or copy) a
minimal `.goga/config.yml` — typically `language` plus agent names — and do not
know the review tuning knobs exist or what they mean. What matters to them:
token economy of the review pass, simplicity of setup, predictable build
behavior. If they cannot get a cheap review pass effortlessly, they either
overspend tokens or skip review entirely.

**Secondary actor — the explicit tuner.** A project author who deliberately
writes review knobs in a project where the tool is installed. Their
expectation: authored values win; the tool may only fill what they left
unsaid; whatever the tool applied is visible in the run summary.

## Goals

1. **Token-efficient minimal review by default.** In any project with the tool
   installed, the review pass of `goga build` takes its lightweight form — a
   short review strategy with a bounded external review (limited patience and
   iteration cap) — without the author writing a single knob.
2. **Effortless correct setup.** The maintainer of a simple build gets the
   tuned review configuration without learning review-cycle mechanics: nothing
   to learn, nothing to write, nothing to repeat per project.
3. **Authored control preserved and transparent.** Any review knob the project
   author writes explicitly wins over the preset — except an authored review
   strategy other than `short`, which the tool surfaces as a loud conflict
   rather than silently standing aside. What the tool applied is visible in
   the run summary, so behavior stays predictable and explainable.

## User Experience

**Entry point.** The user installs the `goga-tool-simple-build` package into
their environment (project tool declaration or container image). From then on
the presets live in every goga run of that project — there is no command to
run, no question to answer, no file to edit for the tool's part.

**Primary scenario.** A project has a minimal authored `.goga/config.yml`
(e.g. `language` plus `build.agent`) with no review knobs. The user runs any
config-consuming goga command — `goga build` in particular. At the
configuration load moment the tool's presets apply where the author was
silent: the review strategy becomes `short`, and the external review becomes
bounded (patience `2`, iteration cap `5`). The run prints a short summary to
stderr naming the tool and each applied amendment (path, `set`). The review
pass then runs in its lightweight bounded form, spending fewer tokens. The
authored `.goga/config.yml` is never modified — it stays byte-identical, and
repeated runs reproduce the same effective configuration.

**Alternative scenario — explicit tuning.** The author writes `patience`
and/or `max_iterations` explicitly — or writes `strategy: short`, agreeing
with the preset. The authored values win; the tool's presets for those leaves
are dropped silently — no warning, no error — while the remaining silent
leaves still receive their presets. The summary lists only the amendments
actually applied.

**Alternative scenario — strategy conflict.** The author writes
`build.review.strategy` with a value other than `short`. The tool treats this
as a conflict with its purpose: the hosting command stops with a clean error
naming the tool, the action, and the path `build.review.strategy` (never the
authored value); the tool's whole contribution is discarded and the authored
file stays byte-identical. Removing the authored strategy or uninstalling the
tool resolves the conflict.

**Failure behavior.** The tool contributes through a hard platform action: if
the tool were to fail, the hosting command would stop with a clean error
naming the tool and the action, and the tool's whole contribution would be
discarded — nothing partial applies. The tool has exactly one deliberate
failure condition: an authored review strategy other than `short` conflicts
with the tool's purpose and stops the command (naming the path, never the
value). Outside that conflict the tool adds no failure of its own: the
presets are fixed values at known configuration paths, valid for any authored
configuration. A broken package import is the single remaining fatal case and
surfaces as a clean error naming the package.

**Consequences and reversibility.** Nothing is persisted anywhere: the presets
exist only in the effective in-memory configuration of each run. Removing the
tool from the environment returns the project to exactly its authored
behavior. Configuring or deconfiguring agents remains entirely the goga
platform's business — the tool never validates agent presence and never
touches agent values.

## Requirements

**R1 — Preset application.** When the tool is installed in a project and any
config-consuming goga surface loads `.goga/config.yml` (the host-side commands
— build, pipeline, lint, contract, install, config, topics, usages status,
usages sync — and the in-container entrypoints), the tool must apply exactly
these three presets, each only where the authored configuration is silent at
the path (absence markers `None`, `{}`, `[]`):

- `build.review.strategy` = `short`
- `build.review.additional.patience` = `2`
- `build.review.additional.max_iterations` = `5`

Absent intermediate branches (`build.review`, `build.review.additional`) must
materialize as part of the amendment.

**R2 — Authored-wins.** The presets must never override authored values. A
path where the authored configuration is not silent keeps the authored value;
the dropped preset produces no warning and no error. Authored emptiness
(`False`, `""`) counts as authored, not silent. The single exception is an
authored `build.review.strategy` other than `short` — a conflict the tool
reports as an error (R10) instead of dropping its preset silently.

**R3 — No agent validation.** The tool must not validate the presence of
`build.review.agent`, `build.agent`, or any other agent, and must not fail on
minimal configurations. The missing-agent error belongs to the goga platform
(agent value guard and agent inheritance: `build.review.agent` inherits
`build.agent`; `additional.agent` inherits `review.agent`).

**R4 — Transparency.** When presets apply, the run must show the platform's
amendment summary to stderr — the tool, and one line per applied amendment
(path, `set`). Configuration values must never appear in any informational
output. When nothing is applied, nothing is printed.

**R5 — File integrity.** The authored `.goga/config.yml` must remain
byte-identical after every run; the presets exist only in the effective
configuration of the run.

**R6 — Determinism.** The same installed tool set and the same authored file
must always produce the same effective configuration, run after run.

**R7 — All-or-nothing contribution.** The tool's contribution commits as a
unit under the platform's hard-action semantics. The tool's single deliberate
failure condition is the strategy conflict (R10); beyond it the tool
introduces no failure modes of its own: the presets are fixed constants
addressed at configuration-model leaf paths and must be well-formed for every
valid authored configuration.

**R8 — Exact footprint.** The tool touches exactly the three leaf paths of
R1 and nothing else — no other configuration paths, no tasks-pass settings,
no environment values.

**R9 — Clean uninstall.** With the tool removed from the environment, the
effective configuration equals the authored configuration exactly.

**R10 — Strategy conflict failure.** When the authored configuration sets
`build.review.strategy` to a value other than `short`, the tool must stop the
hosting command with a clean error naming the tool, the action, and the path
`build.review.strategy` — never the authored value. The tool's whole
contribution is discarded; nothing partial applies. An authored `short` is
not a conflict: the authored value stands and the preset is dropped silently
(R2).

## Constraints

1. **Extension mechanism only.** All behavior must be delivered through the
   goga tool-package facade subscribing to the existing `config` domain
   action (`config / amend_config`). No goga core changes, no new domain
   actions, no changes to merge rules or output format.
2. **Hook contract.** The hook receives only the parameters it declares by
   the fixed offered names; the delivered configuration is read-only;
   amendments go only through the amendment buffer. The product uses
   apply-where-silent amendments; it never uses override amendments.
3. **Hard-action semantics.** The action's error class is fixed by the
   domain: a failing tool hook stops the hosting command with a clean error
   naming the tool and the action; contributions commit as a unit; the
   contribution of one tool is discarded on its failure. The tool's only
   deliberate failure is the strategy conflict (R10).
4. **Platform merge rules.** Authored-wins by default; an override amendment
   from any other tool beats a silent-set amendment regardless of order;
   among equal intents the later tool in enumeration order wins. The tool
   cannot and must not fight other tools for a path.
5. **No persistence.** The authored configuration file is never written; the
   effective amended configuration exists only within the run.
6. **Output secrecy.** Configuration values (including environment values)
   are never printed by the platform; the summary format is fixed (tool,
   path, set/forced).
7. **Tool identity.** The tool's identity is derived by goga from the package
   name (`goga-tool-simple-build`); the package never names itself, and hook
   names are unique per tool per address.
8. **Import-clean facade.** The package facade must import without side
   effects and without failure — a broken import is the single fatal case
   that stops hosting commands. The package carries no runtime dependencies.
9. **Platform version.** The tool targets the goga 2.0.x hooks platform
   (the `config / amend_config` action with `set`/`force` amendment
   semantics), which the project's usage documentation is pinned to.
10. **Agent inheritance is consumer-owned.** Agent resolution and
    inheritance semantics belong to the goga consumers; the tool must not
    interfere with them in any way.

## Scope

### In Scope

- The installable `goga-tool-simple-build` tool package with an import-clean
  facade that registers its configuration-amendment subscription.
- The three fixed review presets (R1) with authored-wins semantics (R2),
  delivered at the configuration load moment of every config-consuming
  surface.
- The behavior observable through the platform: amendment summary (R4),
  effective configuration values (R6), file integrity (R5), clean uninstall
  (R9).

### Out of Scope

- Any validation of agent presence (`build.review.agent`, `build.agent`,
  `additional.agent`) — explicitly dropped: platform inheritance and the
  agent value guard already own the missing-agent error.
- Override (`force`) behavior of any kind — the presets never overwrite
  authored values.
- Any authored-value validation beyond the strategy conflict (R10) — no
  validation of `patience`, `max_iterations`, or any other leaf.
- Any presets or defaults beyond the three review leaves — no tasks-pass
  settings (agent, env, iteration caps, session timeouts, prompts/agents
  dirs, proxy, hosts), no review roles, base_ref, finalize, or other leaves.
- Changes to goga core, new domain actions, changes to merge rules, summary
  format, or output behavior.
- Tool-own configuration (e.g. a `.goga/tools/simple_build/` config file
  making the presets user-tunable) — the preset values are fixed constants.
- Subscriptions to any other domain action (the build validation gate, build
  notifications, statuses, and similar).
- An own CLI (`main` facade) — the tool is hook-only and has no commands.

## Success Criteria

1. In a project with a minimal authored configuration (only `language` and a
   build agent) and the tool installed, running any config-consuming goga
   command yields an effective configuration with
   `build.review.strategy == "short"`,
   `build.review.additional.patience == 2`, and
   `build.review.additional.max_iterations == 5`, while the authored
   `.goga/config.yml` remains byte-identical.
2. In a project where the author explicitly set `patience` and/or
   `max_iterations` (or set `strategy: short`), the authored values survive
   unchanged, the corresponding presets are dropped without any warning or
   error, and the remaining silent leaves still receive their presets.
3. The run output shows the amendment summary naming the tool and each
   applied path with `set`; no configuration values appear in the output;
   when nothing is applied, nothing is printed.
4. `goga config` reports the effective (amended) review values matching the
   target configuration:
   `strategy: short`, `additional: {patience: 2, max_iterations: 5}`.
5. Repeated runs of the same command in the same project produce the
   identical effective configuration.
6. A configuration with no review agent — and even no build section content
   beyond the presets — loads and runs without any error attributable to the
   tool in all non-build commands; the tool adds no failure modes.
7. After removing the tool from the environment, the effective configuration
   equals the authored configuration exactly.
8. In a project where the author explicitly set `build.review.strategy` to a
   value other than `short`, every config-consuming goga command stops with a
   clean error naming the tool, the action, and the path
   `build.review.strategy` — the authored value never appears in the output,
   no amendment is applied, and the authored `.goga/config.yml` stays
   byte-identical.
