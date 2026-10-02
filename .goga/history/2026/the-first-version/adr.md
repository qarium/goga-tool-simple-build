# One hard-action config subscription with a strategy-conflict guard

The tool delivers its three review presets through exactly one hard-action
subscription to `config / amend_config` (hook name `build_presets`): the hook
buffers three unconditional `set` amendments — `build.review.strategy =
short`, `build.review.additional.patience = 2`,
`build.review.additional.max_iterations = 5` — and reads the authored
configuration at exactly one leaf, `build.review.strategy`, solely to detect
a conflict: an authored value other than `short` raises, stopping the hosting
command with a value-free error naming the tool, the action, and the path.
Authored-wins for every other leaf is owned by the platform merge layer, not
by the tool.

## Considered options

Rejected:

- **Three per-path hooks** — the order between hooks of one tool is not part
  of the tool's contract, and one contribution split across three
  registrations adds failure points and names for no benefit.
- **Per-leaf conditional logic around the `set`s** — duplicates the merge
  layer, which already drops a `set` on any non-silent path silently; reading
  the configuration to re-derive that only adds branching and failure
  surface.
- **Extending the conflict check to `patience` / `max_iterations`** — those
  are bounds within whatever review runs; authoring them differently is
  tuning, not a conflict with the tool's purpose. Only the review strategy
  carries that purpose.
- **Quoting the authored value in the conflict error** — the platform prints
  the hook's exception message verbatim, and configuration values must never
  appear in command output; the error names the path, never the value.

## Consequences

- The tool has exactly one deliberate failure condition (the strategy
  conflict); a broken package import remains the only other fatal case, both
  surfacing as clean errors that discard the tool's whole contribution.
- Determinism is trivial: outside the conflict check the contribution is a
  constant, so the same tool set and authored file always produce the same
  effective configuration.

## Open questions

Owned by later pipeline stages, deliberately undecided here:

- **Package module layout** — everything in the facade `__init__.py` versus a
  facade re-exporting a registration module (the `goga_tool_autonomous`
  pattern). A `location`/boundary decision for design and prototype.
- **Test approach** — unit tests of the hook against a stand-in amendment
  view versus integration through `goga config`. A decision for the plan
  stage.
