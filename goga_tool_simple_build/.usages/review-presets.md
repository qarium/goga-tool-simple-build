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
