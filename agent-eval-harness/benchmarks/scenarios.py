"""Synthetic benchmark scenarios for the agent-eval-harness demo.

Every task here is invented for this portfolio piece -- a small,
imaginary "order support" agent that extracts structured data,
classifies tickets, estimates costs, and explains its decisions. None of
it is derived from any real product or dataset. Each scenario pairs one
:class:`~agent_eval_harness.spec.TaskSpec` with a handful of sample agent
outputs so :mod:`run` has something concrete to score: at least one
sample that should pass cleanly, and at least one that should fail or
score partially, so a scorecard actually shows contrast.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_eval_harness.spec import FieldSpec, NumericToleranceSpec, TaskSpec


@dataclass(frozen=True)
class BenchmarkSample:
    """One agent output to score against a scenario's TaskSpec."""

    label: str
    output: dict[str, Any]


@dataclass(frozen=True)
class BenchmarkScenario:
    """A task spec plus the sample outputs to score against it."""

    spec: TaskSpec
    samples: list[BenchmarkSample]


# ---------------------------------------------------------------------------
# 1. Pure schema task -- extracting a structured order summary
# ---------------------------------------------------------------------------

_extract_order_summary = BenchmarkScenario(
    spec=TaskSpec(
        task_id="extract_order_summary",
        description="Extract order_id, item_count, and total from a support ticket.",
        schema=[
            FieldSpec(name="order_id", type=str),
            FieldSpec(name="item_count", type=int),
            FieldSpec(name="total", type=float),
        ],
    ),
    samples=[
        BenchmarkSample(
            label="well_formed",
            output={"order_id": "ORD-8842", "item_count": 3, "total": 129.99},
        ),
        BenchmarkSample(
            label="missing_item_count",
            output={"order_id": "ORD-8843", "total": 54.00},
        ),
        BenchmarkSample(
            label="wrong_type_for_total",
            output={"order_id": "ORD-8844", "item_count": 1, "total": "19.99"},
        ),
    ],
)

# ---------------------------------------------------------------------------
# 2. Exact-match task -- classifying ticket priority
# ---------------------------------------------------------------------------

_classify_ticket_priority = BenchmarkScenario(
    spec=TaskSpec(
        task_id="classify_ticket_priority",
        description="Classify a ticket about a stalled shipment as high priority.",
        exact_fields={"priority": "high", "category": "shipping_delay"},
    ),
    samples=[
        BenchmarkSample(
            label="correct_classification",
            output={"priority": "high", "category": "shipping_delay"},
        ),
        BenchmarkSample(
            label="underestimated_priority",
            output={"priority": "medium", "category": "shipping_delay"},
        ),
    ],
)

# ---------------------------------------------------------------------------
# 3. Numeric-tolerance task -- estimating shipping cost
# ---------------------------------------------------------------------------

_estimate_shipping_cost = BenchmarkScenario(
    spec=TaskSpec(
        task_id="estimate_shipping_cost",
        description="Estimate shipping cost for a 3.2kg package to a standard zone.",
        numeric_fields=[
            NumericToleranceSpec(field="cost_usd", expected=14.50, abs_tolerance=1.00),
        ],
    ),
    samples=[
        BenchmarkSample(label="within_tolerance", output={"cost_usd": 15.10}),
        BenchmarkSample(label="way_off", output={"cost_usd": 42.00}),
    ],
)

# ---------------------------------------------------------------------------
# 4. Judged task -- explaining a refund decision
# ---------------------------------------------------------------------------

_explain_refund_decision = BenchmarkScenario(
    spec=TaskSpec(
        task_id="explain_refund_decision",
        description="Explain why a refund was approved for a damaged-item claim.",
        schema=[FieldSpec(name="approved", type=bool)],
        exact_fields={"approved": True},
        explanation_field="explanation",
        required_keywords=["damaged", "refund"],
        forbidden_phrases=["not our policy"],
    ),
    samples=[
        BenchmarkSample(
            label="clear_explanation",
            output={
                "approved": True,
                "explanation": "The item arrived damaged, so a full refund was issued.",
            },
        ),
        BenchmarkSample(
            label="vague_and_dismissive",
            output={
                "approved": True,
                "explanation": "This is not our policy to cover, but we made an exception.",
            },
        ),
    ],
)

SCENARIOS: list[BenchmarkScenario] = [
    _extract_order_summary,
    _classify_ticket_priority,
    _estimate_shipping_cost,
    _explain_refund_decision,
]
