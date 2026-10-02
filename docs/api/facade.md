# Package facade

The `goga_tool_simple_build` cell — the platform subscription and the single API surface of
the tool. The facade must stay import-clean: a broken import is fatal to every goga command.

## Platform subscription

```python
from goga_tool_simple_build import register_hooks

register_hooks(hooks)  # goga calls this when a command first reaches a hook checkpoint
```

The registration subscribes exactly one hook: address `config` / `amend_config`, name
`build_presets`. No CLI entry, no install lifecycle, no runtime import of goga — the platform
types are referenced under `TYPE_CHECKING` only.

### `register_hooks(hooks: HookRegistrar)`

Subscribe the tool's single review-presets hook to the configuration amendment action.

- `hooks`: the goga subscription surface delivered at registration — exposes
  `subscribe(domain, action, name, hook)`
- Subscribes the hook routine `build_presets` under domain `config`, action `amend_config`,
  hook name `build_presets` — exactly one subscription, unconditional
- Hook name stays unique per tool per address; no configuration or file reads during
  registration; subscribes to no other domain action

### `build_presets(context: ConfigAmendment)`

The amendment hook — contribute the three simple-build review presets, map the review-level
iteration cap, and guard the two conflicts.

- `context`: the per-tool read-and-amend view over the authored configuration

Algorithm:

1. Read the authored leaf `build.review.strategy` from the configuration of `context`; absent
   branches read as absent
2. If the authored value is present and is not `short` — raise an exception whose message
   names the path `build.review.strategy` and never the authored value
3. Read the authored leaves `build.review.max_iterations` and
   `build.review.additional.max_iterations`; absent branches read as absent
4. If both iteration-cap leaves are present — raise an exception whose message names the two
   paths and never the authored values
5. Buffer three apply-where-silent amendments through `context`: `build.review.strategy` set
   to `short`, `build.review.additional.patience` set to `1`,
   `build.review.additional.max_iterations` set to the authored
   `build.review.max_iterations` when present, otherwise to `3`

The amendments are unconditional — the deliberate reads of the configuration are the guard
leaf of step 1 and the two iteration-cap leaves of step 3. Authored-wins is owned by the
merge layer and is never re-derived here. The exact write footprint is the three leaf paths
of step 5 and nothing else: no other configuration paths, no tasks-pass settings, no
environment values. The hook never validates agent presence and never uses the override form
of amendment — the presets never overwrite authored values. Configuration values are never
printed or embedded in any output or error message.

## The presets

| Path | Value |
|---|---|
| `build.review.strategy` | `short` |
| `build.review.additional.patience` | `1` |
| `build.review.additional.max_iterations` | `3` — or the authored `build.review.max_iterations` |

The first two values are fixed constants; the iteration cap defaults to `3` and follows the
authored `build.review.max_iterations` when the project sets it. Beyond that mapping there is
no tool-own configuration to tune the presets with. What an installed tool guarantees in
practice is documented in [Review presets](../review-presets.md).

## Preconditions and side effects

- The hook is a pure function of the delivered context: no state, no cache, no clock or
  environment reads; identical facts produce the identical contribution.
- No project file is ever created or modified; the presets exist only in the effective
  in-memory configuration of each run — the authored `.goga/config.yml` stays
  byte-identical.
- Failures surface as clean command errors through the hard action; the tool's whole
  contribution is discarded — nothing partial applies. The deliberate failures are the
  strategy conflict and the iteration-cap conflict; a broken package import is the single
  remaining fatal case.
