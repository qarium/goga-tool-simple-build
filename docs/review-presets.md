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
| `build.review.additional.patience` | `1` |
| `build.review.additional.max_iterations` | `3` |

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
      patience: 1
      max_iterations: 3
```

## Seeing what was applied

Every run that applies presets prints the platform's amendment summary to stderr —
the tool name and one line per applied amendment (path, `set`). With a minimal
configuration:

```text
config amendments: 3 applied
- simple-build set build.review.strategy
- simple-build set build.review.additional.patience
- simple-build set build.review.additional.max_iterations
```

Check the effective values after a run with `goga config` — it prints the amended
values. When nothing is applied (every leaf already authored), nothing is printed.
Configuration values never appear in any informational output.

## Authoring your own values

Any review knob written explicitly wins. Author `patience` or `max_iterations`
(or `strategy: short`) and the tool stays silent for those leaves — no warning,
no error — while the remaining silent leaves still receive their presets:

```yaml
build:
  review:
    additional:
      patience: 4   # authored — wins over the preset 1
```

Effective: `strategy: short`, `patience: 4`, `max_iterations: 3`.

## The one deliberate conflict

Authoring `build.review.strategy` with a value other than `short` conflicts with
the tool's purpose. Every config-consuming goga command stops with a clean error
naming the tool, the action, and the path `build.review.strategy` — the authored
value is never printed, nothing is applied:

```text
hook build_presets of tool simple-build failed on config.amend_config
```

```yaml
build:
  review:
    strategy: thorough   # conflict — every goga command stops
```

An authored empty strategy (`""`) is a conflict too — it is authored, not silent,
and the tool never normalizes authored values. Remove the authored strategy or
uninstall the tool to resolve the conflict.

## Side effects and reversibility

- The authored `.goga/config.yml` is never modified — it stays byte-identical;
  the presets live only in the effective in-memory configuration of each run.
- Repeated runs reproduce the same effective configuration.
- Removing the tool from the environment returns the project to exactly its
  authored behavior.
- The tool never validates agent presence and never touches agent values — a
  configuration with no review agent loads without any error from the tool.

The contract behind these guarantees is documented in the
[API reference](api/facade.md).
