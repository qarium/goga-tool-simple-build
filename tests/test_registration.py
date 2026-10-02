"""Unit tests of the review-presets hook registration (contract and logic scenarios)."""

from collections.abc import Callable

import pytest
from goga_tool_simple_build import registration

EXPECTED_PRESETS = [
    ("build.review.strategy", "short"),
    ("build.review.additional.patience", 1),
    ("build.review.additional.max_iterations", 3),
]


class StandinRegistrar:
    """Stand-in of the platform hook registrar recording subscribe envelopes."""

    def __init__(self) -> None:
        self.records: list[tuple] = []

    def subscribe(self, domain: str, action: str, name: str, hook: Callable) -> None:
        """Record one subscribe call as a (domain, action, name, hook) tuple."""
        self.records.append((domain, action, name, hook))


class StandinAmendment:
    """Stand-in of the platform config amendment view buffering set calls."""

    def __init__(self, config) -> None:
        self.config = config
        self.buffered: list[tuple] = []

    def set(self, path: str, value) -> None:
        """Buffer one apply-where-silent amendment as a (path, value) tuple."""
        self.buffered.append((path, value))


class StandinAdditional:
    """Stand-in of the authored review additional settings."""

    def __init__(self, patience: int | None = None, max_iterations: int | None = None) -> None:
        self.patience = patience
        self.max_iterations = max_iterations


class StandinReview:
    """Stand-in of the authored review settings with None-able branches."""

    def __init__(
        self,
        strategy: str | None = None,
        max_iterations: int | None = None,
        additional: StandinAdditional | None = None,
    ) -> None:
        self.strategy = strategy
        self.max_iterations = max_iterations
        self.additional = additional


class StandinBuild:
    """Stand-in of the authored build settings with a None-able review branch."""

    def __init__(self, review: StandinReview | None = None) -> None:
        self.review = review


class StandinConfig:
    """Stand-in of the authored configuration snapshot with a None-able build branch."""

    def __init__(self, build: StandinBuild | None = None) -> None:
        self.build = build


class RecordingLevel:
    """Authored-tree level recording every non-dunder attribute read it serves."""

    def __init__(self, children: dict[str, object]) -> None:
        self.reads: list[str] = []
        self._children = children

    def __getattr__(self, name: str):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)

        self.reads.append(name)

        if name in self._children:
            return self._children[name]

        raise AttributeError(name)


def test_register_hooks_subscribes_single_review_hook():
    """Subscribes exactly the build_presets hook to the config amend_config address."""
    registrar = StandinRegistrar()

    result = registration.register_hooks(hooks=registrar)

    assert result is None
    assert len(registrar.records) == 1
    assert registrar.records[0][:3] == ("config", "amend_config", "build_presets")
    assert registrar.records[0][3] is registration.build_presets


def test_build_presets_buffers_three_presets_when_branches_absent():
    """Buffers the three exact presets when no build branch exists at all."""
    amendment = StandinAmendment(config=StandinConfig(build=None))

    result = registration.build_presets(context=amendment)

    assert result is None
    assert amendment.buffered == EXPECTED_PRESETS


def test_build_presets_buffers_presets_when_strategy_authored_short():
    """Buffers all three presets even when strategy is already authored short."""
    config = StandinConfig(build=StandinBuild(review=StandinReview(strategy="short")))
    amendment = StandinAmendment(config=config)

    registration.build_presets(context=amendment)

    assert amendment.buffered == EXPECTED_PRESETS


@pytest.mark.parametrize("authored_strategy", ["thorough", "full", "medium"])
def test_build_presets_raises_on_authored_strategy_conflict(authored_strategy):
    """Raises ValueError naming the path, never the value, before any set call."""
    config = StandinConfig(build=StandinBuild(review=StandinReview(strategy=authored_strategy)))
    amendment = StandinAmendment(config=config)

    with pytest.raises(ValueError, match=r"build\.review\.strategy") as excinfo:
        registration.build_presets(context=amendment)

    assert "build.review.strategy" in str(excinfo.value)
    assert authored_strategy not in str(excinfo.value)
    assert amendment.buffered == []


@pytest.mark.parametrize(
    "build",
    [
        None,
        StandinBuild(review=None),
        StandinBuild(review=StandinReview(strategy=None)),
    ],
)
def test_build_presets_absent_intermediate_branches_read_as_absent(build):
    """Reads every absent intermediate branch as absent and still buffers the presets."""
    amendment = StandinAmendment(config=StandinConfig(build=build))

    registration.build_presets(context=amendment)

    assert amendment.buffered == EXPECTED_PRESETS


def test_build_presets_authored_empty_strategy_is_conflict():
    """Treats an authored empty strategy as a conflict without any tool-side normalization."""
    config = StandinConfig(build=StandinBuild(review=StandinReview(strategy="")))
    amendment = StandinAmendment(config=config)

    with pytest.raises(ValueError, match=r"build\.review\.strategy") as excinfo:
        registration.build_presets(context=amendment)

    assert "build.review.strategy" in str(excinfo.value)
    assert amendment.buffered == []


