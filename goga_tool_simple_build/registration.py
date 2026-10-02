"""Hook registration of the simple-build tool: the review-presets config hook."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from goga.config.hooks.amendments import ConfigAmendment
    from goga.hooks.tools.registration import HookRegistrar

_STRATEGY_CONFLICT_MESSAGE = (
    "authored value at build.review.strategy conflicts with the tool's purpose; "
    "remove the authored strategy or uninstall the tool"
)

_ITERATIONS_CONFLICT_MESSAGE = (
    "authored values at build.review.max_iterations and build.review.additional.max_iterations conflict; "
    "remove one of the authored iteration caps or uninstall the tool"
)


def register_hooks(hooks: HookRegistrar):
    """Subscribe the tool's single review-presets hook to the configuration amendment action.

    Args:
        hooks: platform registration surface delivered to the facade callback.
    """
    hooks.subscribe("config", "amend_config", "build_presets", build_presets)


def build_presets(context: ConfigAmendment):
    """Contribute the three simple-build review presets, map the review-level iteration cap, guard the conflicts.

    Args:
        context: read-and-amend view over the authored configuration.

    Raises:
        ValueError: the authored value at build.review.strategy conflicts with the tool's purpose.
        ValueError: both authored iteration caps are set — build.review.max_iterations and
            build.review.additional.max_iterations.
    """
    build = context.config.build

    review = build.review if build is not None else None
    strategy = review.strategy if review is not None else None

    if strategy is not None and strategy != "short":
        raise ValueError(_STRATEGY_CONFLICT_MESSAGE)

    review_iterations = review.max_iterations if review is not None else None

    additional = review.additional if review is not None else None
    additional_iterations = additional.max_iterations if additional is not None else None

    if review_iterations is not None and additional_iterations is not None:
        raise ValueError(_ITERATIONS_CONFLICT_MESSAGE)

    external_iterations = 3 if review_iterations is None else review_iterations

    context.set("build.review.strategy", "short")
    context.set("build.review.additional.patience", 1)
    context.set("build.review.additional.max_iterations", external_iterations)
