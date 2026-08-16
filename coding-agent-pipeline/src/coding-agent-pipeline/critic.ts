import type { GoalSpec } from "./goalSpec.js";
import type { PlanStep } from "./strategy.js";
import type { ValidationReport } from "./validator.js";

export type CriticDecisionKind = "retry" | "escalate" | "done";
export type EscalateCause = "attempts-exhausted" | "strategies-exhausted";

export interface CriticDecision {
  readonly kind: CriticDecisionKind;
  readonly attempt: number;
  readonly reason: string;
  readonly nextStrategyName?: string; // present when kind === "retry"
  readonly escalateCause?: EscalateCause; // present when kind === "escalate"
  readonly diagnostics?: string[]; // failing check ids, present when kind === "escalate"
}

/**
 * Given the current attempt's validation results and the strategies not yet tried,
 * decides whether to retry the next-ranked strategy, escalate (attempt budget exhausted,
 * or no candidate strategies left), or declare the goal done.
 */
export function decide(
  goal: GoalSpec,
  remainingSteps: PlanStep[],
  attempt: number,
  validation: ValidationReport,
): CriticDecision {
  if (validation.allPassed) {
    return { kind: "done", attempt, reason: "all acceptance criteria and constraints passed" };
  }

  if (attempt >= goal.maxAttempts) {
    return {
      kind: "escalate",
      attempt,
      reason: `attempt budget exhausted (${attempt}/${goal.maxAttempts})`,
      escalateCause: "attempts-exhausted",
      diagnostics: validation.failedIds,
    };
  }

  const next = remainingSteps[0];
  if (!next) {
    return {
      kind: "escalate",
      attempt,
      reason: "no remaining candidate strategies",
      escalateCause: "strategies-exhausted",
      diagnostics: validation.failedIds,
    };
  }

  return {
    kind: "retry",
    attempt,
    reason: `retrying after failing: ${validation.failedIds.join(", ")}`,
    nextStrategyName: next.strategy.name,
  };
}
