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

The amendment hook — contribute the three simple-build review presets and guard the strategy
conflict.

- `context`: the per-tool read-and-amend view over the authored configuration

Algorithm:

1. Read the authored leaf `build.review.strategy` from the configuration of `context`; absent
   branches read as absent
2. If the authored value is present and is not `short` — raise an exception whose message
   names the path `build.review.strategy` and never the authored value
3. Buffer three apply-where-silent amendments through `context`: `build.review.strategy` set
   to `short`, `build.review.additional.patience` set to `1`,
   `build.review.additional.max_iterations` set to `3`

The amendments are unconditional — the only deliberate read of the configuration is the
single guard leaf of step 1. Authored-wins is owned by the merge layer and is never
re-derived here. The exact write footprint is the three leaf paths of step 3 and nothing
else: no other configuration paths, no tasks-pass settings, no environment values. The hook
never validates agent presence and never uses the override form of amendment — the presets
never overwrite authored values. Configuration values are never printed or embedded in any
output or error message.

## The presets

| Path | Value |
|---|---|
| `build.review.strategy` | `short` |
| `build.review.additional.patience` | `1` |
| `build.review.additional.max_iterations` | `3` |

The values are fixed constants — there is no tool-own configuration to tune them with. What
an installed tool guarantees in practice is documented in
[Review presets](../review-presets.md).

## Preconditions and side effects

- The hook is a pure function of the delivered context: no state, no cache, no clock or
  environment reads; identical facts produce the identical contribution.
- No project file is ever created or modified; the presets exist only in the effective
  in-memory configuration of each run — the authored `.goga/config.yml` stays
  byte-identical.
- Failures surface as clean command errors through the hard action; the tool's whole
  contribution is discarded — nothing partial applies. The single deliberate failure is the
  strategy conflict; a broken package import is the single remaining fatal case.