@pytest.mark.parametrize("authored_iterations", [7, 0, -1, 999])
def test_build_presets_maps_authored_review_iterations_into_external_cap(authored_iterations):
    """Maps the authored review-level iteration cap verbatim into the third preset."""
    review = StandinReview(max_iterations=authored_iterations)
    amendment = StandinAmendment(config=StandinConfig(build=StandinBuild(review=review)))

    registration.build_presets(context=amendment)

    assert amendment.buffered == [
        ("build.review.strategy", "short"),
        ("build.review.additional.patience", 1),
        ("build.review.additional.max_iterations", authored_iterations),
    ]


def test_build_presets_maps_review_iterations_with_silent_additional_leaf():
    """Maps the review-level cap when the additional branch exists but its leaf is silent."""
    review = StandinReview(
        max_iterations=7,
        additional=StandinAdditional(patience=None, max_iterations=None),
    )
    amendment = StandinAmendment(config=StandinConfig(build=StandinBuild(review=review)))

    registration.build_presets(context=amendment)

    assert ("build.review.additional.max_iterations", 7) in amendment.buffered


def test_build_presets_keeps_default_cap_when_only_additional_authored():
    """Keeps the default cap 3 in the buffer when only the additional leaf is authored."""
    review = StandinReview(additional=StandinAdditional(patience=None, max_iterations=9))
    amendment = StandinAmendment(config=StandinConfig(build=StandinBuild(review=review)))

    registration.build_presets(context=amendment)

    assert ("build.review.additional.max_iterations", 3) in amendment.buffered


@pytest.mark.parametrize(
    ("review_iterations", "additional_iterations"),
    [(7, 15), (0, 15), (7, 0), (-1, 1)],
)
def test_build_presets_raises_when_both_iteration_caps_authored(review_iterations, additional_iterations):
    """Raises ValueError naming both paths, never the values, before any set call."""
    review = StandinReview(
        max_iterations=review_iterations,
        additional=StandinAdditional(patience=4, max_iterations=additional_iterations),
    )
    amendment = StandinAmendment(config=StandinConfig(build=StandinBuild(review=review)))

    with pytest.raises(ValueError, match=r"build\.review\.max_iterations") as excinfo:
        registration.build_presets(context=amendment)

    message = str(excinfo.value)
    assert "build.review.max_iterations" in message
    assert "build.review.additional.max_iterations" in message
    assert str(review_iterations) not in message
    assert str(additional_iterations) not in message
    assert amendment.buffered == []


def test_build_presets_strategy_conflict_takes_precedence_over_iteration_conflict():
    """Raises the strategy conflict first when both conflicts are authored together."""
    review = StandinReview(
        strategy="thorough",
        max_iterations=7,
        additional=StandinAdditional(patience=4, max_iterations=15),
    )
    amendment = StandinAmendment(config=StandinConfig(build=StandinBuild(review=review)))

    with pytest.raises(ValueError, match=r"build\.review\.strategy") as excinfo:
        registration.build_presets(context=amendment)

    assert "build.review.max_iterations" not in str(excinfo.value)
    assert amendment.buffered == []


def test_build_presets_conflict_read_footprint_is_guard_leaf_only():
    """Reads only the build.review.strategy chain before the conflict raise, nothing else."""
    review_level = RecordingLevel(
        {
            "strategy": "thorough",
            "agent": "claude",
            "additional": StandinAdditional(patience=4, max_iterations=9),
        }
    )
    build_level = RecordingLevel({"review": review_level, "agent": "claude"})
    config_level = RecordingLevel(
        {
            "build": build_level,
            "pipeline": RecordingLevel({"name": "release"}),
            "topics": RecordingLevel({"items": []}),
        }
    )
    amendment = StandinAmendment(config=config_level)

    with pytest.raises(ValueError, match=r"build\.review\.strategy"):
        registration.build_presets(context=amendment)

    assert config_level.reads == ["build"]
    assert build_level.reads == ["review"]
    assert review_level.reads == ["strategy"]
    assert amendment.buffered == []


def test_build_presets_read_footprint_is_guard_and_iteration_chains_only():
    """Reads exactly the strategy guard chain and the two iteration-cap chains on the happy path."""
    additional_level = RecordingLevel({"max_iterations": 9, "patience": 4, "agent": "codex"})
    review_level = RecordingLevel(
        {
            "strategy": "short",
            "max_iterations": None,
            "agent": "claude",
            "additional": additional_level,
        }
    )
    build_level = RecordingLevel({"review": review_level, "agent": "claude"})
    config_level = RecordingLevel(
        {
            "build": build_level,
            "pipeline": RecordingLevel({"name": "release"}),
            "topics": RecordingLevel({"items": []}),
        }
    )
    amendment = StandinAmendment(config=config_level)

    registration.build_presets(context=amendment)

    assert config_level.reads == ["build"]
    assert build_level.reads == ["review"]
    assert review_level.reads == ["strategy", "max_iterations", "additional"]
    assert additional_level.reads == ["max_iterations"]
    assert amendment.buffered == [
        ("build.review.strategy", "short"),
        ("build.review.additional.patience", 1),
        ("build.review.additional.max_iterations", 3),
    ]
