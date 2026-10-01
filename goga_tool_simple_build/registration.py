"""Hook registration of the simple-build tool: the review-presets config hook."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from goga.config.hooks.amendments import ConfigAmendment
    from goga.hooks.tools.registration import HookRegistrar

_CONFLICT_MESSAGE = (
    "authored value at build.review.strategy conflicts with the tool's purpose; "
    "remove the authored strategy or uninstall the tool"
)


def register_hooks(hooks: HookRegistrar):
    """Subscribe the tool's single review-presets hook to the configuration amendment action.

    Args:
        hooks: platform registration surface delivered to the facade callback.
    """
    hooks.subscribe("config", "amend_config", "build_presets", build_presets)


def build_presets(context: ConfigAmendment):
    """Contribute the three simple-build review presets and guard the strategy conflict.

    Args:
        context: read-and-amend view over the authored configuration.

    Raises:
        ValueError: the authored value at build.review.strategy conflicts with the tool's purpose.
    """
    build = context.config.build

    review = build.review if build is not None else None
    strategy = review.strategy if review is not None else None

    if strategy is not None and strategy != "short":
        raise ValueError(_CONFLICT_MESSAGE)

    context.set("build.review.strategy", "short")
    context.set("build.review.additional.patience", 1)
    context.set("build.review.additional.max_iterations", 3)
