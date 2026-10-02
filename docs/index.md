# goga-tool-simple-build

A [goga](https://pypi.org/project/goga/) hook tool that gives simple builds a cheap, minimal
review pass by default: the short review strategy plus a bounded external review, applied
wherever the project author left the review knobs unwritten.

## How it works

The package registers exactly one hook — `build_presets` on the `config / amend_config`
action. At the configuration load moment the hook contributes three apply-where-silent
amendments:

- `build.review.strategy` set to `short` — the lightweight review form;
- `build.review.additional.patience` set to `1`;
- `build.review.additional.max_iterations` set to `3` — together bounding the external
  review.

Each preset applies only where the authored configuration is silent at the path. Authored-wins
is owned by the platform merge layer: the presets never overwrite authored values, a project
that already encodes its review budget keeps it, and nothing is persisted — the authored
`.goga/config.yml` stays byte-identical, and removing the tool returns the project to exactly
its authored behavior.

The only deliberate read of the authored configuration is the conflict guard: an authored
`build.review.strategy` other than `short` conflicts with the tool's purpose and stops the
hosting command with a clean error naming the path — never the authored value. Removing the
authored strategy or uninstalling the tool resolves the conflict.

## Installation

The tool has no runtime dependencies by design — the platform types are referenced under
`TYPE_CHECKING` only, so the package facade stays import-clean with or without goga installed.
The tool is installed into the project's goga docker image — the environment goga commands
run in.

### Declare it as a project dependency

Add the tool to the project's `.goga/config.yml`:

```yaml
tools:
  simple-build: latest
```

A plain `goga install` during the image build then resolves it together with the rest of the
project's declared tools:

```dockerfile
FROM <goga-base-image>

USER root

COPY . /tmp/project
RUN cd /tmp/project && goga install && rm -rf /tmp/project

USER goga
```

### Install it by name

Install the tool by name during the image build:

```dockerfile
FROM <goga-base-image>

USER root

COPY . /tmp/project
RUN cd /tmp/project && goga install simple-build && rm -rf /tmp/project

USER goga
```

## Documentation

- [Review presets](review-presets.md) — what an installed tool guarantees: the presets table,
  authored-wins, and the one deliberate conflict
- [Architecture](architecture.md) — the cell map and the amendment data flow
- [API reference](api/facade.md) — the package facade contract

## Development

The project venv lives outside the repository at `/opt/goga/project`:

```bash
/opt/goga/project/bin/pip install -e '.[test]'
/opt/goga/project/bin/python -m pytest tests/
/opt/goga/project/bin/ruff check goga_tool_simple_build/ tests/
/opt/goga/project/bin/ruff format --exclude '.usages' goga_tool_simple_build/ tests/
```

The `test` extra carries the platform (`goga>=2.0`, unpinned) and the test stack; the unpinned
platform is deliberate — a platform release that changes the amendment surface must surface
as test failures, not silent drift.

`CODEMANIFEST` and `.usages/` files are read-only contracts: when implementation and contract
disagree, the implementation is what gets fixed.
