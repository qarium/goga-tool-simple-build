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
| `build.review.additional.max_iterations` | `3` — or the authored `build.review.max_iterations` |

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

Check the effective values after a run with `goga config` — it prints the amended
values; the run also prints a short amendment summary to stderr naming the tool
and each applied path.

## Authoring your own values

Any review knob written explicitly wins. Author `patience` or
`build.review.additional.max_iterations` (or `strategy: short`) and the tool stays
silent for those leaves — no warning, no error — while the remaining silent leaves
still receive their presets:

```yaml
build:
  review:
    additional:
      patience: 4   # authored — wins over the preset 1
```

Effective: `strategy: short`, `patience: 4`, `max_iterations: 3`.

### Mapping the review-level iteration cap

The external review cap also follows the review-level knob: an authored
`build.review.max_iterations` maps into `build.review.additional.max_iterations`
wherever the latter is silent:

```yaml
build:
  review:
    max_iterations: 7   # authored — maps into the external review cap
```

Effective: `strategy: short`, `patience: 1`, `max_iterations: 7` — both review
loops share the authored cap. The mapping is a preset, not an override: a
directly authored `build.review.additional.max_iterations` would still win,
except that authoring both caps at once is a conflict (below).

## The deliberate conflicts

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

Authoring both `build.review.max_iterations` and
`build.review.additional.max_iterations` is a settings conflict — two competing
iteration caps for the same review. The command stops the same way: the error
names both paths and never the values. Keep the review-level cap to feed the
mapping, or the additional one to pin the external cap directly, or uninstall
the tool:

```yaml
build:
  review:
    max_iterations: 7          # conflict together with the line below —
    additional:
      max_iterations: 15       # every goga command stops
```

## Side effects and reversibility

- The authored `.goga/config.yml` is never modified — it stays byte-identical;
  the presets live only in the effective in-memory configuration of each run.
- Repeated runs reproduce the same effective configuration.
- Removing the tool from the environment returns the project to exactly its
  authored behavior.
- The tool never validates agent presence and never touches agent values — a
  configuration with no review agent loads without any error from the tool.
