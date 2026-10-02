# Project rules

## Minimal facade with dedicated implementation module

The package entry point stays a thin re-export surface while actual routines live in a separate implementation module, and the test tree mirrors that module layout; the structure follows the ecosystem's established reference pattern instead of consolidating code into the entry point to save a file.

## Cohesion-bounded cell granularity

A contract cell maps to a single cohesive package directory; functionalities that exist only together remain in one cell, splitting beyond that cohesion is avoided, and in a greenfield schema the boundary is fixed at package granularity from the start.

## Optional host-platform coupling

References to host-platform types appear only in statically-guarded type annotations, the platform is declared solely as a test/development dependency, the package carries no runtime dependency on it and imports cleanly whether or not the platform is installed, and platform types are never declared as imports provided by project cells.

## Platform semantics ownership boundary

Contributions are made exclusively through declarative subscriptions with unconditional silent-set semantics; every concern owned by the host platform — merging, precedence, reporting, secrecy, integrity, determinism — is consumed as-is and never re-implemented in the tool, and destructive override of authored values is never attempted.

## Fail-stop secrecy on authored conflict

When an authored configuration value conflicts with the tool's purpose, every consuming command halts via an exception that names the actor, the action, and the configuration path but never the authored value; nothing is applied, so the authored file remains byte-identical.

## Contract-scoped planning artifacts

Architecture plans embed only contract artifacts — full specification text and full usage documentation — plus implementation order, a dependency map, and a verification checklist; implementation code and materialization of cell artifacts are explicitly deferred to later pipeline stages.

## Blocking-decision-first sequencing

Open structural decisions that downstream work depends on are resolved before that work begins, presented as explicit either/or questions with a recommendation, rather than proceeding on placeholders that force rework of dependent detailing.
