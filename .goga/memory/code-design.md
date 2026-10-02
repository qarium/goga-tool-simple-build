# Project rules

## Layer-faithful value semantics

Semantic rules about a value (such as whether emptiness counts as intentionally authored or as absent) apply only to the representation a downstream consumer actually receives. First establish what the loading layer delivers for a given leaf, then apply the rule to that loaded shape; and keep normalization in exactly one layer — downstream consumers must not re-trim or reinterpret values that upstream loading has already normalized.

## Executable assertion pinning

Every assertion in a design document or test scenario must be pinned as an exact executable check — precise substring, occurrence-count, and ordered-position conditions — rather than a statement of intent, and never as a naive containment test that also matches unrelated occurrences in the same content.

## Explicit deviation recording

Any deliberate deviation from a mandatory usage convention must be recorded explicitly in the scenario itself, together with the reason the deviation preserves the scenario's meaning, so that later stages cannot "conform to conventions" and turn the scenario into an empty check.

## Dunder hygiene in recording stand-ins

A test stand-in that captures attribute access through dynamic-lookup interception must answer dunder lookups with an error rather than recording them, so that captured read footprints contain only business reads and strict-equality assertions on those footprints remain stable.
